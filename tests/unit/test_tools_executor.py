"""Tests for quell.tools.executor — dispatch, routing, and error handling."""

from __future__ import annotations

import pytest

from quell.llm.types import ToolInvocation, ToolParameterSpec
from quell.tools.executor import execute_tool
from quell.tools.registry import clear_registry, register_tool
from quell.tools.result import ToolResult


@pytest.fixture(autouse=True)
def _clean() -> None:  # type: ignore[return]
    clear_registry()
    yield
    clear_registry()


# ---------------------------------------------------------------------------
# Basic dispatch
# ---------------------------------------------------------------------------


async def test_execute_known_local_tool() -> None:
    """A local tool runs and returns its result."""

    @register_tool(name="echo", description="Echo input.", execute_in_sandbox=False)
    async def echo(msg: str = "") -> ToolResult:
        return ToolResult.success("echo", msg)

    inv = ToolInvocation(name="echo", parameters={"msg": "hello"}, raw_xml="")
    result = await execute_tool(inv)
    assert result.ok is True
    assert result.output == "hello"


async def test_execute_unknown_tool_returns_failure() -> None:
    """Calling an unregistered tool returns a failure result (never raises)."""
    inv = ToolInvocation(name="ghost", parameters={}, raw_xml="")
    result = await execute_tool(inv)
    assert result.ok is False
    assert "Unknown tool" in result.error


async def test_execute_validation_failure() -> None:
    """Missing required arg yields a failure with a validation message."""

    @register_tool(
        name="read_file",
        description="Read.",
        execute_in_sandbox=False,
        parameters=[ToolParameterSpec(name="path", type="string", description="")],
    )
    async def read_file(path: str) -> ToolResult:
        return ToolResult.success("read_file", path)

    # No parameters supplied — should fail validation
    inv = ToolInvocation(name="read_file", parameters={}, raw_xml="")
    result = await execute_tool(inv)
    assert result.ok is False
    assert "validation" in result.error.lower()


async def test_execute_tool_exception_returns_failure() -> None:
    """An exception inside a tool is caught and returned as a failure."""

    @register_tool(name="boom", description="Explode.", execute_in_sandbox=False)
    async def boom() -> ToolResult:
        raise RuntimeError("unexpected crash")

    inv = ToolInvocation(name="boom", parameters={}, raw_xml="")
    result = await execute_tool(inv)
    assert result.ok is False
    assert "unexpected crash" in result.error


# ---------------------------------------------------------------------------
# Type coercion via executor
# ---------------------------------------------------------------------------


async def test_execute_coerces_integer_arg() -> None:
    """Executor coerces string '5' to integer 5 before calling the tool."""
    received: list[object] = []

    @register_tool(
        name="count",
        description="Count.",
        execute_in_sandbox=False,
        parameters=[ToolParameterSpec(name="n", type="integer", description="")],
    )
    async def count(n: int = 0) -> ToolResult:
        received.append(n)
        return ToolResult.success("count", str(n))

    inv = ToolInvocation(name="count", parameters={"n": "7"}, raw_xml="")
    await execute_tool(inv)
    assert received == [7]


# ---------------------------------------------------------------------------
# Sandbox routing stub
# ---------------------------------------------------------------------------


async def test_execute_sandbox_tool_without_sandbox_runs_locally() -> None:
    """Phase-6 stub: sandbox tool falls back to local execution gracefully."""

    @register_tool(
        name="sandbox_op",
        description="Needs sandbox.",
        execute_in_sandbox=True,  # sandbox-flagged
    )
    async def sandbox_op() -> ToolResult:
        return ToolResult.success("sandbox_op", "ran locally")

    inv = ToolInvocation(name="sandbox_op", parameters={}, raw_xml="")
    # No sandbox_url or sandbox_token → local fallback
    result = await execute_tool(inv, sandbox_url=None, sandbox_token=None)
    assert result.ok is True
    assert result.metadata.get("_ran_locally") is True


async def test_execute_sandbox_tool_with_url_returns_stub_failure() -> None:
    """When a sandbox URL is provided (Phase 11 not wired), returns a stub failure."""

    @register_tool(
        name="remote_op",
        description="Remote.",
        execute_in_sandbox=True,
    )
    async def remote_op() -> ToolResult:
        return ToolResult.success("remote_op", "would run remotely")

    inv = ToolInvocation(name="remote_op", parameters={}, raw_xml="")
    result = await execute_tool(
        inv,
        sandbox_url="http://localhost:48081",
        sandbox_token="tok",
    )
    assert result.ok is False
    assert "Phase 11" in result.error


# ---------------------------------------------------------------------------
# agent_state injection
# ---------------------------------------------------------------------------


async def test_execute_injects_agent_state_when_requested() -> None:
    """Tools that declare needs_agent_state=True receive it as a kwarg."""
    received_state: list[object] = []

    @register_tool(
        name="stateful",
        description="Needs state.",
        execute_in_sandbox=False,
        needs_agent_state=True,
    )
    async def stateful(agent_state: object = None) -> ToolResult:
        received_state.append(agent_state)
        return ToolResult.success("stateful", "ok")

    inv = ToolInvocation(name="stateful", parameters={}, raw_xml="")
    sentinel = object()
    await execute_tool(inv, agent_state=sentinel)
    assert received_state == [sentinel]


async def test_execute_does_not_inject_state_when_not_requested() -> None:
    """Tools with needs_agent_state=False never receive agent_state."""
    received_kwargs: list[dict[str, object]] = []

    @register_tool(
        name="stateless",
        description="No state.",
        execute_in_sandbox=False,
        needs_agent_state=False,
    )
    async def stateless(**kwargs: object) -> ToolResult:
        received_kwargs.append(dict(kwargs))
        return ToolResult.success("stateless", "ok")

    inv = ToolInvocation(name="stateless", parameters={}, raw_xml="")
    await execute_tool(inv, agent_state=object())
    assert "agent_state" not in received_kwargs[0]
