#!/usr/bin/env python3
import json
import os
import subprocess
from pathlib import Path

HOME = Path.home()
SCRIPTS_DIR = Path(os.path.realpath(__file__)).parent / "scripts"


# -------------------------
# Discovery
# -------------------------

def get_mime_categories():
    result = subprocess.run([str(SCRIPTS_DIR / "mime_categories.sh")], capture_output=True, text=True)

    categories = {}
    current = None
    for line in result.stdout.strip().splitlines():
        if line.startswith("==="):
            current = line.strip("= ").strip()
            if current not in categories:
                categories[current] = []
        elif current and line.strip():
            categories[current].append(line.strip())

    for cat in categories:
        seen = set()
        cleaned = []
        for entry in categories[cat]:
            if entry.startswith("packages/"):
                continue
            if entry not in seen:
                seen.add(entry)
                cleaned.append(entry)
        categories[cat] = cleaned

    return categories


def get_browser_handlers():
    """Return contested scheme handlers (2+ distinct apps) mapped to their registered .desktop files."""
    result = subprocess.run([str(SCRIPTS_DIR / "mime_browser_handlers.sh")], capture_output=True, text=True)
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return {}


def get_installed_apps():
    # --- .desktop apps ---
    app_dirs = [
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
        HOME / ".local/share/applications",
    ]
    name_to_file = {}
    for d in app_dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.desktop")):
            try:
                content = f.read_text(errors="ignore")
                name = None
                hidden = False
                in_entry = False
                for line in content.splitlines():
                    if line.strip() == "[Desktop Entry]":
                        in_entry = True
                        continue
                    if line.startswith("[") and in_entry:
                        break
                    if not in_entry:
                        continue
                    if line.startswith("Name=") and name is None:
                        name = line[5:].strip()
                    if line.strip() in ("NoDisplay=true", "Hidden=true"):
                        hidden = True
                if name and not hidden:
                    name_to_file[name] = f.name
            except Exception:
                pass

    desktop_apps = sorted(name_to_file.items())
    filename_to_name = {v: k for k, v in name_to_file.items()}

    # --- terminal commands from PATH ---
    seen_bins = set()
    terminal_apps = []
    for path_dir in os.environ.get("PATH", "").split(":"):
        d = Path(path_dir)
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            try:
                if f.name not in seen_bins and f.is_file() and os.access(f, os.X_OK):
                    seen_bins.add(f.name)
                    terminal_apps.append(f.name)
            except Exception:
                pass
    terminal_apps = sorted(terminal_apps)

    return desktop_apps, terminal_apps, filename_to_name


# -------------------------
# Defaults
# -------------------------

def _valid_app(val):
    return val and not val.startswith("{") and not val.startswith("[")


def get_current_defaults(categories, filename_to_name):
    mime_to_app = _read_mimeapps_defaults()
    defaults = {}
    for cat, mimes in categories.items():
        for mime in mimes:
            if mime in mime_to_app and _valid_app(mime_to_app[mime]):
                defaults[cat] = mime_to_app[mime]
                break
        if cat not in defaults and mimes:
            try:
                result = subprocess.run(
                    ["xdg-mime", "query", "default", mimes[0]],
                    capture_output=True, text=True, timeout=2
                )
                app = result.stdout.strip()
                if app:
                    defaults[cat] = app
            except Exception:
                pass
    return defaults


def get_browser_defaults(handlers):
    mime_to_app = _read_mimeapps_defaults()
    defaults = {}
    for handler in handlers:
        mime = f"x-scheme-handler/{handler}"
        if mime in mime_to_app and _valid_app(mime_to_app[mime]):
            defaults[handler] = mime_to_app[mime]
        else:
            try:
                result = subprocess.run(
                    ["xdg-mime", "query", "default", mime],
                    capture_output=True, text=True, timeout=2
                )
                app = result.stdout.strip()
                if app:
                    defaults[handler] = app
            except Exception:
                pass
    return defaults


# -------------------------
# Writes
# -------------------------

def _read_mimeapps_defaults():
    """Read [Default Applications] section from mimeapps.list."""
    mimeapps = HOME / ".config" / "mimeapps.list"
    mime_to_app = {}
    if mimeapps.exists():
        in_defaults = False
        for line in mimeapps.read_text().splitlines():
            if line.strip() == "[Default Applications]":
                in_defaults = True
                continue
            if line.startswith("["):
                in_defaults = False
            if in_defaults and "=" in line:
                mime, app = line.split("=", 1)
                mime_to_app[mime.strip()] = app.strip().split(";")[0]
    return mime_to_app


def _read_mimeapps_full():
    """Read full mimeapps.list, returning (existing_defaults dict, other_sections list)."""
    mimeapps = HOME / ".config" / "mimeapps.list"
    existing = {}
    other_sections = []
    if mimeapps.exists():
        in_defaults = False
        for line in mimeapps.read_text().splitlines():
            if line.strip() == "[Default Applications]":
                in_defaults = True
                continue
            if line.startswith("["):
                in_defaults = False
                other_sections.append(line)
                continue
            if in_defaults and "=" in line:
                mime, app = line.split("=", 1)
                existing[mime.strip()] = app.strip()
            elif not in_defaults and other_sections:
                other_sections.append(line)
    return existing, other_sections


def _write_mimeapps(existing, other_sections):
    mimeapps = HOME / ".config" / "mimeapps.list"
    lines = ["[Default Applications]\n"]
    for mime, app in sorted(existing.items()):
        lines.append(f"{mime}={app}\n")
    for s in other_sections:
        lines.append(s + "\n")
    mimeapps.write_text("".join(lines))


def write_mimeapps(selections, categories):
    existing, other_sections = _read_mimeapps_full()
    for cat, app_file in selections.items():
        if not app_file:
            continue
        for mime in categories.get(cat, []):
            existing[mime] = app_file
    _write_mimeapps(existing, other_sections)


def write_browser_mimeapps(selections):
    existing, other_sections = _read_mimeapps_full()
    for handler, app_file in selections.items():
        if app_file:
            existing[f"x-scheme-handler/{handler}"] = app_file
    _write_mimeapps(existing, other_sections)
