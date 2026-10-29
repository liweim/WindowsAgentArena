#!/bin/bash

set -e

cd "$(dirname "$0")"
LOG_FILE="$(pwd)/nohup_locallstc2_ablation_2.out"

nohup setsid env \
    PYTHONUNBUFFERED=1 \
    WINARENA_IMAGE_TAG=latest \
    PARAKEET_ASR_URL=http://host.docker.internal:18765/v1/audio/transcriptions \
    "DECIDER_URL=${DECIDER_URL:-http://129.94.173.199:18766/v1/systemone}" \
    "LOCALLSTC_HOST_UID=$(id -u)" \
    "LOCALLSTC_HOST_GID=$(id -g)" \
    ./run.sh \
    --mode dev \
    --skip-build true \
    --connect false \
    --start-client true \
    --agent locallstc2 \
    --model qwen3.8-27b \
    --thinking_token_budget 2048 \
    --global_planner_model qwen3.8-27b \
    --visual_grounder_model gta1-7b \
    --state_manager_model qwen3.8-27b \
    --max_steps 50 \
    --som-origin oss \
    --a11y-backend uia \
    --clean-results false \
    --num-workers 3 \
    --result-dir /locallstc/projects/WindowsAgentArena/results/locallstc2_qwen3.8-27b_wo_jev_api \
    --json-name evaluation_examples_windows/test_small.json \
    --remove-container true \
    --wo-jev-api \
    "$@" >"$LOG_FILE" 2>&1 < /dev/null &

runner_pid=$!
echo "Started locallstc2 task run (PID: $runner_pid)"
echo "Logs: tail -f $LOG_FILE"
