import unittest

from mm_agents.run_single import (
    _is_sleep_only_action,
    _update_repeated_action_state,
)


class RepeatedActionDetectionTest(unittest.TestCase):
    def test_recognizes_sleep_only_actions(self):
        self.assertTrue(_is_sleep_only_action("import time; time.sleep(2.222)"))
        self.assertTrue(_is_sleep_only_action("time.sleep(1)"))
        self.assertFalse(
            _is_sleep_only_action(
                "import pyautogui; import time; "
                "pyautogui.click(10, 20); time.sleep(0.5)"
            )
        )

    def test_repeated_sleep_actions_never_hit_limit(self):
        last_action = None
        repeat_count = 0
        for _ in range(5):
            last_action, repeat_count, limit_reached = (
                _update_repeated_action_state(
                    "import time; time.sleep(2.222)", last_action, repeat_count
                )
            )
            self.assertFalse(limit_reached)
        self.assertIsNone(last_action)
        self.assertEqual(repeat_count, 0)

    def test_repeated_gui_actions_still_hit_limit(self):
        action = "import pyautogui; pyautogui.click(10, 20)"
        last_action = None
        repeat_count = 0
        limits = []
        for _ in range(3):
            last_action, repeat_count, limit_reached = (
                _update_repeated_action_state(action, last_action, repeat_count)
            )
            limits.append(limit_reached)
        self.assertEqual(limits, [False, False, True])


if __name__ == "__main__":
    unittest.main()
