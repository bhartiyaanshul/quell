"""Tests for quell.notifiers — Slack, Discord, Telegram, + factory."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from quell.config.schema import (
    DiscordNotifierConfig,
    SlackNotifierConfig,
    TelegramNotifierConfig,
)
from quell.memory.models import Incident
from quell.notifiers import create_notifier
from quell.notifiers.discord import DiscordNotifier
from quell.notifiers.formatting import build_summary
from quell.notifiers.slack import SlackNotifier
from quell.notifiers.telegram import TelegramNotifier
from quell.utils.errors import NotifierError


def _incident(**overrides: object) -> Incident:
    now = datetime.now(UTC)
    defaults: dict[str, object] = {
        "id": "inc_test",
        "signature": "abcd1234abcd1234",
        "severity": "high",
        "status": "resolved",
        "first_seen": now,
        "last_seen": now,
        "occurrence_count": 3,
        "root_cause": "null deref on order.user",
        "fix_pr_url": "https://example.com/pr/1",
        "postmortem": None,
        "agent_graph_id": None,
    }
    defaults.update(overrides)
    return Incident(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Shared formatter
# ---------------------------------------------------------------------------


def test_build_summary_truncates_long_root_cause() -> None:
    long = "x" * 5000
    summary = build_summary(_incident(root_cause=long))
    assert len(summary.root_cause) < 650
    assert summary.root_cause.endswith("\u2026")  # ellipsis


def test_build_summary_defaults_when_root_cause_missing() -> None:
    summary = build_summary(_incident(root_cause=None))
    assert "without a stated root cause" in summary.root_cause


def test_build_summary_severity_colour_known() -> None:
    summary = build_summary(_incident(severity="critical"))
    assert summary.severity_color == "#dc2626"


def test_build_summary_severity_colour_unknown_falls_back() -> None:
    summary = build_summary(_incident(severity="weird"))
    assert summary.severity_color.startswith("#")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def test_create_notifier_slack() -> None:
    cfg = SlackNotifierConfig(type="slack", webhook_url="https://hooks.slack.com/x")
    n = create_notifier(cfg)
    assert isinstance(n, SlackNotifier)


def test_create_notifier_discord() -> None:
    cfg = DiscordNotifierConfig(type="discord", webhook_url="https://discord/x")
    n = create_notifier(cfg)
    assert isinstance(n, DiscordNotifier)


def test_create_notifier_telegram() -> None:
    cfg = TelegramNotifierConfig(type="telegram", chat_id="-1001", bot_token="123:abc")
    n = create_notifier(cfg)
    assert isinstance(n, TelegramNotifier)


# ---------------------------------------------------------------------------
# Config validation — missing webhook / token
# ---------------------------------------------------------------------------


def test_slack_notifier_requires_webhook_url() -> None:
    cfg = SlackNotifierConfig(type="slack", webhook_url="")
    with pytest.raises(NotifierError, match="webhook_url"):
        SlackNotifier(cfg)


def test_discord_notifier_requires_webhook_url() -> None:
    cfg = DiscordNotifierConfig(type="discord", webhook_url="")
    with pytest.raises(NotifierError, match="webhook_url"):
        DiscordNotifier(cfg)


def test_telegram_notifier_requires_bot_token() -> None:
    cfg = TelegramNotifierConfig(type="telegram", chat_id="-1001", bot_token="")
    with pytest.raises(NotifierError, match="bot_token"):
        TelegramNotifier(cfg)


def test_telegram_notifier_requires_chat_id() -> None:
    cfg = TelegramNotifierConfig(type="telegram", chat_id="", bot_token="123:abc")
    with pytest.raises(NotifierError, match="chat_id"):
        TelegramNotifier(cfg)


# ---------------------------------------------------------------------------
# Payload shape — Slack
# ---------------------------------------------------------------------------


def test_slack_payload_contains_blocks_and_fields() -> None:
    payload = SlackNotifier._build_payload(_incident())
    assert payload["text"].startswith("Incident inc_test")
    assert payload["blocks"][0]["type"] == "header"
    assert any(
        b.get("fields") and any("Severity" in f["text"] for f in b["fields"])
        for b in payload["blocks"]
    )
    # PR link appears when present
    rendered = repr(payload)
    assert "example.com/pr/1" in rendered


def test_slack_payload_omits_pr_link_when_absent() -> None:
    payload = SlackNotifier._build_payload(_incident(fix_pr_url=None))
    assert "example.com/pr/1" not in repr(payload)


# ---------------------------------------------------------------------------
# Payload shape — Discord
# ---------------------------------------------------------------------------


def test_discord_payload_embeds_use_decimal_colour() -> None:
    payload = DiscordNotifier._build_payload(_incident(severity="high"))
    embed = payload["embeds"][0]
    assert embed["color"] == int("fb923c", 16)
    assert "Root cause" in embed["description"]


# ---------------------------------------------------------------------------
# Payload shape — Telegram
# ---------------------------------------------------------------------------


def test_telegram_text_escapes_markdown_v2_specials() -> None:
    text = TelegramNotifier._build_text(_incident(severity="high"))
    # Incident ID contains an underscore which MUST be escaped.
    assert "inc\\_test" in text
    assert "\\." in text  # period in root cause or label gets escaped


# ---------------------------------------------------------------------------
# HTTP dispatch — mocked with httpx.MockTransport
# ---------------------------------------------------------------------------


@pytest.fixture
def _patch_httpx(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    """Route every AsyncClient call through a MockTransport capturing payloads."""
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["body"] = request.content.decode("utf-8")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def make_client(*args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    yield captured


async def test_slack_notify_posts_to_webhook(_patch_httpx) -> None:  # type: ignore[no-untyped-def]
    cfg = SlackNotifierConfig(
        type="slack", webhook_url="https://hooks.slack.com/services/abc"
    )
    await SlackNotifier(cfg).notify(_incident())
    assert _patch_httpx["method"] == "POST"
    assert "hooks.slack.com" in _patch_httpx["url"]  # type: ignore[operator]
    assert "inc_test" in _patch_httpx["body"]  # type: ignore[operator]


async def test_discord_notify_posts_to_webhook(_patch_httpx) -> None:  # type: ignore[no-untyped-def]
    cfg = DiscordNotifierConfig(
        type="discord", webhook_url="https://discord.com/api/webhooks/1/abc"
    )
    await DiscordNotifier(cfg).notify(_incident())
    assert _patch_httpx["method"] == "POST"
    assert "discord.com" in _patch_httpx["url"]  # type: ignore[operator]


async def test_telegram_notify_calls_sendmessage(_patch_httpx) -> None:  # type: ignore[no-untyped-def]
    cfg = TelegramNotifierConfig(type="telegram", chat_id="-1001", bot_token="42:abc")
    await TelegramNotifier(cfg).notify(_incident())
    assert "api.telegram.org/bot42:abc/sendMessage" in _patch_httpx["url"]  # type: ignore[operator]
    assert "chat_id" in _patch_httpx["body"]  # type: ignore[operator]


async def test_notify_swallows_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """A flaky channel should log+skip, not raise."""

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure")

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def make_client(*args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    cfg = SlackNotifierConfig(type="slack", webhook_url="https://hooks.slack.com/x")
    # Must not raise.
    await SlackNotifier(cfg).notify(_incident())


async def test_notify_logs_on_http_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 4xx/5xx response should log but not raise."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    transport = httpx.MockTransport(handler)
    orig = httpx.AsyncClient

    def make_client(*args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["transport"] = transport
        return orig(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    cfg = SlackNotifierConfig(type="slack", webhook_url="https://hooks.slack.com/x")
    await SlackNotifier(cfg).notify(_incident())  # must not raise
