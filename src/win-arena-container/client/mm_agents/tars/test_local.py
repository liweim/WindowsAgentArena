"""Offline integration checks: python -m unittest mm_agents.tars.test_local."""

import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from mm_agents.tars.main import TARS
from mm_agents.tars.core.local_session import LLMClient, normalize_grounded_point


def reply(name, **inputs):
    return json.dumps({"thought": "test", "tool_calls": [{"name": name, "input": inputs}]})


class FakeLLM:
    responses = []
    models = []
    def __init__(self, model, **kwargs):
        self.model_name = model
        self.models.append(model)
    def __call__(self, messages, **kwargs):
        return self.responses.pop(0)
    def call_cua(self, description, image, **kwargs):
        assert description == "Save button"
        assert kwargs["environment"] == "windows"
        return (320, 180), "located"
    def get_usage(self):
        return (0, 10, 5, 1)


class LocalTarsTests(unittest.TestCase):
    def test_grounder_bounds(self):
        self.assertEqual(normalize_grounded_point((320, 180)), [320, 180])
        for point in ((1283, 90), (-2, 721), (1400, 90), (10, float("nan")), (True, 0), None):
            with self.subTest(point=point), self.assertRaises(ValueError):
                normalize_grounded_point(point)

    @patch("mm_agents.tars.core.local_session.AbstractLLM", FakeLLM)
    def test_large_overshoot_retries(self):
        from mm_agents.tars.toolkit.schemas import CLICK
        FakeLLM.responses = [reply("click", target="Save button")] * 2
        session = LLMClient("test", "test", [CLICK.schema], "qwen3.8-27b")
        session.add_user_message("Save", [base64.b64encode(self.png).decode()])
        with patch.object(FakeLLM, "call_cua", side_effect=[((1400, 90), ""), ((320, 180), "")]):
            calls, _, _, _ = session.generate_and_process()
        self.assertEqual(calls[0]["input"]["coordinate"], [320, 180])

    def setUp(self):
        from mm_agents.tars.runtime import task_log
        registry_patch = patch.object(task_log, "_registry", task_log.TaskLogRegistry())
        registry_patch.start()
        self.addCleanup(registry_patch.stop)
        buffer = io.BytesIO()
        Image.new("RGB", (1280, 720)).save(buffer, format="PNG")
        self.png = buffer.getvalue()
        FakeLLM.models = []

    @patch("mm_agents.tars.core.local_session.AbstractLLM", FakeLLM)
    def test_grounding_and_invalid_response_retry(self):
        from mm_agents.tars.toolkit.schemas import CLICK
        FakeLLM.responses = [reply("unknown"), reply("click", target="Save button")]
        session = LLMClient("test", "test", [CLICK.schema], "qwen3.8-27b")
        session.add_user_message("Save", [base64.b64encode(self.png).decode()])
        calls, _, _, _ = session.generate_and_process()
        self.assertEqual(calls[0]["input"]["coordinate"], [320, 180])
        self.assertIn("gta1-7b", FakeLLM.models)
        self.assertIn("coordinate", CLICK.schema["input_schema"]["properties"])

    @patch("mm_agents.tars.core.local_session.AbstractLLM", FakeLLM)
    @patch("mm_agents.tars.agent.probe_app_versions", return_value=[])
    def test_full_role_lifecycle(self, probe):
        FakeLLM.responses = [reply("select_skills", selected_skills=["skill-os"]),
                             reply("report_feasible", reason='### Skill basis\n- [skill-os] "Use GUI"'),
                             reply("submit_plan", milestones=["Save"]),
                             reply("click", target="Save button"),
                             reply("done", summary="Saved")]
        test = self
        class Env:
            client_password = "password"
            provider_name = "docker"
            evaluator = {}
            def reset(self, task_config):
                self.actions = []
            def _get_obs(self):
                return {"screenshot": test.png}
            def step(self, action, pause):
                self.actions.append(action)
                return self._get_obs(), 0, action == "DONE", {}
            def evaluate(self):
                return 1.0
        with tempfile.TemporaryDirectory() as directory:
            env = Env()
            task = TARS(env, directory, max_steps=5, screen_width=1920, screen_height=1080,
                        reset_wait=0, evaluation_wait=0)
            self.assertEqual(task.execute_task({"id": "test", "instruction": "Save"}), 1.0)
            self.assertIn("x=480, y=270", env.actions[0])
            log = json.loads((Path(directory) / "execution_log.json").read_text())
            self.assertEqual(log["statistics"]["cua_steps"], 1)
            self.assertEqual(log["statistics"]["harness_steps"], 3)
            self.assertEqual(log["statistics"]["total_steps"], 7)
            self.assertEqual(len(log["action_logs"]), 7)
            self.assertEqual(log["statistics"]["score"], 1.0)
            self.assertTrue(log["success"])
            self.assertEqual(log["failure_reason"], "")
            self.assertEqual(log["task_config"]["instruction"], "Save")
            gui = [entry for entry in log["action_logs"] if entry["type"] == "gui_action"]
            self.assertEqual(len(gui), 1)
            self.assertTrue(gui[0]["execution_success"])
            self.assertIn("x=480, y=270", gui[0]["action"])
            self.assertEqual(log["statistics"]["prompt_tokens"], sum(
                usage["prompt_tokens"] for usage in log["statistics"]["model_usage"].values()))
            self.assertEqual(set(FakeLLM.models), {"qwen3.8-27b", "gta1-7b"})
            self.assertFalse(FakeLLM.responses)
            trace = (Path(directory) / "model_trace.txt").read_text()
            for label in ('"agent": "feasibility_gate"', '"agent": "planner"',
                          '"agent": "executor"', '"stage": "request"', '"stage": "response"'):
                self.assertIn(label, trace)
            self.assertIn("Save", trace)
            self.assertIn("omitted data image url", trace)
            self.assertNotIn(base64.b64encode(self.png).decode(), trace)

    def test_grounder_trace_includes_actual_prompt(self):
        import logging
        from mm_agents.llm import LocalLLM
        from mm_agents.tars.runtime.task_log import setup_task_logger, dump_model_trace
        with tempfile.TemporaryDirectory() as directory:
            setup_task_logger(logging.getLogger("test"), directory)
            client = LocalLLM("gta1-7b")
            client.cua_trace_callback = lambda stage, payload: dump_model_trace(
                stage, payload, agent="executor", model="gta1-7b")
            with patch.object(LocalLLM, "__call__", return_value="(100,100)"):
                client.call_cua("Save button", Image.new("RGB", (1280, 720)),
                                screen_width=1280, screen_height=720)
            trace = (Path(directory) / "model_trace.txt").read_text()
            self.assertIn("visual_grounder_request", trace)
            self.assertIn("Save button", trace)
            self.assertIn("1288", trace)
            self.assertIn("(100,100)", trace)
            self.assertIn("mapped_point", trace)


if __name__ == "__main__":
    unittest.main()
