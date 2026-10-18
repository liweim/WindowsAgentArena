import json
from typing import Any, Mapping, Optional


def execution_result(output_dict: Optional[Mapping[str, Any]]) -> tuple[int, str]:
    """Normalize the Windows guest controller's command response."""
    if not output_dict:
        return 1, "The Windows guest returned no execution result."

    status = str(output_dict.get("status", "error")).lower()
    raw_exitcode = output_dict.get(
        "return_code",
        output_dict.get("returncode", 0 if status == "success" else 1),
    )
    try:
        exitcode = int(raw_exitcode)
    except (TypeError, ValueError):
        exitcode = 0 if status == "success" else 1
    if status != "success" and exitcode == 0:
        exitcode = 1

    log_parts = []
    for key in ("output", "error", "message"):
        value = output_dict.get(key)
        if value and str(value).strip():
            log_parts.append(str(value).strip())
    return exitcode, "\n".join(log_parts)


def powershell_python_wrapper(code: str) -> str:
    """Build guest-side Python that executes PowerShell without shell quoting."""
    return (
        "import subprocess, sys\n"
        f"command = {json.dumps(code)}\n"
        "result = subprocess.run(\n"
        "    ['powershell.exe', '-NoProfile', '-NonInteractive', "
        "'-ExecutionPolicy', 'Bypass', '-Command', command],\n"
        "    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,\n"
        ")\n"
        "sys.stdout.write(result.stdout or '')\n"
        "sys.stderr.write(result.stderr or '')\n"
        "sys.exit(result.returncode)\n"
    )
