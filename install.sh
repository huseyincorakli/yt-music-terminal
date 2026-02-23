#!/usr/bin/env bash
#
# YT Music TUI Installer
# One-command install for Fedora, Ubuntu, and Arch Linux
#

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/huseyincorakli/yt-music-terminal.git}"

# ═══════════════════════════════════════════════════════════════════════════════
#  Colors
# ═══════════════════════════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════
log_info()  { echo -e "${BLUE}➜${NC} $*"; }
log_ok()    { echo -e "${GREEN}✓${NC} $*"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*"; }

# ═══════════════════════════════════════════════════════════════════════════════
#  Detect Distribution
# ═══════════════════════════════════════════════════════════════════════════════
detect_distro() {
    if [[ -f /etc/fedora-release ]] || [[ -f /etc/redhat-release ]]; then
        echo "fedora"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/arch-release ]]; then
        echo "arch"
    elif command -v dnf &>/dev/null; then
        echo "fedora"
    elif command -v apt &>/dev/null; then
        echo "debian"
    elif command -v pacman &>/dev/null; then
        echo "arch"
    else
        echo "unknown"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
#  Detect Shell (user's login shell, not the script's ═════════════════════════ shell)
#══════════════════════════════════════════════════════
detect_shell() {
    USER_SHELL=$(getent passwd "$USER" | cut -d: -f7)
    case "$USER_SHELL" in
        */zsh)
            echo "zsh"
            ;;
        */fish)
            echo "fish"
            ;;
        */bash)
            echo "bash"
            ;;
        *)
            echo "bash"
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════════
#  Check if command exists
# ═══════════════════════════════════════════════════════════════════════════════
has_command() {
    command -v "$1" &>/dev/null
}

# ═══════════════════════════════════════════════════════════════════════════════
#  Main Install Function
# ═══════════════════════════════════════════════════════════════════════════════
main() {
    echo -e "${BOLD}▶ YT Music TUI Installer${NC}"
    echo ""

    # Detect distro
    DISTRO=$(detect_distro)
    log_info "Detected distribution: ${DISTRO}"

    # ═══════════════════════════════════════════════════════════════════════════
    #  Install System Dependencies
    # ═══════════════════════════════════════════════════════════════════════════════
    log_info "Installing system dependencies..."

    case "$DISTRO" in
        fedora)
            if has_command dnf; then
                sudo dnf install -y git mpv python3 || log_warn "Failed to install packages"
            else
                log_error "dnf not found. Please install mpv and python3 manually."
            fi
            ;;
        arch)
            if has_command pacman; then
                sudo pacman -Sy --noconfirm git mpv python python-pip || log_warn "Failed to install some packages"
            else
                log_error "pacman not found. Please install mpv and python3 manually."
            fi
            ;;
        debian)
            if has_command apt; then
                sudo apt update && sudo apt install -y git mpv python3 python3-pip || log_warn "Failed to install some packages"
            else
                log_error "apt not found. Please install mpv and python3 manually."
            fi
            ;;
        *)
            log_warn "Unknown distribution. Please install mpv and python3 manually."
            ;;
    esac

    # Check if mpv is installed now
    if ! has_command mpv; then
        log_warn "mpv not found in PATH. You may need to reopen your terminal or install it manually."
    fi

    # ═══════════════════════════════════════════════════════════════════════════════
    #  Install Python Dependencies
    # ═══════════════════════════════════════════════════════════════════════════════
    log_info "Installing Python dependencies..."

    # Get script directory (where main.py should be)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Handle case when script is piped from curl (stdin)
    # Check if we have the needed files, if not, clone the repo
    if [[ ! -f "$SCRIPT_DIR/pyproject.toml" ]]; then
        log_info "Downloading yt-music-terminal..."
        SCRIPT_DIR="$HOME/ytmusic-install"
        rm -rf "$SCRIPT_DIR"
        git clone --depth 1 "$REPO_URL" "$SCRIPT_DIR"
    fi
    
    REQUIREMENTS="${SCRIPT_DIR}/requirements.txt"

    if [[ ! -f "$REQUIREMENTS" ]]; then
        log_error "requirements.txt not found in ${SCRIPT_DIR}"
        exit 1
    fi

    # Install uv (modern, fast Python package manager)
    if ! has_command uv; then
        log_info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 || \
            log_warn "Failed to install uv"
    fi

    # Source uv if installed but not in PATH
    if [[ -f "$HOME/.local/bin/uv" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # Install Python packages using uv (creates virtualenv automatically)
    if has_command uv; then
        log_info "Installing Python packages with uv..."
        # Add to PATH temporarily for this session
        export PATH="$HOME/.local/bin:$PATH"
        
        # Create venv and install packages
        cd "$SCRIPT_DIR"
        uv venv .venv 2>/dev/null || true
        source .venv/bin/activate 2>/dev/null || true
        uv pip install textual yt-dlp 2>&1 || \
            (deactivate 2>/dev/null; rm -rf .venv; uv venv .venv && source .venv/bin/activate && uv pip install textual yt-dlp) 2>&1 || \
            log_warn "uv failed, trying pip..."
        
        # If uv failed, use pip as fallback
        if ! has_command textual 2>/dev/null; then
            log_info "Falling back to pip..."
            pip install --user --break-system-packages textual yt-dlp 2>&1 || \
                pip3 install --user --break-system-packages textual yt-dlp 2>&1 || \
                log_error "Failed to install Python packages"
        fi
    else
        # No uv, use pip
        log_info "Installing Python packages with pip..."
        pip install --user --break-system-packages textual yt-dlp 2>&1 || \
            pip3 install --user --break-system-packages textual yt-dlp 2>&1 || \
            log_error "Failed to install Python packages"
    fi

    # ═══════════════════════════════════════════════════════════════════════════════
    #  Install ytmusic Package (editable mode)
    # ═══════════════════════════════════════════════════════════════════════════════
    log_info "Installing ytmusic package..."

    if [[ ! -d "${SCRIPT_DIR}/src/ytmusic" ]]; then
        log_error "src/ytmusic not found in ${SCRIPT_DIR}"
        exit 1
    fi

    # Copy source files to a fixed location
    INSTALL_DIR="$HOME/.local/share/ytmusic"
    mkdir -p "$INSTALL_DIR"
    cp -r "${SCRIPT_DIR}/src" "$INSTALL_DIR/"
    cp "${SCRIPT_DIR}/main.py" "$INSTALL_DIR/"
    
    # Create wrapper script that sets PYTHONPATH
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/ytmusic" << WRAPPER
#!/bin/bash
exec python3 "$HOME/.local/share/ytmusic/main.py" "\$@"
WRAPPER
    chmod +x "$HOME/.local/bin/ytmusic"

    # ═══════════════════════════════════════════════════════════════════════════════
    #  Add to PATH (if needed)
    # ═══════════════════════════════════════════════════════════════════════════════
    SHELL_NAME=$(detect_shell)
    PATH_ADDED=false

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        log_info "Adding ~/.local/bin to PATH..."

        case "$SHELL_NAME" in
            bash)
                BASHRC="$HOME/.bashrc"
                if [[ -f "$BASHRC" ]] && ! grep -q 'export PATH="\$HOME/.local/bin"' "$BASHRC"; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$BASHRC"
                    PATH_ADDED=true
                elif [[ ! -f "$BASHRC" ]]; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$BASHRC"
                    PATH_ADDED=true
                fi
                ;;
            zsh)
                ZSHRC="$HOME/.zshrc"
                if [[ -f "$ZSHRC" ]] && ! grep -q 'export PATH="\$HOME/.local/bin"' "$ZSHRC"; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$ZSHRC"
                    PATH_ADDED=true
                elif [[ ! -f "$ZSHRC" ]]; then
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$ZSHRC"
                    PATH_ADDED=true
                fi
                ;;
            fish)
                FISHCONF="$HOME/.config/fish/config.fish"
                mkdir -p "$HOME/.config/fish"
                if [[ -f "$FISHCONF" ]] && ! grep -q '.local/bin' "$FISHCONF"; then
                    echo 'set -gx PATH $HOME/.local/bin $PATH' >> "$FISHCONF"
                    PATH_ADDED=true
                elif [[ ! -f "$FISHCONF" ]]; then
                    echo 'set -gx PATH $HOME/.local/bin $PATH' >> "$FISHCONF"
                    PATH_ADDED=true
                fi
                ;;
        esac
    fi

    # ═══════════════════════════════════════════════════════════════════════════════
    #  Final Message
    # ═══════════════════════════════════════════════════════════════════════════════
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${GREEN}✓ Installation complete!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${BOLD}Usage:${NC}"
    echo "    ytmusic"
    echo ""
    echo -e "  ${BOLD}Keybindings:${NC}"
    echo "    /      Search"
    echo "    Enter  Play selected"
    echo "    Space  Pause/Resume"
    echo "    n      Next in queue"
    echo "    a      Add to queue"
    echo "    d      Remove from queue"
    echo "    Esc    Focus results"
    echo "    q      Quit"
    echo ""

    if [[ "$PATH_ADDED" == "true" ]]; then
        echo -e "  ${YELLOW}⚠ PATH was updated. Run this to apply immediately:${NC}"
        echo -e "      ${BOLD}source ~/${SHELL_NAME}rc${NC}"
    fi

    if ! has_command mpv; then
        echo -e "  ${YELLOW}⚠ Warning: mpv not found. Please install mpv and restart terminal.${NC}"
    fi

    echo ""
}

main "$@"
