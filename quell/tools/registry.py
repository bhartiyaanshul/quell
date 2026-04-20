"""Tool registry — ``@register_tool`` decorator and global lookup.

Every Quell tool is a plain async function decorated with
:func:`register_tool`.  The decorator stores the function and its metadata
in the module-level ``_REGISTRY`` dict so the executor can look it up by
name at call time.

Example::

    from quell.tools.registry import register_tool
    from quell.tools.result import ToolResult

    @register_tool(
        name="ping",
        description="Return a simple pong response.",
        parameters=[],
        execute_in_sandbox=False,
    )
    async def ping() -> ToolResult:
        return ToolResult.success("ping", "pong")
"""

from __future__ import annotations

import functools
from collections.abc import Callable, Coroutine
from typing import Any

from quell.llm.types import ToolMetadata, ToolParameterSpec
from quell.tools.result import ToolResult
from quell.utils.errors import ToolError

# ---------------------------------------------------------------------------
# Internal registry storage
# ---------------------------------------------------------------------------

# Maps tool name → (async function, ToolMetadata)
_REGISTRY: dict[
    str, tuple[Callable[..., Coroutine[Any, Any, ToolResult]], ToolMetadata]
] = {}


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def register_tool(
    *,
    name: str,
    description: str,
    parameters: list[ToolParameterSpec] | None = None,
    execute_in_sandbox: bool = True,
    needs_agent_state: bool = False,
) -> Callable[
    [Callable[..., Coroutine[Any, Any, ToolResult]]],
    Callable[..., Coroutine[Any, Any, ToolResult]],
]:
    """Decorator that registers an async tool function in the global registry.

    Args:
        name:               Unique tool name (used in XML ``<function=name>`` tags).
        description:        One-sentence description shown in the tool catalogue.
        parameters:         List of :class:`~quell.llm.types.ToolParameterSpec`.
        execute_in_sandbox: When ``True`` the executor routes this tool to the
                            sandbox tool server instead of running it locally.
        needs_agent_state:  When ``True`` the executor injects the current agent
                            state as the first keyword argument ``agent_state``.

    Returns:
        A no-op decorator that registers the function and returns it unchanged.

    Raises:
        :exc:`~quell.utils.errors.ToolError`: If *name* is already registered.
    """
    metadata = ToolMetadata(
        name=name,
        description=description,
        parameters=parameters or [],
        execute_in_sandbox=execute_in_sandbox,
        needs_agent_state=needs_agent_state,
    )

    def decorator(
        fn: Callable[..., Coroutine[Any, Any, ToolResult]],
    ) -> Callable[..., Coroutine[Any, Any, ToolResult]]:
        if name in _REGISTRY:
            raise ToolError(f"Tool {name!r} is already registered.")
        _REGISTRY[name] = (fn, metadata)
        functools.update_wrapper(fn, fn)
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_tool(
    name: str,
) -> tuple[Callable[..., Coroutine[Any, Any, ToolResult]], ToolMetadata] | None:
    """Return ``(fn, metadata)`` for *name*, or ``None`` if not registered."""
    return _REGISTRY.get(name)


def list_tools() -> list[ToolMetadata]:
    """Return metadata for every registered tool, sorted by name."""
    return [meta for _, (__, meta) in sorted(_REGISTRY.items())]


def clear_registry() -> None:
    """Remove all registered tools.  Intended for use in tests only."""
    _REGISTRY.clear()


def unregister_tool(name: str) -> None:
    """Remove a single tool from the registry if present.

    Used by the built-in bootstrap to re-run ``@register_tool`` decorators
    after a ``clear_registry()`` call in another test module.
    """
    _REGISTRY.pop(name, None)


__all__ = [
    "register_tool",
    "get_tool",
    "list_tools",
    "clear_registry",
    "unregister_tool",
]
