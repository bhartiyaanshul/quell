"""Detector — turn :class:`RawEvent` stream into :class:`Incident` records.

The detector is intentionally simple and LLM-free:

* It fingerprints each event with :func:`compute_signature`.
* It tracks a :class:`RollingBaseline` per signature.
* It emits an :class:`Incident` when any of three conditions is true:

  1. The signature is *new* (first occurrence).
  2. The current rate is more than ``spike_multiplier`` × the historical
     mean (a burst).
  3. The event severity is ``error`` or ``critical``.

When an incident already exists for a signature, the detector updates
``occurrence_count`` and ``last_seen`` via
:func:`~quell.memory.incidents.bump_occurrence` instead of inserting a
duplicate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa

from quell.detector.baseline import RollingBaseline
from quell.detector.signature import compute_signature
from quell.memory.incidents import bump_occurrence, create_incident
from quell.memory.models import Incident
from quell.monitors.base import RawEvent

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_SEVERITY_TO_INCIDENT: dict[str, str] = {
    "info": "low",
    "warning": "medium",
    "error": "high",
    "critical": "critical",
}


class Detector:
    """Event-stream anomaly detector (signature + rolling baseline).

    The detector is stateful: it keeps baselines in-memory keyed by
    signature.  In Phase 14 the watch loop constructs one ``Detector``
    per process; restarts lose baselines (acceptable — the rule is
    "anything *new* since startup" which is a reasonable restart
    semantic for an always-on process).
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        *,
        spike_multiplier: float = 3.0,
    ) -> None:
        """Construct a fresh detector.

        Args:
            session_factory:  SQLAlchemy async session factory used to
                              persist incidents.  When ``None`` the
                              detector runs in-memory only
                              (useful for tests).
            spike_multiplier: How many times higher than the mean rate
                              counts as a spike.  Default 3×.
        """
        self._session_factory = session_factory
        self._spike_multiplier = spike_multiplier
        self._baselines: dict[str, RollingBaseline] = {}
        self._known_incidents: dict[str, str] = {}  # signature -> incident_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process(self, event: RawEvent) -> Incident | None:
        """Process *event* and return an :class:`Incident` if one fires.

        When the signature is already active, persists a bumped
        occurrence and returns ``None`` (the caller should not spawn a
        second investigation for the same live incident).
        """
        signature = compute_signature(event)
        baseline = self._baselines.setdefault(signature, RollingBaseline())

        ts = event.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        baseline.record(ts)

        is_new = baseline.occurrence_count == 1
        is_spike = (
            baseline.mean_rate > 0
            and baseline.current_rate > baseline.mean_rate * self._spike_multiplier
        )
        high_severity = event.severity in {"error", "critical"}

        if not (is_new or is_spike or high_severity):
            return None

        # Update an already-known incident in place rather than duplicating.
        if signature in self._known_incidents:
            if self._session_factory is not None:
                async with self._session_factory() as session:
                    await bump_occurrence(session, self._known_incidents[signature])
                    await session.commit()
            return None

        if self._session_factory is None:
            # In-memory mode (tests) — fabricate an Incident without persisting
            # and remember the signature so repeats of the same bug return None.
            severity = _SEVERITY_TO_INCIDENT.get(event.severity, "medium")
            now = datetime.now(UTC)
            incident_id = f"inc_inmem_{signature[:8]}"
            self._known_incidents[signature] = incident_id
            return Incident(
                id=incident_id,
                signature=signature,
                severity=severity,
                status="detected",
                first_seen=ts,
                last_seen=now,
                occurrence_count=1,
            )

        async with self._session_factory() as session:
            existing = await session.execute(
                sa.select(Incident).where(Incident.signature == signature)
            )
            incident = existing.scalar_one_or_none()
            if incident is None:
                incident = await create_incident(
                    session,
                    signature=signature,
                    severity=_SEVERITY_TO_INCIDENT.get(event.severity, "medium"),
                    first_seen=ts,
                )
            await session.commit()
            self._known_incidents[signature] = incident.id
            return incident


__all__ = ["Detector"]
