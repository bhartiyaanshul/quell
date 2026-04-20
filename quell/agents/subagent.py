"""GenericSubagent — concrete BaseAgent spawned by the ``create_agent`` tool.

The subagent's system prompt is a small inline template that states the
task, lists the skill names its parent selected, and instructs the
subagent to call ``agent_finish`` when done.
"""

from __future__ import annotations

import jinja2

from quell.agents.base_agent import BaseAgent
from quell.agents.state import AgentState
from quell.agents.types import AgentStatus
from quell.config.schema import QuellConfig
from quell.llm.llm import LLM
from quell.skills import SkillFile
from quell.tools.registry import list_tools

_SYSTEM_PROMPT = jinja2.Template(
    """\
You are {{ agent_name }}, a specialised subagent spawned by the
IncidentCommander to handle one narrow part of an investigation.

Your task: {{ task }}

Investigate iteratively. Call tools to gather evidence; reason between
calls. When you have a concrete answer, call `agent_finish` with a short
summary and your key findings.

<tool_call_format>
<function=tool_name>
<parameter=arg_name>value</parameter>
</function>
</tool_call_format>

<available_tools>
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}
</available_tools>

{% if loaded_skills %}
<specialized_knowledge>
{% for skill in loaded_skills %}
<{{ skill.name }}>
{{ skill.content }}
</{{ skill.name }}>
{% endfor %}
</specialized_knowledge>
{% endif %}
""",
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


class GenericSubagent(BaseAgent):
    """A lightweight subagent that finishes via the ``agent_finish`` tool."""

    # Subagents finish via ``agent_finish``, not ``finish_incident``.
    FINISH_TOOLS = frozenset({"agent_finish"})

    def __init__(
        self,
        config: QuellConfig,
        *,
        name: str,
        task: str,
        llm: LLM | None = None,
        parent_id: str | None = None,
        loaded_skills: list[SkillFile] | None = None,
        agent_id: str | None = None,
    ) -> None:
        super().__init__(config, llm=llm, parent_id=parent_id)
        self._name = name
        self._task = task
        self._loaded_skills: list[SkillFile] = list(loaded_skills or [])
        self._preset_agent_id = agent_id
        # Override the class-level ``name`` for this instance.
        self.name = name  # type: ignore[misc]

    def _build_initial_state(self, task: str) -> AgentState:
        if self._preset_agent_id is not None:
            return AgentState(
                agent_id=self._preset_agent_id,
                name=self._name,
                task=task,
                status=AgentStatus.RUNNING,
                parent_id=self.parent_id,
            )
        return AgentState(
            name=self._name,
            task=task,
            status=AgentStatus.RUNNING,
            parent_id=self.parent_id,
        )

    def _render_system_prompt(self) -> str:
        return _SYSTEM_PROMPT.render(
            agent_name=self._name,
            task=self._task,
            tools=list_tools(),
            loaded_skills=self._loaded_skills,
        )


__all__ = ["GenericSubagent"]
