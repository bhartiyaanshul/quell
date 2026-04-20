"""Tool executor — dispatches tool invocations to local functions or the
sandbox tool server.

:func:`execute_tool` is the single entry point.  It:

1. Looks up the tool in the registry.
2. Validates and coerces arguments via :mod:`~quell.tools.arguments`.
3. Routes to the sandbox tool server (HTTP POST) when ``execute_in_sandbox``
   is ``True`` **and** we are not already running inside the sandbox.
4. Runs locally otherwise.
5. Applies the 50 KB output size cap via
   :meth:`~quell.tools.result.ToolResult.truncate`.

The sandbox routing path is a stub in Phase 6 — it returns a placeholder
``ToolResult`` so that tools that require sandbox execution fail gracefully
with a clear message rather than crashing.  The real HTTP dispatch is wired
up in Phase 11 (Docker runtime + tool server).
"""

from __future__ import annotations

import os
from collections.abc import Callable, Coroutine
from typing import Any

import httpx

from quell.llm.types import ToolInvocation
from quell.tools.arguments import coerce_arguments
from quell.tools.registry import get_tool
from quell.tools.result import ToolResult

# Environment variable set by the tool server inside the sandbox container.
_SANDBOX_ENV_VAR = "QUELL_INSIDE_SANDBOX"


def _in_sandbox() -> bool:
    """Return ``True`` when this process is running inside the sandbox."""
    return os.environ.get(_SANDBOX_ENV_VAR, "").lower() in {"1", "true", "yes"}


async def execute_tool(
    invocation: ToolInvocation,
    *,
    agent_state: object | None = None,
    sandbox_url: str | None = None,
    sandbox_token: str | None = None,
) -> ToolResult:
    """Dispatch *invocation* and return its :class:`~quell.tools.result.ToolResult`.

    Args:
        invocation:     The parsed tool invocation from the LLM response.
        agent_state:    Current agent state, injected if the tool requests it.
        sandbox_url:    Base URL of the sandbox tool server
                        (e.g. ``"http://localhost:48081"``).
        sandbox_token:  Bearer token for the sandbox tool server.

    Returns:
        :class:`~quell.tools.result.ToolResult` (always — never raises).
    """
    entry = get_tool(invocation.name)
    if entry is None:
        return ToolResult.failure(
            invocation.name,
            f"Unknown tool: {invocation.name!r}. "
            "Check the available_tools list in your system prompt.",
        )

    fn, metadata = entry

    # Validate + coerce arguments
    coerced, errors = coerce_arguments(invocation.parameters, metadata)
    if errors:
        return ToolResult.failure(
            invocation.name,
            "Argument validation failed:\n" + "\n".join(f"  • {e}" for e in errors),
        )

    # Route: sandbox vs local
    if metadata.execute_in_sandbox and not _in_sandbox():
        return await _execute_via_sandbox(
            invocation.name,
            coerced,
            fn,
            sandbox_url=sandbox_url,
            sandbox_token=sandbox_token,
            agent_state=agent_state if metadata.needs_agent_state else None,
        )

    return await _execute_locally(fn, invocation.name, coerced, agent_state, metadata)


# ---------------------------------------------------------------------------
# Internal dispatch helpers
# ---------------------------------------------------------------------------


async def _execute_locally(
    fn: Callable[..., Coroutine[Any, Any, ToolResult]],
    tool_name: str,
    kwargs: dict[str, object],
    agent_state: object | None,
    metadata: Any,  # noqa: ANN401 — ToolMetadata imported lazily to avoid cycles
) -> ToolResult:
    """Call *fn* directly in this process and cap the output size."""
    try:
        if metadata.needs_agent_state and agent_state is not None:
            result: ToolResult = await fn(agent_state=agent_state, **kwargs)
        else:
            result = await fn(**kwargs)
    except Exception as exc:  # noqa: BLE001
        return ToolResult.failure(tool_name, f"Tool raised an exception: {exc}")
    return result.truncate()


async def _execute_via_sandbox(
    tool_name: str,
    kwargs: dict[str, object],
    fn: Callable[..., Coroutine[Any, Any, ToolResult]],
    *,
    sandbox_url: str | None,
    sandbox_token: str | None,
    agent_state: object | None,
) -> ToolResult:
    """Route a sandbox tool call to the tool server, or fall back locally.

    When ``sandbox_url`` / ``sandbox_token`` are not configured (e.g. unit
    tests running without Docker) the tool is executed locally and a
    ``_ran_locally`` flag is added to the result metadata.

    When configured, the call is POSTed to the tool server inside the
    sandbox, which runs the tool and returns a serialised ``ToolResult``.
    """
    if not sandbox_url or not sandbox_token:
        # Graceful fallback: run locally with a note in metadata.
        try:
            result: ToolResult = await fn(**kwargs)
            return ToolResult(
                tool_name=result.tool_name,
                ok=result.ok,
                output=result.output,
                error=result.error,
                metadata={**result.metadata, "_ran_locally": True},
                truncated=result.truncated,
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult.failure(
                tool_name,
                f"Sandbox tool ran locally and raised: {exc}",
            )

    agent_id = getattr(agent_state, "agent_id", "") if agent_state else ""
    # The tool server expects all arg values as strings — coerce back from
    # typed to string for wire transport; the server re-coerces per tool
    # metadata on the other side.
    str_args = {k: _stringify(v) for k, v in kwargs.items()}
    payload: dict[str, object] = {
        "tool_name": tool_name,
        "args": str_args,
        "agent_id": agent_id,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{sandbox_url.rstrip('/')}/execute",
                json=payload,
                headers={"Authorization": f"Bearer {sandbox_token}"},
            )
    except httpx.HTTPError as exc:
        return ToolResult.failure(tool_name, f"Sandbox tool server HTTP error: {exc}")

    if resp.status_code != 200:
        return ToolResult.failure(
            tool_name,
            f"Sandbox tool server returned HTTP {resp.status_code}: {resp.text[:200]}",
        )

    data = resp.json()
    return ToolResult(
        tool_name=str(data.get("tool_name", tool_name)),
        ok=bool(data.get("ok", False)),
        output=str(data.get("output", "")),
        error=str(data.get("error", "")),
        metadata=dict(data.get("metadata", {})),
        truncated=bool(data.get("truncated", False)),
    )


def _stringify(value: object) -> str:
    """Convert a coerced argument back to its string wire form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["execute_tool"]
