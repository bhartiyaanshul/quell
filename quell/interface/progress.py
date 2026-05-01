"""Progress-bar context manager for known-length operations.

Phase 4.2 of the v0.3.0 redesign. Same animation rules as ``spinner``:
when ``Output.supports_animation`` is ``False`` (``--quiet`` / ``--json``
/ ``--no-color`` / non-TTY / ``QUELL_NO_ANIM``) the bar falls back to
a single trailing summary line so CI logs stay deterministic.

Usage::

    from quell.interface.progress import progress

    with progress(output, "Loading skills", total=len(items)) as p:
        for item in items:
            do_work(item)
            p.advance()
        p.update("Done")

Designed for known-length batches — for unknown-duration work (LLM
calls, network), use :func:`quell.interface.spinner.spinner` instead.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from quell.interface.spinner import register_quell_spinner

# ``progress`` uses ``SpinnerColumn(spinner_name="quell", ...)``, which
# resolves the name via Rich's global ``SPINNERS`` dict at construction
# time. The shape is registered by ``spinner.py`` at import — ensure
# we've also triggered it here so callers that only import ``progress``
# (e.g. ``doctor.run_doctor``) don't crash with KeyError before the
# bar even renders.
register_quell_spinner()

if TYPE_CHECKING:
    from collections.abc import Iterator

    from quell.interface.output import Output


class _StaticProgress:
    """Fallback returned when animation is disabled.

    Mirrors the ``advance`` / ``update`` API of the live tracker so
    callers don't branch on whether animation is on. ``advance`` is a
    no-op silently — under non-TTY, intermediate steps would just
    spam the log. The exit summary (``__exit__``) is what the user
    sees.
    """

    def __init__(self, label: str, total: int) -> None:
        self.label = label
        self.total = total
        self.completed = 0

    def advance(self, n: int = 1) -> None:
        self.completed += n

    def update(self, label: str | None = None) -> None:
        if label is not None:
            self.label = label


class _LiveProgress:
    """Live tracker backed by a Rich ``Progress`` task."""

    def __init__(self, progress: Progress, task_id: TaskID) -> None:
        self._progress = progress
        self._task_id = task_id

    def advance(self, n: int = 1) -> None:
        self._progress.advance(self._task_id, advance=n)

    def update(self, label: str | None = None) -> None:
        if label is not None:
            self._progress.update(self._task_id, description=label)


@contextmanager
def progress(
    output: Output,
    label: str,
    *,
    total: int,
) -> Iterator[_LiveProgress | _StaticProgress]:
    """Context manager that displays a progress bar for *total* items.

    Yields a tracker exposing ``advance(n=1)`` and ``update(label)``.
    Under animation: a Rich progress bar with a dot spinner, the bar,
    a percentage, and an ETA. Under no-animation: a single line at
    block exit summarising completion ("``label  N/total done``").
    """
    if not output.supports_animation:
        tracker = _StaticProgress(label, total)
        try:
            yield tracker
        finally:
            # Single static summary on stderr — preserves stdout for
            # any data the wrapped block emitted (json, etc).
            from rich.console import Console

            console = Console(stderr=True, no_color=True, highlight=False)
            console.print(f"{tracker.label}  {tracker.completed}/{total} done")
        return

    columns = (
        SpinnerColumn(spinner_name="quell", style="#fb923c"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="#fb923c", finished_style="#22c55e"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )
    with Progress(*columns, transient=True) as rich_progress:
        task_id = rich_progress.add_task(label, total=total)
        yield _LiveProgress(rich_progress, task_id)


__all__ = ["progress"]
