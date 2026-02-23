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
    if command -v mpv &>/dev/null; then
        return 0
    fi

    warn "mpv bulunamadı."
    echo ""
    echo "  Fedora/RHEL : sudo dnf install mpv"
    echo "  Ubuntu/Debian: sudo apt install mpv"
    echo "  Arch         : sudo pacman -S mpv"
    echo "  macOS        : brew install mpv"
    echo ""
    read -r -p "mpv'yi otomatik kurmamı ister misiniz? [e/H] " reply
    case "$reply" in
        [eEyY]*)
            install_mpv
            ;;
        *)
            error "mpv olmadan devam edilemiyor."
            ;;
    esac
}

install_mpv() {
    if command -v dnf &>/dev/null; then
        sudo dnf install -y mpv
    elif command -v apt &>/dev/null; then
        sudo apt-get install -y mpv
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm mpv
    elif command -v brew &>/dev/null; then
        brew install mpv
    else
        error "Paket yöneticisi bulunamadı."
    fi
}

ensure_uv() {
    if command -v uv &>/dev/null; then
        return 0
    fi
    info "uv kuruluyor..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    command -v uv &>/dev/null || error "uv kurulumu başarısız."
}

install_ytmusic() {
    info "ytmusic kuruluyor..."
    export PATH="$HOME/.local/bin:$PATH"
    uv tool install "git+${REPO_URL}" --force
}

check_path() {
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        warn "~/.local/bin PATH'inizde değil."
        echo ""
        echo "  Aşağıdaki satırı shell config dosyanıza ekleyin:"
        echo ""
        echo '    export PATH="$HOME/.local/bin:$PATH"'
        echo ""
    fi
}

echo -e "\n${BOLD}▶ YT Music TUI Kurulumu${NC}\n"

check_mpv
ensure_uv
install_ytmusic
check_path

echo ""
echo -e "${GREEN}✓ Kurulum tamamlandı!${NC} Çalıştırmak için: ${BOLD}ytmusic${NC}"
echo ""
