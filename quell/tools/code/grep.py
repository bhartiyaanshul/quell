"""``code_grep`` — ripgrep-backed content search across the workspace."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")
_MAX_RESULTS = 200


@register_tool(
    name="code_grep",
    description=(
        "Search file contents using ripgrep (or grep as fallback). "
        "Returns up to 200 matching lines."
    ),
    parameters=[
        ToolParameterSpec(
            name="pattern", type="string", description="Regular-expression pattern."
        ),
        ToolParameterSpec(
            name="path",
            type="string",
            description="Workspace-relative subdirectory (default '.').",
            required=False,
        ),
        ToolParameterSpec(
            name="case_insensitive",
            type="boolean",
            description="Case-insensitive match (default false).",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def code_grep(
    pattern: str,
    path: str = ".",
    case_insensitive: bool = False,
) -> ToolResult:
    """Search *pattern* in the workspace.

    Returns matching lines with a ``file:line`` prefix.
    """
    root = _WORKSPACE_ROOT if _WORKSPACE_ROOT.is_dir() else Path.cwd()
    target = (root / path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return ToolResult.failure("code_grep", f"Path escapes workspace: {path}")

    rg = shutil.which("rg")
    if rg:
        cmd = [rg, "--line-number", "--no-heading", "--color=never"]
        if case_insensitive:
            cmd.append("-i")
        cmd.extend([pattern, str(target)])
    else:
        cmd = ["grep", "-rn"]
        if case_insensitive:
            cmd.append("-i")
        cmd.extend([pattern, str(target)])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
    except FileNotFoundError as exc:
        return ToolResult.failure("code_grep", f"grep binary not found: {exc}")

    stdout = out.decode("utf-8", errors="replace")
    stderr = err.decode("utf-8", errors="replace")

    # rg/grep return 1 when there are no matches — not an error.
    if proc.returncode not in (0, 1):
        return ToolResult.failure(
            "code_grep", f"grep failed (rc={proc.returncode}): {stderr.strip()}"
        )

    lines = stdout.splitlines()
    truncated = len(lines) > _MAX_RESULTS
    if truncated:
        lines = lines[:_MAX_RESULTS]
    body = "\n".join(lines) if lines else "(no matches)"
    return ToolResult.success(
        "code_grep",
        body,
        metadata={"match_count": len(lines), "truncated": truncated},
    )
