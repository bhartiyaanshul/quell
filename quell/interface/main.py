"""Main Typer CLI application for Quell.

Defines the root ``app`` object and registers the default callback.
Subcommands (init, doctor, version) are registered by importing
``quell.interface.cli`` at the bottom of this module — they attach
themselves to this ``app`` on import.
"""

from __future__ import annotations

import typer

from quell.interface.output import Output
from quell.version import __version__

app = typer.Typer(
    name="quell",
    help="An on-call engineer that never sleeps.",
    no_args_is_help=False,
)


def _print_version(value: bool) -> None:
    """Typer callback that prints the version and exits when --version is given."""
    if value:
        Output().line(f"quell {__version__}")
        raise typer.Exit()


def _emit_help_json(value: bool) -> None:
    """Typer callback that emits ``help.tree`` JSON and exits.

    Imports lazily so the cold-CLI startup path doesn't pay for Click
    introspection unless the flag is actually requested.
    """
    if value:
        from quell.interface.help_json import emit_help_tree

        emit_help_tree(app)
        raise typer.Exit()


def _print_root_summary(out: Output) -> None:
    """Render the no-args landing page per docs/cli-design.md §11.1.

    Shows a small resource list and the most common commands rather
    than dumping the full ``--help`` tree. Users discover details by
    running ``quell <command> --help`` from there.
    """
    out.line("Quell — an on-call engineer that never sleeps.")
    out.line("")
    out.line("Usage:  quell <resource> <verb> [flags]")
    out.line("        quell <verb> [flags]                # global verbs")
    out.line("")
    out.line("Common commands:")
    out.line("  quell init             Configure Quell for a project")
    out.line("  quell watch            Start the investigation loop")
    out.line("  quell incident list    Show recent incidents")
    out.line("  quell doctor           Verify your setup")
    out.line("")
    out.line("Resources:")
    out.line("  incident    Past investigations")
    out.line("  config      Configuration management")
    out.line("  skill       Runbook management")
    out.line("  notifier    Output channel management")
    out.line("")
    out.line("Run `quell <command> --help` for examples and flag details.")


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
    help_json: bool = typer.Option(  # noqa: B008
        False,
        "--help-json",
        help="Emit the full help tree as JSON for tool integration.",
        is_eager=True,
        callback=_emit_help_json,
    ),
) -> None:
    """Quell — autonomous incident response for production systems."""
    # ``version`` and ``help_json`` are handled by their eager callbacks;
    # consume them so mypy/ruff don't complain about unused parameters.
    _ = version, help_json
    if ctx.invoked_subcommand is None:
        _print_root_summary(Output())


# Register subcommands by importing the CLI module.
# This must come after ``app`` is defined to avoid circular import issues.
import quell.interface.cli as _cli  # noqa: E402, F401
