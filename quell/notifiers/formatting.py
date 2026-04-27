"""Shared formatting for notifier channels.

Each notifier renders slightly differently (Slack blocks, Discord
embeds, Telegram Markdown-V2), but the underlying summary is the
same.  Helpers here produce channel-neutral text + structured fields
that each concrete notifier remaps onto its own payload shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from quell.memory.models import Incident

_MAX_ROOT_CAUSE_CHARS = 600


@dataclass(frozen=True)
class IncidentSummary:
    """Channel-neutral view of an incident for notifier payloads."""

    title: str
    """Short headline, e.g. ``"Incident inc_a1b2c3 -- high severity"``."""

    severity_label: str
    """Human-readable severity, e.g. ``"High"``."""

    severity_color: str
    """Hex colour string matching the severity (``"#fb923c"`` etc.)."""

    root_cause: str
    """Root cause excerpt, truncated to ~600 chars."""

    status: str
    """Incident status, e.g. ``"resolved"``."""

    occurrence_count: int
    fix_pr_url: str | None


_SEVERITY_COLORS: dict[str, str] = {
    "critical": "#dc2626",  # red-600
    "high": "#fb923c",  # orange-400
    "medium": "#fcd34d",  # amber-300
    "low": "#a78bfa",  # violet-400
    "info": "#a1a1aa",  # zinc-400
}


def build_summary(incident: Incident) -> IncidentSummary:
    """Project an :class:`Incident` into a channel-neutral summary."""
    root = incident.root_cause or "Investigation completed without a stated root cause."
    if len(root) > _MAX_ROOT_CAUSE_CHARS:
        root = root[: _MAX_ROOT_CAUSE_CHARS - 1].rstrip() + "\u2026"

    headline = root.split(".")[0].split("\n")[0].strip()[:80]

    severity = (incident.severity or "info").lower()
    return IncidentSummary(
        title=f"Incident {incident.id} \u2014 {headline}",
        severity_label=severity.capitalize(),
        severity_color=_SEVERITY_COLORS.get(severity, _SEVERITY_COLORS["info"]),
        root_cause=root,
        status=incident.status,
        occurrence_count=incident.occurrence_count,
        fix_pr_url=incident.fix_pr_url,
    )


__all__ = ["IncidentSummary", "build_summary"]
