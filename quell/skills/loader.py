"""Skill file loader — parse and discover Markdown skill files.

A *skill* is a Markdown file with a YAML frontmatter block.  The loader
discovers skills under ``quell/skills/<category>/*.md`` (category is one of
:data:`~quell.skills.model.CATEGORIES`) and returns fully parsed
:class:`~quell.skills.model.SkillFile` instances.

Selection (narrowing a skill list down to those applicable to an incident)
lives in :mod:`quell.skills.selector`.

Skill file shape::

    ---
    name: stripe-webhook-timeout
    category: incidents
    description: Stripe webhook endpoints timing out or returning 500
    applicable_when:
      - error_contains: "stripe-signature"
      - error_contains: "webhook timeout"
    severity_hint: high
    ---

    # Stripe webhook timeout runbook
    ...
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import yaml

from quell.skills.model import ALLOWED_SEVERITY, CATEGORIES, SkillFile
from quell.utils.errors import SkillError

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<frontmatter>.*?)\n---\s*\n?(?P<body>.*)$",
    re.DOTALL,
)

# Default bundled skills root — sibling directories under this package.
_DEFAULT_SKILLS_ROOT: Final[Path] = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_skill(
    text: str,
    *,
    name: str | None = None,
    category: str | None = None,
) -> SkillFile:
    """Parse a raw skill file *text* into a :class:`SkillFile`.

    When *name* and/or *category* are supplied, they must match the
    frontmatter values exactly — a defensive check that catches misplaced
    files (wrong directory) or renamed skills (stale filename).

    Raises:
        :class:`~quell.utils.errors.SkillError`: Frontmatter missing,
            malformed, or disagrees with *name* / *category*.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise SkillError(
            "Skill file is missing a YAML frontmatter block "
            "(expected '---' on the first line)."
        )

    try:
        meta = yaml.safe_load(match.group("frontmatter"))
    except yaml.YAMLError as exc:
        raise SkillError(f"Skill frontmatter is not valid YAML: {exc}") from exc

    if not isinstance(meta, dict):
        raise SkillError(
            "Skill frontmatter must be a mapping (got "
            f"{type(meta).__name__}: {meta!r})."
        )

    required = {"name", "category", "description", "severity_hint"}
    missing = required - meta.keys()
    if missing:
        raise SkillError(
            "Skill frontmatter is missing required field(s): "
            + ", ".join(sorted(missing))
        )

    fm_name = str(meta["name"]).strip()
    fm_category = str(meta["category"]).strip()
    description = str(meta["description"]).strip()
    severity = str(meta["severity_hint"]).strip().lower()

    if severity not in ALLOWED_SEVERITY:
        raise SkillError(
            f"severity_hint must be one of {sorted(ALLOWED_SEVERITY)}; got {severity!r}"
        )
    if fm_category not in CATEGORIES:
        raise SkillError(
            f"category must be one of {list(CATEGORIES)}; got {fm_category!r}"
        )
    if name is not None and name != fm_name:
        raise SkillError(
            f"Skill filename slug {name!r} does not match frontmatter name {fm_name!r}."
        )
    if category is not None and category != fm_category:
        raise SkillError(
            f"Skill directory {category!r} does not match frontmatter "
            f"category {fm_category!r}."
        )

    return SkillFile(
        name=fm_name,
        category=fm_category,
        description=description,
        content=match.group("body").strip(),
        applicable_when=_parse_applicable_when(meta.get("applicable_when", [])),
        severity_hint=severity,
    )


def _parse_applicable_when(raw: object) -> list[dict[str, str]]:
    """Validate and normalise the ``applicable_when`` frontmatter field.

    Each entry must be a dict mapping string trigger names to string
    values.  Missing or empty yields ``[]``.
    """
    if raw is None or raw == "":
        return []
    if not isinstance(raw, list):
        raise SkillError(
            "applicable_when must be a list of single-key dicts; got "
            f"{type(raw).__name__}"
        )

    out: list[dict[str, str]] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise SkillError(
                f"applicable_when[{i}] must be a dict; got {type(entry).__name__}"
            )
        coerced: dict[str, str] = {}
        for k, v in entry.items():
            if not isinstance(k, str):
                raise SkillError(
                    f"applicable_when[{i}] key must be a string; got {k!r}"
                )
            coerced[k] = "" if v is None else str(v)
        out.append(coerced)
    return out


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _skills_root(override: Path | None) -> Path:
    return override if override is not None else _DEFAULT_SKILLS_ROOT


def load_skill(
    name: str,
    *,
    skills_root: Path | None = None,
) -> SkillFile | None:
    """Load the skill with slug *name*, or return ``None`` if not found.

    Categories are searched in :data:`CATEGORIES` order.
    """
    root = _skills_root(skills_root)
    for category in CATEGORIES:
        path = root / category / f"{name}.md"
        if path.is_file():
            return parse_skill(
                path.read_text(encoding="utf-8"),
                name=name,
                category=category,
            )
    return None


def list_skills(*, skills_root: Path | None = None) -> list[SkillFile]:
    """Return every parseable skill found under *skills_root*, sorted by name.

    Unparseable files raise :class:`~quell.utils.errors.SkillError` — we do
    not silently skip broken skills, so developers notice typos early.
    """
    root = _skills_root(skills_root)
    out: list[SkillFile] = []
    for category in CATEGORIES:
        category_dir = root / category
        if not category_dir.is_dir():
            continue
        for md_path in sorted(category_dir.glob("*.md")):
            out.append(
                parse_skill(
                    md_path.read_text(encoding="utf-8"),
                    name=md_path.stem,
                    category=category,
                )
            )
    return sorted(out, key=lambda s: s.name)


__all__ = ["parse_skill", "load_skill", "list_skills"]
