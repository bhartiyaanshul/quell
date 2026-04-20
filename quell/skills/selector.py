"""Skill selection — match :class:`SkillFile` instances against an incident
context dict.

The selection language is intentionally small: each condition dict in a
skill's ``applicable_when`` list has one or more trigger keys drawn from
:data:`SUPPORTED_TRIGGERS`, each mapped to a string value.

* Within one condition dict, **all** keys must match (AND).
* Across a skill's condition list, **any** matching condition selects it (OR).
* Skills with an empty ``applicable_when`` are never auto-selected — they
  are explicit opt-in (loaded by name) to keep the system prompt focused.

Unknown trigger keys never match; a typo in a skill's frontmatter will
cause it to be silently unreachable rather than accidentally matching
every incident.
"""

from __future__ import annotations

from typing import Final

from quell.skills.model import SkillFile

SUPPORTED_TRIGGERS: Final[frozenset[str]] = frozenset(
    {
        "error_contains",
        "signature_contains",
        "framework_is",
        "tech_stack_includes",
    }
)


def _match_condition(cond: dict[str, str], context: dict[str, str]) -> bool:
    """Return ``True`` when at least one key/value in *cond* matches *context*."""
    for key, value in cond.items():
        val_lower = value.lower()
        if key == "error_contains" and val_lower in context.get("error", "").lower():
            return True
        if (
            key == "signature_contains"
            and val_lower in context.get("signature", "").lower()
        ):
            return True
        if key == "framework_is" and val_lower == context.get("framework", "").lower():
            return True
        if (
            key == "tech_stack_includes"
            and val_lower in context.get("tech_stack", "").lower()
        ):
            return True
    return False


def _condition_all_keys_match(cond: dict[str, str], context: dict[str, str]) -> bool:
    """Every key in *cond* must match *context* for the condition to fire."""
    if not cond:
        return False
    return all(_match_condition({key: value}, context) for key, value in cond.items())


def select_applicable(
    skills: list[SkillFile],
    context: dict[str, str],
) -> list[SkillFile]:
    """Return the subset of *skills* whose ``applicable_when`` matches *context*.

    Order of the input list is preserved.
    """
    out: list[SkillFile] = []
    for skill in skills:
        if not skill.applicable_when:
            continue
        for cond in skill.applicable_when:
            if _condition_all_keys_match(cond, context):
                out.append(skill)
                break
    return out


__all__ = ["SUPPORTED_TRIGGERS", "select_applicable"]
