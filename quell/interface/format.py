"""Stateless string formatters for the Quell CLI.

These take primitive values and return display strings. They contain
no I/O — pure transforms — so they're trivial to unit-test and reuse
across human and JSON output paths (the JSON path emits raw values;
the human path runs them through these helpers).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def relative_time(when: datetime, *, now: datetime | None = None) -> str:
    """Convert *when* to a human-friendly relative time string.

    Buckets:
      < 60s      → "just now"
      < 60m      → "{N}m ago"
      < 24h      → "{N}h ago"
      < 48h      → "yesterday"
      < 30d      → "{N}d ago"
      otherwise  → ISO date "YYYY-MM-DD"

    Both *when* and *now* are normalized to UTC for the comparison so
    timezone-mismatched inputs don't produce nonsensical output.
    """
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    if now is None:
        now = datetime.now(UTC)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    delta: timedelta = now - when
    seconds = delta.total_seconds()

    if seconds < 0:
        # Future timestamp — rare but possible with clock skew.
        return when.strftime("%Y-%m-%d")
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds / 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds / 3600)}h ago"
    if seconds < 86400 * 2:
        return "yesterday"
    if seconds < 86400 * 30:
        return f"{int(seconds / 86400)}d ago"
    return when.strftime("%Y-%m-%d")


def truncate_id(value: str, *, max_length: int = 12) -> str:
    """Truncate a long identifier with a single-character ellipsis.

    Example: ``inc_a1b2c3d4e5f6`` → ``inc_a1b2c…`` at ``max_length=10``.
    Returns *value* unchanged if it already fits.
    """
    if len(value) <= max_length:
        return value
    if max_length <= 1:
        return "…"
    return value[: max_length - 1] + "…"


def format_cost_usd(amount: float) -> str:
    """Format a USD amount with sensible precision per scale.

    < 1¢       → 4 decimal places (``$0.0034``)
    < $1       → 3 decimal places (``$0.123``)
    otherwise  → 2 decimal places (``$1.45``, ``$123.40``)
    """
    if amount < 0.01:
        return f"${amount:.4f}"
    if amount < 1:
        return f"${amount:.3f}"
    return f"${amount:.2f}"


__all__ = ["format_cost_usd", "relative_time", "truncate_id"]
