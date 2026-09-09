"""Adapt TARS role/tool conversations to WindowsAgentArena's model interface."""

import base64
import copy
from dataclasses import asdict, is_dataclass
import io
import json
import logging
import math
import os
import uuid

from json_repair import repair_json
from PIL import Image
from mm_agents.llm import AbstractLLM
from ..runtime.task_log import dump_model_trace

TARGETS = (("coordinate", "target"), ("start_coordinate", "start_target"),
           ("end_coordinate", "end_target"))


def normalize_grounded_point(point, width=1280, height=720):
    """Reject out-of-frame points without silently changing the selected target."""
    if not isinstance(point, (tuple, list)) or len(point) != 2:
        raise ValueError(f"Grounder did not return a coordinate pair: {point}")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in point):
        raise ValueError(f"Grounder returned invalid coordinates: {point}")
    x, y = point
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Grounder point {point} outside {width}x{height}; describe the target more precisely")
    return [int(x), int(y)]


class LLMClient:
    def __init__(self, name, system_prompt, tools, model, provider=None,
                 temperature=None, top_p=None, only_n_most_recent_images=5, **kwargs):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = copy.deepcopy(tools)
        self.model_name = model
        self.image_limit = only_n_most_recent_images
        self.client = AbstractLLM(model, temperature=temperature or 0,
                                 max_tokens=int(os.getenv("TARS_MAX_TOKENS", "4096")),
                                 top_p=top_p if top_p is not None else 0.95)
        self.grounder = None
        self.reset()
        for tool in self.tools:
            schema = tool["input_schema"]
            props = schema.get("properties", {})
            for coordinate, target in TARGETS:
                if coordinate not in props:
                    continue
                del props[coordinate]
                props[target] = {"type": "string", "description":
                                 "Precise visual description of the target element for GTA1."}
                schema["required"] = [target if key == coordinate else key
                                      for key in schema.get("required", [])]
                tool["description"] = {
                    "click": "Click the described target using GTA1; supports click count, button and modifier keys.",
                    "type": "Type text; optionally describe a target field to focus using GTA1 first.",
                    "scroll": "Scroll over the described target using GTA1. Positive clicks: up; negative: down; shift: horizontal.",
                    "drag_and_drop": "Drag from start_target to end_target, both described visually and located by GTA1.",
                }.get(tool["name"], "Act on the described GUI target located by GTA1.")

    def reset(self):
        self.messages = []
        self.latest_image = None

    @property
    def usage(self):
        _, inputs, outputs, _ = self.client.get_usage()
        return {"total_input_tokens": inputs, "total_output_tokens": outputs}

    def add_user_message(self, text, images=None):
        content = [{"type": "input_image", "image_url": f"data:image/png;base64,{data}"}
                   for data in images or []]
        if images:
            self.latest_image = images[-1]
        content.append({"type": "input_text", "text": text})
        self.messages.append({"role": "user", "content": content})

    def add_tool_results(self, results):
        for call_id, result in results:
            payload = asdict(result) if is_dataclass(result) else dict(result)
            image = payload.pop("base64_data", None)
            self.add_user_message(json.dumps({"tool_call_id": call_id, "result": payload},
                                             ensure_ascii=False, default=str),
                                  images=[image] if image else None)

    def _ground(self, call):
        inp = call["input"]
        props = next(tool for tool in self.tools if tool["name"] == call["name"])["input_schema"]["properties"]
        for coordinate, target in TARGETS:
            if coordinate in inp:
                raise ValueError("GUI coordinates must come from GTA1; supply target descriptions")
            if target not in props or target not in inp:
                continue
            if not isinstance(inp[target], str) or not inp[target].strip():
                raise ValueError(f"{target} must be a nonempty description")
            if not self.latest_image:
                raise RuntimeError("Cannot ground without a screenshot")
            if self.grounder is None:
                self.grounder = AbstractLLM(os.getenv("TARS_GROUNDER_MODEL", "gta1-7b"), temperature=0)
                if hasattr(self.grounder, "client"):
                    self.grounder.client.cua_trace_callback = lambda stage, payload: dump_model_trace(
                        stage, payload, agent=self.name, model=self.grounder.model_name)
            with Image.open(io.BytesIO(base64.b64decode(self.latest_image))) as image:
                logger = logging.getLogger("desktopenv.tars")
                logger.info("Grounding request: tool=%s target=%r screenshot_size=%s",
                            call["name"], inp[target], image.size)
                # The existing role handlers expect coordinates in this space.
                image = image.resize((1280, 720))
                point, reason = self.grounder.call_cua(inp[target], image,
                    environment="windows", screen_width=1280, screen_height=720)
                logger.info("Grounding response: point=%s trace=%s", point,
                            getattr(getattr(self.grounder, "client", None), "last_gta1_trace", None))
            inp[coordinate] = normalize_grounded_point(point)

    def generate_and_process(self):
        instruction = ('\nReturn one JSON object: {"thought": "...", "tool_calls": '
                       '[{"name": "tool_name", "input": {...}}]}. '
                       'Return exactly one tool call. GUI targets MUST be visual descriptions, '
                       'not coordinates; a separate grounder locates them.\nTools:\n')
        messages = copy.deepcopy(self.messages)
        budget = self.image_limit
        if budget is not None:
            for message in reversed(messages):
                kept = []
                for block in reversed(message["content"]):
                    if block["type"] == "input_image":
                        if budget <= 0:
                            continue
                        budget -= 1
                    kept.append(block)
                message["content"] = list(reversed(kept))
        prompt = [{"role": "system", "content": [{"type": "input_text", "text":
                    self.system_prompt + instruction + json.dumps(self.tools)}]}, *messages]
        for attempt in range(3):
            dump_model_trace("request", {"messages": prompt}, agent=self.name,
                             model=self.model_name, attempt=attempt + 1)
            try:
                raw = self.client(prompt, max_retries=3)
            except Exception as exc:
                dump_model_trace("request_error", {"error": repr(exc)}, agent=self.name,
                                 model=self.model_name, attempt=attempt + 1)
                raise
            dump_model_trace("response", raw, agent=self.name,
                             model=self.model_name, attempt=attempt + 1)
            if not raw:
                raise RuntimeError(f"{self.name}: model returned no response")
            try:
                data = repair_json(raw.rsplit("</think>", 1)[-1], return_objects=True)
                calls = data["tool_calls"]
                if not isinstance(calls, list) or len(calls) != 1:
                    raise ValueError("Return exactly one tool call")
                call = calls[0]
                known = {tool["name"]: tool for tool in self.tools}
                if call["name"] not in known or not isinstance(call["input"], dict):
                    raise ValueError("Unknown tool or invalid input")
                required = known[call["name"]]["input_schema"].get("required", [])
                if any(key not in call["input"] for key in required):
                    raise ValueError(f"Missing required arguments: {required}")
                call["id"] = uuid.uuid4().hex
                serialized = json.dumps(data, ensure_ascii=False)
                self._ground(call)
                self.messages.append({"role": "assistant", "content": [
                    {"type": "input_text", "text": serialized}]})
                return calls, [str(data.get("thought", ""))], [], "tool_use"
            except (ValueError, TypeError, KeyError) as exc:
                dump_model_trace("validation_error", {"error": str(exc)}, agent=self.name,
                                 model=self.model_name, attempt=attempt + 1)
                prompt.append({"role": "user", "content": [{"type": "input_text",
                               "text": f"Invalid response: {exc}. Return valid tool-call JSON."}]})
        raise RuntimeError(f"{self.name}: invalid tool response after three attempts")

    def print_usage(self):
        return f"{self.name}: {self.usage}"
