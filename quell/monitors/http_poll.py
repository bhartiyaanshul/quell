"""HTTP-poll monitor — fires an event when a health-check URL returns
anything other than the expected HTTP status code, or when the request
times out / fails entirely.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import httpx

from quell.config.schema import HttpPollMonitorConfig
from quell.monitors.base import Monitor, RawEvent


class HttpPollMonitor(Monitor):
    """Poll an HTTP endpoint and yield a :class:`~quell.monitors.base.RawEvent`
    on any non-expected response or network failure."""

    def __init__(self, config: HttpPollMonitorConfig) -> None:
        self._config = config

    def events(self) -> AsyncGenerator[RawEvent, None]:
        """Return an async generator that polls the configured URL."""
        return self._stream()

    async def _stream(self) -> AsyncGenerator[RawEvent, None]:
        while True:
            event = await self._poll_once()
            if event is not None:
                yield event
            await asyncio.sleep(self._config.interval_seconds)

    async def _poll_once(self) -> RawEvent | None:
        ts = datetime.now(UTC)
        url = self._config.url

        try:
            async with httpx.AsyncClient(
                timeout=float(self._config.timeout_seconds)
            ) as client:
                resp = await client.get(url)

            if resp.status_code != self._config.expected_status:
                return RawEvent(
                    source="http-poll",
                    timestamp=ts,
                    raw=(
                        f"HTTP {resp.status_code} from {url} "
                        f"(expected {self._config.expected_status})"
                    ),
                    metadata={
                        "url": url,
                        "status_code": resp.status_code,
                        "expected": self._config.expected_status,
                        "body_snippet": resp.text[:500],
                    },
                    severity="error",
                )
            return None

        except httpx.TimeoutException:
            return RawEvent(
                source="http-poll",
                timestamp=ts,
                raw=f"Timeout polling {url} after {self._config.timeout_seconds}s",
                metadata={"url": url, "timeout_seconds": self._config.timeout_seconds},
                severity="error",
            )
        except httpx.RequestError as exc:
            return RawEvent(
                source="http-poll",
                timestamp=ts,
                raw=f"Request error polling {url}: {exc}",
                metadata={"url": url, "error": str(exc)},
                severity="error",
            )


__all__ = ["HttpPollMonitor"]
