"""Tool server — ``GET /health``."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Return 200 with a tiny payload so the runtime can gate on readiness."""
    return {"status": "ok"}


__all__ = ["router"]
