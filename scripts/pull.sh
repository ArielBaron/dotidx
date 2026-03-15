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

# 1. Check if the directory exists to get the remote URL
if [ -d "$BACKUP/.git" ]; then
  echo "Found existing profile at $BACKUP. Getting remote URL..."
  REMOTE_URL=$(git -C "$BACKUP" remote get-url origin)
else
  echo "Error: Backup directory not found or not a git repo: $BACKUP"
  echo "Cannot 're-clone' without a source URL."
  exit 1
fi

# 2. THE NUKE OPTION: Delete and Re-clone
echo "⚠️  Deleting local $PROFILE and performing a fresh clone..."
rm -rf "$BACKUP"

# 3. Clone fresh
# We use --recurse-submodules just in case your dots use them
if git clone "$REMOTE_URL" "$BACKUP"; then
  echo "✅ Successfully re-cloned $PROFILE from $REMOTE_URL"
else
  echo "❌ Failed to clone $PROFILE"
  exit 1
fi

echo "Done. Profile is now in sync with remote (all local changes discarded)."

echo "✅ Successfully updated $PROFILE"
