#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/../nohup_locallstc.out"

method="${1:-locallstc}"
if [ "$#" -gt 0 ]; then
    shift
fi

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
    --agent "$method" \
    --model qwen3.5-9b \
    --global_planner_model qwen3.5-9b \
    --visual_grounder_model gta1-7b \
    --state_manager_model qwen3.5-9b \
    --max_steps 100 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --worker-id 0 \
    --num-workers 1 \
    --ephemeral-vm-storage true \
    --container-name a11yarena-locallstc \
    --browser-port 18113 \
    --rdp-port 13392 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/locallstc_qwen3.5-9b \
    --json-name evaluation_examples_windows/test_one.json \
    --remove-container true \
    --rerun_fail \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started $method in container winarena-waa (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
