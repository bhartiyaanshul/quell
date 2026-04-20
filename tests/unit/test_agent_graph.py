"""Tests for Phase 13 — AgentGraph, message broker, and graph tools."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from quell.agents.graph import AgentGraph, get_default_graph, reset_default_graph
from quell.agents.messages import (
    AgentMessageQueue,
    get_default_broker,
    reset_default_broker,
)
from quell.agents.state import AgentState
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.types import LLMResponse, ToolInvocation
from quell.tools.builtins import register_builtin_tools
from quell.tools.executor import execute_tool


@pytest.fixture(autouse=True)
def _reset():  # type: ignore[no-untyped-def]
    register_builtin_tools()
    reset_default_graph()
    reset_default_broker()
    yield
    reset_default_graph()
    reset_default_broker()


# ---------------------------------------------------------------------------
# AgentGraph
# ---------------------------------------------------------------------------


def test_graph_add_and_lookup() -> None:
    g = AgentGraph()
    s = AgentState(name="root", task="t")
    g.add_agent(s)
    assert g.get_agent(s.agent_id) is s
    assert g.get_children(s.agent_id) == []


def test_graph_parent_child_relationship() -> None:
    g = AgentGraph()
    parent = AgentState(name="root", task="root")
    child = AgentState(name="sub", task="sub", parent_id=parent.agent_id)
    g.add_agent(parent)
    g.add_agent(child)
    kids = g.get_children(parent.agent_id)
    assert [c.agent_id for c in kids] == [child.agent_id]


def test_graph_ascii_summary_renders() -> None:
    g = AgentGraph()
    parent = AgentState(name="commander", task="x")
    child = AgentState(name="subagent", task="y", parent_id=parent.agent_id)
    g.add_agent(parent)
    g.add_agent(child)
    summary = g.ascii_summary()
    assert "commander" in summary
    assert "subagent" in summary


def test_graph_mark_completed() -> None:
    g = AgentGraph()
    s = AgentState(name="x", task="y", status=AgentStatus.RUNNING)
    g.add_agent(s)
    g.mark_completed(s.agent_id)
    assert s.status == AgentStatus.COMPLETED


# ---------------------------------------------------------------------------
# AgentMessageQueue
# ---------------------------------------------------------------------------


async def test_broker_send_and_receive() -> None:
    broker = AgentMessageQueue()
    await broker.send("a", "b", "hello")
    env = await broker.receive("b", timeout=1.0)
    assert env is not None
    assert env.from_agent_id == "a"
    assert env.to_agent_id == "b"
    assert env.content == "hello"


async def test_broker_receive_times_out() -> None:
    broker = AgentMessageQueue()
    env = await broker.receive("nobody", timeout=0.05)
    assert env is None


async def test_broker_delivers_in_fifo_order() -> None:
    broker = AgentMessageQueue()
    await broker.send("a", "b", "first")
    await broker.send("a", "b", "second")
    e1 = await broker.receive("b", timeout=0.5)
    e2 = await broker.receive("b", timeout=0.5)
    assert e1 is not None and e2 is not None
    assert (e1.content, e2.content) == ("first", "second")


# ---------------------------------------------------------------------------
# send_message / wait_for_message tools
# ---------------------------------------------------------------------------


async def test_send_and_wait_tools_round_trip() -> None:
    sender = AgentState(name="sender", task="t")
    receiver = AgentState(name="receiver", task="t")

    # Send (as sender)
    send_inv = ToolInvocation(
        name="send_message",
        parameters={"to_agent_id": receiver.agent_id, "message": "ping"},
        raw_xml="",
    )
    send_result = await execute_tool(send_inv, agent_state=sender)
    assert send_result.ok is True

    # Wait (as receiver)
    wait_inv = ToolInvocation(
        name="wait_for_message",
        parameters={"timeout_seconds": "1"},
        raw_xml="",
    )
    wait_result = await execute_tool(wait_inv, agent_state=receiver)
    assert wait_result.ok is True
    assert wait_result.output == "ping"
    assert wait_result.metadata["from"] == sender.agent_id


async def test_wait_for_message_timeout_reported() -> None:
    receiver = AgentState(name="receiver", task="t")
    wait_inv = ToolInvocation(
        name="wait_for_message",
        parameters={"timeout_seconds": "0.05"},
        raw_xml="",
    )
    result = await execute_tool(wait_inv, agent_state=receiver)
    assert result.ok is True
    assert result.metadata["timed_out"] is True


# ---------------------------------------------------------------------------
# view_graph tool
# ---------------------------------------------------------------------------


async def test_view_graph_tool() -> None:
    graph = get_default_graph()
    parent = AgentState(name="commander", task="")
    child = AgentState(name="sub", task="", parent_id=parent.agent_id)
    graph.add_agent(parent)
    graph.add_agent(child)
    inv = ToolInvocation(name="view_graph", parameters={}, raw_xml="")
    result = await execute_tool(inv)
    assert result.ok is True
    assert "commander" in result.output
    assert "sub" in result.output


# ---------------------------------------------------------------------------
# create_agent tool — end-to-end with a mocked subagent LLM
# ---------------------------------------------------------------------------


async def test_create_agent_spawns_background_subagent() -> None:
    from quell.llm.llm import LLM

    # Patch the LLM used by GenericSubagent so it returns agent_finish
    # on the first turn.
    fake_resp = LLMResponse(
        content=(
            "<function=agent_finish>"
            "<parameter=summary>subagent done</parameter>"
            "</function>"
        ),
        model="m",
        input_tokens=0,
        output_tokens=0,
    )

    async def _fake_generate(self, messages, tools=None):  # type: ignore[no-untyped-def]
        return fake_resp

    # Monkeypatch instance method via class
    original = LLM.generate
    LLM.generate = _fake_generate  # type: ignore[method-assign]
    try:
        parent = AgentState(name="commander", task="investigate")
        get_default_graph().add_agent(parent)
        inv = ToolInvocation(
            name="create_agent",
            parameters={"name": "log-reader", "task": "read logs", "skills": ""},
            raw_xml="",
        )
        result = await execute_tool(inv, agent_state=parent)
        assert result.ok is True
        sub_id = str(result.metadata["agent_id"])

        # Wait for the background task to finish.
        handle = get_default_graph().get_task(sub_id)
        assert handle is not None
        await asyncio.wait_for(handle, timeout=5.0)

        # The subagent should have sent its summary back to the parent.
        env = await get_default_broker().receive(parent.agent_id, timeout=1.0)
        assert env is not None
        assert env.from_agent_id == sub_id
    finally:
        LLM.generate = original  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# GenericSubagent integration
# ---------------------------------------------------------------------------


async def test_generic_subagent_renders_task_in_prompt() -> None:
    from quell.agents.subagent import GenericSubagent

    sub = GenericSubagent(
        QuellConfig(),
        name="triage-bot",
        task="Read the last 100 lines of the checkout log.",
    )
    sub.llm.generate = AsyncMock(  # type: ignore[method-assign]
        return_value=LLMResponse(
            content="No tools needed.", model="x", input_tokens=0, output_tokens=0
        )
    )
    out = await sub.agent_loop("Read the last 100 lines of the checkout log.")
    assert out["status"] == "completed"
    assert sub.state is not None
    system = sub.state.messages[0].content
    assert "triage-bot" in system
    assert "Read the last 100 lines" in system
