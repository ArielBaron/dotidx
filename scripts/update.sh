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

# Get just the filename
INPUT_RAW="${1:-}"
INPUT=$(basename "$INPUT_RAW")

# -------------------------
# Path Discovery Logic
# -------------------------
TARGET_SRC=""

if [ -n "$INPUT" ]; then
  CANDIDATES=(
    "$BACKUP/$INPUT"
    "$BACKUP/$INPUT.conf"
    "$BACKUP/.config/$INPUT"
    "$BACKUP/.config/$INPUT.conf"
  )

  for cand in "${CANDIDATES[@]}"; do
    if [ -e "$cand" ]; then
      rel_to_backup="${cand#$BACKUP}"
      TARGET_SRC="$HOME$rel_to_backup"

      if [[ "$TARGET_SRC" == *.conf ]] && [ ! -e "$TARGET_SRC" ]; then
        TARGET_SRC="${TARGET_SRC%.conf}"
      fi

      if [ -e "$TARGET_SRC" ]; then
        echo "Matched '$INPUT' to system path: $TARGET_SRC"
        break
      else
        TARGET_SRC=""
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
updated_count=0
for src in "${TRACKED[@]}"; do
  [ ! -e "$src" ] && continue

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
  updated_count=$((updated_count + 1))
done

if [ "$updated_count" -eq 0 ]; then
  echo "Nothing to update."
  exit 0
fi

# -------------------------
# CLEANUP PHASE (Full update only)
# -------------------------
if [ -z "$INPUT" ]; then
  echo "Running cleanup..."
  # Use -print0 to handle spaces/weird names safely
  find "$BACKUP" -mindepth 1 -not -path "$BACKUP/.git*" -print0 | while IFS= read -r -d '' path; do
    keep=false
    for t in "${TRACKED[@]}"; do
      tracked_dst="$BACKUP${t#$HOME}"
      if [[ "$tracked_dst" == "$path"* ]] || [[ "$path" == "$tracked_dst"* ]]; then
        keep=true
        break
      fi
    done
    if [ "$keep" = false ]; then
      rm -rf "$path"
    fi
  done
fi

# -------------------------
# GIT PHASE
# -------------------------
if [ -d "$BACKUP/.git" ]; then
  cd "$BACKUP"
  git add -A

  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  MSG="auto-update [$PROFILE] ${INPUT:-all} ($TIMESTAMP)"

  # '|| true' on commit is vital if no changes exist
  git commit -m "$MSG" || echo "Nothing new to commit."

  # '|| true' on push prevents script crash on network failure
  git push origin "$(git rev-parse --abbrev-ref HEAD)" || echo "Push failed (check network/remote)"
fi

echo "✅ Backup complete."
