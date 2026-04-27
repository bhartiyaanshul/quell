"""Visual replay of a past incident investigation.

Phase 22 ships a terminal renderer only — no re-invocation of the
LLM.  The dashboard provides the same data through
``/api/incidents/{id}/replay`` plus the ``ReplayTimeline`` React
component.
"""

from __future__ import annotations

from quell.replay.renderer import render_terminal_timeline

__all__ = ["render_terminal_timeline"]
