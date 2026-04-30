"""Tests for ``quell init --yes`` (Phase 3.6 — flag-first init).

Verifies the non-interactive code path produces a valid ``config.toml``
from flags + ``$QUELL_*`` env vars and exits cleanly when required
combinations are missing. Keyring writes are stubbed so the tests
don't touch the host's actual keychain.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


@pytest.fixture(autouse=True)
def stub_keyring(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Stub keyring.set_password so tests don't touch the host keychain."""
    store: dict[str, str] = {}

    def fake_set(service: str, username: str, value: str) -> None:
        store[f"{service}:{username}"] = value

    monkeypatch.setattr("keyring.set_password", fake_set)
    return store


def _read_config(project_dir: Path) -> dict[str, object]:
    config_file = project_dir / ".quell" / "config.toml"
    return tomllib.loads(config_file.read_text(encoding="utf-8"))


def test_yes_with_defaults_writes_minimal_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--yes", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stderr
    cfg = _read_config(tmp_path)
    assert cfg["llm"] == {"model": "anthropic/claude-haiku-4-5"}
    monitors = cfg["monitors"]
    assert isinstance(monitors, list)
    assert monitors[0]["type"] == "local-file"
    assert monitors[0]["path"] == "/var/log/app.log"
    assert "notifiers" not in cfg


def test_yes_with_explicit_flags(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--yes",
            "--path",
            str(tmp_path),
            "--monitor",
            "local-file",
            "--log-path",
            "/tmp/app.log",
            "--llm-provider",
            "openai",
            "--notifier",
            "slack",
        ],
    )
    assert result.exit_code == 0, result.stderr
    cfg = _read_config(tmp_path)
    assert cfg["llm"]["model"] == "openai/gpt-4o"
    assert cfg["monitors"][0]["path"] == "/tmp/app.log"
    assert cfg["notifiers"][0]["type"] == "slack"


def test_yes_telegram_requires_chat_id(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--yes",
            "--path",
            str(tmp_path),
            "--notifier",
            "telegram",
        ],
    )
    assert result.exit_code == 2, result.stderr
    assert "telegram-chat-id" in result.stderr


def test_yes_telegram_with_chat_id(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "init",
            "--yes",
            "--path",
            str(tmp_path),
            "--notifier",
            "telegram",
            "--telegram-chat-id",
            "12345",
        ],
    )
    assert result.exit_code == 0, result.stderr
    cfg = _read_config(tmp_path)
    assert cfg["notifiers"][0]["chat_id"] == "12345"


def test_yes_http_poll_requires_url(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "--yes", "--path", str(tmp_path), "--monitor", "http-poll"],
    )
    assert result.exit_code == 2, result.stderr
    assert "http-url" in result.stderr


def test_yes_unknown_monitor_errors(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "--yes", "--path", str(tmp_path), "--monitor", "smoke-signals"],
    )
    assert result.exit_code == 2, result.stderr


def test_yes_stores_api_key_from_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stub_keyring: dict[str, str],
) -> None:
    monkeypatch.setenv("QUELL_ANTHROPIC_API_KEY", "sk-test-12345")
    result = runner.invoke(app, ["init", "--yes", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stderr
    assert stub_keyring.get("quell/anthropic:api_key") == "sk-test-12345"


def test_yes_warns_when_api_key_env_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("QUELL_ANTHROPIC_API_KEY", raising=False)
    result = runner.invoke(app, ["init", "--yes", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stderr
    assert "QUELL_ANTHROPIC_API_KEY" in result.stdout


def test_yes_writes_gitignore_entry(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--yes", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.stderr
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".quell/" in gitignore
