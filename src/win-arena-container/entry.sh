#!/bin/bash

# Fix for Azure ML Job not using the correct root path
cd /

echo "Starting WinArena..."

prepare_image=false
start_client=true
agent="navi"
model="gpt-4-vision-preview"
temperature=0
seed=42
top_p=0.95
top_k=20
som_origin="oss"
a11y_backend="uia"
clean_results=true
worker_id="0"
num_workers="1"
result_dir="./results"
json_name="evaluation_examples_windows/test_all.json" 
diff_lvl="normal"
client_extra_args=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prepare-image) prepare_image=$2; shift 2 ;;
        --start-client) start_client=$2; shift 2 ;;
        --agent) agent=$2; shift 2 ;;
        --model) model=$2; shift 2 ;;
        --temperature) temperature=$2; shift 2 ;;
        --seed) seed=$2; shift 2 ;;
        --top-p|--top_p) top_p=$2; shift 2 ;;
        --top-k|--top_k) top_k=$2; shift 2 ;;
        --som-origin) som_origin=$2; shift 2 ;;
        --a11y-backend) a11y_backend=$2; shift 2 ;;
        --clean-results) clean_results=$2; shift 2 ;;
        --worker-id) worker_id=$2; shift 2 ;;
        --num-workers) num_workers=$2; shift 2 ;;
        --result-dir) result_dir=$2; shift 2 ;;
        --json-name) json_name=$2; shift 2 ;;
        --diff-lvl) diff_lvl=$2; shift 2 ;;
        --help) echo "Usage: $0 [options]"; exit 0 ;;
        *) client_extra_args+=("$1"); shift ;;
    esac
done

# Starts the VM and blocks until the Windows Arena Server is ready
echo "Starting VM..."
./entry_setup.sh
echo "VM started, server ready"

if [ "$prepare_image" = "true" ]; then
    echo "Preparing Arena image by gracefully shutting down the Windows VM..."
    response=$(curl --write-out '%{http_code}' --silent --output /dev/null -X POST 20.20.20.21:5000/shutdown)

    if [ $response -eq 200 ]; then
        echo "Windows VM is shutting down..."
        sleep 180 # Wait for any updates to be saved, and for windows.boot to be created
    else
        echo "Failed to shut down the Windows VM. Exiting..."
    fi
else
    echo "Skipping image preparation..."
    # Start the client script
    if [ "$start_client" = "true" ]; then
        echo "Starting client..."
        ./start_client.sh --agent "$agent" --model "$model" --temperature "$temperature" --seed "$seed" --top-p "$top_p" --top-k "$top_k" --som-origin "$som_origin" --a11y-backend "$a11y_backend" --clean-results "$clean_results" --worker-id "$worker_id" --num-workers "$num_workers" --result-dir "$result_dir" --json-name "$json_name" --diff-lvl "$diff_lvl" "${client_extra_args[@]}"
        client_status=$?
        echo "Client exited with status $client_status"
        exit "$client_status"
    else
        echo "Keeping container alive"
        while true; do
            sleep 60
        done
        echo "Exiting..."
    fi
fi

# Wait for any process to exit
wait -n

# Exit with the status of the process that exited first
exit $?
