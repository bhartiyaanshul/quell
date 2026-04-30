"""CLI helpers for inspecting the incident database.

Backs the Phase 15 commands ``quell history``, ``quell show <id>``, and
``quell stats``. Each helper opens its own short-lived session rather
than relying on a caller-supplied session for simplicity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from quell.interface.errors import NotFoundError, handle_cli_error
from quell.interface.output import Output
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.memory.incidents import get_incident, list_incidents
from quell.memory.stats import (
    count_incidents,
    mean_time_to_resolve,
    top_signatures,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


async def _session_factory() -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = get_engine()
    await create_tables(engine)
    return get_session_factory(engine), engine


async def print_history(limit: int = 10) -> None:
    """Print the ``limit`` most recent incidents."""
    out = Output()
    factory, engine = await _session_factory()
    async with factory() as session:
        rows = await list_incidents(session, limit=limit)
    if not rows:
        out.info("(no incidents recorded yet)")
    else:
        out.line(f"{'ID':<20} {'STATUS':<14} {'SEV':<9} LAST_SEEN")
        for r in rows:
            out.line(
                f"{r.id:<20} {r.status:<14} {r.severity:<9} "
                f"{r.last_seen.isoformat(timespec='seconds')}"
            )
    await engine.dispose()


async def print_incident(incident_id: str) -> None:
    """Print full details of a single incident."""
    out = Output()
    factory, engine = await _session_factory()
    async with factory() as session:
        inc = await get_incident(session, incident_id)
    if inc is None:
        await engine.dispose()
        code = handle_cli_error(
            NotFoundError(
                f"No incident with ID {incident_id!r}.",
                fix="quell history    # see existing IDs",
            ),
            out,
        )
        raise typer.Exit(code=code)

    out.header(f"Incident {inc.id}")
    out.key_value(
        [
            ("signature", inc.signature),
            ("severity", inc.severity),
            ("status", inc.status),
            ("first_seen", inc.first_seen.isoformat()),
            ("last_seen", inc.last_seen.isoformat()),
            ("occurrence_count", str(inc.occurrence_count)),
            *([("root_cause", inc.root_cause)] if inc.root_cause else []),
            *([("fix_pr_url", inc.fix_pr_url)] if inc.fix_pr_url else []),
        ]
    )
    await engine.dispose()


async def print_stats() -> None:
    """Print aggregate incident statistics."""
    out = Output()
    factory, engine = await _session_factory()
    async with factory() as session:
        total = await count_incidents(session)
        resolved = await count_incidents(session, status="resolved")
        detected = await count_incidents(session, status="detected")
        investigating = await count_incidents(session, status="investigating")
        mttr_seconds = await mean_time_to_resolve(session)
        top = await top_signatures(session, limit=5)

    out.header("Incident statistics")
    pairs: list[tuple[str, str]] = [
        ("total incidents", str(total)),
        ("detected", str(detected)),
        ("investigating", str(investigating)),
        ("resolved", str(resolved)),
    ]
    if mttr_seconds is not None:
        pairs.append(("MTTR", f"{mttr_seconds / 60:.1f} minutes"))
    out.key_value(pairs)
    if top:
        out.line("")
        out.line("  top signatures:")
        for sig, count in top:
            out.line(f"    {sig}  x{count}")
    await engine.dispose()


__all__ = ["print_history", "print_incident", "print_stats"]
