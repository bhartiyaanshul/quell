"""Tests for ``quell skill <verb>`` (Phase 3.3).

Coverage targets the v0.3.0 CLI contract for the ``skill`` resource:
``list`` / ``show`` / ``enable`` / ``disable`` in default and ``--json``
modes, plus the disabled-state round-trip via the local config file.
``database-deadlock`` is a stable bundled skill we use as the fixture
target — if that file ever moves, this test catches it immediately.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)

SKILL = "database-deadlock"


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text("repo_path = '.'\n", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# skill list
# ---------------------------------------------------------------------------


def test_list_default_renders_table(project_dir: Path) -> None:
    result = runner.invoke(app, ["skill", "list", "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr
    assert SKILL in result.stdout
    assert "ENABLED" in result.stdout


def test_list_json_envelope(project_dir: Path) -> None:
    result = runner.invoke(app, ["skill", "list", "--path", str(project_dir), "--json"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "skill.list"
    skills = payload["data"]["skills"]
    assert any(s["name"] == SKILL for s in skills)
    assert all(s["enabled"] for s in skills)


# ---------------------------------------------------------------------------
# skill show
# ---------------------------------------------------------------------------


def test_show_renders_runbook(project_dir: Path) -> None:
    result = runner.invoke(app, ["skill", "show", SKILL, "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr
    assert SKILL in result.stdout
    assert "category:" in result.stdout


def test_show_unknown_exits_not_found(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["skill", "show", "no-such-skill", "--path", str(project_dir)]
    )
    assert result.exit_code == 7, result.stderr
    assert "no-such-skill" in result.stderr


def test_show_json_envelope(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["skill", "show", SKILL, "--path", str(project_dir), "--json"]
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "skill.show"
    assert payload["data"]["name"] == SKILL
    assert payload["data"]["enabled"] is True
    assert payload["data"]["content"]


# ---------------------------------------------------------------------------
# skill disable / enable round-trip
# ---------------------------------------------------------------------------


def test_disable_writes_to_config(project_dir: Path) -> None:
    result = runner.invoke(app, ["skill", "disable", SKILL, "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr
    contents = (project_dir / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert SKILL in contents
    assert "skills" in contents

    # show now reflects disabled state
    show = runner.invoke(
        app, ["skill", "show", SKILL, "--path", str(project_dir), "--json"]
    )
    payload = json.loads(show.stdout)
    assert payload["data"]["enabled"] is False


def test_enable_removes_from_disabled(project_dir: Path) -> None:
    runner.invoke(app, ["skill", "disable", SKILL, "--path", str(project_dir)])
    result = runner.invoke(app, ["skill", "enable", SKILL, "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr

    show = runner.invoke(
        app, ["skill", "show", SKILL, "--path", str(project_dir), "--json"]
    )
    payload = json.loads(show.stdout)
    assert payload["data"]["enabled"] is True


def test_enable_idempotent(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["skill", "enable", SKILL, "--path", str(project_dir), "--json"]
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data"]["changed"] is False


def test_disable_unknown_skill_exits_not_found(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["skill", "disable", "no-such-skill", "--path", str(project_dir)]
    )
    assert result.exit_code == 7, result.stderr
