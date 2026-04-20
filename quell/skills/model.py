"""Core skill types — the :class:`SkillFile` dataclass and category
constants shared by :mod:`quell.skills.loader` and
:mod:`quell.skills.selector`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

CATEGORIES: Final[tuple[str, ...]] = ("incidents", "frameworks", "technologies")
"""Recognised skill categories, searched in this order by ``load_skill``."""

ALLOWED_SEVERITY: Final[frozenset[str]] = frozenset({"low", "medium", "high"})


@dataclass(frozen=True)
class SkillFile:
    """A single loaded skill.

    Attributes:
        name:            Slug identifying the skill (also used in the system
                         prompt as the XML tag name).
        category:        One of :data:`CATEGORIES`.
        description:     One-line human-readable description.
        content:         Full Markdown body (frontmatter stripped).
        applicable_when: List of condition dicts; a skill matches a context
                         when *any* condition matches (OR semantics).
        severity_hint:   ``"low"`` | ``"medium"`` | ``"high"`` — surfaced to
                         the agent so it can prioritise.
    """

    name: str
    category: str
    description: str
    content: str
    applicable_when: list[dict[str, str]] = field(default_factory=list)
    severity_hint: str = "medium"


__all__ = ["CATEGORIES", "ALLOWED_SEVERITY", "SkillFile"]
