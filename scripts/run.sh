#!/bin/bash
set -e
source ./shared.sh

mode="azure"
prepare_image=false
skip_build=false
interactive=false
connect=false
use_kvm=true
ram_size=8G
cpu_cores=8
mount_vm_storage=true
ephemeral_vm_storage=false
mount_client=true
mount_server=true
container_name="a11yarena"
browser_port=9006
rdp_port=3390
start_client=true
agent="navi"
model="gpt-4-vision-preview"
temperature=0
seed=42
top_p=0.95
top_k=20
som_origin="oss"
a11y_backend="uia"
gpu_enabled=false
clean_results=true
worker_id=0
num_workers=1
result_dir="./results"
json_name="evaluation_examples_windows/test_all.json"
diff_lvl="normal"
remove_container=true
isolate_tasks=false
storage_base_path=""
OPENAI_API_KEY=""
AZURE_API_KEY=""
AZURE_ENDPOINT=""
method_cli_args=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --container-name) container_name="$2"; shift 2 ;;
        --prepare-image) prepare_image=$2; shift 2 ;;
        --skip-build) skip_build=$2; shift 2 ;;
        --interactive) interactive=$2; shift 2 ;;
        --connect) connect=$2; shift 2 ;;
        --use-kvm) use_kvm=$2; shift 2 ;;
        --ram-size) ram_size=$2; shift 2 ;;
        --cpu-cores) cpu_cores=$2; shift 2 ;;
        --mount-vm-storage) mount_vm_storage=$2; shift 2 ;;
        --ephemeral-vm-storage) ephemeral_vm_storage=$2; shift 2 ;;
        --mount-client) mount_client=$2; shift 2 ;;
        --mount-server) mount_server=$2; shift 2 ;;
        --browser-port) browser_port="$2"; shift 2 ;;
        --rdp-port) rdp_port="$2"; shift 2 ;;
        --start-client) start_client=$2; shift 2 ;;
        --agent) agent=$2; shift 2 ;;
        --model) model=$2; shift 2 ;;
        --temperature) temperature=$2; shift 2 ;;
        --seed) seed=$2; shift 2 ;;
        --top-p|--top_p) top_p=$2; shift 2 ;;
        --top-k|--top_k) top_k=$2; shift 2 ;;
        --som-origin) som_origin=$2; shift 2 ;;
        --a11y-backend) a11y_backend=$2; shift 2 ;;
        --gpu-enabled) gpu_enabled=$2; shift 2 ;;
        --clean-results) clean_results=$2; shift 2 ;;
        --worker-id) worker_id=$2; shift 2 ;;
        --num-workers) num_workers=$2; shift 2 ;;
        --result-dir) result_dir=$2; shift 2 ;;
        --json-name) json_name=$2; shift 2 ;;
        --diff-lvl) diff_lvl=$2; shift 2 ;;
        --remove-container) remove_container=$2; shift 2 ;;
        --isolate-tasks) isolate_tasks=$2; shift 2 ;;
        --storage-base-path) storage_base_path=$2; shift 2 ;;
        --openai-api-key) OPENAI_API_KEY="$2"; shift 2 ;;
        --azure-api-key) AZURE_API_KEY="$2"; shift 2 ;;
        --azure-endpoint) AZURE_ENDPOINT="$2"; shift 2 ;;
        --mode) mode=$2; shift 2 ;;
        --help) echo "Usage: $0 [options]"; exit 0 ;;
        *) method_cli_args+=("$1"); shift ;;
    esac
done

# The outer launcher owns only container/VM options. Preserve every other
# token for the selected agent's parser inside the client.
if [ ${#method_cli_args[@]} -gt 0 ]; then
    printf -v method_cli_serialized '%q ' "${method_cli_args[@]}"
    MM_AGENTS_EXTRA_ARGS="${MM_AGENTS_EXTRA_ARGS:+$MM_AGENTS_EXTRA_ARGS }$method_cli_serialized"
    export MM_AGENTS_EXTRA_ARGS
fi

if [ "$mode" = "dev" ]; then
  winarena_image_name="winarena-$mode"
else
  winarena_image_name="winarena"
fi
winarena_image_tag="${WINARENA_IMAGE_TAG:-latest}"
winarena_full_image_name="windowsarena/$winarena_image_name"

if ! docker info >/dev/null 2>&1; then
    log_error_exit "Docker daemon is not running. Please start Docker and try again."
fi

if ! docker image inspect "${winarena_full_image_name}:${winarena_image_tag}" >/dev/null 2>&1; then
    echo "Docker image ${winarena_full_image_name}:${winarena_image_tag} not found."
    if [ "$skip_build" = true ]; then
        log_error_exit "The skip_build flag is set to true, but the image was not found."
    fi
fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
vm_setup_image_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/vm/image")
vm_storage_mount_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/vm/storage")
if [ -n "$storage_base_path" ]; then
    vm_storage_base_path=$(getrealpath "$storage_base_path")
else
    vm_storage_base_path="$vm_storage_mount_path"
fi
server_mount_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/vm/setup")
client_mount_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/client")
locallstc_root_path=$(getrealpath "$SCRIPT_DIR/../../..")
entry_script_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/entry.sh")
entry_setup_script_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/entry_setup.sh")
start_client_script_path=$(getrealpath "$SCRIPT_DIR/../src/win-arena-container/start_client.sh")
task_json_mount_path=""

echo "Using VM Setup Image path: $vm_setup_image_path"
echo "Using VM storage mount path: $vm_storage_mount_path"
echo "Using server mount path: $server_mount_path"
echo "Using client mount path: $client_mount_path"

if [ ! -e /dev/kvm ]; then
    echo "/dev/kvm not found. Setting use_kvm to false."
    use_kvm=false
fi

build_container_image() {
    echo "Building Container Image..."
    source "$SCRIPT_DIR/build-container-image.sh" --mode $mode --image-tag "$winarena_image_tag"
}

ephemeral_vm_storage_dir=""

cleanup_ephemeral_vm_storage() {
    if [ -n "$ephemeral_vm_storage_dir" ] && [ -d "$ephemeral_vm_storage_dir" ]; then
        echo "Removing ephemeral VM storage directory: $ephemeral_vm_storage_dir"
        rm -rf "$ephemeral_vm_storage_dir"
    fi
}

prepare_vm_storage_mount_path() {
    if [ "$mount_vm_storage" != true ] || [ "$ephemeral_vm_storage" != true ]; then
        return
    fi
    if [ "$prepare_image" = true ]; then
        log_error_exit "--ephemeral-vm-storage true is incompatible with --prepare-image true."
    fi
    if [ "$connect" = true ]; then
        log_error_exit "--ephemeral-vm-storage true is incompatible with --connect true."
    fi
    if [ "$isolate_tasks" = true ]; then
        log_error_exit "--ephemeral-vm-storage true is redundant with --isolate-tasks true; choose one."
    fi

    ephemeral_vm_storage_dir=$(mktemp -d -t winarena-storage-XXXXXX)
    trap cleanup_ephemeral_vm_storage EXIT
    echo "Creating ephemeral VM storage copy at: $ephemeral_vm_storage_dir"
    cp -a --reflink=auto "$vm_storage_mount_path/." "$ephemeral_vm_storage_dir/"
    vm_storage_mount_path="$ephemeral_vm_storage_dir"
}

invoke_docker_container() {
    docker_command="docker run"
    if [ "$interactive" = true ] && [ -t 1 ]; then docker_command+=" -it"; fi
    docker_command+=" -p ${browser_port}:8006 -p ${rdp_port}:3389 --name $container_name --platform linux/amd64"
    if [ "$remove_container" = true ]; then docker_command+=" --rm"; fi
    if [ "$interactive" != true ]; then docker_command+=" -d"; fi
    if [ "$use_kvm" = true ]; then docker_command+=" --device=/dev/kvm"; else docker_command+=" -e KVM=N"; fi
    docker_command+=" -e RAM_SIZE=$ram_size -e CPU_CORES=$cpu_cores"
    if [ "$prepare_image" = true ]; then docker_command+=" --mount type=bind,source=${vm_setup_image_path}/setup.iso,target=/custom.iso"; fi
    if [ "$mount_vm_storage" = true ]; then docker_command+=" -v ${vm_storage_mount_path}/.:/storage"; fi
    if [ -n "$task_json_mount_path" ]; then docker_command+=" -v ${task_json_mount_path}:/winarena-task.json:ro"; fi
    if [ "$mount_server" = true ]; then docker_command+=" -v ${server_mount_path}/.:/shared"; fi
    if [ "$mount_client" = true ]; then docker_command+=" -v ${client_mount_path}/.:/client"; fi
    docker_command+=" -v ${entry_script_path}:/entry.sh:ro -v ${entry_setup_script_path}:/entry_setup.sh:ro -v ${start_client_script_path}:/start_client.sh:ro"
    docker_command+=" -v ${locallstc_root_path}/.:/locallstc -e PYTHONPATH=/locallstc:/client"
    docker_command+=" --add-host=host.docker.internal:host-gateway"
    docker_command+=" -e LOCAL_API_URL=http://host.docker.internal:30000/v1 -e GTA1_API_URL=http://host.docker.internal:1234/v1 -e UITARS_API_URL=http://host.docker.internal:1235/v1"
    if [ -n "${MM_AGENTS_EXTRA_ARGS:-}" ]; then docker_command+=" -e MM_AGENTS_EXTRA_ARGS"; fi
    if [ -n "${LOCALLSTC_EXTRA_ARGS:-}" ]; then docker_command+=" -e LOCALLSTC_EXTRA_ARGS"; fi
    if [ -n "${LOCALLSTC_HOST_UID:-}" ]; then docker_command+=" -e LOCALLSTC_HOST_UID"; fi
    if [ -n "${LOCALLSTC_HOST_GID:-}" ]; then docker_command+=" -e LOCALLSTC_HOST_GID"; fi
    docker_command+=" --cap-add NET_ADMIN --stop-timeout 120 --entrypoint /bin/bash"
    if [ "$gpu_enabled" = true ] && [ "$(command -v nvidia-smi)" ]; then docker_command+=" --gpus all"; fi
    if [ -n "$OPENAI_API_KEY" ]; then
        docker_command+=" -e OPENAI_API_KEY=$OPENAI_API_KEY"
    else
        if [ -n "$AZURE_API_KEY" ]; then docker_command+=" -e AZURE_API_KEY=$AZURE_API_KEY"; fi
        if [ -n "$AZURE_ENDPOINT" ]; then docker_command+=" -e AZURE_ENDPOINT=$AZURE_ENDPOINT"; fi
    fi
    docker_command+=" $winarena_full_image_name:$winarena_image_tag"
    entrypoint_args=" -c './entry.sh --prepare-image $prepare_image --start-client $start_client --agent $agent --model $model --temperature $temperature --seed $seed --top-p $top_p --top-k $top_k --som-origin $som_origin --a11y-backend $a11y_backend --clean-results $clean_results --worker-id $worker_id --num-workers $num_workers --result-dir $result_dir --json-name $json_name --diff-lvl $diff_lvl; status=\$?; if [ -n "\${LOCALLSTC_HOST_UID:-}" ] && [ -n "\${LOCALLSTC_HOST_GID:-}" ] && [ -d "$result_dir" ]; then chown -R \"\$LOCALLSTC_HOST_UID:\$LOCALLSTC_HOST_GID\" "$result_dir"; fi; exit \$status'"
    if [ "$interactive" = true ]; then entrypoint_args=""; fi
    docker_command+=$entrypoint_args
    echo "Invoking Docker Container with the command:"
    echo "$docker_command"
    if [ "$interactive" = true ]; then
        eval $docker_command
        return
    fi

    container_id=$(eval $docker_command)
    echo "Started container: $container_id"

    docker logs -f --tail 0 "$container_name" &
    log_pid=$!

    wait_status=0
    status=$(docker wait "$container_name") || wait_status=$?
    kill "$log_pid" >/dev/null 2>&1 || true
    wait "$log_pid" >/dev/null 2>&1 || true

    if [ $wait_status -ne 0 ] || ! [[ "$status" =~ ^[0-9]+$ ]]; then
        log_error_exit "Failed to wait for container $container_name to exit cleanly."
    fi

    echo "Container $container_name exited with status $status."
    return "$status"
}

if [ "$connect" = true ]; then
    echo "Connecting to existing container $container_name..."
    docker_exec_command="docker exec"
    if [ -t 1 ]; then docker_exec_command+=" -it"; fi
    docker_exec_command+=" $container_name /bin/bash"
    echo "Invoking docker exec with the command:"
    echo "$docker_exec_command"
    eval $docker_exec_command
    exit 0
fi

if [ "$skip_build" = false ]; then build_container_image; fi

prepare_storage_copy() {
    local destination=$1
    local started_at finished_at

    mkdir -p "$destination"
    started_at=$(date +%s)
    echo "Preparing isolated VM storage: $destination"
    cp -a --reflink=auto --sparse=always "$vm_storage_base_path/." "$destination/"
    finished_at=$(date +%s)
    echo "Prepared isolated VM storage in $((finished_at - started_at)) seconds: $destination"
}

write_single_task_json() {
    local domain=$1
    local example_id=$2
    local output_path=$3

    python3 - "$domain" "$example_id" "$output_path" <<'PY'
import json
import sys

domain, example_id, output_path = sys.argv[1:]
with open(output_path, "w", encoding="utf-8") as output_file:
    json.dump({domain: [example_id]}, output_file)
PY
}

run_isolated_tasks() {
    local source_json_path manifest_path storage_run_root result_host_dir
    local original_json_name original_storage_mount_path original_clean_results
    local line domain example_id current_storage next_storage
    local index next_index copy_pid task_status overall_status golden_signature current_golden_signature
    local -a task_entries

    if [ "$mount_vm_storage" != true ]; then
        log_error_exit "--isolate-tasks requires --mount-vm-storage true."
    fi
    if [ "$start_client" != true ] || [ "$prepare_image" = true ] || [ "$interactive" = true ] || [ "$connect" = true ]; then
        log_error_exit "--isolate-tasks requires a non-interactive client run with --prepare-image false and --connect false."
    fi
    if [ "$num_workers" -ne 1 ]; then
        log_error_exit "--isolate-tasks currently requires --num-workers 1."
    fi
    if [ ! -f "$vm_storage_base_path/data.img" ]; then
        log_error_exit "Golden VM storage is missing data.img: $vm_storage_base_path"
    fi

    if [[ "$json_name" = /* ]]; then
        source_json_path="$json_name"
    else
        source_json_path="$client_mount_path/$json_name"
    fi
    if [ ! -f "$source_json_path" ]; then
        log_error_exit "Task JSON not found on host: $source_json_path"
    fi

    result_host_dir=""
    if [[ "$result_dir" == /locallstc/* ]]; then
        result_host_dir="$locallstc_root_path/${result_dir#/locallstc/}"
    elif [[ "$result_dir" == /client/* ]]; then
        result_host_dir="$client_mount_path/${result_dir#/client/}"
    elif [[ "$result_dir" != /* ]]; then
        result_host_dir="$client_mount_path/${result_dir#./}"
    fi

    storage_run_root=$(mktemp -d "$SCRIPT_DIR/../src/win-arena-container/vm/task-storage.${container_name}.XXXXXX")
    manifest_path="$storage_run_root/tasks.tsv"
    python3 - "$source_json_path" "$manifest_path" "$result_host_dir" "${LOCALLSTC_EXTRA_ARGS:-}" <<'PY'
import json
import os
import shlex
import sys

source_path, manifest_path, result_dir, extra_args = sys.argv[1:]
extra_argv = shlex.split(extra_args)
rerun = "--rerun" in extra_argv
rerun_fail = "--rerun_fail" in extra_argv

def should_run(domain, example_id):
    if not result_dir or rerun:
        return True
    task_result_dir = os.path.join(result_dir, domain, example_id)
    result_path = os.path.join(task_result_dir, "result.txt")
    error_path = os.path.join(task_result_dir, "err_reason.txt")
    if os.path.exists(error_path) or not os.path.exists(result_path):
        return True
    try:
        with open(result_path, "r", encoding="utf-8") as result_file:
            score = float(result_file.read().strip())
    except (OSError, ValueError):
        return True
    return rerun_fail and score <= 0.0

with open(source_path, "r", encoding="utf-8") as source_file:
    tasks = json.load(source_file)
with open(manifest_path, "w", encoding="utf-8") as manifest_file:
    for domain, example_ids in tasks.items():
        for example_id in example_ids:
            if "\t" in domain or "\t" in example_id or "\n" in domain or "\n" in example_id:
                raise ValueError("Task domain and ID cannot contain tabs or newlines")
            if should_run(domain, example_id):
                manifest_file.write(f"{domain}\t{example_id}\n")
PY
    mapfile -t task_entries < "$manifest_path"
    if [ "${#task_entries[@]}" -eq 0 ]; then
        echo "Task JSON contains no tasks: $source_json_path"
        rm -rf "$storage_run_root"
        return 0
    fi

    original_json_name="$json_name"
    original_storage_mount_path="$vm_storage_mount_path"
    original_clean_results="$clean_results"
    overall_status=0
    golden_signature=$(stat -c '%s:%b:%Y:%Z' "$vm_storage_base_path/data.img")
    cleanup_isolated_run() {
        if [[ "${copy_pid:-}" =~ ^[0-9]+$ ]]; then
            kill "$copy_pid" >/dev/null 2>&1 || true
            wait "$copy_pid" >/dev/null 2>&1 || true
            copy_pid=""
        fi
        docker rm -f "$container_name" >/dev/null 2>&1 || true
        if [[ -n "$storage_run_root" && "$storage_run_root" == */task-storage.* ]]; then
            rm -rf "$storage_run_root"
        fi
    }
    trap cleanup_isolated_run EXIT
    trap 'cleanup_isolated_run; exit 130' INT
    trap 'cleanup_isolated_run; exit 143' TERM

    current_storage="$storage_run_root/storage-0"
    prepare_storage_copy "$current_storage"

    for ((index = 0; index < ${#task_entries[@]}; index++)); do
        line=${task_entries[$index]}
        domain=${line%%$'\t'*}
        example_id=${line#*$'\t'}

        copy_pid=""
        next_index=$((index + 1))
        if [ "$next_index" -lt "${#task_entries[@]}" ]; then
            next_storage="$storage_run_root/storage-$next_index"
            prepare_storage_copy "$next_storage" &
            copy_pid=$!
            echo "Preparing task $((next_index + 1)) storage in background (PID $copy_pid)."
        fi

        task_json_mount_path="$storage_run_root/task-$index.json"
        write_single_task_json "$domain" "$example_id" "$task_json_mount_path"
        vm_storage_mount_path="$current_storage"
        json_name="/winarena-task.json"
        if [ "$index" -gt 0 ]; then
            clean_results=false
        fi

        echo "Running isolated task $((index + 1))/${#task_entries[@]}: $domain/$example_id"
        task_status=0
        invoke_docker_container || task_status=$?

        docker rm -f "$container_name" >/dev/null 2>&1 || true
        rm -rf "$current_storage"

        if [ -n "$copy_pid" ]; then
            if ! wait "$copy_pid"; then
                log_error_exit "Failed to prepare storage for task $((next_index + 1))."
            fi
            current_storage="$next_storage"
        fi

        current_golden_signature=$(stat -c '%s:%b:%Y:%Z' "$vm_storage_base_path/data.img")
        if [ "$current_golden_signature" != "$golden_signature" ]; then
            log_error_exit "Golden VM storage changed while running isolated task $domain/$example_id."
        fi
        if [ "$task_status" -ne 0 ]; then
            overall_status="$task_status"
            echo "WARNING: Isolated task $domain/$example_id exited with status $task_status; continuing with the next fresh storage copy." >&2
        fi
    done

    json_name="$original_json_name"
    vm_storage_mount_path="$original_storage_mount_path"
    clean_results="$original_clean_results"
    task_json_mount_path=""
    trap - EXIT INT TERM
    cleanup_isolated_run
    return "$overall_status"
}

if [ "$isolate_tasks" = true ]; then
    run_isolated_tasks
else
    prepare_vm_storage_mount_path
    invoke_docker_container
fi
