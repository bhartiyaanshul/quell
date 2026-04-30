"""Tests for ``quell.utils.timeparse.parse_since``.

Verifies the small set of forms the CLI ``--since`` flag promises:
``today`` / ``yesterday``, ``"<N> <unit> ago"``, and ISO 8601. Also
covers the failure path — an unparseable value must raise
``UsageError`` so the CLI can render a friendly fix message.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quell.interface.errors import UsageError
from quell.utils.timeparse import parse_since

NOW = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)


def test_today_returns_start_of_today() -> None:
    result = parse_since("today", now=NOW)
    assert result == datetime(2026, 4, 30, 0, 0, 0, tzinfo=UTC)


def test_yesterday_returns_start_of_yesterday() -> None:
    result = parse_since("yesterday", now=NOW)
    assert result == datetime(2026, 4, 29, 0, 0, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("value", "expected_delta"),
    [
        ("5m ago", timedelta(minutes=5)),
        ("1 minute ago", timedelta(minutes=1)),
        ("30 minutes ago", timedelta(minutes=30)),
        ("2h ago", timedelta(hours=2)),
        ("1 hour ago", timedelta(hours=1)),
        ("3 hours ago", timedelta(hours=3)),
        ("1d ago", timedelta(days=1)),
        ("7 days ago", timedelta(days=7)),
        ("1 week ago", timedelta(weeks=1)),
        ("2 weeks ago", timedelta(weeks=2)),
    ],
)
def test_relative_phrases_subtract_from_now(
    value: str, expected_delta: timedelta
) -> None:
    result = parse_since(value, now=NOW)
    assert result == NOW - expected_delta


def test_iso_date_treated_as_utc_midnight() -> None:
    result = parse_since("2026-04-29", now=NOW)
    assert result == datetime(2026, 4, 29, 0, 0, 0, tzinfo=UTC)


def test_iso_datetime_naive_treated_as_utc() -> None:
    result = parse_since("2026-04-29T08:00:00", now=NOW)
    assert result == datetime(2026, 4, 29, 8, 0, 0, tzinfo=UTC)


def test_iso_datetime_with_offset_normalized_to_utc() -> None:
    # +05:00 offset → 08:00+05 == 03:00 UTC.
    result = parse_since("2026-04-29T08:00:00+05:00", now=NOW)
    assert result == datetime(2026, 4, 29, 3, 0, 0, tzinfo=UTC)


def test_unknown_unit_raises_usage_error() -> None:
    with pytest.raises(UsageError) as info:
        parse_since("5 fortnights ago", now=NOW)
    assert "fortnight" in str(info.value).lower()
    assert info.value.fix is not None


def test_unparseable_value_raises_usage_error() -> None:
    with pytest.raises(UsageError) as info:
        parse_since("nonsense", now=NOW)
    assert info.value.fix is not None
    assert "today" in info.value.fix.lower()


def test_whitespace_is_tolerated() -> None:
    result = parse_since("  1 hour ago  ", now=NOW)
    assert result == NOW - timedelta(hours=1)


def test_case_insensitive_keywords() -> None:
    assert parse_since("TODAY", now=NOW) == datetime(2026, 4, 30, 0, 0, 0, tzinfo=UTC)
    assert parse_since("Yesterday", now=NOW) == datetime(
        2026, 4, 29, 0, 0, 0, tzinfo=UTC
    )
