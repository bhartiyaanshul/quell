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


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.startswith("quell ")
