"""Bootstrap helper — (re-)register every Phase 12 built-in tool.

Importing ``quell.tools.code``, ``quell.tools.git``, etc. registers the
bundled tools as a side effect of evaluating their ``@register_tool``
decorators.  The side-effect-only pattern is fragile across test files
that call :func:`~quell.tools.registry.clear_registry` — once the module
has been imported the decorator body does not re-run on a second import.

:func:`register_builtin_tools` papers over that by unregistering any
known built-in names, then reloading each module so the decorator fires
again.  It is safe to call multiple times.
"""

from __future__ import annotations

import importlib
import sys

from quell.tools.registry import unregister_tool

_BUILTIN_TOOL_NAMES: tuple[str, ...] = (
    "code_read",
    "code_grep",
    "git_log",
    "git_blame",
    "git_diff",
    "logs_query",
    "http_probe",
    "create_incident_report",
    "create_postmortem",
    "agent_finish",
    "finish_incident",
    # Phase 13 — inter-agent coordination.
    "create_agent",
    "send_message",
    "wait_for_message",
    "view_graph",
)

_BUILTIN_MODULES: tuple[str, ...] = (
    "quell.tools.code.read",
    "quell.tools.code.grep",
    "quell.tools.git.log",
    "quell.tools.git.blame",
    "quell.tools.git.diff",
    "quell.tools.monitoring.logs_query",
    "quell.tools.monitoring.http_probe",
    "quell.tools.reporting.incident_report",
    "quell.tools.reporting.postmortem",
    "quell.tools.agents_graph.agent_finish",
    "quell.tools.agents_graph.finish_incident",
    # Phase 13 — inter-agent coordination lives under quell.agents to
    # avoid an import cycle between tools and agents.
    "quell.agents.graph_tools",
)


def register_builtin_tools() -> None:
    """Register every bundled Phase 12 tool.  Idempotent."""
    for name in _BUILTIN_TOOL_NAMES:
        unregister_tool(name)
    for modname in _BUILTIN_MODULES:
        if modname in sys.modules:
            importlib.reload(sys.modules[modname])
        else:
            importlib.import_module(modname)


__all__ = ["register_builtin_tools"]
