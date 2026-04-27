"""Typed CRUD operations for the :class:`Event` model.

Events are the per-iteration breadcrumbs a `BaseAgent` drops during
an investigation — one per LLM call, one per tool call, one per
error.  They power the Phase 21 dashboard timeline and the Phase 22
replay feature.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.models import Event

EventType = str  # "llm_call" | "tool_call" | "error" | "info"


def _new_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid.uuid4().hex[:12]}"


async def create_event(
    session: AsyncSession,
    *,
    agent_run_id: str,
    event_type: EventType,
    payload: dict[str, Any],
    timestamp: datetime | None = None,
) -> Event:
    """Insert a new Event row and return it.

    Args:
        session:      Active async session.
        agent_run_id: Parent :class:`AgentRun` id.
        event_type:   One of ``"llm_call"`` / ``"tool_call"`` /
                      ``"error"`` / ``"info"``.
        payload:      JSON-serialisable structured data (schemas vary by
                      ``event_type`` — see docs/architecture.md).
        timestamp:    Override the observed-at time (defaults to now).
    """
    event = Event(
        id=_new_id(),
        agent_run_id=agent_run_id,
        event_type=event_type,
        timestamp=timestamp or datetime.now(UTC),
        payload=payload,
    )
    session.add(event)
    await session.flush()
    return event


async def list_events_for_run(
    session: AsyncSession,
    agent_run_id: str,
    *,
    event_type: EventType | None = None,
) -> Sequence[Event]:
    """Return every Event for *agent_run_id* ordered by timestamp."""
    query = (
        sa.select(Event)
        .where(Event.agent_run_id == agent_run_id)
        .order_by(Event.timestamp.asc())
    )
    if event_type is not None:
        query = query.where(Event.event_type == event_type)
    result = await session.execute(query)
    return result.scalars().all()


async def count_events_for_run(session: AsyncSession, agent_run_id: str) -> int:
    """Return the number of events recorded for *agent_run_id*."""
    result = await session.execute(
        sa.select(sa.func.count(Event.id)).where(Event.agent_run_id == agent_run_id)
    )
    return int(result.scalar_one() or 0)


__all__ = ["create_event", "list_events_for_run", "count_events_for_run"]
