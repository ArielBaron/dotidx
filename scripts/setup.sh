#!/bin/bash
set -e

CONFIG_DIR="$HOME/.config/dotidx"
STATE_FILE="$CONFIG_DIR/state.conf"
BASE_BACKUP_DIR="$HOME/dotidxBackup"

# 1. Force Profile Name
read -p "Enter profile name (lowercase, no symbols): " PROFILE
if [[ ! "$PROFILE" =~ ^[a-z0-9]+$ ]]; then
  echo "FATAL: Invalid name '$PROFILE'. Use lowercase alphanumeric only."
  exit 1
fi

PROFILE_BACKUP_DIR="$BASE_BACKUP_DIR/$PROFILE"

mkdir -p "$CONFIG_DIR"
mkdir -p "$PROFILE_BACKUP_DIR"
# Initialize as JSON object if empty
if [ ! -s "$CONFIG_DIR/track.conf" ]; then
  echo "{}" >"$CONFIG_DIR/track.conf"
fi

# 2. Save Session State
echo "$PROFILE" >"$STATE_FILE"
echo "Profile '$PROFILE' active."

# 3. Handle Git Remote
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

    # Try to pull existing content if remote is non-empty
    if git ls-remote --heads "$URL" 2>/dev/null | grep -q .; then
      echo "Remote has content, pulling first..."
      git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
    fi
  fi

  # Fetch and try to checkout/reset to remote
  git fetch origin

  # Try to handle whatever branch exists
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    git checkout -B main origin/main
  elif git rev-parse --verify origin/master >/dev/null 2>&1; then
    git checkout -B master origin/master
  else
    # No remote branches, create initial commit
    echo "# $PROFILE backups" >README.md
    git add README.md
    git commit -m "initial" || true
  fi

  echo "Backup repo for '$PROFILE' synchronized with remote."
fi
