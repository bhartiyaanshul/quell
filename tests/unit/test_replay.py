"""Tests for Phase 22 — terminal replay renderer + CLI handler."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quell.interface.replay import run_replay
from quell.memory import (
    create_event,
    create_run,
    create_tables,
    finish_run,
    get_engine_memory,
    get_session_factory,
)
from quell.memory.incidents import create_incident
from quell.memory.models import AgentRun, Event
from quell.replay.renderer import render_terminal_timeline


@pytest.fixture
async def seeded_engine():  # type: ignore[no-untyped-def]
    """In-memory SQLite with two runs + events for a single incident."""
    engine = get_engine_memory()
    await create_tables(engine)
    factory = get_session_factory(engine)

    async with factory() as session:
        now = datetime.now(UTC).replace(microsecond=0)
        incident = await create_incident(session, signature="z" * 16, severity="high")

        # Run 1 — two events + finish.
        run1 = await create_run(
            session,
            incident_id=incident.id,
            name="incident_commander",
            skills=["django", "postgres"],
            started_at=now,
        )
        await create_event(
            session,
            agent_run_id=run1.id,
            event_type="llm_call",
            payload={
                "model": "anthropic/claude-haiku-4-5",
                "input_tokens": 1000,
                "output_tokens": 500,
                "latency_ms": 1234,
            },
            timestamp=now + timedelta(seconds=1),
        )
        await create_event(
            session,
            agent_run_id=run1.id,
            event_type="tool_call",
            payload={
                "tool_name": "code_read",
                "ok": True,
                "latency_ms": 42,
            },
            timestamp=now + timedelta(seconds=2),
        )
        await finish_run(
            session,
            run1.id,
            status="completed",
            final_result={
                "summary": "null deref on order.user",
                "_metrics": {"cost_usd": 0.0028, "iterations": 1},
            },
            finished_at=now + timedelta(seconds=3),
        )

        # Run 2 — one error event.
        run2 = await create_run(
            session,
            incident_id=incident.id,
            name="log_analyst",
            started_at=now + timedelta(seconds=5),
        )
        await create_event(
            session,
            agent_run_id=run2.id,
            event_type="error",
            payload={"exc_type": "LLMError", "message": "rate limit exceeded"},
            timestamp=now + timedelta(seconds=6),
        )
        await finish_run(
            session,
            run2.id,
            status="failed",
            final_result=None,
            finished_at=now + timedelta(seconds=7),
        )

        await session.commit()

    yield engine, factory, incident.id
    await engine.dispose()


# ---------------------------------------------------------------------------
# render_terminal_timeline — pure-function tests
# ---------------------------------------------------------------------------


def test_renderer_handles_no_runs() -> None:
    out = render_terminal_timeline(incident_id="inc_empty", runs=[])
    assert "inc_empty" in out
    assert "no agent runs" in out


def test_renderer_formats_single_run_with_events() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    run = AgentRun(
        id="run_abc",
        incident_id="inc_1",
        parent_agent_id=None,
        name="stub",
        skills=["django"],
        status="completed",
        started_at=now,
        finished_at=now + timedelta(seconds=2),
        final_result={"summary": "done", "_metrics": {"cost_usd": 0.01}},
    )
    events = [
        Event(
            id="evt_1",
            agent_run_id="run_abc",
            event_type="llm_call",
            timestamp=now + timedelta(seconds=1),
            payload={
                "model": "anthropic/claude-haiku-4-5",
                "input_tokens": 100,
                "output_tokens": 50,
                "latency_ms": 123,
            },
        ),
    ]
    out = render_terminal_timeline(incident_id="inc_1", runs=[(run, events)])

    assert "inc_1" in out
    assert "Run 1" in out
    assert "stub" in out
    assert "django" in out
    assert "$0.0100" in out
    assert "llm_call" in out
    assert "claude-haiku" in out
    assert "done" in out


def test_renderer_totals_across_runs() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    run_a = AgentRun(
        id="run_a",
        incident_id="inc_x",
        parent_agent_id=None,
        name="a",
        skills=[],
        status="completed",
        started_at=now,
        finished_at=now + timedelta(seconds=1),
        final_result={"_metrics": {"cost_usd": 0.03}},
    )
    run_b = AgentRun(
        id="run_b",
        incident_id="inc_x",
        parent_agent_id=None,
        name="b",
        skills=[],
        status="completed",
        started_at=now + timedelta(seconds=2),
        finished_at=now + timedelta(seconds=3),
        final_result={"_metrics": {"cost_usd": 0.02}},
    )
    out = render_terminal_timeline(
        incident_id="inc_x",
        runs=[(run_a, []), (run_b, [])],
    )
    assert "2 runs" in out
    assert "$0.0500" in out  # 0.03 + 0.02 combined total line


def test_renderer_emits_error_events() -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    run = AgentRun(
        id="run_err",
        incident_id="inc_e",
        parent_agent_id=None,
        name="stub",
        skills=[],
        status="failed",
        started_at=now,
        finished_at=now + timedelta(seconds=1),
        final_result=None,
    )
    events = [
        Event(
            id="evt_e",
            agent_run_id="run_err",
            event_type="error",
            timestamp=now,
            payload={"exc_type": "LLMError", "message": "provider timeout"},
        ),
    ]
    out = render_terminal_timeline(incident_id="inc_e", runs=[(run, events)])
    assert "error" in out
    assert "provider timeout" in out


# ---------------------------------------------------------------------------
# run_replay — full CLI handler round-trip
# ---------------------------------------------------------------------------


async def test_run_replay_prints_expected_fields(monkeypatch, capsys, seeded_engine):  # type: ignore[no-untyped-def]
    engine, factory, incident_id = seeded_engine

    # Route run_replay at the seeded in-memory engine.
    from quell.interface import replay as replay_module

    monkeypatch.setattr(replay_module, "get_engine", lambda **_: engine)
    monkeypatch.setattr(replay_module, "get_session_factory", lambda _engine: factory)
    monkeypatch.setattr(replay_module, "create_tables", _noop_create)

    ok = await run_replay(incident_id)
    assert ok is True

    captured = capsys.readouterr().out
    assert incident_id in captured
    assert "Run 1" in captured
    assert "incident_commander" in captured
    assert "llm_call" in captured
    assert "tool_call" in captured
    assert "code_read" in captured
    assert "Run 2" in captured
    assert "log_analyst" in captured
    assert "error" in captured
    assert "rate limit" in captured


async def test_run_replay_returns_false_for_missing_incident(
    monkeypatch, capsys, seeded_engine
):  # type: ignore[no-untyped-def]
    engine, factory, _ = seeded_engine
    from quell.interface import replay as replay_module

    monkeypatch.setattr(replay_module, "get_engine", lambda **_: engine)
    monkeypatch.setattr(replay_module, "get_session_factory", lambda _engine: factory)
    monkeypatch.setattr(replay_module, "create_tables", _noop_create)

    ok = await run_replay("inc_does_not_exist")
    assert ok is False
    captured = capsys.readouterr().out
    assert "No incident" in captured


async def _noop_create(_engine) -> None:  # type: ignore[no-untyped-def]
    """Replaces ``create_tables`` in tests — tables already exist."""
