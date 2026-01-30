#!/usr/bin/env python3
import argparse
import subprocess
import json
import shutil
from pathlib import Path

from interactive import (
    interactive_select,
    show_success,
    show_error,
    show_info,
    show_warning,
)
from rich.console import Console

console = Console()

# -------------------------
# Path Constants
# -------------------------

HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "dotidx"
TRACK_FILE = CONFIG_DIR / "track.conf"
STATE_FILE = CONFIG_DIR / "state.conf"
BACKUP_DIR = HOME / "dotidxBackup"
DOT_CONFIG = HOME / ".config"
LOCAL_APPS = HOME / ".local" / "share" / "applications"

# -------------------------
# Helpers
# -------------------------

def get_current_profile():
    if not STATE_FILE.exists():
        show_error("No active profile. Run 'dotidx setup' or 'dotidx profile <name>'.")
        exit(1)
    return STATE_FILE.read_text().strip()

def load_track_data():
    if not TRACK_FILE.exists() or TRACK_FILE.stat().st_size == 0:
        return {}
    try:
        with open(TRACK_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_track_data(data):
    with open(TRACK_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_tracked_for_profile(profile):
    data = load_track_data()
    tracked_paths = []
    for path_str, profiles in data.items():
        if profile in profiles:
            tracked_paths.append(Path(path_str).expanduser().resolve())
    return set(tracked_paths)

# -------------------------
# Commands
# -------------------------

def run_setup(repo_url=None):
    script_dir = Path(__file__).parent.resolve()
    setup_script = script_dir / "scripts" / "setup.sh"
    cmd = [str(setup_script)]
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
    script_dir = Path(__file__).parent.resolve()
    update_script = script_dir / "scripts" / "rest.sh"
    subprocess.run([str(update_script)], check=True)


def run_update():
    script_dir = Path(__file__).parent.resolve()
    update_script = script_dir / "scripts" / "update.sh"
    subprocess.run([str(update_script)], check=True)

def run_config():
    profile = get_current_profile()
    data = load_track_data()
    profile_tracked = [str(p) for p in get_tracked_for_profile(profile)]
    
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
    preselected = [c for c in candidates if str(c) in profile_tracked]
    
    show_info(f"Configuring profile: [bold]{profile}[/bold]")
    selected = interactive_select(candidates, preselected, HOME)

    new_selected_strs = set(str(p.resolve()) for p in selected)
    
    # Update global data structure
    for c in candidates:
        c_str = str(c.resolve()).replace(str(HOME), "~")
        path_key = str(c.resolve())
        current_profiles = data.get(path_key, [])
        
        if path_key in new_selected_strs:
            if profile not in current_profiles:
                current_profiles.append(profile)
        else:
            if profile in current_profiles:
                current_profiles.remove(profile)
        
        if current_profiles:
            data[path_key] = sorted(current_profiles)
        elif path_key in data:
            del data[path_key]

    save_track_data(data)
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

def run_add(name):
    profile = get_current_profile()
    checks = [HOME / name, HOME / f".{name}", DOT_CONFIG / name]
    candidates = [p.resolve() for p in checks if p.exists()]

    if not candidates:
        show_error(f"No match found for: {name}")
        return
    
    target = candidates[0]
    target_str = str(target)
    data = load_track_data()
    
    profiles = data.get(target_str, [])
    if profile in profiles:
        show_info(f"Already tracked in '{profile}': {target_str}")
        return
        
    profiles.append(profile)
    data[target_str] = sorted(profiles)
    save_track_data(data)
    show_success(f"Added to '{profile}': {target_str}")

def run_remove(name):
    profile = get_current_profile()
    data = load_track_data()
    target_key = None

    for path_str in data:
        if name in path_str:
            target_key = path_str
            break

    if not target_key or profile not in data[target_key]:
        show_error(f"Not tracked in '{profile}': {name}")
        return

    data[target_key].remove(profile)
    if not data[target_key]:
        del data[target_key]
    
    save_track_data(data)
    show_success(f"Removed '{name}' from profile '{profile}'.")

def main():
    parser = argparse.ArgumentParser(description="dotidx – multi-profile dotfile tracking")
    parser.add_argument(
        "mode",
        choices=["rest","update", "sync", "config", "list", "setup", "add", "remove", "profile"],
    )
    parser.add_argument("additional", nargs="?")
    args = parser.parse_args()

    if args.mode == "update": run_update()
    elif args.mode == "rest": run_rest()
    elif args.mode == "config": run_config()
    elif args.mode == "list": run_list()
    elif args.mode == "setup": run_setup(args.additional)
    elif args.mode == "add": run_add(args.additional)
    elif args.mode == "remove": run_remove(args.additional)
    elif args.mode == "profile": run_profile_switch(args.additional)

if __name__ == "__main__":
    main()
