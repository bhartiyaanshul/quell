"""CLI helpers for inspecting the incident database.

Backs the Phase 15 commands ``quell history``, ``quell show <id>``, and
``quell stats``.  Each helper opens its own short-lived session rather
than relying on a caller-supplied session for simplicity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

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
    factory, engine = await _session_factory()
    async with factory() as session:
        rows = await list_incidents(session, limit=limit)
    if not rows:
        typer.echo("(no incidents recorded yet)")
    else:
        typer.echo(f"{'ID':<20} {'STATUS':<14} {'SEV':<9} LAST_SEEN")
        for r in rows:
            typer.echo(
                f"{r.id:<20} {r.status:<14} {r.severity:<9} "
                f"{r.last_seen.isoformat(timespec='seconds')}"
            )
    await engine.dispose()


async def print_incident(incident_id: str) -> None:
    """Print full details of a single incident."""
    factory, engine = await _session_factory()
    async with factory() as session:
        inc = await get_incident(session, incident_id)
    if inc is None:
        typer.echo(f"Incident {incident_id!r} not found.")
        await engine.dispose()
        raise typer.Exit(code=1)

    typer.echo(f"Incident {inc.id}")
    typer.echo(f"  signature:         {inc.signature}")
    typer.echo(f"  severity:          {inc.severity}")
    typer.echo(f"  status:            {inc.status}")
    typer.echo(f"  first_seen:        {inc.first_seen.isoformat()}")
    typer.echo(f"  last_seen:         {inc.last_seen.isoformat()}")
    typer.echo(f"  occurrence_count:  {inc.occurrence_count}")
    if inc.root_cause:
        typer.echo(f"  root_cause:        {inc.root_cause}")
    if inc.fix_pr_url:
        typer.echo(f"  fix_pr_url:        {inc.fix_pr_url}")
    await engine.dispose()


async def print_stats() -> None:
    """Print aggregate incident statistics."""
    factory, engine = await _session_factory()
    async with factory() as session:
        total = await count_incidents(session)
        resolved = await count_incidents(session, status="resolved")
        detected = await count_incidents(session, status="detected")
        investigating = await count_incidents(session, status="investigating")
        mttr_seconds = await mean_time_to_resolve(session)
        top = await top_signatures(session, limit=5)

    typer.echo("Incident statistics")
    typer.echo(f"  total incidents:   {total}")
    typer.echo(f"  detected:          {detected}")
    typer.echo(f"  investigating:     {investigating}")
    typer.echo(f"  resolved:          {resolved}")
    if mttr_seconds is not None:
        typer.echo(f"  MTTR:              {mttr_seconds / 60:.1f} minutes")
    if top:
        typer.echo("  top signatures:")
        for sig, count in top:
            typer.echo(f"    {sig}  x{count}")
    await engine.dispose()


__all__ = ["print_history", "print_incident", "print_stats"]
