"""Tests for BaseAgent.agent_loop and IncidentCommander.

Strategy: a minimal ``_StubAgent`` subclass provides a fixed system prompt;
the LLM is injected via constructor and its ``generate`` coroutine is
mocked with ``AsyncMock(side_effect=[...])`` to simulate multi-turn
conversations without touching any provider.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from quell.agents.base_agent import BaseAgent
from quell.agents.incident_commander import IncidentCommander
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.llm import LLM
from quell.llm.types import LLMResponse
from quell.tools.registry import clear_registry, register_tool
from quell.tools.result import ToolResult
from quell.utils.errors import LLMError

# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------


class _StubAgent(BaseAgent):
    """Minimal concrete agent with a fixed system prompt."""

    name = "stub"

    def _render_system_prompt(self) -> str:
        return "You are a test agent."


def _resp(content: str) -> LLMResponse:
    return LLMResponse(
        content=content, model="test-model", input_tokens=0, output_tokens=0
    )


def _make_agent_with_llm(
    *responses: LLMResponse,
    raise_first: Exception | None = None,
) -> _StubAgent:
    """Construct a ``_StubAgent`` whose LLM yields the given responses."""
    config = QuellConfig()
    llm = LLM(config.llm)
    mock = AsyncMock()
    if raise_first is not None:
        mock.side_effect = raise_first
    elif len(responses) == 1:
        mock.return_value = responses[0]
    else:
        mock.side_effect = list(responses)
    llm.generate = mock  # type: ignore[method-assign]
    return _StubAgent(config, llm=llm)


@pytest.fixture(autouse=True)
def _clean_registry():  # type: ignore[no-untyped-def]
    clear_registry()
    yield
    clear_registry()


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


async def test_agent_loop_happy_path_finish_tool() -> None:
    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success(
            "finish_incident",
            "root cause: null deref in checkout",
            metadata={"root_cause": "null deref", "severity": "high"},
        )

    agent = _make_agent_with_llm(_resp("<function=finish_incident></function>"))
    out = await agent.agent_loop("investigate the crash")

    assert out["status"] == "completed"
    assert out["iterations"] == 1
    assert out["errors"] == []
    result = out["result"]
    assert isinstance(result, dict)
    assert result["root_cause"] == "null deref"
    assert result["severity"] == "high"
    assert result["summary"] == "root cause: null deref in checkout"

    assert agent.state is not None
    assert agent.state.status == AgentStatus.COMPLETED
    # system prompt + initial user task + assistant turn + observations
    assert len(agent.state.messages) == 4


async def test_agent_loop_no_tools_treats_as_finish() -> None:
    agent = _make_agent_with_llm(_resp("The logs already show the answer."))
    out = await agent.agent_loop("what broke?")

    assert out["status"] == "completed"
    assert out["iterations"] == 0  # no tool-executing turn ran
    assert out["errors"] == []
    assert out["result"] == {}
    assert agent.state is not None
    assert agent.state.status == AgentStatus.COMPLETED


# ---------------------------------------------------------------------------
# Failure / termination paths
# ---------------------------------------------------------------------------


async def test_agent_loop_hits_max_iterations() -> None:
    @register_tool(name="noop", description="Does nothing.", execute_in_sandbox=False)
    async def noop() -> ToolResult:
        return ToolResult.success("noop", "ok")

    # An infinite-ish stream of non-finish tool calls.
    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=noop></function>")
    )
    agent = _StubAgent(config, llm=llm)
    agent_state_builder = agent._build_initial_state

    # Override the builder to cap iterations tightly for fast tests.
    def _tight_state(task: str):  # type: ignore[no-untyped-def]
        state = agent_state_builder(task)
        state.max_iterations = 3
        return state

    agent._build_initial_state = _tight_state  # type: ignore[method-assign]

    out = await agent.agent_loop("spin forever")
    assert out["status"] == "failed"
    assert out["iterations"] == 3
    errors = out["errors"]
    assert isinstance(errors, list)
    assert any("max_iterations" in e for e in errors)


async def test_agent_loop_tool_failure_continues() -> None:
    @register_tool(name="broken", description="Always fails.", execute_in_sandbox=False)
    async def broken() -> ToolResult:
        return ToolResult.failure("broken", "disk full")

    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "investigation done")

    agent = _make_agent_with_llm(
        _resp("<function=broken></function>"),
        _resp("<function=finish_incident></function>"),
    )
    out = await agent.agent_loop("investigate")

    assert out["status"] == "completed"
    assert out["iterations"] == 2
    assert agent.state is not None
    # The broken tool's failure should appear in the observation history
    assert any("disk full" in m.content for m in agent.state.messages)


async def test_agent_loop_llm_error_sets_failed() -> None:
    agent = _make_agent_with_llm(raise_first=LLMError("provider timeout"))

    out = await agent.agent_loop("investigate")
    assert out["status"] == "failed"
    assert out["iterations"] == 0
    errors = out["errors"]
    assert isinstance(errors, list)
    assert any("provider timeout" in e for e in errors)
    assert any("LLMError" in e for e in errors)


# ---------------------------------------------------------------------------
# Multi-iteration behaviour
# ---------------------------------------------------------------------------


async def test_agent_loop_multi_iteration_multi_tools() -> None:
    call_counts: dict[str, int] = {"noop": 0}

    @register_tool(name="noop", description="Records calls.", execute_in_sandbox=False)
    async def noop() -> ToolResult:
        call_counts["noop"] += 1
        return ToolResult.success("noop", f"call {call_counts['noop']}")

    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done", metadata={"iterations": 3})

    two_noops = "<function=noop></function>\n<function=noop></function>"
    agent = _make_agent_with_llm(
        _resp(two_noops),
        _resp(two_noops),
        _resp("<function=finish_incident></function>"),
    )

    out = await agent.agent_loop("multi-step investigate")
    assert out["status"] == "completed"
    assert out["iterations"] == 3
    assert call_counts["noop"] == 4  # 2 iterations × 2 tool calls each
    result = out["result"]
    assert isinstance(result, dict)
    assert result["iterations"] == 3


async def test_agent_loop_final_result_merges_metadata() -> None:
    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success(
            "finish_incident",
            "see attached summary",
            metadata={
                "root_cause": "race condition",
                "fix_pr_url": "https://example.com/pr/1",
            },
        )

    agent = _make_agent_with_llm(_resp("<function=finish_incident></function>"))
    out = await agent.agent_loop("investigate")
    result = out["result"]
    assert isinstance(result, dict)
    assert result["summary"] == "see attached summary"
    assert result["root_cause"] == "race condition"
    assert result["fix_pr_url"] == "https://example.com/pr/1"


# ---------------------------------------------------------------------------
# IncidentCommander integration
# ---------------------------------------------------------------------------


async def test_incident_commander_renders_prompt_and_loops() -> None:
    @register_tool(
        name="finish_incident",
        description="Finish.",
        execute_in_sandbox=False,
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    config = QuellConfig()
    cmd = IncidentCommander(config)
    cmd.llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>")
    )
    out = await cmd.agent_loop("investigate 500s in /api/checkout")
    assert out["status"] == "completed"
    assert cmd.state is not None
    # First message is the rendered system prompt, which must reference
    # the IncidentCommander's role.
    system_msg = cmd.state.messages[0]
    assert system_msg.role == "system"
    assert "incident_commander" in system_msg.content
    assert "available_tools" in system_msg.content
    assert "finish_incident" in system_msg.content
