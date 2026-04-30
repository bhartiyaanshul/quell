"""Shared helpers for CLI command modules.

Phase 3.7 of the v0.3.0 redesign — consolidates the per-resource
boilerplate (universal-flag handling, error rendering) into one place
so command files only declare their own positional args and verb-
specific flags.

The universal flag set (``--json`` / ``--quiet`` / ``--no-color``,
plus ``--yes`` / ``--dry-run`` / ``--path`` on destructive verbs) still
lives on each command function — Typer only discovers options via
function signatures, so a decorator-based "middleware" in the Click
sense isn't natural. What this module gives you is the construction
+ error-handling glue every command was repeating.

Per ``docs/cli-design.md`` §13: every command writes through ``Output``,
errors raise ``QuellCLIError`` subclasses, and the top-level handler
formats them with the spec's exit codes. The functions here implement
the second half of that — call ``safe_run`` once per command body.
"""

from __future__ import annotations

from collections.abc import Callable

import typer

from quell.interface.errors import QuellCLIError, handle_cli_error
from quell.interface.output import Output


def build_output(
    *,
    json_mode: bool = False,
    quiet: bool = False,
    no_color: bool = False,
    verbose: bool = False,
) -> Output:
    """Construct an ``Output`` from the universal flag set.

    Centralises the ``no_color or None`` translation (CLI flag is a
    plain bool but ``Output.no_color`` is a tri-state ``bool | None``
    so auto-detect can run when the user didn't pass ``--no-color``).
    """
    return Output(
        quiet=quiet,
        json_mode=json_mode,
        no_color=no_color or None,
        verbose=verbose,
    )


def safe_run(out: Output, run: Callable[[], None]) -> None:
    """Run *run*; render any ``QuellCLIError`` and exit with its code.

    The lambda pattern at call sites (``safe_run(out, lambda: handler(...))``)
    keeps the handler call inline — caller-visible argument names stay
    in the command function so ``--help`` and IDE jumps still work.
    """
    try:
        run()
    except QuellCLIError as exc:
        code = handle_cli_error(exc, out)
        raise typer.Exit(code=code) from None


__all__ = ["build_output", "safe_run"]
