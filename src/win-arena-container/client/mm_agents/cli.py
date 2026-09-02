"""Method-owned command-line parsing for the WinArena agent runners.

The process entry point deliberately does not parse arguments.  This module
only looks at the raw token stream to select an agent, then builds and runs the
parser registered for that agent.  Consequently, one framework never validates
or reserves another framework's options.
"""

import argparse
import logging
import os
import shlex
import sys
from typing import Callable, Dict, List, Optional

from mm_agents.compat import normalize_agent_name, prepare_framework_args


logger = logging.getLogger("desktopenv.experiment")
ParserConfigurer = Callable[[argparse.ArgumentParser], None]


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected a boolean value")


def _extract_agent_name(argv: List[str]) -> str:
    """Select a method without interpreting or validating any other token."""
    selected = "navi"
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in {"--agent_name", "--agent-name", "--agent"}:
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                # Leave malformed syntax untouched for the selected method's
                # ArgumentParser to diagnose.
                index += 1
                continue
            selected = argv[index + 1]
            index += 2
            continue
        for prefix in ("--agent_name=", "--agent-name=", "--agent="):
            if token.startswith(prefix):
                value = token[len(prefix):]
                if value:
                    selected = value
                break
        index += 1
    return normalize_agent_name(selected)


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    # Environment
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--action_space", "--action-space", default="pyautogui")
    parser.add_argument(
        "--observation_type",
        "--observation-type",
        choices=["screenshot", "a11y_tree", "screenshot_a11y_tree", "som"],
        default="a11y_tree",
    )
    parser.add_argument("--screen_width", "--screen-width", type=int, default=1920)
    parser.add_argument("--screen_height", "--screen-height", type=int, default=1200)
    parser.add_argument(
        "--sleep_after_execution",
        "--sleep-after-execution",
        type=float,
        default=3.0,
    )
    parser.add_argument("--max_steps", "--max-steps", type=int, default=15)
    parser.add_argument("--a11y_backend", "--a11y-backend", default="uia")
    parser.add_argument("--record", action="store_true")

    # Method selection and shared agent settings
    parser.add_argument("--agent_name", "--agent-name", "--agent", default="navi")
    parser.add_argument("--som_origin", "--som-origin", default="oss")
    parser.add_argument(
        "--max_trajectory_length",
        "--max-trajectory-length",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--test_config_base_dir",
        "--test-config-base-dir",
        default="evaluation_examples_windows",
    )

    # Shared model sampling settings.  Individual methods decide which ones
    # they use, but the container launcher supplies them for every method.
    parser.add_argument("--model", default="gpt-4-vision-preview")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--top_p", "--top-p", type=float, default=0.95)
    parser.add_argument("--top_k", "--top-k", type=int, default=20)
    parser.add_argument("--max_tokens", "--max-tokens", type=int, default=1500)
    parser.add_argument("--stop_token", "--stop-token", default=None)

    # Benchmark and output
    parser.add_argument("--domain", default="all")
    parser.add_argument("--emulator_ip", "--emulator-ip", default="20.20.20.21")
    parser.add_argument(
        "--test_all_meta_path",
        "--test-all-meta-path",
        "--json-name",
        default="evaluation_examples_windows/test_all.json",
    )
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--rerun_fail", "--rerun-fail", action="store_true")
    parser.add_argument("--result_dir", "--result-dir", default="./results")
    parser.add_argument(
        "--clean_results",
        "--clean-results",
        nargs="?",
        const=True,
        type=_parse_bool,
        default=False,
    )
    parser.add_argument("--trial_id", "--trial-id", default="0")
    parser.add_argument("--worker_id", "--worker-id", type=int, default=0)
    parser.add_argument("--num_workers", "--num-workers", type=int, default=1)
    parser.add_argument("--diff_lvl", "--diff-lvl", default="normal")


def _add_context_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--rag", action="store_true")
    parser.add_argument("--summarize_rag", "--summarize-rag", action="store_true")
    parser.add_argument("--rag_topk", "--rag-topk", type=int, default=4)
    parser.add_argument(
        "--rag_filename",
        "--rag-filename",
        default="retrieved_chunk_size_512_chunk_overlap_20_topk_4_embed_bge-large-en-v1.5.txt",
    )


def _add_standalone_environment_options(
    parser: argparse.ArgumentParser,
    *,
    provider: bool = False,
) -> None:
    """Keep framework-native launch options at that framework's boundary.

    The integrated runner already owns the live DesktopEnv, so these values are
    compatibility inputs rather than instructions to create a second VM.
    """
    parser.add_argument("--path_to_vm", "--path-to-vm", default=None)
    parser.add_argument("--snapshot_name", "--snapshot-name", default="init_state")
    if provider:
        parser.add_argument("--provider_name", "--provider-name", default="docker")
    parser.add_argument("--get_score", "--get-score", action="store_true")
    parser.add_argument(
        "--log_level",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )


def _add_gta1_options(parser: argparse.ArgumentParser) -> None:
    _add_standalone_environment_options(parser)
    _add_context_options(parser)
    parser.add_argument("--client_password", "--client-password", default="password")
    parser.add_argument("--judge_model", "--judge-model", default="o3")
    parser.add_argument("--ground_model", "--ground-model", default="gta1-7b")
    parser.add_argument("--n_samples", "--n-samples", type=int, default=8)
    parser.set_defaults(
        action_space="pyautogui",
        observation_type="screenshot",
        screen_width=1920,
        screen_height=1080,
        sleep_after_execution=0.0,
        model="o3",
        result_dir="./results/gta1_agent",
    )


def _add_agents3_options(parser: argparse.ArgumentParser) -> None:
    _add_standalone_environment_options(parser, provider=True)
    _add_context_options(parser)
    parser.add_argument("--ground_model", "--ground-model", required=True)
    parser.add_argument("--model_provider", "--model-provider", default="")
    parser.add_argument("--model_url", "--model-url", default="")
    parser.add_argument("--model_api_key", "--model-api-key", default="")
    parser.add_argument(
        "--model_temperature", "--model-temperature", type=float, default=1.0
    )
    parser.add_argument("--ground_provider", "--ground-provider", default="")
    parser.add_argument("--ground_url", "--ground-url", default="")
    parser.add_argument("--ground_api_key", "--ground-api-key", default="")
    parser.add_argument("--grounding_width", "--grounding-width", type=int, default=None)
    parser.add_argument(
        "--grounding_height", "--grounding-height", type=int, default=None
    )
    parser.add_argument(
        "--code_agent_budget", "--code-agent-budget", type=int, default=20
    )
    parser.add_argument(
        "--disable_reflection", "--disable-reflection", action="store_true"
    )
    parser.set_defaults(
        provider_name="vmware",
        action_space="pyautogui",
        observation_type="screenshot",
        screen_width=1920,
        screen_height=1080,
        max_trajectory_length=8,
        model="gpt-4o",
        result_dir="./results",
    )


def _add_planner_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--global_planner_model", "--global-planner-model", default=None
    )
    parser.add_argument(
        "--visual_grounder_model", "--visual-grounder-model", default="gta1-7b"
    )
    parser.add_argument("--state_manager_model", "--state-manager-model", default=None)
    parser.add_argument("--client_password", "--client-password", default="password")
    parser.add_argument("--wo_roi", "--wo-roi", action="store_true")
    parser.add_argument("--roi_margin", "--roi-margin", type=int, default=50)
    parser.add_argument("--refine_period", "--refine-period", type=int, default=5)
    parser.add_argument("--bash_timeout", "--bash-timeout", type=int, default=60)


def _add_locallstc_options(parser: argparse.ArgumentParser) -> None:
    _add_standalone_environment_options(parser, provider=True)
    _add_context_options(parser)
    _add_planner_options(parser)
    parser.add_argument(
        "--guest_platform",
        "--guest-platform",
        choices=["linux", "windows", "android"],
        default="windows",
    )
    parser.add_argument("--vm_ram", "--vm-ram", default="4G")
    parser.add_argument(
        "--visual_grounder_scale", "--visual-grounder-scale", type=float, default=1.0
    )
    parser.add_argument(
        "--force_refine_period", "--force-refine-period", type=int, default=20
    )
    for option in (
        "wo_l2s",
        "wo_s2l",
        "wo_cp",
        "wo_al",
        "wo_sls",
        "wo_fv",
        "wo_ps",
        "wo_sa",
        "wo_sr",
        "wo_think",
    ):
        parser.add_argument(
            "--{}".format(option),
            "--{}".format(option.replace("_", "-")),
            action="store_true",
        )
    parser.add_argument(
        "--thinking_token_budget", "--thinking-token-budget", type=int, default=None
    )
    parser.set_defaults(
        observation_type="screenshot",
        screen_width=1280,
        screen_height=720,
        sleep_after_execution=0.5,
        global_planner_model="qwen3.5-9b",
        state_manager_model="qwen3.5-9b",
        refine_period=10,
        bash_timeout=300,
        result_dir="./results/dual_agent",
    )


def _add_hisa_options(parser: argparse.ArgumentParser) -> None:
    _add_standalone_environment_options(parser, provider=True)
    _add_context_options(parser)
    _add_planner_options(parser)
    parser.add_argument("--vm_ram", "--vm-ram", default="4G")
    parser.add_argument("--wo_pattern", "--wo-pattern", action="store_true")
    parser.add_argument("--pattern_dir", "--pattern-dir", default="./qdrant_storage")
    parser.add_argument(
        "--use_qdrant_server", "--use-qdrant-server", action="store_true"
    )
    parser.add_argument(
        "--qdrant_server_url",
        "--qdrant-server-url",
        default="http://localhost:6333",
    )
    parser.add_argument("--wo_step", "--wo-step", action="store_true")
    parser.add_argument("--wo_refinement", "--wo-refinement", action="store_true")
    parser.add_argument(
        "--sliding_window_size", "--sliding-window-size", type=int, default=5
    )
    parser.set_defaults(
        observation_type="screenshot",
        screen_width=1280,
        screen_height=720,
        sleep_after_execution=0.5,
        global_planner_model="qwen3.5-9b",
        state_manager_model="qwen3.5-9b",
        bash_timeout=300,
        result_dir="./results/dual_agent",
    )


def _add_coact_options(parser: argparse.ArgumentParser) -> None:
    _add_standalone_environment_options(parser)
    _add_context_options(parser)
    parser.add_argument("--client_password", "--client-password", default="password")
    parser.add_argument(
        "--oai_config_path",
        "--oai-config-path",
        default="mm_agents/coact/OAI_CONFIG_LIST",
    )
    parser.add_argument(
        "--orchestrator_model",
        "--orchestrator-model",
        default="o3-2025-04-16",
    )
    parser.add_argument(
        "--coding_model", "--coding-model", default="o4-mini-2025-04-16"
    )
    parser.add_argument(
        "--summarizer_model", "--summarizer-model", default="o4-mini-2025-04-16"
    )
    parser.add_argument("--cua_model", "--cua-model", default="computer-use-preview")
    parser.add_argument(
        "--orchestrator_max_steps", "--orchestrator-max-steps", type=int, default=15
    )
    parser.add_argument(
        "--coding_max_steps", "--coding-max-steps", type=int, default=20
    )
    parser.add_argument("--cua_max_steps", "--cua-max-steps", type=int, default=25)
    parser.add_argument("--cut_off_steps", "--cut-off-steps", type=int, default=50)
    parser.add_argument(
        "--coact_reset_delay", "--coact-reset-delay", type=float, default=0.0
    )
    parser.add_argument("--num_envs", "--num-envs", type=int, default=1)
    parser.set_defaults(
        observation_type="screenshot",
        screen_width=1920,
        screen_height=1080,
        sleep_after_execution=0.5,
        result_dir="./results/coact_15_10_10_20",
    )


METHOD_CONFIGURERS: Dict[str, Optional[ParserConfigurer]] = {
    "navi": None,
    "claude": None,
    "gta1": _add_gta1_options,
    "agents3": _add_agents3_options,
    "locallstc": _add_locallstc_options,
    "hisa": _add_hisa_options,
    "coact": _add_coact_options,
}


def _validate_method_options(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.agent_name == "agents3":
        args.grounding_width = args.grounding_width or args.screen_width
        args.grounding_height = args.grounding_height or args.screen_height

    if args.agent_name == "locallstc":
        enabled = [
            name
            for name in (
                "wo_l2s",
                "wo_s2l",
                "wo_cp",
                "wo_al",
                "wo_sls",
                "wo_fv",
                "wo_ps",
                "wo_sa",
                "wo_sr",
            )
            if getattr(args, name)
        ]
        if len(enabled) > 1 and set(enabled) != {"wo_l2s", "wo_s2l"}:
            parser.error(
                "LocalLSTC ablation flags are mutually exclusive except "
                "--wo_l2s and --wo_s2l."
            )
        if args.global_planner_model:
            args.model = args.global_planner_model


def parse_agent_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Delegate the raw command line to the parser owned by the selected method."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    extra_args = os.environ.get("MM_AGENTS_EXTRA_ARGS", "").strip()
    if extra_args:
        extra_argv = shlex.split(extra_args)
        logger.info("Applying MM_AGENTS_EXTRA_ARGS: %s", extra_argv)
        raw_argv.extend(extra_argv)

    selected = _extract_agent_name(raw_argv)
    if selected == "locallstc":
        extra_args = os.environ.get("LOCALLSTC_EXTRA_ARGS", "").strip()
        if extra_args:
            extra_argv = shlex.split(extra_args)
            logger.info("Applying LOCALLSTC_EXTRA_ARGS: %s", extra_argv)
            raw_argv.extend(extra_argv)

    if selected not in METHOD_CONFIGURERS:
        supported = ", ".join(sorted(METHOD_CONFIGURERS))
        raise SystemExit(
            "Unknown agent {!r}. Supported agents: {}".format(selected, supported)
        )

    parser = argparse.ArgumentParser(
        description="Run {} on WindowsAgentArena".format(selected),
        allow_abbrev=False,
    )
    _add_common_options(parser)
    configure = METHOD_CONFIGURERS[selected]
    if configure is not None:
        configure(parser)

    # This is the first point at which values are interpreted or validated.
    args = parser.parse_args(raw_argv)
    args.agent_name = normalize_agent_name(args.agent_name)
    if args.agent_name != selected:
        parser.error("agent selection changed while parsing")
    prepare_framework_args(args)
    _validate_method_options(args, parser)
    return args
