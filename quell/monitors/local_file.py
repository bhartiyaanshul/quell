"""Local log-file monitor — tails a file and emits a RawEvent per new line.

Supports two line formats:
* ``"json"``  — each line is parsed as JSON; the ``level``/``severity`` field
  sets :attr:`~quell.monitors.base.RawEvent.severity` (falls back to ``"info"``
  on parse errors).
* ``"regex"`` — each line is matched against ``pattern``; non-matching lines are
  silently dropped.  The named capture groups are available in ``metadata``.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from quell.config.schema import LocalFileMonitorConfig
from quell.monitors.base import Monitor, RawEvent
from quell.utils.errors import MonitorError

_POLL_INTERVAL = 0.1  # seconds between readline attempts


class LocalFileMonitor(Monitor):
    """Tail a local log file and yield one :class:`~quell.monitors.base.RawEvent`
    per new line."""

    def __init__(self, config: LocalFileMonitorConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def events(self) -> AsyncGenerator[RawEvent, None]:
        """Return an async generator that tails the configured log file."""
        return self._stream()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _stream(self) -> AsyncGenerator[RawEvent, None]:
        path = Path(self._config.path)
        if not path.exists():
            raise MonitorError(f"Log file not found: {path}")

        loop = asyncio.get_running_loop()

        def _open() -> TextIOWrapper:
            return open(path, encoding="utf-8", errors="replace")  # noqa: SIM115

        fh = await loop.run_in_executor(None, _open)
        try:
            # Seek to end so we only tail *new* content.
            await loop.run_in_executor(None, lambda: fh.seek(0, 2))
            while True:
                line: str = await loop.run_in_executor(None, fh.readline)
                if line:
                    event = self._parse_line(line.rstrip("\n"))
                    if event is not None:
                        yield event
                else:
                    await asyncio.sleep(_POLL_INTERVAL)
        finally:
            await loop.run_in_executor(None, fh.close)

    def _parse_line(self, line: str) -> RawEvent | None:
        """Parse *line* according to ``config.format``.

        Returns ``None`` when the line should be silently skipped (regex
        format, no match).
        """
        ts = datetime.now(UTC)

        if self._config.format == "regex":
            if not self._config.pattern:
                return RawEvent(
                    source="local-file",
                    timestamp=ts,
                    raw=line,
                    metadata={"path": self._config.path},
                )
            m = re.search(self._config.pattern, line)
            if not m:
                return None
            return RawEvent(
                source="local-file",
                timestamp=ts,
                raw=line,
                metadata={"path": self._config.path, "groups": m.groupdict()},
                severity="error",
            )

        # Default: "json" format — attempt to parse, fall back gracefully.
        try:
            data: dict[str, Any] = json.loads(line)
            raw_level: str = str(
                data.get("level", data.get("severity", "info"))
            ).lower()
            severity = (
                raw_level
                if raw_level in {"info", "warning", "error", "critical"}
                else "info"
            )
            return RawEvent(
                source="local-file",
                timestamp=ts,
                raw=line,
                metadata={"path": self._config.path, "parsed": data},
                severity=severity,
            )
        except (json.JSONDecodeError, ValueError):
            return RawEvent(
                source="local-file",
                timestamp=ts,
                raw=line,
                metadata={"path": self._config.path},
                severity="info",
            )


__all__ = ["LocalFileMonitor"]
