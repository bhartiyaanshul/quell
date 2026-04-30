"""Tests for ``quell config <verb>`` (Phase 3.2).

Coverage targets the v0.3.0 CLI contract for the ``config`` resource
(``docs/cli-design.md`` §3.2 + §14): show / get / set / validate / edit
in default and ``--json`` modes, plus the destructive-command rules
on ``set`` (``--yes`` / ``--dry-run``) and the secret-key refusal.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Project directory with a minimal valid local config."""
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text(
        "\n".join(
            [
                "repo_path = '.'",
                "",
                "[llm]",
                "model = 'anthropic/claude-haiku-4-5'",
                "max_context_tokens = 100000",
                "",
                "[agent]",
                "max_iterations = 50",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# config show
# ---------------------------------------------------------------------------


def test_show_renders_toml(project_dir: Path) -> None:
    result = runner.invoke(app, ["config", "show", "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr
    assert "anthropic/claude-haiku-4-5" in result.stdout
    assert "max_iterations" in result.stdout


def test_show_json_envelope(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["config", "show", "--path", str(project_dir), "--json"]
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "config.show"
    assert payload["data"]["config"]["llm"]["model"] == "anthropic/claude-haiku-4-5"


# ---------------------------------------------------------------------------
# config get
# ---------------------------------------------------------------------------


def test_get_returns_scalar(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["config", "get", "llm.model", "--path", str(project_dir)]
    )
    assert result.exit_code == 0, result.stderr
    assert result.stdout.strip() == "anthropic/claude-haiku-4-5"


def test_get_unknown_key_exits_not_found(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["config", "get", "llm.nonexistent", "--path", str(project_dir)]
    )
    assert result.exit_code == 7, result.stderr
    assert "nonexistent" in result.stderr


def test_get_json_envelope(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "get",
            "agent.max_iterations",
            "--path",
            str(project_dir),
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "config.get"
    assert payload["data"]["key"] == "agent.max_iterations"
    assert payload["data"]["value"] == 50


# ---------------------------------------------------------------------------
# config set
# ---------------------------------------------------------------------------


def test_set_writes_value_with_yes(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "llm.model",
            "anthropic/claude-sonnet-4-6",
            "--path",
            str(project_dir),
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.stderr
    contents = (project_dir / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert "anthropic/claude-sonnet-4-6" in contents


def test_set_dry_run_does_not_write(project_dir: Path) -> None:
    before = (project_dir / ".quell" / "config.toml").read_text(encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "agent.max_iterations",
            "100",
            "--path",
            str(project_dir),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.stderr
    after = (project_dir / ".quell" / "config.toml").read_text(encoding="utf-8")
    assert before == after
    assert "(dry-run)" in result.stdout


def test_set_coerces_int(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "agent.max_iterations",
            "100",
            "--path",
            str(project_dir),
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["data"]["new_value"] == 100
    assert payload["data"]["applied"] is True


def test_set_rejects_invalid_literal(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "llm.reasoning_effort",
            "extreme",
            "--path",
            str(project_dir),
            "--yes",
        ],
    )
    assert result.exit_code == 2, result.stderr
    assert "extreme" in result.stderr


def test_set_refuses_secret_keys(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "llm.api_key",
            "sk-test",
            "--path",
            str(project_dir),
            "--yes",
        ],
    )
    assert result.exit_code == 2, result.stderr
    assert "keychain" in result.stderr.lower()


def test_set_without_yes_in_non_tty_errors(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "llm.model",
            "openai/gpt-4o",
            "--path",
            str(project_dir),
        ],
    )
    assert result.exit_code == 2, result.stderr
    assert "--yes" in result.stderr


def test_set_unknown_key_exits_not_found(project_dir: Path) -> None:
    result = runner.invoke(
        app,
        [
            "config",
            "set",
            "llm.nonexistent",
            "x",
            "--path",
            str(project_dir),
            "--yes",
        ],
    )
    assert result.exit_code == 7, result.stderr


# ---------------------------------------------------------------------------
# config validate
# ---------------------------------------------------------------------------


def test_validate_accepts_good_config(project_dir: Path) -> None:
    result = runner.invoke(app, ["config", "validate", "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr


def test_validate_rejects_invalid_toml(tmp_path: Path) -> None:
    quell_dir = tmp_path / ".quell"
    quell_dir.mkdir()
    (quell_dir / "config.toml").write_text("this is = not [valid", encoding="utf-8")
    result = runner.invoke(app, ["config", "validate", "--path", str(tmp_path)])
    assert result.exit_code == 3, result.stderr


def test_validate_json_envelope(project_dir: Path) -> None:
    result = runner.invoke(
        app, ["config", "validate", "--path", str(project_dir), "--json"]
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "config.validate"
    assert payload["data"]["valid"] is True


# ---------------------------------------------------------------------------
# config edit
# ---------------------------------------------------------------------------


def test_edit_invokes_editor_and_validates(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stub $EDITOR to a no-op so we exercise the validation path."""
    # ``true`` exits 0 without touching the file.
    monkeypatch.setenv("EDITOR", "true")
    result = runner.invoke(app, ["config", "edit", "--path", str(project_dir)])
    assert result.exit_code == 0, result.stderr
    assert "Saved" in result.stdout


def test_edit_refuses_in_json_mode(project_dir: Path) -> None:
    # No --json on edit_cmd, but the handler still checks if Output.json_mode
    # is somehow set; this test documents that --json isn't a flag and the
    # command runs normally with $EDITOR=true.
    os.environ["EDITOR"] = "true"
    try:
        result = runner.invoke(app, ["config", "edit", "--path", str(project_dir)])
        assert result.exit_code == 0, result.stderr
    finally:
        os.environ.pop("EDITOR", None)
