"""Tests for ``quell notifier <verb>`` (Phase 3.4).

Coverage targets the v0.3.0 CLI contract for the ``notifier`` resource:
``list`` / ``test`` / ``add`` / ``remove`` plus the deprecated
``quell test-notifier`` alias. Network calls in ``test`` are mocked
with ``httpx.MockTransport`` so the tests don't hit real webhooks.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text("repo_path = '.'\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def project_with_slack(tmp_path: Path) -> Path:
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text(
        "\n".join(
            [
                "repo_path = '.'",
                "",
                "[[notifiers]]",
                "type = 'slack'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def patch_keyring(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Stub keyring.get_password so test_handler thinks the secret exists."""
    store: dict[str, str] = {
        "quell/slack:webhook_url": "https://hooks.slack.com/services/abc",
    }

    def fake_get(service: str, username: str) -> str | None:
        return store.get(f"{service}:{username}")

    monkeypatch.setattr("keyring.get_password", fake_get)
    return store


@pytest.fixture
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    """Route every AsyncClient call through a 200-OK mock transport."""
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def make_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    yield captured


# ---------------------------------------------------------------------------
# notifier list
# ---------------------------------------------------------------------------


def test_list_empty(empty_project: Path) -> None:
    result = runner.invoke(app, ["notifier", "list", "--path", str(empty_project)])
    assert result.exit_code == 0, result.stderr
    assert "No notifiers configured." in result.stdout


def test_list_renders_configured(project_with_slack: Path) -> None:
    result = runner.invoke(app, ["notifier", "list", "--path", str(project_with_slack)])
    assert result.exit_code == 0, result.stderr
    assert "slack" in result.stdout
    assert "TYPE" in result.stdout


def test_list_json_envelope(project_with_slack: Path) -> None:
    result = runner.invoke(
        app, ["notifier", "list", "--path", str(project_with_slack), "--json"]
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "notifier.list"
    types = [n["type"] for n in payload["data"]["notifiers"]]
    assert "slack" in types


# ---------------------------------------------------------------------------
# notifier add / remove
# ---------------------------------------------------------------------------


def test_add_writes_to_config(empty_project: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "add", "slack", "--path", str(empty_project), "--yes"],
    )
    assert result.exit_code == 0, result.stderr
    contents = (empty_project / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert "slack" in contents
    assert "[[notifiers]]" in contents


def test_add_dry_run_does_not_write(empty_project: Path) -> None:
    before = (empty_project / ".quell" / "config.toml").read_text(encoding="utf-8")
    result = runner.invoke(
        app,
        ["notifier", "add", "discord", "--path", str(empty_project), "--dry-run"],
    )
    assert result.exit_code == 0, result.stderr
    after = (empty_project / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert before == after
    assert "(dry-run)" in result.stdout


def test_add_telegram_requires_chat_id(empty_project: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "add", "telegram", "--path", str(empty_project), "--yes"],
    )
    assert result.exit_code == 2, result.stderr
    assert "chat-id" in result.stderr


def test_add_telegram_with_chat_id(empty_project: Path) -> None:
    result = runner.invoke(
        app,
        [
            "notifier",
            "add",
            "telegram",
            "--chat-id",
            "12345",
            "--path",
            str(empty_project),
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.stderr
    contents = (empty_project / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert "telegram" in contents
    assert "12345" in contents


def test_add_existing_returns_already_exists(project_with_slack: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "add", "slack", "--path", str(project_with_slack), "--yes"],
    )
    assert result.exit_code == 8, result.stderr
    assert "already" in result.stderr.lower()


def test_add_unknown_channel_errors(empty_project: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "add", "carrierpigeon", "--path", str(empty_project), "--yes"],
    )
    assert result.exit_code == 2, result.stderr


def test_remove_idempotent_when_missing(empty_project: Path) -> None:
    result = runner.invoke(
        app,
        [
            "notifier",
            "remove",
            "slack",
            "--path",
            str(empty_project),
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data"]["removed"] is False


def test_remove_drops_entry(project_with_slack: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "remove", "slack", "--path", str(project_with_slack), "--yes"],
    )
    assert result.exit_code == 0, result.stderr
    contents = (project_with_slack / ".quell" / "config.toml").read_text(
        encoding="utf-8"
    )
    assert "slack" not in contents


# ---------------------------------------------------------------------------
# notifier test
# ---------------------------------------------------------------------------


def test_test_sends_to_configured_channel(
    project_with_slack: Path,
    patch_keyring: dict[str, str],
    patch_httpx: dict[str, Any],
) -> None:
    result = runner.invoke(
        app, ["notifier", "test", "slack", "--path", str(project_with_slack)]
    )
    assert result.exit_code == 0, result.stderr
    assert "Sent." in result.stdout
    assert patch_httpx["url"] == "https://hooks.slack.com/services/abc"


def test_test_missing_notifier_exits_not_found(empty_project: Path) -> None:
    result = runner.invoke(
        app, ["notifier", "test", "slack", "--path", str(empty_project)]
    )
    assert result.exit_code == 7, result.stderr


def test_test_unknown_channel_errors(project_with_slack: Path) -> None:
    result = runner.invoke(
        app,
        ["notifier", "test", "carrierpigeon", "--path", str(project_with_slack)],
    )
    assert result.exit_code == 2, result.stderr


# ---------------------------------------------------------------------------
# Deprecated alias: quell test-notifier
# ---------------------------------------------------------------------------


def test_test_notifier_alias_warns_and_works(
    project_with_slack: Path,
    patch_keyring: dict[str, str],
    patch_httpx: dict[str, Any],
) -> None:
    result = runner.invoke(
        app, ["test-notifier", "slack", "--path", str(project_with_slack)]
    )
    assert result.exit_code == 0, result.stderr
    assert "[deprecation]" in result.stderr
    assert "quell notifier test" in result.stderr
