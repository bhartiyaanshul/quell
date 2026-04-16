"""Base types and abstract interface for Quell event source adapters.

Every monitor is a class that implements :class:`Monitor`.  The
:func:`create_monitor` factory function instantiates the right concrete
subclass from a validated :data:`~quell.config.schema.MonitorConfig`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from quell.config.schema import (
    HttpPollMonitorConfig,
    LocalFileMonitorConfig,
    MonitorConfig,
    SentryMonitorConfig,
    VercelMonitorConfig,
)
from quell.utils.errors import MonitorError

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class RawEvent:
    """A single raw event emitted by a monitor adapter."""

    source: str
    """Identifier for the monitor type (e.g. ``"local-file"``)."""

    timestamp: datetime
    """When this event was observed (UTC)."""

    raw: str
    """The raw text content of the event."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Source-specific structured data (parsed JSON fields, URL, etc.)."""

    severity: str = "info"
    """One of ``"info"``, ``"warning"``, ``"error"``, ``"critical"``."""


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class Monitor(ABC):
    """Abstract base class for Quell event source adapters.

    Subclasses must implement :meth:`events`, which returns an async
    generator that yields :class:`RawEvent` objects indefinitely.
    """

    @abstractmethod
    def events(self) -> AsyncGenerator[RawEvent, None]:
        """Return an async generator that yields :class:`RawEvent` objects."""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_monitor(config: MonitorConfig) -> Monitor:
    """Instantiate the correct :class:`Monitor` subclass for *config*.

    Uses isinstance narrowing on the Pydantic discriminated union so that
    mypy can verify each branch receives the right concrete config type.

    Args:
        config: A validated monitor config (discriminated on ``type`` field).

    Returns:
        A concrete :class:`Monitor` ready to call :meth:`~Monitor.events` on.

    Raises:
        MonitorError: If the config type has no registered implementation.
    """
    if isinstance(config, LocalFileMonitorConfig):
        from quell.monitors.local_file import LocalFileMonitor  # noqa: PLC0415

        return LocalFileMonitor(config)
    if isinstance(config, HttpPollMonitorConfig):
        from quell.monitors.http_poll import HttpPollMonitor  # noqa: PLC0415

        return HttpPollMonitor(config)
    if isinstance(config, VercelMonitorConfig):
        from quell.monitors.vercel import VercelMonitor  # noqa: PLC0415

        return VercelMonitor(config)
    if isinstance(config, SentryMonitorConfig):
        from quell.monitors.sentry import SentryMonitor  # noqa: PLC0415

        return SentryMonitor(config)
    raise MonitorError(  # pragma: no cover
        f"Unknown monitor config type: {type(config).__name__!r}"
    )


__all__ = ["RawEvent", "Monitor", "create_monitor"]
