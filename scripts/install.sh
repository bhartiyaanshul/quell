#!/usr/bin/env bash
# Quell — one-command installer.
#
# This script gets you from a fresh clone to a working `quell` binary
# on your PATH.  It:
#
#   1. Verifies Python 3.12+ is available (or tells you how to install it).
#   2. Installs pipx if it's missing (via brew / apt / dnf / pacman).
#   3. Installs Quell as a pipx app from the current directory.
#   4. Verifies `quell --version` works in a fresh shell.
#   5. Optionally runs `quell init` right away.
#
# Usage:
#   ./scripts/install.sh            # interactive
#   ./scripts/install.sh --yes      # assume yes to all prompts
#   ./scripts/install.sh --dev      # editable dev install (no pipx)
#
# Safe to re-run.  Existing installs are upgraded with --force.

set -euo pipefail

# ---------------------------------------------------------------------------
# Pretty output
# ---------------------------------------------------------------------------

if [ -t 1 ]; then
    BOLD="$(tput bold 2>/dev/null || printf '')"
    DIM="$(tput dim 2>/dev/null || printf '')"
    RED="$(tput setaf 1 2>/dev/null || printf '')"
    GREEN="$(tput setaf 2 2>/dev/null || printf '')"
    YELLOW="$(tput setaf 3 2>/dev/null || printf '')"
    BLUE="$(tput setaf 4 2>/dev/null || printf '')"
    RESET="$(tput sgr0 2>/dev/null || printf '')"
else
    BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; RESET=""
fi

step()  { printf "\n${BOLD}${BLUE}▶ %s${RESET}\n" "$*"; }
ok()    { printf "${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "${YELLOW}!${RESET} %s\n" "$*"; }
err()   { printf "${RED}✗${RESET} %s\n" "$*" >&2; }
say()   { printf "  %s\n" "$*"; }

banner() {
    printf "\n"
    printf "${BOLD}Quell installer${RESET}\n"
    printf "${DIM}%s${RESET}\n" "Your production's autonomous on-call."
    printf "\n"
}

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------

ASSUME_YES=0
DEV_MODE=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) ASSUME_YES=1 ;;
        --dev)    DEV_MODE=1 ;;
        -h|--help)
            sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) err "Unknown flag: $arg"; exit 1 ;;
    esac
done

confirm() {
    # Usage: confirm "Message" default_answer
    local msg="$1" default="${2:-y}"
    if [ "$ASSUME_YES" = "1" ]; then
        return 0
    fi
    local prompt="[Y/n]"
    if [ "$default" = "n" ]; then prompt="[y/N]"; fi
    read -r -p "  $msg $prompt " reply
    reply="${reply:-$default}"
    case "$reply" in
        [Yy]*) return 0 ;;
        *)     return 1 ;;
    esac
}

# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

detect_os() {
    case "$(uname -s)" in
        Darwin) echo "macos" ;;
        Linux)  echo "linux" ;;
        *)      echo "unknown" ;;
    esac
}

OS="$(detect_os)"

package_manager() {
    if [ "$OS" = "macos" ]; then
        command -v brew >/dev/null 2>&1 && { echo "brew"; return; }
    fi
    if [ "$OS" = "linux" ]; then
        command -v apt-get >/dev/null 2>&1 && { echo "apt"; return; }
        command -v dnf     >/dev/null 2>&1 && { echo "dnf"; return; }
        command -v pacman  >/dev/null 2>&1 && { echo "pacman"; return; }
    fi
    echo "unknown"
}

PKG="$(package_manager)"

install_with_pm() {
    # Install a package by name using the detected package manager.
    local pkg="$1"
    case "$PKG" in
        brew)   brew install "$pkg" ;;
        apt)    sudo apt-get update -qq && sudo apt-get install -y "$pkg" ;;
        dnf)    sudo dnf install -y "$pkg" ;;
        pacman) sudo pacman -S --noconfirm "$pkg" ;;
        *)      return 1 ;;
    esac
}

# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

banner

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ ! -f "$REPO_ROOT/pyproject.toml" ] || ! grep -q '^name = "quell-agent"' "$REPO_ROOT/pyproject.toml"; then
    err "scripts/install.sh must be run from inside the Quell repo."
    err "Current REPO_ROOT=$REPO_ROOT does not look like the Quell checkout."
    exit 1
fi
say "Repo: ${DIM}$REPO_ROOT${RESET}"
say "OS:   ${DIM}$OS (package manager: $PKG)${RESET}"

# ---------------------------------------------------------------------------
# Step 1 — Python 3.12+
# ---------------------------------------------------------------------------

step "Checking Python 3.12+"

PYTHON=""
for cand in python3.12 python3.13 python3.14 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        ver="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
        major="${ver%%.*}"
        minor="${ver##*.}"
        if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]; then
            PYTHON="$(command -v "$cand")"
            ok "Found $cand → $PYTHON (Python $ver)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "No Python 3.12+ on PATH."
    case "$PKG" in
        brew)   say "Install: ${BOLD}brew install python@3.12${RESET}" ;;
        apt)    say "Install: ${BOLD}sudo apt-get install python3.12 python3.12-venv${RESET}" ;;
        dnf)    say "Install: ${BOLD}sudo dnf install python3.12${RESET}" ;;
        pacman) say "Install: ${BOLD}sudo pacman -S python${RESET}" ;;
        *)      say "Install Python 3.12 from https://www.python.org/downloads/" ;;
    esac
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2 — Branch: pipx install vs editable dev install
# ---------------------------------------------------------------------------

if [ "$DEV_MODE" = "1" ]; then
    step "Editable dev install (requested via --dev)"

    if [ ! -d "$REPO_ROOT/.venv" ]; then
        say "Creating venv at $REPO_ROOT/.venv"
        "$PYTHON" -m venv "$REPO_ROOT/.venv"
    fi

    "$REPO_ROOT/.venv/bin/pip" install --upgrade pip -q
    "$REPO_ROOT/.venv/bin/pip" install -e "$REPO_ROOT" -q
    "$REPO_ROOT/.venv/bin/pip" install -q pytest pytest-asyncio pytest-cov ruff mypy

    ok "Installed in editable mode."
    say ""
    say "${BOLD}Activate the venv to get the quell command:${RESET}"
    say "  ${DIM}source $REPO_ROOT/.venv/bin/activate${RESET}"
    say "  ${DIM}quell --version${RESET}"
    say ""
    say "Or run directly without activating:"
    say "  ${DIM}$REPO_ROOT/.venv/bin/quell --version${RESET}"
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 2 (normal path) — pipx
# ---------------------------------------------------------------------------

step "Checking pipx"

if ! command -v pipx >/dev/null 2>&1; then
    warn "pipx is not installed."
    if confirm "Install pipx now via $PKG?"; then
        case "$PKG" in
            brew)   install_with_pm pipx ;;
            apt)    install_with_pm pipx ;;
            dnf)    install_with_pm pipx ;;
            pacman) install_with_pm python-pipx ;;
            *)
                err "No supported package manager detected."
                say "Install pipx manually: https://pipx.pypa.io/latest/installation/"
                exit 1
                ;;
        esac
    else
        err "Cannot continue without pipx.  See --dev for a venv-based alternative."
        exit 1
    fi
fi

ok "pipx: $(command -v pipx)"

# Force pipx to use the Python we detected for its shared environment.
# Without this, pipx may default to a broken or misconfigured system
# Python (common on macOS when brew installed a newer python@ as a
# side-effect of installing pipx itself and failed to symlink it).
export PIPX_DEFAULT_PYTHON="$PYTHON"

pipx ensurepath >/dev/null 2>&1 || true

# pipx puts shims in ~/.local/bin (Linux) or ~/.local/bin (macOS).  The
# current shell may not yet have this in PATH.  We'll verify at the end.

# If pipx's shared env is already broken (from a previous failed run or
# a brew Python conflict), reinitialise it against our verified Python.
if ! pipx list >/dev/null 2>&1; then
    warn "pipx's shared environment is broken — rebuilding it with $PYTHON."
    rm -rf "$HOME/.local/pipx/shared" 2>/dev/null || true
    rm -rf "$HOME/.local/share/pipx/shared" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Step 3 — Install Quell
# ---------------------------------------------------------------------------

step "Installing Quell via pipx"

if pipx list --short 2>/dev/null | grep -q '^quell-agent '; then
    say "Existing installation found — upgrading with --force."
    pipx install --force --python "$PYTHON" "$REPO_ROOT"
else
    pipx install --python "$PYTHON" "$REPO_ROOT"
fi

ok "Quell installed."

# ---------------------------------------------------------------------------
# Step 4 — Verify
# ---------------------------------------------------------------------------

step "Verifying the install"

# pipx puts the binary in $PIPX_BIN_DIR (default ~/.local/bin).
PIPX_BIN="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$HOME/.local/bin")"
QUELL_BIN="$PIPX_BIN/quell"

if [ ! -x "$QUELL_BIN" ]; then
    err "Expected $QUELL_BIN to exist but it doesn't."
    exit 1
fi

VERSION_OUTPUT="$("$QUELL_BIN" --version 2>&1 || true)"
if [[ "$VERSION_OUTPUT" != *"quell-agent"* ]]; then
    err "Installed binary did not return a quell-agent version string."
    err "Got: $VERSION_OUTPUT"
    exit 1
fi

ok "$VERSION_OUTPUT"
say "Binary: ${DIM}$QUELL_BIN${RESET}"

# ---------------------------------------------------------------------------
# Step 5 — PATH check
# ---------------------------------------------------------------------------

if ! command -v quell >/dev/null 2>&1; then
    warn "'quell' is not yet on PATH in this shell."
    say "Run ONE of the following, then re-open your terminal:"
    say ""
    say "  ${BOLD}For zsh (default on macOS):${RESET}"
    say "    ${DIM}echo 'export PATH=\"$PIPX_BIN:\$PATH\"' >> ~/.zshrc${RESET}"
    say ""
    say "  ${BOLD}For bash:${RESET}"
    say "    ${DIM}echo 'export PATH=\"$PIPX_BIN:\$PATH\"' >> ~/.bashrc${RESET}"
    say ""
    say "Or restart your shell:  ${BOLD}exec \$SHELL -l${RESET}"
else
    ok "quell is on PATH as $(command -v quell)"
fi

# ---------------------------------------------------------------------------
# Step 6 — Next steps (+ optional quell init)
# ---------------------------------------------------------------------------

step "Next steps"
say "1.  ${BOLD}cd${RESET} into the project you want Quell to watch."
say "2.  ${BOLD}quell init${RESET}    — interactive setup wizard."
say "3.  ${BOLD}quell doctor${RESET}  — verify environment + API key."
say "4.  ${BOLD}quell watch${RESET}   — start the investigation loop."
say ""
say "Full docs: ${BOLD}docs/getting-started.md${RESET}"
printf "\n${GREEN}${BOLD}✓ Quell is installed.${RESET}\n\n"

if [ "$ASSUME_YES" != "1" ] && command -v quell >/dev/null 2>&1; then
    if confirm "Run 'quell init' now in the current directory?" "n"; then
        exec quell init
    fi
fi
