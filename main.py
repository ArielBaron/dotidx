#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os

REAL_FILE_PATH = Path(os.path.realpath(__file__))
REAL_DIR = REAL_FILE_PATH.parent
sys.path.append(str(REAL_DIR))

from ui import show_success, show_error, show_info
from dotfile import (
    run_pull,
    run_setup,
    run_profile_switch,
    run_rest,
    run_sync,
    run_update,
    run_config,
    run_list,
    run_add,
    run_remove,
)
from mime import get_mime_categories, write_mimeapps, write_browser_mimeapps
from mime_tui import mime_config_tui, browser_config_tui


def run_mime(subcommand, key=None, value=None, extras=None):
    if subcommand not in ("config", "set"):
        show_error(f"Unknown subcommand '{subcommand}'. Use 'config' or 'set'.")
        return

    if subcommand == "config":
        if key is not None or value is not None or extras:
            show_error("'mime config' takes no arguments.")
            return
        categories = get_mime_categories()
        result = mime_config_tui(categories)
        if result is None:
            show_info("Cancelled.")
        else:
            selections, browser_selections = result
            write_mimeapps(selections, categories)
            if browser_selections:
                write_browser_mimeapps(browser_selections)
            show_success("mimeapps.list updated successfully.")

    elif subcommand == "set":
        if key is None or value is None or extras:
            show_error("'mime set' requires exactly two arguments: <type> <tool>")
            return
        print(f"subcommand: set")
        print(f"key: {key}")
        print(f"value: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="dotidx – multi-profile dotfile tracking"
    )
    parser.add_argument(
        "mode",
        choices=[
            "pull",
            "rest",
            "mime",
            "update",
            "sync",
            "config",
            "list",
            "setup",
            "add",
            "remove",
            "profile",
        ],
    )
    parser.add_argument("additional", nargs="?")
    parser.add_argument("key", nargs="?")
    parser.add_argument("value", nargs="?")
    parser.add_argument(
        "-p",
        "--path",
        action="store_true",
        help="Treat input as a direct filesystem path",
    )
    args, extras = parser.parse_known_args()

    if args.mode == "update":
        run_update(args.additional)
    elif args.mode == "sync":
        run_sync()
    elif args.mode == "rest":
        run_rest()
    elif args.mode == "pull":
        run_pull()
    elif args.mode == "config":
        run_config()
    elif args.mode == "list":
        run_list()
    elif args.mode == "setup":
        run_setup(args.additional)
    elif args.mode == "add":
        run_add(args.additional, args.path)
    elif args.mode == "remove":
        run_remove(args.additional, args.path)
    elif args.mode == "profile":
        run_profile_switch(args.additional)
    elif args.mode == "mime":
        run_mime(args.additional, args.key, args.value, extras)


if __name__ == "__main__":
    main()
