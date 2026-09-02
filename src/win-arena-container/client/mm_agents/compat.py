"""Adapters between bundled agent frameworks and WindowsAgentArena.

This module intentionally keeps framework imports lazy.  Navi users should
not need optional dependencies used only by HiSA, Agent-S3, or CoAct.
"""

import logging
import os
from typing import Dict, Optional


logger = logging.getLogger("desktopenv.experiment")

AGENT_ALIASES = {
    "agent-s3": "agents3",
    "agent_s3": "agents3",
    "s3": "agents3",
    "gta1_agent": "gta1",
    "local-lstc": "locallstc",
    "local_lstc": "locallstc",
}
STEP_AGENT_NAMES = frozenset({"gta1", "agents3"})
FRAMEWORK_AGENT_NAMES = frozenset({"locallstc", "hisa", "coact"})
SUPPORTED_AGENT_NAMES = frozenset(
    {"navi", "claude"} | STEP_AGENT_NAMES | FRAMEWORK_AGENT_NAMES
)
LEGACY_NAVI_DEFAULT_MODEL = "gpt-4-vision-preview"
FRAMEWORK_DEFAULT_MODELS = {
    "gta1": "o3",
    "agents3": "gpt-4o",
    "hisa": "gpt-5-mini",
    "locallstc": "gpt-5-mini",
}


def normalize_agent_name(name: str) -> str:
    """Return the canonical, case-insensitive framework name."""
    normalized = str(name or "").strip().lower()
    return AGENT_ALIASES.get(normalized, normalized)


def prepare_framework_args(args) -> None:
    """Normalize settings that are required by the added GUI frameworks."""
    args.agent_name = normalize_agent_name(args.agent_name)
    if args.agent_name not in SUPPORTED_AGENT_NAMES:
        supported = ", ".join(sorted(SUPPORTED_AGENT_NAMES))
        raise ValueError(
            "Unknown agent name {!r}. Supported agents: {}".format(
                args.agent_name, supported
            )
        )

    if args.agent_name in STEP_AGENT_NAMES | FRAMEWORK_AGENT_NAMES:
        framework_default = FRAMEWORK_DEFAULT_MODELS.get(args.agent_name)
        if args.model == LEGACY_NAVI_DEFAULT_MODEL and framework_default:
            logger.warning(
                "%s does not support Navi's legacy default model %s; using %s",
                args.agent_name,
                args.model,
                framework_default,
            )
            args.model = framework_default
        if args.action_space != "pyautogui":
            logger.warning(
                "%s requires pyautogui actions; overriding --action_space=%s",
                args.agent_name,
                args.action_space,
            )
        if args.observation_type != "screenshot":
            logger.warning(
                "%s requires screenshot observations; overriding --observation_type=%s",
                args.agent_name,
                args.observation_type,
            )
        args.action_space = "pyautogui"
        args.observation_type = "screenshot"

    # run_single_example uses these attributes for all step-based agents.
    args.method = args.agent_name
    if not hasattr(args, "record"):
        args.record = False


def _infer_provider(model_name: str, explicit_provider: Optional[str], default: str) -> str:
    if explicit_provider:
        return explicit_provider

    from mm_agents.llm import MODEL_CONFIGS

    config = MODEL_CONFIGS.get(model_name)
    if config is not None and config.client_class == "LocalLLM":
        return "vllm"
    return default


def build_step_agent(args, env):
    """Build an agent that follows the standard ``reset/predict`` protocol."""
    if args.agent_name == "gta1":
        from mm_agents.gta1_agent import GTA1Agent

        return GTA1Agent(
            platform="windows",
            planner_model=args.model,
            judge_model=args.judge_model or args.model,
            ground_model=args.ground_model,
            max_tokens=args.max_tokens,
            top_p=args.top_p,
            temperature=args.temperature,
            action_space="pyautogui",
            observation_type="screenshot",
            max_steps=args.max_steps,
            N_SEQ=args.n_samples,
            client_password=args.client_password,
            screen_width=args.screen_width,
            screen_height=args.screen_height,
        )

    if args.agent_name == "agents3":
        from mm_agents.gui_agents.s3.agents.agent_s import AgentS3
        from mm_agents.gui_agents.s3.agents.grounding import OSWorldACI

        model_provider = _infer_provider(
            args.model, args.model_provider or None, "openai"
        )
        ground_provider = _infer_provider(
            args.ground_model, args.ground_provider or None, "openai"
        )
        generation_params = {
            "engine_type": model_provider,
            "model": args.model,
            "base_url": args.model_url,
            "api_key": args.model_api_key,
            "temperature": args.model_temperature,
        }
        grounding_params = {
            "engine_type": ground_provider,
            "model": args.ground_model,
            "base_url": args.ground_url,
            "api_key": args.ground_api_key,
            "grounding_width": args.grounding_width,
            "grounding_height": args.grounding_height,
        }
        grounding_agent = OSWorldACI(
            env=env,
            platform="windows",
            engine_params_for_generation=generation_params,
            engine_params_for_grounding=grounding_params,
            width=args.screen_width,
            height=args.screen_height,
            code_agent_budget=args.code_agent_budget,
        )
        return AgentS3(
            generation_params,
            grounding_agent,
            platform="windows",
            max_trajectory_length=args.max_trajectory_length,
            enable_reflection=not args.disable_reflection,
        )

    raise ValueError("{} is not a step-based agent".format(args.agent_name))


def build_additional_context(args, example: Dict) -> str:
    if not args.rag:
        return ""

    from mm_agents.utils import build_additional_contexts

    config_path = example.get("__task_config_path", "")
    return build_additional_contexts(
        example_dir=os.path.dirname(config_path),
        summarize_rag=args.summarize_rag,
        use_rag=True,
        rag_topk=args.rag_topk,
        rag_filename=args.rag_filename,
    )


def run_step_agent_example(
    agent,
    env,
    example,
    args,
    example_result_dir,
    scores,
):
    """Run GTA1 or Agent-S3 through their shared execution loop."""
    from mm_agents.run_single import run_single_example

    additional_context = build_additional_context(args, example)
    score_count = len(scores)
    run_single_example(
        agent,
        env,
        example,
        args.max_steps,
        example["instruction"],
        additional_context,
        args,
        example_result_dir,
        scores,
    )
    return scores[-1] if len(scores) > score_count else 0.0


def _run_locallstc(env, example, args, example_result_dir) -> float:
    from mm_agents.locallstc.main import LocalLSTC

    model = args.global_planner_model or args.model
    framework = LocalLSTC(
        env=env,
        global_planner_model=model,
        visual_grounder_model=args.visual_grounder_model,
        visual_grounder_scale=args.visual_grounder_scale,
        state_manager_model=args.state_manager_model or model,
        client_password=args.client_password,
        screen_width=args.screen_width,
        screen_height=args.screen_height,
        sleep_after_execution=args.sleep_after_execution,
        max_steps=args.max_steps,
        result_dir=args.result_dir,
        save_dir=example_result_dir,
        record=args.record,
        wo_roi=args.wo_roi,
        roi_margin=args.roi_margin,
        refine_period=args.refine_period,
        force_refine_period=args.force_refine_period,
        bash_timeout=args.bash_timeout,
        guest_platform=args.guest_platform,
        wo_l2s=args.wo_l2s,
        wo_s2l=args.wo_s2l,
        wo_cp=args.wo_cp,
        wo_al=args.wo_al,
        wo_sls=args.wo_sls,
        wo_fv=args.wo_fv,
        wo_ps=args.wo_ps,
        wo_sa=args.wo_sa,
        wo_sr=args.wo_sr,
        wo_think=args.wo_think,
        thinking_token_budget=args.thinking_token_budget,
        temperature=args.temperature,
        seed=args.seed,
        top_p=args.top_p,
        top_k=args.top_k,
    )
    return framework.execute_task(
        example, additional_context=build_additional_context(args, example)
    )


def _run_hisa(env, example, args, example_result_dir) -> float:
    from mm_agents.hisa.main import HiSA

    model = args.global_planner_model or args.model
    framework = HiSA(
        env=env,
        global_planner_model=model,
        visual_grounder_model=args.visual_grounder_model,
        state_manager_model=args.state_manager_model or model,
        client_password=args.client_password,
        screen_width=args.screen_width,
        screen_height=args.screen_height,
        sleep_after_execution=args.sleep_after_execution,
        max_steps=args.max_steps,
        save_dir=example_result_dir,
        record=args.record,
        wo_pattern=args.wo_pattern,
        pattern_dir=args.pattern_dir,
        use_qdrant_server=args.use_qdrant_server,
        qdrant_server_url=args.qdrant_server_url,
        wo_roi=args.wo_roi,
        roi_margin=args.roi_margin,
        refine_period=args.refine_period,
        bash_timeout=args.bash_timeout,
        wo_step=args.wo_step,
        wo_refinement=args.wo_refinement,
        sliding_window_size=args.sliding_window_size,
    )
    return framework.execute_task(
        example, additional_context=build_additional_context(args, example)
    )


def _run_coact(env, example, args, example_result_dir) -> float:
    from mm_agents.run_coact import process_task

    config_path = example.get("__task_config_path")
    if not config_path:
        raise ValueError("CoAct requires __task_config_path in the task config")
    domain = example.get("domain", "unknown")
    example_id = example.get("id") or os.path.basename(example_result_dir)
    _, score = process_task(
        (domain, example_id, config_path),
        env=env,
        path_to_vm=args.path_to_vm,
        snapshot_name=args.snapshot_name,
        orchestrator_model=args.orchestrator_model,
        coding_model=args.coding_model,
        summarizer_model=args.summarizer_model,
        cua_model=args.cua_model,
        result_dir=args.result_dir,
        orchestrator_max_steps=args.orchestrator_max_steps,
        cua_max_steps=args.cua_max_steps,
        coding_max_steps=args.coding_max_steps,
        cut_off_steps=args.cut_off_steps,
        screen_width=args.screen_width,
        screen_height=args.screen_height,
        sleep_after_execution=args.sleep_after_execution,
        config_path=args.oai_config_path,
        client_password=args.client_password,
        summarize_rag=args.summarize_rag,
        rag=args.rag,
        rag_topk=args.rag_topk,
        rag_filename=args.rag_filename,
        headless=args.headless,
        logger=logger,
        reset_delay=args.coact_reset_delay,
        close_env=False,
    )
    return float(score)


def run_framework_example(
    env,
    example,
    args,
    example_result_dir,
    scores,
) -> float:
    """Run a framework that owns its complete task execution loop."""
    if args.agent_name == "locallstc":
        score = _run_locallstc(env, example, args, example_result_dir)
    elif args.agent_name == "hisa":
        score = _run_hisa(env, example, args, example_result_dir)
    elif args.agent_name == "coact":
        score = _run_coact(env, example, args, example_result_dir)
    else:
        raise ValueError("{} is not a framework agent".format(args.agent_name))

    scores.append(float(score))
    result_path = os.path.join(example_result_dir, "result.txt")
    if not os.path.exists(result_path):
        with open(result_path, "w", encoding="utf-8") as result_file:
            result_file.write("{}\n".format(score))
    return float(score)
