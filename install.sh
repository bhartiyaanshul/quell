#!/usr/bin/env bash
# Quell — one-command installer.
#
# Install from anywhere with no prerequisites beyond git + Python 3.12:
#
#     curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash
#
# What it does:
#   1. Checks for Python 3.12+ and git.
#   2. Installs pipx if it's missing (brew / apt / dnf / pacman).
#   3. Clones Quell to ~/.cache/quell/source (idempotent upgrade on re-run).
#   4. Installs Quell as a pipx app so `quell` lands on your PATH.
#   5. Prints next steps.
#
# Advanced usage:
#   ./install.sh --yes         # assume yes to all prompts
#   ./install.sh --dev         # editable dev install (no pipx) — for contributors
#   ./install.sh --ref=BRANCH  # install from a specific git ref (default: main)
#   QUELL_SOURCE=/path ./install.sh   # skip clone, use existing checkout
#
# Safe to re-run.  Existing installs are upgraded.

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

# ---------------------------------------------------------------------------
# Config + flags
# ---------------------------------------------------------------------------

QUELL_REPO="${QUELL_REPO:-https://github.com/bhartiyaanshul/quell.git}"
QUELL_OWNER="${QUELL_OWNER:-bhartiyaanshul/quell}"
QUELL_CACHE_DIR="${QUELL_CACHE_DIR:-$HOME/.cache/quell}"
QUELL_SOURCE="${QUELL_SOURCE:-}"
QUELL_INSTALL_DIR="${QUELL_INSTALL_DIR:-$HOME/.local/bin}"
REF="main"
ASSUME_YES=0
DEV_MODE=0
FORCE_SOURCE=0

for arg in "$@"; do
    case "$arg" in
        --yes|-y)      ASSUME_YES=1 ;;
        --dev)         DEV_MODE=1 ;;
        --from-source) FORCE_SOURCE=1 ;;
        --ref=*)       REF="${arg#--ref=}" ;;
        -h|--help)
            sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) err "Unknown flag: $arg"; exit 1 ;;
    esac
done

confirm() {
    local msg="$1" default="${2:-y}"
    if [ "$ASSUME_YES" = "1" ]; then
        return 0
    fi
    local prompt="[Y/n]"
    if [ "$default" = "n" ]; then prompt="[y/N]"; fi
    read -r -p "  $msg $prompt " reply </dev/tty || reply=""
    reply="${reply:-$default}"
    case "$reply" in [Yy]*) return 0 ;; *) return 1 ;; esac
}

# ---------------------------------------------------------------------------
# OS + package manager
# ---------------------------------------------------------------------------

case "$(uname -s)" in
    Darwin) OS="macos" ;;
    Linux)  OS="linux" ;;
    *)      OS="unknown" ;;
esac

detect_pm() {
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
PKG="$(detect_pm)"

pm_install() {
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
# Banner
# ---------------------------------------------------------------------------

printf "\n${BOLD}Quell installer${RESET}\n"
printf "${DIM}Your production's autonomous on-call.${RESET}\n\n"
say "OS:   ${DIM}$OS (pm: $PKG)${RESET}"
say "Ref:  ${DIM}$REF${RESET}"
say "Mode: ${DIM}$( [ "$DEV_MODE" = "1" ] && echo 'dev (editable)' || echo 'binary → pipx fallback' )${RESET}"

# ---------------------------------------------------------------------------
# Fast path — try the prebuilt standalone binary first.
# ---------------------------------------------------------------------------
# Maps `uname -s` / `uname -m` to the asset naming convention used by
# .github/workflows/build-binaries.yml.  If the matching asset exists on
# the latest release, we install it and skip Python entirely — no pipx,
# no clone, no compile, just one download + chmod.

try_prebuilt_binary() {
    if [ "$DEV_MODE" = "1" ] || [ "$FORCE_SOURCE" = "1" ]; then
        return 1
    fi
    command -v curl >/dev/null 2>&1 || return 1

    local uname_s uname_m arch asset_name asset_url tmpdir
    uname_s="$(uname -s)"
    uname_m="$(uname -m)"
    case "$uname_m" in
        arm64|aarch64) arch="arm64" ;;
        x86_64|amd64)  arch="x86_64" ;;
        *)             return 1 ;;
    esac
    asset_name="quell-${uname_s}-${arch}.tar.gz"
    asset_url="https://github.com/${QUELL_OWNER}/releases/latest/download/${asset_name}"

    step "Trying prebuilt binary (${asset_name})"

    # Probe the release page — GitHub redirects 404 for missing assets.
    if ! curl -fsSLI "$asset_url" >/dev/null 2>&1; then
        warn "No prebuilt binary published yet — falling back to Python install."
        return 1
    fi

    tmpdir="$(mktemp -d)"
    trap 'rm -rf "$tmpdir"' EXIT
    curl -fsSL "$asset_url" -o "$tmpdir/$asset_name"
    tar -xzf "$tmpdir/$asset_name" -C "$tmpdir"
    mkdir -p "$QUELL_INSTALL_DIR"
    rm -rf "$QUELL_INSTALL_DIR/quell" "$QUELL_INSTALL_DIR/.quell-runtime" 2>/dev/null || true
    # The archive expands to ./quell/{quell, _internal/, ...}.  We install
    # the directory under a hidden name and symlink the executable so
    # upgrades are atomic.
    mv "$tmpdir/quell" "$QUELL_INSTALL_DIR/.quell-runtime"
    ln -sf "$QUELL_INSTALL_DIR/.quell-runtime/quell" "$QUELL_INSTALL_DIR/quell"
    chmod +x "$QUELL_INSTALL_DIR/.quell-runtime/quell"
    ok "Installed standalone binary to $QUELL_INSTALL_DIR/quell"
    return 0
}

if try_prebuilt_binary; then
    PIPX_BIN="$QUELL_INSTALL_DIR"
    QUELL_BIN="$QUELL_INSTALL_DIR/quell"
    SKIP_PYTHON_INSTALL=1
else
    SKIP_PYTHON_INSTALL=0
fi

# ---------------------------------------------------------------------------
# Step 1 — Python
# ---------------------------------------------------------------------------

if [ "$SKIP_PYTHON_INSTALL" = "1" ]; then
    step "Skipping Python install path (prebuilt binary succeeded)"
    PYTHON=""
    SRC_DIR=""
    goto_verify=1
else
    goto_verify=0
fi

if [ "$goto_verify" = "0" ]; then
step "Checking Python 3.12+"

PYTHON=""
for cand in python3.12 python3.13 python3.14 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        ver="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo "0.0")"
        major="${ver%%.*}"; minor="${ver##*.}"
        if [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 12 ]; then
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
        *)      say "Install from https://www.python.org/downloads/" ;;
    esac
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2 — git
# ---------------------------------------------------------------------------

step "Checking git"
if ! command -v git >/dev/null 2>&1; then
    err "git is required to fetch Quell sources."
    exit 1
fi
ok "git: $(command -v git)"

# ---------------------------------------------------------------------------
# Step 3 — Fetch / locate Quell source
# ---------------------------------------------------------------------------

step "Fetching Quell source"

if [ -n "$QUELL_SOURCE" ]; then
    if [ ! -f "$QUELL_SOURCE/pyproject.toml" ]; then
        err "QUELL_SOURCE='$QUELL_SOURCE' does not contain pyproject.toml"
        exit 1
    fi
    SRC_DIR="$QUELL_SOURCE"
    ok "Using existing checkout at $SRC_DIR"
elif [ -f "$(dirname "$0")/pyproject.toml" ] && grep -q 'quell-agent' "$(dirname "$0")/pyproject.toml" 2>/dev/null; then
    SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
    ok "Running from checkout at $SRC_DIR"
else
    mkdir -p "$QUELL_CACHE_DIR"
    SRC_DIR="$QUELL_CACHE_DIR/source"
    if [ -d "$SRC_DIR/.git" ]; then
        say "Updating existing clone at $SRC_DIR"
        git -C "$SRC_DIR" fetch --quiet origin
        git -C "$SRC_DIR" checkout --quiet "$REF"
        git -C "$SRC_DIR" reset --hard --quiet "origin/$REF" 2>/dev/null || \
            git -C "$SRC_DIR" reset --hard --quiet "$REF"
    else
        say "Cloning $QUELL_REPO → $SRC_DIR"
        git clone --quiet --depth 1 --branch "$REF" "$QUELL_REPO" "$SRC_DIR"
    fi
    ok "Source ready at $SRC_DIR"
fi

# ---------------------------------------------------------------------------
# Step 4 — Dev branch or pipx branch
# ---------------------------------------------------------------------------

if [ "$DEV_MODE" = "1" ]; then
    step "Editable dev install"
    if [ ! -d "$SRC_DIR/.venv" ]; then
        "$PYTHON" -m venv "$SRC_DIR/.venv"
    fi
    "$SRC_DIR/.venv/bin/pip" install --upgrade pip -q
    "$SRC_DIR/.venv/bin/pip" install -e "$SRC_DIR" -q
    "$SRC_DIR/.venv/bin/pip" install -q pytest pytest-asyncio pytest-cov ruff mypy
    ok "Installed in editable mode at $SRC_DIR/.venv"
    say ""
    say "${BOLD}Activate with:${RESET}  ${DIM}source $SRC_DIR/.venv/bin/activate${RESET}"
    say "${BOLD}Or run via:${RESET}      ${DIM}$SRC_DIR/.venv/bin/quell${RESET}"
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 4 (normal) — pipx
# ---------------------------------------------------------------------------

step "Checking pipx"

if ! command -v pipx >/dev/null 2>&1; then
    warn "pipx is not installed."
    if confirm "Install pipx via $PKG?"; then
        case "$PKG" in
            brew|apt|dnf) pm_install pipx ;;
            pacman)       pm_install python-pipx ;;
            *)
                err "No supported package manager.  See https://pipx.pypa.io/"
                exit 1
                ;;
        esac
    else
        err "Cannot continue without pipx.  Re-run with --dev for a venv install."
        exit 1
    fi
fi
ok "pipx: $(command -v pipx)"

# Pin pipx's shared env + per-app venvs to the Python we verified.  On
# macOS, `brew install pipx` often pulls in a newer python@ as a
# dependency; if that symlink fails, pipx's default Python is broken.
export PIPX_DEFAULT_PYTHON="$PYTHON"
pipx ensurepath >/dev/null 2>&1 || true

# Reset pipx shared env if it's broken.
if ! pipx list >/dev/null 2>&1; then
    warn "pipx shared env is broken — rebuilding against $PYTHON."
    rm -rf "$HOME/.local/pipx/shared" "$HOME/.local/share/pipx/shared" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Step 5 — Install
# ---------------------------------------------------------------------------

step "Installing Quell"
if pipx list --short 2>/dev/null | grep -q '^quell-agent '; then
    pipx install --force --python "$PYTHON" "$SRC_DIR"
else
    pipx install --python "$PYTHON" "$SRC_DIR"
fi
ok "Quell installed."

PIPX_BIN="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$HOME/.local/bin")"
QUELL_BIN="$PIPX_BIN/quell"
fi  # close the `if [ "$goto_verify" = "0" ]` block

# ---------------------------------------------------------------------------
# Step 6 — Verify (runs for both install paths)
# ---------------------------------------------------------------------------

step "Verifying the install"

if [ ! -x "$QUELL_BIN" ]; then
    err "Expected $QUELL_BIN but it doesn't exist."
    exit 1
fi
VERSION_OUTPUT="$("$QUELL_BIN" --version 2>&1 || true)"
if [[ "$VERSION_OUTPUT" != *"quell-agent"* ]]; then
    # Fallback to the `version` subcommand for older builds.
    VERSION_OUTPUT="$("$QUELL_BIN" version 2>&1 || true)"
fi
if [[ "$VERSION_OUTPUT" != *"quell-agent"* ]]; then
    err "Installed binary did not return a quell-agent version string."
    err "Got: $VERSION_OUTPUT"
    exit 1
fi
ok "$VERSION_OUTPUT"
say "Binary: ${DIM}$QUELL_BIN${RESET}"

# ---------------------------------------------------------------------------
# Step 7 — PATH check
# ---------------------------------------------------------------------------

if ! command -v quell >/dev/null 2>&1; then
    warn "'quell' is not yet on PATH in this shell."
    case "$(basename "${SHELL:-}")" in
        zsh)  say "Run: ${BOLD}echo 'export PATH=\"$PIPX_BIN:\$PATH\"' >> ~/.zshrc && exec \$SHELL -l${RESET}" ;;
        bash) say "Run: ${BOLD}echo 'export PATH=\"$PIPX_BIN:\$PATH\"' >> ~/.bashrc && exec \$SHELL -l${RESET}" ;;
        *)    say "Add $PIPX_BIN to your shell's PATH and restart." ;;
    esac
else
    ok "quell is on PATH: $(command -v quell)"
fi

# ---------------------------------------------------------------------------
# Step 8 — Next steps
# ---------------------------------------------------------------------------

step "Next steps"
say "1.  ${BOLD}cd${RESET} into the project you want Quell to watch."
say "2.  ${BOLD}quell init${RESET}    — interactive setup wizard."
say "3.  ${BOLD}quell doctor${RESET}  — verify environment + API key."
say "4.  ${BOLD}quell watch${RESET}   — start the investigation loop."
say ""
say "Docs: ${BOLD}https://github.com/bhartiyaanshul/quell/tree/main/docs${RESET}"
printf "\n${GREEN}${BOLD}✓ Quell is installed.${RESET}\n\n"

if [ "$ASSUME_YES" != "1" ] && command -v quell >/dev/null 2>&1; then
    if confirm "Run 'quell init' now in the current directory?" "n"; then
        exec quell init
    fi
fi
