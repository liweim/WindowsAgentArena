#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/nohup_locallstc.out"

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
    --agent locallstc \
    --model qwen3.8-27b \
    --global_planner_model qwen3.8-27b \
    --visual_grounder_model gta1-7b \
    --state_manager_model qwen3.8-27b \
    --max_steps 50 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --isolate-tasks true \
    --container-name a11yarena-locallstc \
    --result-dir /locallstc/projects/WindowsAgentArena/results/locallstc_qwen3.8-27b \
    --json-name evaluation_examples_windows/cognitive.json \
    --remove-container true \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started locallstc in container winarena-waa (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
