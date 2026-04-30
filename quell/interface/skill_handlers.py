"""Handlers + JSON schemas for ``quell skill <verb>``.

Phase 3.3 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2).
The Typer commands in ``skill_cmd.py`` are thin shims that build an
``Output`` from universal flags and call the matching handler here.

Disabled state is persisted via ``skills.disabled`` in the local
``config.toml`` — disabling a skill removes it from the watch loop's
auto-selection without deleting the runbook file. Explicit-by-name
loads (subagent spawn) still work; that's deliberate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel, ValidationError

from quell.config.loader import load_config
from quell.config.paths import local_config_file
from quell.config.schema import QuellConfig
from quell.interface.config_helpers import read_local_toml, set_in_dict
from quell.interface.errors import ConfigError, NotFoundError, handle_cli_error
from quell.interface.output import Output
from quell.skills import list_skills as load_all_skills
from quell.skills.loader import load_skill
from quell.skills.model import SkillFile
from quell.utils.toml_writer import dumps as toml_dumps

# ---------------------------------------------------------------------------
# JSON output schemas
# ---------------------------------------------------------------------------


class SkillRow(BaseModel):
    """One skill summary — used by ``list`` and ``show``."""

    name: str
    category: str
    description: str
    severity_hint: str
    enabled: bool


class SkillListData(BaseModel):
    """Data payload for ``skill.list``."""

    skills: list[SkillRow]


class SkillShowData(BaseModel):
    """Data payload for ``skill.show``."""

    name: str
    category: str
    description: str
    severity_hint: str
    enabled: bool
    applicable_when: list[dict[str, str]]
    content: str


class SkillToggleData(BaseModel):
    """Data payload for ``skill.enable`` / ``skill.disable``."""

    name: str
    enabled: bool
    file: str
    changed: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _disabled_set(path: Path | None) -> set[str]:
    return set(load_config(local_dir=path, inject_secrets=False).skills.disabled)


def _row(skill: SkillFile, disabled: set[str]) -> SkillRow:
    return SkillRow(
        name=skill.name,
        category=skill.category,
        description=skill.description,
        severity_hint=skill.severity_hint,
        enabled=skill.name not in disabled,
    )


def _write_disabled(file_path: Path, disabled: list[str]) -> None:
    """Persist ``skills.disabled = [...]`` to the local TOML, validating first."""
    raw = read_local_toml(file_path)
    set_in_dict(raw, "skills.disabled", sorted(set(disabled)))
    try:
        QuellConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(
            f"Updating skills.disabled would invalidate the config: {exc}",
            fix="quell config show   # confirm the existing shape",
        ) from exc
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(toml_dumps(raw), encoding="utf-8")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def list_handler(out: Output, path: Path | None) -> None:
    disabled = _disabled_set(path)
    skills = load_all_skills()
    rows = [_row(s, disabled) for s in skills]
    payload = SkillListData(skills=rows)
    out.json("skill.list", payload)
    if out.is_json or out.is_quiet:
        return

    if not rows:
        out.info("No skills found.")
        return

    table_rows = [
        [
            r.name,
            r.category,
            r.severity_hint,
            "yes" if r.enabled else "no",
            r.description,
        ]
        for r in rows
    ]
    out.table(
        table_rows,
        headers=["NAME", "CATEGORY", "SEV", "ENABLED", "DESCRIPTION"],
    )


def show_handler(out: Output, name: str, path: Path | None) -> None:
    skill = load_skill(name)
    if skill is None:
        code = handle_cli_error(
            NotFoundError(
                f"No skill named {name!r}.",
                fix="quell skill list   # see available skills",
            ),
            out,
        )
        raise typer.Exit(code=code)

    disabled = _disabled_set(path)
    payload = SkillShowData(
        name=skill.name,
        category=skill.category,
        description=skill.description,
        severity_hint=skill.severity_hint,
        enabled=skill.name not in disabled,
        applicable_when=skill.applicable_when,
        content=skill.content,
    )
    out.json("skill.show", payload)
    if out.is_json or out.is_quiet:
        return

    out.header(f"Skill {skill.name}")
    out.key_value(
        [
            ("category", skill.category),
            ("severity", skill.severity_hint),
            ("enabled", "yes" if payload.enabled else "no"),
            ("description", skill.description),
        ]
    )
    if skill.applicable_when:
        out.line("")
        out.line("  applicable when:")
        for cond in skill.applicable_when:
            for k, v in cond.items():
                out.line(f"    {k} = {v!r}")
    out.line("")
    out.line(skill.content)


def _toggle(
    out: Output,
    name: str,
    *,
    path: Path | None,
    enable: bool,
) -> None:
    if load_skill(name) is None:
        raise NotFoundError(
            f"No skill named {name!r}.",
            fix="quell skill list   # see available skills",
        )
    file_path = local_config_file(path)
    disabled = list(_disabled_set(path))
    in_list = name in disabled
    changed = False
    if enable and in_list:
        disabled.remove(name)
        changed = True
    elif not enable and not in_list:
        disabled.append(name)
        changed = True

    if changed:
        _write_disabled(file_path, disabled)
    elif enable and not in_list:
        # Already enabled — idempotent. Surface as a friendly note.
        pass
    elif not enable and in_list:
        pass

    payload: dict[str, Any] = {
        "name": name,
        "enabled": enable,
        "file": str(file_path),
        "changed": changed,
    }
    out.json(
        "skill.enable" if enable else "skill.disable",
        SkillToggleData(**payload),
    )
    if out.is_json or out.is_quiet:
        return
    state = "enabled" if enable else "disabled"
    if changed:
        out.success(f"{name} {state}.")
    else:
        out.info(f"{name} was already {state}; no change.")


def enable_handler(out: Output, name: str, path: Path | None) -> None:
    _toggle(out, name, path=path, enable=True)


def disable_handler(out: Output, name: str, path: Path | None) -> None:
    _toggle(out, name, path=path, enable=False)


__all__ = [
    "SkillListData",
    "SkillRow",
    "SkillShowData",
    "SkillToggleData",
    "disable_handler",
    "enable_handler",
    "list_handler",
    "show_handler",
]
