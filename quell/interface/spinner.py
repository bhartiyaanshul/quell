"""Spinner / status context manager for long-running operations.

Per ``docs/cli-design.md`` §10.1: animations only run when stdout is a
TTY, ``--quiet``/``--json``/``--no-color`` are unset, ``QUELL_NO_ANIM``
is unset, and the operation is expected to take > 200ms. This module
checks those gates via ``Output.supports_animation`` and falls back to
a single static line when animation isn't supported — so CI logs and
non-TTY consumers get deterministic output.

Usage::

    with spinner(output, "Calling LLM…") as status:
        response = llm.call(...)
        status.update("Parsing response…")
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Iterator

    from quell.interface.output import Output


class _StaticStatus:
    """Fallback returned when animation is disabled.

    Mirrors the parts of ``rich.status.Status`` we use (``update``) so
    callers don't need to branch on whether they got a real spinner.
    Each ``update()`` emits a fresh static line so progress is still
    visible in non-TTY logs.
    """

    def __init__(self, console: Console, message: str) -> None:
        self._console = console
        self._console.print(message)

    def update(self, message: str) -> None:
        self._console.print(message)


@contextmanager
def spinner(output: Output, message: str) -> Iterator[object]:
    """Context manager that shows a spinner while a block runs.

    Yields an object with an ``update(message)`` method. Use it to
    reflect the operation's current phase ("calling LLM" → "parsing
    response" etc.) — the spinner stays the same; only the label changes.

    When animation is disabled, falls back to printing each message
    on its own line so the same call sites work in CI without a TTY.
    """
    if not output.supports_animation:
        # Animation disabled — emit a single static line and yield a
        # stub that prints subsequent updates as new lines.
        console = Console(stderr=True, no_color=True, highlight=False)
        yield _StaticStatus(console, message)
        return

    # Real spinner. We render it on stderr so stdout stays clean for
    # any data the wrapped block produces (json output, streamed events).
    console = Console(stderr=True)
    with console.status(message, spinner="dots") as status:
        yield status


__all__ = ["spinner"]
