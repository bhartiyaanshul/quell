"""Tests for quell.monitors — RawEvent, factory, and LocalFileMonitor."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest

from quell.config.schema import (
    HttpPollMonitorConfig,
    LocalFileMonitorConfig,
    SentryMonitorConfig,
    VercelMonitorConfig,
)
from quell.monitors.base import RawEvent, create_monitor
from quell.monitors.http_poll import HttpPollMonitor
from quell.monitors.local_file import LocalFileMonitor
from quell.monitors.sentry import SentryMonitor
from quell.monitors.vercel import VercelMonitor
from quell.utils.errors import MonitorError

# ---------------------------------------------------------------------------
# RawEvent
# ---------------------------------------------------------------------------


def test_raw_event_defaults() -> None:
    """RawEvent has sensible defaults for optional fields."""
    ev = RawEvent(source="test", timestamp=datetime.now(UTC), raw="hello")
    assert ev.severity == "info"
    assert ev.metadata == {}


# ---------------------------------------------------------------------------
# Factory — create_monitor
# ---------------------------------------------------------------------------


def test_create_monitor_local_file() -> None:
    config = LocalFileMonitorConfig(type="local-file", path="/fake/path.log")
    assert isinstance(create_monitor(config), LocalFileMonitor)


def test_create_monitor_http_poll() -> None:
    config = HttpPollMonitorConfig(type="http-poll", url="http://example.com")
    assert isinstance(create_monitor(config), HttpPollMonitor)


def test_create_monitor_vercel() -> None:
    config = VercelMonitorConfig(type="vercel", project_id="prj_test")
    assert isinstance(create_monitor(config), VercelMonitor)


def test_create_monitor_sentry() -> None:
    config = SentryMonitorConfig(
        type="sentry", project_slug="proj", organization_slug="org"
    )
    assert isinstance(create_monitor(config), SentryMonitor)


# ---------------------------------------------------------------------------
# LocalFileMonitor — _parse_line (sync, unit tests)
# ---------------------------------------------------------------------------


def test_parse_line_json_error_level() -> None:
    """JSON line with level=error maps to severity='error'."""
    config = LocalFileMonitorConfig(type="local-file", path="fake.log")
    monitor = LocalFileMonitor(config)
    ev = monitor._parse_line('{"level": "error", "message": "boom"}')
    assert ev is not None
    assert ev.severity == "error"


def test_parse_line_json_severity_field() -> None:
    """JSON line may use 'severity' instead of 'level'."""
    config = LocalFileMonitorConfig(type="local-file", path="fake.log")
    monitor = LocalFileMonitor(config)
    ev = monitor._parse_line('{"severity": "warning", "msg": "watch out"}')
    assert ev is not None
    assert ev.severity == "warning"


def test_parse_line_json_fallback_on_bad_json() -> None:
    """Non-JSON lines are wrapped as info events instead of being dropped."""
    config = LocalFileMonitorConfig(type="local-file", path="fake.log")
    monitor = LocalFileMonitor(config)
    ev = monitor._parse_line("plain text log line")
    assert ev is not None
    assert ev.severity == "info"
    assert ev.raw == "plain text log line"


def test_parse_line_regex_match() -> None:
    """Regex format yields an event with named capture groups in metadata."""
    config = LocalFileMonitorConfig(
        type="local-file",
        path="fake.log",
        format="regex",
        pattern=r"ERROR: (?P<msg>.+)",
    )
    monitor = LocalFileMonitor(config)
    ev = monitor._parse_line("ERROR: disk full")
    assert ev is not None
    assert ev.metadata["groups"]["msg"] == "disk full"
    assert ev.severity == "error"


def test_parse_line_regex_no_match_returns_none() -> None:
    """Non-matching lines return None so the stream skips them."""
    config = LocalFileMonitorConfig(
        type="local-file",
        path="fake.log",
        format="regex",
        pattern=r"CRITICAL: .+",
    )
    monitor = LocalFileMonitor(config)
    assert monitor._parse_line("INFO: all good") is None


# ---------------------------------------------------------------------------
# LocalFileMonitor — streaming (async integration tests)
# ---------------------------------------------------------------------------


async def test_local_file_not_found_raises() -> None:
    """Streaming from a nonexistent file raises MonitorError."""
    config = LocalFileMonitorConfig(
        type="local-file", path="/definitely/does/not/exist/quell_test.log"
    )
    monitor = LocalFileMonitor(config)
    with pytest.raises(MonitorError, match="not found"):
        await monitor.events().__anext__()


async def test_local_file_yields_new_line(tmp_path: Path) -> None:
    """New lines appended to the file are yielded as RawEvent objects."""
    log_file = tmp_path / "app.log"
    log_file.write_text("", encoding="utf-8")

    config = LocalFileMonitorConfig(type="local-file", path=str(log_file))
    monitor = LocalFileMonitor(config)

    collected: list[RawEvent] = []

    async def _collect() -> None:
        async for ev in monitor.events():
            collected.append(ev)
            break

    async def _write() -> None:
        await asyncio.sleep(0.05)
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write('{"level": "warning", "message": "spike"}\n')

    await asyncio.gather(asyncio.wait_for(_collect(), timeout=3.0), _write())

    assert len(collected) == 1
    assert collected[0].severity == "warning"
    assert collected[0].source == "local-file"
