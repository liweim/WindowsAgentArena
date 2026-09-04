#!/usr/bin/env bash

set -e
set -o pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
source "${SCRIPT_DIR}/shared.sh"

# Defaults follow LocalGUI/run_win.sh while every existing launcher option
# remains available below.
mode="dev"
prepare_image=false
skip_build=true
interactive=false
connect=false
use_kvm=true
ram_size=8G
cpu_cores=8
mount_vm_storage=true
ephemeral_vm_storage=false
mount_client=true
mount_server=true
container_name="winarena-locallstc"
browser_port=18112
rdp_port=13391
start_client=true
agent="locallstc"
model="qwen3.6-27b"
temperature=0
seed=42
top_p=0.95
top_k=20
som_origin="oss"
a11y_backend="uia"
gpu_enabled=false
clean_results=false
worker_id=0
num_workers=1
result_dir="/locallstc/projects/WindowsAgentArena/results/locallstc_qwen3.6-27b"
result_dir_explicit=false
json_name="evaluation_examples_windows/test_one.json"
diff_lvl="normal"
remove_container=false
isolate_tasks=true
isolate_tasks_explicit=false
storage_base_path=""

# run_win.sh-style lifecycle options. Use --detach false to retain the old
# foreground behavior, and --replace-container false to protect an existing
# container with the requested name.
detach=true
detach_explicit=false
replace_container=true
log_file=""
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
        --result-dir) result_dir=$2; result_dir_explicit=true; shift 2 ;;
        --json-name) json_name=$2; shift 2 ;;
        --diff-lvl) diff_lvl=$2; shift 2 ;;
        --remove-container) remove_container=$2; shift 2 ;;
        --isolate-tasks) isolate_tasks=$2; isolate_tasks_explicit=true; shift 2 ;;
        --storage-base-path) storage_base_path=$2; shift 2 ;;
        --mode) mode=$2; shift 2 ;;
        --detach) detach=$2; detach_explicit=true; shift 2 ;;
        --replace-container) replace_container=$2; shift 2 ;;
        --log-file) log_file=$2; shift 2 ;;
        --help)
            cat <<'EOF'
Usage: ./run-local.sh [launcher options] [agent options]

Launcher options:
  --container-name <name>          Container name (default: winarena-locallstc)
  --prepare-image <true/false>     Prepare an arena golden image (default: false)
  --skip-build <true/false>        Skip building the container image (default: true)
  --interactive <true/false>       Open an interactive container (default: false)
  --connect <true/false>           Connect to an existing container (default: false)
  --use-kvm <true/false>           Enable KVM acceleration (default: true)
  --ram-size <size>                VM memory (default: 8G)
  --cpu-cores <count>              VM CPU cores (default: 8)
  --mount-vm-storage <true/false>  Mount VM storage (default: true)
  --ephemeral-vm-storage <bool>    Use a temporary VM storage copy (default: false)
  --mount-client <true/false>      Mount the client source (default: true)
  --mount-server <true/false>      Mount the server source (default: true)
  --browser-port <port>            Browser/VNC port (default: 18112)
  --rdp-port <port>                RDP port (default: 13391)
  --start-client <true/false>      Start the arena client (default: true)
  --agent <name>                   Agent (default: locallstc)
  --model <name>                   Model (default: qwen3.6-27b)
  --temperature <value>            Sampling temperature (default: 0)
  --seed <value>                   Sampling seed (default: 42)
  --top-p <value>                  Top-p sampling value (default: 0.95)
  --top-k <value>                  Top-k sampling value (default: 20)
  --som-origin <name>              SoM source (default: oss)
  --a11y-backend <name>            Accessibility backend (default: uia)
  --gpu-enabled <true/false>       Enable GPU access (default: false)
  --clean-results <true/false>     Clean result directory (default: false)
  --worker-id <id>                 Worker ID (default: 0)
  --num-workers <count>            Worker count (default: 1)
  --result-dir <path>              Result directory inside the container
  --json-name <path>               Task metadata under /client
  --diff-lvl <level>               Benchmark difficulty (default: normal)
  --remove-container <true/false>  Auto-remove the container (default: false)
  --isolate-tasks <true/false>     Use fresh VM storage per task (default: true)
  --storage-base-path <path>       Golden VM storage path
  --mode <dev/azure>               Image mode (default: dev)
  --detach <true/false>            Run through nohup/setsid (default: true)
  --replace-container <bool>       Replace a same-name container (default: true)
  --log-file <path>                Detached log file

Unrecognized options are forwarded to the selected agent parser.
EOF
            exit 0
            ;;
        *) method_cli_args+=("$1"); shift ;;
    esac
done

case "$detach" in
    true|false) ;;
    *) log_error_exit "--detach must be true or false." ;;
esac
case "$replace_container" in
    true|false) ;;
    *) log_error_exit "--replace-container must be true or false." ;;
esac
if [ "$detach" = true ] && { [ "$interactive" = true ] || [ "$connect" = true ]; }; then
    if [ "$detach_explicit" = true ]; then
        log_error_exit "--detach true cannot be combined with --interactive true or --connect true."
    fi
    detach=false
fi
if [ "$isolate_tasks_explicit" = false ] && \
   { [ "$prepare_image" = true ] || [ "$interactive" = true ] || \
     [ "$start_client" != true ] || [ "$ephemeral_vm_storage" = true ]; }; then
    isolate_tasks=false
fi
if [ "$result_dir_explicit" = false ]; then
    if [ "$agent" = "locallstc" ]; then
        result_dir="/locallstc/projects/WindowsAgentArena/results/locallstc_${model}"
    else
        result_dir="./results"
    fi
fi

if [ "$agent" = "locallstc" ]; then
    export WINARENA_IMAGE_TAG="${WINARENA_IMAGE_TAG:-locallstc-stable}"
fi

task_storage_parent="${ROOT_DIR}/src/win-arena-container/vm"
client_root="${ROOT_DIR}/src/win-arena-container/client"
locallstc_host_root="$(getrealpath "${SCRIPT_DIR}/../../..")"

resolve_result_host_dir() {
    case "$result_dir" in
        /locallstc/*)
            printf '%s/%s\n' "$locallstc_host_root" "${result_dir#/locallstc/}"
            ;;
        /client/*)
            printf '%s/%s\n' "$client_root" "${result_dir#/client/}"
            ;;
        /*)
            return 1
            ;;
        *)
            printf '%s/%s\n' "$client_root" "${result_dir#./}"
            ;;
    esac
}

result_host_dir="$(resolve_result_host_dir || true)"
if [ -n "$result_host_dir" ]; then
    mkdir -p "$result_host_dir"
fi

repair_result_ownership() {
    local host_uid host_gid mismatched_owner_path

    [ -n "$result_host_dir" ] || return 0
    host_uid="$(id -u)"
    host_gid="$(id -g)"
    mismatched_owner_path="$({
        find "$result_host_dir" ! -uid "$host_uid" -print -quit
    } 2>/dev/null || true)"
    [ -n "$mismatched_owner_path" ] || return 0

    if ! docker image inspect "${image_repository}:${image_tag}" >/dev/null 2>&1; then
        echo "Warning: cannot repair result ownership before image ${image_repository}:${image_tag} is built."
        return 0
    fi

    echo "Repairing result ownership left by an interrupted container run."
    docker run --rm --user 0 \
        --volume "${result_host_dir}:/results" \
        --entrypoint /bin/chown \
        "${image_repository}:${image_tag}" \
        -R "${host_uid}:${host_gid}" /results
}

apply_result_acl() {
    local host_uid

    [ -n "$result_host_dir" ] || return 0
    command -v setfacl >/dev/null 2>&1 || return 0
    host_uid="$(id -u)"
    if ! setfacl -R -m "u:${host_uid}:rwX" "$result_host_dir"; then
        echo "Warning: could not update access ACLs under $result_host_dir."
    fi
    if ! setfacl -R -d -m "u:${host_uid}:rwX" "$result_host_dir"; then
        echo "Warning: could not update default ACLs on $result_host_dir."
    fi
}

if [ "$connect" != true ] && [ "$start_client" = true ] && [ "$isolate_tasks" = true ]; then
    if [[ "$json_name" = /* ]]; then
        task_meta_path="$json_name"
    else
        task_meta_path="${client_root}/${json_name}"
    fi
    if [ ! -f "$task_meta_path" ]; then
        log_error_exit "Task metadata does not exist: $task_meta_path"
    fi

    if [ -n "$storage_base_path" ]; then
        if [[ "$storage_base_path" = /* ]]; then
            storage_check_path="$(getrealpath "$storage_base_path")"
        else
            storage_check_path="$(getrealpath "${SCRIPT_DIR}/${storage_base_path}")"
        fi
    else
        storage_check_path="${ROOT_DIR}/src/win-arena-container/vm/storage"
    fi
    if [ ! -f "${storage_check_path}/data.img" ]; then
        log_error_exit "Golden VM storage is missing data.img: $storage_check_path"
    fi
fi

cleanup_stale_task_storage() {
    local stale_path

    [ "$isolate_tasks" = true ] || return 0
    while IFS= read -r -d '' stale_path; do
        case "$stale_path" in
            "$task_storage_parent"/task-storage."$container_name".*)
                echo "Removing stale isolated VM storage: $stale_path"
                rm -rf -- "$stale_path"
                ;;
        esac
    done < <(
        find "$task_storage_parent" -mindepth 1 -maxdepth 1 -type d \
            -name "task-storage.${container_name}.*" -print0
    )
}

container_result_dir="$result_dir"
if [[ "$container_result_dir" != /* ]]; then
    container_result_dir="/client/${container_result_dir#./}"
fi

if ! docker info >/dev/null 2>&1; then
    log_error_exit "Docker daemon is not running or is not accessible."
fi

if [ "$mode" = "dev" ]; then
    image_repository="windowsarena/winarena-dev"
else
    image_repository="windowsarena/winarena"
fi
image_tag="${WINARENA_IMAGE_TAG:-latest}"

if [ "$connect" != true ] && [ "$skip_build" = true ]; then
    if ! docker image inspect "${image_repository}:${image_tag}" >/dev/null 2>&1; then
        log_error_exit "Docker image does not exist: ${image_repository}:${image_tag}"
    fi
fi

if [ "$connect" != true ]; then
    if docker inspect "$container_name" >/dev/null 2>&1; then
        if [ "$replace_container" != true ]; then
            log_error_exit "Container $container_name already exists; use --replace-container true or another --container-name."
        fi
        docker exec --user 0 "$container_name" \
            chown -R "$(id -u):$(id -g)" "$container_result_dir" \
            >/dev/null 2>&1 || true
        docker rm -f "$container_name" >/dev/null
    fi
    cleanup_stale_task_storage
    repair_result_ownership
fi
apply_result_acl

config_file_path="${ROOT_DIR}/config.json"
echo "Using configuration file: $config_file_path"
echo "Using mode: $mode"

if [[ -f "$config_file_path" ]]; then
    OPENAI_API_KEY="$(extract_json_field_from_file "OPENAI_API_KEY" "$config_file_path" || true)"
    AZURE_API_KEY="$(extract_json_field_from_file "AZURE_API_KEY" "$config_file_path" || true)"
    AZURE_ENDPOINT="$(extract_json_field_from_file "AZURE_ENDPOINT" "$config_file_path" || true)"
else
    echo "Configuration file not found; continuing without remote API keys."
    OPENAI_API_KEY=""
    AZURE_API_KEY=""
    AZURE_ENDPOINT=""
fi

export PYTHONUNBUFFERED=1
export LOCALLSTC_HOST_UID="${LOCALLSTC_HOST_UID:-$(id -u)}"
export LOCALLSTC_HOST_GID="${LOCALLSTC_HOST_GID:-$(id -g)}"

if [ "$agent" = "locallstc" ]; then
    locallstc_args=(
        --global_planner_model "$model"
        --visual_grounder_model gta1-7b
        --state_manager_model "$model"
        --thinking_token_budget 16384
        --max_steps 100
        --bash_timeout 180
        --rerun_fail
    )
    printf -v default_locallstc_args '%q ' "${locallstc_args[@]}"
    cli_locallstc_args=""
    if [ ${#method_cli_args[@]} -gt 0 ]; then
        printf -v cli_locallstc_args '%q ' "${method_cli_args[@]}"
    fi
    LOCALLSTC_EXTRA_ARGS="${default_locallstc_args}${LOCALLSTC_EXTRA_ARGS:-} ${cli_locallstc_args}"
    export LOCALLSTC_EXTRA_ARGS
fi

run_args=(
    "${SCRIPT_DIR}/run.sh"
    --mode "$mode"
    --prepare-image "$prepare_image"
    --container-name "$container_name"
    --skip-build "$skip_build"
    --interactive "$interactive"
    --connect "$connect"
    --use-kvm "$use_kvm"
    --ram-size "$ram_size"
    --cpu-cores "$cpu_cores"
    --mount-vm-storage "$mount_vm_storage"
    --ephemeral-vm-storage "$ephemeral_vm_storage"
    --mount-client "$mount_client"
    --mount-server "$mount_server"
    --browser-port "$browser_port"
    --rdp-port "$rdp_port"
    --start-client "$start_client"
    --agent "$agent"
    --model "$model"
    --temperature "$temperature"
    --seed "$seed"
    --top-p "$top_p"
    --top-k "$top_k"
    --som-origin "$som_origin"
    --a11y-backend "$a11y_backend"
    --gpu-enabled "$gpu_enabled"
    --clean-results "$clean_results"
    --worker-id "$worker_id"
    --num-workers "$num_workers"
    --result-dir "$result_dir"
    --json-name "$json_name"
    --diff-lvl "$diff_lvl"
    --remove-container "$remove_container"
    --isolate-tasks "$isolate_tasks"
)
if [[ -n "$storage_base_path" ]]; then
    run_args+=(--storage-base-path "$storage_base_path")
fi
if [ "$agent" != "locallstc" ] && [ ${#method_cli_args[@]} -gt 0 ]; then
    run_args+=("${method_cli_args[@]}")
fi
if [ -n "$OPENAI_API_KEY" ]; then
    run_args+=(--openai-api-key "$OPENAI_API_KEY")
fi
if [ -n "$AZURE_API_KEY" ]; then
    run_args+=(--azure-api-key "$AZURE_API_KEY")
fi
if [ -n "$AZURE_ENDPOINT" ]; then
    run_args+=(--azure-endpoint "$AZURE_ENDPOINT")
fi

cd "$SCRIPT_DIR"

if [ "$detach" = false ]; then
    exec "${run_args[@]}"
fi

safe_container_name="$(printf '%s' "$container_name" | tr -cs 'A-Za-z0-9_.@-' '-')"
run_id_raw="${RUN_NAME:-$(date +%Y%m%d-%H%M%S)-$$}"
run_id="$(printf '%s' "$run_id_raw" | tr -cs 'A-Za-z0-9_.:@-' '-')"
if [ -z "$log_file" ]; then
    log_file="${ROOT_DIR}/nohup.out"
fi
runner_pid_file="${ROOT_DIR}/run_${safe_container_name}.runner.pid"
mkdir -p "$(dirname -- "$log_file")"

nohup setsid "${run_args[@]}" >"$log_file" 2>&1 < /dev/null &
runner_pid=$!
printf '%s\n' "$runner_pid" >"$runner_pid_file"

echo "Started run $run_id in container $container_name"
echo "Runner PID: $runner_pid"
echo "PID file: $runner_pid_file"
echo "Logs: tail -f $log_file"
echo "Browser: http://localhost:$browser_port"
echo "RDP: localhost:$rdp_port"
