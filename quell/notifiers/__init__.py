"""Notifier channels for Quell.

A notifier is called after :class:`~quell.agents.IncidentCommander`
finishes investigating an incident.  Three concrete implementations
ship in v0.2: Slack, Discord, and Telegram.

Extending: subclass :class:`~quell.notifiers.base.Notifier`, register a
new config shape under ``quell.config.schema.NotifierConfig``, and add
an ``isinstance`` branch to :func:`create_notifier`.
"""

from __future__ import annotations

from quell.notifiers.base import Notifier, create_notifier

__all__ = ["Notifier", "create_notifier"]
