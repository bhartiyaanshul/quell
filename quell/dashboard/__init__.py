"""Quell dashboard — a read-only FastAPI backend + static Next.js SPA.

The dashboard is launched with ``quell dashboard`` and served locally
on ``localhost:7777``.  It exposes:

* ``GET /api/incidents``                 — list, filterable by status.
* ``GET /api/incidents/{id}``            — full detail + runs + findings.
* ``GET /api/incidents/{id}/replay``     — replay timeline (Phase 22).
* ``GET /api/runs/{run_id}/events``      — raw event stream.
* ``GET /api/stats``                     — aggregate counts + MTTR.

Everything else is static assets served from
``quell/dashboard/static/`` — the prebuilt Next.js export (see
``dashboard/`` in the repo).  That directory is built in CI on every
release tag and included as package data in the wheel.
"""

from __future__ import annotations

from quell.dashboard.launcher import launch_dashboard
from quell.dashboard.server import create_dashboard_app

__all__ = ["create_dashboard_app", "launch_dashboard"]
