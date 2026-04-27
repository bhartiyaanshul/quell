"""AgentState — the mutable, per-run state carried by every agent.

:class:`AgentState` is a Pydantic v2 model so callers can snapshot it with
``model_copy()`` and serialize it with ``model_dump()`` for persistence.

The :attr:`AgentState.messages` list holds :class:`~quell.llm.types.LLMMessage`
instances (a stdlib ``@dataclass``).  Because Pydantic v2 does not introspect
arbitrary dataclasses by default, the model opts into
``arbitrary_types_allowed=True`` — validation for those entries is therefore
structural, not deep.  All other fields are validated normally.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from quell.agents.types import AgentStatus
from quell.llm.types import LLMMessage


def _now() -> datetime:
    """UTC-aware current timestamp."""
    return datetime.now(UTC)


def _new_id() -> str:
    """Generate a fresh UUID4 string for ``agent_id``."""
    return str(uuid4())


class AgentState(BaseModel):
    """Mutable per-run state for a single agent.

    Attributes:
        agent_id:       UUID4 string identifying this agent.
        parent_id:      ``None`` for a root agent, set to the parent's
                        ``agent_id`` for subagents (Phase 13).
        name:           Human-readable agent role (e.g. ``"incident_commander"``).
        task:           Initial task description given to the agent.
        status:         Current lifecycle state.
        messages:       Full conversation history (system, user, assistant,
                        and tool-observation messages).
        iteration:      Current loop iteration; incremented after each
                        tool-executing turn.
        max_iterations: Safety cap — the loop transitions to ``FAILED`` when
                        this value is reached.
        errors:         Accumulated error messages.
        sandbox_url:    Base URL of the Docker sandbox tool server (Phase 11).
        sandbox_token:  Bearer token for the sandbox tool server (Phase 11).
        final_result:   Structured result produced by a finish tool.
        created_at:     UTC timestamp of construction.
        updated_at:     UTC timestamp of the last state mutation — call
                        :meth:`touch` to refresh.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str = Field(default_factory=_new_id)
    parent_id: str | None = None
    name: str
    task: str
    status: AgentStatus = AgentStatus.IDLE
    messages: list[LLMMessage] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 50
    errors: list[str] = Field(default_factory=list)
    sandbox_url: str | None = None
    sandbox_token: str | None = None
    final_result: dict[str, object] | None = None

    # v0.2 — rolling token + cost totals updated by the agent loop.
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    def touch(self) -> None:
        """Refresh :attr:`updated_at` to the current UTC timestamp.

        The agent loop calls this after every mutation that would otherwise
        leave ``updated_at`` stale.
        """
        self.updated_at = _now()

    def cost_so_far(self) -> float:
        """Convenience alias for :attr:`estimated_cost_usd`."""
        return self.estimated_cost_usd


__all__ = ["AgentState"]
