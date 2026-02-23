# YT Music TUI

A beautiful terminal-based YouTube Music player for Linux.

![YT Music TUI](https://img.shields.io/badge/Linux-Fedora-%23354d20?logo=fedora)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python)

## Features

- 🎵 Stream audio directly from YouTube
- 🔍 Search YouTube from within the terminal
- 📋 Queue management system
- 🎨 Beautiful dark-themed UI with progress bar
- ⌨️ Full keyboard navigation

## One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/huseyincorakli/yt-music-terminal/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/yourusername/yt-music-terminal.git
cd yt-music-terminal
chmod +x install.sh
./install.sh
```

## Prerequisites

### System Packages (Required)

| Package | Fedora | Ubuntu/Debian | Arch |
|---------|--------|---------------|------|
| `mpv` | `dnf install mpv` | `apt install mpv` | `pacman -S mpv` |
| `python3` | `dnf install python3` | `apt install python3` | `pacman -S python` |

### Python Packages

Installed automatically by `install.sh`:
- `textual>=0.60.0` — TUI framework
- `yt-dlp>=2024.1.0` — YouTube search and streaming

## Usage

```bash
ytmusic
```

## Keybindings

| Key | Action |
|-----|--------|
| `/` | Search |
| `Enter` | Play selected |
| `Space` | Pause / Resume |
| `n` | Next in queue |
| `a` | Add to queue |
| `d` | Remove from queue |
| `Esc` | Focus results |
| `q` | Quit |

## Known Limitations

- **mpv required**: `mpv` must be installed via your system's package manager (not pip)
- **YouTube dependency**: Search functionality depends on `yt-dlp`, which may need occasional updates as YouTube changes its API
- **Linux only**: Currently supports Linux distributions only (tested on Fedora, Ubuntu, Arch)

## Uninstall

```bash
rm -f ~/.local/bin/ytmusic
pip uninstall -y textual yt-dlp
```

Then remove the PATH addition from your `~/.bashrc` or `~/.zshrc` if desired.

## License

MIT
