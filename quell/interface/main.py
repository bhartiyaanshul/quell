"""Main Typer CLI application for Quell."""

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
        typer.echo(f"Quell v{__version__} — coming soon")
