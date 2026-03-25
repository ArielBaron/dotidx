#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="$HOME/.config/dotidx/state.conf"
BASE_BACKUP="$HOME/dotidxBackup"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: No active profile found."
    exit 1
fi

PROFILE=$(cat "$STATE_FILE")
BACKUP="$BASE_BACKUP/$PROFILE"

if [ ! -d "$BACKUP" ]; then
    echo "Backup directory not found: $BACKUP"
    exit 1
fi

echo "Restoring profile: $PROFILE..."

# Iterate through all files in the backup
while IFS= read -r -d '' backup_file; do
    rel_path="${backup_file#$BACKUP/}"

    # Map home files relative to $HOME
    if [[ "$rel_path" == "~/"* ]]; then
        rel_path="${rel_path#??}"  # remove leading ~/
        home_file="$HOME/$rel_path"
    else
        home_file="$rel_path"  # absolute system path
    fi

    mkdir -p "$(dirname "$home_file")"
    cp -RL "$backup_file" "$home_file" && echo "Restored: $home_file"
done < <(find "$BACKUP" -type f -not -path "*/.git/*" -print0)

echo "Sync complete."
