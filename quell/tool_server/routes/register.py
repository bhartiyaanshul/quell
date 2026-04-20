"""Tool server — ``POST /register_agent``.

Subagents created via the Phase 13 ``create_agent`` tool announce
themselves here before they start calling tools, so the tool server can
record which agents are allowed to execute tools.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory set of registered agent ids. The process inside the sandbox
# is single-tenant (one root agent + its subagents), so this simple set
# is sufficient.
_REGISTERED: set[str] = set()


class RegisterRequest(BaseModel):
    agent_id: str


@router.post("/register_agent")
async def register_agent(req: RegisterRequest) -> dict[str, str]:
    """Register *agent_id* as a known caller."""
    _REGISTERED.add(req.agent_id)
    return {"status": "registered", "agent_id": req.agent_id}


def is_registered(agent_id: str) -> bool:
    """Test helper: was *agent_id* previously registered?"""
    return agent_id in _REGISTERED


def clear_registered() -> None:
    """Test helper: wipe the registered-agent set."""
    _REGISTERED.clear()


__all__ = ["router", "is_registered", "clear_registered"]
