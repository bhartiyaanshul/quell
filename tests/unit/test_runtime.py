"""Tests for quell.runtime — mocked Docker SDK."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quell.config.schema import SandboxConfig
from quell.runtime import (
    DockerRuntime,
    SandboxHealthCheckError,
    SandboxInfo,
    SandboxStartError,
)


class _FakeContainer:
    def __init__(self, container_id: str = "abc123def456", host_port: int = 49152):
        self.id = container_id
        self._host_port = host_port
        self.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "48081/tcp": [{"HostIp": "0.0.0.0", "HostPort": str(host_port)}]
                }
            }
        }
        self.stop = MagicMock()
        self.remove = MagicMock()

    def reload(self) -> None:
        pass


class _FakeClient:
    def __init__(self, container: _FakeContainer | None = None):
        self.containers = MagicMock()
        self.containers.run = MagicMock(return_value=container or _FakeContainer())
        self.containers.get = MagicMock(return_value=container or _FakeContainer())


@pytest.fixture
def fake_workspace(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("demo", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# create_sandbox — happy path (mocked health check)
# ---------------------------------------------------------------------------


async def test_create_sandbox_returns_info(fake_workspace: Path) -> None:
    client = _FakeClient(_FakeContainer(container_id="cid123", host_port=49200))

    async def _ok(info):  # type: ignore[no-untyped-def]
        return None

    with patch("quell.runtime.docker_runtime._wait_for_health", new=_ok):
        rt = DockerRuntime(SandboxConfig(), client=client)
        info = await rt.create_sandbox(fake_workspace, agent_id="agent-1")

    assert isinstance(info, SandboxInfo)
    assert info.container_id == "cid123"
    assert info.host_port == 49200
    assert info.agent_id == "agent-1"
    assert info.workspace_path == fake_workspace
    assert len(info.bearer_token) >= 32

    # Called docker run with the expected kwargs
    _, kwargs = client.containers.run.call_args
    assert kwargs["detach"] is True
    assert kwargs["volumes"][str(fake_workspace.resolve())]["mode"] == "ro"
    assert kwargs["environment"]["QUELL_INSIDE_SANDBOX"] == "1"
    assert kwargs["environment"]["QUELL_AGENT_ID"] == "agent-1"
    assert "QUELL_BEARER_TOKEN" in kwargs["environment"]


async def test_create_sandbox_rejects_missing_workspace(tmp_path: Path) -> None:
    rt = DockerRuntime(SandboxConfig(), client=_FakeClient())
    with pytest.raises(SandboxStartError, match="does not exist"):
        await rt.create_sandbox(tmp_path / "nope", agent_id="a")


async def test_create_sandbox_wraps_docker_errors(fake_workspace: Path) -> None:
    client = _FakeClient()
    client.containers.run.side_effect = RuntimeError("docker daemon not running")
    rt = DockerRuntime(SandboxConfig(), client=client)
    with pytest.raises(SandboxStartError, match="docker daemon"):
        await rt.create_sandbox(fake_workspace, agent_id="a")


async def test_create_sandbox_destroys_on_health_fail(fake_workspace: Path) -> None:
    container = _FakeContainer()
    client = _FakeClient(container)

    async def _fail(info):  # type: ignore[no-untyped-def]
        raise SandboxHealthCheckError("never ready")

    with patch("quell.runtime.docker_runtime._wait_for_health", new=_fail):
        rt = DockerRuntime(SandboxConfig(), client=client)
        with pytest.raises(SandboxHealthCheckError):
            await rt.create_sandbox(fake_workspace, agent_id="a")

    container.stop.assert_called_once()
    container.remove.assert_called_once()


# ---------------------------------------------------------------------------
# destroy_sandbox — idempotent, never raises
# ---------------------------------------------------------------------------


async def test_destroy_sandbox_calls_stop_and_remove(tmp_path: Path) -> None:
    container = _FakeContainer()
    client = _FakeClient(container)
    rt = DockerRuntime(SandboxConfig(), client=client)
    info = SandboxInfo(
        container_id="cid",
        host_port=49200,
        bearer_token="tok",
        workspace_path=tmp_path,
        agent_id="a",
    )
    await rt.destroy_sandbox(info)
    container.stop.assert_called_once()
    container.remove.assert_called_once()


async def test_destroy_sandbox_handles_missing_container(tmp_path: Path) -> None:
    client = _FakeClient()
    client.containers.get.side_effect = RuntimeError("not found")
    rt = DockerRuntime(SandboxConfig(), client=client)
    # Must not raise.
    info = SandboxInfo(
        container_id="cid",
        host_port=49200,
        bearer_token="tok",
        workspace_path=tmp_path,
        agent_id="a",
    )
    await rt.destroy_sandbox(info)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


async def test_tool_server_url(tmp_path: Path) -> None:
    rt = DockerRuntime(SandboxConfig(), client=_FakeClient())
    info = SandboxInfo(
        container_id="cid",
        host_port=49200,
        bearer_token="tok",
        workspace_path=tmp_path,
        agent_id="a",
    )
    assert await rt.get_tool_server_url(info) == "http://127.0.0.1:49200"


def test_bearer_token_is_url_safe() -> None:
    # secrets.token_urlsafe output: A-Z, a-z, 0-9, -, _
    import secrets

    tok = secrets.token_urlsafe(32)
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert set(tok) <= allowed
