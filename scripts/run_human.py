#!/usr/bin/env python3

import argparse
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run human_run.py inside a fresh WinArena container."
    )
    parser.add_argument(
        "-e",
        "--example",
        type=str,
        default="",
        help="Path to the example JSON on the host. If omitted, prompt for it.",
    )
    parser.add_argument(
        "--container-name",
        type=str,
        default="winarena",
        help="Temporary container name.",
    )
    parser.add_argument("--browser-port", type=str, default="9006")
    parser.add_argument("--rdp-port", type=str, default="3390")
    parser.add_argument(
        "--captcha-port",
        type=str,
        default="8765",
        help="Host port for the local CAPTCHA service to expose inside the Windows VM.",
    )
    parser.add_argument("--skip-build", type=str, default="true")
    parser.add_argument("--use-kvm", type=str, default="true")
    parser.add_argument("--ram-size", type=str, default="8G")
    parser.add_argument("--cpu-cores", type=str, default="8")
    parser.add_argument("--mode", type=str, default="dev")
    parser.add_argument(
        "--keep-container",
        type=str,
        default="false",
        help="Keep the temporary container after human_run.py exits.",
    )
    return parser.parse_args()


def prompt_example(example: str) -> str:
    if example:
        return example
    return input("Example JSON path: ").strip()


def host_to_container_example(example_abs: Path, client_root: Path) -> str:
    try:
        relative = example_abs.relative_to(client_root)
    except ValueError as exc:
        raise ValueError(
            f"Example path must be inside {client_root}"
        ) from exc
    return f"/client/{relative.as_posix()}"


def run_command(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def run_command_capture(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        check=True,
        text=True,
        capture_output=True,
    )


def container_exists(container_name: str, cwd: Path) -> bool:
    result = run_command_capture(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name=^{container_name}$",
            "--format",
            "{{.Names}}",
        ],
        cwd=cwd,
    )
    return result.stdout.strip() == container_name


def wait_for_container(container_name: str, cwd: Path, timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if container_exists(container_name, cwd):
            return
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for container {container_name} to appear.")


def probe_server_ready(container_name: str, cwd: Path) -> bool:
    result = subprocess.run(
        [
            "docker",
            "exec",
            container_name,
            "/bin/bash",
            "-lc",
            "curl --silent --output /dev/null --write-out '%{http_code}' 20.20.20.21:5000/probe || true",
        ],
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip() == "200"


def start_vm(container_name: str, cwd: Path) -> None:
    run_command(
        [
            "docker",
            "exec",
            "-d",
            container_name,
            "/bin/bash",
            "-lc",
            "/start_vm.sh >/tmp/start_vm.log 2>&1",
        ],
        cwd=cwd,
    )


def configure_shopping_base_url(cwd: Path) -> None:
    base_url = "http://host.docker.internal:7770/"
    commands = [
        [
            "docker",
            "exec",
            "shopping",
            "/var/www/magento2/bin/magento",
            "setup:store-config:set",
            f"--base-url={base_url}",
        ],
        [
            "docker",
            "exec",
            "shopping",
            "mysql",
            "-u",
            "magentouser",
            "-pMyPassword",
            "magentodb",
            "-e",
            f"UPDATE core_config_data SET value='{base_url}' WHERE path='web/secure/base_url';",
        ],
        [
            "docker",
            "exec",
            "shopping",
            "/var/www/magento2/bin/magento",
            "cache:flush",
        ],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=str(cwd), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def configure_shopping_admin_base_url(cwd: Path) -> None:
    base_url = "http://host.docker.internal:7780/"
    commands = [
        [
            "docker",
            "exec",
            "shopping_admin",
            "/var/www/magento2/bin/magento",
            "setup:store-config:set",
            f"--base-url={base_url}",
        ],
        [
            "docker",
            "exec",
            "shopping_admin",
            "mysql",
            "-u",
            "magentouser",
            "-pMyPassword",
            "magentodb",
            "-e",
            f"UPDATE core_config_data SET value='{base_url}' WHERE path='web/secure/base_url';",
        ],
        [
            "docker",
            "exec",
            "shopping_admin",
            "/var/www/magento2/bin/magento",
            "cache:flush",
        ],
    ]
    for cmd in commands:
        subprocess.run(cmd, cwd=str(cwd), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def configure_self_hosted_services(container_name: str, cwd: Path) -> None:
    run_command(
        [
            "docker",
            "exec",
            container_name,
            "/bin/bash",
            "-lc",
            (
                "host_ip=$(getent hosts host.docker.internal | awk '{print $1; exit}'); "
                "if [ -z \"$host_ip\" ]; then host_ip=$(ip route | awk '/default/ {print $3; exit}'); fi; "
                "(curl --silent --max-time 5 http://$host_ip:7770/ >/dev/null || "
                "curl --silent --max-time 5 http://$host_ip:7780/ >/dev/null) || exit 0; "
                "HOST_IP=$host_ip python3 - <<'PY'\n"
                "import os, requests\n"
                "host_ip = os.environ['HOST_IP']\n"
                "cmd = \"$h='C:\\\\Windows\\\\System32\\\\drivers\\\\etc\\\\hosts'; \" \\\n"
                "      \"$entry='%s host.docker.internal'; \" \\\n"
                "      \"(Get-Content $h) | Where-Object {$_ -notmatch 'host\\\\.docker\\\\.internal'} | Set-Content $h; \" \\\n"
                "      \"Add-Content -Path $h -Value \\\"`n$entry\\\"\" % host_ip\n"
                "requests.post('http://20.20.20.21:5000/execute', json={'command': ['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command', cmd], 'shell': False}, timeout=10)\n"
                "PY\n"
            ),
        ],
        cwd=cwd,
    )


def configure_captcha_service_host(container_name: str, cwd: Path, captcha_port: str) -> None:
    run_command(
        [
            "docker",
            "exec",
            container_name,
            "/bin/bash",
            "-lc",
            (
                "host_ip=$(getent hosts host.docker.internal | awk '{print $1; exit}'); "
                "if [ -z \"$host_ip\" ]; then host_ip=$(ip route | awk '/default/ {print $3; exit}'); fi; "
                f"curl --silent --max-time 5 http://$host_ip:{captcha_port}/status >/dev/null || exit 0; "
                "HOST_IP=$host_ip python3 - <<'PY'\n"
                "import os, requests\n"
                "host_ip = os.environ['HOST_IP']\n"
                "cmd = \"$h='C:\\\\Windows\\\\System32\\\\drivers\\\\etc\\\\hosts'; \" \\\n"
                "      \"$entry='%s host.docker.internal'; \" \\\n"
                "      \"(Get-Content $h) | Where-Object {$_ -notmatch 'host\\\\.docker\\\\.internal'} | Set-Content $h; \" \\\n"
                "      \"Add-Content -Path $h -Value \\\"`n$entry\\\"\" % host_ip\n"
                "requests.post('http://20.20.20.21:5000/execute', json={'command': ['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command', cmd], 'shell': False}, timeout=10)\n"
                "PY\n"
            ),
        ],
        cwd=cwd,
    )


def ensure_vm_ready(container_name: str, cwd: Path, timeout_seconds: int = 300) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if probe_server_ready(container_name, cwd):
            return

        print("Windows VM boot is in progress...", flush=True)
        time.sleep(5)

    raise RuntimeError("Timed out waiting for the Windows VM server to become ready.")


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    client_root = repo_root / "src" / "win-arena-container" / "client"

    example_raw = prompt_example(args.example)
    if not example_raw:
        print("No example path provided.", file=sys.stderr)
        return 1

    example_abs = Path(example_raw).expanduser().resolve()
    if not example_abs.exists():
        print(f"Example file does not exist: {example_abs}", file=sys.stderr)
        return 1

    try:
        container_example = host_to_container_example(example_abs, client_root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    cleanup_needed = args.keep_container.lower() != "true"

    launcher: subprocess.Popen[str] | None = None
    launcher_log = script_dir / ".run_human_launcher.log"

    try:
        subprocess.run(
            ["docker", "rm", "-f", args.container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        launcher = subprocess.Popen(
            [
                "./run.sh",
                "--mode", args.mode,
                "--container-name", args.container_name,
                "--skip-build", args.skip_build,
                "--use-kvm", args.use_kvm,
                "--ram-size", args.ram_size,
                "--cpu-cores", args.cpu_cores,
                "--browser-port", args.browser_port,
                "--rdp-port", args.rdp_port,
                "--start-client", "false",
                "--ephemeral-vm-storage", "true",
            ],
            cwd=str(script_dir),
            stdout=launcher_log.open("w"),
            stderr=subprocess.STDOUT,
        )

        print("Starting fresh WinArena container...", flush=True)
        wait_for_container(args.container_name, script_dir)
        print("Container started. Starting Windows VM...", flush=True)
        start_vm(args.container_name, script_dir)
        print("Waiting for Windows VM to become ready...", flush=True)
        ensure_vm_ready(args.container_name, script_dir)
        configure_shopping_base_url(script_dir)
        configure_shopping_admin_base_url(script_dir)
        configure_self_hosted_services(args.container_name, script_dir)
        configure_captcha_service_host(args.container_name, script_dir, args.captcha_port)
        print(f"Windows VM is ready. Connect via RDP at localhost:{args.rdp_port}.", flush=True)
        print("Launching interactive human_run.py session...", flush=True)

        exec_cmd = [
            "docker",
            "exec",
            "-it" if sys.stdout.isatty() else "",
            args.container_name,
            "/bin/bash",
            "-lc",
            f'cd /client && python human_run.py --example "{container_example}"',
        ]
        exec_cmd = [part for part in exec_cmd if part]
        run_command(exec_cmd, cwd=script_dir)
    finally:
        if cleanup_needed:
            subprocess.run(
                ["docker", "rm", "-f", args.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        if launcher is not None:
            try:
                launcher.wait(timeout=10)
            except subprocess.TimeoutExpired:
                launcher.terminate()
                try:
                    launcher.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    launcher.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
