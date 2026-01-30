#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Configuration
# -------------------------
STATE_FILE="$HOME/.config/dotidx/state.conf"
BASE_BACKUP="$HOME/dotidxBackup"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: No active profile found. Run 'dotidx profile <name>'."
    exit 1
fi

PROFILE=$(cat "$STATE_FILE")
BACKUP="$BASE_BACKUP/$PROFILE"

# -------------------------
# Verify backup exists
# -------------------------
if [ ! -d "$BACKUP" ]; then
    echo "Backup directory for profile '$PROFILE' not found: $BACKUP"
    exit 1
fi

echo "Syncing profile: $PROFILE (REPLACEMENT MODE)..."

# -------------------------
# SYNC PHASE
# -------------------------
failed=false
permission_errors=()

# Iterate through files in the specific profile backup folder
while IFS= read -r -d '' backup_file; do
    # Calculate path relative to the profile directory
    rel_path="${backup_file#$BACKUP/}"
    home_file="$HOME/$rel_path"
    
    if [ ! -e "$home_file" ]; then
        echo "ERROR: File does not exist in home: $home_file"
        failed=true
    else
        # Use rsync or cp to overwrite existing file in HOME with backup content
        if cp -a "$backup_file" "$home_file" 2>/dev/null; then
            echo "Replaced: $home_file"
        else
            echo "SKIPPED (permission denied): $home_file"
            permission_errors+=("$home_file")
        fi
    fi
done < <(find "$BACKUP" -type f -not -path "*/.git/*" -print0)

# -------------------------
# Summary
# -------------------------
if [ ${#permission_errors[@]} -gt 0 ]; then
    echo ""
    echo "Warning: ${#permission_errors[@]} file(s) skipped due to permission errors in profile '$PROFILE':"
    for file in "${permission_errors[@]}"; do
        echo "  - $file"
    done
fi

if [ "$failed" = true ]; then
    echo ""
    echo "Sync failed: some files in the '$PROFILE' backup don't exist in your home directory."
    exit 1
fi

echo "Sync complete for profile '$PROFILE'."
