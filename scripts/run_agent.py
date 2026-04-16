#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def str2bool(value: str) -> bool:
    return str(value).lower() == "true"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run WindowsAgentArena locally with one fresh container per task.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--run-script", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--prepare-image", required=True)
    parser.add_argument("--container-name", required=True)
    parser.add_argument("--skip-build", required=True)
    parser.add_argument("--interactive", required=True)
    parser.add_argument("--use-kvm", required=True)
    parser.add_argument("--ram-size", required=True)
    parser.add_argument("--cpu-cores", required=True)
    parser.add_argument("--mount-vm-storage", required=True)
    parser.add_argument("--mount-client", required=True)
    parser.add_argument("--mount-server", required=True)
    parser.add_argument("--browser-port", required=True)
    parser.add_argument("--rdp-port", required=True)
    parser.add_argument("--clean-results", required=True)
    parser.add_argument("--worker-id", required=True)
    parser.add_argument("--num-workers", required=True)
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--json-name", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--som-origin", required=True)
    parser.add_argument("--a11y-backend", required=True)
    parser.add_argument("--diff-lvl", required=True)
    parser.add_argument("--gpu-enabled", required=True)
    parser.add_argument("--openai-api-key", default="")
    parser.add_argument("--azure-api-key", default="")
    parser.add_argument("--azure-endpoint", default="")
    return parser


def get_task_list(meta_path: Path, worker_id: int, num_workers: int) -> list[tuple[str, str]]:
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    all_tasks = [(domain, example_id) for domain in meta for example_id in meta[domain]]
    tasks_per_worker = len(all_tasks) // num_workers
    extra = len(all_tasks) % num_workers
    start_index = worker_id * tasks_per_worker + min(worker_id, extra)
    end_index = start_index + tasks_per_worker + (1 if worker_id < extra else 0)
    return all_tasks[start_index:end_index]


def write_single_task_meta(client_root: Path, domain: str, example_id: str) -> str:
    generated_dir = client_root / "evaluation_examples_windows" / "generated_single_tasks"
    generated_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{domain}__{example_id}.json"
    rel_path = Path("evaluation_examples_windows") / "generated_single_tasks" / file_name
    abs_path = generated_dir / file_name
    with abs_path.open("w", encoding="utf-8") as f:
        json.dump({domain: [example_id]}, f)
    return str(rel_path)


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


def ensure_vm_ready(container_name: str, cwd: Path, timeout_seconds: int = 300) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if probe_server_ready(container_name, cwd):
            return
        print("Windows VM boot is in progress...", flush=True)
        time.sleep(5)
    raise RuntimeError("Timed out waiting for the Windows VM server to become ready.")


def main() -> int:
    args = build_arg_parser().parse_args()
    repo_root = Path(args.repo_root).resolve()
    client_root = repo_root / "src" / "win-arena-container" / "client"
    meta_path = client_root / args.json_name

    if not meta_path.exists():
        print(f"Task meta JSON does not exist: {meta_path}", file=sys.stderr)
        return 1

    worker_id = int(args.worker_id)
    num_workers = int(args.num_workers)
    tasks = get_task_list(meta_path, worker_id, num_workers)
    if not tasks:
        print("No tasks assigned to this worker.")
        return 0

    generated_dir = client_root / "evaluation_examples_windows" / "generated_single_tasks"
    generated_dir.mkdir(parents=True, exist_ok=True)

    first_task = True
    try:
        for domain, example_id in tasks:
            single_task_json = write_single_task_meta(client_root, domain, example_id)
            print(f"\n=== Running fresh task {domain}/{example_id} ===", flush=True)

            subprocess.run(
                ["docker", "rm", "-f", args.container_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

            launcher_cmd = [
                args.run_script,
                "--mode", args.mode,
                "--prepare-image", args.prepare_image,
                "--container-name", args.container_name,
                "--skip-build", args.skip_build if first_task else "true",
                "--interactive", args.interactive,
                "--connect", "false",
                "--use-kvm", args.use_kvm,
                "--ram-size", args.ram_size,
                "--cpu-cores", args.cpu_cores,
                "--mount-vm-storage", args.mount_vm_storage,
                "--ephemeral-vm-storage", "true",
                "--mount-client", args.mount_client,
                "--mount-server", args.mount_server,
                "--browser-port", args.browser_port,
                "--rdp-port", args.rdp_port,
                "--start-client", "false",
                "--clean-results", args.clean_results if first_task else "false",
                "--worker-id", args.worker_id,
                "--num-workers", "1",
                "--result-dir", args.result_dir,
                "--json-name", single_task_json,
                "--agent", args.agent,
                "--model", args.model,
                "--som-origin", args.som_origin,
                "--a11y-backend", args.a11y_backend,
                "--diff-lvl", args.diff_lvl,
                "--gpu-enabled", args.gpu_enabled,
            ]

            if args.openai_api_key:
                launcher_cmd.extend(["--openai-api-key", args.openai_api_key])
            if args.azure_api_key:
                launcher_cmd.extend(["--azure-api-key", args.azure_api_key])
            if args.azure_endpoint:
                launcher_cmd.extend(["--azure-endpoint", args.azure_endpoint])

            launcher_log = repo_root / "scripts" / f".run_agent_{args.container_name}.log"
            launcher: subprocess.Popen[str] | None = None
            try:
                launcher = subprocess.Popen(
                    launcher_cmd,
                    cwd=str(repo_root / "scripts"),
                    stdout=launcher_log.open("w"),
                    stderr=subprocess.STDOUT,
                )

                print("Starting fresh WinArena container...", flush=True)
                wait_for_container(args.container_name, repo_root / "scripts")
                print("Container started. Starting Windows VM...", flush=True)
                start_vm(args.container_name, repo_root / "scripts")
                print("Waiting for Windows VM to become ready...", flush=True)
                ensure_vm_ready(args.container_name, repo_root / "scripts")
                print("Windows VM is ready. Launching agent...", flush=True)

                client_cmd = [
                    "docker",
                    "exec",
                    args.container_name,
                    "/bin/bash",
                    "-lc",
                    (
                        "cd / && ./start_client.sh "
                        f"--agent {args.agent} "
                        f"--model {args.model} "
                        f"--som-origin {args.som_origin} "
                        f"--a11y-backend {args.a11y_backend} "
                        f"--clean-results {args.clean_results if first_task else 'false'} "
                        f"--worker-id {args.worker_id} "
                        "--num-workers 1 "
                        f"--result-dir {args.result_dir} "
                        f"--json-name {single_task_json} "
                        f"--diff-lvl {args.diff_lvl}"
                    ),
                ]
                run_command(client_cmd, repo_root / "scripts")
            finally:
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
            first_task = False
    finally:
        shutil.rmtree(generated_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
