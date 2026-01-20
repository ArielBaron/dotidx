#!/bin/sh
set -e

CONFIG_DIR="$HOME/.config/dotidx"
BACKUP_DIR="$HOME/dotidxBackup"

mkdir -p "$CONFIG_DIR"
mkdir -p "$BACKUP_DIR"
touch "$CONFIG_DIR/track.conf"

echo "Built $CONFIG_DIR and $BACKUP_DIR"

URL="$1"

if [ -z "$URL" ]; then
    read -r -p "Add a URL? (y/N) " answer
    case "$answer" in
        [Yy]*) read -r -p "Enter repo URL: " URL ;;
        *) URL="" ;;
    esac
fi

if [ -n "$URL" ]; then
    TMP_DIR=$(mktemp -d)

    echo "Cloning $URL..."
    git clone "$URL" "$TMP_DIR"

    # copy repo contents WITHOUT .git
    rsync -a --exclude='.git' "$TMP_DIR"/ "$BACKUP_DIR"/
    rm -rf "$TMP_DIR"

    cd "$BACKUP_DIR"

    if [ ! -d ".git" ]; then
        git init
        git remote add origin "$URL"
    fi

    git add -A
    git commit -m "initial import" || echo "Nothing to commit"
    git push -u origin master || git push -u origin main || true

    echo "Backup repo initialized."
fi