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

# Iterate and force overwrite
while IFS= read -r -d '' backup_file; do
    rel_path="${backup_file#$BACKUP/}"
    home_file="$HOME/$rel_path"
    
    # Ensure target directory exists
    mkdir -p "$(dirname "$home_file")"
    
    # Force copy backup over home
    if cp -f "$backup_file" "$home_file"; then
        echo "Restored: $home_file"
    else
        echo "FAILED: $home_file"
    fi
done < <(find "$BACKUP" -type f -not -path "*/.git/*" -print0)

echo "Sync complete."
