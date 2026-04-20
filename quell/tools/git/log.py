"""``git_log`` — recent commit log for the workspace."""

from __future__ import annotations

import asyncio
from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")


@register_tool(
    name="git_log",
    description="Show recent git commits (oneline format with author and time).",
    parameters=[
        ToolParameterSpec(
            name="limit",
            type="integer",
            description="Number of commits to show (default 20).",
            required=False,
        ),
        ToolParameterSpec(
            name="path",
            type="string",
            description="Optional path filter (default '.')",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def git_log(limit: int = 20, path: str = ".") -> ToolResult:
    """Return the last *limit* commits touching *path*."""
    root = _WORKSPACE_ROOT if _WORKSPACE_ROOT.is_dir() else Path.cwd()
    cmd = [
        "git",
        "-C",
        str(root),
        "log",
        f"-n{int(limit)}",
        "--pretty=format:%h %ai %an — %s",
        "--",
        path,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        return ToolResult.failure(
            "git_log", err.decode("utf-8", errors="replace").strip()
        )
    return ToolResult.success(
        "git_log",
        out.decode("utf-8", errors="replace").rstrip() or "(no commits)",
        metadata={"limit": limit, "path": path},
    )
