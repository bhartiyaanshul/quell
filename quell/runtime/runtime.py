"""AbstractRuntime — the protocol every sandbox runtime must implement."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from quell.runtime.sandbox_info import SandboxInfo


class AbstractRuntime(Protocol):
    """Protocol describing the three operations the agent loop needs.

    Implementations: :class:`~quell.runtime.docker_runtime.DockerRuntime`
    (production), plus whatever test doubles tests construct.
    """

    async def create_sandbox(self, workspace: Path, agent_id: str) -> SandboxInfo:
        """Start a new sandbox container and return its handle.

        The sandbox is not considered ready until the tool server
        inside reports healthy; implementations should wait for that
        before returning.
        """
        ...

    async def destroy_sandbox(self, info: SandboxInfo) -> None:
        """Stop and remove the sandbox container identified by *info*."""
        ...

    async def get_tool_server_url(self, info: SandboxInfo) -> str:
        """Return the base URL the host can use to reach the tool server."""
        ...


__all__ = ["AbstractRuntime"]
