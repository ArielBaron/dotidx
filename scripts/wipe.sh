#!/usr/bin/env bash
set -euo pipefail
CONFIG_DIR="$HOME/.config/dotidx"
STATE_FILE="$CONFIG_DIR/state.conf"
BASE_BACKUP="$HOME/dotidxBackup"
if [ ! -f "$STATE_FILE" ]; then
  echo "Error: No active profile found."
  exit 1
fi
PROFILE=$(cat "$STATE_FILE")
PROFILE_BACKUP="$BASE_BACKUP/$PROFILE"
TRACK_CONF="$CONFIG_DIR/${PROFILE}_track.conf"
echo "Wiping profile: $PROFILE"
if [ -d "$PROFILE_BACKUP" ]; then
  rm -rf "$PROFILE_BACKUP"
  echo "Deleted backup directory: $PROFILE_BACKUP"
fi
if [ -f "$TRACK_CONF" ]; then
  rm -f "$TRACK_CONF"
  echo "Deleted tracking config: $TRACK_CONF"
fi
rm -f "$STATE_FILE"
echo "Wipe complete for profile: $PROFILE"

