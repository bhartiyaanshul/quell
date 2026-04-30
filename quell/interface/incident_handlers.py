"""Async handlers for ``quell incident <verb>``.

Split from ``incident_cmd.py`` so the Typer entry-point file stays
focused on the public flag surface. JSON schemas live in a sibling
module (``incident_schemas``) — both files stay under the 300-line cap.

The Typer commands here build an ``Output`` from universal flags and
``await`` the handler that matches their verb. Deprecated aliases in
``cli.py`` reuse these handlers so behaviour only lives in one place.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import typer

from quell.interface.errors import NotFoundError, handle_cli_error
from quell.interface.format import relative_time
from quell.interface.incident_schemas import (
    IncidentListData,
    IncidentReplayData,
    IncidentRow,
    IncidentStatsData,
    ReplayEvent,
    ReplayRun,
)
from quell.memory.agent_runs import list_runs_for_incident
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.memory.events import list_events_for_run
from quell.memory.incidents import get_incident, list_incidents
from quell.memory.stats import (
    count_incidents,
    mean_time_to_resolve,
    top_signatures,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

    from quell.interface.output import Output
    from quell.memory.models import Incident


async def _open_session() -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = get_engine()
    await create_tables(engine)
    return get_session_factory(engine), engine


def _row_from_incident(incident: Incident) -> IncidentRow:
    return IncidentRow.model_validate(incident, from_attributes=True)


def _exit_with(code: int) -> None:
    if code != 0:
        raise typer.Exit(code=code)


async def list_handler(
    out: Output,
    *,
    limit: int,
    status: str | None,
    severity: str | None,
    since_dt: datetime | None,
) -> None:
    factory, engine = await _open_session()
    try:
        async with factory() as session:
            rows = await list_incidents(
                session,
                status=status,
                severity=severity,
                since=since_dt,
                limit=limit,
            )
            total = await count_incidents(
                session, status=status, severity=severity, since=since_dt
            )
    finally:
        await engine.dispose()

    payload = IncidentListData(
        incidents=[_row_from_incident(r) for r in rows],
        total=total,
        limit=limit,
    )
    out.json("incident.list", payload)
    if out.is_json or out.is_quiet:
        return

    if not rows:
        out.info("No incidents recorded yet.")
        return

    # IDs render at full length; users copy them into ``incident show``
    # and ``incident replay`` so truncation would be hostile to that flow.
    table_rows = [
        [r.id, r.status, r.severity, relative_time(r.last_seen)] for r in rows
    ]
    out.table(table_rows, headers=["ID", "STATUS", "SEV", "LAST SEEN"])
    if total > len(rows):
        out.info(f"Showing {len(rows)} of {total}. Use --limit to see more.")


async def show_handler(out: Output, incident_id: str) -> None:
    factory, engine = await _open_session()
    try:
        async with factory() as session:
            incident = await get_incident(session, incident_id)
    finally:
        await engine.dispose()

    if incident is None:
        _exit_with(
            handle_cli_error(
                NotFoundError(
                    f"No incident with ID {incident_id!r}.",
                    fix="quell incident list   # see existing IDs",
                ),
                out,
            )
        )
        return

    row = _row_from_incident(incident)
    out.json("incident.show", row)
    if out.is_json or out.is_quiet:
        return

    out.header(f"Incident {row.id}")
    pairs: list[tuple[str, str]] = [
        ("signature", row.signature),
        ("severity", row.severity),
        ("status", row.status),
        ("first_seen", row.first_seen.isoformat()),
        ("last_seen", row.last_seen.isoformat()),
        ("occurrence_count", str(row.occurrence_count)),
    ]
    if row.cost_usd:
        pairs.append(("cost_usd", f"${row.cost_usd:.4f}"))
    if row.root_cause:
        pairs.append(("root_cause", row.root_cause))
    if row.fix_pr_url:
        pairs.append(("fix_pr_url", row.fix_pr_url))
    out.key_value(pairs)


async def stats_handler(out: Output) -> None:
    factory, engine = await _open_session()
    try:
        async with factory() as session:
            total = await count_incidents(session)
            by_status = {
                "detected": await count_incidents(session, status="detected"),
                "investigating": await count_incidents(session, status="investigating"),
                "resolved": await count_incidents(session, status="resolved"),
            }
            mttr_seconds = await mean_time_to_resolve(session)
            top = await top_signatures(session, limit=5)
    finally:
        await engine.dispose()

    payload = IncidentStatsData(
        total=total,
        by_status=by_status,
        mttr_seconds=mttr_seconds,
        top_signatures=top,
    )
    out.json("incident.stats", payload)
    if out.is_json or out.is_quiet:
        return

    out.header("Incident statistics")
    pairs: list[tuple[str, str]] = [("total incidents", str(total))]
    pairs += [(status, str(count)) for status, count in by_status.items()]
    if mttr_seconds is not None:
        pairs.append(("MTTR", f"{mttr_seconds / 60:.1f} minutes"))
    out.key_value(pairs)
    if top:
        out.line("")
        out.line("  top signatures:")
        for sig, count in top:
            out.line(f"    {sig}  x{count}")


async def replay_handler(out: Output, incident_id: str) -> None:
    from quell.replay.renderer import render_terminal_timeline

    factory, engine = await _open_session()
    try:
        async with factory() as session:
            incident = await get_incident(session, incident_id)
            if incident is None:
                _exit_with(
                    handle_cli_error(
                        NotFoundError(
                            f"No incident with ID {incident_id!r}.",
                            fix="quell incident list   # see existing IDs",
                        ),
                        out,
                    )
                )
                return
            runs = await list_runs_for_incident(session, incident_id)
            run_payloads: list[ReplayRun] = []
            terminal_runs: list[tuple[object, list[object]]] = []
            for run in runs:
                events = await list_events_for_run(session, run.id)
                run_payloads.append(
                    ReplayRun(
                        id=run.id,
                        name=run.name,
                        status=run.status,
                        started_at=run.started_at,
                        finished_at=run.finished_at,
                        events=[
                            ReplayEvent(
                                type=e.event_type,
                                timestamp=e.timestamp,
                                payload=e.payload,
                            )
                            for e in events
                        ],
                    )
                )
                terminal_runs.append((run, list(events)))
    finally:
        await engine.dispose()

    payload = IncidentReplayData(
        incident=_row_from_incident(incident),
        runs=run_payloads,
    )
    out.json("incident.replay", payload)
    if out.is_json or out.is_quiet:
        return

    rendered = render_terminal_timeline(
        incident_id=incident_id,
        runs=terminal_runs,  # type: ignore[arg-type]
    )
    out.line(rendered)


__all__ = [
    "list_handler",
    "replay_handler",
    "show_handler",
    "stats_handler",
]
