"""Observation formatter — converts tool results into LLM message content.

After the executor runs a batch of tool invocations, the results need to
be fed back to the LLM as a single ``user`` turn.
:func:`format_observations` produces that turn's content.

The format is XML-like so the LLM can unambiguously correlate each
result with the tool call that produced it::

    <tool_result name="code_read" status="ok">
    def main():
        print("hello")
    </tool_result>

    <tool_result name="git_log" status="error">
    git not found — install git
    </tool_result>
"""

from __future__ import annotations

from quell.tools.result import ToolResult

_MAX_INLINE_BYTES = 50_000  # hard cap applied before formatting


def format_observations(results: list[ToolResult]) -> str:
    """Render *results* as a single string suitable for a ``user`` LLM message.

    Args:
        results: One or more :class:`~quell.tools.result.ToolResult` objects.

    Returns:
        A multi-block XML string.  Never empty — returns a no-op notice
        when *results* is an empty list.
    """
    if not results:
        return "<tool_results>(no tool results)</tool_results>"

    blocks: list[str] = []
    for r in results:
        capped = r.truncate(_MAX_INLINE_BYTES)
        status = "ok" if capped.ok else "error"
        body = capped.output if capped.ok else capped.error
        truncation_note = "\n[output truncated]" if capped.truncated else ""
        blocks.append(
            f'<tool_result name="{capped.tool_name}" status="{status}">\n'
            f"{body}{truncation_note}\n"
            f"</tool_result>"
        )

    return "\n\n".join(blocks)


__all__ = ["format_observations"]
