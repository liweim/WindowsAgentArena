#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_gta1.out"

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
    --agent gta1 \
    --model qwen3.5-9b \
    --judge_model qwen3.5-9b \
    --ground_model gta1-7b \
    --n_samples 3 \
    --headless \
    --max_steps 100 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-gta1 \
    --browser-port 18116 \
    --rdp-port 13395 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/gta1_qwen3.5-9b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started gta1 in container winarena-waa4 (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
