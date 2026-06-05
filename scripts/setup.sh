#!/bin/bash
set -e
CONFIG_DIR="$HOME/.config/dotidx"
STATE_FILE="$CONFIG_DIR/state.conf"
BASE_BACKUP_DIR="$HOME/dotidxBackup"
read -p "Enter profile name (lowercase, no symbols): " PROFILE
if [[ ! "$PROFILE" =~ ^[a-z0-9]+$ ]]; then
  echo "FATAL: Invalid name '$PROFILE'. Use lowercase alphanumeric only."
  exit 1
fi
PROFILE_BACKUP_DIR="$BASE_BACKUP_DIR/$PROFILE"
mkdir -p "$CONFIG_DIR"
mkdir -p "$PROFILE_BACKUP_DIR"
TRACK_CONF="$CONFIG_DIR/${PROFILE}_track.conf"
if [ ! -s "$TRACK_CONF" ]; then
  echo "[]" >"$TRACK_CONF"
fi
echo "$PROFILE" >"$STATE_FILE"
echo "Profile '$PROFILE' active."
URL="$1"
if [ -z "$URL" ]; then
  read -p "Add a URL for this profile? (y/N) " answer
  case "$answer" in
  [Yy]*) read -p "Enter repo URL: " URL ;;
  *) URL="" ;;
  esac
fi
if [ -n "$URL" ]; then
  echo "Initializing repo in $PROFILE_BACKUP_DIR..."
  cd "$PROFILE_BACKUP_DIR"
  if [ ! -d ".git" ]; then
    git init
    git remote add origin "$URL"
    if git ls-remote --heads "$URL" 2>/dev/null | grep -q .; then
      echo "Remote has content, pulling first..."
      git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    fi
  fi
  git fetch origin
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    git checkout -B main origin/main
  elif git rev-parse --verify origin/master >/dev/null 2>&1; then
    git checkout -B master origin/master
  else
    echo "# $PROFILE backups" >README.md
    git add README.md
    git commit -m "initial" || true
  fi
  echo "Backup repo for '$PROFILE' synchronized with remote."
fi
CURRENT_CONTENT=$(cat "$TRACK_CONF")
if [ "$CURRENT_CONTENT" = "[]" ]; then
  mapfile -t CANDIDATES < <(
    find "$CONFIG_DIR" "$PROFILE_BACKUP_DIR" \
      -name "*_track.conf" \
      ! -name "${PROFILE}_track.conf" 2>/dev/null |
      sort -u
  )
  if [ ${#CANDIDATES[@]} -gt 0 ]; then
    echo "No tracking config for '$PROFILE'. Base off an existing one?"
    for i in "${!CANDIDATES[@]}"; do
      echo "  [$i] ${CANDIDATES[$i]}"
    done
    echo "  [s] Skip"
    read -p "Choice: " CHOICE
    if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -lt "${#CANDIDATES[@]}" ]; then
      cp "${CANDIDATES[$CHOICE]}" "$TRACK_CONF"
      echo "✅ Copied $(basename "${CANDIDATES[$CHOICE]}") as ${PROFILE}_track.conf"
    fi
  fi
fi

