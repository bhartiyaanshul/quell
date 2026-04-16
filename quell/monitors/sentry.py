"""Sentry monitor — polls the Sentry Issues REST API and emits an event for
each new unresolved issue discovered since the last poll.

Requires a Sentry auth token stored in the OS keychain under
``quell/sentry`` / ``auth_token``.  Run ``quell init`` to configure it.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx

from quell.config.schema import SentryMonitorConfig
from quell.monitors.base import Monitor, RawEvent
from quell.utils.errors import MonitorError
from quell.utils.keyring_utils import get_secret

_API_BASE = "https://sentry.io/api/0"


class SentryMonitor(Monitor):
    """Poll Sentry's Issues API and yield events for newly observed issues."""

    def __init__(self, config: SentryMonitorConfig) -> None:
        self._config = config

    def events(self) -> AsyncGenerator[RawEvent, None]:
        """Return an async generator that polls Sentry for new issues."""
        return self._stream()

    async def _stream(self) -> AsyncGenerator[RawEvent, None]:
        token = get_secret("quell/sentry", "auth_token")
        if not token:
            raise MonitorError(
                "Sentry auth token not found in keychain — run `quell init`"
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
        org = self._config.organization_slug
        proj = self._config.project_slug

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{_API_BASE}/projects/{org}/{proj}/issues/",
                    params={"query": "is:unresolved", "limit": 25},
                    headers=headers,
                )

            if resp.status_code != 200:
                yield RawEvent(
                    source="sentry",
                    timestamp=ts,
                    raw=f"Sentry API error: HTTP {resp.status_code}",
                    metadata={"status_code": resp.status_code},
                    severity="error",
                )
                return

            issues: list[dict[str, Any]] = resp.json()
            for issue in issues:
                issue_id: str = str(issue.get("id", ""))
                if issue_id and issue_id not in seen_ids:
                    seen_ids.add(issue_id)
                    level: str = str(issue.get("level", "error")).lower()
                    yield RawEvent(
                        source="sentry",
                        timestamp=ts,
                        raw=str(issue.get("title", "Unknown Sentry issue")),
                        metadata={
                            "issue": issue,
                            "project_slug": proj,
                            "organization_slug": org,
                        },
                        severity=level,
                    )

        except httpx.RequestError as exc:
            yield RawEvent(
                source="sentry",
                timestamp=ts,
                raw=f"Sentry API request error: {exc}",
                metadata={"error": str(exc)},
                severity="warning",
            )


__all__ = ["SentryMonitor"]
