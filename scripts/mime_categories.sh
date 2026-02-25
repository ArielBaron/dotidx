#!/usr/bin/env bash
set -euo pipefail

IFS=: read -ra dirs <<< "${XDG_DATA_HOME:-$HOME/.local/share}:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
MIME_DIRS=()
for d in "${dirs[@]}"; do
  [ -d "$d/mime" ] && MIME_DIRS+=("$d/mime")
done

echo "=== audio ==="
find "${MIME_DIRS[@]}" -name "*.xml" 2>/dev/null | xargs grep -hoP 'type="audio/\K[^"]+' | sed 's/^/audio\//' | sort -u
echo "=== video ==="
find "${MIME_DIRS[@]}" -name "*.xml" 2>/dev/null | xargs grep -hoP 'type="video/\K[^"]+' | sed 's/^/video\//' | sort -u
echo "=== image ==="
find "${MIME_DIRS[@]}" -name "*.xml" 2>/dev/null | xargs grep -hoP 'type="image/\K[^"]+' | sed 's/^/image\//' | sort -u
echo "=== text ==="
find "${MIME_DIRS[@]}" -name "*.xml" 2>/dev/null | xargs grep -hoP 'type="text/\K[^"]+' | sed 's/^/text\//' | sort -u

for icon in package-x-generic x-office-document x-office-spreadsheet x-office-presentation; do
  case "$icon" in
    package-x-generic) label="archive" ;;
    *) label="office" ;;
  esac
  echo "=== $label ==="
  find "${MIME_DIRS[@]}" -name "*.xml" 2>/dev/null \
    | xargs grep -l "generic-icon name=\"$icon\"" 2>/dev/null \
    | sed "s|.*/mime/||;s|\.xml||" | sort -u
done

echo "=== browser ==="
for d in "${dirs[@]}"; do
  cut -d= -f1 "$d/applications/mimeinfo.cache" 2>/dev/null | grep "^x-scheme-handler/"
done | sort -u
