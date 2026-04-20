"""Shared type definitions for the Quell agent layer.

Cross-module communication in the agent subsystem flows through the types
defined here.  Only :class:`AgentStatus` is consumed by the Phase 7 loop;
:class:`AgentMessage` and :class:`ToolObservation` are pre-staged for the
Phase 14 database persistence layer.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    """Lifecycle state of an agent.

    * ``IDLE``      — constructed but the loop has not started.
    * ``RUNNING``   — the loop is iterating.
    * ``WAITING``   — subagent waiting to be resumed (Phase 13).
    * ``COMPLETED`` — the agent called a finish tool or returned cleanly.
    * ``FAILED``    — the loop aborted due to an error or iteration cap.
    """

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


def _now() -> datetime:
    """UTC-aware current timestamp (mirrors ``quell.memory`` pattern)."""
    return datetime.now(UTC)


class AgentMessage(BaseModel):
    """A persisted snapshot of one message produced during an agent run.

    Used by the Phase 14 DB persistence layer to write ``Event`` rows.
    Phase 7 does not consume this model directly.
    """

    iteration: int
    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=_now)


class ToolObservation(BaseModel):
    """A persisted snapshot of one tool execution during an agent run.

    Used by the Phase 14 DB persistence layer to write ``Event`` rows.
    Phase 7 does not consume this model directly.
    """

    iteration: int
    tool_name: str
    ok: bool
    output: str = ""
    error: str = ""
    timestamp: datetime = Field(default_factory=_now)


__all__ = [
    "AgentStatus",
    "AgentMessage",
    "ToolObservation",
]
