"""ToolResult — the canonical return type for every Quell tool.

No raw dicts or strings cross tool boundaries; every tool returns a
:class:`ToolResult`.  The executor, formatter, and agent loop all consume
this type so they stay decoupled from individual tool implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """Result of a single tool execution.

    Attributes:
        tool_name:  The name of the tool that produced this result.
        ok:         ``True`` if the tool completed without errors.
        output:     Primary text output (shown to the LLM).
        error:      Error message when ``ok`` is ``False``.
        metadata:   Optional structured data (not shown to the LLM directly).
        truncated:  ``True`` when ``output`` was cut to stay within size limits.
    """

    tool_name: str
    ok: bool
    output: str = ""
    error: str = ""
    metadata: dict[str, object] = field(default_factory=dict)
    truncated: bool = False

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------

    @classmethod
    def success(
        cls,
        tool_name: str,
        output: str,
        *,
        metadata: dict[str, object] | None = None,
        truncated: bool = False,
    ) -> ToolResult:
        """Return a successful result."""
        return cls(
            tool_name=tool_name,
            ok=True,
            output=output,
            metadata=metadata or {},
            truncated=truncated,
        )

    @classmethod
    def failure(
        cls,
        tool_name: str,
        error: str,
        *,
        metadata: dict[str, object] | None = None,
    ) -> ToolResult:
        """Return a failure result."""
        return cls(
            tool_name=tool_name,
            ok=False,
            error=error,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Size-limiting helper
    # ------------------------------------------------------------------

    _MAX_OUTPUT_BYTES: int = 50_000  # 50 KB

    def truncate(self, max_bytes: int = _MAX_OUTPUT_BYTES) -> ToolResult:
        """Return a copy with ``output`` capped at *max_bytes* UTF-8 bytes.

        When truncation is needed the head and tail are preserved and a
        notice is inserted in the middle so the LLM understands the gap.
        """
        encoded = self.output.encode("utf-8")
        if len(encoded) <= max_bytes:
            return self

        half = max_bytes // 2
        head = encoded[:half].decode("utf-8", errors="replace")
        tail = encoded[-half:].decode("utf-8", errors="replace")
        notice = f"\n\n[... {len(encoded) - max_bytes} bytes truncated ...]\n\n"
        return ToolResult(
            tool_name=self.tool_name,
            ok=self.ok,
            output=head + notice + tail,
            error=self.error,
            metadata=self.metadata,
            truncated=True,
        )


__all__ = ["ToolResult"]
