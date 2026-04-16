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
    help="Your production's autonomous on-call.",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Quell — autonomous incident response for production systems."""
    if ctx.invoked_subcommand is None:
        typer.echo(f"Quell v{__version__} — run `quell --help` for commands")


# Register subcommands by importing the CLI module.
# This must come after ``app`` is defined to avoid circular import issues.
import quell.interface.cli as _cli  # noqa: E402, F401
