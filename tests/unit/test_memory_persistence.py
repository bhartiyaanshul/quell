"""Tests for Phase 19 — AgentRun / Event / Finding persistence.

Two flavours:

1. Direct CRUD tests against an in-memory SQLite engine.
2. Integration: run ``agent_loop`` end-to-end with a session factory
   and assert that rows land in the DB.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from quell.agents.base_agent import BaseAgent
from quell.config.schema import QuellConfig
from quell.llm.llm import LLM
from quell.llm.types import LLMResponse
from quell.memory import (
    count_events_for_run,
    create_event,
    create_finding,
    create_run,
    create_tables,
    finish_run,
    get_engine_memory,
    get_session_factory,
    list_events_for_run,
    list_findings_for_incident,
    list_runs_for_incident,
)
from quell.memory.incidents import create_incident
from quell.tools.registry import clear_registry, register_tool
from quell.tools.result import ToolResult


@pytest.fixture
async def session_factory():  # type: ignore[no-untyped-def]
    """Fresh in-memory SQLite per test."""
    engine = get_engine_memory()
    await create_tables(engine)
    factory = get_session_factory(engine)
    yield factory
    await engine.dispose()


@pytest.fixture(autouse=True)
def _clean_registry():  # type: ignore[no-untyped-def]
    clear_registry()
    yield
    clear_registry()


# ---------------------------------------------------------------------------
# CRUD — AgentRun
# ---------------------------------------------------------------------------


async def test_create_run_populates_defaults(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(
            session, signature="sig1234567890ab", severity="high"
        )
        run = await create_run(
            session,
            incident_id=incident.id,
            name="incident_commander",
            skills=["skill-a", "skill-b"],
        )
        await session.commit()

    assert run.id.startswith("run_")
    assert run.status == "running"
    assert run.skills == ["skill-a", "skill-b"]
    assert run.finished_at is None


async def test_finish_run_sets_status_and_result(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(session, signature="s" * 16, severity="low")
        run = await create_run(session, incident_id=incident.id, name="stub")
        await session.commit()

        finished = await finish_run(
            session,
            run.id,
            status="completed",
            final_result={"summary": "fixed"},
        )
        await session.commit()

    assert finished is not None
    assert finished.status == "completed"
    assert finished.finished_at is not None
    assert finished.final_result == {"summary": "fixed"}


async def test_finish_run_missing_id_returns_none(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        assert await finish_run(session, "run_nonexistent", status="failed") is None


async def test_list_runs_for_incident_ordered_by_started_at(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(session, signature="x" * 16, severity="low")
        r1 = await create_run(
            session,
            incident_id=incident.id,
            name="stub",
            started_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        r2 = await create_run(
            session,
            incident_id=incident.id,
            name="stub",
            started_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
        await session.commit()

        rows = await list_runs_for_incident(session, incident.id)
    assert [r.id for r in rows] == [r1.id, r2.id]


# ---------------------------------------------------------------------------
# CRUD — Event
# ---------------------------------------------------------------------------


async def test_create_and_list_events(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(session, signature="e" * 16, severity="low")
        run = await create_run(session, incident_id=incident.id, name="stub")
        for et in ("llm_call", "tool_call", "tool_call", "error"):
            await create_event(
                session,
                agent_run_id=run.id,
                event_type=et,
                payload={"k": "v"},
            )
        await session.commit()

        all_events = await list_events_for_run(session, run.id)
        tool_only = await list_events_for_run(session, run.id, event_type="tool_call")
        total = await count_events_for_run(session, run.id)

    assert len(all_events) == 4
    assert len(tool_only) == 2
    assert total == 4


# ---------------------------------------------------------------------------
# CRUD — Finding
# ---------------------------------------------------------------------------


async def test_create_finding_defaults(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(session, signature="f" * 16, severity="high")
        run = await create_run(session, incident_id=incident.id, name="stub")
        f = await create_finding(
            session,
            incident_id=incident.id,
            agent_run_id=run.id,
            category="null_reference",
            description="order.user is None",
            file_path="src/checkout.ts",
            line_number=42,
        )
        await session.commit()

    assert f.id.startswith("fnd_")
    assert f.confidence == 1.0
    assert f.file_path == "src/checkout.ts"
    assert f.line_number == 42


async def test_list_findings_for_incident(session_factory):  # type: ignore[no-untyped-def]
    async with session_factory() as session:
        incident = await create_incident(session, signature="g" * 16, severity="high")
        run = await create_run(session, incident_id=incident.id, name="stub")
        await create_finding(
            session,
            incident_id=incident.id,
            agent_run_id=run.id,
            category="null_reference",
            description="one",
        )
        await create_finding(
            session,
            incident_id=incident.id,
            agent_run_id=run.id,
            category="db_error",
            description="two",
        )
        await session.commit()

        findings = await list_findings_for_incident(session, incident.id)

    assert len(findings) == 2
    assert {f.category for f in findings} == {"null_reference", "db_error"}


# ---------------------------------------------------------------------------
# Integration — agent_loop persists rows when session_factory is wired
# ---------------------------------------------------------------------------


class _StubAgent(BaseAgent):
    name = "stub"

    def _render_system_prompt(self) -> str:
        return "You are a test agent."


def _resp(
    content: str, input_tokens: int = 100, output_tokens: int = 50
) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="test-model",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def test_agent_loop_persists_run_and_events(session_factory):  # type: ignore[no-untyped-def]
    """Full integration: agent_loop creates an AgentRun + events + run-finish."""
    # Seed an incident for the run to reference.
    async with session_factory() as session:
        incident = await create_incident(session, signature="i" * 16, severity="high")
        await session.commit()

    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success(
            "finish_incident",
            "root cause: null deref",
            metadata={
                "findings": [
                    {
                        "category": "null_reference",
                        "description": "order.user missing",
                        "file_path": "src/checkout.ts",
                        "line_number": 42,
                        "confidence": 0.9,
                    }
                ],
            },
        )

    # Build agent with persistence wired.
    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>"),
    )
    agent = _StubAgent(
        config,
        llm=llm,
        session_factory=session_factory,
        incident_id=incident.id,
        loaded_skill_names=["test-skill"],
    )
    result = await agent.agent_loop("investigate")
    assert result["status"] == "completed"

    # Verify what landed in the DB.
    async with session_factory() as session:
        runs = await list_runs_for_incident(session, incident.id)
        assert len(runs) == 1
        run = runs[0]
        assert run.status == "completed"
        assert run.finished_at is not None
        assert run.skills == ["test-skill"]

        events = await list_events_for_run(session, run.id)
        event_types = [e.event_type for e in events]
        # 1 llm_call, 1 tool_call
        assert "llm_call" in event_types
        assert "tool_call" in event_types

        llm_event = next(e for e in events if e.event_type == "llm_call")
        assert llm_event.payload["input_tokens"] == 100
        assert llm_event.payload["output_tokens"] == 50

        tool_event = next(e for e in events if e.event_type == "tool_call")
        assert tool_event.payload["tool_name"] == "finish_incident"
        assert tool_event.payload["ok"] is True

        findings = await list_findings_for_incident(session, incident.id)
        assert len(findings) == 1
        assert findings[0].file_path == "src/checkout.ts"
        assert findings[0].line_number == 42


async def test_agent_loop_persists_llm_error_event(session_factory):  # type: ignore[no-untyped-def]
    """An LLM failure should be recorded as an 'error' event."""
    from quell.utils.errors import LLMError

    async with session_factory() as session:
        incident = await create_incident(session, signature="j" * 16, severity="high")
        await session.commit()

    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(side_effect=LLMError("provider timeout"))  # type: ignore[method-assign]
    agent = _StubAgent(
        config,
        llm=llm,
        session_factory=session_factory,
        incident_id=incident.id,
    )
    out = await agent.agent_loop("investigate")
    assert out["status"] == "failed"

    async with session_factory() as session:
        runs = await list_runs_for_incident(session, incident.id)
        assert runs[0].status == "failed"
        events = await list_events_for_run(session, runs[0].id)
        error_events = [e for e in events if e.event_type == "error"]
        assert len(error_events) == 1
        assert "provider timeout" in error_events[0].payload["message"]


async def test_agent_loop_without_session_factory_still_works(session_factory):  # type: ignore[no-untyped-def]
    """The loop must work even when no session_factory is supplied
    (Phase 7 backward-compat path)."""

    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>"),
    )
    agent = _StubAgent(config, llm=llm)  # no session_factory
    result = await agent.agent_loop("test")
    assert result["status"] == "completed"
    # No DB writes should have happened.
    async with session_factory() as session:
        rows = await list_runs_for_incident(session, "inc_none")
        assert rows == []
