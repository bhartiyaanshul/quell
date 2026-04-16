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
    typer.echo(f"quell-agent {__version__}")


__all__ = ["init", "doctor", "show_version"]
