#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/nohup_gta1.out"

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
    --model qwen3.8-27b \
    --thinking_token_budget 2048 \
    --judge_model qwen3.8-27b \
    --ground_model gta1-7b \
    --n_samples 3 \
    --headless \
    --max_steps 50 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --num-workers 4 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/gta1_qwen3.8-27b \
    --json-name evaluation_examples_windows/test_small.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started gta1 task run (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
