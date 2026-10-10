#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/nohup_tars.out"

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
    --agent tars \
    --model qwen3.8-27b \
    --global-planner-model qwen3.8-27b \
    --visual-grounder-model gta1-7b \
    --max-steps 50 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --isolate-tasks true \
    --container-name a11yarena-tars \
    --result-dir /locallstc/projects/WindowsAgentArena/results/tars_qwen3.8-27b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    --rerun \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started TARS in container a11yarena-tars (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
