"""Tests for quell.agents.state and quell.agents.types."""

from __future__ import annotations

import time
import uuid
from datetime import datetime

import pytest

from quell.agents.state import AgentState
from quell.agents.types import AgentMessage, AgentStatus, ToolObservation
from quell.llm.types import LLMMessage

# ---------------------------------------------------------------------------
# AgentStatus enum
# ---------------------------------------------------------------------------


def test_agent_status_members() -> None:
    assert AgentStatus.IDLE.value == "idle"
    assert AgentStatus.RUNNING.value == "running"
    assert AgentStatus.WAITING.value == "waiting"
    assert AgentStatus.COMPLETED.value == "completed"
    assert AgentStatus.FAILED.value == "failed"


def test_agent_status_is_str_enum() -> None:
    # ``str, Enum`` mixin — values compare equal to their string form.
    assert AgentStatus.RUNNING == "running"
    assert {AgentStatus.IDLE, AgentStatus.FAILED} == {"idle", "failed"}


# ---------------------------------------------------------------------------
# AgentState defaults & factories
# ---------------------------------------------------------------------------


def test_state_default_factories() -> None:
    state = AgentState(name="commander", task="investigate 500s")

    # Auto uuid4
    uuid.UUID(state.agent_id)  # raises if not a valid UUID

    # Default status
    assert state.status == AgentStatus.IDLE

    # Default lists are fresh per-instance (no shared mutable default)
    assert state.messages == []
    assert state.errors == []
    other = AgentState(name="x", task="y")
    state.messages.append(LLMMessage(role="user", content="hi"))
    assert other.messages == []

    # Default iteration + max_iterations
    assert state.iteration == 0
    assert state.max_iterations == 50

    # Timestamps populated, UTC-aware
    assert isinstance(state.created_at, datetime)
    assert state.created_at.tzinfo is not None
    assert state.updated_at.tzinfo is not None

    # Nullable defaults
    assert state.parent_id is None
    assert state.sandbox_url is None
    assert state.sandbox_token is None
    assert state.final_result is None


def test_state_required_fields_enforced() -> None:
    with pytest.raises(ValueError):
        AgentState()  # type: ignore[call-arg]  # missing name + task


def test_state_status_transitions() -> None:
    state = AgentState(name="a", task="b")
    state.status = AgentStatus.RUNNING
    assert state.status is AgentStatus.RUNNING
    state.status = AgentStatus.COMPLETED
    assert state.status is AgentStatus.COMPLETED


def test_state_messages_accept_llm_message() -> None:
    state = AgentState(name="a", task="b")
    state.messages.append(LLMMessage(role="system", content="you are helpful"))
    state.messages.append(LLMMessage(role="user", content="hi"))
    assert len(state.messages) == 2
    assert state.messages[0].role == "system"
    assert state.messages[1].content == "hi"


def test_state_touch_advances_updated_at() -> None:
    state = AgentState(name="a", task="b")
    before = state.updated_at
    time.sleep(0.01)
    state.touch()
    assert state.updated_at > before


def test_state_model_dump_serializes() -> None:
    state = AgentState(
        name="commander",
        task="find the bug",
        status=AgentStatus.RUNNING,
    )
    state.iteration = 3
    state.errors.append("transient LLM timeout")
    dumped = state.model_dump()

    assert dumped["name"] == "commander"
    assert dumped["task"] == "find the bug"
    assert dumped["status"] == "running"  # str enum serializes to its value
    assert dumped["iteration"] == 3
    assert dumped["errors"] == ["transient LLM timeout"]
    assert isinstance(dumped["agent_id"], str)


def test_state_accepts_parent_id() -> None:
    parent = AgentState(name="root", task="root task")
    child = AgentState(name="child", task="subtask", parent_id=parent.agent_id)
    assert child.parent_id == parent.agent_id


def test_state_max_iterations_override() -> None:
    state = AgentState(name="a", task="b", max_iterations=5)
    assert state.max_iterations == 5


# ---------------------------------------------------------------------------
# AgentMessage / ToolObservation (Phase 14 prep)
# ---------------------------------------------------------------------------


def test_agent_message_construction() -> None:
    msg = AgentMessage(iteration=2, role="assistant", content="I'll check the logs.")
    assert msg.iteration == 2
    assert msg.role == "assistant"
    assert msg.content == "I'll check the logs."
    assert isinstance(msg.timestamp, datetime)
    assert msg.timestamp.tzinfo is not None


def test_tool_observation_construction() -> None:
    obs = ToolObservation(
        iteration=1,
        tool_name="code_read",
        ok=True,
        output="def main(): pass",
    )
    assert obs.tool_name == "code_read"
    assert obs.ok is True
    assert obs.output == "def main(): pass"
    assert obs.error == ""  # default
    assert isinstance(obs.timestamp, datetime)


def test_tool_observation_failure_shape() -> None:
    obs = ToolObservation(
        iteration=2,
        tool_name="http_probe",
        ok=False,
        error="connection refused",
    )
    assert obs.ok is False
    assert obs.error == "connection refused"
    assert obs.output == ""
