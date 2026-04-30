"""Pydantic schemas for ``quell config <verb>`` JSON output.

Per ``docs/cli-design.md`` §13: resource-specific schemas live alongside
their commands rather than in the central ``output_schemas`` module.
Split from ``config_handlers`` so each module stays under the project's
300-line cap.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ConfigShowData(BaseModel):
    """Data payload for ``config.show``."""

    config: dict[str, Any]
    file: str


class ConfigGetData(BaseModel):
    """Data payload for ``config.get``."""

    key: str
    value: Any


class ConfigSetData(BaseModel):
    """Data payload for ``config.set``."""

    key: str
    old_value: Any
    new_value: Any
    file: str
    applied: bool


class ConfigValidateData(BaseModel):
    """Data payload for ``config.validate``."""

    valid: bool
    errors: list[str]
    file: str


__all__ = [
    "ConfigGetData",
    "ConfigSetData",
    "ConfigShowData",
    "ConfigValidateData",
]
