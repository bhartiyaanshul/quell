"""``finish_incident`` — root agent signals the investigation is complete."""

from __future__ import annotations

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult


@register_tool(
    name="finish_incident",
    description=(
        "Terminate the investigation and produce the final structured "
        "incident summary (root cause, evidence, proposed fix)."
    ),
    parameters=[
        ToolParameterSpec(
            name="root_cause",
            type="string",
            description="The identified root cause.",
        ),
        ToolParameterSpec(
            name="evidence",
            type="string",
            description="Supporting evidence (files, log lines, stack frames).",
        ),
        ToolParameterSpec(
            name="proposed_fix",
            type="string",
            description="Concrete next step for a human reviewer.",
        ),
        ToolParameterSpec(
            name="status",
            type="string",
            description='"resolved" | "blocked" (default "resolved").',
            required=False,
        ),
    ],
    execute_in_sandbox=False,
)
async def finish_incident(
    root_cause: str,
    evidence: str,
    proposed_fix: str,
    status: str = "resolved",
) -> ToolResult:
    """Return the structured investigation result."""
    summary = (
        f"status: {status}\nroot_cause: {root_cause}\nproposed_fix: {proposed_fix}"
    )
    return ToolResult.success(
        "finish_incident",
        summary,
        metadata={
            "root_cause": root_cause,
            "evidence": evidence,
            "proposed_fix": proposed_fix,
            "status": status,
        },
    )
