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
TRACK_CONF="$HOME/.config/dotidx/${PROFILE}_track.conf"
INPUT_RAW="${1:-}"
INPUT=$(basename "$INPUT_RAW")
if [ ! -s "$TRACK_CONF" ]; then
    echo "No tracking configuration found."
    exit 0
fi
mapfile -t TRACKED < <(jq -r '.[]' "$TRACK_CONF")
declare -A EXPECTED_TOPS
EXPECTED_TOPS[".git"]=1
EXPECTED_TOPS["~"]=1
for src in "${TRACKED[@]}"; do
    if [[ "$src" == "~"* || "$src" == "$HOME"* ]]; then
        EXPECTED_TOPS["~"]=1
    else
        top=$(echo "$src" | cut -d'/' -f2)
        EXPECTED_TOPS["$top"]=1
    fi
done
for entry in "$BACKUP"/*/ "$BACKUP"/.[!.]*; do
    [ -e "$entry" ] || continue
    name=$(basename "$entry")
    if [[ -z "${EXPECTED_TOPS[$name]+_}" ]]; then
        echo "Removing stale: $entry"
        rm -rf "$entry"
    fi
done
updated_count=0
for src in "${TRACKED[@]}"; do
    [[ -n "$INPUT" && "$src" != *"$INPUT"* ]] && continue
    if [[ "$src" == "~"* ]]; then
        rel="${src#~/}"
        src="$HOME/$rel"
        dst="$BACKUP/~/$rel"
    elif [[ "$src" == "$HOME"* ]]; then
        rel="${src#$HOME/}"
        dst="$BACKUP/~/$rel"
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
if [ -d "$BACKUP/.git" ]; then
    cd "$BACKUP"
    git add -A
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    MSG="auto-update [$PROFILE] ${INPUT:-all} ($TIMESTAMP)"
    git commit -m "$MSG" || echo "Nothing new to commit."
    git push origin "$(git rev-parse --abbrev-ref HEAD)" || echo "Push failed (check network/remote)"
fi
echo "✅ Backup complete."