#!/usr/bin/env bash

# Collect .desktop files from standard locations, ignoring missing dirs
desktop_files=()
for dir in \
  /usr/share/applications \
  /usr/local/share/applications \
  "${XDG_DATA_HOME:-$HOME/.local/share}/applications"; do
  if [ -d "$dir" ]; then
    while IFS= read -r -d '' f; do
      desktop_files+=("$f")
    done < <(find "$dir" -maxdepth 1 -name '*.desktop' -print0 2>/dev/null)
  fi
done

if [ ${#desktop_files[@]} -eq 0 ]; then
  echo "{}"
  exit 0
fi

awk '
  /^\[Desktop Entry\]/ { in_entry=1; name=""; mimes=""; next }
  /^\[/ && !/^\[Desktop Entry\]/ { in_entry=0 }
  in_entry && /^Name=/ && name=="" { name=substr($0,6) }
  in_entry && /^MimeType=/ { mimes=substr($0,10) }
  in_entry && /^(NoDisplay|Hidden)=true/ { name="" }
  ENDFILE {
    if (name!="" && mimes!="") {
      n=split(mimes,arr,";")
      for (i=1;i<=n;i++) {
        m=arr[i]; gsub(/^[ \t]+|[ \t]+$/,"",m)
        if (m~/^x-scheme-handler\//) {
          h=substr(m,18)
          handlers[h][name]=FILENAME
        }
      }
    }
    name=""; mimes=""
  }
  END {
    printf "{"
    fh=1
    for (h in handlers) {
      if (!fh) printf ","
      fh=0
      printf "\"%s\":{",h
      fa=1
      for (a in handlers[h]) {
        if (!fa) printf ","
        fa=0
        f=handlers[h][a]; gsub(/.*\//,"",f)
        printf "\"%s\":\"%s\"",a,f
      }
      printf "}"
    }
    printf "}\n"
  }
' "${desktop_files[@]}"
