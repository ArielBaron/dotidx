#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="$HOME/.config/dotidx/state.conf"
TRACK_CONF="$HOME/.config/dotidx/track.conf"
BASE_BACKUP="$HOME/dotidxBackup"

if [ ! -f "$STATE_FILE" ]; then
    echo "Error: No active profile found."
    exit 1
fi

PROFILE=$(cat "$STATE_FILE")
BACKUP="$BASE_BACKUP/$PROFILE"

# Optional argument: only update a specific file/dir
INPUT_RAW="${1:-}"
INPUT=$(basename "$INPUT_RAW")

if [ ! -s "$TRACK_CONF" ]; then
    echo "No tracking configuration found."
    exit 0
fi

mapfile -t TRACKED < <(
    jq -r --arg prof "$PROFILE" '
        to_entries[] | select(.value | index($prof)) | .key
    ' "$TRACK_CONF"
)

updated_count=0
for src in "${TRACKED[@]}"; do
    # Skip if specific input is given
    [[ -n "$INPUT" && "$src" != *"$INPUT"* ]] && continue

    # Expand home paths
    if [[ "$src" == "~"* ]]; then
        src="$HOME/${src#~/}"
        dst="$BACKUP/${src#$HOME/}"
    else
        dst="$BACKUP$src"
    fi

    if [ ! -e "$src" ]; then
        continue
    fi

    echo "Updating: $src"
    mkdir -p "$(dirname "$dst")"
    if [ -d "$src" ]; then
        rsync -a --copy-links --safe-links --delete --exclude ".git" "$src/" "$dst/"
    else
        cp -RL "$src" "$dst"
    fi
    updated_count=$((updated_count + 1))
done

[[ "$updated_count" -eq 0 ]] && echo "Nothing to update."

# Git commit & push
if [ -d "$BACKUP/.git" ]; then
    cd "$BACKUP"
    git add -A
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    MSG="auto-update [$PROFILE] ${INPUT:-all} ($TIMESTAMP)"
    git commit -m "$MSG" || echo "Nothing new to commit."
    git push origin "$(git rev-parse --abbrev-ref HEAD)" || echo "Push failed (check network/remote)"
fi

echo "✅ Backup complete."
