"""Main Typer CLI application for Quell.

Defines the root ``app`` object and registers the default callback.
Subcommands (init, doctor, version) are registered by importing
``quell.interface.cli`` at the bottom of this module — they attach
themselves to this ``app`` on import.
"""

from __future__ import annotations

import typer

from quell.version import __version__

app = typer.Typer(
    name="quell",
    help="An on-call engineer that never sleeps.",
    no_args_is_help=False,
)


def _print_version(value: bool) -> None:
    """Typer callback that prints the version and exits when --version is given."""
    if value:
        typer.echo(f"quell {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(  # noqa: B008 — Typer option factory pattern
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        is_eager=True,
        callback=_print_version,
    ),
) -> None:
    """Quell — autonomous incident response for production systems."""
    # ``version`` handled by the eager callback; consume it so mypy/ruff
    # don't complain about the unused parameter.
    _ = version
    if ctx.invoked_subcommand is None:
        typer.echo(f"Quell v{__version__} — run `quell --help` for commands")


# Register subcommands by importing the CLI module.
# This must come after ``app`` is defined to avoid circular import issues.
import quell.interface.cli as _cli  # noqa: E402, F401
