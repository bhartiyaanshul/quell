"""Tool server — ``POST /execute``.

Receives a tool invocation from the host-side agent loop, dispatches it
through the shared :func:`~quell.tools.executor.execute_tool`, and
returns a JSON-encoded :class:`~quell.tools.result.ToolResult`.

The server runs *inside* the sandbox, so when the executor checks
``_in_sandbox()`` it sees ``True`` and runs the tool locally.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from quell.llm.types import ToolInvocation
from quell.tool_server.context import set_current_agent_id
from quell.tools.executor import execute_tool

router = APIRouter()


class ExecuteRequest(BaseModel):
    """Request body for ``POST /execute``."""

    tool_name: str
    args: dict[str, str]
    agent_id: str


class ExecuteResponse(BaseModel):
    """Response body — a serialised ``ToolResult``."""

    tool_name: str
    ok: bool
    output: str
    error: str
    metadata: dict[str, object]
    truncated: bool


@router.post("/execute", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest) -> ExecuteResponse:
    """Dispatch a tool call inside the sandbox and return its result."""
    set_current_agent_id(req.agent_id)
    invocation = ToolInvocation(
        name=req.tool_name,
        parameters=req.args,
        raw_xml="",
    )
    result = await execute_tool(invocation)
    return ExecuteResponse(
        tool_name=result.tool_name,
        ok=result.ok,
        output=result.output,
        error=result.error,
        metadata=dict(result.metadata),
        truncated=result.truncated,
    )


__all__ = ["router", "ExecuteRequest", "ExecuteResponse"]
