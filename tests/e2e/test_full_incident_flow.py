"""End-to-end flow — monitor → detector → commander → finish.

The LLM is mocked.  The monitor is an in-process ``AsyncGenerator`` that
yields a hand-crafted error event and stops.  The agent's finish tool
runs for real.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from quell.agents.incident_commander import IncidentCommander
from quell.config.schema import QuellConfig
from quell.detector import Detector
from quell.llm.types import LLMResponse
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.monitors.base import Monitor, RawEvent
from quell.skills import list_skills, select_applicable
from quell.tools.builtins import register_builtin_tools
from quell.watch import incident_prompt


class _InlineMonitor(Monitor):
    """Yields one crafted event then stops — good enough for an e2e test."""

    def __init__(self, event: RawEvent) -> None:
        self._event = event

    async def events(self) -> AsyncGenerator[RawEvent, None]:
        yield self._event


@pytest.fixture(autouse=True)
def _bootstrap():  # type: ignore[no-untyped-def]
    register_builtin_tools()
    yield


async def test_full_incident_flow(tmp_path) -> None:  # type: ignore[no-untyped-def]
    register_builtin_tools()

    # Set up a temp database for the detector.
    db_file = tmp_path / "incidents.db"
    engine = get_engine(db_file)
    await create_tables(engine)
    factory = get_session_factory(engine)
    detector = Detector(session_factory=factory)

    # Fabricate an incident-worthy event.
    event = RawEvent(
        source="local-file",
        timestamp=datetime.now(UTC),
        raw=(
            "TypeError: Cannot read properties of null (reading 'id') "
            "at processOrder (src/checkout.ts:42:18)"
        ),
        severity="error",
    )
    monitor = _InlineMonitor(event)

    # Run detector over the single event.
    incident = None
    async for ev in monitor.events():
        incident = await detector.process(ev)
    assert incident is not None

    # Pick skills (should match unhandled-null at minimum).
    skills = select_applicable(
        list_skills(),
        {"error": event.raw, "signature": incident.signature},
    )
    skill_names = {s.name for s in skills}
    assert "unhandled-null" in skill_names

    # Spin up the commander with a mocked LLM that calls finish_incident.
    commander = IncidentCommander(QuellConfig(), loaded_skills=skills)
    commander.llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=LLMResponse(
            content=(
                "<function=finish_incident>"
                "<parameter=root_cause>null deref on order.user</parameter>"
                "<parameter=evidence>src/checkout.ts:42</parameter>"
                "<parameter=proposed_fix>guard against order.user is None</parameter>"
                "<parameter=status>resolved</parameter>"
                "</function>"
            ),
            model="test",
            input_tokens=0,
            output_tokens=0,
        )
    )

    result = await commander.agent_loop(incident_prompt(incident))

    assert result["status"] == "completed"
    assert isinstance(result["result"], dict)
    assert result["result"]["root_cause"] == "null deref on order.user"
    assert result["result"]["status"] == "resolved"
    assert result["result"]["proposed_fix"].startswith("guard")

    await engine.dispose()
