"""CLI command definitions for Quell.

Imports the shared Typer ``app`` from ``quell.interface.main`` and
registers global verbs (``init``, ``doctor``, ``watch``, ``dashboard``,
``version``) plus resource sub-apps. Phase 3.1 adds the ``incident``
resource (see ``docs/cli-design.md`` §3); the old top-level ``history``
/ ``show`` / ``stats`` / ``replay`` commands remain as deprecated
aliases that emit a stderr warning and forward to the same handlers.

This module must be imported by ``main.py`` to activate the commands.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from quell.interface.config_cmd import config_app
from quell.interface.incident_cmd import incident_app
from quell.interface.incident_handlers import (
    list_handler,
    replay_handler,
    show_handler,
    stats_handler,
)
from quell.interface.main import app
from quell.interface.output import Output
from quell.interface.skill_cmd import skill_app
from quell.version import __version__

# Resource sub-apps. Phase 3.4 will add notifier.
app.add_typer(incident_app, name="incident")
app.add_typer(config_app, name="config")
app.add_typer(skill_app, name="skill")


def _emit_deprecation(old: str, new: str) -> None:
    """Print a deprecation warning to stderr.

    Goes to stderr regardless of ``--json`` / ``--quiet`` so JSON output
    on stdout stays clean and CI logs still surface the migration hint.
    Stable prefix (``[deprecation]``) so parsers can grep for it.

    Uses ``typer.echo(err=True)`` rather than raw ``sys.stderr.write`` so
    Click's ``CliRunner`` captures it correctly under ``mix_stderr=False``.
    """
    typer.echo(
        f"[deprecation] '{old}' is deprecated; use '{new}' instead. "
        "(will be removed in v0.4.0)",
        err=True,
    )


@app.command()
def init(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to configure (defaults to current directory).",
            exists=False,
        ),
    ] = None,
) -> None:
    """Run the interactive setup wizard to configure Quell for a project."""
    from quell.interface.wizard import run_init

    run_init(path)


@app.command()
def doctor(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to check (defaults to current directory).",
        ),
    ] = None,
) -> None:
    """Check your environment and configuration for issues."""
    from quell.interface.doctor import run_doctor

    ok = run_doctor(path)
    if not ok:
        raise typer.Exit(code=1)


@app.command(name="version")
def show_version() -> None:
    """Print the installed Quell version and exit."""
    Output().line(f"quell {__version__}")


@app.command()
def watch(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to watch (defaults to current directory).",
        ),
    ] = None,
) -> None:
    """Start the monitor -> detector -> agent investigation loop."""
    from quell.config.loader import load_config
    from quell.watch import watch as run_watch

    config = load_config(local_dir=path, inject_secrets=True)
    try:
        asyncio.run(run_watch(config))
    except KeyboardInterrupt:
        Output().info("(quell watch: interrupted)")


@app.command()
def dashboard(
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to bind the dashboard on."),
    ] = 7777,
    host: Annotated[
        str,
        typer.Option("--host", help="Interface to bind to (default localhost)."),
    ] = "127.0.0.1",
    no_open: Annotated[
        bool,
        typer.Option("--no-open", help="Do not auto-open the browser."),
    ] = False,
) -> None:
    """Launch the read-only web dashboard on the local machine."""
    from quell.dashboard.launcher import run_dashboard_sync

    try:
        run_dashboard_sync(host=host, port=port, open_browser=not no_open)
    except KeyboardInterrupt:
        Output().info("(quell dashboard: interrupted)")


@app.command(name="test-notifier")
def test_notifier(
    channel: Annotated[
        str,
        typer.Argument(
            help="Notifier type to exercise: 'slack', 'discord', or 'telegram'."
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory whose config to load.",
        ),
    ] = None,
) -> None:
    """Send a synthetic test incident through a configured notifier."""
    from quell.interface.notifier_test import run_test_notifier

    ok = asyncio.run(run_test_notifier(channel=channel, project_dir=path))
    if not ok:
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Deprecated aliases — forward to the ``incident`` sub-app handlers.
# Removed in v0.4.0 per docs/cli-design.md §3.4.
# ---------------------------------------------------------------------------


@app.command()
def history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max rows to show.")] = 10,
) -> None:
    """[deprecated] Use ``quell incident list`` instead."""
    _emit_deprecation("quell history", "quell incident list")
    asyncio.run(
        list_handler(
            Output(),
            limit=limit,
            status=None,
            severity=None,
            since_dt=None,
        )
    )


@app.command()
def show(incident_id: str) -> None:
    """[deprecated] Use ``quell incident show <id>`` instead."""
    _emit_deprecation("quell show", "quell incident show")
    asyncio.run(show_handler(Output(), incident_id))


@app.command()
def stats() -> None:
    """[deprecated] Use ``quell incident stats`` instead."""
    _emit_deprecation("quell stats", "quell incident stats")
    asyncio.run(stats_handler(Output()))


@app.command()
def replay(incident_id: str) -> None:
    """[deprecated] Use ``quell incident replay <id>`` instead."""
    _emit_deprecation("quell replay", "quell incident replay")
    asyncio.run(replay_handler(Output(), incident_id))


__all__ = [
    "dashboard",
    "doctor",
    "history",
    "init",
    "replay",
    "show",
    "show_version",
    "stats",
    "test_notifier",
    "watch",
]
