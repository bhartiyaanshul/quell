"""Tests for quell.interface.format."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quell.interface.format import format_cost_usd, relative_time, truncate_id

# ---------------------------------------------------------------------------
# relative_time
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("delta_seconds", "expected"),
    [
        (5, "just now"),
        (59, "just now"),
        (60, "1m ago"),
        (180, "3m ago"),
        (3600, "1h ago"),
        (3600 * 2 + 30, "2h ago"),
        (3600 * 23, "23h ago"),
        (3600 * 25, "yesterday"),  # 25 hours
        (86400 * 1.5, "yesterday"),
        (86400 * 3, "3d ago"),
        (86400 * 29, "29d ago"),
    ],
)
def test_relative_time_buckets(delta_seconds: float, expected: str) -> None:
    now = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)
    when = now - timedelta(seconds=delta_seconds)
    assert relative_time(when, now=now) == expected


def test_relative_time_far_past_returns_iso_date() -> None:
    now = datetime(2026, 4, 30, tzinfo=UTC)
    when = now - timedelta(days=60)
    assert relative_time(when, now=now) == when.strftime("%Y-%m-%d")


def test_relative_time_naive_datetime_normalized_to_utc() -> None:
    now = datetime(2026, 4, 30, 12, 0, 0, tzinfo=UTC)
    when_naive = datetime(2026, 4, 30, 11, 30, 0)  # no tzinfo
    assert relative_time(when_naive, now=now) == "30m ago"


def test_relative_time_future_timestamp_returns_iso() -> None:
    """Clock-skewed future timestamps degrade gracefully, don't crash."""
    now = datetime(2026, 4, 30, tzinfo=UTC)
    when = now + timedelta(hours=1)
    assert relative_time(when, now=now) == when.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# truncate_id
# ---------------------------------------------------------------------------


def test_truncate_id_truncates_long_value() -> None:
    assert truncate_id("inc_a1b2c3d4e5f6", max_length=10) == "inc_a1b2c…"


def test_truncate_id_passes_short_value_through() -> None:
    assert truncate_id("inc_abc", max_length=12) == "inc_abc"


def test_truncate_id_at_exact_length() -> None:
    assert truncate_id("abcdefghijkl", max_length=12) == "abcdefghijkl"


def test_truncate_id_max_length_one() -> None:
    """Edge case: max_length=1 just returns the ellipsis."""
    assert truncate_id("anything", max_length=1) == "…"


# ---------------------------------------------------------------------------
# format_cost_usd
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (0.0034, "$0.0034"),
        (0.001, "$0.0010"),
        (0.123, "$0.123"),
        (0.5, "$0.500"),
        (1.0, "$1.00"),
        (1.45, "$1.45"),
        (123.4, "$123.40"),
        (1000.5, "$1000.50"),
    ],
)
def test_format_cost_usd(amount: float, expected: str) -> None:
    assert format_cost_usd(amount) == expected
