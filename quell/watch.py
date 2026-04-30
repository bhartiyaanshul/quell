"""``quell watch`` — the main event loop.

Wires together every earlier phase:

* A :class:`~quell.monitors.base.Monitor` yields :class:`RawEvent` objects.
* A :class:`~quell.detector.Detector` turns events into :class:`Incident`.
* An :class:`~quell.agents.IncidentCommander` investigates each fresh
  incident concurrently in the background.

The function is meant to run until cancelled.  A clean Ctrl-C in the
CLI cancels the outer task; in-flight investigations drain on shutdown.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from quell.agents.incident_commander import IncidentCommander
from quell.config.schema import QuellConfig
from quell.detector import Detector
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.monitors.base import Monitor, create_monitor
from quell.notifiers import Notifier, create_notifier
from quell.skills import list_skills, select_applicable
from quell.tools.builtins import register_builtin_tools
from quell.utils.errors import NotifierError

if TYPE_CHECKING:
    from quell.memory.models import Incident


def incident_prompt(incident: Incident) -> str:
    """Render a first-user-turn message from an :class:`Incident`."""
    return (
        f"Investigate incident {incident.id} "
        f"(signature={incident.signature}, severity={incident.severity}, "
        f"first_seen={incident.first_seen.isoformat()}).\n\n"
        "Begin by reading the most recent logs and recent git commits. "
        "Identify the root cause and call `finish_incident` with a "
        "structured summary."
    )


def _context_from_incident(incident: Incident, evidence: str = "") -> dict[str, str]:
    """Build the context dict used by :func:`select_applicable`."""
    return {
        "error": evidence or incident.signature,
        "signature": incident.signature,
        "framework": "",
        "tech_stack": "",
    }


async def watch(config: QuellConfig) -> None:
    """Run the watch loop indefinitely using *config*."""
    register_builtin_tools()

    if not config.monitors:
        logger.warning("watch: no monitors configured — exiting")
        return

    engine = get_engine()
    await create_tables(engine)
    session_factory = get_session_factory(engine)
    detector = Detector(session_factory=session_factory)

    monitor: Monitor = create_monitor(config.monitors[0])
    # Drop user-disabled skills before select_applicable so they don't
    # get auto-loaded into the system prompt. Explicit-by-name loads via
    # subagent spawn still work — disabling just removes from auto-pickup.
    disabled = set(config.skills.disabled)
    all_skills = [s for s in list_skills() if s.name not in disabled]
    notifiers = _build_notifiers(config)
    background: set[asyncio.Task[dict[str, object]]] = set()

    try:
        async for event in monitor.events():
            incident = await detector.process(event)
            if incident is None:
                continue

            context = _context_from_incident(incident, evidence=event.raw)
            skills = select_applicable(all_skills, context)
            commander = IncidentCommander(
                config,
                loaded_skills=skills,
                session_factory=session_factory,
                incident_id=incident.id,
            )

            logger.info(
                "launching investigation for incident {} ({} skills)",
                incident.id,
                len(skills),
            )
            task = asyncio.create_task(
                _investigate_and_notify(commander, incident, notifiers)
            )
            background.add(task)
            task.add_done_callback(background.discard)
    finally:
        # Drain in-flight investigations on shutdown.
        for task in list(background):
            task.cancel()
        await engine.dispose()


def _build_notifiers(config: QuellConfig) -> list[Notifier]:
    """Instantiate every notifier declared in *config*.

    Configuration errors (missing webhook URL etc.) are logged and the
    offending notifier is skipped so the watch loop still starts with
    the channels that are correctly set up.
    """
    built: list[Notifier] = []
    for cfg in config.notifiers:
        try:
            built.append(create_notifier(cfg))
        except NotifierError as exc:
            logger.warning("notifier {!r} disabled: {}", cfg.type, exc)
    return built


async def _investigate_and_notify(
    commander: IncidentCommander,
    incident: Incident,
    notifiers: list[Notifier],
) -> dict[str, object]:
    """Run the commander, then fan the result out to every notifier."""
    result = await commander.agent_loop(task=incident_prompt(incident))

    if not notifiers:
        return result

    # Fire notifications in parallel; each notifier handles its own
    # transient errors so we do not cancel the others.
    await asyncio.gather(
        *(n.notify(incident) for n in notifiers),
        return_exceptions=True,
    )
    return result


__all__ = ["watch", "incident_prompt"]
