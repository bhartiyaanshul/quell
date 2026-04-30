"""Tests for the terminal replay renderer.

The end-to-end ``run_replay`` integration tests previously in this file
moved to ``test_cli_incident.py`` along with the migration of the old
``quell replay`` handler into the ``incident`` resource (Phase 3.1).
What remains here is the pure-function renderer surface — it has no
database dependency, so it stays separate from the CLI tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quell.memory.models import AgentRun, Event
from quell.replay.renderer import render_terminal_timeline


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
