#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Configuration
# -------------------------
BACKUP="$HOME/dotidxBackup"
TRACK_CONF="$HOME/.config/dotidx/track.conf"

mkdir -p "$BACKUP"

# -------------------------
# Load tracked paths
# -------------------------
if [ ! -s "$TRACK_CONF" ]; then
  echo "No tracked files. Nothing to back up."
  exit 0
fi

mapfile -t TRACKED < <(jq -r '.[]' "$TRACK_CONF" | sed "s|^~|$HOME|")

echo "Backing up ${#TRACKED[@]} paths..."

# -------------------------
# COPY PHASE
# - NO symlinks
# - Always copy real content
# -------------------------
for src in "${TRACKED[@]}"; do
  if [ ! -e "$src" ]; then
    echo "Skipping missing: $src"
    continue
  fi

  dst="$BACKUP${src#$HOME}"
  mkdir -p "$(dirname "$dst")"

  if [ -d "$src" ]; then
    # remove nested git repos inside tracked paths
    find "$src" -type d -name ".git" -prune -exec rm -rf {} +

    rsync \
      -a \
      --copy-links \
      --safe-links \
      --delete \
      "$src/" "$dst/"
  else
    cp -RL "$src" "$dst"
  fi
done

# -------------------------
# CLEANUP PHASE
# - remove untracked files
# - NEVER touch outer .git or .config
# -------------------------
while IFS= read -r path; do
  keep=false

  for t in "${TRACKED[@]}"; do
    tracked_dst="$BACKUP${t#$HOME}"
    [[ "$path" == "$tracked_dst"* ]] && keep=true && break
  done

  if ! $keep; then
    rm -rf "$path"
    echo "Removed: $path"
  fi
done < <(
  find "$BACKUP" \
    -depth -mindepth 1 \
    -path "$BACKUP/.git" -prune -o \
    -path "$BACKUP/.git/*" -prune -o \
    -path "$BACKUP/.config" -prune -o \
    -path "$BACKUP/.config/*" -prune -o \
    -print
)

# -------------------------
# GIT PHASE
# -------------------------
cd "$BACKUP"

if [ -d ".git" ]; then
  git add -A
  git commit -m "auto-update ($(date '+%Y-%m-%d %H:%M:%S'))" || echo "Nothing to commit"
  git push || echo "Push failed or no remote configured"
else
  echo "No Git repository found. Use: dotidx setup [url]"
fi

# -------------------------
# FINAL VERIFY
# -------------------------
if find "$BACKUP" -type l | grep -q .; then
  echo "WARNING: symlinks detected in backup (this should not happen)"
else
  echo "Verified: no symlinks in backup"
fi

echo "Backup complete."
echo "Note: nested .git directories inside tracked paths were removed."