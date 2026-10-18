import unittest

from mm_agents.gui_agents.s3.agents.code_agent import (
    _powershell_python_wrapper,
    execute_code,
    extract_code_block,
)


class _PythonOnlyController:
    def __init__(self):
        self.script = None

    def run_python_script(self, script):
        self.script = script
        return {"status": "success", "output": "ok", "return_code": 0}


class CodeAgentExecutionTest(unittest.TestCase):
    def test_shell_wrapper_uses_powershell(self):
        wrapper = _powershell_python_wrapper("Get-ChildItem")
        self.assertIn("powershell.exe", wrapper)
        self.assertIn("Get-ChildItem", wrapper)
        self.assertNotIn("run_bash_script", wrapper)

    def test_bash_block_uses_python_controller(self):
        controller = _PythonOnlyController()
        result = execute_code("bash", "Get-ChildItem", controller)

        self.assertEqual(result["status"], "success")
        self.assertIn("powershell.exe", controller.script)
        self.assertIn("Get-ChildItem", controller.script)

    def test_extracts_native_powershell_block(self):
        code_type, code = extract_code_block(
            "<answer>```powershell\nGet-ChildItem\n```</answer>"
        )
        self.assertEqual(code_type, "powershell")
        self.assertEqual(code, "Get-ChildItem")


if __name__ == "__main__":
    unittest.main()
