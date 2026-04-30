"""``quell config <verb>`` — Typer entry points.

Phase 3.2 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2).
This module owns the public flag surface and per-command examples,
then delegates to the handlers in :mod:`quell.interface.config_handlers`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from quell.interface.config_handlers import (
    edit_handler,
    get_handler,
    set_handler,
    show_handler,
    validate_handler,
)
from quell.interface.errors import QuellCLIError, handle_cli_error
from quell.interface.output import Output

config_app = typer.Typer(
    name="config",
    help="Configuration management — show, get, set, validate, edit.",
    no_args_is_help=True,
)


def _build_output(json_mode: bool, quiet: bool, no_color: bool) -> Output:
    return Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)


def _safe(out: Output, run: Callable[[], None]) -> None:
    """Render any ``QuellCLIError`` raised by *run* and exit with its code."""
    try:
        run()
    except QuellCLIError as exc:
        code = handle_cli_error(exc, out)
        raise typer.Exit(code=code) from None


@config_app.command("show")
def show_cmd(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of TOML.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Show the merged configuration.

    Examples:
      quell config show
      quell config show --json | jq '.data.config.llm.model'
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: show_handler(out, path))


@config_app.command("get")
def get_cmd(
    key: Annotated[str, typer.Argument(help="Dotted config key, e.g. 'llm.model'.")],
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of the raw value.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Get a single config value by dotted key.

    Examples:
      quell config get llm.model
      quell config get agent.max_iterations --json
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: get_handler(out, key, path))


@config_app.command("set")
def set_cmd(
    key: Annotated[str, typer.Argument(help="Dotted config key, e.g. 'llm.model'.")],
    value: Annotated[
        str, typer.Argument(help="New value (parsed per the field type).")
    ],
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip the confirmation prompt.")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would change without writing.")
    ] = False,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of human output.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Set a config value by dotted key (writes to the local config file).

    Examples:
      quell config set llm.model "anthropic/claude-haiku-4-5" --yes
      quell config set agent.max_iterations 100 --dry-run
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(
        out,
        lambda: set_handler(out, key, value, path=path, yes=yes, dry_run=dry_run),
    )


@config_app.command("validate")
def validate_cmd(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of human output.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Validate the local config file against the schema.

    Examples:
      quell config validate
      quell config validate --json   # 0 = valid, 3 = invalid
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: validate_handler(out, path))


@config_app.command("edit")
def edit_cmd(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Open the local config file in $EDITOR. Validates on save.

    Examples:
      quell config edit              # uses $EDITOR (or vi)
      EDITOR=code-w quell config edit
    """
    out = _build_output(json_mode=False, quiet=False, no_color=no_color)
    _safe(out, lambda: edit_handler(out, path))


__all__ = ["config_app"]
