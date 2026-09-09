#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_agents3.out"

nohup setsid env \
    PYTHONUNBUFFERED=1 \
    WINARENA_IMAGE_TAG=latest \
    "LOCALLSTC_HOST_UID=$(id -u)" \
    "LOCALLSTC_HOST_GID=$(id -g)" \
    ./run.sh \
    --mode dev \
    --skip-build true \
    --connect false \
    --start-client true \
    --agent agents3 \
    --model qwen3.5-9b \
    --ground_model uitars-1.5-7b \
    --provider_name docker \
    --headless \
    --max_steps 100 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-agents3 \
    --browser-port 18114 \
    --rdp-port 13393 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/agents3_qwen3.5-9b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started agents3 in container winarena-waa2 (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
