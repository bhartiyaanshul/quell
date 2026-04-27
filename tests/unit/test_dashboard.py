"""Tests for Phase 21 — dashboard FastAPI backend.

Uses ``httpx.ASGITransport`` to exercise routes in-process without
booting uvicorn.  Seed an in-memory SQLite with a couple of incidents
+ runs + events and assert the JSON payloads are shaped as the
frontend expects.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from quell.dashboard.server import create_dashboard_app
from quell.memory import (
    create_event,
    create_finding,
    create_run,
    create_tables,
    finish_run,
    get_engine_memory,
    get_session_factory,
)
from quell.memory.incidents import create_incident, update_incident


@pytest.fixture
async def seeded_factory():  # type: ignore[no-untyped-def]
    """In-memory SQLite with two incidents, three runs, some events."""
    engine = get_engine_memory()
    await create_tables(engine)
    factory = get_session_factory(engine)

    async with factory() as session:
        now = datetime.now(UTC)
        # Incident A — resolved, one run, two events + a finding.
        a = await create_incident(session, signature="a" * 16, severity="high")
        run_a = await create_run(
            session,
            incident_id=a.id,
            name="incident_commander",
            skills=["django", "postgres"],
            started_at=now - timedelta(minutes=5),
        )
        await create_event(
            session,
            agent_run_id=run_a.id,
            event_type="llm_call",
            payload={
                "model": "anthropic/claude-haiku-4-5",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
            timestamp=now - timedelta(minutes=4),
        )
        await create_event(
            session,
            agent_run_id=run_a.id,
            event_type="tool_call",
            payload={"tool_name": "code_read", "ok": True, "latency_ms": 42},
            timestamp=now - timedelta(minutes=3),
        )
        await create_finding(
            session,
            incident_id=a.id,
            agent_run_id=run_a.id,
            category="null_reference",
            description="order.user is None",
            file_path="src/checkout.ts",
            line_number=42,
        )
        await finish_run(
            session,
            run_a.id,
            status="completed",
            final_result={
                "summary": "null deref",
                "_metrics": {
                    "cost_usd": 0.0028,
                    "iterations": 3,
                    "input_tokens": 1000,
                    "output_tokens": 500,
                },
            },
            finished_at=now - timedelta(minutes=2),
        )
        await update_incident(
            session,
            a.id,
            status="resolved",
            root_cause="null deref",
            cost_usd=0.0028,
        )

        # Incident B — still detected, no runs yet.
        b = await create_incident(session, signature="b" * 16, severity="low")

        await session.commit()

    yield factory, a.id, b.id
    await engine.dispose()


async def _client(session_factory) -> httpx.AsyncClient:  # type: ignore[no-untyped-def]
    app = create_dashboard_app(session_factory, static_dir=None)  # type: ignore[arg-type]
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://dashboard.test")


# ---------------------------------------------------------------------------
# /api/incidents
# ---------------------------------------------------------------------------


async def test_list_incidents_returns_all(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, b_id = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/api/incidents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    ids = [i["id"] for i in data["incidents"]]
    assert a_id in ids and b_id in ids


async def test_list_incidents_filters_by_status(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/api/incidents?status=resolved")
    data = resp.json()
    assert data["count"] == 1
    assert data["incidents"][0]["id"] == a_id


async def test_get_incident_includes_runs_and_findings(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get(f"/api/incidents/{a_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident"]["id"] == a_id
    assert data["incident"]["cost_usd"] == 0.0028
    assert len(data["runs"]) == 1
    assert data["runs"][0]["cost_usd"] == 0.0028
    assert data["runs"][0]["iterations"] == 3
    assert len(data["findings"]) == 1
    assert data["findings"][0]["file_path"] == "src/checkout.ts"


async def test_get_incident_404(seeded_factory):  # type: ignore[no-untyped-def]
    factory, _, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/api/incidents/inc_does_not_exist")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/runs/{run_id}/events
# ---------------------------------------------------------------------------


async def test_list_events_for_run(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, _ = seeded_factory
    async with await _client(factory) as client:
        incident = (await client.get(f"/api/incidents/{a_id}")).json()
        run_id = incident["runs"][0]["id"]
        resp = await client.get(f"/api/runs/{run_id}/events")
    data = resp.json()
    assert data["count"] == 2
    types = [e["event_type"] for e in data["events"]]
    assert "llm_call" in types and "tool_call" in types


async def test_list_events_filters_by_type(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, _ = seeded_factory
    async with await _client(factory) as client:
        incident = (await client.get(f"/api/incidents/{a_id}")).json()
        run_id = incident["runs"][0]["id"]
        resp = await client.get(f"/api/runs/{run_id}/events?event_type=llm_call")
    data = resp.json()
    assert data["count"] == 1
    assert data["events"][0]["event_type"] == "llm_call"


# ---------------------------------------------------------------------------
# /api/stats
# ---------------------------------------------------------------------------


async def test_stats_endpoint_shape(seeded_factory):  # type: ignore[no-untyped-def]
    factory, _, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/api/stats")
    data = resp.json()
    assert data["total"] == 2
    assert data["by_status"]["resolved"] == 1
    assert data["by_status"]["detected"] == 1
    assert isinstance(data["top_signatures"], list)


# ---------------------------------------------------------------------------
# /api/incidents/{id}/replay
# ---------------------------------------------------------------------------


async def test_replay_endpoint_groups_events_by_run(seeded_factory):  # type: ignore[no-untyped-def]
    factory, a_id, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get(f"/api/incidents/{a_id}/replay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["incident_id"] == a_id
    assert len(data["runs"]) == 1
    run = data["runs"][0]
    assert len(run["events"]) == 2
    assert run["cost_usd"] == 0.0028
    assert data["totals"]["runs"] == 1
    assert data["totals"]["events"] == 2


async def test_replay_endpoint_404_on_missing_incident(seeded_factory):  # type: ignore[no-untyped-def]
    factory, _, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/api/incidents/inc_nope/replay")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# OpenAPI / root behaviour
# ---------------------------------------------------------------------------


async def test_openapi_schema_exposed(seeded_factory):  # type: ignore[no-untyped-def]
    factory, _, _ = seeded_factory
    async with await _client(factory) as client:
        resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert "paths" in resp.json()
