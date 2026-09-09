"""WindowsAgentArena lifecycle for TARS: gate, planner, executor, grounding."""

import json
import logging
from pathlib import Path
import time


class TARS:
    def __init__(self, env, save_dir, max_steps=100, screen_width=1280,
                 screen_height=720, sleep_after_execution=0.5, record=False,
                 global_planner_model="qwen3.8-27b", visual_grounder_model="gta1-7b",
                 reset_wait=60, evaluation_wait=20):
        self.env, self.save_dir = env, Path(save_dir)
        if max_steps <= 0 or min(reset_wait, evaluation_wait, sleep_after_execution) < 0:
            raise ValueError("max_steps must be positive and waits must be nonnegative")
        if min(screen_width, screen_height) <= 0:
            raise ValueError("Screen dimensions must be positive")
        self.max_steps = max_steps
        self.screen_size = (screen_width, screen_height)
        self.pause, self.record = sleep_after_execution, record
        self.reset_wait, self.evaluation_wait = reset_wait, evaluation_wait
        self.planner_model, self.grounder_model = global_planner_model, visual_grounder_model
        self.logger = logging.getLogger("desktopenv.tars")
        self.recording, self.agent = False, None

    def execute_task(self, task_config):
        from .core import config as config_module
        from dataclasses import replace
        import os
        # Roles share the same immutable config snapshot, set before their import.
        config_module.config = replace(config_module.config,
            gate_model=self.planner_model, planner_model=self.planner_model,
            executor_model=self.planner_model, summarization_model=self.planner_model)
        from .roles import probing, executor
        from . import agent as agent_module
        for module in (probing, executor, agent_module):
            module.config = config_module.config
        os.environ["TARS_GROUNDER_MODEL"] = self.grounder_model
        from .runtime.eval_hooks import evaluate_tars
        from .runtime import task_log

        self.save_dir.mkdir(parents=True, exist_ok=True)
        (self.save_dir / "config.json").write_text(json.dumps(task_config, ensure_ascii=False, indent=2), encoding="utf-8")
        started, actions_log, score = time.monotonic(), [], None
        failure_reason = ""
        task_log._registry.action_logs = []
        try:
            self.env.reset(task_config=task_config)
            self.agent = agent_module.TarsAgent(self.env, screen_size=self.screen_size)
            self.agent.reset(task_config["instruction"], self.logger, str(self.save_dir))
            time.sleep(self.reset_wait)
            obs = self.env._get_obs()
            if self.record:
                self.env.controller.start_recording()
                self.recording = True
            for step in range(self.max_steps):
                response, actions = self.agent.predict(obs)
                if not actions:
                    raise RuntimeError("TARS returned no actions")
                for action in actions:
                    action_started = time.monotonic()
                    pending = next((entry for entry in reversed(task_log._registry.action_logs)
                                    if entry.get("pending")), None)
                    if pending is None:
                        control = action.get("action_type") if isinstance(action, dict) else action
                        kind = {"WAIT": "wait", "DONE": "termination", "FAIL": "infeasible"}.get(
                            control, "gui_action")
                        pending = dict(step=len(task_log._registry.action_logs) + 1,
                            harness_step=step + 1, type=kind, agent="harness", detail=response,
                            screenshot=task_log.get_last_step_screenshot_name())
                        task_log._registry.action_logs.append(pending)
                    pending.update(action=action, execution_success=False, pending=False)
                    try:
                        obs, reward, done, info = self.env.step(action, self.pause)
                    except Exception as exc:
                        pending["error"] = str(exc)
                        raise
                    finally:
                        pending["step_time"] = time.monotonic() - action_started
                    pending.update(execution_success=True, done=done, info=info)
                    entry = dict(step_num=step + 1, action=action, response=response, done=done, info=info)
                    actions_log.append(entry)
                    with (self.save_dir / "traj.jsonl").open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
                    if done:
                        break
                if done:
                    break
            time.sleep(self.evaluation_wait)
            score = evaluate_tars(self.env)
            self.agent.log_usage()
            (self.save_dir / "result.txt").write_text(str(score), encoding="utf-8")
            return score
        except Exception as exc:
            failure_reason = str(exc)
            raise
        finally:
            entries = task_log._registry.action_logs
            from collections import Counter
            counts = Counter(entry["type"] for entry in entries)
            stats = dict(score=score, total_steps=len(entries), harness_steps=len(actions_log),
                         cua_steps=counts["gui_action"], api_steps=counts["api"],
                         coding_steps=counts["bash_execution"], wait_steps=counts["wait"],
                         termination_steps=counts["termination"], infeasible_steps=counts["infeasible"],
                         other_steps=counts["planning"] + counts["wait"] + counts["termination"] + counts["infeasible"],
                         execution_time=time.monotonic() - started,
                         total_cost=0, prompt_tokens=0, completion_tokens=0, image_count=0,
                         model_usage={})
            for role in ("skill_gate", "task_planner", "task_runner"):
                session = getattr(getattr(self.agent, role, None), "llm", None)
                for label, client in ((role, getattr(session, "client", None)),
                                      (role + "_grounder", getattr(session, "grounder", None))):
                    if client is not None:
                        cost, inputs, outputs, images = client.get_usage()
                        stats["model_usage"][label] = dict(model_name=client.model_name, cost=cost,
                            prompt_tokens=inputs, completion_tokens=outputs, image_count=images)
                        for key, value in zip(("total_cost", "prompt_tokens", "completion_tokens", "image_count"),
                                              (cost, inputs, outputs, images)):
                            stats[key] += value
            if not failure_reason and score != 1.0:
                failure_reason = "Task marked infeasible" if counts["infeasible"] else (
                    "Maximum steps reached" if not counts["termination"] else "Evaluation did not pass")
            log = {"score": score, "task_config": task_config, "additional_context": "",
                   "success": score == 1.0, "failure_reason": failure_reason,
                   "action_logs": entries, "harness_actions": actions_log, "statistics": stats,
                   "statistics_note": "Each role tool call and harness-only control action is one step; executor GUI dispatch and execution share one entry. Planning tools count as other_steps."}
            try:
                (self.save_dir / "execution_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            finally:
                self.cleanup()

    def cleanup(self):
        if self.recording:
            self.recording = False
            try:
                self.env.controller.end_recording(str(self.save_dir / "recording.mp4"))
            except Exception:
                self.logger.exception("Failed to stop recording")
