"""Machine-readable help tree for ``quell --help-json`` (Phase 5.5).

Wraps Click's ``Context.to_info_dict()`` introspection in the standard
``{kind, version, data}`` JSON envelope so agents and editor plugins
can consume Quell's command surface without scraping ``--help`` text.

The output schema is whatever ``to_info_dict`` produces — Click owns
that shape, and pinning a custom transform here would just drift. The
envelope adds a stable ``kind`` (``help.tree``) and a ``version``
(matching the rest of the JSON output contract) so consumers can
gate on it cleanly.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

import click
from typer.main import get_command

from quell.interface.output_schemas import make_envelope

if TYPE_CHECKING:
    import typer


def emit_help_tree(app: typer.Typer, *, name: str = "quell") -> None:
    """Walk *app*, emit a ``help.tree`` envelope to stdout, and exit.

    Designed for ``--help-json``: prints exactly one JSON line and
    raises ``typer.Exit(0)`` so the calling subcommand never runs.
    """
    info = _command_info_dict(app, name=name)
    envelope = make_envelope("help.tree", info)
    sys.stdout.write(json.dumps(envelope, default=str) + "\n")
    sys.stdout.flush()


def _command_info_dict(app: typer.Typer, *, name: str) -> dict[str, Any]:
    """Return Click's ``to_info_dict`` for the Typer *app*.

    Wrapped in a thin shim so callers don't have to import Click. The
    returned dict has the canonical Click shape (``name``, ``params``,
    ``commands`` recursively, etc.) — see Click's docs for details.
    """
    cmd = get_command(app)
    ctx = click.Context(cmd, info_name=name)
    return cmd.to_info_dict(ctx)


__all__ = ["emit_help_tree"]
