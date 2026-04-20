"""Request-scoped context for the tool server.

Uses :class:`contextvars.ContextVar` so the ``agent_id`` extracted by the
auth middleware is available to downstream tool execution code without
threading it through every signature.
"""

from __future__ import annotations

from contextvars import ContextVar

_current_agent_id: ContextVar[str | None] = ContextVar(
    "quell_current_agent_id", default=None
)


def set_current_agent_id(agent_id: str) -> None:
    """Set the agent id bound to the current request."""
    _current_agent_id.set(agent_id)


def get_current_agent_id() -> str | None:
    """Return the agent id bound to the current request (or ``None``)."""
    return _current_agent_id.get()


__all__ = ["set_current_agent_id", "get_current_agent_id"]
