"""``quell incident <verb>`` — Typer entry points.

Phase 3.1 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2).
This module is intentionally thin: it owns the public ``--flag``
surface and the per-command ``--help`` examples, then delegates to
async handlers in :mod:`quell.interface.incident_handlers`.

The old top-level commands (``quell history``, ``show``, ``stats``,
``replay``) become deprecated aliases registered in
:mod:`quell.interface.cli` — they call the same handlers through this
module so the human + JSON contracts only live in one place.
"""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer

from quell.interface.errors import QuellCLIError, handle_cli_error
from quell.interface.incident_handlers import (
    list_handler,
    replay_handler,
    show_handler,
    stats_handler,
)
from quell.interface.output import Output
from quell.utils.timeparse import parse_since

incident_app = typer.Typer(
    name="incident",
    help="Past investigations — list, show, stats, replay.",
    no_args_is_help=True,
)


@incident_app.command("list")
def list_cmd(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max rows to show.")] = 10,
    status: Annotated[
        str | None,
        typer.Option(
            "--status",
            help="Filter: detected, investigating, resolved, failed.",
        ),
    ] = None,
    severity: Annotated[
        str | None,
        typer.Option("--severity", help="Filter: low, medium, high, critical."),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help="Only show incidents seen since (e.g. '1 hour ago', '2026-04-29').",
        ),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of a table.")
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Show recent incidents.

    Examples:
      quell incident list                                    # 10 most recent
      quell incident list --status resolved --severity high  # filter
      quell incident list --since "1 week ago" --limit 50
      quell incident list --json | jq '.data.incidents[].id' # pipe to jq
    """
    out = Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)
    try:
        since_dt = parse_since(since) if since else None
    except QuellCLIError as exc:
        code = handle_cli_error(exc, out)
        raise typer.Exit(code=code) from None

    asyncio.run(
        list_handler(
            out,
            limit=limit,
            status=status,
            severity=severity,
            since_dt=since_dt,
        )
    )


@incident_app.command("show")
def show_cmd(
    incident_id: Annotated[
        str, typer.Argument(help="Incident ID, e.g. 'inc_a1b2c3d4'.")
    ],
    json_mode: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON instead of a key-value list."),
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Show details of a single incident by ID.

    Examples:
      quell incident show inc_a1b2c3d4
      quell incident show inc_a1b2c3d4 --json
    """
    out = Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)
    asyncio.run(show_handler(out, incident_id))


@incident_app.command("stats")
def stats_cmd(
    json_mode: Annotated[
        bool,
        typer.Option("--json", help="Emit JSON instead of a key-value list."),
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Show aggregate incident statistics.

    Examples:
      quell incident stats
      quell incident stats --json
    """
    out = Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)
    asyncio.run(stats_handler(out))


@incident_app.command("replay")
def replay_cmd(
    incident_id: Annotated[str, typer.Argument(help="Incident ID to replay.")],
    json_mode: Annotated[
        bool,
        typer.Option("--json", help="Emit a JSON timeline instead of human output."),
    ] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Print the full event timeline for a past incident investigation.

    Examples:
      quell incident replay inc_a1b2c3d4
      quell incident replay inc_a1b2c3d4 --json > timeline.json
    """
    out = Output(quiet=quiet, json_mode=json_mode, no_color=no_color or None)
    asyncio.run(replay_handler(out, incident_id))


__all__ = ["incident_app"]
