#!/usr/bin/env bash

set -u

if (($# != 1)); then
    echo "Usage: $0 <container-name>" >&2
    exit 2
fi

container_name="$1"

declare -A process_groups=()

# Locate the detached run.sh process for the selected task. Killing the whole
# process group also stops all of its children.
while read -r pid pgid args; do
    [[ -n "${pid:-}" && -n "${pgid:-}" ]] || continue

    if [[ "$args" == *"run.sh"* && "$args" == *"--container-name $container_name"* ]]; then
        process_groups["$pgid"]=1
    fi
done < <(ps -eo pid=,pgid=,args=)

if ((${#process_groups[@]})); then
    for pgid in "${!process_groups[@]}"; do
        echo "Stopping process group $pgid"
        kill -TERM -- "-$pgid" 2>/dev/null || true
    done

    # Give run.sh a short opportunity to remove its container cleanly.
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
else
    echo "No matching run.sh process found for container $container_name"
fi

# Remove the matching container if it remains. A missing container is harmless.
if docker inspect "$container_name" >/dev/null 2>&1; then
    echo "Removing container $container_name"
    docker rm -f "$container_name" >/dev/null
fi

echo "Process and container $container_name are stopped"
