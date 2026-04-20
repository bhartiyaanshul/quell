"""``create_incident_report`` — structured summary for human review."""

from __future__ import annotations

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult


@register_tool(
    name="create_incident_report",
    description=(
        "Produce a structured incident report for human review. "
        "Does not write anywhere — the report is returned in the tool output "
        "and the structured fields in metadata."
    ),
    parameters=[
        ToolParameterSpec(
            name="title", type="string", description="Short incident title."
        ),
        ToolParameterSpec(
            name="root_cause", type="string", description="Hypothesised root cause."
        ),
        ToolParameterSpec(
            name="evidence",
            type="string",
            description="Supporting evidence (file paths, log lines).",
        ),
        ToolParameterSpec(
            name="proposed_fix",
            type="string",
            description="Concrete next step (no code changes applied).",
        ),
        ToolParameterSpec(
            name="severity",
            type="string",
            description="Severity label: low/medium/high/critical.",
            required=False,
        ),
    ],
    execute_in_sandbox=False,
)
async def create_incident_report(
    title: str,
    root_cause: str,
    evidence: str,
    proposed_fix: str,
    severity: str = "medium",
) -> ToolResult:
    """Return a human-readable report plus a structured ``metadata`` copy."""
    body = (
        f"# {title}\n\n"
        f"**Severity:** {severity}\n\n"
        f"## Root cause\n{root_cause}\n\n"
        f"## Evidence\n{evidence}\n\n"
        f"## Proposed fix\n{proposed_fix}\n"
    )
    return ToolResult.success(
        "create_incident_report",
        body,
        metadata={
            "title": title,
            "root_cause": root_cause,
            "evidence": evidence,
            "proposed_fix": proposed_fix,
            "severity": severity,
        },
    )
