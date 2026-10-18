import ast
import unittest

from mm_agents.gta1.main import OSWorldACI
from mm_agents.gta1.prompts import (
    GTA1_JUDGE_SYSTEM_PROMPT,
    GTA1_PLANNER_SYSTEM_PROMPT,
)


class GTA1WindowsAdaptationTest(unittest.TestCase):
    def test_prompts_describe_windows_not_ubuntu(self):
        self.assertIn("Windows 11", GTA1_PLANNER_SYSTEM_PROMPT)
        self.assertNotIn("You are on Ubuntu", GTA1_PLANNER_SYSTEM_PROMPT)
        self.assertNotIn("sudo rights", GTA1_PLANNER_SYSTEM_PROMPT)
        self.assertIn("Windows 11", GTA1_JUDGE_SYSTEM_PROMPT)

    def test_set_cell_values_uses_windows_libreoffice_python(self):
        # set_cell_values only depends on the platform; bypass model clients.
        agent = object.__new__(OSWorldACI)
        agent.platform = "windows"
        command = agent.set_cell_values(
            {"A1": "hello", "B2": 3}, "Book1.xlsx", "Sheet1"
        )

        ast.parse(command)
        self.assertIn(r"C:\Program Files\LibreOffice\program\python.exe", command)
        self.assertNotIn("sudo", command)
        self.assertNotIn(" ss ", command)
        self.assertIn("Book1.xlsx", command)
        self.assertIn("Sheet1", command)


if __name__ == "__main__":
    unittest.main()
