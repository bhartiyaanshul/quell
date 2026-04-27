"""Terminal renderer for the Phase 22 replay feature.

Takes a list of :class:`AgentRun` + their :class:`Event` rows from
the incident DB and produces a single human-readable timeline
string.  Consumed by ``quell replay <incident_id>``.

The output is intentionally plain text — `rich` Console renders it
with colours on top when piped through ``Console.print``.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from quell.memory.models import AgentRun, Event


def _fmt_time(ts: datetime) -> str:
    """Format as ``HH:MM:SS`` in the local timezone."""
    return ts.astimezone().strftime("%H:%M:%S")


def _fmt_duration(start: datetime, end: datetime | None) -> str:
    if end is None:
        return "in progress"
    secs = int((end - start).total_seconds())
    if secs < 60:
        return f"{secs}s"
    m, s = divmod(secs, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def _fmt_cost(usd: float | None) -> str:
    if usd is None:
        return "—"
    if usd == 0:
        return "$0.0000"
    return f"${usd:.4f}"


def _event_summary(event: Event) -> tuple[str, str, str]:
    """Return ``(tag, subject, detail)`` for a single event row."""
    p: dict[str, Any] = dict(event.payload or {})
    et = event.event_type
    if et == "llm_call":
        model = str(p.get("model", "model"))
        tin = int(p.get("input_tokens") or 0)
        tout = int(p.get("output_tokens") or 0)
        lat = int(p.get("latency_ms") or 0)
        return (
            "llm_call ",
            model,
            f"{tin:>5} in / {tout:>5} out   {lat:>4} ms",
        )
    if et == "tool_call":
        name = str(p.get("tool_name", "?"))
        ok = bool(p.get("ok"))
        lat = int(p.get("latency_ms") or 0)
        status = "ok   " if ok else "error"
        return ("tool_call", name, f"{status}   {lat:>4} ms")
    if et == "error":
        msg = str(p.get("message") or p.get("exc_type") or "error")
        return ("error    ", "-", msg[:120])
    # Fallback / info events.
    return (et.ljust(9), "-", str(p)[:120])


def render_terminal_timeline(
    *,
    incident_id: str,
    runs: Sequence[tuple[AgentRun, Sequence[Event]]],
) -> str:
    """Return a multi-line string summarising every run for *incident_id*."""
    lines: list[str] = []
    plural = "s" if len(runs) != 1 else ""
    heading = f"Incident {incident_id} — replay ({len(runs)} run{plural})"
    lines.append(heading)
    lines.append("=" * len(heading))
    lines.append("")

    if not runs:
        lines.append("(no agent runs recorded yet)")
        return "\n".join(lines)

    total_cost = 0.0
    total_events = 0
    for i, (run, events) in enumerate(runs, start=1):
        run_cost = 0.0
        metrics: dict[str, Any] = {}
        if run.final_result and isinstance(run.final_result, dict):
            raw = run.final_result.get("_metrics", {})
            if isinstance(raw, dict):
                metrics = raw
                run_cost = float(metrics.get("cost_usd") or 0.0)
        total_cost += run_cost
        total_events += len(events)
        lines.append(
            f"Run {i}  {run.name}  "
            f"({_fmt_time(run.started_at)} -> "
            f"{_fmt_time(run.finished_at) if run.finished_at else '…'}, "
            f"{_fmt_duration(run.started_at, run.finished_at)}"
            f"{', ' + _fmt_cost(run_cost) if run_cost else ''})"
        )
        if run.skills:
            lines.append(f"  skills: {', '.join(run.skills)}")
        if not events:
            lines.append("  (no events)")
        for event in events:
            tag, subject, detail = _event_summary(event)
            lines.append(
                f"  {_fmt_time(event.timestamp)}  {tag}  {subject:<26}  {detail}"
            )
        if run.final_result and isinstance(run.final_result, dict):
            summary = run.final_result.get("summary")
            if isinstance(summary, str) and summary:
                lines.append(f"  -> {summary[:200]}")
        lines.append("")

    lines.append(
        f"Total: {total_events} event{'s' if total_events != 1 else ''}, "
        f"{_fmt_cost(total_cost)} spent."
    )
    return "\n".join(lines)


__all__ = ["render_terminal_timeline"]
