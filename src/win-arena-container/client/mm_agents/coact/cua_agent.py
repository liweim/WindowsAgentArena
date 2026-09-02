import base64
import json
import logging
import os
import time
import traceback
from typing import Any, Dict, List, Tuple
from PIL import Image
import io
import openai
from openai import OpenAI  # pip install --upgrade openai>=1.66.2
from mm_agents.llm import AbstractLLM
from .model_config import is_local_model
from mm_agents.utils import get_price

# from configs.config import OPENAI_API_KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
logger = logging.getLogger("desktopenv")

PROMPT_TEMPLATE = """# Task
{instruction}

# Hints
- Sudo password is "{CLIENT_PASSWORD}".
- Keep the windows/applications opened at the end of the task.
- Do not use shortcut to reload the application except for the browser, just close and reopen.
- If "The document has been changed by others" pops out, you should click "cancel" and reopen the file.
- If you have completed the user task, reply with the information you want the user to know along with 'TERMINATE'.
- If you don't know how to continue the task, reply your concern or question along with 'IDK'.
""".strip()
DEFAULT_REPLY = "Please continue the user task. If you have completed the user task, reply with the information you want the user to know along with 'TERMINATE'."


def _usage_delta(before: tuple[float, int, int, int], after: tuple[float, int, int, int]) -> tuple[float, int, int, int]:
    return (
        after[0] - before[0],
        after[1] - before[1],
        after[2] - before[2],
        after[3] - before[3],
    )


def _extract_finished_content(raw_response: str) -> str:
    import re

    match = re.search(r"finished\s*\(\s*content\s*=\s*['\"](.*?)['\"]\s*\)", raw_response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def _extract_action_block(raw_response: str) -> str:
    import re

    if not raw_response:
        return ""

    match = re.search(r"Action:\s*(.+?)\s*$", raw_response, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    stripped = raw_response.strip()
    if stripped.upper() in {"WAIT", "IDK", "DONE", "TERMINATE"}:
        return stripped
    if "pyautogui." in stripped:
        return stripped
    return ""


def _recoverable_local_result(step_no: int, detail: str) -> str:
    return f"IDK: GUI agent stopped at step {step_no}. {detail}".strip()


def _cua_to_pyautogui(action) -> str:
    """Convert an Action (dict **or** Pydantic model) into a pyautogui call."""
    def fld(key: str, default: Any = None) -> Any:
        return action.get(key, default) if isinstance(action, dict) else getattr(action, key, default)

    act_type = fld("type")
    if not isinstance(act_type, str):
        act_type = str(act_type).split(".")[-1]
    act_type = act_type.lower()

    if act_type in ["click", "double_click"]:
        button = fld('button', 'left')
        if button == 1 or button == 'left':
            button = 'left'
        elif button == 2 or button == 'middle':
            button = 'middle'
        elif button == 3 or button == 'right':
            button = 'right'

        if act_type == "click":
            return f"pyautogui.click({fld('x')}, {fld('y')}, button='{button}')"
        if act_type == "double_click":
            return f"pyautogui.doubleClick({fld('x')}, {fld('y')}, button='{button}')"
        
    if act_type == "scroll":
        cmd = ""
        if fld('scroll_y', 0) != 0:
            cmd += f"pyautogui.scroll({-fld('scroll_y', 0) / 100}, x={fld('x', 0)}, y={fld('y', 0)});"
        return cmd
    if act_type == "drag":
        path = fld('path', [{"x": 0, "y": 0}, {"x": 0, "y": 0}])
        cmd = f"pyautogui.moveTo({path[0]['x']}, {path[0]['y']}, _pause=False); "
        cmd += f"pyautogui.dragTo({path[1]['x']}, {path[1]['y']}, duration=0.5, button='left')"
        return cmd

    if act_type == 'move':
        return f"pyautogui.moveTo({fld('x')}, {fld('y')})"

    if act_type == "keypress":
        keys = fld("keys", []) or [fld("key")]
        if len(keys) == 1:
            return f"pyautogui.press('{keys[0].lower()}')"
        else:
            return "pyautogui.hotkey('{}')".format("', '".join(keys)).lower()
        
    if act_type == "type":
        text = str(fld("text", ""))
        return "pyautogui.typewrite({:})".format(repr(text))
    
    if act_type == "wait":
        return "WAIT"
    
    return "WAIT"  # fallback


def _to_input_items(output_items: list) -> list:
    """
    Convert `response.output` into the JSON-serialisable items we're allowed
    to resend in the next request.  We drop anything the CUA schema doesn't
    recognise (e.g. `status`, `id`, …) and cap history length.
    """
    cleaned: List[Dict[str, Any]] = []

    for item in output_items:
        raw: Dict[str, Any] = item if isinstance(item, dict) else item.model_dump()

        # ---- strip noisy / disallowed keys ---------------------------------
        raw.pop("status", None)
        cleaned.append(raw)

    return cleaned  # keep just the most recent 50 items


def call_openai_cua(client: OpenAI,
                    history_inputs: list,
                    screen_width: int = 1920,
                    screen_height: int = 1080,
                    environment: str = "linux",
                    model: str = "computer-use-preview") -> Tuple[Any, int, int]:
    """Call OpenAI CUA API with retry logic. Always returns tokens even on failure."""
    retry = 0
    response = None
    max_retries = 1
    input_tokens = 0
    output_tokens = 0
    
    while retry < max_retries:
        try:
            response = client.responses.create(
                model=model,
                tools=[{
                    "type": "computer_use_preview",
                    "display_width": screen_width,
                    "display_height": screen_height,
                    "environment": environment,
                }],
                input=history_inputs,
                reasoning={
                    "summary": "concise"
                },
                tool_choice="required",
                truncation="auto",
            )
            # Successfully got response
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            break
        except openai.BadRequestError as e:
            retry += 1
            logger.error(f"BadRequestError in response.create (attempt {retry}/{max_retries}): {e}")
            # Try to extract token usage from error if available
            try:
                if hasattr(e, 'response') and hasattr(e.response, 'json'):
                    error_data = e.response.json()
                    if 'usage' in error_data:
                        input_tokens = error_data['usage'].get('input_tokens', 0)
                        output_tokens = error_data['usage'].get('output_tokens', 0)
            except:
                pass
            time.sleep(0.5)
        except openai.InternalServerError as e:
            retry += 1
            logger.error(f"InternalServerError in response.create (attempt {retry}/{max_retries}): {e}")
            time.sleep(0.5)
        except Exception as e:
            retry += 1
            logger.error(f"Unexpected error in response.create (attempt {retry}/{max_retries}): {e}")
            logger.error(traceback.format_exc())
            time.sleep(0.5)
    
    if retry == max_retries or response is None:
        error_msg = "Failed to call OpenAI after retries"
        logger.error(error_msg)
        raise Exception(error_msg)

    return response, input_tokens, output_tokens


def run_cua(
    env,
    instruction: str,
    max_steps: int,
    save_path: str = './',
    sleep_after_execution: float = 0.3,
    truncate_history_inputs: int = 100,
    client_password: str = "",
    model: str = "computer-use-preview",
) -> Tuple[List, str, float, int, int, int, List[Dict]]:
    """
    Run CUA agent with comprehensive error handling and token usage tracking.
    Always returns token usage, even on failure.

    Returns:
        Tuple containing:
        - history_inputs: List of conversation history
        - reasoning: Final reasoning text
        - total_cost: Total cost across all steps
        - total_input_tokens: Total input tokens
        - total_output_tokens: Total output tokens
        - total_image_count: Total images processed
        - step_details: List of per-step details (new)
    """
    # Initialize ALL tracking variables at the very beginning to ensure they exist
    total_input_tokens = 0
    total_output_tokens = 0
    total_image_count = 0
    reasoning = "ERROR: Task execution failed before initialization"
    history_inputs = []
    step_no = 0
    reasoning_list = []
    response = None
    step_details = []  # New: store per-step information
    
    try:
        if is_local_model(model):
            llm = AbstractLLM(model_name=model)
            logger.info(f"Instruction: {instruction}")
            obs = env.controller.get_screenshot()
            with open(os.path.join(save_path, "initial_screenshot.png"), "wb") as f:
                f.write(obs)
            total_image_count = 0
            history_inputs = []
            step_summaries: List[str] = []

            while step_no < max_steps:
                step_no += 1
                screenshot = Image.open(io.BytesIO(obs)).convert("RGB")
                screen_width, screen_height = screenshot.size
                history_block = ""
                if step_summaries:
                    history_block = "\n\n# Previous Steps\n" + "\n".join(step_summaries[-truncate_history_inputs:])
                prompt = PROMPT_TEMPLATE.format(instruction=instruction, CLIENT_PASSWORD=client_password) + history_block

                client = llm.client
                messages = client._build_cua_messages(prompt, screenshot, screen_width, screen_height)
                before_usage = llm.get_usage()
                raw_response = llm(messages, max_retries=3) or ""
                after_usage = llm.get_usage()
                step_cost, step_input_tokens, step_output_tokens, step_image_count = _usage_delta(before_usage, after_usage)
                total_input_tokens += step_input_tokens
                total_output_tokens += step_output_tokens
                total_image_count += step_image_count

                if not raw_response:
                    reasoning = _recoverable_local_result(
                        step_no,
                        "The local GUI model returned no response, likely due to context exhaustion or generation failure.",
                    )
                    step_details.append({
                        "step": step_no,
                        "actions": [],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no - 1}.png" if step_no > 1 else "initial_screenshot.png",
                        "error": "Empty model response",
                    })
                    break

                py_cmd, step_reasoning = client.parse_cua_response(raw_response, messages, screen_width, screen_height)
                reasoning = step_reasoning or raw_response
                lower_raw = raw_response.lower()
                action_repr = _extract_action_block(raw_response) or py_cmd

                if "finished(" in lower_raw:
                    finished_content = _extract_finished_content(raw_response)
                    if finished_content:
                        reasoning = finished_content
                    step_details.append({
                        "step": step_no,
                        "actions": [],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no - 1}.png" if step_no > 1 else "initial_screenshot.png",
                    })
                    break

                if isinstance(action_repr, str) and action_repr.strip().upper() in {"IDK", "DONE", "TERMINATE"}:
                    reasoning = action_repr.strip()
                    step_details.append({
                        "step": step_no,
                        "actions": [],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no - 1}.png" if step_no > 1 else "initial_screenshot.png",
                    })
                    break

                if isinstance(reasoning, str) and (reasoning.startswith("Error:") or reasoning.startswith("ERROR")):
                    reasoning = _recoverable_local_result(
                        step_no,
                        f"The GUI model output could not be parsed safely. Last parser message: {reasoning}",
                    )
                    step_details.append({
                        "step": step_no,
                        "actions": [],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no - 1}.png" if step_no > 1 else "initial_screenshot.png",
                        "error": "Parser failure",
                    })
                    break

                if not py_cmd:
                    reasoning = _recoverable_local_result(
                        step_no,
                        "The GUI model did not yield an executable action.",
                    )
                    step_details.append({
                        "step": step_no,
                        "actions": [],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no - 1}.png" if step_no > 1 else "initial_screenshot.png",
                        "error": "Missing executable action",
                    })
                    break

                try:
                    next_obs, *_ = env.step(py_cmd, sleep_after_execution)
                    obs = next_obs["screenshot"]
                    with open(os.path.join(save_path, f"step_{step_no}.png"), "wb") as f:
                        f.write(obs)
                    step_details.append({
                        "step": step_no,
                        "actions": [py_cmd],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no}.png",
                    })
                    history_action = action_repr or py_cmd
                    step_summaries.append(f"Step {step_no}: Thought: {reasoning} | Action: {history_action}")
                    history_inputs.append(
                        {
                            "step": step_no,
                            "thought": reasoning,
                            "action": history_action,
                        }
                    )
                except Exception as e:
                    reasoning = _recoverable_local_result(
                        step_no,
                        f"Executing the proposed GUI action failed with: {str(e)}",
                    )
                    step_details.append({
                        "step": step_no,
                        "actions": [py_cmd],
                        "reasoning": reasoning,
                        "input_tokens": step_input_tokens,
                        "output_tokens": step_output_tokens,
                        "cost": step_cost,
                        "screenshot": f"step_{step_no}.png" if step_no > 0 else "initial_screenshot.png",
                        "error": str(e),
                    })
                    break

            total_cost = llm.get_usage()[0]
            return history_inputs, reasoning, total_cost, total_input_tokens, total_output_tokens, total_image_count, step_details

        client = OpenAI(api_key=OPENAI_API_KEY)

        # 0 / reset & first screenshot
        logger.info(f"Instruction: {instruction}")
        obs = env.controller.get_screenshot()
        screenshot_b64 = base64.b64encode(obs).decode("utf-8")
        screen_width, screen_height = Image.open(io.BytesIO(base64.b64decode(screenshot_b64))).size
        with open(os.path.join(save_path, "initial_screenshot.png"), "wb") as f:
            f.write(obs)
        total_image_count = 1  # Initial screenshot successfully captured
        
        history_inputs = [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": PROMPT_TEMPLATE.format(instruction=instruction, CLIENT_PASSWORD=client_password)},
                {"type": "input_image", "image_url": f"data:image/png;base64,{screenshot_b64}"},
            ],
        }]

        # Initial CUA call
        try:
            response, input_tokens, output_tokens = call_openai_cua(client, history_inputs, screen_width, screen_height, model=model)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            logger.info(f"Initial CUA call - Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        except Exception as e:
            logger.error(f"Failed to initialize CUA: {e}")
            logger.error(traceback.format_exc())
            reasoning = f"ERROR: Failed to initialize CUA: {str(e)}"
            # Return with whatever tokens we have
            prompt_price, completion_price = get_price(model)
            total_cost = total_input_tokens * prompt_price + total_output_tokens * completion_price
            logger.info(f"Returning with partial usage - Cost: ${total_cost:.4f}, Tokens: {total_input_tokens + total_output_tokens}, Images: {total_image_count}")
            return history_inputs, reasoning, total_cost, total_input_tokens, total_output_tokens, total_image_count, step_details

        # 1 / iterative dialogue
        while step_no < max_steps:
            step_no += 1

            history_inputs += _to_input_items(response.output)

            # --- robustly pull out computer_call(s) ------------------------------
            calls: List[Dict[str, Any]] = []
            breakflag = False
            
            for i, o in enumerate(response.output):
                typ = o["type"] if isinstance(o, dict) else getattr(o, "type", None)
                if not isinstance(typ, str):
                    typ = str(typ).split(".")[-1]
                if typ == "computer_call":
                    calls.append(o if isinstance(o, dict) else o.model_dump())
                elif typ == "reasoning" and len(o.summary) > 0:
                    reasoning = o.summary[0].text
                    reasoning_list.append(reasoning)
                    logger.info(f"[Reasoning]: {reasoning}")
                elif typ == 'message':
                    if 'TERMINATE' in o.content[0].text:
                        reasoning_list.append(f"Final output: {o.content[0].text}")
                        reasoning = "My thinking process\n" + "\n- ".join(reasoning_list) + '\nPlease check the screenshot and see if it fulfills your requirements.'
                        breakflag = True
                        break
                    if 'IDK' in o.content[0].text:
                        reasoning = f"{o.content[0].text}. I don't know how to complete the task. Please check the current screenshot."
                        breakflag = True
                        break
                    try:
                        json.loads(o.content[0].text)
                        history_inputs.pop(len(history_inputs) - len(response.output) + i)
                        step_no -= 1
                    except Exception:
                        logger.info(f"[Message]: {o.content[0].text}")
                        if '?' in o.content[0].text:
                            history_inputs += [{
                                "role": "user",
                                "content": [
                                    {"type": "input_text", "text": DEFAULT_REPLY},
                                ],
                            }]
                        elif "{" in o.content[0].text and "}" in o.content[0].text:
                            history_inputs.pop(len(history_inputs) - len(response.output) + i)
                            step_no -= 1
                        else:
                            logger.info(f"[Message]: {o.content[0].text}")
                            history_inputs.pop(len(history_inputs) - len(response.output) + i)
                            reasoning = o.content[0].text
                            reasoning_list.append(reasoning)
                            step_no -= 1

            if breakflag:
                break

            # Execute actions - try each action, continue on failure
            for action_call in calls:
                try:
                    py_cmd = _cua_to_pyautogui(action_call["action"])
                    obs, *_ = env.step(py_cmd, sleep_after_execution)

                    screenshot_b64 = base64.b64encode(obs["screenshot"]).decode("utf-8")
                    with open(os.path.join(save_path, f"step_{step_no}.png"), "wb") as f:
                        f.write(obs["screenshot"])
                    history_inputs += [{
                        "type": "computer_call_output",
                        "call_id": action_call["call_id"],
                        "output": {
                            "type": "computer_screenshot",
                            "image_url": f"data:image/png;base64,{screenshot_b64}",
                        },
                    }]
                    total_image_count += 1
                    
                    if "pending_safety_checks" in action_call and len(action_call.get("pending_safety_checks", [])) > 0:
                        history_inputs[-1]['acknowledged_safety_checks'] = [
                            {
                                "id": psc["id"],
                                "code": psc["code"],
                                "message": "Please acknowledge this warning if you'd like to proceed."
                            }
                            for psc in action_call.get("pending_safety_checks", [])
                        ]
                except Exception as e:
                    logger.error(f"Failed to execute action at step {step_no}: {e}")
                    # Continue with other actions
                    continue
            
            # truncate history inputs while preserving call_id pairs
            if len(history_inputs) > truncate_history_inputs:
                original_history = history_inputs[:]
                history_inputs = [history_inputs[0]] + history_inputs[-truncate_history_inputs:]
                
                # Find all call_ids in the truncated history
                call_ids_in_truncated = set()
                for item in history_inputs:
                    if isinstance(item, dict) and 'call_id' in item:
                        call_ids_in_truncated.add(item['call_id'])
                
                # Check if any call_ids are missing their pairs
                call_id_types = {}  # call_id -> list of types that reference it
                for item in history_inputs:
                    if isinstance(item, dict) and 'call_id' in item:
                        call_id = item['call_id']
                        item_type = item.get('type', '')
                        if call_id not in call_id_types:
                            call_id_types[call_id] = []
                        call_id_types[call_id].append(item_type)
                
                # Find unpaired call_ids (should have both computer_call and computer_call_output)
                unpaired_call_ids = []
                for call_id, types in call_id_types.items():
                    # Check if we have both call and output
                    has_call = 'computer_call' in types
                    has_output = 'computer_call_output' in types
                    if not (has_call and has_output):
                        unpaired_call_ids.append(call_id)
                
                # Add missing pairs from original history while preserving order
                if unpaired_call_ids:
                    # Find missing paired items in their original order
                    missing_items = []
                    for item in original_history:
                        if (isinstance(item, dict) and 
                            item.get('call_id') in unpaired_call_ids and 
                            item not in history_inputs):
                            missing_items.append(item)
                    
                    # Insert missing items back, preserving their original order
                    for missing_item in missing_items:
                        original_index = original_history.index(missing_item)
                        insert_pos = len(history_inputs)  # default to end
                        for i, existing_item in enumerate(history_inputs[1:], 1):
                            if existing_item in original_history:
                                existing_original_index = original_history.index(existing_item)
                                if existing_original_index > original_index:
                                    insert_pos = i
                                    break
                        history_inputs.insert(insert_pos, missing_item)

            # Record step details before next API call
            # Extract action scripts from calls
            step_actions = []
            for action_call in calls:
                try:
                    py_cmd = _cua_to_pyautogui(action_call["action"])
                    step_actions.append(py_cmd)
                except:
                    pass

            # Next CUA call
            try:
                response, input_tokens, output_tokens = call_openai_cua(client, history_inputs, screen_width, screen_height, model=model)
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                logger.info(f"Step {step_no} CUA call - Input tokens: {input_tokens}, Output tokens: {output_tokens}, Total: {total_input_tokens + total_output_tokens}")

                # Record this step's details
                prompt_price, completion_price = get_price(model)
                step_cost = input_tokens * prompt_price + output_tokens * completion_price
                step_detail = {
                    "step": step_no,
                    "actions": step_actions,
                    "reasoning": reasoning if reasoning else "",
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": step_cost,
                    "screenshot": f"step_{step_no}.png"
                }
                step_details.append(step_detail)

            except Exception as e:
                logger.error(f"Failed to call CUA at step {step_no}: {e}")
                logger.error(traceback.format_exc())
                reasoning = f"ERROR at step {step_no}: Failed to call CUA API: {str(e)}"

                # Record failed step
                step_detail = {
                    "step": step_no,
                    "actions": step_actions,
                    "reasoning": reasoning,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0,
                    "screenshot": f"step_{step_no}.png",
                    "error": str(e)
                }
                step_details.append(step_detail)
                break
        
        # Cleanup: press Esc
        logger.info("Task completed, press Esc to close the temporary window")
        try:
            esc_cmd = "pyautogui.press('esc')"
            obs, *_ = env.step(esc_cmd, sleep_after_execution)
        except Exception:
            pass  # Not critical

    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(f"Unexpected error in run_cua: {e}")
        logger.error(traceback.format_exc())
        reasoning = f"CRITICAL ERROR: {str(e)}"
    
    finally:
        # ALWAYS calculate and log usage, regardless of success or failure
        prompt_price, completion_price = get_price(model)
        total_cost = total_input_tokens * prompt_price + total_output_tokens * completion_price
        logger.info(f"=== CUA Task Summary ===")
        logger.info(f"Total cost: ${total_cost:.4f}")
        logger.info(f"Total tokens: {total_input_tokens + total_output_tokens} (input: {total_input_tokens}, output: {total_output_tokens})")
        logger.info(f"Total images sent: {total_image_count}")
        logger.info(f"Steps completed: {step_no}")
        
        # Clean up image URLs in history for JSON serialization
        if history_inputs and len(history_inputs) > 0:
            if 'content' in history_inputs[0]:
                for content_item in history_inputs[0]['content']:
                    if isinstance(content_item, dict) and content_item.get('type') == 'input_image':
                        content_item['image_url'] = "<image>"
            for item in history_inputs:
                if isinstance(item, dict) and item.get('type') == 'computer_call_output':
                    if 'output' in item and 'image_url' in item['output']:
                        item['output']['image_url'] = "<image>"

    return history_inputs, reasoning, total_cost, total_input_tokens, total_output_tokens, total_image_count, step_details
