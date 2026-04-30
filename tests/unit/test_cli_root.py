"""Tests for the root-level CLI behaviour (Phase 5.3).

`quell` with no args shows the resource list + common commands per
docs/cli-design.md §11.1, not the full Typer help dump. This file
locks the contract — if the wording or structure changes, fix here
first so users can re-derive the migration from the test diff.
"""

from __future__ import annotations

from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


def test_no_args_shows_resource_list_not_help_dump() -> None:
    """`quell` alone lists resources + common commands."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0, result.stderr
    out = result.stdout
    # Resource section
    assert "Resources:" in out
    assert "incident" in out
    assert "config" in out
    assert "skill" in out
    assert "notifier" in out
    # Common-commands section
    assert "Common commands:" in out
    assert "quell init" in out
    assert "quell doctor" in out
    # Pointer to deeper help
    assert "--help" in out
    # Confirm we didn't render the verbose Typer help dump.
    # Typer's auto-generated help opens with `Usage:` followed by
    # `[OPTIONS] COMMAND` — our summary uses the spec-shaped form.
    assert "[OPTIONS] COMMAND" not in out


def test_no_args_does_not_print_full_typer_help() -> None:
    """Sanity — confirm `--help` still works and is the verbose dump."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # `--help` is allowed to be verbose — it's the explicit ask.
    # We only enforce that the no-args path isn't the same thing.
    assert "[OPTIONS]" in result.stdout or "Commands" in result.stdout
