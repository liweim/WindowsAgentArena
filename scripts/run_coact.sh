#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_coact.out"

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
    --agent coact \
    --model qwen3.5-9b \
    --orchestrator_model qwen3.5-9b \
    --coding_model qwen3.5-9b \
    --summarizer_model qwen3.5-9b \
    --cua_model uitars-1.5-7b \
    --orchestrator_max_steps 15 \
    --coding_max_steps 20 \
    --cua_max_steps 25 \
    --cut_off_steps 100 \
    --headless \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-coact \
    --browser-port 18115 \
    --rdp-port 13394 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/coact_qwen3.5-9b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started coact in container winarena-waa3 (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
