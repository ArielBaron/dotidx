#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Configuration
# -------------------------
CONFIG_DIR="$HOME/.config/dotidx"
STATE_FILE="$CONFIG_DIR/state.conf"
TRACK_CONF="$CONFIG_DIR/track.conf"
BASE_BACKUP="$HOME/dotidxBackup"

# Verify profile exists before destructive actions
if [ ! -f "$STATE_FILE" ]; then
    echo "Error: No active profile found. Nothing to clear."
    exit 1
fi

PROFILE=$(cat "$STATE_FILE")
PROFILE_BACKUP="$BASE_BACKUP/$PROFILE"

# -------------------------
# DESTRUCTIVE PHASE
# -------------------------
# 1. Remove profile-specific backup folder
if [ -d "$PROFILE_BACKUP" ]; then
    rm -rf "$PROFILE_BACKUP"
    echo "Deleted backup directory for profile: $PROFILE"
fi

# 2. Scrub profile from track.conf using jq
if [ -f "$TRACK_CONF" ]; then
    # Removes the profile from all lists; deletes keys that become empty
    tmp=$(mktemp)
    jq --arg prof "$PROFILE" '
        with_entries(
            .value |= map(select(. != $prof)) | 
            select(.value | length > 0)
        )' "$TRACK_CONF" > "$tmp" && mv "$tmp" "$TRACK_CONF"
    echo "Removed '$PROFILE' from tracking configuration."
fi

# 3. Remove session state
rm -f "$STATE_FILE"

echo "Clear complete for profile: $PROFILE"
