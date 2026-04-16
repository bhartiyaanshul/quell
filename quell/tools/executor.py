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

    Phase 6 stub: if no sandbox URL is configured (sandbox not yet started),
    attempt local execution so that unit tests can exercise sandbox-flagged
    tools without a running Docker container.
    """
    if not sandbox_url or not sandbox_token:
        # Graceful fallback: run locally with a warning note in metadata.
        # In Phase 11 this path will issue an HTTP POST to the tool server.
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

    # Full HTTP dispatch (wired in Phase 11).
    return ToolResult.failure(
        tool_name,
        "Sandbox tool server HTTP dispatch not yet implemented (Phase 11).",
    )


__all__ = ["execute_tool"]
