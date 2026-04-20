"""Inter-agent message passing — a process-local ``asyncio.Queue`` per agent."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentEnvelope:
    """One message addressed to an agent."""

    from_agent_id: str
    to_agent_id: str
    content: str


class AgentMessageQueue:
    """Broker that owns one :class:`asyncio.Queue` per known agent.

    Messages are plain strings.  Structured payloads are the sender's
    responsibility (typically JSON) — the broker does not care.
    """

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[AgentEnvelope]] = {}

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def ensure(self, agent_id: str) -> asyncio.Queue[AgentEnvelope]:
        """Return the queue for *agent_id*, creating it if needed."""
        q = self._queues.get(agent_id)
        if q is None:
            q = asyncio.Queue()
            self._queues[agent_id] = q
        return q

    async def send(self, from_id: str, to_id: str, message: str) -> None:
        """Enqueue a message addressed to *to_id*."""
        await self.ensure(to_id).put(
            AgentEnvelope(from_agent_id=from_id, to_agent_id=to_id, content=message)
        )

    async def receive(
        self,
        agent_id: str,
        *,
        timeout: float | None = 30.0,
    ) -> AgentEnvelope | None:
        """Wait up to *timeout* seconds for a message addressed to *agent_id*.

        Returns ``None`` when the wait times out.
        """
        queue = self.ensure(agent_id)
        try:
            if timeout is None:
                return await queue.get()
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except TimeoutError:
            return None

    def clear(self) -> None:
        """Drop every queue (tests only)."""
        self._queues.clear()


# Process-wide default broker.  Tests may reset via :func:`reset_default_broker`.
_default_broker = AgentMessageQueue()


def get_default_broker() -> AgentMessageQueue:
    """Return the shared message broker."""
    return _default_broker


def reset_default_broker() -> None:
    """Replace the default broker with a fresh instance (tests only)."""
    global _default_broker  # noqa: PLW0603
    _default_broker = AgentMessageQueue()


__all__ = [
    "AgentEnvelope",
    "AgentMessageQueue",
    "get_default_broker",
    "reset_default_broker",
]
