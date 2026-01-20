#!/usr/bin/env bash
set -euo pipefail

# -------------------------
# Configuration
# -------------------------
BACKUP="$HOME/dotidxBackup"
TRACK_CONF="$HOME/.config/dotidx/track.conf"

rm -rf $BACKUP
rm -rf $TRACK_CONF

echo "deleted both config and backup"