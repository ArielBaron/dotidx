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
    echo "{}" > "$CONFIG_DIR/track.conf"
fi

# 2. Save Session State
echo "$PROFILE" > "$STATE_FILE"
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
    fi

    # Fetch and reset to remote state instead of rsyncing a temp dir
    git fetch origin
    # Try to switch to main or master from remote
    if git rev-parse --verify origin/main >/dev/null 2>&1; then
        git checkout -b main origin/main || git checkout main
    elif git rev-parse --verify origin/master >/dev/null 2>&1; then
        git checkout -b master origin/master || git checkout master
    fi

    echo "Backup repo for '$PROFILE' synchronized with remote."
fi
