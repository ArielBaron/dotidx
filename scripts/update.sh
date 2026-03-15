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

# Get just the filename (e.g., converts /home/ariel/.zshrc -> .zshrc)
INPUT_RAW="${1:-}"
INPUT=$(basename "$INPUT_RAW")

# -------------------------
# Path Discovery Logic
# -------------------------
TARGET_SRC=""

if [ -n "$INPUT" ]; then
  # Define the search candidates within the backup folder
  CANDIDATES=(
    "$BACKUP/$INPUT"
    "$BACKUP/$INPUT.conf"
    "$BACKUP/.config/$INPUT"
    "$BACKUP/.config/$INPUT.conf"
  )

  for cand in "${CANDIDATES[@]}"; do
    if [ -e "$cand" ]; then
      # Map the backup path back to the real system path
      # Remove the $BACKUP prefix from the candidate path
      rel_to_backup="${cand#$BACKUP}"

      # Construct the system path: $HOME + the relative part
      TARGET_SRC="$HOME$rel_to_backup"

      # If we matched a .conf candidate, check if the real file is without .conf
      if [[ "$TARGET_SRC" == *.conf ]] && [ ! -e "$TARGET_SRC" ]; then
        TARGET_SRC="${TARGET_SRC%.conf}"
      fi

      if [ -e "$TARGET_SRC" ]; then
        echo "Matched '$INPUT' to system path: $TARGET_SRC"
        break
      else
        TARGET_SRC="" # Reset and keep looking if system file doesn't exist
      fi
    fi
  done

  if [ -z "$TARGET_SRC" ]; then
    echo "Error: Could not find a tracked match for '$INPUT' in $PROFILE backup structure."
    exit 1
  fi
fi

# -------------------------
# Load tracked paths
# -------------------------
if [ ! -s "$TRACK_CONF" ]; then
  echo "No tracking configuration found."
  exit 0
fi

mapfile -t TRACKED < <(jq -r --arg prof "$PROFILE" 'to_entries[] | select(.value | index($prof)) | .key' "$TRACK_CONF" | sed "s|^~|$HOME|")

# -------------------------
# COPY PHASE
# -------------------------
updated=false
for src in "${TRACKED[@]}"; do
  [ ! -e "$src" ] && continue

  # If a target was discovered, only sync that specific path
  if [ -n "$TARGET_SRC" ] && [ "$src" != "$TARGET_SRC" ]; then
    continue
  fi

  dst="$BACKUP${src#$HOME}"
  mkdir -p "$(dirname "$dst")"

  echo "Updating: $src"
  if [ -d "$src" ]; then
    rsync -a --copy-links --safe-links --delete --exclude ".git" "$src/" "$dst/"
  else
    cp -RL "$src" "$dst"
  fi
  updated=true
done

# -------------------------
# CLEANUP PHASE (Full update only)
# -------------------------
if [ -z "$INPUT" ]; then
  find "$BACKUP" -mindepth 1 -not -path "$BACKUP/.git*" | while read -r path; do
    keep=false
    for t in "${TRACKED[@]}"; do
      tracked_dst="$BACKUP${t#$HOME}"
      if [[ "$tracked_dst" == "$path"* ]] || [[ "$path" == "$tracked_dst"* ]]; then
        keep=true
        break
      fi
    done
    [ "$keep" = false ] && rm -rf "$path"
  done
fi
# -------------------------
# GIT PHASE
# -------------------------
if [ -d "$BACKUP/.git" ]; then
  cd "$BACKUP"
  git add -A

  # Get a clean timestamp
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  # Create a dynamic message
  if [ -n "$INPUT" ]; then
    MSG="auto-update [$PROFILE] $INPUT ($TIMESTAMP)"
  else
    MSG="auto-update [$PROFILE] all ($TIMESTAMP)"
  fi

  # Commit and push
  # '|| true' ensures that if the file hasn't actually changed since the last
  # update, the script doesn't exit with an error.
  git commit -m "$MSG" || echo "Nothing new to commit for $INPUT"

  git push origin "$(git rev-parse --abbrev-ref HEAD)" || echo "Push failed"
fi
echo "✅ Backup complete."
