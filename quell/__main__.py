"""Entry point for ``python -m quell``.

Forces UTF-8 on stdout/stderr before the CLI dispatches anything, so
Quell's help / log output doesn't crash on Windows consoles that
default to the legacy ``cp1252`` charmap codec.  Rich — which Typer
uses to render help — otherwise throws ``UnicodeEncodeError`` on any
character outside the 8-bit range (em-dashes, bullets, arrows, etc.)
when launched from PowerShell or CMD with an old code page.

No-op on Python 3.7+ POSIX systems, which are already UTF-8 native.
"""

from __future__ import annotations

import contextlib
import sys


def _force_utf8_io() -> None:
    # Best-effort: stream may not be a TextIOWrapper (tests capturing
    # stdout, redirected pipes, etc.).  contextlib.suppress keeps the
    # fallback readable to ruff.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with contextlib.suppress(Exception):
                reconfigure(encoding="utf-8", errors="replace")


_force_utf8_io()

from quell.interface.main import app  # noqa: E402 — must run after reconfigure

app()
