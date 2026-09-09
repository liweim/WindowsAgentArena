#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_tars.out"

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
    --model qwen3.5-9b \
    --global-planner-model qwen3.5-9b \
    --visual-grounder-model gta1-7b \
    --max-steps 100 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-tars \
    --browser-port 18118 \
    --rdp-port 13397 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/tars_qwen3.5-9b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    --rerun-fail \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started TARS in container a11yarena-tars (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
