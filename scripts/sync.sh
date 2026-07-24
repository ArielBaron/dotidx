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
        rsync -a -v --exclude='.git' "$entry/" "$HOME/" || echo "[WARN] Skipped unwriteable or restricted files in $entry" >&2
    else
        target="/$base"
        sudo rsync -a -v --exclude='.git' "$entry/" "$target/" || echo "[WARN] Skipped unwriteable or restricted files in $entry" >&2
    fi
done