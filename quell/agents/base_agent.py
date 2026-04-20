"""BaseAgent and the canonical ``agent_loop()`` driving all investigations.

The loop is intentionally minimal: it calls the LLM, parses XML tool calls,
dispatches each via :func:`~quell.tools.executor.execute_tool`, formats the
results with :func:`~quell.tools.formatting.format_observations`, and
appends everything to :attr:`~quell.agents.state.AgentState.messages`.

Termination conditions:

1. The LLM response contains no tool calls — treated as "agent is done
   reasoning" and transitions to :attr:`AgentStatus.COMPLETED`.
2. One of the executed tools is in :attr:`BaseAgent.FINISH_TOOLS` (the
   Phase 12 ``agent_finish`` / ``finish_incident`` family) — transitions to
   :attr:`AgentStatus.COMPLETED` and records the tool's output + metadata
   as :attr:`AgentState.final_result`.
3. The iteration counter reaches :attr:`AgentState.max_iterations` —
   transitions to :attr:`AgentStatus.FAILED`.
4. The LLM call raises an :class:`~quell.utils.errors.LLMError` (or any
   other :class:`~quell.utils.errors.QuellError`) — transitions to
   :attr:`AgentStatus.FAILED`; the error text is appended to
   :attr:`AgentState.errors`.

The loop is contractually non-raising.  Callers inspect the returned dict
to determine outcome.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from loguru import logger

from quell.agents.state import AgentState
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.llm import LLM
from quell.llm.parser import parse_tool_invocations
from quell.llm.types import LLMMessage
from quell.tools.executor import execute_tool
from quell.tools.formatting import format_observations
from quell.tools.result import ToolResult
from quell.utils.errors import LLMError, QuellError


class BaseAgent(ABC):
    """Abstract base class for every Quell agent.

    Subclasses must override :meth:`_render_system_prompt` to supply the
    system message that seeds the conversation.  Everything else — the
    loop body, finish detection, error handling — is inherited.

    Attributes:
        FINISH_TOOLS: Tool names whose successful invocation terminates
                      the loop.  Override in subclasses to extend.
        name:         Human-readable agent role; surfaced in state and logs.
    """

    FINISH_TOOLS: ClassVar[frozenset[str]] = frozenset(
        {"agent_finish", "finish_incident"}
    )
    name: ClassVar[str] = "base"

    def __init__(
        self,
        config: QuellConfig,
        *,
        llm: LLM | None = None,
        parent_id: str | None = None,
    ) -> None:
        """Instantiate an agent.

        Args:
            config:    Root configuration.  Used to construct the LLM when
                       ``llm`` is not supplied.
            llm:       Pre-built LLM (primarily for test injection).  When
                       ``None``, a new :class:`LLM` is built from
                       ``config.llm``.
            parent_id: ``agent_id`` of the parent agent (for Phase 13
                       subagent spawning); ``None`` for a root agent.
        """
        self.config = config
        self.llm = llm or LLM(config.llm)
        self.parent_id = parent_id
        self.state: AgentState | None = None

    # ------------------------------------------------------------------
    # Abstract + overridable hooks
    # ------------------------------------------------------------------

    @abstractmethod
    def _render_system_prompt(self) -> str:
        """Return the fully rendered system prompt for this agent."""

    def _is_finish_tool(self, name: str) -> bool:
        """Return ``True`` when *name* should terminate the loop."""
        return name in self.FINISH_TOOLS

    def _build_initial_state(self, task: str) -> AgentState:
        """Construct the initial :class:`AgentState` for a new run."""
        return AgentState(
            name=self.name,
            task=task,
            status=AgentStatus.RUNNING,
            parent_id=self.parent_id,
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def agent_loop(self, task: str) -> dict[str, object]:
        """Drive the agent until it finishes, fails, or hits the cap.

        Args:
            task: Task description given to the agent — appended verbatim
                  as the first user message after the system prompt.

        Returns:
            A dict with keys:

            * ``status``     (``"completed"`` | ``"failed"``)
            * ``iterations`` (int — number of tool-executing turns)
            * ``errors``     (``list[str]`` — accumulated error messages)
            * ``result``     (``dict[str, object]`` — from finish tool)
        """
        state = self._build_initial_state(task)
        self.state = state

        state.messages.append(
            LLMMessage(role="system", content=self._render_system_prompt())
        )
        state.messages.append(LLMMessage(role="user", content=task))

        logger.info(
            "agent_loop start: agent={} id={} task={!r}",
            self.name,
            state.agent_id,
            task,
        )

        while state.status == AgentStatus.RUNNING:
            if state.iteration >= state.max_iterations:
                state.status = AgentStatus.FAILED
                state.errors.append(f"max_iterations ({state.max_iterations}) reached")
                break

            try:
                response = await self.llm.generate(state.messages)
            except LLMError as exc:
                state.status = AgentStatus.FAILED
                state.errors.append(f"LLMError: {exc}")
                logger.error("agent_loop LLM error: {}", exc)
                break
            except QuellError as exc:
                state.status = AgentStatus.FAILED
                state.errors.append(f"{type(exc).__name__}: {exc}")
                logger.error("agent_loop QuellError: {}", exc)
                break

            state.messages.append(
                LLMMessage(role="assistant", content=response.content)
            )

            tool_calls = parse_tool_invocations(response.content)
            if not tool_calls:
                # Assistant produced prose but no tool calls — treat as a
                # clean finish.  Concrete agents that want to coerce a
                # finish-tool call can enforce it in their prompt.
                state.status = AgentStatus.COMPLETED
                logger.info("agent_loop finished via prose response (no tool calls)")
                break

            results: list[ToolResult] = []
            for inv in tool_calls:
                try:
                    result = await execute_tool(
                        inv,
                        agent_state=state,
                        sandbox_url=state.sandbox_url,
                        sandbox_token=state.sandbox_token,
                    )
                except Exception as exc:  # noqa: BLE001 — executor is contractually non-raising
                    result = ToolResult.failure(inv.name, f"executor crashed: {exc}")
                    logger.error("executor crashed for {}: {}", inv.name, exc)
                results.append(result)

            state.messages.append(
                LLMMessage(role="user", content=format_observations(results))
            )
            state.iteration += 1
            state.touch()

            # Finish detection — first matching finish tool wins.
            for r in results:
                if self._is_finish_tool(r.tool_name):
                    state.status = AgentStatus.COMPLETED
                    state.final_result = {"summary": r.output, **r.metadata}
                    logger.info(
                        "agent_loop finished via {} after {} iterations",
                        r.tool_name,
                        state.iteration,
                    )
                    break

        state.touch()
        return {
            "status": state.status.value,
            "iterations": state.iteration,
            "errors": list(state.errors),
            "result": state.final_result or {},
        }


__all__ = ["BaseAgent"]
