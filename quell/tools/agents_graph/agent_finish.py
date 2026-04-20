"""``agent_finish`` — subagent signals it is done with its task."""

from __future__ import annotations

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult


@register_tool(
    name="agent_finish",
    description=(
        "Signal that this agent has finished its task. "
        "Produces a structured result returned to the parent."
    ),
    parameters=[
        ToolParameterSpec(
            name="summary",
            type="string",
            description="Short summary of what the agent accomplished.",
        ),
        ToolParameterSpec(
            name="findings",
            type="string",
            description="Key evidence or conclusions (free-form).",
            required=False,
        ),
    ],
    execute_in_sandbox=False,
)
async def agent_finish(summary: str, findings: str = "") -> ToolResult:
    """Return a success with the summary + findings in metadata."""
    return ToolResult.success(
        "agent_finish",
        summary,
        metadata={"findings": findings} if findings else {},
    )
