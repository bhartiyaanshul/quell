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

import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar

from loguru import logger

from quell.agents.state import AgentState
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.cost import estimate_cost
from quell.llm.llm import LLM
from quell.llm.parser import parse_tool_invocations
from quell.llm.types import LLMMessage, LLMResponse, ToolInvocation
from quell.tools.executor import execute_tool
from quell.tools.formatting import format_observations
from quell.tools.result import ToolResult
from quell.utils.errors import LLMError, QuellError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


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
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        incident_id: str | None = None,
        loaded_skill_names: Sequence[str] | None = None,
    ) -> None:
        """Instantiate an agent.

        Args:
            config:          Root configuration.  Used to construct the LLM
                             when ``llm`` is not supplied.
            llm:             Pre-built LLM (primarily for test injection).
                             When ``None``, a new :class:`LLM` is built
                             from ``config.llm``.
            parent_id:       ``agent_id`` of the parent agent (for Phase
                             13 subagent spawning); ``None`` for a root
                             agent.
            session_factory: Optional async session factory.  When
                             supplied, the loop writes :class:`AgentRun`
                             + per-iteration :class:`Event` rows so the
                             dashboard + replay features can replay the
                             investigation later.  Omit for tests that
                             don't need persistence.
            incident_id:     Parent :class:`Incident` id.  Required when
                             ``session_factory`` is supplied; ignored
                             otherwise.
            loaded_skill_names: Names of skill runbooks injected into
                             the system prompt; persisted on
                             :class:`AgentRun.skills` for the dashboard.
        """
        self.config = config
        self.llm = llm or LLM(config.llm)
        self.parent_id = parent_id
        self.state: AgentState | None = None
        self._session_factory = session_factory
        self._incident_id = incident_id
        self._loaded_skill_names: list[str] = list(loaded_skill_names or [])
        self._run_id: str | None = None  # set on agent_loop entry when persisting

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
        # Propagate the AgentConfig caps into the state so tests + subclasses
        # can override per-run if needed.
        state.max_iterations = self.config.agent.max_iterations
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

        # Persistence begins — create the AgentRun row if a session
        # factory was wired up.
        await self._persist_run_start()

        while state.status == AgentStatus.RUNNING:
            if state.iteration >= state.max_iterations:
                state.status = AgentStatus.FAILED
                state.errors.append(f"max_iterations ({state.max_iterations}) reached")
                await self._persist_event(
                    "error",
                    {"message": state.errors[-1], "kind": "max_iterations"},
                )
                break

            t0 = time.monotonic()
            try:
                response = await self.llm.generate(state.messages)
            except LLMError as exc:
                state.status = AgentStatus.FAILED
                state.errors.append(f"LLMError: {exc}")
                logger.error("agent_loop LLM error: {}", exc)
                await self._persist_event(
                    "error", {"exc_type": "LLMError", "message": str(exc)}
                )
                break
            except QuellError as exc:
                state.status = AgentStatus.FAILED
                state.errors.append(f"{type(exc).__name__}: {exc}")
                logger.error("agent_loop QuellError: {}", exc)
                await self._persist_event(
                    "error",
                    {"exc_type": type(exc).__name__, "message": str(exc)},
                )
                break

            latency_ms = int((time.monotonic() - t0) * 1000)

            # Update running cost totals.
            state.total_input_tokens += response.input_tokens
            state.total_output_tokens += response.output_tokens
            state.estimated_cost_usd += estimate_cost(
                response.model, response.input_tokens, response.output_tokens
            )

            await self._persist_llm_call(state, response, latency_ms)

            # Budget check — halt before the next iteration if the user
            # configured a cap and we've blown past it.
            budget = self.config.agent.max_cost_usd
            if budget is not None and state.estimated_cost_usd > budget:
                state.status = AgentStatus.FAILED
                state.errors.append(
                    f"budget exceeded: estimated ${state.estimated_cost_usd:.4f} "
                    f"> max_cost_usd=${budget:.4f}"
                )
                await self._persist_event(
                    "error",
                    {
                        "kind": "budget_exceeded",
                        "estimated_cost_usd": state.estimated_cost_usd,
                        "max_cost_usd": budget,
                    },
                )
                state.messages.append(
                    LLMMessage(role="assistant", content=response.content)
                )
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
                t_tool = time.monotonic()
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
                tool_latency_ms = int((time.monotonic() - t_tool) * 1000)
                await self._persist_tool_call(inv, result, tool_latency_ms)
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
                    await self._persist_findings_from_result(r)
                    logger.info(
                        "agent_loop finished via {} after {} iterations",
                        r.tool_name,
                        state.iteration,
                    )
                    break

        state.touch()
        await self._persist_run_finish(state)
        return {
            "status": state.status.value,
            "iterations": state.iteration,
            "errors": list(state.errors),
            "result": state.final_result or {},
            "input_tokens": state.total_input_tokens,
            "output_tokens": state.total_output_tokens,
            "cost_usd": state.estimated_cost_usd,
        }

    # ------------------------------------------------------------------
    # Persistence helpers — all no-ops when no session_factory was wired
    # ------------------------------------------------------------------

    async def _persist_run_start(self) -> None:
        """Create the :class:`AgentRun` row on ``agent_loop`` entry."""
        if self._session_factory is None or self._incident_id is None:
            return
        from quell.memory.agent_runs import create_run  # noqa: PLC0415

        try:
            async with self._session_factory() as session:
                run = await create_run(
                    session,
                    incident_id=self._incident_id,
                    name=self.name,
                    skills=self._loaded_skill_names,
                    parent_agent_id=self.parent_id,
                )
                self._run_id = run.id
                await session.commit()
        except Exception as exc:  # noqa: BLE001 — persistence must never crash the loop
            logger.warning("agent_loop: could not persist run start: {}", exc)

    async def _persist_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Write a single :class:`Event` row if persistence is enabled."""
        if self._session_factory is None or self._run_id is None:
            return
        from quell.memory.events import create_event  # noqa: PLC0415

        try:
            async with self._session_factory() as session:
                await create_event(
                    session,
                    agent_run_id=self._run_id,
                    event_type=event_type,
                    payload=payload,
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "agent_loop: could not persist {} event: {}", event_type, exc
            )

    async def _persist_llm_call(
        self,
        state: AgentState,
        response: LLMResponse,
        latency_ms: int,
    ) -> None:
        """Persist an ``llm_call`` event."""
        # Only record the LAST message plus the response — the full
        # compressed history is available in reconstructed form via the
        # earlier events and would bloat the row.
        last_user = next(
            (m for m in reversed(state.messages) if m.role == "user"), None
        )
        await self._persist_event(
            "llm_call",
            {
                "model": response.model,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "latency_ms": latency_ms,
                "iteration": state.iteration,
                "response_preview": response.content[:500],
                "prompt_preview": (last_user.content[:500] if last_user else ""),
            },
        )

    async def _persist_tool_call(
        self,
        invocation: ToolInvocation,
        result: ToolResult,
        latency_ms: int,
    ) -> None:
        """Persist a ``tool_call`` event."""
        await self._persist_event(
            "tool_call",
            {
                "tool_name": invocation.name,
                "parameters": invocation.parameters,
                "ok": result.ok,
                "output_preview": (result.output[:500] if result.output else ""),
                "error": result.error,
                "latency_ms": latency_ms,
            },
        )

    async def _persist_findings_from_result(self, result: ToolResult) -> None:
        """Persist :class:`Finding` rows if the finish tool's metadata lists any.

        Finish tools can populate ``metadata["findings"]`` with a list of
        dicts containing ``category``, ``description``, and optional
        ``file_path`` / ``line_number`` / ``confidence``.  Each entry
        becomes a persisted :class:`Finding` tied to the current run.
        """
        if (
            self._session_factory is None
            or self._run_id is None
            or self._incident_id is None
        ):
            return
        raw = result.metadata.get("findings") if result.metadata else None
        if not isinstance(raw, list):
            return

        from quell.memory.findings import create_finding  # noqa: PLC0415

        try:
            async with self._session_factory() as session:
                for entry in raw:
                    if not isinstance(entry, dict):
                        continue
                    await create_finding(
                        session,
                        incident_id=self._incident_id,
                        agent_run_id=self._run_id,
                        category=str(entry.get("category", "general")),
                        description=str(entry.get("description", "")),
                        file_path=entry.get("file_path"),
                        line_number=entry.get("line_number"),
                        confidence=float(entry.get("confidence", 1.0)),
                    )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent_loop: could not persist findings: {}", exc)

    async def _persist_run_finish(self, state: AgentState) -> None:
        """Finalise the :class:`AgentRun` row on loop exit and roll the
        running cost total forward onto the parent :class:`Incident`."""
        if self._session_factory is None or self._run_id is None:
            return
        from quell.memory.agent_runs import finish_run  # noqa: PLC0415
        from quell.memory.incidents import (  # noqa: PLC0415
            get_incident,
            update_incident,
        )

        # Store the final token + cost totals in the AgentRun's
        # ``final_result`` dict alongside the agent-reported payload so
        # the dashboard can surface them without a join.
        final_payload: dict[str, Any] = dict(state.final_result or {})
        final_payload.setdefault("_metrics", {})
        if isinstance(final_payload["_metrics"], dict):
            final_payload["_metrics"].update(
                {
                    "input_tokens": state.total_input_tokens,
                    "output_tokens": state.total_output_tokens,
                    "cost_usd": round(state.estimated_cost_usd, 6),
                    "iterations": state.iteration,
                }
            )

        try:
            async with self._session_factory() as session:
                await finish_run(
                    session,
                    self._run_id,
                    status=state.status.value,
                    final_result=final_payload,
                )
                # Bump the Incident's running cost.
                if self._incident_id is not None:
                    incident = await get_incident(session, self._incident_id)
                    if incident is not None:
                        new_cost = float(incident.cost_usd or 0.0) + float(
                            state.estimated_cost_usd
                        )
                        await update_incident(
                            session,
                            self._incident_id,
                            cost_usd=new_cost,
                        )
                await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("agent_loop: could not persist run finish: {}", exc)


__all__ = ["BaseAgent"]
