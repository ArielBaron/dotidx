#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import os

REAL_FILE_PATH = Path(os.path.realpath(__file__))
REAL_DIR = REAL_FILE_PATH.parent
VERSION = "3.4.0"
sys.path.append(str(REAL_DIR))

from dotfile import (
    run_pull,
    run_setup,
    run_profile_switch,
    run_rest,
    run_sync,
    run_update,
    run_config,
    run_list,
    run_track,
    run_untrack,
    run_wipe,
)


def main():
    parser = argparse.ArgumentParser(
        description="dotidx – multi-profile dotfile tracking"
    )
    parser.add_argument(
        "mode",
        choices=[
            "pull",
            "rest",
            "update",
            "sync",
            "config",
            "list",
            "setup",
            "track",
            "untrack",
            "profile",
            "wipe",
        ],
    )
    parser.add_argument("additional", nargs="?")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"dotidx v{VERSION}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "-p",
        "--path",
        action="store_true",
        help="Treat input as a direct filesystem path",
    )
    args = parser.parse_args()

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
        run_list(args.additional)
    elif args.mode == "setup":
        run_setup(args.additional)
    elif args.mode == "track":
        run_track(args.additional, args.path)
    elif args.mode == "untrack":
        run_untrack(args.additional, args.path)
    elif args.mode == "profile":
        run_profile_switch(args.additional)
    elif args.mode == "wipe":
        run_wipe()


if __name__ == "__main__":
    main()