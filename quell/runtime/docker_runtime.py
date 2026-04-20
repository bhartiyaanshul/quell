"""DockerRuntime — the default sandbox runtime backed by the Docker SDK.

Lifecycle:

1. :meth:`create_sandbox` pulls the image (no-op if cached), generates a
   bearer token, starts the container with the workspace mounted
   read-only, then polls ``GET /health`` until it returns 200 or the
   timeout elapses.
2. :meth:`destroy_sandbox` stops and removes the container, best-effort.

The Docker SDK is synchronous; we wrap its calls in ``asyncio.to_thread``
so we don't block the event loop.  Tests patch the client entirely.
"""

from __future__ import annotations

import asyncio
import secrets
from pathlib import Path
from typing import cast

import httpx
from loguru import logger

from quell.config.schema import SandboxConfig
from quell.runtime.errors import (
    SandboxHealthCheckError,
    SandboxStartError,
)
from quell.runtime.sandbox_info import SandboxInfo

# The docker SDK has no py.typed marker; we keep it at ``object`` here
# and narrow locally.  Tests inject a duck-typed fake with the same
# ``.containers.run`` / ``.containers.get`` / ``.reload`` shape.
DockerClient = object

_TOOL_SERVER_PORT = 48081
_HEALTH_TIMEOUT = 30.0
_HEALTH_POLL_INTERVAL = 0.5


class DockerRuntime:
    """Docker-backed implementation of :class:`AbstractRuntime`."""

    def __init__(
        self,
        config: SandboxConfig | None = None,
        *,
        client: object | None = None,
    ) -> None:
        """Build a runtime.

        Args:
            config: Sandbox config (image, limits, network whitelist).
                    Defaults are sensible for local development.
            client: Pre-built Docker client.  Tests inject a fake here.
                    When ``None``, a real client is constructed on first
                    use via ``docker.from_env()``.
        """
        self._config = config or SandboxConfig()
        self._client: object | None = client

    # ------------------------------------------------------------------
    # Client bootstrap (lazy so tests can run without Docker)
    # ------------------------------------------------------------------

    def _get_client(self) -> object:
        if self._client is None:
            import docker as docker_sdk  # noqa: PLC0415

            self._client = docker_sdk.from_env()
        return self._client

    # ------------------------------------------------------------------
    # AbstractRuntime protocol
    # ------------------------------------------------------------------

    async def create_sandbox(self, workspace: Path, agent_id: str) -> SandboxInfo:
        """Start a sandbox container for *agent_id* mounting *workspace*.

        Raises:
            :class:`SandboxStartError`:       Container failed to start.
            :class:`SandboxHealthCheckError`: Container never became ready.
        """
        if not workspace.exists():
            raise SandboxStartError(f"Workspace does not exist: {workspace}")

        client: object = self._get_client()
        bearer_token = secrets.token_urlsafe(32)
        limits = self._config.limits

        try:
            container: object = await asyncio.to_thread(
                client.containers.run,  # type: ignore[attr-defined]  # duck-typed Docker SDK
                self._config.image,
                detach=True,
                auto_remove=False,
                ports={f"{_TOOL_SERVER_PORT}/tcp": None},  # random host port
                volumes={
                    str(workspace.resolve()): {
                        "bind": "/workspace",
                        "mode": "ro",
                    }
                },
                environment={
                    "QUELL_INSIDE_SANDBOX": "1",
                    "QUELL_BEARER_TOKEN": bearer_token,
                    "QUELL_AGENT_ID": agent_id,
                },
                mem_limit=f"{limits.memory_mb}m",
                nano_cpus=int(limits.cpus * 1_000_000_000),
                labels={"quell.agent_id": agent_id},
            )
        except Exception as exc:  # noqa: BLE001
            raise SandboxStartError(
                f"Failed to start sandbox container: {exc}"
            ) from exc

        # Reload to pick up the random host-side port binding.
        await asyncio.to_thread(container.reload)  # type: ignore[attr-defined]
        host_port = _extract_host_port(container)

        info = SandboxInfo(
            container_id=str(container.id),  # type: ignore[attr-defined]
            host_port=host_port,
            bearer_token=bearer_token,
            workspace_path=workspace,
            agent_id=agent_id,
        )

        try:
            await _wait_for_health(info)
        except SandboxHealthCheckError:
            # Destroy the broken container before giving up so we don't
            # leak resources between failed runs.
            await self.destroy_sandbox(info)
            raise

        logger.info(
            "sandbox ready: agent={} container={} port={}",
            agent_id,
            str(container.id)[:12],  # type: ignore[attr-defined]
            host_port,
        )
        return info

    async def destroy_sandbox(self, info: SandboxInfo) -> None:
        """Stop and remove the container; never raises."""
        client = self._get_client()
        try:
            container: object = await asyncio.to_thread(
                client.containers.get,  # type: ignore[attr-defined]
                info.container_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sandbox destroy: container {} not found: {}",
                info.container_id[:12],
                exc,
            )
            return

        try:
            await asyncio.to_thread(container.stop, timeout=10)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.warning("sandbox stop error: {}", exc)

        try:
            await asyncio.to_thread(container.remove, force=True)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            logger.warning("sandbox remove error: {}", exc)

    async def get_tool_server_url(self, info: SandboxInfo) -> str:
        """Return the base URL the host uses to reach the tool server."""
        return f"http://127.0.0.1:{info.host_port}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_host_port(container: object) -> int:
    """Pull the dynamically allocated host port for the tool-server."""
    attrs = cast(
        dict[str, object],
        container.attrs,  # type: ignore[attr-defined]
    )
    ports = cast(
        dict[str, list[dict[str, str]] | None],
        cast(dict[str, object], attrs.get("NetworkSettings", {})).get("Ports", {}),
    )
    bindings = ports.get(f"{_TOOL_SERVER_PORT}/tcp")
    if not bindings:
        raise SandboxStartError(f"Container did not expose port {_TOOL_SERVER_PORT}")
    host_port = int(bindings[0]["HostPort"])
    return host_port


async def _wait_for_health(info: SandboxInfo) -> None:
    """Poll ``/health`` until success or timeout."""
    url = f"http://127.0.0.1:{info.host_port}/health"
    headers = {"Authorization": f"Bearer {info.bearer_token}"}
    deadline = asyncio.get_event_loop().time() + _HEALTH_TIMEOUT
    last_error: str = ""
    async with httpx.AsyncClient(timeout=2.0) as client:
        while asyncio.get_event_loop().time() < deadline:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            except httpx.HTTPError as exc:
                last_error = str(exc)
            await asyncio.sleep(_HEALTH_POLL_INTERVAL)
    raise SandboxHealthCheckError(
        f"Sandbox health check timed out after {_HEALTH_TIMEOUT}s: {last_error}"
    )


__all__ = ["DockerRuntime"]
