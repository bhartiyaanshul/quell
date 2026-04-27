"""Typed CRUD operations for the :class:`Finding` model.

A Finding is a structured evidence item surfaced by an investigation —
a specific file + line where a root-cause lives, a categorisation
tag, and a confidence score.  Findings are written when the agent
calls its finish tool with metadata containing a ``findings`` list.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.models import Finding


def _new_id() -> str:
    """Generate a unique finding ID."""
    return f"fnd_{uuid.uuid4().hex[:12]}"


async def create_finding(
    session: AsyncSession,
    *,
    incident_id: str,
    agent_run_id: str,
    category: str,
    description: str,
    file_path: str | None = None,
    line_number: int | None = None,
    confidence: float = 1.0,
    created_at: datetime | None = None,
) -> Finding:
    """Insert a new Finding row and return it."""
    finding = Finding(
        id=_new_id(),
        incident_id=incident_id,
        agent_run_id=agent_run_id,
        category=category,
        description=description,
        file_path=file_path,
        line_number=line_number,
        confidence=confidence,
        created_at=created_at or datetime.now(UTC),
    )
    session.add(finding)
    await session.flush()
    return finding


async def list_findings_for_incident(
    session: AsyncSession, incident_id: str
) -> Sequence[Finding]:
    """Return every Finding for *incident_id* ordered by ``created_at``."""
    result = await session.execute(
        sa.select(Finding)
        .where(Finding.incident_id == incident_id)
        .order_by(Finding.created_at.asc())
    )
    return result.scalars().all()


__all__ = ["create_finding", "list_findings_for_incident"]
