"""``/api/stats`` aggregate counters for the dashboard landing."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from quell.memory.stats import (
    count_incidents,
    mean_time_to_resolve,
    top_signatures,
)

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def stats_endpoint(request: Request) -> dict[str, Any]:
    """Return dashboard-wide counters."""
    factory = request.app.state.session_factory
    async with factory() as session:
        total = await count_incidents(session)
        detected = await count_incidents(session, status="detected")
        investigating = await count_incidents(session, status="investigating")
        resolved = await count_incidents(session, status="resolved")
        mttr_seconds = await mean_time_to_resolve(session)
        top = await top_signatures(session, limit=5)

    return {
        "total": total,
        "by_status": {
            "detected": detected,
            "investigating": investigating,
            "resolved": resolved,
        },
        "mttr_seconds": mttr_seconds,
        "top_signatures": [{"signature": sig, "count": count} for sig, count in top],
    }
