"""CLI command definitions for Quell.

Imports the shared Typer ``app`` from ``quell.interface.main`` and
registers ``init``, ``doctor``, and ``version`` as subcommands.
This module must be imported by ``main.py`` to activate the commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from quell.interface.main import app
from quell.interface.output import Output
from quell.version import __version__


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
    import asyncio

    from quell.config.loader import load_config
    from quell.watch import watch as run_watch

    config = load_config(local_dir=path, inject_secrets=True)
    try:
        asyncio.run(run_watch(config))
    except KeyboardInterrupt:
        Output().info("(quell watch: interrupted)")


@app.command()
def history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max rows to show.")] = 10,
) -> None:
    """Show the most recent incidents."""
    import asyncio

    from quell.interface.history import print_history

    asyncio.run(print_history(limit))


@app.command()
def show(incident_id: str) -> None:
    """Show details of a single incident by ID."""
    import asyncio

    from quell.interface.history import print_incident

    asyncio.run(print_incident(incident_id))


@app.command()
def stats() -> None:
    """Show aggregate incident statistics."""
    import asyncio

    from quell.interface.history import print_stats

    asyncio.run(print_stats())


@app.command()
def replay(incident_id: str) -> None:
    """Print the full event timeline for a past incident investigation."""
    import asyncio

    from quell.interface.replay import run_replay

    ok = asyncio.run(run_replay(incident_id))
    if not ok:
        raise typer.Exit(code=1)


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
    import asyncio

    from quell.interface.notifier_test import run_test_notifier

    ok = asyncio.run(run_test_notifier(channel=channel, project_dir=path))
    if not ok:
        raise typer.Exit(code=1)


__all__ = [
    "init",
    "doctor",
    "show_version",
    "watch",
    "history",
    "show",
    "stats",
    "test_notifier",
    "dashboard",
    "replay",
]
