"""Vercel monitor — polls the Vercel Deployments REST API and emits an event
whenever a deployment enters the ``ERROR`` state.

Requires a Vercel personal access token stored in the OS keychain under
``quell/vercel`` / ``api_token``.  Run ``quell init`` to configure it.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx

from quell.config.schema import VercelMonitorConfig
from quell.monitors.base import Monitor, RawEvent
from quell.utils.errors import MonitorError
from quell.utils.keyring_utils import get_secret

_API_BASE = "https://api.vercel.com"


class VercelMonitor(Monitor):
    """Poll Vercel's deployments API and yield events for ERROR-state deployments."""

    def __init__(self, config: VercelMonitorConfig) -> None:
        self._config = config

    def events(self) -> AsyncGenerator[RawEvent, None]:
        """Return an async generator that polls Vercel for failed deployments."""
        return self._stream()

    async def _stream(self) -> AsyncGenerator[RawEvent, None]:
        token = get_secret("quell/vercel", "api_token")
        if not token:
            raise MonitorError(
                "Vercel API token not found in keychain — run `quell init`"
            )

        headers = {"Authorization": f"Bearer {token}"}
        seen_ids: set[str] = set()

        while True:
            async for event in self._fetch_events(headers, seen_ids):
                yield event
            await asyncio.sleep(self._config.interval_seconds)

    async def _fetch_events(
        self,
        headers: dict[str, str],
        seen_ids: set[str],
    ) -> AsyncGenerator[RawEvent, None]:
        ts = datetime.now(UTC)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/v6/deployments",
                    params={
                        "projectId": self._config.project_id,
                        "limit": 10,
                    },
                    headers=headers,
                )

            if resp.status_code != 200:
                yield RawEvent(
                    source="vercel",
                    timestamp=ts,
                    raw=f"Vercel API error: HTTP {resp.status_code}",
                    metadata={"status_code": resp.status_code},
                    severity="error",
                )
                return

            data: dict[str, Any] = resp.json()
            for dep in data.get("deployments", []):
                dep_id: str = dep.get("uid", "")
                state: str = dep.get("state", "")
                if dep_id and dep_id not in seen_ids:
                    seen_ids.add(dep_id)
                    if state == "ERROR":
                        yield RawEvent(
                            source="vercel",
                            timestamp=ts,
                            raw=(f"Vercel deployment {dep_id} entered ERROR state"),
                            metadata={
                                "deployment": dep,
                                "project_id": self._config.project_id,
                            },
                            severity="error",
                        )

        except httpx.RequestError as exc:
            yield RawEvent(
                source="vercel",
                timestamp=ts,
                raw=f"Vercel API request error: {exc}",
                metadata={"error": str(exc)},
                severity="warning",
            )


__all__ = ["VercelMonitor"]
