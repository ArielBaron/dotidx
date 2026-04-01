#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path
import sys
import os

REAL_FILE_PATH = Path(os.path.realpath(__file__))
REAL_DIR = REAL_FILE_PATH.parent
sys.path.append(str(REAL_DIR))

from ui import show_success, show_error, show_info, console
from dotfile_tui import interactive_select

HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "dotidx"
STATE_FILE = CONFIG_DIR / "state.conf"
BACKUP_DIR = HOME / "dotidxBackup"
DOT_CONFIG = HOME / ".config"
LOCAL_APPS = HOME / ".local" / "share" / "applications"
SCRIPTS_DIR = REAL_DIR / "scripts"


# -------------------------
# Data Helpers
# -------------------------


def get_current_profile():
    if not STATE_FILE.exists():
        show_error("No active profile. Run 'dotidx setup' or 'dotidx profile <name>'.")
        exit(1)
    return STATE_FILE.read_text().strip()


def get_track_file(profile=None):
    if profile is None:
        profile = get_current_profile()
    return CONFIG_DIR / f"{profile}_track.conf"


def load_track_data(profile=None):
    track_file = get_track_file(profile)
    if not track_file.exists() or track_file.stat().st_size == 0:
        return []
    try:
        with open(track_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_track_data(data, profile=None):
    track_file = get_track_file(profile)
    with open(track_file, "w") as f:
        json.dump(sorted(data), f, indent=2)


def get_tracked_for_profile(profile=None):
    data = load_track_data(profile)
    return set(Path(p).expanduser().resolve() for p in data)


# -------------------------
# Commands
# -------------------------


def run_setup(repo_url=None):
    cmd = ["bash", str(SCRIPTS_DIR / "setup.sh")]
    if repo_url:
        cmd.append(repo_url)
    subprocess.run(cmd, check=True)


def run_profile_switch(name):
    if not name:
        show_info(f"Current profile: {get_current_profile()}")
        return
    if not (BACKUP_DIR / name).exists():
        show_error(f"Profile '{name}' does not exist in {BACKUP_DIR}")
        return
    STATE_FILE.write_text(name)
    show_success(f"Switched to profile: {name}")


def run_rest():
    subprocess.run(["bash", str(SCRIPTS_DIR / "rest.sh")], check=True)


def run_sync():
    subprocess.run(["bash", str(SCRIPTS_DIR / "sync.sh")], check=True)


def run_update(target=None):
    cmd = ["bash", str(SCRIPTS_DIR / "update.sh")]
    if target:
        target_path = Path(target).expanduser().resolve()
        cmd.append(str(target_path))
    subprocess.run(cmd, check=True)


def run_pull():
    subprocess.run(["bash", str(SCRIPTS_DIR / "pull.sh")], check=True)


def run_wipe():
    subprocess.run(["bash", str(SCRIPTS_DIR / "wipe.sh")], check=True)


def run_config():
    profile = get_current_profile()
    tracked_paths = get_tracked_for_profile(profile)

    candidates = []
    for f in HOME.iterdir():
        if f.name.startswith(".") and f != DOT_CONFIG:
            candidates.append(f)
    if DOT_CONFIG.exists():
        for d in DOT_CONFIG.iterdir():
            if d.is_dir():
                candidates.append(d)
    if LOCAL_APPS.exists():
        candidates.append(LOCAL_APPS)

    candidates.sort()
    preselected = [c for c in candidates if c.resolve() in tracked_paths]

    show_info(f"Configuring profile: [bold]{profile}[/bold]")
    selected = interactive_select(candidates, preselected, HOME)

    new_selected = set(str(p.resolve()) for p in selected)
    save_track_data(list(new_selected), profile)
    show_success(f"Configuration complete for '{profile}'.")


def run_list():
    profile = get_current_profile()
    tracked = get_tracked_for_profile(profile)
    if not tracked:
        show_info(f"No dotfiles tracked for profile '{profile}'.")
        return

    console.print(f"\n[bold cyan]Tracked ({profile}):[/bold cyan]\n")
    for p in sorted(tracked):
        display = str(p).replace(str(HOME), "~")
        console.print(f"  [green]•[/green] {display}")


def run_track(name, is_path=False):
    profile = get_current_profile()

    if is_path:
        target = Path(name).expanduser().resolve()
        candidates = [target] if target.exists() else []
    else:
        checks = [HOME / name, HOME / f".{name}", DOT_CONFIG / name]
        candidates = [p.resolve() for p in checks if p.exists()]

    if not candidates:
        show_error(f"No match found for: {name}")
        return

    target_str = str(candidates[0])
    data = load_track_data(profile)

    if target_str in data:
        show_info(f"Already tracked in '{profile}': {target_str}")
        return

    data.append(target_str)
    save_track_data(data, profile)
    show_success(f"Added to '{profile}': {target_str}")


def run_untrack(name, is_path=False):
    profile = get_current_profile()
    data = load_track_data(profile)

    if is_path:
        target_key = str(Path(name).expanduser().resolve())
    else:
        target_key = next((p for p in data if name in p), None)

    if not target_key or target_key not in data:
        show_error(f"Not tracked in '{profile}': {name}")
        return

    data.remove(target_key)
    save_track_data(data, profile)
    show_success(f"Removed '{name}' from profile '{profile}'.")