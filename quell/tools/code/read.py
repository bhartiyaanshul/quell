"""``code_read`` — read a slice of a file from the workspace."""

from __future__ import annotations

from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")
_MAX_LINES = 2000


@register_tool(
    name="code_read",
    description="Read a file from the workspace, optionally between line numbers.",
    parameters=[
        ToolParameterSpec(
            name="path", type="string", description="Workspace-relative path."
        ),
        ToolParameterSpec(
            name="start_line",
            type="integer",
            description="1-indexed first line (default 1).",
            required=False,
        ),
        ToolParameterSpec(
            name="end_line",
            type="integer",
            description="Inclusive last line; -1 for EOF (default -1).",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def code_read(
    path: str,
    start_line: int = 1,
    end_line: int = -1,
) -> ToolResult:
    """Return ``path`` content between *start_line* and *end_line* inclusive."""
    try:
        target = _resolve(path)
    except ValueError as exc:
        return ToolResult.failure("code_read", str(exc))

    if not target.is_file():
        return ToolResult.failure("code_read", f"Not a file: {path}")

    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ToolResult.failure("code_read", f"Read failed: {exc}")

    lines = text.splitlines()
    if start_line < 1:
        start_line = 1
    if end_line == -1 or end_line > len(lines):
        end_line = len(lines)
    if start_line > end_line:
        return ToolResult.failure(
            "code_read", f"start_line ({start_line}) > end_line ({end_line})"
        )

    slice_lines = lines[start_line - 1 : end_line]
    if len(slice_lines) > _MAX_LINES:
        slice_lines = slice_lines[:_MAX_LINES]
    numbered = "\n".join(
        f"{start_line + i:6d}  {line}" for i, line in enumerate(slice_lines)
    )
    return ToolResult.success(
        "code_read",
        numbered,
        metadata={
            "path": path,
            "start_line": start_line,
            "end_line": start_line + len(slice_lines) - 1,
            "total_lines": len(lines),
        },
    )


def _resolve(path: str) -> Path:
    """Resolve *path* under ``/workspace`` and reject traversal attempts."""
    root = _WORKSPACE_ROOT if _WORKSPACE_ROOT.is_dir() else Path.cwd()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes workspace: {path}") from exc
    return candidate
