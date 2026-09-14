#!/usr/bin/env python3
# Stop only this repository's detached run.sh batch for the selected container.
import argparse
import os
from pathlib import Path
import signal
import sys
import time

script_dir = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Stop run_locallstc and let its cleanup remove disposable VM storage.")
parser.add_argument("--container-name", required=True, help="Container name of the batch to stop")
parser.add_argument("--dry-run", action="store_true", help="Show matching batches without stopping them")
args = parser.parse_args()


def matches(pid):
    try:
        proc = Path("/proc") / str(pid)
        argv = (proc / "cmdline").read_bytes().decode().strip("\0").split("\0")
        # run_locallstc uses setsid: only its session leader owns batch cleanup.
        if os.getsid(pid) != pid or os.getpgid(pid) != pid:
            return False
        cwd = (proc / "cwd").resolve()
        # Accept a directly executed script or bash script; exclude bash -c
        # strings and processes that merely mention the launcher in arguments.
        if Path(argv[0]).name in ("bash", "sh"):
            if len(argv) < 2 or argv[1].startswith("-"):
                return False
            script_index = 1
        else:
            script_index = 0
        if (cwd / argv[script_index]).resolve() != script_dir / "run.sh":
            return False
        values = [argv[i + 1] for i in range(script_index + 1, len(argv) - 1)
                  if argv[i] == "--container-name"]
        return bool(values) and values[-1] == args.container_name
    except (OSError, ValueError, IndexError, UnicodeError):
        return False


pids = [int(p.name) for p in Path("/proc").iterdir() if p.name.isdigit() and matches(int(p.name))]
if not pids:
    print(f"No active batch found for {args.container_name} in {script_dir}.")
    sys.exit(0)
for pid in pids:
    print(f"{'Would stop' if args.dry_run else 'Stopping'} batch PID/PGID {pid}, container {args.container_name}.", flush=True)
    if not args.dry_run and matches(pid):
        # Wake bash out of docker wait too, so its TERM trap runs immediately.
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
if args.dry_run:
    sys.exit(0)
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    remaining = [pid for pid in pids if matches(pid)]
    if not remaining:
        print("Batch stopped. The launcher's cleanup handles its container and temporary disks; results are retained.")
        sys.exit(0)
    time.sleep(0.5)
print(f"Still waiting for batch cleanup: {remaining}. No SIGKILL sent; inspect the run log.", file=sys.stderr)
sys.exit(1)
