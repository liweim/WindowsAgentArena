#!/usr/bin/env bash

set -u

if (($# > 1)); then
    echo "Usage: $0 [agent-or-run-id-or-container-name]" >&2
    exit 2
fi

selector="${1:-}"
run_state_dir="${WAA_RUN_STATE_DIR:-/tmp/windows-agent-arena-runs-$(id -u)}"
declare -A process_groups=()
declare -A run_ids=()
declare -A containers=()

matches_selector() {
    local run_id=$1
    local container_base=$2
    local agent=${3:-}
    [ -z "$selector" ] || [ "$selector" = "$run_id" ] || \
        [ "$selector" = "$container_base" ] || [ "$selector" = "$agent" ] || \
        [[ "$selector" == "$container_base"-w* ]]
}

# State files cover the interval before the first worker container exists and
# map an automatically generated run ID back to its detached process group.
if [ -d "$run_state_dir" ]; then
    while IFS=$'\t' read -r run_id pid pgid container_base agent; do
        [[ -n "${run_id:-}" && -n "${pid:-}" && -n "${pgid:-}" ]] || continue
        process_args=$(ps -p "$pid" -o args= 2>/dev/null || true)
        if ! kill -0 "$pid" 2>/dev/null || \
           ! [[ "$process_args" =~ (^|[[:space:]])([^[:space:]]*/)?run\.sh([[:space:]]|$) ]]; then
            rm -f "$run_state_dir/$run_id.tsv"
            continue
        fi
        if matches_selector "$run_id" "$container_base" "${agent:-}"; then
            run_ids["$run_id"]=1
            process_groups["$pgid"]=1
        fi
    done < <(cat "$run_state_dir"/*.tsv 2>/dev/null || true)
fi

# Labels find every worker container without requiring its generated name.
while read -r container_id; do
    [ -n "$container_id" ] || continue
    run_id=$(docker inspect --format '{{index .Config.Labels "waa.run-id"}}' "$container_id" 2>/dev/null || true)
    agent=$(docker inspect --format '{{index .Config.Labels "waa.agent"}}' "$container_id" 2>/dev/null || true)
    container_name=$(docker inspect --format '{{.Name}}' "$container_id" 2>/dev/null || true)
    container_name=${container_name#/}
    if [ -z "$selector" ] || [ "$selector" = "$run_id" ] || \
       [ "$selector" = "$agent" ] || [ "$selector" = "$container_name" ]; then
        containers["$container_id"]=1
        [ -n "$run_id" ] && run_ids["$run_id"]=1
    fi
done < <(docker ps -aq --filter label=waa.managed=true 2>/dev/null)

# Backward-compatible fallback for old launchers with an explicit container
# name. With no selector, only new state-managed task runs are stopped.
if [ -n "$selector" ]; then
    while read -r pid pgid args; do
        [[ -n "${pid:-}" && -n "${pgid:-}" ]] || continue
        [[ "$args" =~ (^|[[:space:]])([^[:space:]]*/)?run\.sh([[:space:]]|$) ]] || continue
        if [[ "$args" == *"--container-name $selector"* ]]; then
            process_groups["$pgid"]=1
        fi
    done < <(ps -eo pid=,pgid=,args=)
fi

for pgid in "${!process_groups[@]}"; do
    echo "Stopping process group $pgid"
    kill -TERM -- "-$pgid" 2>/dev/null || true
done

# Give run.sh a short opportunity to run its cleanup trap.
for _ in {1..10}; do
    remaining=false
    for pgid in "${!process_groups[@]}"; do
        if kill -0 -- "-$pgid" 2>/dev/null; then
            remaining=true
            break
        fi
    done
    "$remaining" || break
    sleep 1
done

for pgid in "${!process_groups[@]}"; do
    if kill -0 -- "-$pgid" 2>/dev/null; then
        echo "Force-stopping process group $pgid"
        kill -KILL -- "-$pgid" 2>/dev/null || true
    fi
done

# Refresh after stopping because a worker may have started during shutdown.
for run_id in "${!run_ids[@]}"; do
    while read -r container_id; do
        [ -n "$container_id" ] && containers["$container_id"]=1
    done < <(docker ps -aq --filter "label=waa.run-id=$run_id" 2>/dev/null)
done

for container_id in "${!containers[@]}"; do
    container_name=$(docker inspect --format '{{.Name}}' "$container_id" 2>/dev/null || true)
    container_name=${container_name#/}
    echo "Removing container ${container_name:-$container_id}"
    docker rm -f "$container_id" >/dev/null 2>&1 || true
done

if ((${#process_groups[@]} == 0 && ${#containers[@]} == 0)); then
    if [ -n "$selector" ]; then
        echo "No running task group or container matched: $selector"
    else
        echo "No running WindowsAgentArena task groups found"
    fi
else
    echo "Selected task run(s) stopped"
fi
