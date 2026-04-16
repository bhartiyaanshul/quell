"""Shared data types for the Quell LLM layer.

All cross-module communication in the LLM subsystem flows through the
types defined here — no raw dicts or ``Any`` across boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


@dataclass
class LLMMessage:
    """A single message in an LLM conversation thread."""

    role: Literal["system", "user", "assistant"]
    content: str


# ---------------------------------------------------------------------------
# Tool call types (emitted by the XML parser)
# ---------------------------------------------------------------------------


@dataclass
class ToolInvocation:
    """A single tool invocation parsed from an LLM response."""

    name: str
    """The tool name as it appeared in the XML tag."""

    parameters: dict[str, str]
    """Raw string values keyed by parameter name."""

    raw_xml: str
    """The verbatim XML block, preserved for debugging."""


@dataclass
class ToolParameterSpec:
    """Metadata for one parameter of a registered tool."""

    name: str
    type: str  # "string" | "integer" | "float" | "boolean"
    description: str
    required: bool = True


@dataclass
class ToolMetadata:
    """Metadata for a registered tool, used to build the system-prompt
    tool catalogue and to validate LLM-provided arguments."""

    name: str
    description: str
    parameters: list[ToolParameterSpec] = field(default_factory=list)
    execute_in_sandbox: bool = True
    needs_agent_state: bool = False


# ---------------------------------------------------------------------------
# LLM response
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """Parsed response from a single LLM generation call."""

    content: str
    """Full text content of the assistant turn."""

    model: str
    """Model string that produced this response.

    Example: ``"anthropic/claude-haiku-4-5"``
    """

    input_tokens: int = 0
    output_tokens: int = 0

    @classmethod
    def from_litellm(cls, raw: object) -> LLMResponse:
        """Construct from a LiteLLM ``ModelResponse`` object.

        Uses ``getattr`` with safe defaults so the type checker stays happy
        without importing litellm's internal types directly.
        """
        choice = getattr(raw, "choices", [{}])[0]
        message = getattr(choice, "message", None) or {}
        content: str = (
            getattr(message, "content", None)
            or (message.get("content") if isinstance(message, dict) else None)
            or ""
        )
        usage = getattr(raw, "usage", None) or {}
        input_tokens: int = (
            getattr(usage, "prompt_tokens", None)
            or (usage.get("prompt_tokens") if isinstance(usage, dict) else None)
            or 0
        )
        output_tokens: int = (
            getattr(usage, "completion_tokens", None)
            or (usage.get("completion_tokens") if isinstance(usage, dict) else None)
            or 0
        )
        model: str = getattr(raw, "model", "") or ""
        return cls(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )


__all__ = [
    "LLMMessage",
    "ToolInvocation",
    "ToolParameterSpec",
    "ToolMetadata",
    "LLMResponse",
]
