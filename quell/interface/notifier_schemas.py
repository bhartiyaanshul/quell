"""Pydantic schemas for ``quell notifier <verb>`` JSON output.

Per ``docs/cli-design.md`` §13: resource-specific schemas live alongside
their commands. Split out from ``notifier_handlers`` so each module
stays under the project's 300-line cap.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class NotifierRow(BaseModel):
    """One configured notifier — used by ``list``."""

    type: str
    settings: dict[str, Any]
    secret_configured: bool


class NotifierListData(BaseModel):
    """Data payload for ``notifier.list``."""

    notifiers: list[NotifierRow]


class NotifierTestData(BaseModel):
    """Data payload for ``notifier.test``."""

    type: str
    sent: bool


class NotifierAddData(BaseModel):
    """Data payload for ``notifier.add``."""

    type: str
    file: str
    applied: bool


class NotifierRemoveData(BaseModel):
    """Data payload for ``notifier.remove``."""

    type: str
    file: str
    removed: bool


__all__ = [
    "NotifierAddData",
    "NotifierListData",
    "NotifierRemoveData",
    "NotifierRow",
    "NotifierTestData",
]
