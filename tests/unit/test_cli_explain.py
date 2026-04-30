"""Tests for ``quell explain <command>`` (Phase 5.4).

Locks the long-form-doc output's structural pieces — full path,
docstring, flag block, universal-flag note — so accidental changes
to the rendering or the introspection path are caught.
"""

from __future__ import annotations

from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


def test_explain_incident_list_renders_full_doc() -> None:
    result = runner.invoke(app, ["explain", "incident", "list"])
    assert result.exit_code == 0, result.stderr
    out = result.stdout
    # Path header
    assert "quell incident list" in out
    # Docstring summary preserved
    assert "Show recent incidents." in out
    # Flag table
    assert "--status" in out
    assert "--severity" in out
    # Universal-flag reminder block
    assert "Universal flags" in out


def test_explain_resource_lists_subcommands() -> None:
    """`explain incident` (no verb) lists the four verbs."""
    result = runner.invoke(app, ["explain", "incident"])
    assert result.exit_code == 0, result.stderr
    out = result.stdout
    assert "Subcommands:" in out
    for verb in ("list", "show", "stats", "replay"):
        assert verb in out


def test_explain_unknown_command_exits_not_found() -> None:
    result = runner.invoke(app, ["explain", "doesnt-exist"])
    assert result.exit_code == 7, result.stderr
    assert "doesnt-exist" in result.stderr


def test_explain_no_args_explains_root() -> None:
    result = runner.invoke(app, ["explain"])
    assert result.exit_code == 0, result.stderr
    out = result.stdout
    # The root summary lists every Phase 3 resource as a subcommand.
    assert "Subcommands:" in out
    for resource in ("incident", "config", "skill", "notifier"):
        assert resource in out
