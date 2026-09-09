"""VM app version probing at agent reset."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..toolkit.vm_handlers import run_bash_on_vm

APP_VERSION_COMMANDS: dict[str, str] = {
    "chrome": "Get-ItemProperty 'HKCU:\\Software\\Google\\Chrome\\BLBeacon' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty version",
    "gimp": "Get-Command gimp* -ErrorAction SilentlyContinue | Select-Object -First 1 Name,Version,Source",
    "libreoffice": "Get-Command soffice* -ErrorAction SilentlyContinue | Select-Object -First 1 Name,Version,Source",
    "os": "Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,OSArchitecture",
    "thunderbird": "Get-Command thunderbird* -ErrorAction SilentlyContinue | Select-Object -First 1 Name,Version,Source",
    "vlc": "Get-Command vlc* -ErrorAction SilentlyContinue | Select-Object -First 1 Name,Version,Source",
    "vs_code": "Get-Command code* -ErrorAction SilentlyContinue | Select-Object -First 1 Name,Version,Source",
}


def probe_app_versions(env: Any, *, timeout: int = 30) -> list[str]:
    """Run version commands on the VM; return flat lines for skill injection."""
    lines: list[str] = []
    for _app, cmd in APP_VERSION_COMMANDS.items():
        result = run_bash_on_vm(env, cmd, timeout=timeout)
        output = result.output if hasattr(result, "output") else str(result)
        lines.append(cmd)
        if output:
            for line in output.strip().splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return lines


def today_line() -> str:
    return f"Today is {datetime.today().strftime('%A, %B %d, %Y')}"



def format_app_version_section(version_lines: list[str] | None) -> str:
    lines = ["## App version checking", "", "Probe results from this VM:"]
    if version_lines:
        for line in version_lines:
            stripped = line.strip()
            if stripped:
                lines.append(f"- {stripped}")
    else:
        lines.append("- _(No live probe results yet.)_")
    return "\n".join(lines)

