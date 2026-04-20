"""SandboxInfo — identifiers and credentials for one running sandbox."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxInfo:
    """Handle to a running sandbox container.

    Attributes:
        container_id:   Docker container ID.
        host_port:      Random host port mapped to the container's
                        tool-server port (48081).
        bearer_token:   Per-sandbox URL-safe token used for tool-server
                        authentication.
        workspace_path: User's project root, mounted read-only inside
                        the container at ``/workspace``.
        agent_id:       Agent that owns this sandbox (one sandbox per
                        root agent; subagents share the parent's sandbox).
    """

    container_id: str
    host_port: int
    bearer_token: str
    workspace_path: Path
    agent_id: str


__all__ = ["SandboxInfo"]
