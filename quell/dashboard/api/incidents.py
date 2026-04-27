"""``/api/incidents`` endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from quell.memory.agent_runs import list_runs_for_incident
from quell.memory.findings import list_findings_for_incident
from quell.memory.incidents import get_incident, list_incidents
from quell.memory.models import AgentRun, Finding, Incident

router = APIRouter(tags=["incidents"])


def _incident_row(incident: Incident) -> dict[str, Any]:
    return {
        "id": incident.id,
        "signature": incident.signature,
        "severity": incident.severity,
        "status": incident.status,
        "first_seen": incident.first_seen.isoformat(),
        "last_seen": incident.last_seen.isoformat(),
        "occurrence_count": incident.occurrence_count,
        "root_cause": incident.root_cause,
        "fix_pr_url": incident.fix_pr_url,
        "cost_usd": float(getattr(incident, "cost_usd", 0.0) or 0.0),
    }


def _run_row(run: AgentRun) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if run.final_result and isinstance(run.final_result, dict):
        raw_metrics = run.final_result.get("_metrics", {})
        if isinstance(raw_metrics, dict):
            metrics = raw_metrics
    return {
        "id": run.id,
        "name": run.name,
        "parent_agent_id": run.parent_agent_id,
        "skills": run.skills or [],
        "status": run.status,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "final_result": run.final_result or {},
        "input_tokens": metrics.get("input_tokens"),
        "output_tokens": metrics.get("output_tokens"),
        "cost_usd": metrics.get("cost_usd"),
        "iterations": metrics.get("iterations"),
    }


def _finding_row(finding: Finding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "category": finding.category,
        "description": finding.description,
        "file_path": finding.file_path,
        "line_number": finding.line_number,
        "confidence": finding.confidence,
        "created_at": finding.created_at.isoformat(),
        "agent_run_id": finding.agent_run_id,
    }


@router.get("/incidents")
async def list_incidents_endpoint(
    request: Request,
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, Any]:
    """Return recent incidents, newest first."""
    factory = request.app.state.session_factory
    async with factory() as session:
        rows = await list_incidents(session, status=status, limit=limit)
        incidents = [_incident_row(r) for r in rows]
    return {"incidents": incidents, "count": len(incidents)}


@router.get("/incidents/{incident_id}")
async def get_incident_endpoint(request: Request, incident_id: str) -> dict[str, Any]:
    """Return one incident plus its runs + findings (joined)."""
    factory = request.app.state.session_factory
    async with factory() as session:
        incident = await get_incident(session, incident_id)
        if incident is None:
            raise HTTPException(
                status_code=404, detail=f"Incident {incident_id} not found"
            )
        runs = await list_runs_for_incident(session, incident_id)
        findings = await list_findings_for_incident(session, incident_id)
    return {
        "incident": _incident_row(incident),
        "runs": [_run_row(r) for r in runs],
        "findings": [_finding_row(f) for f in findings],
    }
