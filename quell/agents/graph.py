"""AgentGraph — in-process registry of agents + their parent/child links.

A single :class:`AgentGraph` lives in the process that runs the root
:class:`~quell.agents.incident_commander.IncidentCommander`.  When the
commander calls ``create_agent`` (Phase 13 tool) the graph records the
new subagent's :class:`~quell.agents.state.AgentState`, starts its
``agent_loop`` on a background ``asyncio.Task``, and makes the handle
available so the commander can query progress or wait for the result.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from quell.agents.state import AgentState
from quell.agents.types import AgentStatus


@dataclass
class _AgentRecord:
    state: AgentState
    task: asyncio.Task[object] | None = None


@dataclass
class AgentGraph:
    """Registry of all agents running in the current process."""

    _records: dict[str, _AgentRecord] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_agent(
        self,
        state: AgentState,
        task: asyncio.Task[object] | None = None,
    ) -> None:
        """Register *state* (and its background task) in the graph."""
        self._records[state.agent_id] = _AgentRecord(state=state, task=task)

    def attach_task(self, agent_id: str, task: asyncio.Task[object]) -> None:
        """Bind a background task to an already-registered agent."""
        rec = self._records.get(agent_id)
        if rec is not None:
            rec.task = task

    def mark_completed(self, agent_id: str) -> None:
        """Advance *agent_id* to ``COMPLETED`` (no-op if unknown)."""
        rec = self._records.get(agent_id)
        if rec is not None:
            rec.state.status = AgentStatus.COMPLETED

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_agent(self, agent_id: str) -> AgentState | None:
        rec = self._records.get(agent_id)
        return rec.state if rec is not None else None

    def get_task(self, agent_id: str) -> asyncio.Task[object] | None:
        rec = self._records.get(agent_id)
        return rec.task if rec is not None else None

    def get_children(self, parent_id: str) -> list[AgentState]:
        return [
            rec.state
            for rec in self._records.values()
            if rec.state.parent_id == parent_id
        ]

    def all_agents(self) -> list[AgentState]:
        return [rec.state for rec in self._records.values()]

    def ascii_summary(self) -> str:
        """Cheap ascii rendering of the graph for the ``view_graph`` tool."""
        if not self._records:
            return "(no agents)"
        roots = [
            rec.state for rec in self._records.values() if rec.state.parent_id is None
        ]
        lines: list[str] = []
        for root in roots:
            _emit(self, root, prefix="", lines=lines)
        return "\n".join(lines)


def _emit(
    graph: AgentGraph, state: AgentState, *, prefix: str, lines: list[str]
) -> None:
    lines.append(
        f"{prefix}- {state.name} ({state.agent_id[:8]}) "
        f"[{state.status.value}] iter={state.iteration}"
    )
    for child in graph.get_children(state.agent_id):
        _emit(graph, child, prefix=prefix + "  ", lines=lines)


# A single module-level instance used by the graph tools.  Tests may
# reset it via :func:`reset_default_graph`.
_default_graph = AgentGraph()


def get_default_graph() -> AgentGraph:
    """Return the shared process-wide :class:`AgentGraph`."""
    return _default_graph


def reset_default_graph() -> None:
    """Replace the default graph with a fresh instance (tests only)."""
    global _default_graph  # noqa: PLW0603
    _default_graph = AgentGraph()


__all__ = [
    "AgentGraph",
    "get_default_graph",
    "reset_default_graph",
]
