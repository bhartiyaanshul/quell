"""Smoke test for the ``quell version`` subcommand.

The original Phase 15 ``history`` / ``show`` / ``stats`` tests have
moved to ``test_cli_incident.py`` along with the resource-style
commands and their deprecated aliases (Phase 3.1). What remains here
is the ``version`` subcommand — kept as an alias for ``--version``
per ``docs/cli-design.md`` §3.4 and useful as a no-fixture sanity
check that the Typer app still wires up cleanly.
"""

from __future__ import annotations

from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner()


def test_version_command_prints_version_with_binary_path() -> None:
    """`quell version` shows `quell <ver> (<binary path>)` per cli-design §4.

    Phase 6.2 — the resolved binary path is appended in parentheses so
    users can tell which install is running without `which -a quell`.
    """
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.startswith("quell ")
    # Binary path is parenthesised; assert structurally rather than
    # against an exact path (CI vs. local dev paths differ).
    assert "(" in result.stdout
    assert ")" in result.stdout


def test_root_version_flag_matches_subcommand() -> None:
    """`quell --version` should mirror `quell version`."""
    flag = runner.invoke(app, ["--version"])
    sub = runner.invoke(app, ["version"])
    assert flag.exit_code == 0
    assert sub.exit_code == 0
    assert flag.stdout == sub.stdout
