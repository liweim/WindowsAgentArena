#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_hisa.out"

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
    --agent hisa \
    --model qwen3.5-9b \
    --global_planner_model qwen3.5-9b \
    --visual_grounder_model gta1-7b \
    --state_manager_model qwen3.5-9b \
    --wo_pattern \
    --headless \
    --max_steps 100 \
    --bash_timeout 180 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-hisa \
    --browser-port 18117 \
    --rdp-port 13396 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/hisa_qwen3.5-9b_wo_pattern \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started hisa in container winarena-waa5 (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
