"""Typed CRUD operations for the Incident model.

All functions are async and accept an :class:`AsyncSession` — callers are
responsible for managing transaction boundaries and committing.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.models import Incident


def _new_id() -> str:
    """Generate a unique incident ID."""
    return f"inc_{uuid.uuid4().hex[:12]}"


async def create_incident(
    session: AsyncSession,
    *,
    signature: str,
    severity: str,
    status: str = "detected",
    first_seen: datetime | None = None,
) -> Incident:
    """Insert a new Incident row and return it.

    Args:
        session:    Active async session.
        signature:  Stable error signature (from the detector).
        severity:   Severity label (low / medium / high / critical).
        status:     Initial lifecycle status.
        first_seen: Event timestamp (defaults to now).

    Returns:
        The newly-created :class:`Incident`.
    """
    now = first_seen or datetime.now(UTC)
    incident = Incident(
        id=_new_id(),
        signature=signature,
        severity=severity,
        status=status,
        first_seen=now,
        last_seen=now,
        occurrence_count=1,
    )
    session.add(incident)
    await session.flush()
    return incident


async def get_incident(session: AsyncSession, incident_id: str) -> Incident | None:
    """Fetch an Incident by primary key.

    Returns:
        The matching :class:`Incident`, or ``None`` if not found.
    """
    result = await session.execute(
        sa.select(Incident).where(Incident.id == incident_id)
    )
    return result.scalar_one_or_none()


async def list_incidents(
    session: AsyncSession,
    *,
    status: str | None = None,
    limit: int = 50,
) -> Sequence[Incident]:
    """Return incidents, optionally filtered by status.

    Args:
        session: Active async session.
        status:  If provided, only return incidents with this status.
        limit:   Maximum number of rows to return.

    Returns:
        A sequence of :class:`Incident` ordered by ``last_seen`` descending.
    """
    query = sa.select(Incident).order_by(Incident.last_seen.desc()).limit(limit)
    if status is not None:
        query = query.where(Incident.status == status)
    result = await session.execute(query)
    return result.scalars().all()


async def update_incident(
    session: AsyncSession,
    incident_id: str,
    **fields: object,
) -> Incident | None:
    """Update arbitrary fields on an Incident and return the updated row.

    Args:
        session:     Active async session.
        incident_id: Primary key of the incident to update.
        **fields:    Column names and their new values.

    Returns:
        The updated :class:`Incident`, or ``None`` if not found.
    """
    incident = await get_incident(session, incident_id)
    if incident is None:
        return None
    for key, value in fields.items():
        setattr(incident, key, value)
    await session.flush()
    return incident


async def bump_occurrence(session: AsyncSession, incident_id: str) -> Incident | None:
    """Increment occurrence_count and refresh last_seen for an Incident.

    Returns:
        The updated :class:`Incident`, or ``None`` if not found.
    """
    return await update_incident(
        session,
        incident_id,
        occurrence_count=sa.text("occurrence_count + 1"),  # noqa: S608 — not user input
        last_seen=datetime.now(UTC),
    )


__all__ = [
    "create_incident",
    "get_incident",
    "list_incidents",
    "update_incident",
    "bump_occurrence",
]
