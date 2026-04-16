"""Tests for quell.memory — SQLAlchemy models, DB setup, CRUD, and stats."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from quell.memory.db import create_tables, get_engine_memory, get_session_factory
from quell.memory.incidents import (
    create_incident,
    get_incident,
    list_incidents,
    update_incident,
)
from quell.memory.models import AgentRun, Event, Finding, Incident
from quell.memory.stats import (
    count_incidents,
    mean_time_to_resolve,
    top_signatures,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def session() -> AsyncSession:  # type: ignore[misc]
    """Yield a fresh in-memory AsyncSession with all tables created."""
    engine = get_engine_memory()
    await create_tables(engine)
    factory = get_session_factory(engine)
    async with factory() as s:
        yield s
    await engine.dispose()


# ---------------------------------------------------------------------------
# Schema / migration
# ---------------------------------------------------------------------------


async def test_create_tables_idempotent() -> None:
    """create_tables can be called multiple times without error."""
    engine = get_engine_memory()
    await create_tables(engine)
    await create_tables(engine)  # second call must not raise
    await engine.dispose()


async def test_all_models_importable() -> None:
    """ORM model classes are importable and have expected table names."""
    assert Incident.__tablename__ == "incidents"
    assert AgentRun.__tablename__ == "agent_runs"
    assert Event.__tablename__ == "events"
    assert Finding.__tablename__ == "findings"


# ---------------------------------------------------------------------------
# Incident CRUD
# ---------------------------------------------------------------------------


async def test_create_and_retrieve_incident(session: AsyncSession) -> None:
    """create_incident + get_incident round-trip works correctly."""
    inc = await create_incident(
        session,
        signature="TypeError: Cannot read property",
        severity="high",
    )
    await session.commit()

    fetched = await get_incident(session, inc.id)
    assert fetched is not None
    assert fetched.id == inc.id
    assert fetched.signature == "TypeError: Cannot read property"
    assert fetched.severity == "high"
    assert fetched.status == "detected"
    assert fetched.occurrence_count == 1


async def test_get_incident_missing_returns_none(session: AsyncSession) -> None:
    """get_incident returns None for an unknown id."""
    result = await get_incident(session, "inc_doesnotexist")
    assert result is None


async def test_list_incidents_filtered_by_status(session: AsyncSession) -> None:
    """list_incidents correctly filters by status."""
    await create_incident(session, signature="sig-a", severity="low", status="detected")
    await create_incident(
        session, signature="sig-b", severity="high", status="resolved"
    )
    await session.commit()

    detected = await list_incidents(session, status="detected")
    resolved = await list_incidents(session, status="resolved")

    assert len(detected) == 1
    assert detected[0].signature == "sig-a"
    assert len(resolved) == 1
    assert resolved[0].signature == "sig-b"


async def test_update_incident(session: AsyncSession) -> None:
    """update_incident changes the requested fields."""
    inc = await create_incident(session, signature="sig-x", severity="medium")
    await session.commit()

    updated = await update_incident(
        session, inc.id, status="investigating", root_cause="null pointer in handler"
    )
    await session.commit()

    assert updated is not None
    assert updated.status == "investigating"
    assert updated.root_cause == "null pointer in handler"


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


async def test_count_incidents(session: AsyncSession) -> None:
    """count_incidents returns correct total and status-filtered counts."""
    await create_incident(session, signature="s1", severity="low", status="detected")
    await create_incident(session, signature="s2", severity="high", status="resolved")
    await session.commit()

    assert await count_incidents(session) == 2
    assert await count_incidents(session, status="detected") == 1
    assert await count_incidents(session, status="resolved") == 1
    assert await count_incidents(session, status="abandoned") == 0


async def test_mean_time_to_resolve_no_resolved(session: AsyncSession) -> None:
    """mean_time_to_resolve returns None when no resolved incidents exist."""
    await create_incident(session, signature="s1", severity="low", status="detected")
    await session.commit()

    assert await mean_time_to_resolve(session) is None


async def test_mean_time_to_resolve_with_data(session: AsyncSession) -> None:
    """mean_time_to_resolve computes correct average seconds."""
    now = datetime.now(UTC)
    inc = await create_incident(
        session,
        signature="s1",
        severity="high",
        status="resolved",
        first_seen=now - timedelta(seconds=120),
    )
    await update_incident(session, inc.id, last_seen=now, status="resolved")
    await session.commit()

    mttr = await mean_time_to_resolve(session)
    assert mttr is not None
    assert 100 < mttr < 140  # ~120 seconds


async def test_top_signatures(session: AsyncSession) -> None:
    """top_signatures returns signatures ranked by occurrence count."""
    await create_incident(session, signature="common-error", severity="high")
    await create_incident(session, signature="common-error", severity="high")
    await create_incident(session, signature="rare-error", severity="low")
    await session.commit()

    sigs = await top_signatures(session, limit=5)
    assert len(sigs) >= 1
    # Most common should appear first
    top_sig, _ = sigs[0]
    assert top_sig in ("common-error", "rare-error")
