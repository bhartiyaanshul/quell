"""``quell explain <command>`` — verbose, agent-friendly command docs.

Phase 5.4 of the v0.3.0 redesign. Where ``--help`` is terse and
``--help-json`` is machine-readable, ``explain`` is the long-form
variant: walks the help tree, finds a single command (or sub-app),
and prints everything an agent needs to use it without trial and
error — usage line, every flag with type and default, every
documented example, and a closing reminder of the universal flag set.
"""

from __future__ import annotations

from typing import Any

from quell.interface.errors import NotFoundError
from quell.interface.help_json import _command_info_dict
from quell.interface.main import app
from quell.interface.output import Output

_UNIVERSAL_FLAGS_NOTE = (
    "Universal flags accepted on every command (see `quell --help`):\n"
    "  --json         Emit JSON instead of human output.\n"
    "  --quiet, -q    Errors only (exit code is the signal).\n"
    "  --no-color     Disable ANSI colors.\n"
    "  --path PATH    Project directory (defaults to cwd).\n"
    "  --yes, -y      Skip confirmation prompts (destructive verbs).\n"
    "  --dry-run      Preview without writing (destructive verbs)."
)


def _walk(
    info: dict[str, Any],
    path: list[str],
) -> dict[str, Any] | None:
    """Resolve ``["incident", "list"]`` to that command's info_dict."""
    current = info
    for segment in path:
        commands = current.get("commands") or {}
        if segment not in commands:
            return None
        current = commands[segment]
    return current


def _format_param_row(param: dict[str, Any]) -> str:
    opts = " / ".join(param.get("opts") or []) or param.get("name", "")
    type_name = (param.get("type") or {}).get("name", "")
    default = param.get("default")
    default_str = "" if default in (None, False, []) else f"  (default: {default})"
    help_text = (param.get("help") or "").strip()
    return f"  {opts:<28} {type_name:<10}{default_str}\n      {help_text}"


def _render_command(out: Output, path: list[str], info: dict[str, Any]) -> None:
    full_path = " ".join(["quell", *path])
    out.header(full_path)

    help_text = (info.get("help") or "").strip()
    if help_text:
        # Print the docstring as-is — Examples: blocks already live
        # there from Phase 5.2 and read naturally inline.
        out.line(help_text)
        out.line("")

    sub_commands = info.get("commands") or {}
    if sub_commands:
        out.line("Subcommands:")
        for name, sub_info in sorted(sub_commands.items()):
            summary = (sub_info.get("help") or "").splitlines()[0:1] or [""]
            out.line(f"  {name:<14} {summary[0].strip()}")
        out.line("")
        out.line(f"Run `quell explain {' '.join([*path, '<verb>'])}` for verb detail.")
        return

    params = [p for p in (info.get("params") or []) if not p.get("hidden")]
    if params:
        out.line("Flags:")
        for param in params:
            out.line(_format_param_row(param))
        out.line("")

    out.line(_UNIVERSAL_FLAGS_NOTE)


def explain(out: Output, command_path: list[str]) -> None:
    """Render verbose docs for *command_path* via *out*.

    Raises ``NotFoundError`` when no command matches — the caller
    should let ``safe_run`` translate that to exit 7 with the standard
    fix-message rendering.
    """
    if not command_path:
        # No path supplied: explain the root.
        info = _command_info_dict(app, name="quell")
        _render_command(out, [], info)
        return

    root = _command_info_dict(app, name="quell")
    target = _walk(root, command_path)
    if target is None:
        joined = " ".join(command_path)
        raise NotFoundError(
            f"No command matches {joined!r}.",
            fix="quell --help    # see available commands",
        )
    _render_command(out, command_path, target)


__all__ = ["explain"]
