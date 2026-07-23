#!/usr/bin/env bash
set -euo pipefail

STATE=$(cat ~/.config/dotidx/state.conf)
BACKUP_DIR="$HOME/dotidxBackup/$STATE"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Backup directory $BACKUP_DIR does not exist." >&2
    exit 1
fi

shopt -s dotglob
for entry in "$BACKUP_DIR"/* "$BACKUP_DIR"/.*; do
    [ -e "$entry" ] || continue
    base=$(basename "$entry")
    if [ "$base" = "." ] || [ "$base" = ".." ]; then
        continue
    elif [ "$base" = "~" ]; then
        cp -a -v "$entry/." "$HOME/"
    else
        target="/$base"
        sudo cp -a -v "$entry/." "$target/"
    fi
done