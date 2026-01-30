#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Configuration
# -------------------------
STATE_FILE="$HOME/.config/dotidx/state.conf"
TRACK_CONF="$HOME/.config/dotidx/track.conf"
BASE_BACKUP="$HOME/dotidxBackup"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: No active profile found."
    exit 1
fi

PROFILE=$(cat "$STATE_FILE")
BACKUP="$BASE_BACKUP/$PROFILE"
mkdir -p "$BACKUP"

# -------------------------
# Load tracked paths
# -------------------------
if [ ! -s "$TRACK_CONF" ]; then
    echo "No tracking configuration found."
    exit 0
fi

mapfile -t TRACKED < <(jq -r --arg prof "$PROFILE" 'to_entries[] | select(.value | index($prof)) | .key' "$TRACK_CONF" | sed "s|^~|$HOME|")

if [ ${#TRACKED[@]} -eq 0 ]; then
    echo "No files tracked for profile: $PROFILE"
    exit 0
fi

# -------------------------
# COPY PHASE
# -------------------------
for src in "${TRACKED[@]}"; do
    [ ! -e "$src" ] && continue
    dst="$BACKUP${src#$HOME}"
    mkdir -p "$(dirname "$dst")"
    if [ -d "$src" ]; then
        # Use rsync to mirror content
        rsync -a --copy-links --safe-links --delete --exclude ".git" "$src/" "$dst/"
    else
        cp -RL "$src" "$dst"
    fi
done

# -------------------------
# CLEANUP PHASE
# -------------------------
# We only delete files inside $BACKUP that are NOT in the tracking list
# and NOT part of the .git directory.
find "$BACKUP" -mindepth 1 -not -path "$BACKUP/.git*" | while read -r path; do
    keep=false
    for t in "${TRACKED[@]}"; do
        tracked_dst="$BACKUP${t#$HOME}"
        # Keep if path is tracked_dst, or a parent of tracked_dst, or a child of tracked_dst
        if [[ "$tracked_dst" == "$path"* ]] || [[ "$path" == "$tracked_dst"* ]]; then
            keep=true
            break
        fi
    done
    if [ "$keep" = false ]; then
        rm -rf "$path"
    fi
done

# -------------------------
# GIT PHASE
# -------------------------
if [ -d "$BACKUP/.git" ]; then
    cd "$BACKUP"
    # Basic check to ensure it's a repo
    if [ -f ".git/config" ]; then
        git add -A
        git commit -m "auto-update [$PROFILE] ($(date '+%Y-%m-%d %H:%M:%S'))" || echo "Nothing to commit"
        git push origin "$(git rev-parse --abbrev-ref HEAD)" || echo "Push failed"
    else
        echo "Error: .git directory is corrupted in $BACKUP"
    fi
else
    echo "No .git found for profile '$PROFILE'."
fi

echo "Backup complete for profile '$PROFILE'."
