"""``quell skill <verb>`` — Typer entry points.

Phase 3.3 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2).
Thin shims that build an ``Output`` from the universal flags and
delegate to :mod:`quell.interface.skill_handlers`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from quell.interface.errors import QuellCLIError, handle_cli_error
from quell.interface.output import Output
from quell.interface.skill_handlers import (
    disable_handler,
    enable_handler,
    list_handler,
    show_handler,
)

skill_app = typer.Typer(
    name="skill",
    help="Runbook management — list, show, enable, disable.",
    no_args_is_help=True,
)


def _build_output(json_mode: bool, quiet: bool, no_color: bool) -> Output:
    return Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)


def _safe(out: Output, run: Callable[[], None]) -> None:
    try:
        run()
    except QuellCLIError as exc:
        code = handle_cli_error(exc, out)
        raise typer.Exit(code=code) from None


@skill_app.command("list")
def list_cmd(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project directory (defaults to cwd)."),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of a table.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """List every bundled skill with its enabled state.

    Examples:
      quell skill list
      quell skill list --json | jq '.data.skills[] | select(.enabled)'
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: list_handler(out, path))


@skill_app.command("show")
def show_cmd(
    name: Annotated[str, typer.Argument(help="Skill slug, e.g. 'postgres-deadlock'.")],
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
    """Show full details for a single skill, including its runbook body.

    Examples:
      quell skill show postgres-deadlock
      quell skill show stripe-webhook-timeout --json
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: show_handler(out, name, path))


@skill_app.command("enable")
def enable_cmd(
    name: Annotated[str, typer.Argument(help="Skill slug to enable.")],
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
    """Re-enable a disabled skill (idempotent — already-enabled is a no-op).

    Examples:
      quell skill enable postgres-deadlock
      quell skill enable stripe-webhook-timeout --json
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: enable_handler(out, name, path))


@skill_app.command("disable")
def disable_cmd(
    name: Annotated[str, typer.Argument(help="Skill slug to disable.")],
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
    """Disable a skill so the watch loop stops auto-loading it.

    Examples:
      quell skill disable postgres-deadlock
      quell skill disable stripe-webhook-timeout --json
    """
    out = _build_output(json_mode, quiet, no_color)
    _safe(out, lambda: disable_handler(out, name, path))


__all__ = ["skill_app"]
