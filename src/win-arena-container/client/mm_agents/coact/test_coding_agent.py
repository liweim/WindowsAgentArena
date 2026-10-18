import unittest

from mm_agents.coact.coding_execution import (
    execution_result,
    powershell_python_wrapper,
)
from mm_agents.coact.message_utils import is_termination_message, message_text


class CodingAgentExecutionTest(unittest.TestCase):
    def test_normalizes_success_and_failure_responses(self):
        self.assertEqual(
            execution_result(
                {
                    "status": "success",
                    "output": "done",
                    "error": "",
                    "returncode": 0,
                }
            ),
            (0, "done"),
        )
        self.assertEqual(
            execution_result(
                {
                    "status": "success",
                    "output": "",
                    "error": "bad command",
                    "returncode": 3,
                }
            ),
            (3, "bad command"),
        )
        self.assertEqual(
            execution_result({"status": "error", "message": "offline"}),
            (1, "offline"),
        )

    def test_builds_windows_powershell_wrapper(self):
        wrapper = powershell_python_wrapper("Get-ChildItem")
        self.assertIn("powershell.exe", wrapper)
        self.assertNotIn("run_bash_script", wrapper)


class TerminationMessageTest(unittest.TestCase):
    def test_accepts_whitespace_and_case_in_multimodal_content(self):
        message = {"content": [{"type": "text", "text": "\n\n TERMINATE \r\n"}]}
        self.assertTrue(is_termination_message(message))

    def test_accepts_plain_content_and_configured_tokens(self):
        self.assertTrue(
            is_termination_message(
                {"content": "  InFeAsIbLe\n"},
                ("terminate", "infeasible"),
            )
        )

    def test_rejects_non_terminal_sentences(self):
        message = {"content": [{"type": "text", "text": "Task done. TERMINATE"}]}
        self.assertFalse(is_termination_message(message))

    def test_extracts_all_text_blocks(self):
        message = {
            "content": [
                {"type": "image_url", "image_url": {"url": "<image>"}},
                {"type": "text", "text": "TERMINATE"},
            ]
        }
        self.assertEqual(message_text(message), "TERMINATE")


if __name__ == "__main__":
    unittest.main()
