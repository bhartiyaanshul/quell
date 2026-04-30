"""Pydantic schemas for ``quell incident <verb>`` JSON output.

Per ``docs/cli-design.md`` §13: resource-specific schemas live alongside
their commands rather than in the central ``output_schemas`` module.
Kept in a separate file from ``incident_handlers`` so each module stays
under the project's 300-line cap and tests can import the schemas
without pulling in the database layer.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IncidentRow(BaseModel):
    """Per-incident payload used in both ``list`` and ``show`` output."""

    id: str
    signature: str
    severity: str
    status: str
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    cost_usd: float
    root_cause: str | None = None
    fix_pr_url: str | None = None


class IncidentListData(BaseModel):
    """Data payload for ``incident.list``."""

    incidents: list[IncidentRow]
    total: int
    limit: int


class IncidentStatsData(BaseModel):
    """Data payload for ``incident.stats``."""

    total: int
    by_status: dict[str, int]
    mttr_seconds: float | None
    top_signatures: list[tuple[str, int]]


class ReplayEvent(BaseModel):
    """A single agent event, as serialized into ``incident.replay``."""

    type: str
    timestamp: datetime
    payload: dict[str, object]


class ReplayRun(BaseModel):
    """One agent run inside the replay timeline."""

    id: str
    name: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    events: list[ReplayEvent]


class IncidentReplayData(BaseModel):
    """Data payload for ``incident.replay``."""

    incident: IncidentRow
    runs: list[ReplayRun]


__all__ = [
    "IncidentListData",
    "IncidentReplayData",
    "IncidentRow",
    "IncidentStatsData",
    "ReplayEvent",
    "ReplayRun",
]
