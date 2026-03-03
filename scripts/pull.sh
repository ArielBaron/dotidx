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

if [ ! -d "$BACKUP" ]; then
  echo "Backup directory not found: $BACKUP"
  exit 1
fi

echo "Pulling latest changes for profile: $PROFILE..."
cd "$BACKUP"

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Fetch all updates from remote
echo "Fetching latest from remote..."
git fetch origin

# Check if the remote branch exists
if git show-ref --verify --quiet "refs/remotes/origin/$CURRENT_BRANCH"; then
  # Remote branch exists, set upstream if not set
  if ! git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
    echo "Setting upstream branch to origin/$CURRENT_BRANCH"
    git branch --set-upstream-to="origin/$CURRENT_BRANCH" "$CURRENT_BRANCH"
  fi

  # Pull the latest changes
  echo "Pulling updates..."
  git pull --ff-only

else
  echo "Warning: Remote branch origin/$CURRENT_BRANCH doesn't exist"
  echo "Available remote branches:"
  git branch -r

  # If main/master exists, offer to switch
  if git show-ref --verify --quiet "refs/remotes/origin/main"; then
    echo "Switching to main branch..."
    git checkout main
    git branch --set-upstream-to=origin/main main
    git pull --ff-only
  elif git show-ref --verify --quiet "refs/remotes/origin/master"; then
    echo "Switching to master branch..."
    git checkout master
    git branch --set-upstream-to=origin/master master
    git pull --ff-only
  else
    echo "Error: No suitable remote branch found"
    exit 1
  fi
fi

echo "✅ Successfully updated $PROFILE"
