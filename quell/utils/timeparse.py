"""Lightweight ``--since`` parser for CLI list commands.

Accepts the small set of forms the spec calls out in §3.3 — relative
phrases (``"1 hour ago"``, ``"5m ago"``), the words ``today`` /
``yesterday``, and ISO 8601 dates / datetimes. Always returns a UTC
datetime so callers can compare against database timestamps without
worrying about the local timezone.

Out-of-scope on purpose: full natural-language parsing (``"last
Tuesday"``), absolute times in the user's local timezone, durations
without ``ago``. Adding any of those is a deliberate design decision,
not a one-line tweak — they'd need a real parsing library.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from quell.interface.errors import UsageError

_UNIT_SECONDS: dict[str, int] = {
    "s": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hr": 3600,
    "hour": 3600,
    "hours": 3600,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "w": 86400 * 7,
    "week": 86400 * 7,
    "weeks": 86400 * 7,
}

_RELATIVE_RE = re.compile(
    r"^\s*(?P<n>\d+)\s*(?P<unit>[a-zA-Z]+)\s+ago\s*$",
    re.IGNORECASE,
)


def parse_since(value: str, *, now: datetime | None = None) -> datetime:
    """Parse a ``--since`` argument into a UTC datetime.

    Accepts:
      * ``"today"`` — start of today (UTC).
      * ``"yesterday"`` — start of yesterday (UTC).
      * Relative ``"<N> <unit> ago"`` where unit is s/m/h/d/w (with
        optional plurals or shorthands). Examples: ``"5m ago"``,
        ``"1 hour ago"``, ``"2 weeks ago"``.
      * ISO 8601 date (``"2026-04-29"``) or datetime
        (``"2026-04-29T12:00:00"``). Naive ISO datetimes are treated as
        UTC; tz-aware ones are converted to UTC.

    Raises:
        UsageError: When *value* doesn't match any supported form. The
        attached fix message lists the valid forms so the user can
        recover without checking the docs.
    """
    now = now or datetime.now(UTC)
    candidate = value.strip()

    if candidate.lower() == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if candidate.lower() == "yesterday":
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight - timedelta(days=1)

    match = _RELATIVE_RE.match(candidate)
    if match:
        amount = int(match.group("n"))
        unit = match.group("unit").lower()
        seconds = _UNIT_SECONDS.get(unit)
        if seconds is None:
            raise UsageError(
                f"--since: unknown time unit {unit!r} in {value!r}.",
                fix=(
                    "Use s, m, h, d, or w (e.g. '5m ago', '2 hours ago', '1 week ago')."
                ),
            )
        return now - timedelta(seconds=amount * seconds)

    # ISO date or datetime — fromisoformat handles both since Python 3.11.
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise UsageError(
            f"--since: could not parse {value!r}.",
            fix=(
                "Use one of: 'today', 'yesterday', '<N> <unit> ago' "
                "(e.g. '5m ago', '1 hour ago'), or an ISO date "
                "('2026-04-29' or '2026-04-29T12:00:00')."
            ),
        ) from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


__all__ = ["parse_since"]
