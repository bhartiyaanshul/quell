"""Aggregate queries for Quell incident statistics.

Used by `quell stats` and the tracer's final report.
"""

from __future__ import annotations

from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.models import Incident


async def count_incidents(
    session: AsyncSession,
    *,
    status: str | None = None,
) -> int:
    """Return the total number of incidents, optionally filtered by status.

    Args:
        session: Active async session.
        status:  If given, count only incidents with this status.
    """
    query = sa.select(sa.func.count()).select_from(Incident)
    if status is not None:
        query = query.where(Incident.status == status)
    result = await session.execute(query)
    return result.scalar_one()


async def mean_time_to_resolve(session: AsyncSession) -> float | None:
    """Return MTTR in seconds across all resolved incidents.

    Returns:
        Mean seconds from ``first_seen`` to ``last_seen`` for resolved
        incidents, or ``None`` if no resolved incidents exist.
    """
    result = await session.execute(
        sa.select(Incident).where(Incident.status == "resolved")
    )
    incidents = result.scalars().all()
    if not incidents:
        return None

    total_seconds: float = sum(
        (inc.last_seen - inc.first_seen).total_seconds() for inc in incidents
    )
    return total_seconds / len(incidents)


async def top_signatures(
    session: AsyncSession, *, limit: int = 10
) -> list[tuple[str, int]]:
    """Return the most frequently-occurring error signatures.

    Args:
        session: Active async session.
        limit:   Maximum number of entries to return.

    Returns:
        List of ``(signature, total_occurrences)`` tuples, descending by count.
    """
    result = await session.execute(
        sa.select(
            Incident.signature,
            sa.func.sum(Incident.occurrence_count).label("total"),
        )
        .group_by(Incident.signature)
        .order_by(sa.desc("total"))
        .limit(limit)
    )
    return [(row.signature, row.total) for row in result.all()]


async def incidents_in_range(
    session: AsyncSession,
    since: datetime,
    until: datetime | None = None,
) -> int:
    """Count incidents whose ``first_seen`` falls within a time window.

    Args:
        session: Active async session.
        since:   Start of the window (inclusive).
        until:   End of the window (inclusive). Defaults to now.
    """
    until = until or datetime.now(UTC)
    result = await session.execute(
        sa.select(sa.func.count())
        .select_from(Incident)
        .where(Incident.first_seen >= since)
        .where(Incident.first_seen <= until)
    )
    return result.scalar_one()


__all__ = [
    "count_incidents",
    "mean_time_to_resolve",
    "top_signatures",
    "incidents_in_range",
]
