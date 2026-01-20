
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
BACKUP_DIR = HOME / "dotidxBackup"
DOT_CONFIG = HOME / ".config"
LOCAL_APPS = HOME / ".local" / "share" / "applications"

# -------------------------
# Helpers
# -------------------------

def expand_list(path_list):
    return set(Path(p).expanduser().resolve() for p in path_list)


def load_json_list(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_json_list(path: Path, items, home: Path):
    with open(path, "w") as f:
        json.dump(
            [str(p).replace(str(home), "~") for p in sorted(items)],
            f,
            indent=2,
        )

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


def run_update():
    script_dir = Path(__file__).parent.resolve()
    update_script = script_dir / "scripts" / "update.sh"
    subprocess.run([str(update_script)], check=True)
    show_success("Backup sync complete.")


def clear_config():
    script_dir = Path(__file__).parent.resolve()
    clear_script = script_dir / "scripts" / "clear.sh"
    subprocess.run([str(clear_script)], check=True)
    show_success("config cleared.")


def run_config():
    yes_list = set(str(p) for p in expand_list(load_json_list(TRACK_FILE)))
    candidates = []

    # top-level dotfiles in ~ (except .config)
    for f in HOME.iterdir():
        if f.name.startswith(".") and f != DOT_CONFIG:
            if str(f) not in yes_list:
                candidates.append(f)

    # subdirectories of ~/.config
    if DOT_CONFIG.exists():
        for d in DOT_CONFIG.iterdir():
            if d.is_dir() and str(d) not in yes_list:
                candidates.append(d)

    # ~/.local/share/applications as ONE directory
    if LOCAL_APPS.exists() and str(LOCAL_APPS) not in yes_list:
        candidates.append(LOCAL_APPS)

    if not candidates:
        show_info("No new dotfiles to configure.")
        return

    candidates.sort()

    preselected = [c for c in candidates if str(c) in yes_list]

    show_info(f"Found {len(candidates)} dotfiles to configure...")
    selected = interactive_select(candidates, preselected, HOME)

    yes_list = set(str(p) for p in selected)
    save_json_list(TRACK_FILE, yes_list, HOME)

    show_success(f"Configuration complete. Tracking {len(yes_list)} items.")


def run_list():
    tracked = expand_list(load_json_list(TRACK_FILE))
    if not tracked:
        show_info("No dotfiles are currently tracked.")
        return

    home_items = []
    config_items = []

    for path in tracked:
        try:
            rel = path.relative_to(HOME)
        except ValueError:
            continue

        display = Path("~") / rel
        if rel.parts[0] == ".config":
            config_items.append(display)
        else:
            home_items.append(display)

    console.print("\n[bold cyan]Tracked Dotfiles:[/bold cyan]\n")
    for p in sorted(home_items):
        console.print(f"  [green]•[/green] {p}")
    for p in sorted(config_items):
        console.print(f"  [green]•[/green] {p}")
    console.print()


def run_add(name):
    tracked = expand_list(load_json_list(TRACK_FILE))
    candidates = set()

    checks = [
        HOME / name,
        HOME / f".{name}",
        DOT_CONFIG / name,
    ]

    for p in checks:
        if p.exists():
            candidates.add(p.resolve())

    for p in HOME.glob(f".{name}.*"):
        candidates.add(p.resolve())

    if not candidates:
        show_error(f"No match found for: {name}")
        return

    if len(candidates) > 1:
        show_warning("Multiple matches:")
        for c in sorted(candidates):
            console.print(f"  [yellow]•[/yellow] {c}")
        return

    target = candidates.pop()
    if target in tracked:
        show_info(f"Already tracked: {target}")
        return

    tracked.add(target)
    save_json_list(TRACK_FILE, tracked, HOME)
    show_success(f"Added: {target}")


def run_remove(name):
    tracked = expand_list(load_json_list(TRACK_FILE))
    matches = set()

    for t in tracked:
        try:
            rel = t.relative_to(HOME)
        except ValueError:
            continue

        if (
            rel.parts[0] == name
            or rel.parts[0] == f".{name}"
            or rel.parts[0].startswith(f".{name}.")
            or rel.parts[:2] == (".config", name)
        ):
            matches.add(t)

    if not matches:
        show_error(f"No tracked entry for: {name}")
        return

    if len(matches) > 1:
        show_warning("Multiple matches:")
        for m in sorted(matches):
            console.print(f"  [yellow]•[/yellow] {m}")
        return

    tracked.remove(matches.pop())
    save_json_list(TRACK_FILE, tracked, HOME)
    show_success("Removed.")


def run_rest():
    show_warning("This will delete ALL backups and reset configuration.")
    ans = input("Type 'yes' to continue: ").strip().lower()
    if ans != "yes":
        show_info("Cancelled.")
        return

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    TRACK_FILE.write_text("[]\n")
    show_success("Reset complete.")

# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(description="dotidx – explicit dotfile tracking")
    parser.add_argument(
        "mode",
        choices=["update", "config", "list", "setup", "add", "remove", "rest"],
    )
    parser.add_argument("addtional", nargs="?")
    args = parser.parse_args()

    if args.mode == "update":
        run_update()

    elif args.mode == "config":
        if args.addtional == "rest":
            clear_config()
        elif args.addtional:
            show_error(f"{args.addtional} is not a valid option for config")
        else:
            run_config()

    elif args.mode == "list":
        run_list()

    elif args.mode == "setup":
        run_setup(args.addtional)

    elif args.mode == "add":
        if not args.addtional:
            show_error("Name of program missing.")
        else:
            run_add(args.addtional)

    elif args.mode == "remove":
        if not args.addtional:
            show_error("Name of program missing.")
        else:
            run_remove(args.addtional)

    elif args.mode == "rest":
        run_rest()


if __name__ == "__main__":
    main()