"""``/api/runs/{run_id}/events`` endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from quell.memory.events import list_events_for_run

router = APIRouter(tags=["events"])


@router.get("/runs/{run_id}/events")
async def list_events_endpoint(
    request: Request,
    run_id: str,
    event_type: str | None = Query(default=None),
) -> dict[str, Any]:
    """Return every event for *run_id* ordered by timestamp."""
    factory = request.app.state.session_factory
    async with factory() as session:
        rows = await list_events_for_run(session, run_id, event_type=event_type)
        events = [
            {
                "id": r.id,
                "agent_run_id": r.agent_run_id,
                "event_type": r.event_type,
                "timestamp": r.timestamp.isoformat(),
                "payload": r.payload,
            }
            for r in rows
        ]
    return {"events": events, "count": len(events)}
