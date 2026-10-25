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
    # VM state files can inherit host ACL entries that are not representable
    # on the task-storage filesystem (for example UID 4294967295). They are not
    # guest state, so copy the data and timestamps without host ACLs/xattrs,
    # then restore the ordinary Unix mode.
    cp -a --no-preserve=mode,ownership,xattr --reflink=auto --sparse=always -- "$entry" "$destination/"
    if [ ! -L "$entry" ]; then
        chmod --reference="$entry" "$destination/${entry##*/}"
    fi
done
qemu-img create -q -f qcow2 -F raw -b "$baseline/data.img" "$destination/data.qcow2"
