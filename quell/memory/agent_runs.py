"""Typed CRUD operations for the :class:`AgentRun` model.

All functions are async and accept an :class:`AsyncSession`; callers
manage transaction boundaries.

An AgentRun represents one end-to-end agent_loop execution tied to an
:class:`Incident`.  The row is created on ``agent_loop`` entry with
``status="running"`` and finalised on exit by :func:`finish_run`.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.models import AgentRun


def _new_id() -> str:
    """Generate a unique agent-run ID."""
    return f"run_{uuid.uuid4().hex[:12]}"


async def create_run(
    session: AsyncSession,
    *,
    incident_id: str,
    name: str,
    skills: Sequence[str] | None = None,
    parent_agent_id: str | None = None,
    started_at: datetime | None = None,
) -> AgentRun:
    """Insert a new AgentRun row with ``status="running"`` and return it.

    Args:
        session:         Active async session.
        incident_id:     Parent :class:`Incident` id.
        name:            Agent role, e.g. ``"incident_commander"``.
        skills:          Slugs of :class:`~quell.skills.SkillFile` loaded.
        parent_agent_id: ``agent_id`` of the spawner (Phase 13 subagents).
        started_at:      Override the start timestamp (defaults to now).

    Returns:
        The newly-created :class:`AgentRun`.
    """
    run = AgentRun(
        id=_new_id(),
        incident_id=incident_id,
        parent_agent_id=parent_agent_id,
        name=name,
        skills=list(skills) if skills else [],
        status="running",
        started_at=started_at or datetime.now(UTC),
    )
    session.add(run)
    await session.flush()
    return run


async def finish_run(
    session: AsyncSession,
    run_id: str,
    *,
    status: str,
    final_result: dict[str, Any] | None = None,
    finished_at: datetime | None = None,
) -> AgentRun | None:
    """Update an AgentRun on loop exit.

    Args:
        session:      Active async session.
        run_id:       Primary key of the run to finalise.
        status:       ``"completed"`` or ``"failed"``.
        final_result: Optional structured payload from the finish tool.
        finished_at:  Override the finish timestamp (defaults to now).

    Returns:
        The updated :class:`AgentRun`, or ``None`` if not found.
    """
    run = await get_run(session, run_id)
    if run is None:
        return None
    run.status = status
    run.finished_at = finished_at or datetime.now(UTC)
    run.final_result = final_result
    await session.flush()
    return run


async def get_run(session: AsyncSession, run_id: str) -> AgentRun | None:
    """Fetch an AgentRun by primary key."""
    result = await session.execute(sa.select(AgentRun).where(AgentRun.id == run_id))
    return result.scalar_one_or_none()


async def list_runs_for_incident(
    session: AsyncSession, incident_id: str
) -> Sequence[AgentRun]:
    """Return every AgentRun for *incident_id* ordered by ``started_at``."""
    result = await session.execute(
        sa.select(AgentRun)
        .where(AgentRun.incident_id == incident_id)
        .order_by(AgentRun.started_at.asc())
    )
    return result.scalars().all()


__all__ = [
    "create_run",
    "finish_run",
    "get_run",
    "list_runs_for_incident",
]
