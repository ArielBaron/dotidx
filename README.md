# v3.3.6
![AUR version](https://img.shields.io/aur/version/dotidx?color=blue&style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
![Platform: Arch Linux](https://img.shields.io/badge/Platform-Arch_Linux-1793d1?logo=arch-linux&style=flat-square)

`dotidx` is a multi-profile dotfile manager for Arch Linux that prioritizes **ease of use, reproducibility, explicit state and effective isolated backups**.

Unlike symlink-based managers, it uses **real file copies** and **profile-isolated tracking**, making it robust across systems and environments.

---

## Why dotidx?

Most dotfile managers either rely on symlinks or require you to restructure your entire home directory. dotidx does neither.

Your backup is just a folder of real files — easy to read, edit, share, and understand without any tooling. No symlink confusion, no hidden indirection. Combined with multi-profile isolation and Git backing, it covers the full workflow: track, backup, restore, and switch — without getting in your way.

It is not meant to replace Git. It is meant to make Git-backed dotfile management simple enough that you actually do it.

---

## Key Features

- Multi-profile support (`work`, `server`, `personal`, etc.)
- No symlinks — real file copies only
- Git-backed backups
- Interactive TUI for file selection
- MIME / browser handler configuration and TUI
- Strict, deterministic sync and update behavior

---

## How It Actually Works

### Config Layout

- Active profile: `~/.config/dotidx/state.conf`
- Per-profile tracking: `~/.config/dotidx/<profile>_track.conf`
- Backups: `~/dotidxBackup/<profile>/`

Each profile is fully isolated.

---

### Commands

#### `update`
```
dotidx update
```
- Copies tracked files into backup dir with full path
- Forces backup state to only contain tracked files
- Runs `git commit` then `git push`, with a commit message of the current time

---

#### `sync`
```
dotidx sync
```
- Overwrites local files with their backup version

---

#### `pull`
```
dotidx pull
```
- Updates backup from remote Git
- Does NOT apply changes to actual local files

---

#### `setup [url]`
Create a new profile and optionally connect it to a Git repo.

#### `profile [name]`
Show or switch active profile.

---

### Tracking

#### `config`
Interactive TUI for selecting dotfiles.

Scans:
- `~/.*`
- `~/.config/*`
- Desktop entries

#### `track <path>`
Add file or directory to tracking.

#### `untrack <path>`
Remove from tracking.

#### `list [type]`
- `current` — list tracked files for active profile
- `profiles` — list tracked files for all profiles

---

#### `rest`
⚠️ Full reset:
- Deletes backup
- Clears state
- Removes tracking

#### `wipe`
Clears backup contents only.

#### `revert [n]`
Rollback backup state to nth generation ago (defaults to `n=1`).

---

## Installation

### AUR (recommended)
```bash
yay -S dotidx
```

### Manual
```bash
git clone https://github.com/ArielBaron/dotidx.git
cd dotidx
mkdir -p ~/.config/dotidx
ln -s "$(pwd)/main.py" ~/.local/bin/dotidx
```

---

## Dependencies

- python
- rsync
- git
- python-rich
- python-textual
- jq

---

## Scripts

Located in `scripts/`:
- `setup.sh`
- `update.sh`
- `sync.sh`
- `pull.sh`
- `rest.sh`
- `wipe.sh`
- `revert.sh`
- MIME helpers

These scripts implement the actual filesystem and Git logic.

---

## Project Structure

```
dotidx/
├── main.py
├── dotfile.py
├── interactive.py
├── ui.py
├── dotfile_tui.py
├── mime.py
├── mime_tui.py
├── scripts/
└── README.md
```

---

## Design Principles

- Profiles are isolated
- Backups are authoritative
- No hidden behavior — no symlinks
- Failures are explicit

---

## Examples

### Basic setup
```bash
dotidx setup https://github.com/you/dotfiles.git
dotidx profile personal
dotidx config
```

### Track a file manually
```bash
dotidx track ~/.bashrc
dotidx track ~/.config/nvim
```

### Push your current system state
```bash
dotidx update
```
Copies tracked files into backup, removes untracked files from backup, then commits and pushes if Git is configured.

### Restore on a new machine
```bash
dotidx pull
dotidx sync
```

### Switching profiles
```bash
dotidx profile work
dotidx update
```
Each profile has its own tracked files, backup, and Git history.

### Safe workflow
```bash
dotidx update      # save current state
# make changes
dotidx update      # commit changes
dotidx sync        # test restore
```

---

## License

MIT — see LICENSE.

© 2026 Ariel Baron.