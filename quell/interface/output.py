"""Single output facade for the Quell CLI.

Per ``docs/cli-design.md``: every command writes through this — never
``print()`` / ``typer.echo()`` directly. Centralising output is what
lets ``--json``, ``--quiet``, ``--no-color``, ``NO_COLOR``, and
``QUELL_NO_ANIM`` all behave consistently.

Mode rules: ``info`` / ``success`` / ``warn`` / ``header`` / ``panel``
/ ``table`` / ``key_value`` / ``line`` print to stdout in default mode
and are suppressed under ``--quiet`` or ``--json``. ``error`` always
prints (as plain text or as a JSON envelope under ``--json``); ``json``
only emits under ``--json``; ``debug`` only emits under ``--verbose``.
"""

from __future__ import annotations

import json as _json
import os
import sys

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme

from quell.interface.output_schemas import (
    ENVELOPE_VERSION,
    ErrorEnvelope,
    make_envelope,
)

# Palette — mirrors the landing-page palette so brand stays consistent
# across web and terminal. See docs/cli-design.md §9.1.
_THEME: Theme = Theme(
    {
        "accent": "#fb923c",  # primary orange
        "success": "#22c55e",  # green
        "warning": "#fcd34d",  # amber
        "error": "#ef4444",  # red
        "info": "#94a3b8",  # blue-gray (secondary text)
        "muted": "#64748b",  # dim gray (metadata, separators)
    }
)


class Output:
    """Output facade. Construct once per command invocation.

    Args:
        quiet: ``--quiet`` — suppress all non-error output.
        json_mode: ``--json`` — emit only JSON envelopes; errors as JSON
            on stderr.
        no_color: ``--no-color`` — disable ANSI colors. ``None`` =
            auto-detect (off when ``NO_COLOR`` is set or stdout is not
            a TTY).
        verbose: ``--verbose`` — show debug-level logging on stderr.
    """

    def __init__(
        self,
        *,
        quiet: bool = False,
        json_mode: bool = False,
        no_color: bool | None = None,
        verbose: bool = False,
    ) -> None:
        self.quiet = quiet
        self.json_mode = json_mode
        self.verbose = verbose

        if no_color is None:
            no_color = self._detect_no_color()
        # In JSON mode we never emit colors, even on a TTY — output must
        # be byte-for-byte deterministic for downstream parsers.
        effective_no_color = no_color or json_mode

        self._stdout: Console = Console(
            no_color=effective_no_color,
            theme=_THEME,
            highlight=False,
        )
        self._stderr: Console = Console(
            stderr=True,
            no_color=effective_no_color,
            theme=_THEME,
            highlight=False,
        )
        # Rendering methods (info/success/warn/header/panel/table/...)
        # are suppressed in both quiet and json modes.
        self._silenced: bool = quiet or json_mode

    # ------------------------------------------------------------------
    # Capability properties
    # ------------------------------------------------------------------

    @property
    def is_json(self) -> bool:
        return self.json_mode

    @property
    def is_quiet(self) -> bool:
        return self.quiet

    @property
    def supports_color(self) -> bool:
        return not self._stdout.no_color and self._stdout.is_terminal

    @property
    def supports_animation(self) -> bool:
        """True iff a spinner / progress bar should actually animate."""
        return (
            self._stdout.is_terminal
            and not self.quiet
            and not self.json_mode
            and not self._stdout.no_color
            and os.environ.get("QUELL_NO_ANIM") != "1"
        )

    # ------------------------------------------------------------------
    # Status methods (info / success / warn / error / debug)
    # ------------------------------------------------------------------

    def info(self, message: str) -> None:
        """Secondary informational text — muted styling."""
        if self._silenced:
            return
        self._stdout.print(f"[info]{message}[/info]")

    def success(self, message: str) -> None:
        """Success line with ✓ prefix."""
        if self._silenced:
            return
        self._stdout.print(f"[success]✓[/success] {message}")

    def warn(self, message: str) -> None:
        """Warning line with ! prefix."""
        if self._silenced:
            return
        self._stdout.print(f"[warning]![/warning] {message}")

    def error(
        self,
        message: str,
        *,
        fix: str | None = None,
        exit_code: int = 1,
    ) -> None:
        """Error line — always emitted, even in quiet/JSON modes.

        Args:
            message: Single-sentence description of what went wrong.
            fix: Optional corrective action. May be multi-line; each
                line is rendered as a code suggestion. The first line
                is also used as ``fix_command`` in JSON mode.
            exit_code: Exit code recorded on the JSON envelope. The
                caller is responsible for actually exiting with this
                code; ``error()`` does not call ``sys.exit``.
        """
        if self.json_mode:
            envelope = ErrorEnvelope(
                error=message,
                fix_command=self._first_line(fix),
                exit_code=exit_code,
            )
            self._stderr.print(envelope.model_dump_json())
            return

        self._stderr.print(f"[error]Error:[/error] {message}")
        if fix:
            self._stderr.print()
            self._stderr.print("[muted]Fix:[/muted]")
            for line in fix.strip().splitlines():
                self._stderr.print(f"  [accent]{line}[/accent]")

    def debug(self, message: str) -> None:
        """Debug-level log line — only emitted under ``--verbose``."""
        if not self.verbose:
            return
        self._stderr.print(f"[muted][debug] {message}[/muted]")

    # ------------------------------------------------------------------
    # Rendering methods (header / panel / table / key_value / line)
    # ------------------------------------------------------------------

    def header(self, text: str) -> None:
        """Section header — bold, no color."""
        if self._silenced:
            return
        self._stdout.print(f"\n[bold]{text}[/bold]")

    def panel(
        self,
        content: str,
        *,
        title: str | None = None,
        padding: tuple[int, int] = (1, 2),
    ) -> None:
        """Bordered panel — used for first-run welcome, multi-line callouts."""
        if self._silenced:
            return
        self._stdout.print(
            Panel(content, title=title, padding=padding, border_style="muted")
        )

    def table(
        self,
        rows: list[list[str]],
        *,
        headers: list[str] | None = None,
        footer: str | None = None,
    ) -> None:
        """Borderless aligned table.

        Args:
            rows: List of rows, each row a list of strings.
            headers: Optional column headers (rendered bold).
            footer: Optional muted text below the table (e.g.
                ``"Showing 10 of 47."``).
        """
        if self._silenced:
            return
        table = Table(show_edge=False, header_style="bold", box=None, pad_edge=False)
        column_count = len(headers) if headers else (len(rows[0]) if rows else 0)
        if headers:
            for column in headers:
                table.add_column(column)
        else:
            for _ in range(column_count):
                table.add_column()
        for row in rows:
            table.add_row(*row)
        self._stdout.print(table)
        if footer:
            self._stdout.print(f"[muted]{footer}[/muted]")

    def key_value(self, pairs: list[tuple[str, str]]) -> None:
        """Key/value pairs as right-aligned ``  key:  value`` lines."""
        if self._silenced or not pairs:
            return
        max_key = max(len(k) for k, _ in pairs)
        for key, value in pairs:
            padded = key.rjust(max_key)
            self._stdout.print(f"  [muted]{padded}:[/muted]  {value}")

    def line(self, text: str = "") -> None:
        """Raw line — markup not interpreted. Drop-in for ``typer.echo``.

        Subject to quiet/json suppression. For themed text, use
        ``info`` / ``success`` / ``warn`` / ``header`` instead.
        """
        if self._silenced:
            return
        self._stdout.print(text, markup=False, highlight=False)

    # ------------------------------------------------------------------
    # JSON method (only emits in --json mode)
    # ------------------------------------------------------------------

    def json(
        self,
        kind: str,
        data: object,
        *,
        version: str = ENVELOPE_VERSION,
    ) -> None:
        """Emit a JSON envelope to stdout. No-op when not in JSON mode.

        Pydantic models are auto-serialized via ``model_dump()``.
        Other types fall back to ``str()`` for the JSON encoder so
        ``Path``, ``datetime``, etc. don't crash the call.
        """
        if not self.json_mode:
            return
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        envelope = make_envelope(kind, data, version=version)
        # Bypass Rich for raw, deterministic JSON output.
        sys.stdout.write(_json.dumps(envelope, default=str) + "\n")
        sys.stdout.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_no_color() -> bool:
        return os.environ.get("NO_COLOR") is not None

    @staticmethod
    def _first_line(text: str | None) -> str | None:
        if text is None:
            return None
        stripped = text.strip()
        return stripped.splitlines()[0] if stripped else None


__all__ = ["Output"]
