"""``create_postmortem`` — blameless postmortem document."""

from __future__ import annotations

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult


@register_tool(
    name="create_postmortem",
    description=(
        "Produce a blameless postmortem (Markdown) suitable for publishing "
        "after the incident is resolved."
    ),
    parameters=[
        ToolParameterSpec(name="title", type="string", description="Postmortem title."),
        ToolParameterSpec(
            name="summary", type="string", description="One-paragraph overview."
        ),
        ToolParameterSpec(
            name="impact", type="string", description="User-visible impact + scope."
        ),
        ToolParameterSpec(
            name="timeline",
            type="string",
            description="Chronological event list.",
        ),
        ToolParameterSpec(
            name="root_cause", type="string", description="Why it happened."
        ),
        ToolParameterSpec(
            name="resolution", type="string", description="How it was fixed."
        ),
        ToolParameterSpec(
            name="action_items",
            type="string",
            description="Preventative follow-ups.",
        ),
    ],
    execute_in_sandbox=False,
)
async def create_postmortem(
    title: str,
    summary: str,
    impact: str,
    timeline: str,
    root_cause: str,
    resolution: str,
    action_items: str,
) -> ToolResult:
    """Return a Markdown postmortem plus structured metadata."""
    body = (
        f"# {title}\n\n"
        f"## Summary\n{summary}\n\n"
        f"## Impact\n{impact}\n\n"
        f"## Timeline\n{timeline}\n\n"
        f"## Root cause\n{root_cause}\n\n"
        f"## Resolution\n{resolution}\n\n"
        f"## Action items\n{action_items}\n"
    )
    return ToolResult.success(
        "create_postmortem",
        body,
        metadata={
            "title": title,
            "summary": summary,
            "impact": impact,
            "timeline": timeline,
            "root_cause": root_cause,
            "resolution": resolution,
            "action_items": action_items,
        },
    )
