"""Smoke tests for the Phase 12 built-in tool families."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from quell.llm.types import ToolInvocation
from quell.tools.builtins import register_builtin_tools
from quell.tools.executor import execute_tool
from quell.tools.registry import get_tool


@pytest.fixture(autouse=True)
def _bootstrap_builtins():  # type: ignore[no-untyped-def]
    """Ensure every built-in tool is (re-)registered before each test.

    Other test modules call ``clear_registry()`` in their own autouse
    fixtures; this fixture restores the built-ins when control returns.
    """
    register_builtin_tools()
    yield


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "hello.py").write_text(
        "def greet(name):\n    return f'hi {name}'\n", encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Tool registration is side-effecting; preserve existing state across tests
# by re-importing the modules in a scoped fixture. The production code
# registers once at import time, so we patch the workspace root where
# relevant rather than tearing down the registry.
# ---------------------------------------------------------------------------


def test_code_read_returns_file_slice(workspace: Path) -> None:
    with patch("quell.tools.code.read._WORKSPACE_ROOT", workspace):
        entry = get_tool("code_read")
        assert entry is not None

    async def _run() -> None:
        inv = ToolInvocation(
            name="code_read",
            parameters={"path": "hello.py", "start_line": "1", "end_line": "2"},
            raw_xml="",
        )
        with patch("quell.tools.code.read._WORKSPACE_ROOT", workspace):
            result = await execute_tool(inv)
        assert result.ok is True, result.error
        assert "def greet" in result.output

    import asyncio

    asyncio.run(_run())


def test_code_read_rejects_path_traversal(workspace: Path) -> None:
    async def _run() -> None:
        inv = ToolInvocation(
            name="code_read",
            parameters={"path": "../../etc/passwd"},
            raw_xml="",
        )
        with patch("quell.tools.code.read._WORKSPACE_ROOT", workspace):
            result = await execute_tool(inv)
        assert result.ok is False
        assert "escapes workspace" in result.error

    import asyncio

    asyncio.run(_run())


async def test_logs_query_filters_by_substring(tmp_path: Path) -> None:
    log = tmp_path / "app.log"
    log.write_text(
        "\n".join(
            [
                "INFO server started",
                "ERROR stripe-signature missing",
                "INFO heartbeat",
                "ERROR stripe-signature invalid",
            ]
        ),
        encoding="utf-8",
    )
    inv = ToolInvocation(
        name="logs_query",
        parameters={"path": str(log), "contains": "stripe", "limit": "10"},
        raw_xml="",
    )
    result = await execute_tool(inv)
    assert result.ok is True
    assert "stripe-signature missing" in result.output
    assert "heartbeat" not in result.output


async def test_incident_report_tool_renders() -> None:
    inv = ToolInvocation(
        name="create_incident_report",
        parameters={
            "title": "Checkout 500s",
            "root_cause": "null deref",
            "evidence": "logs",
            "proposed_fix": "null-check",
            "severity": "high",
        },
        raw_xml="",
    )
    result = await execute_tool(inv)
    assert result.ok is True
    assert "# Checkout 500s" in result.output
    assert "null deref" in result.output
    assert result.metadata["severity"] == "high"


async def test_postmortem_tool_renders() -> None:
    inv = ToolInvocation(
        name="create_postmortem",
        parameters={
            "title": "Stripe outage",
            "summary": "Webhook timed out for 5 min",
            "impact": "2% of checkouts failed",
            "timeline": "12:00 first alert\n12:03 triage started",
            "root_cause": "DB lock contention",
            "resolution": "Added index on orders.customer_id",
            "action_items": "Move webhook processing off the hot path",
        },
        raw_xml="",
    )
    result = await execute_tool(inv)
    assert result.ok is True
    assert "## Timeline" in result.output
    assert "# Stripe outage" in result.output


async def test_agent_finish_tool_produces_metadata() -> None:
    inv = ToolInvocation(
        name="agent_finish",
        parameters={"summary": "logs gathered", "findings": "3 unique signatures"},
        raw_xml="",
    )
    result = await execute_tool(inv)
    assert result.ok is True
    assert result.output == "logs gathered"
    assert result.metadata["findings"] == "3 unique signatures"


async def test_finish_incident_tool_populates_metadata() -> None:
    inv = ToolInvocation(
        name="finish_incident",
        parameters={
            "root_cause": "null deref",
            "evidence": "checkout.py:42",
            "proposed_fix": "guard None",
        },
        raw_xml="",
    )
    result = await execute_tool(inv)
    assert result.ok is True
    assert result.metadata["root_cause"] == "null deref"
    assert result.metadata["status"] == "resolved"


def test_all_phase12_tools_registered() -> None:
    expected = {
        "code_read",
        "code_grep",
        "git_log",
        "git_blame",
        "git_diff",
        "logs_query",
        "http_probe",
        "create_incident_report",
        "create_postmortem",
        "agent_finish",
        "finish_incident",
    }
    for name in expected:
        assert get_tool(name) is not None, f"Tool {name!r} missing from registry"


def test_register_builtin_tools_is_idempotent() -> None:
    # Calling it again must not raise even though the registrations exist.
    register_builtin_tools()
    register_builtin_tools()
    assert get_tool("code_read") is not None
