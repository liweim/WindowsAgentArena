#!/usr/bin/env python3
"""Analyze LocalLSTC2 result directories and JEV routing behavior.

Examples:
    python paper/analyze.py
    python paper/analyze.py results/locallstc2_qwen3.8-27b_2
    python paper/analyze.py RESULTS --baseline BASELINE
    python paper/analyze.py RESULTS --baseline BASELINE --json

The API-routing labels are behavioral proxies: an API candidate is positive when
the planner actually emits that method in the action list following the JEV
decision.  This measures routing alignment, not semantic ground-truth utility.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = REPO_ROOT / "results" / "locallstc2_qwen3.8-27b_2"
DEFAULT_BASELINE = REPO_ROOT / "results" / "locallstc2_qwen3.8-27b"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
TASK_ID_RE = re.compile(r"\[Example ID\]:\s*(\S+)")
API_SCORE_RE = re.compile(
    r"\[jev_api_scores\] subgoal=(.*?) threshold=([0-9.]+) scores=(\{[^\n]+\})"
)
API_SELECTED_RE = re.compile(r"\[jev_api\] selected=([^\n]+)")
ACTIONS_RE = re.compile(r'"actions"\s*:\s*\[([\s\S]*?)\]')
STEP_RE = re.compile(r"Step (\d+)/\d+")
MEMORY_RE = re.compile(
    r"\[jev_memory\] selected=A(\d+) start_step=(\d+) p=([^\s]+)"
)


def safe_number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def nested(data: dict[str, Any], *keys: str, default: Any = 0) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def percentile(values: Iterable[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = math.floor((len(ordered) - 1) * fraction)
    return ordered[index]


def mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def load_tasks(result_dir: Path) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(result_dir.glob("*/*/execution_log.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        task_id = str(nested(data, "task_config", "id", default=path.parent.name))
        data["__path"] = str(path)
        tasks[task_id] = data
    if not tasks:
        raise FileNotFoundError(f"No execution_log.json files found under {result_dir}")
    return tasks


def load_summary(result_dir: Path) -> dict[str, Any]:
    path = result_dir / "summary.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle).get("summary", {})


def latest_debug_logs(result_dir: Path) -> dict[str, tuple[Path, str]]:
    """Return the newest debug log for each explicit Example ID."""
    selected: dict[str, tuple[Path, str]] = {}
    for path in sorted((result_dir / "logs").glob("debug-*.log")):
        text = ANSI_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
        match = TASK_ID_RE.search(text)
        if match:
            selected[match.group(1)] = (path, text)
    return selected


def aggregate_run(
    result_dir: Path, tasks: dict[str, dict[str, Any]], summary: dict[str, Any]
) -> dict[str, Any]:
    stats = [task.get("statistics", {}) for task in tasks.values()]
    scores = [safe_number(item.get("score")) for item in stats]
    steps = [safe_number(item.get("total_steps")) for item in stats]
    execution = [safe_number(item.get("execution_time")) for item in stats]
    planner_seconds = [
        safe_number(nested(item, "latency", "global_planner_seconds")) for item in stats
    ]
    memory_seconds = [
        safe_number(nested(item, "latency", "jev_memory_seconds")) for item in stats
    ]
    api_seconds = [
        safe_number(nested(item, "latency", "jev_api_seconds")) for item in stats
    ]
    jev_seconds = [a + b for a, b in zip(memory_seconds, api_seconds)]

    score_counts = Counter(scores)
    total_execution = sum(execution)
    total_planner_seconds = sum(planner_seconds)
    total_jev_seconds = sum(jev_seconds)
    planner_prompt = sum(
        safe_number(nested(item, "model_usage", "global_planner", "prompt_tokens"))
        for item in stats
    )
    planner_completion = sum(
        safe_number(nested(item, "model_usage", "global_planner", "completion_tokens"))
        for item in stats
    )
    jev_prompt = sum(
        safe_number(nested(item, "model_usage", "jev", "prompt_tokens"))
        for item in stats
    )
    jev_requests = sum(
        safe_number(nested(item, "model_usage", "jev", "request_count"))
        for item in stats
    )

    return {
        "path": str(result_dir),
        "tasks": len(tasks),
        "task_outcome_percent": safe_number(summary.get("task_outcome"), mean(scores) * 100),
        "success_rate_percent": safe_number(summary.get("success_rate"), mean(scores) * 100),
        "access_requirement_percent": safe_number(summary.get("access_requirement")),
        "mean_execution_score": mean(scores),
        "full_successes": sum(score == 1.0 for score in scores),
        "zero_scores": sum(score == 0.0 for score in scores),
        "score_distribution": [
            {"score": score, "count": score_counts[score]} for score in sorted(score_counts)
        ],
        "steps": int(sum(steps)),
        "mean_steps": mean(steps),
        "cua_steps": int(sum(safe_number(item.get("cua_steps")) for item in stats)),
        "api_steps": int(sum(safe_number(item.get("api_steps")) for item in stats)),
        "code_steps": int(sum(safe_number(item.get("coding_steps")) for item in stats)),
        "execution_seconds": total_execution,
        "mean_execution_seconds": mean(execution),
        "prompt_tokens": int(sum(safe_number(item.get("prompt_tokens")) for item in stats)),
        "completion_tokens": int(sum(safe_number(item.get("completion_tokens")) for item in stats)),
        "planner_prompt_tokens": int(planner_prompt),
        "planner_completion_tokens": int(planner_completion),
        "planner_total_tokens": int(planner_prompt + planner_completion),
        "jev_prompt_tokens": int(jev_prompt),
        "jev_requests": int(jev_requests),
        "planner_seconds": total_planner_seconds,
        "jev_memory_seconds": sum(memory_seconds),
        "jev_api_seconds": sum(api_seconds),
        "jev_total_seconds": total_jev_seconds,
        "jev_mean_seconds_per_task": mean(jev_seconds),
        "jev_p50_seconds_per_task": percentile(jev_seconds, 0.50),
        "jev_p90_seconds_per_task": percentile(jev_seconds, 0.90),
        "jev_p95_seconds_per_task": percentile(jev_seconds, 0.95),
        "jev_max_seconds_per_task": max(jev_seconds, default=0.0),
        "jev_mean_seconds_per_request": (
            total_jev_seconds / jev_requests if jev_requests else 0.0
        ),
        "jev_share_execution_percent": (
            total_jev_seconds / total_execution * 100 if total_execution else 0.0
        ),
        "jev_share_planner_percent": (
            total_jev_seconds / total_planner_seconds * 100
            if total_planner_seconds
            else 0.0
        ),
    }


def auroc(score_labels: list[tuple[float, bool]]) -> float | None:
    """Compute AUROC with average ranks for tied scores."""
    positives = sum(label for _, label in score_labels)
    negatives = len(score_labels) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(score_labels, key=lambda item: item[0])
    positive_rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        positive_rank_sum += average_rank * sum(label for _, label in ordered[index:end])
        index = end
    return (
        positive_rank_sum - positives * (positives + 1) / 2
    ) / (positives * negatives)


def classification_metrics(
    score_labels: list[tuple[float, bool]], threshold: float
) -> dict[str, Any]:
    tp = sum(score >= threshold and label for score, label in score_labels)
    fp = sum(score >= threshold and not label for score, label in score_labels)
    fn = sum(score < threshold and label for score, label in score_labels)
    tn = sum(score < threshold and not label for score, label in score_labels)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2,
        "f1": f1,
        "selected": tp + fp,
        "selection_rate": (tp + fp) / len(score_labels) if score_labels else 0.0,
    }


def parse_jev_logs(
    result_dir: Path,
    task_ids: set[str],
    requested_thresholds: list[float],
) -> dict[str, Any]:
    logs = latest_debug_logs(result_dir)
    api_events: list[dict[str, Any]] = []
    memory_events: list[dict[str, Any]] = []
    fallbacks = Counter()
    observed_thresholds = Counter()

    for task_id, (_, text) in logs.items():
        if task_id not in task_ids:
            continue
        fallbacks["api"] += text.count("[jev_fallback] api")
        fallbacks["memory"] += text.count("[jev_fallback] memory")
        matches = list(API_SCORE_RE.finditer(text))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            segment = text[match.end() : end]
            scores = json.loads(match.group(3))
            threshold = float(match.group(2))
            observed_thresholds[threshold] += 1
            selected_match = API_SELECTED_RE.search(segment)
            selected_text = selected_match.group(1).strip() if selected_match else "NONE"
            selected = [] if selected_text == "NONE" else selected_text.split(",")
            action_arrays = ACTIONS_RE.findall(segment)
            immediate_actions = action_arrays[0] if action_arrays else ""
            used = [
                name
                for name in scores
                if re.search(re.escape(name) + r"\s*\(", immediate_actions)
            ]
            api_events.append(
                {
                    "task": task_id,
                    "subgoal": match.group(1),
                    "threshold": threshold,
                    "scores": scores,
                    "selected": selected,
                    "used": used,
                }
            )

        current_step: int | None = None
        for line in text.splitlines():
            step_match = STEP_RE.search(line)
            if step_match:
                current_step = int(step_match.group(1))
            memory_match = MEMORY_RE.search(line)
            if memory_match:
                start_step = int(memory_match.group(2))
                memory_events.append(
                    {
                        "task": task_id,
                        "decision_step": current_step,
                        "anchor": int(memory_match.group(1)),
                        "start_step": start_step,
                        "omitted_prior_steps": max(0, start_step - 1),
                        "confidence": float(memory_match.group(3)),
                    }
                )

    score_labels = [
        (float(score), name in event["used"])
        for event in api_events
        for name, score in event["scores"].items()
    ]
    thresholds = sorted(set(requested_thresholds) | set(observed_thresholds))
    threshold_metrics = [classification_metrics(score_labels, value) for value in thresholds]
    grid = [classification_metrics(score_labels, value / 100) for value in range(1, 100)]
    actual_selected = sum(len(event["selected"]) for event in api_events)
    actual_used = sum(len(event["used"]) for event in api_events)
    actual_tp = sum(
        len(set(event["selected"]) & set(event["used"])) for event in api_events
    )
    false_negatives = [
        {
            "task": event["task"],
            "subgoal": event["subgoal"],
            "method": method,
            "score": event["scores"][method],
        }
        for event in api_events
        for method in sorted(set(event["used"]) - set(event["selected"]))
    ]
    memory_confidences = [event["confidence"] for event in memory_events]
    omitted_steps = [event["omitted_prior_steps"] for event in memory_events]

    return {
        "matched_debug_logs": len(set(logs) & task_ids),
        "api_events": len(api_events),
        "candidate_instances": len(score_labels),
        "actual_selected_instances": actual_selected,
        "actual_selection_rate": actual_selected / len(score_labels) if score_labels else 0.0,
        "none_events": sum(not event["selected"] for event in api_events),
        "multi_select_events": sum(len(event["selected"]) > 1 for event in api_events),
        "planner_api_uses": actual_used,
        "actual_tp": actual_tp,
        "actual_fp": actual_selected - actual_tp,
        "actual_fn": actual_used - actual_tp,
        "auroc": auroc(score_labels),
        "observed_thresholds": dict(sorted(observed_thresholds.items())),
        "threshold_metrics": threshold_metrics,
        "best_f1_on_0.01_grid": max(grid, key=lambda item: item["f1"]) if grid else {},
        "best_balanced_accuracy_on_0.01_grid": (
            max(grid, key=lambda item: item["balanced_accuracy"]) if grid else {}
        ),
        "false_negatives": false_negatives,
        "api_fallbacks": fallbacks["api"],
        "memory_events": len(memory_events),
        "memory_mean_confidence": mean(memory_confidences),
        "memory_median_confidence": percentile(memory_confidences, 0.50),
        "memory_mean_omitted_prior_steps": mean(omitted_steps),
        "memory_total_omitted_prior_steps": int(sum(omitted_steps)),
        "memory_fallbacks": fallbacks["memory"],
    }


def exact_mcnemar_p(improved: int, regressed: int) -> float:
    discordant = improved + regressed
    if not discordant:
        return 1.0
    tail = min(improved, regressed)
    probability = sum(math.comb(discordant, value) for value in range(tail + 1))
    return min(1.0, 2 * probability / (2**discordant))


def compare_runs(
    baseline_tasks: dict[str, dict[str, Any]], current_tasks: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    shared = sorted(set(baseline_tasks) & set(current_tasks))
    rows = []
    for task_id in shared:
        old_stats = baseline_tasks[task_id].get("statistics", {})
        new_stats = current_tasks[task_id].get("statistics", {})
        old_score = safe_number(old_stats.get("score"))
        new_score = safe_number(new_stats.get("score"))
        rows.append(
            {
                "task": task_id,
                "baseline_score": old_score,
                "current_score": new_score,
                "delta": new_score - old_score,
                "baseline_steps": int(safe_number(old_stats.get("total_steps"))),
                "current_steps": int(safe_number(new_stats.get("total_steps"))),
            }
        )
    improved = [row for row in rows if row["delta"] > 0]
    regressed = [row for row in rows if row["delta"] < 0]
    pass_gains = sum(
        row["baseline_score"] != 1.0 and row["current_score"] == 1.0 for row in rows
    )
    pass_losses = sum(
        row["baseline_score"] == 1.0 and row["current_score"] != 1.0 for row in rows
    )
    return {
        "shared_tasks": len(shared),
        "mean_score_delta": mean(row["delta"] for row in rows),
        "improved_count": len(improved),
        "regressed_count": len(regressed),
        "unchanged_count": len(rows) - len(improved) - len(regressed),
        "pass_gains": pass_gains,
        "pass_losses": pass_losses,
        "mcnemar_exact_p": exact_mcnemar_p(pass_gains, pass_losses),
        "improved": improved,
        "regressed": regressed,
    }


def percentage_delta(current: float, baseline: float) -> float:
    return (current / baseline - 1) * 100 if baseline else 0.0


def print_run(title: str, run: dict[str, Any], jev: dict[str, Any]) -> None:
    print(f"\n{title}")
    print("=" * len(title))
    print(f"Directory: {run['path']}")
    print(
        f"Tasks: {run['tasks']} | task outcome: {run['task_outcome_percent']:.2f}% | "
        f"success: {run['success_rate_percent']:.2f}% | full/zero: "
        f"{run['full_successes']}/{run['zero_scores']}"
    )
    print(
        f"Steps: {run['steps']} ({run['mean_steps']:.2f}/task) | "
        f"API steps: {run['api_steps']} | execution: {run['execution_seconds']:.2f}s"
    )
    print(
        f"Planner tokens: {run['planner_total_tokens']:,} "
        f"({run['planner_prompt_tokens']:,} prompt + "
        f"{run['planner_completion_tokens']:,} completion)"
    )
    print(
        f"JEV: {run['jev_requests']} requests, {run['jev_prompt_tokens']:,} prompt tokens, "
        f"{run['jev_total_seconds']:.2f}s total ({run['jev_api_seconds']:.2f}s API + "
        f"{run['jev_memory_seconds']:.2f}s memory)"
    )
    print(
        f"JEV latency/task: mean={run['jev_mean_seconds_per_task']:.2f}s, "
        f"p50={run['jev_p50_seconds_per_task']:.2f}s, "
        f"p90={run['jev_p90_seconds_per_task']:.2f}s, "
        f"p95={run['jev_p95_seconds_per_task']:.2f}s, "
        f"max={run['jev_max_seconds_per_task']:.2f}s"
    )
    print(
        f"JEV share: {run['jev_share_execution_percent']:.3f}% of execution time; "
        f"{run['jev_share_planner_percent']:.3f}% of planner time; "
        f"{run['jev_mean_seconds_per_request']:.3f}s/request"
    )

    print("\nJEV API routing")
    print(
        f"Matched logs/events: {jev['matched_debug_logs']}/{jev['api_events']} | "
        f"candidate instances: {jev['candidate_instances']:,} | "
        f"selected: {jev['actual_selected_instances']:,} "
        f"({jev['actual_selection_rate'] * 100:.2f}%)"
    )
    print(
        f"Planner API uses: {jev['planner_api_uses']} | TP/FP/FN: "
        f"{jev['actual_tp']}/{jev['actual_fp']}/{jev['actual_fn']} | "
        f"AUROC: {jev['auroc']:.4f}" if jev["auroc"] is not None else "AUROC: n/a"
    )
    for metrics in jev["threshold_metrics"]:
        print(
            f"  threshold={metrics['threshold']:.2f}: "
            f"precision={metrics['precision'] * 100:.2f}%, "
            f"recall={metrics['recall'] * 100:.2f}%, "
            f"balanced_acc={metrics['balanced_accuracy'] * 100:.2f}%, "
            f"selected={metrics['selected']} ({metrics['selection_rate'] * 100:.2f}%)"
        )
    best = jev["best_balanced_accuracy_on_0.01_grid"]
    if best:
        print(
            f"  best balanced-accuracy threshold on 0.01 grid: {best['threshold']:.2f} "
            f"(recall={best['recall'] * 100:.2f}%, "
            f"balanced_acc={best['balanced_accuracy'] * 100:.2f}%)"
        )
    print(
        f"Memory JEV: {jev['memory_events']} decisions, "
        f"mean confidence={jev['memory_mean_confidence']:.3f}, "
        f"mean omitted prior steps={jev['memory_mean_omitted_prior_steps']:.2f}, "
        f"fallbacks={jev['memory_fallbacks']}"
    )
    if jev["false_negatives"]:
        print("False negatives:")
        for item in jev["false_negatives"]:
            print(
                f"  {item['task']}: {item['method']} score={item['score']:.4f} "
                f"subgoal={item['subgoal']}"
            )


def print_comparison(
    baseline: dict[str, Any], current: dict[str, Any], paired: dict[str, Any]
) -> None:
    print("\nPaired comparison")
    print("=================")
    fields = [
        ("task outcome", "task_outcome_percent", "pp"),
        ("full successes", "full_successes", "count"),
        ("steps", "steps", "relative"),
        ("execution seconds", "execution_seconds", "relative"),
        ("planner prompt tokens", "planner_prompt_tokens", "relative"),
        ("planner completion tokens", "planner_completion_tokens", "relative"),
        ("JEV prompt tokens", "jev_prompt_tokens", "relative"),
        ("JEV requests", "jev_requests", "relative"),
        ("JEV seconds", "jev_total_seconds", "relative"),
    ]
    for label, key, kind in fields:
        old = baseline[key]
        new = current[key]
        if kind == "pp":
            delta = f"{new - old:+.2f} pp"
        elif kind == "count":
            delta = f"{int(new - old):+d}"
        else:
            delta = f"{percentage_delta(new, old):+.2f}%"
        print(f"{label:27s} {old:>12,.2f} -> {new:>12,.2f}  ({delta})")
    print(
        f"Task transitions: improved={paired['improved_count']}, "
        f"regressed={paired['regressed_count']}, unchanged={paired['unchanged_count']}"
    )
    print(
        f"Full-pass transitions: gain={paired['pass_gains']}, loss={paired['pass_losses']}, "
        f"exact McNemar p={paired['mcnemar_exact_p']:.4f}"
    )
    if paired["improved"]:
        print("Improved tasks:")
        for row in paired["improved"]:
            print(
                f"  {row['task']}: {row['baseline_score']:.4f} -> "
                f"{row['current_score']:.4f}; steps "
                f"{row['baseline_steps']} -> {row['current_steps']}"
            )
    if paired["regressed"]:
        print("Regressed tasks:")
        for row in paired["regressed"]:
            print(
                f"  {row['task']}: {row['baseline_score']:.4f} -> "
                f"{row['current_score']:.4f}; steps "
                f"{row['baseline_steps']} -> {row['current_steps']}"
            )


def parse_thresholds(raw: str) -> list[float]:
    values = []
    for item in raw.split(","):
        value = float(item.strip())
        if not 0 <= value <= 1:
            raise argparse.ArgumentTypeError("thresholds must be within [0, 1]")
        values.append(value)
    return values


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "result_dir",
        nargs="?",
        default=str(DEFAULT_RESULT),
        help="Result directory to analyze (default: latest qwen3.8-27b_2 run)",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Optional baseline result directory; pass an empty string to disable",
    )
    parser.add_argument(
        "--thresholds",
        type=parse_thresholds,
        default=parse_thresholds("0.08,0.10,0.20,0.30,0.40,0.50,0.60"),
        help="Comma-separated thresholds to report",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    result_dir = resolve_path(args.result_dir)
    current_tasks = load_tasks(result_dir)
    current_run = aggregate_run(result_dir, current_tasks, load_summary(result_dir))
    current_jev = parse_jev_logs(result_dir, set(current_tasks), args.thresholds)
    output: dict[str, Any] = {"current": current_run, "current_jev": current_jev}

    baseline_run = None
    baseline_jev = None
    paired = None
    if args.baseline:
        baseline_dir = resolve_path(args.baseline)
        baseline_tasks = load_tasks(baseline_dir)
        baseline_run = aggregate_run(
            baseline_dir, baseline_tasks, load_summary(baseline_dir)
        )
        baseline_jev = parse_jev_logs(baseline_dir, set(baseline_tasks), args.thresholds)
        paired = compare_runs(baseline_tasks, current_tasks)
        output.update(
            {
                "baseline": baseline_run,
                "baseline_jev": baseline_jev,
                "paired": paired,
            }
        )

    if args.json:
        json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        if baseline_run is not None and baseline_jev is not None:
            print_run("Baseline run", baseline_run, baseline_jev)
        print_run("Current run", current_run, current_jev)
        if baseline_run is not None and paired is not None:
            print_comparison(baseline_run, current_run, paired)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
