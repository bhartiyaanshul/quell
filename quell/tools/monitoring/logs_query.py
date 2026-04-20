"""``logs_query`` — read recent lines from a local log file.

Kept deliberately narrow: the tool only exposes the *local-file* monitor
source.  Remote log sources (Vercel, Sentry, Datadog, etc.) are fetched
via their own tools in later work.
"""

from __future__ import annotations

from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_MAX_LINES = 500


@register_tool(
    name="logs_query",
    description=(
        "Return the last N lines of a local log file, optionally filtered "
        "by a case-insensitive substring."
    ),
    parameters=[
        ToolParameterSpec(
            name="path",
            type="string",
            description="Absolute path to the log file.",
        ),
        ToolParameterSpec(
            name="limit",
            type="integer",
            description="Maximum lines to return (default 100).",
            required=False,
        ),
        ToolParameterSpec(
            name="contains",
            type="string",
            description="Case-insensitive substring filter.",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def logs_query(
    path: str,
    limit: int = 100,
    contains: str = "",
) -> ToolResult:
    """Return up to *limit* tail lines of *path* optionally filtered by *contains*."""
    target = Path(path)
    if not target.is_file():
        return ToolResult.failure("logs_query", f"Not a file: {path}")

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ToolResult.failure("logs_query", f"Read failed: {exc}")

    lines = text.splitlines()
    if contains:
        needle = contains.lower()
        lines = [line for line in lines if needle in line.lower()]

    if limit < 1:
        limit = 1
    if limit > _MAX_LINES:
        limit = _MAX_LINES

    tail = lines[-limit:]
    return ToolResult.success(
        "logs_query",
        "\n".join(tail) if tail else "(no matching lines)",
        metadata={"path": path, "returned": len(tail), "filter": contains},
    )
