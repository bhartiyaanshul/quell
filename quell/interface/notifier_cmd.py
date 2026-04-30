"""``quell notifier <verb>`` — Typer entry points.

Phase 3.4 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2).
Thin shims that build an ``Output`` from the universal flags and
delegate to :mod:`quell.interface.notifier_handlers`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from quell.interface.cli_helpers import build_output, safe_run
from quell.interface.notifier_handlers import (
    add_handler,
    list_handler,
    remove_handler,
    test_handler,
)

notifier_app = typer.Typer(
    name="notifier",
    help="Output channels — list, test, add, remove.",
    no_args_is_help=True,
)


@notifier_app.command("list")
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
    """List configured notifier channels and their secret state.

    Examples:
      quell notifier list
      quell notifier list --json | jq '.data.notifiers[] | select(.secret_configured)'
    """
    out = build_output(json_mode=json_mode, quiet=quiet, no_color=no_color)
    safe_run(out, lambda: list_handler(out, path))


@notifier_app.command("test")
def test_cmd(
    channel: Annotated[
        str, typer.Argument(help="Channel to test: slack, discord, or telegram.")
    ],
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
    """Send a synthetic test incident through a configured notifier.

    Examples:
      quell notifier test slack
      quell notifier test discord --json
    """
    out = build_output(json_mode=json_mode, quiet=quiet, no_color=no_color)
    safe_run(out, lambda: asyncio.run(test_handler(out, channel, path)))


@notifier_app.command("add")
def add_cmd(
    channel: Annotated[
        str, typer.Argument(help="Channel to add: slack, discord, or telegram.")
    ],
    chat_id: Annotated[
        str | None,
        typer.Option("--chat-id", help="Telegram chat ID (required for telegram)."),
    ] = None,
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
    """Add a notifier entry to the local config (secret stored separately).

    Examples:
      quell notifier add slack --yes
      quell notifier add telegram --chat-id 12345 --yes
      quell notifier add discord --dry-run
    """
    out = build_output(json_mode=json_mode, quiet=quiet, no_color=no_color)
    safe_run(
        out,
        lambda: add_handler(
            out, channel, chat_id=chat_id, path=path, yes=yes, dry_run=dry_run
        ),
    )


@notifier_app.command("remove")
def remove_cmd(
    channel: Annotated[
        str, typer.Argument(help="Channel to remove: slack, discord, or telegram.")
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
    """Remove a notifier entry from the local config. Idempotent.

    Examples:
      quell notifier remove slack --yes
      quell notifier remove telegram --dry-run
    """
    out = build_output(json_mode=json_mode, quiet=quiet, no_color=no_color)
    safe_run(
        out,
        lambda: remove_handler(out, channel, path=path, yes=yes, dry_run=dry_run),
    )


__all__ = ["notifier_app"]
