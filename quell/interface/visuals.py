"""Visual rendering primitives for the Quell CLI.

Free functions rather than ``Output`` methods so we can stay under the
300-line file cap on ``output.py`` and keep the import surface
explicit at call sites: ``from quell.interface.visuals import diff``.

Every renderer respects the same suppression rules as ``Output``
(quiet / json silence everything; non-TTY / no-color drops styling).
``badge()`` returns a markup string instead of printing — it composes
into table cells and inline text.

See ``docs/cli-design.md`` §9 for the palette and §11 for the
first-run experience these primitives are designed for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.box import ROUNDED
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

if TYPE_CHECKING:
    from quell.interface.output import Output


# Maps semantic status names to theme tokens defined in output._THEME.
# Keep in sync with the palette in docs/cli-design.md §9.1.
_STATUS_STYLES: dict[str, str] = {
    "success": "success",
    "resolved": "success",
    "ok": "success",
    "warning": "warning",
    "warn": "warning",
    "detected": "warning",
    "error": "error",
    "failed": "error",
    "info": "info",
    "investigating": "info",
    "muted": "muted",
}


def badge(label: str, *, status: str = "info") -> str:
    """Return a Rich-markup string for a small colored badge.

    Renders as a colored block character (``▎``) followed by the
    label. Returns a string so the badge can be embedded inline
    (e.g. inside a table cell or sentence)::

        out.line(f"Status: {badge('resolved', status='success')}")

    Unknown status falls back to the ``info`` color so a typo never
    crashes a command — just mis-colors a single badge.
    """
    style = _STATUS_STYLES.get(status, "info")
    return f"[{style}]▎[/{style}]{label}"


def diff(out: Output, filename: str, hunks: list[tuple[str, str]]) -> None:
    """Render a +/- diff block.

    Args:
        out: The Output instance to render through.
        filename: Path / file label rendered as a muted header.
        hunks: List of ``(kind, line)`` tuples. ``kind`` is ``"add"``
            (green ``+``), ``"rm"`` (red ``-``), or anything else
            (rendered as plain context).
    """
    if out.is_quiet or out.is_json:
        return
    out._stdout.print(f"  [muted]── {filename} ──[/muted]")  # noqa: SLF001
    for kind, line in hunks:
        if kind == "add":
            out._stdout.print(f"  [success]+ {line}[/success]")  # noqa: SLF001
        elif kind == "rm":
            out._stdout.print(f"  [error]- {line}[/error]")  # noqa: SLF001
        else:
            out._stdout.print(f"    {line}")  # noqa: SLF001


def markdown(out: Output, text: str) -> None:
    """Render *text* as Markdown (headers, code, lists, links)."""
    if out.is_quiet or out.is_json:
        return
    out._stdout.print(Markdown(text))  # noqa: SLF001 — facade owns the console


def divider(out: Output, label: str | None = None) -> None:
    """Render a horizontal divider with an optional label.

    Without a label: a full-width muted rule.
    With a label: ``─── label ───`` muted, left-aligned.
    """
    if out.is_quiet or out.is_json:
        return
    if label:
        out._stdout.print(f"[muted]─── {label} ───[/muted]")  # noqa: SLF001
    else:
        out._stdout.print(Rule(style="muted"))  # noqa: SLF001


def step_indicator(out: Output, current: int, total: int, message: str) -> None:
    """Render a numbered progress indicator: ``▸ 1/5  message``.

    ``▸`` is the same cursor symbol used in prompts, in accent color —
    visually links the step header to the prompt that follows.
    """
    if out.is_quiet or out.is_json:
        return
    out._stdout.print(  # noqa: SLF001
        f"[accent]▸[/accent] [accent]{current}[/accent]"
        f"[muted]/{total}[/muted]  {message}"
    )


def next_step(out: Output, action: str, *, command: str | None = None) -> None:
    """Render a next-step hint with the action arrow.

    Without a command: ``→ action``.
    With a command:    ``→ action  $ command``.
    """
    if out.is_quiet or out.is_json:
        return
    if command:
        out._stdout.print(  # noqa: SLF001
            f"[accent]→[/accent] {action}  [muted]$[/muted] [accent]{command}[/accent]",
            soft_wrap=True,
        )
    else:
        out._stdout.print(f"[accent]→[/accent] {action}")  # noqa: SLF001


def empty_state(out: Output, message: str, *, hint: str | None = None) -> None:
    """Render an empty-state message with an optional next-step hint.

    Used in place of ``[]`` when a list view returns no rows: gives
    the user actionable text instead of a blank screen.
    """
    if out.is_quiet or out.is_json:
        return
    out._stdout.print(f"[muted]{message}[/muted]")  # noqa: SLF001
    if hint:
        next_step(out, hint)


def welcome_panel(out: Output, title: str, body: str) -> None:
    """Render the first-run welcome panel.

    Rounded borders + accent-colored title. Skipped under quiet/json
    per the global rules — those modes don't get welcome banners.
    """
    if out.is_quiet or out.is_json:
        return
    out._stdout.print(  # noqa: SLF001
        Panel(
            body,
            title=f"[accent]{title}[/accent]",
            border_style="muted",
            box=ROUNDED,
            padding=(1, 2),
        )
    )


__all__ = [
    "badge",
    "diff",
    "divider",
    "empty_state",
    "markdown",
    "next_step",
    "step_indicator",
    "welcome_panel",
]
