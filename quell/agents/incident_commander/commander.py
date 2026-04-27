"""IncidentCommander — the root agent responsible for orchestrating a full
incident investigation.

In Phase 7 this is the only concrete :class:`BaseAgent` implementation.
Subagents (created via the Phase 13 ``create_agent`` tool) will add more
specialized classes later.

The system prompt is loaded from ``system_prompt.jinja`` via a
``jinja2.PackageLoader`` so the template ships in the wheel without any
``MANIFEST.in`` or ``package_data`` fiddling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import jinja2

from quell.agents.base_agent import BaseAgent
from quell.config.schema import QuellConfig
from quell.llm.llm import LLM
from quell.skills import SkillFile
from quell.tools.registry import list_tools

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader("quell.agents.incident_commander", "."),
    autoescape=False,  # system prompts are not HTML — we control the content
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=jinja2.StrictUndefined,
)


class IncidentCommander(BaseAgent):
    """Root agent that investigates one incident end-to-end."""

    name = "incident_commander"

    def __init__(
        self,
        config: QuellConfig,
        *,
        llm: LLM | None = None,
        parent_id: str | None = None,
        loaded_skills: list[SkillFile] | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        incident_id: str | None = None,
    ) -> None:
        """Instantiate the commander.

        Args:
            config:          Root configuration.
            llm:             Optional pre-built LLM for test injection.
            parent_id:       Always ``None`` for the true root agent.
            loaded_skills:   Specialized knowledge (from
                             :mod:`quell.skills`) injected into the
                             system prompt.  Typically prepared by
                             calling :func:`quell.skills.select_applicable`
                             against a context derived from the incident.
            session_factory: Async session factory for persisting
                             :class:`AgentRun` + :class:`Event` rows.
            incident_id:     Parent :class:`Incident` id. Required when
                             ``session_factory`` is supplied.
        """
        skill_names = [s.name for s in (loaded_skills or [])]
        super().__init__(
            config,
            llm=llm,
            parent_id=parent_id,
            session_factory=session_factory,
            incident_id=incident_id,
            loaded_skill_names=skill_names,
        )
        self._loaded_skills: list[SkillFile] = list(loaded_skills or [])

    def _render_system_prompt(self) -> str:
        """Render ``system_prompt.jinja`` with the current tool catalogue."""
        template = _ENV.get_template("system_prompt.jinja")
        return template.render(
            agent_name=self.name,
            tools=list_tools(),
            loaded_skills=self._loaded_skills,
        )


__all__ = ["IncidentCommander"]
