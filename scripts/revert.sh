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
TRACK_CONF="$HOME/.config/dotidx/${PROFILE}_track.conf"

# number of commits to go back (default 1)
N="${1:-1}"

if [ ! -d "$BACKUP/.git" ]; then
    echo "Error: Backup is not a git repository."
    exit 1
fi

cd "$BACKUP"

# ensure we have enough commits
TOTAL_COMMITS=$(git rev-list --count HEAD)
if [ "$TOTAL_COMMITS" -le "$N" ]; then
    echo "Error: Not enough commits to revert $N steps."
    exit 1
fi

echo "Reverting $N commit(s)..."

# hard reset to N commits back
git reset --hard "HEAD~$N"

echo "Git history moved back."

# restore working tree already handled by reset
echo "Working tree restored."

# sync track.conf from backup (if exists)
BACKUP_TRACK="$BACKUP/track.conf"

if [ -f "$BACKUP_TRACK" ]; then
    echo "Restoring tracking configuration..."
    cp "$BACKUP_TRACK" "$TRACK_CONF"
else
    echo "Warning: No track.conf found in backup."
fi

echo "✅ Revert complete."