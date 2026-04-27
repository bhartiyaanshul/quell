"""CLI handler for ``quell replay <incident_id>``."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from rich.console import Console

from quell.memory.agent_runs import list_runs_for_incident
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.memory.events import list_events_for_run
from quell.memory.incidents import get_incident
from quell.memory.models import AgentRun, Event
from quell.replay.renderer import render_terminal_timeline

_console = Console()


async def run_replay(incident_id: str, *, db_path: Path | None = None) -> bool:
    """Load stored events + runs and print the timeline to the terminal.

    Returns:
        ``True`` on success, ``False`` if the incident wasn't found.
    """
    engine = get_engine(db_path=db_path)
    await create_tables(engine)
    factory = get_session_factory(engine)

    try:
        async with factory() as session:
            incident = await get_incident(session, incident_id)
            if incident is None:
                _console.print(f"[red]No incident with id[/red] {incident_id!r}")
                return False

            runs = await list_runs_for_incident(session, incident_id)
            enriched: list[tuple[AgentRun, Sequence[Event]]] = []
            for run in runs:
                events = await list_events_for_run(session, run.id)
                enriched.append((run, events))
    finally:
        await engine.dispose()

    output = render_terminal_timeline(incident_id=incident_id, runs=enriched)
    _console.print(output)
    return True


__all__ = ["run_replay"]
