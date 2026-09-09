"""Per-task logging for the Tars agent pipeline.

One shared ``tars.task`` logger backs every role. Agents receive a tagged adapter
via :func:`get_agent_logger` so log formatters can always read an ``agent`` field
without spawning child loggers that might bypass task handlers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

TURN_RULE = "-" * 72
CONTEXT_RULE = "=" * 72
_DEFAULT_AGENT_TAG = "tars"


@dataclass
class TaskLogRegistry:
    """Mutable per-task logging context (output dir, shared logger, latest screenshot)."""

    base_logger: logging.Logger | None = None
    output_dir: Path | None = None
    latest_step_shot: str = field(default="")
    trace_index: int = 0
    step: int = 0
    action_logs: list = field(default_factory=list)

    def bind(self, logger: logging.Logger, output_dir: str) -> Path:
        self.base_logger = logger
        self.output_dir = Path(output_dir)
        self.latest_step_shot = ""
        self.trace_index = 0
        self.step = 0
        self.action_logs = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "model_trace.txt").write_text(
            f"# Model Log\ntask_id: {self.output_dir.name}\ncreated_at: {datetime.now().isoformat()}\n",
            encoding="utf-8")
        return self.output_dir

    def tagged(self, agent: str) -> logging.LoggerAdapter:
        return logging.LoggerAdapter(self.base_logger, {"agent": agent})

    def png_destination(self, label: str) -> Path | None:
        if self.output_dir is None:
            return None
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        nonce = secrets.token_hex(3)
        return self.output_dir / f"{label}_{stamp}_{nonce}.png"


_registry = TaskLogRegistry()


def _sanitize_trace(value):
    if isinstance(value, str) and value.startswith("data:image/"):
        digest = hashlib.sha256(value.encode()).hexdigest()[:16]
        return f"<omitted data image url, chars={len(value)}, sha256={digest}>"
    if isinstance(value, bytes):
        return f"<omitted bytes, len={len(value)}>"
    if isinstance(value, dict):
        return {key: _sanitize_trace(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_trace(item) for item in value]
    return value


def dump_model_trace(stage, payload, *, agent, model, attempt=None):
    """Append the actual request/response at the model boundary, like LocalLSTC."""
    if _registry.output_dir is None:
        return
    _registry.trace_index += 1
    entry = dict(index=_registry.trace_index, stage=stage, agent=agent, model=model,
                 step=_registry.step, attempt=attempt, timestamp=datetime.now().isoformat(),
                 screenshot_file=_registry.latest_step_shot, payload=_sanitize_trace(payload))
    with (_registry.output_dir / "model_trace.txt").open("a", encoding="utf-8") as stream:
        stream.write(f"\n## Prompt {_registry.trace_index:04d}\n")
        stream.write(json.dumps(entry, ensure_ascii=False, indent=2, default=str) + "\n")


def __getattr__(name: str):
    # Back-compat: legacy code reads ``task_log.results_dir`` etc. on the module.
    mapping = {
        "logger": "base_logger",
        "results_dir": "output_dir",
        "last_step_screenshot_name": "latest_step_shot",
    }
    if name in mapping:
        return getattr(_registry, mapping[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _AgentTagFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "agent"):
            record.agent = _DEFAULT_AGENT_TAG
        return True


def setup_task_logger(task_logger: logging.Logger, task_result_dir: str) -> Path:
    """Wire the shared task logger and return the per-task output directory."""
    return _registry.bind(task_logger, task_result_dir)


def get_agent_logger(agent_name: str) -> logging.LoggerAdapter:
    return _registry.tagged(agent_name)


def get_last_step_screenshot_name() -> str:
    return _registry.latest_step_shot


def save_screenshot_bytes(png_bytes: bytes, label: str = "screenshot") -> str:
    if not png_bytes:
        return ""
    dest = _registry.png_destination(label)
    if dest is None:
        return ""
    dest.write_bytes(png_bytes)
    get_agent_logger(_DEFAULT_AGENT_TAG).info("Screenshot saved: %s", dest)
    return str(dest)


def save_screenshot(screenshot_b64: str, step_idx: int) -> str:
    _registry.step = step_idx
    if not screenshot_b64:
        return ""
    written = save_screenshot_bytes(base64.b64decode(screenshot_b64), label=f"step_{step_idx}")
    if written:
        _registry.latest_step_shot = Path(written).name
    return written


class _TurnRecorder:
    """Formats one LLM turn (thinking, tools, results) into structured log lines."""

    def __init__(self, sink: logging.LoggerAdapter) -> None:
        self._sink = sink

    @classmethod
    def for_agent(cls, agent_name: str) -> _TurnRecorder:
        return cls(get_agent_logger(agent_name))

    def record(
        self,
        *,
        thinking_blocks: Iterable[Any],
        text_blocks: Iterable[Any],
        tool_calls: Iterable[dict],
        tool_results: Iterable[tuple[str, Any]],
        agent_action: Any,
    ) -> None:
        self._sink.info(TURN_RULE)
        for block in thinking_blocks:
            self._sink.info("Thinking: %s", block)
        for block in text_blocks:
            self._sink.info("Text: %s", block)
        for call in tool_calls:
            self._sink.info("Tool call [%s][%s]: %s", call["id"], call["name"], call["input"])
        for tool_id, payload in tool_results:
            self._sink.info(
                "Tool call [%s]:\nRESULT:\n%s\nERROR:\n%s",
                tool_id,
                getattr(payload, "output", None),
                getattr(payload, "error", None),
            )
        self._sink.info("Agent action:\n%s", agent_action)
        self._sink.info("")


def log_agent_api_call(
    agent_name: str,
    tool_calls: list,
    thinking_blocks: list,
    text_blocks: list,
    tool_call_results: list,
    agent_action: str,
) -> None:
    results = dict(tool_call_results)
    for call in tool_calls:
        result = results.get(call["id"])
        payload = asdict(result) if is_dataclass(result) else result
        if isinstance(payload, dict):
            payload = dict(payload)
            if payload.get("base64_data"):
                payload["base64_data"] = "<image omitted; see screenshot logs>"
        name = call["name"]
        if name in {"click", "type", "scroll", "drag_and_drop", "hotkey", "hold_and_press"}:
            kind = "gui_action"
        elif name in {"run_python", "run_bash", "probe_python", "probe_bash", "run_background", "install_package"}:
            kind = "bash_execution"
        elif name == "wait":
            kind = "wait"
        elif name in {"done", "fail", "report_feasible", "report_infeasible", "select_skills", "submit_plan",
                      "mark_milestone_done", "set_sub_milestones", "mark_sub_milestone_done",
                      "add_milestone", "delete_milestone", "update_milestone"}:
            kind = "planning"
        else:
            kind = "api"
        pending = agent_name == "executor" and isinstance(agent_action, str) and kind == "gui_action"
        _registry.action_logs.append(dict(
            step=len(_registry.action_logs) + 1, harness_step=_registry.step,
            type=kind, tool=name, agent=agent_name, tool_call_id=call["id"],
            input=call["input"], detail=payload, thought="\n".join(text_blocks),
            thinking="\n".join(thinking_blocks), screenshot=_registry.latest_step_shot,
            execution_success=None if pending else not bool(isinstance(payload, dict) and payload.get("error")),
            pending=pending, timestamp=datetime.now().isoformat()))
    _TurnRecorder.for_agent(agent_name).record(
        thinking_blocks=thinking_blocks,
        text_blocks=text_blocks,
        tool_calls=tool_calls,
        tool_results=tool_call_results,
        agent_action=agent_action,
    )


class _ContextSnapshotWriter:
    FILENAME = "full_context.log"

    @staticmethod
    def _header(
        *,
        agent_name: str,
        model: str,
        attempt: int,
        message_count: int,
    ) -> str:
        ts = datetime.now().isoformat(timespec="seconds")
        return (
            f"{CONTEXT_RULE}\n"
            f"API request | {ts} | agent={agent_name} model={model} "
            f"attempt={attempt} message_count={message_count}\n"
        )

    @classmethod
    def compose(
        cls,
        *,
        agent_name: str,
        model: str,
        attempt: int,
        message_count: int,
        system_prompt: str,
        messages_text: str,
    ) -> str:
        head = cls._header(
            agent_name=agent_name,
            model=model,
            attempt=attempt,
            message_count=message_count,
        )
        return f"{head}--- SYSTEM ---\n{system_prompt}\n--- MESSAGES ---\n{messages_text}\n\n"

    @classmethod
    def append(cls, body: str) -> None:
        if _registry.output_dir is None:
            return
        path = _registry.output_dir / cls.FILENAME
        with path.open("a", encoding="utf-8") as handle:
            handle.write(body)


def append_full_context_log(
    agent_name: str,
    *,
    model: str,
    attempt: int,
    message_count: int,
    system_prompt: str,
    messages_text: str,
) -> None:
    """Append a full (untruncated) API request snapshot to the task's full_context.log."""
    snapshot = _ContextSnapshotWriter.compose(
        agent_name=agent_name,
        model=model,
        attempt=attempt,
        message_count=message_count,
        system_prompt=system_prompt,
        messages_text=messages_text,
    )
    _ContextSnapshotWriter.append(snapshot)
