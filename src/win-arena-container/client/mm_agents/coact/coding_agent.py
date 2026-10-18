from typing import Any, Callable, Optional

from .autogen.llm_config import LLMConfig
from .autogen.code_utils import PYTHON_VARIANTS
from .autogen.agentchat.contrib.multimodal_conversable_agent import MultimodalConversableAgent
from .coding_execution import execution_result, powershell_python_wrapper


CODER_SYSTEM_MESSAGE = """# Your role
- You are a programmer operating inside the Windows 11 guest shown in the screenshot.
- The current Windows user is `Docker`; its profile is `C:\\Users\\Docker` and its Desktop is `C:\\Users\\Docker\\Desktop`.
- Write code in a single ```python...``` code block whenever possible. Python runs directly in the Windows guest.
- If a shell is genuinely necessary, use one ```powershell...``` code block with Windows PowerShell syntax.
- Do not use Linux paths, bash utilities, sudo, apt, `/home/user`, `/root`, or `/tmp`.

# Requirements
- You MUST verify the result before save the changes.
- When you write code, identify it as either Python or PowerShell.
- Wrap all your code in ONE code block. DO NOT let user save the code as a file and execute it for you.
- Do not include __main__ in your python code.
- When you modify a spreadsheet, **make sure every value is in the expected cell**.
- When importing a package, you need to check if the package has been installed. If not, you need to install it yourself.
- You need to print the progressive and final result.
- If you met execution error, you need to analyze the error message and try to fix the error.
"""


class TerminalProxyAgent(MultimodalConversableAgent):
    def __init__(
            self, 
        name: str, 
        env,
        llm_config: LLMConfig = False, 
        system_message: str = "",
        human_input_mode: str = "NEVER",
        code_execution_config = {},
        is_termination_msg: Optional[Callable[[dict[str, Any]], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = None,
        default_auto_reply: Optional[str] = None,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            is_termination_msg=is_termination_msg,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config,
            llm_config=llm_config,
            default_auto_reply=default_auto_reply,
            description=description
        )
        self.env = env

    def run_code(self, code: str, lang: str = "python", **kwargs):
        image = None
        normalized_lang = (lang or "").lower()
        if normalized_lang in ["powershell", "ps1", "pwsh", "bash", "shell", "sh"]:
            output_dict = self.env.controller.run_python_script(
                powershell_python_wrapper(code)
            )
            exitcode, logs = execution_result(output_dict)
        elif normalized_lang in PYTHON_VARIANTS:
            output_dict = self.env.controller.run_python_script(code)
            exitcode, logs = execution_result(output_dict)
        else:
            exitcode = -1
            logs = (
                f"Unsupported language {lang!r}. Use Python or Windows PowerShell."
            )
        return exitcode, logs, image
