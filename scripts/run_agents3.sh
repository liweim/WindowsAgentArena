#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/nohup_agents3.out"

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
    --model qwen3.8-27b \
    --thinking_token_budget 16384 \
    --ground_model uitars-1.5-7b \
    --provider_name docker \
    --headless \
    --screen_width 1280 \
    --screen_height 800 \
    --grounding_width 1280 \
    --grounding_height 800 \
    --max_steps 50 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --container-name a11yarena-agents3 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/agents3_qwen3.8-27b \
    --json-name evaluation_examples_windows/test_all.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started agents3 in container winarena-waa2 (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
