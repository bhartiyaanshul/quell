"""Tests for quell.interface.doctor — health check logic."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.doctor import (
    CheckResult,
    check_config,
    check_docker,
    check_git,
    check_github_token,
    check_python_version,
)
from quell.interface.main import app

_runner = CliRunner(mix_stderr=False)

# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


def test_check_result_ok_flag() -> None:
    """CheckResult.ok reflects the supplied boolean."""
    assert CheckResult(name="x", ok=True).ok is True
    assert CheckResult(name="x", ok=False).ok is False


# ---------------------------------------------------------------------------
# check_python_version
# ---------------------------------------------------------------------------


async def test_check_python_version_passes() -> None:
    """Python version check passes on the current interpreter (≥ 3.12)."""
    result = await check_python_version()
    # We're running this test on the same Python, so it must pass
    major, minor = sys.version_info[:2]
    assert result.ok == ((major, minor) >= (3, 12))
    assert result.name == "Python ≥ 3.12"


# ---------------------------------------------------------------------------
# check_git
# ---------------------------------------------------------------------------


async def test_check_git_found() -> None:
    """check_git passes when command_exists returns True."""
    with patch(
        "quell.interface.doctor.command_exists", new=AsyncMock(return_value=True)
    ):
        result = await check_git()
    assert result.ok is True


async def test_check_git_not_found() -> None:
    """check_git fails when command_exists returns False."""
    with patch(
        "quell.interface.doctor.command_exists", new=AsyncMock(return_value=False)
    ):
        result = await check_git()
    assert result.ok is False
    assert "not found" in result.detail


# ---------------------------------------------------------------------------
# check_docker
# ---------------------------------------------------------------------------


async def test_check_docker_running() -> None:
    """check_docker passes when `docker info` returns successfully."""
    from quell.utils.shell import CommandResult

    mock_result = CommandResult(returncode=0, stdout="27.0.3", stderr="")
    with patch(
        "quell.interface.doctor.run_command", new=AsyncMock(return_value=mock_result)
    ):
        result = await check_docker()
    assert result.ok is True
    assert "27.0.3" in result.detail


async def test_check_docker_not_running() -> None:
    """check_docker fails when docker daemon is not responding."""
    from quell.utils.shell import CommandResult

    mock_result = CommandResult(returncode=1, stdout="", stderr="Cannot connect")
    with patch(
        "quell.interface.doctor.run_command", new=AsyncMock(return_value=mock_result)
    ):
        result = await check_docker()
    assert result.ok is False


async def test_check_docker_not_installed() -> None:
    """check_docker fails gracefully when docker is not on PATH."""
    with patch(
        "quell.interface.doctor.run_command",
        new=AsyncMock(side_effect=FileNotFoundError),
    ):
        result = await check_docker()
    assert result.ok is False
    assert "docker not found" in result.detail


# ---------------------------------------------------------------------------
# check_config
# ---------------------------------------------------------------------------


async def test_check_config_no_file(tmp_path: Path) -> None:
    """check_config passes even with no config file (defaults are valid)."""
    result = await check_config(tmp_path)
    assert result.ok is True


async def test_check_config_invalid_toml(tmp_path: Path) -> None:
    """check_config fails when .quell/config.toml is malformed."""
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text("not = [valid toml", encoding="utf-8")
    result = await check_config(tmp_path)
    assert result.ok is False


async def test_check_config_valid_toml(tmp_path: Path) -> None:
    """check_config passes with a valid minimal config.toml."""
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text(
        '[llm]\nmodel = "openai/gpt-4o"\n', encoding="utf-8"
    )
    result = await check_config(tmp_path)
    assert result.ok is True


# ---------------------------------------------------------------------------
# check_github_token
# ---------------------------------------------------------------------------


async def test_check_github_token_not_set() -> None:
    """check_github_token fails when no token is in the keychain."""
    with patch("quell.interface.doctor.get_secret", return_value=None):
        result = await check_github_token()
    assert result.ok is False
    assert "Not set" in result.detail


async def test_check_github_token_valid() -> None:
    """check_github_token passes when GitHub API returns 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"login": "testuser"}

    with (
        patch("quell.interface.doctor.get_secret", return_value="ghp_faketoken"),
        patch("httpx.AsyncClient") as mock_client_class,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        result = await check_github_token()

    assert result.ok is True
    assert "testuser" in result.detail


async def test_check_github_token_invalid() -> None:
    """check_github_token fails when GitHub API returns 401."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {}

    with (
        patch("quell.interface.doctor.get_secret", return_value="ghp_badtoken"),
        patch("httpx.AsyncClient") as mock_client_class,
    ):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client
        result = await check_github_token()

    assert result.ok is False


# ---------------------------------------------------------------------------
# CLI integration — --json envelope and --quiet exit code (Phase 3.5)
# ---------------------------------------------------------------------------


def test_doctor_json_envelope(tmp_path: Path) -> None:
    """`quell doctor --json` emits a doctor.run envelope on stdout."""
    result = _runner.invoke(app, ["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(result.stdout)
    assert payload["kind"] == "doctor.run"
    assert payload["version"] == "0.3"
    assert "checks" in payload["data"]
    assert isinstance(payload["data"]["passed"], int)
    assert isinstance(payload["data"]["failed"], int)


def test_doctor_quiet_suppresses_output(tmp_path: Path) -> None:
    """`quell doctor --quiet` keeps stdout clean; exit code is the signal."""
    result = _runner.invoke(app, ["doctor", "--path", str(tmp_path), "--quiet"])
    assert result.stdout.strip() == ""
    # exit_code is 1 if any check failed (likely in CI), else 0 — both are valid.
    assert result.exit_code in (0, 1)


# ---------------------------------------------------------------------------
# check_single_install (Phase 6.1)
# ---------------------------------------------------------------------------


async def test_check_single_install_passes_with_no_quell_on_path(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    """Running from source / pytest: no `quell` on PATH is a pass."""
    from quell.interface.doctor import check_single_install

    monkeypatch.setattr("quell.interface.doctor._find_quell_binaries", lambda: [])
    result = await check_single_install()
    assert result.ok is True


async def test_check_single_install_passes_with_one_binary(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    from quell.interface.doctor import check_single_install

    monkeypatch.setattr(
        "quell.interface.doctor._find_quell_binaries",
        lambda: [Path("/Users/dev/.local/bin/quell")],
    )
    result = await check_single_install()
    assert result.ok is True
    assert "/Users/dev/.local/bin/quell" in result.detail


async def test_check_single_install_fails_with_multiple(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    """Multiple distinct binaries — flag with the corrective command."""
    from quell.interface.doctor import check_single_install

    monkeypatch.setattr(
        "quell.interface.doctor._find_quell_binaries",
        lambda: [
            Path("/Users/dev/.local/bin/quell"),
            Path("/opt/homebrew/bin/quell"),
        ],
    )
    result = await check_single_install()
    assert result.ok is False
    assert "2" in result.detail
    assert "pip uninstall" in result.detail
