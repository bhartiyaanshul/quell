"""``git_blame`` — line-level authorship annotation."""

from __future__ import annotations

import asyncio
from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")


@register_tool(
    name="git_blame",
    description="Show `git blame` for a file, optionally restricted to a line range.",
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
            description="Inclusive end line; -1 for EOF (default -1).",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def git_blame(
    path: str,
    start_line: int = 1,
    end_line: int = -1,
) -> ToolResult:
    """Return ``git blame`` output for *path*."""
    root = _WORKSPACE_ROOT if _WORKSPACE_ROOT.is_dir() else Path.cwd()
    cmd = ["git", "-C", str(root), "blame", "--line-porcelain"]
    if end_line != -1:
        cmd.extend(["-L", f"{start_line},{end_line}"])
    elif start_line > 1:
        cmd.extend(["-L", f"{start_line},"])
    cmd.extend(["--", path])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        return ToolResult.failure(
            "git_blame", err.decode("utf-8", errors="replace").strip()
        )
    return ToolResult.success(
        "git_blame",
        out.decode("utf-8", errors="replace").rstrip() or "(no output)",
        metadata={"path": path, "start_line": start_line, "end_line": end_line},
    )
