"""Runtime-specific exception subclasses."""

from __future__ import annotations

from quell.utils.errors import SandboxError


class SandboxStartError(SandboxError):
    """The sandbox container failed to start."""


class SandboxHealthCheckError(SandboxError):
    """The sandbox started but never became healthy."""


class SandboxNotFoundError(SandboxError):
    """A sandbox container referenced by ID does not exist."""


__all__ = [
    "SandboxStartError",
    "SandboxHealthCheckError",
    "SandboxNotFoundError",
]
