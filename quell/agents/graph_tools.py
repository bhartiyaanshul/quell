"""Tools that let one agent coordinate with others: ``create_agent``,
``send_message``, ``wait_for_message``, ``view_graph``.

These tools are kept inside :mod:`quell.agents` (rather than
``quell.tools.agents_graph``) to avoid an import cycle between tools and
agents.  :func:`quell.tools.builtins.register_builtin_tools` imports this
module, which is enough to register all four tools via their
``@register_tool`` decorators.
"""

from __future__ import annotations

import asyncio

from loguru import logger

from quell.agents.graph import get_default_graph
from quell.agents.messages import get_default_broker
from quell.agents.state import AgentState
from quell.agents.subagent import GenericSubagent
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.types import ToolParameterSpec
from quell.skills import SkillFile, list_skills
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

# A Config pulled once per process so every subagent shares the same LLM
# settings.  Tests override this via ``set_default_config``.
_CONFIG: QuellConfig = QuellConfig()


def set_default_config(config: QuellConfig) -> None:
    """Set the process-wide config used when spawning subagents."""
    global _CONFIG  # noqa: PLW0603
    _CONFIG = config


def _resolve_agent_id(agent_state: object | None) -> str:
    """Extract ``agent_id`` from the injected state (or return empty)."""
    if isinstance(agent_state, AgentState):
        return agent_state.agent_id
    return ""


def _pick_skills(names: list[str]) -> list[SkillFile]:
    """Resolve a list of skill slugs against the bundled skills, silently
    dropping anything that doesn't exist."""
    if not names:
        return []
    wanted = {n.strip() for n in names if n.strip()}
    return [s for s in list_skills() if s.name in wanted]


# ---------------------------------------------------------------------------
# create_agent
# ---------------------------------------------------------------------------


@register_tool(
    name="create_agent",
    description=(
        "Spawn a new subagent with its own task and optional skill set. "
        "Returns the new agent_id; the subagent runs in the background."
    ),
    parameters=[
        ToolParameterSpec(name="name", type="string", description="Subagent name."),
        ToolParameterSpec(
            name="task", type="string", description="What the subagent must do."
        ),
        ToolParameterSpec(
            name="skills",
            type="string",
            description="Comma-separated skill slugs (e.g. 'fastapi,postgres').",
            required=False,
        ),
    ],
    execute_in_sandbox=False,
    needs_agent_state=True,
)
async def create_agent(
    name: str,
    task: str,
    skills: str = "",
    *,
    agent_state: object | None = None,
) -> ToolResult:
    """Spawn *name* as a background subagent of the current agent."""
    parent_id = _resolve_agent_id(agent_state)
    skill_names = [s for s in (skills or "").split(",") if s.strip()]
    loaded = _pick_skills(skill_names)

    # Seed the graph with a placeholder state so ``view_graph`` and
    # message passing work before the loop actually runs; the subagent
    # adopts this agent_id so messages round-trip cleanly.
    seed = AgentState(
        name=name,
        task=task,
        status=AgentStatus.RUNNING,
        parent_id=parent_id,
    )
    subagent = GenericSubagent(
        _CONFIG,
        name=name,
        task=task,
        parent_id=parent_id,
        loaded_skills=loaded,
        agent_id=seed.agent_id,
    )
    graph = get_default_graph()
    graph.add_agent(seed)

    async def _run() -> object:
        try:
            result = await subagent.agent_loop(task)
        finally:
            # Replace the seed state with the real one from the subagent
            # so the graph reflects actual iteration counts / status.
            if subagent.state is not None:
                graph.add_agent(subagent.state)
        if subagent.state is not None:
            await get_default_broker().send(
                from_id=subagent.state.agent_id,
                to_id=parent_id,
                message=str(result),
            )
        return result

    task_handle = asyncio.create_task(_run())
    graph.attach_task(seed.agent_id, task_handle)
    logger.info("subagent spawned: {} ({})", name, seed.agent_id[:8])
    return ToolResult.success(
        "create_agent",
        f"Spawned {name} as agent_id={seed.agent_id}",
        metadata={"agent_id": seed.agent_id, "name": name},
    )


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


@register_tool(
    name="send_message",
    description="Send a string message to another agent by agent_id.",
    parameters=[
        ToolParameterSpec(
            name="to_agent_id", type="string", description="Recipient agent_id."
        ),
        ToolParameterSpec(
            name="message", type="string", description="Message content (free-form)."
        ),
    ],
    execute_in_sandbox=False,
    needs_agent_state=True,
)
async def send_message(
    to_agent_id: str,
    message: str,
    *,
    agent_state: object | None = None,
) -> ToolResult:
    """Post *message* to another agent's queue."""
    sender = _resolve_agent_id(agent_state)
    await get_default_broker().send(sender, to_agent_id, message)
    return ToolResult.success(
        "send_message",
        f"Queued message to {to_agent_id}",
        metadata={"from": sender, "to": to_agent_id},
    )


# ---------------------------------------------------------------------------
# wait_for_message
# ---------------------------------------------------------------------------


@register_tool(
    name="wait_for_message",
    description=(
        "Block until a message arrives for this agent, or return a timeout "
        "notice after N seconds."
    ),
    parameters=[
        ToolParameterSpec(
            name="timeout_seconds",
            type="float",
            description="Max wait in seconds (default 30).",
            required=False,
        ),
    ],
    execute_in_sandbox=False,
    needs_agent_state=True,
)
async def wait_for_message(
    timeout_seconds: float = 30.0,
    *,
    agent_state: object | None = None,
) -> ToolResult:
    """Wait for a message addressed to the current agent."""
    receiver = _resolve_agent_id(agent_state)
    if not receiver:
        return ToolResult.failure(
            "wait_for_message", "No agent_id on the current state."
        )
    envelope = await get_default_broker().receive(receiver, timeout=timeout_seconds)
    if envelope is None:
        return ToolResult.success(
            "wait_for_message",
            f"(timeout after {timeout_seconds}s; no message received)",
            metadata={"timed_out": True},
        )
    return ToolResult.success(
        "wait_for_message",
        envelope.content,
        metadata={"from": envelope.from_agent_id, "to": envelope.to_agent_id},
    )


# ---------------------------------------------------------------------------
# view_graph
# ---------------------------------------------------------------------------


@register_tool(
    name="view_graph",
    description="Return a plain-text rendering of the current agent graph.",
    parameters=[],
    execute_in_sandbox=False,
)
async def view_graph() -> ToolResult:
    """Describe the agent graph as ascii tree."""
    return ToolResult.success("view_graph", get_default_graph().ascii_summary())


__all__ = [
    "create_agent",
    "send_message",
    "wait_for_message",
    "view_graph",
    "set_default_config",
]
