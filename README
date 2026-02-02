# dotidx v1.0.0

![AUR version](https://img.shields.io/aur/version/dotidx?color=blue&style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)
![Platform: Arch Linux](https://img.shields.io/badge/Platform-Arch_Linux-1793d1?logo=arch-linux&style=flat-square)

`dotidx` is a high-performance, manifest-driven dotfile manager. It prioritizes physical isolation over symbolic linking, ensuring that your system configuration remains stable even if the backup repository is detached or corrupted.

---

## 1. Technical Architecture

`dotidx` operates on a three-tier architecture: The Core Logic, The Manifest Layer, and The Physical Sync Engine.

### 1.1 Directory Structure
| Path | Purpose |
| :--- | :--- |
| `/usr/bin/dotidx` | Primary entry point (symbolic link to shared script). |
| `/usr/share/dotidx/` | Global library containing `main.py` and `interactive.py`. |
| `/usr/share/dotidx/scripts/` | Shell-level utility hooks for post-sync automation. |
| `~/.config/dotidx/` | User-specific application state. |
| `~/.config/dotidx/config.json` | Global application settings and active profile pointer. |
| `~/.config/dotidx/profiles/` | Directory containing plaintext `.txt` manifests. |

### 1.2 Sync Logic
The tool utilizes `rsync` with the following default flag set: `rsync -avzP --delete --ignore-missing-args`. This ensures:
- Atomicity: File transfers are handled as discrete units.
- Integrity: `--delete` ensures the target matches the source exactly.
- Compression: `-z` reduces I/O overhead during synchronization.

---

## 2. Installation

### 2.1 Arch User Repository (Recommended)
```bash
yay -S dotidx
```

### 2.2 Manual Installation (Development)
```bash
git clone https://github.com/ArielBaron/dotidx.git
cd dotidx
mkdir -p ~/.config/dotidx/profiles
ln -s $(pwd)/main.py ~/.local/bin/dotidx
```

---

## 3. Command Reference

### 3.1 `setup`
Initializes the `dotidx` environment.
- Behavior: Checks for existing config files. If missing, prompts for the absolute path to your git backup repository.
- Usage: `dotidx setup`

### 3.2 `add [path]`
Registers a file or directory into the current active profile.
- Optional: `-p`, `--path` (Raw path interpretation).
- Behavior: Resolves relative paths to absolute paths, checks for read permissions, and appends the entry to the manifest file.

### 3.3 `remove [path]`
De-registers a path from the manifest.
- Behavior: Performs a string match removal from the current `.txt` profile. Does not modify the physical filesystem.

### 3.4 `list`
Displays the current state of tracked files.
- UI: Renders a formatted table using `python-rich` displaying path, type (File/Dir), and local existence status.

### 3.5 `update`
Synchronizes system files to the backup repository (Push).
- Flags: `--verbose` (Displays raw `rsync` output).
- Architecture:
    1. Reads active profile.
    2. Resolves paths.
    3. Executes `rsync` from `$HOME` source to `$BACKUP` target.

### 3.6 `rest`
Restores files from the backup repository to the system (Pull).
- Risk: Overwrites local files with repository versions.
- Usage: Ideal for setting up a new machine.

### 3.7 `profile`
Manages multiple isolated environments.
- `dotidx profile [name]`: Switch to specified profile.
- `dotidx profile --list`: List all discovered manifests in `~/.config/dotidx/profiles/`.
- `dotidx profile --create [name]`: Initialize a new empty manifest.

### 3.8 `interactive`
Launches the TUI menu.
- Behavior: Allows visual selection of profiles and sync operations without typing subcommands.

---

## 4. Configuration Specification (`config.json`)

The configuration file follows this schema:
```json
{
  "backup_path": "/home/user/code/dotfiles",
  "active_profile": "main",
  "rsync_flags": "-avzP",
  "last_sync": "2026-01-31T17:00:00"
}
```

---

## 5. Comparison with Industry Standards

| Metric | dotidx | GNU Stow | yadm |
| :--- | :--- | :--- | :--- |
| **Logic** | Physical Sync | Symlink Farm | Git Sparse-checkout |
| **Dependency** | Python, rsync | Perl | Git |
| **Isolation** | Cold storage | Intertwined | Intertwined |
| **Multi-Profile**| Native manifests | Folder-based | Branch-based |
| **Complexity** | 1 (Simple) | 2 (Medium) | 3 (Expert) |

---

## 6. Development and Troubleshooting

### 6.1 Known Issues
- Path Expansion: Ensure paths do not contain trailing slashes unless intended for directory-only content sync.
- Permission Errors: `dotidx` requires read access to files tracked. Use `chmod` to rectify before running `update`.

### 6.2 Contributing
1. Fork the repository.
2. Implement features in a separate branch.
3. Ensure `interactive.py` logic is maintained.
4. Submit PR against `main`.

---

## 7. License
This project is licensed under the MIT License - see the LICENSE file for details.

---
© 2026 Ariel Baron. All Rights Reserved.
