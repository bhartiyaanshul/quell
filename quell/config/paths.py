"""XDG-compliant path resolution for Quell config and data directories.

Follows XDG Base Directory Specification on Linux/macOS and uses APPDATA /
LOCALAPPDATA on Windows. Falls back to `~/.config/quell` and
`~/.local/share/quell` if environment variables are not set.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Name used in all path components
_APP = "quell"


def config_dir() -> Path:
    """Return the user-level global config directory.

    - Linux/macOS: ``$XDG_CONFIG_HOME/quell`` (default ``~/.config/quell``)
    - Windows:     ``%APPDATA%\\quell``
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / _APP


def data_dir() -> Path:
    """Return the user-level data directory (SQLite DB, run logs).

    - Linux/macOS: ``$XDG_DATA_HOME/quell`` (default ``~/.local/share/quell``)
    - Windows:     ``%LOCALAPPDATA%\\quell``
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        xdg = os.environ.get("XDG_DATA_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / _APP


def global_config_file() -> Path:
    """Return the path to the global ``config.toml``."""
    return config_dir() / "config.toml"


def local_config_file(start: Path | None = None) -> Path:
    """Return the path to the repo-local ``.quell/config.toml``.

    Args:
        start: Directory to search from (defaults to ``Path.cwd()``).
    """
    return (start or Path.cwd()) / ".quell" / "config.toml"


def db_file() -> Path:
    """Return the path to the SQLite incident database."""
    return data_dir() / "incidents.db"


def ensure_dirs() -> None:
    """Create config and data directories if they do not exist."""
    config_dir().mkdir(parents=True, exist_ok=True)
    data_dir().mkdir(parents=True, exist_ok=True)


__all__ = [
    "config_dir",
    "data_dir",
    "global_config_file",
    "local_config_file",
    "db_file",
    "ensure_dirs",
]
