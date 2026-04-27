"""``/api/incidents/{id}/replay`` — replay timeline (Phase 22)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from quell.memory.agent_runs import list_runs_for_incident
from quell.memory.events import list_events_for_run
from quell.memory.incidents import get_incident

router = APIRouter(tags=["replay"])


@router.get("/incidents/{incident_id}/replay")
async def replay_endpoint(request: Request, incident_id: str) -> dict[str, Any]:
    """Return the full event timeline grouped by run.

    The response is shaped for direct rendering by the dashboard's
    ``ReplayTimeline`` component.
    """
    factory = request.app.state.session_factory
    async with factory() as session:
        incident = await get_incident(session, incident_id)
        if incident is None:
            raise HTTPException(
                status_code=404, detail=f"Incident {incident_id} not found"
            )
        runs = await list_runs_for_incident(session, incident_id)
        runs_payload: list[dict[str, Any]] = []
        total_cost = 0.0
        total_events = 0
        for run in runs:
            events = await list_events_for_run(session, run.id)
            metrics: dict[str, Any] = {}
            if run.final_result and isinstance(run.final_result, dict):
                raw = run.final_result.get("_metrics", {})
                if isinstance(raw, dict):
                    metrics = raw
            cost = float(metrics.get("cost_usd") or 0.0)
            total_cost += cost
            total_events += len(events)
            runs_payload.append(
                {
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "started_at": run.started_at.isoformat(),
                    "finished_at": (
                        run.finished_at.isoformat() if run.finished_at else None
                    ),
                    "cost_usd": cost,
                    "iterations": metrics.get("iterations"),
                    "events": [
                        {
                            "id": e.id,
                            "event_type": e.event_type,
                            "timestamp": e.timestamp.isoformat(),
                            "payload": e.payload,
                        }
                        for e in events
                    ],
                }
            )

    return {
        "incident_id": incident_id,
        "runs": runs_payload,
        "totals": {
            "runs": len(runs_payload),
            "events": total_events,
            "cost_usd": total_cost,
        },
    }
