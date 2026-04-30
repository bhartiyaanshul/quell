"""Tests for quell.interface.wizard — init wizard logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from quell.interface.wizard import (
    _detect_git_remote,
    _detect_project_type,
    _ensure_gitignore,
    _write_config_toml,
)

# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------


def test_detect_project_type_python_poetry(tmp_path: Path) -> None:
    """Detects Python project from pyproject.toml."""
    (tmp_path / "pyproject.toml").touch()
    result = _detect_project_type(tmp_path)
    assert "Python" in result


def test_detect_project_type_nodejs(tmp_path: Path) -> None:
    """Detects Node.js project from package.json."""
    (tmp_path / "package.json").touch()
    result = _detect_project_type(tmp_path)
    assert "Node" in result


def test_detect_project_type_unknown(tmp_path: Path) -> None:
    """Returns 'Unknown' when no known marker exists."""
    assert _detect_project_type(tmp_path) == "Unknown"


def test_detect_git_remote_no_git(tmp_path: Path) -> None:
    """Returns None when directory is not a git repo."""
    result = _detect_git_remote(tmp_path)
    assert result is None


# ---------------------------------------------------------------------------
# .gitignore management
# ---------------------------------------------------------------------------


def test_ensure_gitignore_creates_new(tmp_path: Path) -> None:
    """Creates .gitignore with .quell/ when none exists."""
    _ensure_gitignore(tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert ".quell/" in content


def test_ensure_gitignore_appends_to_existing(tmp_path: Path) -> None:
    """Appends .quell/ to existing .gitignore without duplication."""
    gi = tmp_path / ".gitignore"
    gi.write_text("node_modules/\n", encoding="utf-8")
    _ensure_gitignore(tmp_path)
    content = gi.read_text()
    assert ".quell/" in content
    assert "node_modules/" in content


def test_ensure_gitignore_idempotent(tmp_path: Path) -> None:
    """Does not duplicate .quell/ entry if it already exists."""
    gi = tmp_path / ".gitignore"
    gi.write_text(".quell/\n", encoding="utf-8")
    _ensure_gitignore(tmp_path)
    content = gi.read_text()
    assert content.count(".quell/") == 1


# ---------------------------------------------------------------------------
# Config TOML writing
# ---------------------------------------------------------------------------


def test_write_config_toml_creates_file(tmp_path: Path) -> None:
    """Writes a valid, parseable .quell/config.toml from a data dict."""
    import tomllib

    data = {
        "repo_path": str(tmp_path),
        "llm": {"model": "openai/gpt-4o"},
        "monitors": [{"type": "local-file", "path": "/var/log/app.log"}],
    }
    _write_config_toml(tmp_path, data)
    config_file = tmp_path / ".quell" / "config.toml"
    assert config_file.exists()
    parsed = tomllib.loads(config_file.read_text(encoding="utf-8"))
    assert parsed == data


def test_write_config_toml_creates_quell_dir(tmp_path: Path) -> None:
    """Creates .quell/ directory if it does not exist."""
    _write_config_toml(tmp_path, {"repo_path": "."})
    assert (tmp_path / ".quell").is_dir()


def test_write_config_toml_handles_windows_path(tmp_path: Path) -> None:
    """Regression: backslashes in paths must round-trip through tomllib."""
    import tomllib

    data = {"repo_path": r"C:\Users\anshul", "llm": {"model": "ollama/llama3"}}
    _write_config_toml(tmp_path, data)
    parsed = tomllib.loads(
        (tmp_path / ".quell" / "config.toml").read_text(encoding="utf-8")
    )
    assert parsed["repo_path"] == r"C:\Users\anshul"


# ---------------------------------------------------------------------------
# run_init integration (mocked questionary)
# ---------------------------------------------------------------------------


def test_run_init_writes_config_and_gitignore(tmp_path: Path) -> None:
    """run_init creates config.toml and .gitignore when wizard is answered."""
    answers = iter(
        [
            "local-file",  # monitor type
            str(tmp_path / "app.log"),  # log path
            "none",  # notifier
            "Anthropic (Claude)",  # LLM provider
            "sk-test",  # API key
            "",  # GitHub token (skip)
        ]
    )

    def _mock_ask(self: object) -> str:  # type: ignore[override]
        return next(answers)

    with (
        patch("questionary.select") as mock_select,
        patch("questionary.path") as mock_path,
        patch("questionary.text") as mock_text,
        patch("questionary.password") as mock_password,
        patch("quell.interface.wizard.set_secret"),
    ):
        # Make every .ask() call consume the next answer
        for mock in (mock_select, mock_path, mock_text, mock_password):
            instance = MagicMock()
            instance.ask.side_effect = lambda: next(answers, "")
            mock.return_value = instance

        from quell.interface.wizard import run_init

        run_init(tmp_path)

    assert (tmp_path / ".quell" / "config.toml").exists()
    assert (tmp_path / ".gitignore").exists()
