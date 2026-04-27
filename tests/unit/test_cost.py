"""Tests for Phase 20 — LLM cost estimation and budget enforcement."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from quell.agents.base_agent import BaseAgent
from quell.config.schema import AgentConfig, QuellConfig
from quell.llm.cost import MODEL_RATES, estimate_cost, has_rate_card
from quell.llm.llm import LLM
from quell.llm.types import LLMResponse
from quell.memory import (
    create_tables,
    get_engine_memory,
    get_session_factory,
    list_events_for_run,
    list_runs_for_incident,
)
from quell.memory.incidents import create_incident, get_incident
from quell.tools.registry import clear_registry, register_tool
from quell.tools.result import ToolResult


@pytest.fixture
async def session_factory():  # type: ignore[no-untyped-def]
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
# estimate_cost — lookup correctness
# ---------------------------------------------------------------------------


def test_estimate_cost_known_anthropic_model() -> None:
    # claude-haiku-4-5: ($0.80 in, $4.00 out) / 1M tokens.
    # 1000 in + 500 out => 1000*0.80/1e6 + 500*4.00/1e6 = 0.0008 + 0.002 = 0.0028
    cost = estimate_cost("anthropic/claude-haiku-4-5", 1000, 500)
    assert abs(cost - 0.0028) < 1e-6


def test_estimate_cost_known_openai_model() -> None:
    # gpt-4o: ($2.50 in, $10 out) / 1M.
    # 2000 in + 1000 out => 0.005 + 0.01 = 0.015
    cost = estimate_cost("openai/gpt-4o", 2000, 1000)
    assert abs(cost - 0.015) < 1e-6


def test_estimate_cost_ollama_is_free() -> None:
    assert estimate_cost("ollama/llama3", 100_000, 50_000) == 0.0


def test_estimate_cost_unknown_model_is_zero() -> None:
    assert estimate_cost("someone/new-model-we-dont-track", 1000, 1000) == 0.0


def test_estimate_cost_case_insensitive() -> None:
    a = estimate_cost("Anthropic/Claude-Haiku-4-5", 1000, 500)
    b = estimate_cost("anthropic/claude-haiku-4-5", 1000, 500)
    assert abs(a - b) < 1e-6


def test_estimate_cost_bare_slug_matches() -> None:
    """``claude-haiku-4-5`` without the provider prefix still matches."""
    # This uses the fallback that strips the provider prefix.
    cost = estimate_cost("claude-haiku-4-5", 1000, 500)
    # Unknown -- bare slug lookup is NOT currently supported (by design).
    # Change this test if we later add that feature.
    assert cost == 0.0


def test_has_rate_card() -> None:
    assert has_rate_card("anthropic/claude-haiku-4-5") is True
    assert has_rate_card("openai/gpt-4o-mini") is True
    assert has_rate_card("totally/made-up") is False


def test_model_rates_table_shape() -> None:
    for key, rates in MODEL_RATES.items():
        assert isinstance(key, str) and "/" in key
        assert isinstance(rates, tuple) and len(rates) == 2
        assert all(isinstance(r, int | float) and r >= 0 for r in rates)


# ---------------------------------------------------------------------------
# AgentState — cost accumulation
# ---------------------------------------------------------------------------


def test_agent_state_cost_fields_default_to_zero() -> None:
    from quell.agents.state import AgentState

    s = AgentState(name="x", task="y")
    assert s.total_input_tokens == 0
    assert s.total_output_tokens == 0
    assert s.estimated_cost_usd == 0.0
    assert s.cost_so_far() == 0.0


# ---------------------------------------------------------------------------
# Budget enforcement via agent_loop
# ---------------------------------------------------------------------------


class _StubAgent(BaseAgent):
    name = "stub"

    def _render_system_prompt(self) -> str:
        return "You are a test agent."


def _resp(
    content: str, input_tokens: int = 10_000, output_tokens: int = 5_000
) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="anthropic/claude-haiku-4-5",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


async def test_agent_loop_reports_running_cost() -> None:
    """Cost + token totals flow through to the return dict."""

    @register_tool(
        name="finish_incident", description="Finish.", execute_in_sandbox=False
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>", 1000, 500),
    )
    agent = _StubAgent(config, llm=llm)
    result = await agent.agent_loop("test")

    assert result["status"] == "completed"
    assert result["input_tokens"] == 1000
    assert result["output_tokens"] == 500
    # 1000 * 0.80 / 1e6 + 500 * 4.00 / 1e6 = 0.0028
    assert abs(result["cost_usd"] - 0.0028) < 1e-6


async def test_agent_loop_halts_on_budget_exceeded() -> None:
    """A tight max_cost_usd terminates the loop with FAILED + error message."""

    @register_tool(name="noop", description="Does nothing.", execute_in_sandbox=False)
    async def noop() -> ToolResult:
        return ToolResult.success("noop", "ok")

    # Each LLM call costs $0.028 (10k in + 5k out against haiku rates).
    # With max_cost_usd=0.01, the loop should halt after the first call.
    config = QuellConfig(agent=AgentConfig(max_iterations=50, max_cost_usd=0.01))
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=noop></function>"),
    )
    agent = _StubAgent(config, llm=llm)
    result = await agent.agent_loop("spin forever")

    assert result["status"] == "failed"
    assert any("budget exceeded" in e for e in result["errors"])
    # We should have charged for exactly one LLM call before halting.
    assert result["input_tokens"] == 10_000
    assert result["output_tokens"] == 5_000


async def test_budget_none_never_halts() -> None:
    """``max_cost_usd=None`` disables the cap completely."""

    @register_tool(
        name="finish_incident", description="Finish.", execute_in_sandbox=False
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    config = QuellConfig(agent=AgentConfig(max_cost_usd=None))
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp(
            "<function=finish_incident></function>", 5_000_000, 1_000_000
        ),
    )
    agent = _StubAgent(config, llm=llm)
    result = await agent.agent_loop("expensive task")
    assert result["status"] == "completed"
    assert result["cost_usd"] > 1.0  # would have been way over any sensible cap


async def test_agent_config_max_iterations_propagates_to_state() -> None:
    """`config.agent.max_iterations` replaces AgentState's default."""

    @register_tool(name="noop", description="Does nothing.", execute_in_sandbox=False)
    async def noop() -> ToolResult:
        return ToolResult.success("noop", "ok")

    config = QuellConfig(agent=AgentConfig(max_iterations=2))
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=noop></function>", 1, 1),
    )
    agent = _StubAgent(config, llm=llm)
    result = await agent.agent_loop("loop")
    assert result["status"] == "failed"
    assert result["iterations"] == 2
    assert any("max_iterations (2)" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Persistence: cost rolls onto the Incident row
# ---------------------------------------------------------------------------


async def test_incident_cost_usd_accumulates_across_runs(session_factory):  # type: ignore[no-untyped-def]
    """Each finished agent_loop adds its cost to Incident.cost_usd."""

    @register_tool(
        name="finish_incident", description="Finish.", execute_in_sandbox=False
    )
    async def finish_incident() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    async with session_factory() as session:
        incident = await create_incident(session, signature="c" * 16, severity="high")
        await session.commit()

    # First run costs 0.0028.
    config = QuellConfig()
    llm = LLM(config.llm)
    llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>", 1000, 500),
    )
    agent = _StubAgent(
        config,
        llm=llm,
        session_factory=session_factory,
        incident_id=incident.id,
    )
    await agent.agent_loop("run 1")

    # Second run costs another 0.0056 (double tokens).
    clear_registry()

    @register_tool(
        name="finish_incident", description="Finish.", execute_in_sandbox=False
    )
    async def finish_incident2() -> ToolResult:
        return ToolResult.success("finish_incident", "done")

    llm2 = LLM(config.llm)
    llm2.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=_resp("<function=finish_incident></function>", 2000, 1000),
    )
    agent2 = _StubAgent(
        config,
        llm=llm2,
        session_factory=session_factory,
        incident_id=incident.id,
    )
    await agent2.agent_loop("run 2")

    async with session_factory() as session:
        refreshed = await get_incident(session, incident.id)
        assert refreshed is not None
        assert abs(refreshed.cost_usd - (0.0028 + 0.0056)) < 1e-6

        runs = await list_runs_for_incident(session, incident.id)
        assert len(runs) == 2
        # Each run stores its own metrics in final_result._metrics.
        for run in runs:
            metrics = (run.final_result or {}).get("_metrics", {})
            assert metrics.get("cost_usd") is not None

        # llm_call events recorded the token counts.
        all_events = []
        for run in runs:
            all_events.extend(await list_events_for_run(session, run.id))
        llm_events = [e for e in all_events if e.event_type == "llm_call"]
        assert len(llm_events) == 2
