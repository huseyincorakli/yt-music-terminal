#!/usr/bin/env bash
#
# YT Music TUI Installer
# Uses uv tool install for isolated installation
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
BOLD='\033[1m'

info()  { echo -e "${GREEN}➜${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $*"; }
error() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

REPO_URL="https://github.com/huseyincorakli/yt-music-terminal"

check_mpv() {
    if command -v mpv &>/dev/null && command -v git &>/dev/null; then
        return 0
    fi

    warn "Missing dependencies detected."
    echo ""
    echo "  Fedora/RHEL : sudo dnf install mpv git"
    echo "  Ubuntu/Debian: sudo apt install mpv git"
    echo "  Arch         : sudo pacman -S mpv git"
    echo "  macOS        : brew install mpv git"
    echo ""
    read -r -p "Install automatically? [y/N] " reply
    case "$reply" in
        [yY]*)
            install_mpv
            ;;
        *)
            error "Required packages not found."
            ;;
    esac
}

install_mpv() {
    if command -v dnf &>/dev/null; then
        sudo dnf install -y mpv git
    elif command -v apt &>/dev/null; then
        sudo apt-get install -y mpv git
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm mpv git
    elif command -v brew &>/dev/null; then
        brew install mpv git
    else
        error "Package manager not found."
    fi
}

ensure_uv() {
    if command -v uv &>/dev/null; then
        return 0
    fi
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv &>/dev/null || error "uv installation failed."
}

install_ytmusic() {
    info "Installing ytmusic..."
    export PATH="$HOME/.local/bin:$PATH"
    uv tool install "git+${REPO_URL}" --force
}

check_path() {
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        warn "~/.local/bin not in your PATH."
        echo ""
        echo "  Add this to your shell config:"
        echo ""
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo ""
    fi
}

echo -e "\n${BOLD}▶ YT Music TUI Installation${NC}\n"

check_mpv
ensure_uv
install_ytmusic
check_path

echo ""
echo -e "${GREEN}✓ Installation complete!${NC} Run with: ${BOLD}ytmusic${NC}"
echo ""
