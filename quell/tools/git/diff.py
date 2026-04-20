"""``git_diff`` — diff between two refs or the working tree."""

from __future__ import annotations

import asyncio
from pathlib import Path

from quell.llm.types import ToolParameterSpec
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult

_WORKSPACE_ROOT = Path("/workspace")


@register_tool(
    name="git_diff",
    description=(
        "Show `git diff` between two refs (or working tree vs HEAD if refs omitted)."
    ),
    parameters=[
        ToolParameterSpec(
            name="from_ref",
            type="string",
            description="Base ref; default HEAD.",
            required=False,
        ),
        ToolParameterSpec(
            name="to_ref",
            type="string",
            description="Target ref; default working tree.",
            required=False,
        ),
        ToolParameterSpec(
            name="path",
            type="string",
            description="Optional path filter.",
            required=False,
        ),
    ],
    execute_in_sandbox=True,
)
async def git_diff(
    from_ref: str = "HEAD",
    to_ref: str = "",
    path: str = "",
) -> ToolResult:
    """Return the diff between *from_ref* and *to_ref*."""
    root = _WORKSPACE_ROOT if _WORKSPACE_ROOT.is_dir() else Path.cwd()
    cmd = ["git", "-C", str(root), "diff", "--no-color"]
    if to_ref:
        cmd.extend([from_ref, to_ref])
    else:
        cmd.append(from_ref)
    if path:
        cmd.extend(["--", path])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await proc.communicate()
    if proc.returncode not in (0, 1):
        return ToolResult.failure(
            "git_diff", err.decode("utf-8", errors="replace").strip()
        )
    body = out.decode("utf-8", errors="replace").rstrip() or "(no changes)"
    return ToolResult.success(
        "git_diff",
        body,
        metadata={"from_ref": from_ref, "to_ref": to_ref, "path": path},
    )
