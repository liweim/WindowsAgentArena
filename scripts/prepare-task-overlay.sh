#!/bin/bash
# Called by run.sh. The baseline must be offline and immutable for the batch.
set -euo pipefail

baseline=$(realpath -- "$1")
destination=$(realpath -- "$2")
if [ "$baseline" = "$destination" ] || [ -e "$destination/data.img" ] || [ -e "$destination/data.qcow2" ]; then
    echo "Refusing to overwrite existing task disks: $destination" >&2
    exit 1
fi
if [ -e "$baseline/data.qcow2" ]; then
    echo "Ambiguous baseline: both data.img and data.qcow2 exist in $baseline" >&2
    exit 1
fi

# Include hidden files and all auxiliary state, but never copy the system disk.
shopt -s dotglob nullglob
for entry in "$baseline"/*; do
    [ "${entry##*/}" = data.img ] && continue
    cp -a --reflink=auto --sparse=always -- "$entry" "$destination/"
done
qemu-img create -q -f qcow2 -F raw -b "$baseline/data.img" "$destination/data.qcow2"
