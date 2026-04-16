"""Tests for HTTP-based monitors: HttpPollMonitor, VercelMonitor, SentryMonitor."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from quell.config.schema import (
    HttpPollMonitorConfig,
    SentryMonitorConfig,
    VercelMonitorConfig,
)
from quell.monitors.http_poll import HttpPollMonitor
from quell.monitors.sentry import SentryMonitor
from quell.monitors.vercel import VercelMonitor
from quell.utils.errors import MonitorError

# ---------------------------------------------------------------------------
# Sentinel — used to break out of infinite monitor loops in tests.
# We cannot use StopAsyncIteration because Python 3.7+ converts it to
# RuntimeError when it propagates out of an async generator.
# ---------------------------------------------------------------------------


class _HaltError(Exception):
    """Private sentinel raised by mocked sleeps to terminate a monitor loop."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(mock_cls: MagicMock, response: MagicMock) -> None:
    """Wire *mock_cls* (patched AsyncClient) to return *response* from .get()."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    mock_cls.return_value = client


def _make_client_error(mock_cls: MagicMock, exc: Exception) -> None:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=exc)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    mock_cls.return_value = client


def _resp(status: int, body: object = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.text = str(body or "")
    r.json = MagicMock(return_value=body or {})
    return r


# ---------------------------------------------------------------------------
# HttpPollMonitor
# ---------------------------------------------------------------------------


async def test_http_poll_2xx_yields_no_event() -> None:
    """200 OK with expected_status=200 should yield nothing before the sleep."""
    config = HttpPollMonitorConfig(
        type="http-poll", url="http://example.com/health", interval_seconds=9999
    )
    monitor = HttpPollMonitor(config)
    events = []

    with (
        patch("quell.monitors.http_poll.httpx.AsyncClient") as mock_cls,
        patch(
            "quell.monitors.http_poll.asyncio.sleep",
            new=AsyncMock(side_effect=_HaltError),
        ),
    ):
        _make_client(mock_cls, _resp(200))
        try:
            async for ev in monitor.events():
                events.append(ev)
        except _HaltError:
            pass

    assert events == []


async def test_http_poll_non_2xx_yields_event() -> None:
    """A 503 response yields an error event."""
    config = HttpPollMonitorConfig(
        type="http-poll", url="http://example.com/health", interval_seconds=9999
    )
    monitor = HttpPollMonitor(config)

    with patch("quell.monitors.http_poll.httpx.AsyncClient") as mock_cls:
        _make_client(mock_cls, _resp(503, "Service Unavailable"))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "503" in ev.raw


async def test_http_poll_timeout_yields_event() -> None:
    """A TimeoutException yields an error event mentioning timeout."""
    config = HttpPollMonitorConfig(
        type="http-poll", url="http://example.com", interval_seconds=9999
    )
    monitor = HttpPollMonitor(config)

    with patch("quell.monitors.http_poll.httpx.AsyncClient") as mock_cls:
        _make_client_error(mock_cls, httpx.TimeoutException("timed out"))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "imeout" in ev.raw  # matches "Timeout" or "timeout"


async def test_http_poll_request_error_yields_event() -> None:
    """A RequestError yields an error event."""
    config = HttpPollMonitorConfig(
        type="http-poll", url="http://example.com", interval_seconds=9999
    )
    monitor = HttpPollMonitor(config)

    with patch("quell.monitors.http_poll.httpx.AsyncClient") as mock_cls:
        _make_client_error(mock_cls, httpx.RequestError("connection refused"))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "connection refused" in ev.raw


# ---------------------------------------------------------------------------
# VercelMonitor
# ---------------------------------------------------------------------------


async def test_vercel_no_token_raises() -> None:
    """Missing Vercel token raises MonitorError immediately."""
    config = VercelMonitorConfig(type="vercel", project_id="prj_test")
    monitor = VercelMonitor(config)

    with (
        patch("quell.monitors.vercel.get_secret", return_value=None),
        pytest.raises(MonitorError, match="Vercel API token"),
    ):
        await monitor.events().__anext__()


async def test_vercel_error_deployment_yields_event() -> None:
    """An ERROR-state deployment in the API response yields an event."""
    config = VercelMonitorConfig(
        type="vercel", project_id="prj_abc", interval_seconds=9999
    )
    monitor = VercelMonitor(config)
    payload = {"deployments": [{"uid": "dep_001", "state": "ERROR", "name": "app"}]}

    with (
        patch("quell.monitors.vercel.get_secret", return_value="tok"),
        patch("quell.monitors.vercel.httpx.AsyncClient") as mock_cls,
    ):
        _make_client(mock_cls, _resp(200, payload))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "dep_001" in ev.raw


async def test_vercel_ready_deployment_yields_no_event() -> None:
    """A READY deployment yields nothing before the sleep fires."""
    config = VercelMonitorConfig(
        type="vercel", project_id="prj_abc", interval_seconds=9999
    )
    monitor = VercelMonitor(config)
    payload = {"deployments": [{"uid": "dep_002", "state": "READY", "name": "app"}]}
    events = []

    with (
        patch("quell.monitors.vercel.get_secret", return_value="tok"),
        patch("quell.monitors.vercel.httpx.AsyncClient") as mock_cls,
        patch(
            "quell.monitors.vercel.asyncio.sleep",
            new=AsyncMock(side_effect=_HaltError),
        ),
    ):
        _make_client(mock_cls, _resp(200, payload))
        try:
            async for ev in monitor.events():
                events.append(ev)
        except _HaltError:
            pass

    assert events == []


async def test_vercel_api_error_yields_event() -> None:
    """A non-200 API response yields an error event."""
    config = VercelMonitorConfig(
        type="vercel", project_id="prj_abc", interval_seconds=9999
    )
    monitor = VercelMonitor(config)

    with (
        patch("quell.monitors.vercel.get_secret", return_value="tok"),
        patch("quell.monitors.vercel.httpx.AsyncClient") as mock_cls,
    ):
        _make_client(mock_cls, _resp(401))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "401" in ev.raw


# ---------------------------------------------------------------------------
# SentryMonitor
# ---------------------------------------------------------------------------


async def test_sentry_no_token_raises() -> None:
    """Missing Sentry token raises MonitorError immediately."""
    config = SentryMonitorConfig(
        type="sentry", project_slug="proj", organization_slug="org"
    )
    monitor = SentryMonitor(config)

    with (
        patch("quell.monitors.sentry.get_secret", return_value=None),
        pytest.raises(MonitorError, match="Sentry auth token"),
    ):
        await monitor.events().__anext__()


async def test_sentry_new_issue_yields_event() -> None:
    """A new Sentry issue yields an event with the issue title."""
    config = SentryMonitorConfig(
        type="sentry",
        project_slug="proj",
        organization_slug="org",
        interval_seconds=9999,
    )
    monitor = SentryMonitor(config)
    issues = [{"id": "111", "title": "NullPointerException", "level": "error"}]

    with (
        patch("quell.monitors.sentry.get_secret", return_value="tok"),
        patch("quell.monitors.sentry.httpx.AsyncClient") as mock_cls,
    ):
        _make_client(mock_cls, _resp(200, issues))
        ev = await monitor.events().__anext__()

    assert "NullPointerException" in ev.raw
    assert ev.severity == "error"


async def test_sentry_seen_issue_not_repeated() -> None:
    """The same issue ID should only be yielded once across multiple polls."""
    config = SentryMonitorConfig(
        type="sentry",
        project_slug="proj",
        organization_slug="org",
        interval_seconds=9999,
    )
    monitor = SentryMonitor(config)
    issues = [{"id": "111", "title": "Same error", "level": "error"}]
    call_count = 0

    async def _get(*args: object, **kwargs: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise _HaltError
        return _resp(200, issues)

    collected = []
    with (
        patch("quell.monitors.sentry.get_secret", return_value="tok"),
        patch("quell.monitors.sentry.httpx.AsyncClient") as mock_cls,
        patch("quell.monitors.sentry.asyncio.sleep", new=AsyncMock(return_value=None)),
    ):
        client = AsyncMock()
        client.get = _get
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = client
        try:
            async for ev in monitor.events():
                collected.append(ev)
        except _HaltError:
            pass

    assert len(collected) == 1  # second poll skips the already-seen ID


async def test_sentry_api_error_yields_event() -> None:
    """A non-200 Sentry API response yields an error event."""
    config = SentryMonitorConfig(
        type="sentry",
        project_slug="proj",
        organization_slug="org",
        interval_seconds=9999,
    )
    monitor = SentryMonitor(config)

    with (
        patch("quell.monitors.sentry.get_secret", return_value="tok"),
        patch("quell.monitors.sentry.httpx.AsyncClient") as mock_cls,
    ):
        _make_client(mock_cls, _resp(403))
        ev = await monitor.events().__anext__()

    assert ev.severity == "error"
    assert "403" in ev.raw
