# dotidx v2.0.9

![AUR version](https://img.shields.io/aur/version/dotidx?color=blue&style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
![Platform: Arch Linux](https://img.shields.io/badge/Platform-Arch_Linux-1793d1?logo=arch-linux&style=flat-square)

`dotidx` is a multi-profile dotfile manager for Arch Linux. It physically copies tracked files to a local backup directory and optionally pushes them to a remote git repository, prioritizing stability over symlink-based approaches.

---

## How It Works

Tracked files are stored in `~/.config/dotidx/track.conf` (a JSON map of paths to the profiles that own them). The active profile is stored in `~/.config/dotidx/state.conf`. Backups live under `~/dotidxBackup/<profile>/`.

**Push flow (`update`):** Copies tracked files from `$HOME` → `~/dotidxBackup/<profile>/`, then runs `git add -A && git commit && git push`.

**Pull flow (`sync`):** Copies files from `~/dotidxBackup/<profile>/` back to `$HOME`, overwriting local versions.

---

## Installation

### Arch User Repository (Recommended)
```bash
yay -S dotidx
```

### Manual
```bash
git clone https://github.com/ArielBaron/dotidx.git
cd dotidx
mkdir -p ~/.config/dotidx/profiles
ln -s $(pwd)/main.py ~/.local/bin/dotidx
```

**Dependencies:** `python`, `rsync`, `git`, `python-rich`, `python-textual`, `jq`

---

## Commands

### `setup [url]`
Initializes a new profile. Prompts for a profile name and optionally a remote git repository URL. If a URL is provided, the backup directory is initialized as a git repo and synced with the remote.

```bash
dotidx setup
dotidx setup https://github.com/user/dotfiles.git
```

### `config`
Opens an interactive TUI to select which dotfiles to track under the active profile. Scans `~/.*`, `~/.config/*/`, and `~/.local/share/applications/`. Pre-selects already-tracked paths.

```bash
dotidx config
```

### `mime`
Opens an interactive TUI to configure default applications for MIME types and URI schemes.

```bash
dotidx mime
```

### `add <name>`
Adds a single file or directory to the active profile's tracking list. By default, searches common locations (`~/name`, `~/.name`, `~/.config/name`). Use `-p` to pass a direct path.

```bash
dotidx add zsh
dotidx add -p ~/.zshrc
```

### `remove <name>`
Removes a path from the active profile's tracking list. Does **not** touch the filesystem.

```bash
dotidx remove zsh
dotidx remove -p ~/.zshrc
```

### `list`
Prints all paths tracked under the active profile.

```bash
dotidx list
```

### `update`
Copies all tracked files to `~/dotidxBackup/<profile>/`, prunes stale entries, and commits + pushes if the backup directory has a `.git` repo.

```bash
dotidx update
```

### `sync`
Restores files from `~/dotidxBackup/<profile>/` back to their original locations in `$HOME`, overwriting current versions. Use this when setting up a new machine.

```bash
dotidx sync
```

### `rest`
⚠️ **Destructive.** Deletes the active profile's backup directory, removes the profile from `track.conf`, and clears `state.conf`. This cannot be undone.

```bash
dotidx rest
```

### `profile [name]`
Switches the active profile. If no name is given, prints the current profile.

```bash
dotidx profile
dotidx profile work
```

---

## File Structure

| Path | Purpose |
| :--- | :--- |
| `~/.config/dotidx/track.conf` | JSON map of tracked paths to their owning profiles |
| `~/.config/dotidx/state.conf` | Name of the currently active profile |
| `~/dotidxBackup/<profile>/` | Physical backup directory per profile |
| `/usr/share/dotidx/` | Installed library (`main.py`, `interactive.py`) |
| `/usr/share/dotidx/scripts/` | Shell scripts (`setup.sh`, `update.sh`, `sync.sh`, `rest.sh`) |

---

## License
MIT — see `LICENSE` for details.

© 2026 Ariel Baron.
