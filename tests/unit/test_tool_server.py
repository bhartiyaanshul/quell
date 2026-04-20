"""Tests for quell.tool_server — FastAPI app running inside the sandbox."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from quell.tool_server import create_app
from quell.tool_server.routes.register import clear_registered, is_registered
from quell.tools.registry import clear_registry, register_tool
from quell.tools.result import ToolResult

_TOKEN = "test-bearer-token"
_AUTH = {"Authorization": f"Bearer {_TOKEN}"}


@pytest.fixture(autouse=True)
def _clean():  # type: ignore[no-untyped-def]
    clear_registry()
    clear_registered()
    yield
    clear_registry()
    clear_registered()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(_TOKEN))


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_ok_without_auth(client: TestClient) -> None:
    # /health must be reachable without a bearer token so the runtime
    # can probe readiness.
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def test_execute_requires_bearer_token(client: TestClient) -> None:
    resp = client.post("/execute", json={"tool_name": "x", "args": {}, "agent_id": "a"})
    assert resp.status_code == 401


def test_execute_rejects_wrong_token(client: TestClient) -> None:
    resp = client.post(
        "/execute",
        json={"tool_name": "x", "args": {}, "agent_id": "a"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /register_agent
# ---------------------------------------------------------------------------


def test_register_agent_records_id(client: TestClient) -> None:
    resp = client.post("/register_agent", json={"agent_id": "agent-42"}, headers=_AUTH)
    assert resp.status_code == 200
    assert resp.json()["agent_id"] == "agent-42"
    assert is_registered("agent-42")


# ---------------------------------------------------------------------------
# /execute
# ---------------------------------------------------------------------------


def test_execute_dispatches_known_tool(client: TestClient) -> None:
    @register_tool(name="echo", description="Echo a message.", execute_in_sandbox=False)
    async def echo(msg: str = "") -> ToolResult:
        return ToolResult.success("echo", f"got:{msg}")

    resp = client.post(
        "/execute",
        json={"tool_name": "echo", "args": {"msg": "hi"}, "agent_id": "a"},
        headers=_AUTH,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["output"] == "got:hi"
    assert body["tool_name"] == "echo"


def test_execute_unknown_tool_returns_failure(client: TestClient) -> None:
    resp = client.post(
        "/execute",
        json={"tool_name": "does_not_exist", "args": {}, "agent_id": "a"},
        headers=_AUTH,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "Unknown tool" in body["error"]


def test_execute_argument_validation_fails_cleanly(client: TestClient) -> None:
    from quell.llm.types import ToolParameterSpec

    @register_tool(
        name="strict",
        description="Needs a required int.",
        parameters=[
            ToolParameterSpec(
                name="limit", type="integer", description="", required=True
            )
        ],
        execute_in_sandbox=False,
    )
    async def strict(limit: int) -> ToolResult:
        return ToolResult.success("strict", f"ok:{limit}")

    resp = client.post(
        "/execute",
        json={"tool_name": "strict", "args": {}, "agent_id": "a"},
        headers=_AUTH,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "validation failed" in body["error"].lower()
