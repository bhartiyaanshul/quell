"""Typed exception hierarchy for Quell.

All errors raised by Quell are subclasses of `QuellError`.
Catch `QuellError` to handle any Quell-originated exception;
catch a specific subclass to handle a particular failure domain.
"""

from __future__ import annotations


class QuellError(Exception):
    """Base exception for all errors raised by Quell."""


class ConfigError(QuellError):
    """Configuration loading or validation failed."""


class MonitorError(QuellError):
    """A monitor adapter encountered an unrecoverable error."""


class AgentError(QuellError):
    """An agent encountered an error during execution."""


class ToolError(QuellError):
    """A tool execution failed."""


class SandboxError(QuellError):
    """Sandbox (Docker container) lifecycle error."""


class LLMError(QuellError):
    """LLM communication or parsing error."""


class SkillError(QuellError):
    """Skill file parsing or loading error."""


__all__ = [
    "QuellError",
    "ConfigError",
    "MonitorError",
    "AgentError",
    "ToolError",
    "SandboxError",
    "LLMError",
    "SkillError",
]
