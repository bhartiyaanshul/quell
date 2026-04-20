"""Tests for quell.skills — parsing, loading, and selection."""

from __future__ import annotations

from pathlib import Path

import pytest

from quell.skills import (
    CATEGORIES,
    SkillFile,
    list_skills,
    load_skill,
    parse_skill,
    select_applicable,
)
from quell.utils.errors import SkillError

# ---------------------------------------------------------------------------
# parse_skill
# ---------------------------------------------------------------------------


_VALID_SKILL = """---
name: demo-skill
category: incidents
description: A demo skill for tests
applicable_when:
  - error_contains: "boom"
  - framework_is: "fastapi"
severity_hint: medium
---

# Demo

The body goes here.
"""


def test_parse_skill_valid() -> None:
    skill = parse_skill(_VALID_SKILL)
    assert skill.name == "demo-skill"
    assert skill.category == "incidents"
    assert skill.description == "A demo skill for tests"
    assert skill.severity_hint == "medium"
    assert skill.applicable_when == [
        {"error_contains": "boom"},
        {"framework_is": "fastapi"},
    ]
    assert "The body goes here." in skill.content
    assert not skill.content.startswith("---")  # frontmatter stripped


def test_parse_skill_accepts_matching_name_and_category() -> None:
    skill = parse_skill(_VALID_SKILL, name="demo-skill", category="incidents")
    assert skill.name == "demo-skill"


def test_parse_skill_rejects_slug_mismatch() -> None:
    with pytest.raises(SkillError, match="does not match"):
        parse_skill(_VALID_SKILL, name="wrong-name")


def test_parse_skill_rejects_category_mismatch() -> None:
    with pytest.raises(SkillError, match="does not match"):
        parse_skill(_VALID_SKILL, category="frameworks")


def test_parse_skill_missing_frontmatter() -> None:
    with pytest.raises(SkillError, match="missing a YAML frontmatter"):
        parse_skill("just plain markdown, no frontmatter")


def test_parse_skill_malformed_yaml() -> None:
    text = "---\nname: foo\ncategory: incidents\n  bad: [unbalanced\n---\nbody"
    with pytest.raises(SkillError, match="not valid YAML"):
        parse_skill(text)


def test_parse_skill_missing_required_fields() -> None:
    text = "---\nname: foo\ncategory: incidents\n---\nbody"
    with pytest.raises(SkillError, match="missing required field"):
        parse_skill(text)


def test_parse_skill_invalid_severity() -> None:
    text = """---
name: demo
category: incidents
description: x
severity_hint: catastrophic
---
body"""
    with pytest.raises(SkillError, match="severity_hint"):
        parse_skill(text)


def test_parse_skill_invalid_category() -> None:
    text = """---
name: demo
category: vibes
description: x
severity_hint: low
---
body"""
    with pytest.raises(SkillError, match="category must be one of"):
        parse_skill(text)


def test_parse_skill_applicable_when_must_be_list() -> None:
    text = """---
name: demo
category: incidents
description: x
severity_hint: low
applicable_when: "not a list"
---
body"""
    with pytest.raises(SkillError, match="must be a list"):
        parse_skill(text)


def test_parse_skill_applicable_when_entry_must_be_dict() -> None:
    text = """---
name: demo
category: incidents
description: x
severity_hint: low
applicable_when:
  - "not a dict"
---
body"""
    with pytest.raises(SkillError, match="must be a dict"):
        parse_skill(text)


def test_parse_skill_empty_applicable_when_ok() -> None:
    text = """---
name: demo
category: incidents
description: x
severity_hint: low
---
body"""
    skill = parse_skill(text)
    assert skill.applicable_when == []


# ---------------------------------------------------------------------------
# load_skill / list_skills — using an isolated skills root fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_skills_root(tmp_path: Path) -> Path:
    """Build a temp skills directory tree with two skills."""
    (tmp_path / "incidents").mkdir()
    (tmp_path / "frameworks").mkdir()
    (tmp_path / "technologies").mkdir()

    (tmp_path / "incidents" / "alpha.md").write_text(
        """---
name: alpha
category: incidents
description: first
applicable_when:
  - error_contains: "alpha"
severity_hint: high
---

alpha body
""",
        encoding="utf-8",
    )
    (tmp_path / "frameworks" / "beta.md").write_text(
        """---
name: beta
category: frameworks
description: second
applicable_when:
  - framework_is: "beta"
severity_hint: low
---

beta body
""",
        encoding="utf-8",
    )
    return tmp_path


def test_load_skill_finds_across_categories(fake_skills_root: Path) -> None:
    skill = load_skill("alpha", skills_root=fake_skills_root)
    assert skill is not None
    assert skill.category == "incidents"

    other = load_skill("beta", skills_root=fake_skills_root)
    assert other is not None
    assert other.category == "frameworks"


def test_load_skill_missing_returns_none(fake_skills_root: Path) -> None:
    assert load_skill("does-not-exist", skills_root=fake_skills_root) is None


def test_list_skills_returns_all_sorted(fake_skills_root: Path) -> None:
    skills = list_skills(skills_root=fake_skills_root)
    assert [s.name for s in skills] == ["alpha", "beta"]


def test_list_skills_handles_missing_category_dirs(tmp_path: Path) -> None:
    # Only one of the three category dirs exists.
    (tmp_path / "incidents").mkdir()
    (tmp_path / "incidents" / "only.md").write_text(
        """---
name: only
category: incidents
description: x
applicable_when: []
severity_hint: low
---
""",
        encoding="utf-8",
    )
    skills = list_skills(skills_root=tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "only"


def test_list_skills_raises_on_broken_file(tmp_path: Path) -> None:
    (tmp_path / "incidents").mkdir()
    (tmp_path / "incidents" / "broken.md").write_text(
        "no frontmatter here", encoding="utf-8"
    )
    with pytest.raises(SkillError):
        list_skills(skills_root=tmp_path)


# ---------------------------------------------------------------------------
# select_applicable
# ---------------------------------------------------------------------------


def _mk(
    name: str,
    when: list[dict[str, str]],
    *,
    category: str = "incidents",
    severity: str = "medium",
) -> SkillFile:
    return SkillFile(
        name=name,
        category=category,
        description="",
        content="",
        applicable_when=when,
        severity_hint=severity,
    )


def test_select_applicable_error_contains_matches() -> None:
    s = _mk("s1", [{"error_contains": "timeout"}])
    assert select_applicable([s], {"error": "Database TIMEOUT after 30s"}) == [s]


def test_select_applicable_error_contains_no_match() -> None:
    s = _mk("s1", [{"error_contains": "timeout"}])
    assert select_applicable([s], {"error": "permission denied"}) == []


def test_select_applicable_framework_is_case_insensitive() -> None:
    s = _mk("s1", [{"framework_is": "fastapi"}])
    assert select_applicable([s], {"framework": "FastAPI"}) == [s]


def test_select_applicable_tech_stack_includes() -> None:
    s = _mk("s1", [{"tech_stack_includes": "postgres"}])
    assert select_applicable([s], {"tech_stack": "Postgres,Redis,Docker"}) == [s]


def test_select_applicable_or_semantics_across_conditions() -> None:
    s = _mk("s1", [{"error_contains": "x"}, {"framework_is": "fastapi"}])
    # Only the second condition matches — skill still selected.
    assert select_applicable([s], {"framework": "fastapi"}) == [s]


def test_select_applicable_signature_contains() -> None:
    s = _mk("s1", [{"signature_contains": "deadbeef"}])
    assert select_applicable([s], {"signature": "errsig-DEADBEEF-42"}) == [s]


def test_select_applicable_skill_without_when_never_selected() -> None:
    s = _mk("s1", [])
    # Empty applicable_when means the skill is opt-in (e.g. loaded by name).
    assert select_applicable([s], {"error": "anything"}) == []


def test_select_applicable_unknown_key_does_not_match() -> None:
    s = _mk("s1", [{"unknown_trigger": "value"}])
    assert select_applicable([s], {"error": "value"}) == []


def test_select_applicable_multi_key_dict_requires_all() -> None:
    # AND within a dict: both keys must match.
    s = _mk("s1", [{"framework_is": "fastapi", "error_contains": "boom"}])
    assert select_applicable([s], {"framework": "fastapi", "error": "boom"}) == [s]
    assert select_applicable([s], {"framework": "fastapi", "error": "ok"}) == []


def test_select_applicable_preserves_input_order() -> None:
    skills = [
        _mk(str(i), [{"error_contains": "x"}]) for i in ("zebra", "alpha", "mango")
    ]
    out = select_applicable(skills, {"error": "x"})
    assert [s.name for s in out] == ["zebra", "alpha", "mango"]


# ---------------------------------------------------------------------------
# Bundled skills smoke test — the 7 shipped skills must parse cleanly.
# ---------------------------------------------------------------------------


def test_bundled_skills_parse() -> None:
    skills = list_skills()  # uses default bundled root
    names = {s.name for s in skills}
    expected = {
        "stripe-webhook-timeout",
        "unhandled-null",
        "openai-rate-limit",
        "fastapi",
        "nextjs-app-router",
        "postgres",
        "redis",
    }
    assert expected.issubset(names)
    for skill in skills:
        assert skill.category in CATEGORIES
        assert skill.description
        assert skill.content
        assert skill.severity_hint in {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# Integration with IncidentCommander — skills render into the system prompt
# ---------------------------------------------------------------------------


def test_incident_commander_renders_skills_into_prompt() -> None:
    from quell.agents.incident_commander import IncidentCommander
    from quell.config.schema import QuellConfig

    skill = _mk(
        "race-condition",
        [{"error_contains": "race"}],
        category="incidents",
    )
    # Replace content so we can assert it appears in the rendered prompt.
    skill = SkillFile(
        name=skill.name,
        category=skill.category,
        description="demo",
        content="Check for shared mutable state.",
        applicable_when=skill.applicable_when,
        severity_hint=skill.severity_hint,
    )

    cfg = QuellConfig()
    cmd = IncidentCommander(cfg, loaded_skills=[skill])
    prompt = cmd._render_system_prompt()

    assert "<specialized_knowledge>" in prompt
    assert "<race-condition>" in prompt
    assert "Check for shared mutable state." in prompt
    assert "</race-condition>" in prompt


def test_incident_commander_empty_skills_omits_block() -> None:
    from quell.agents.incident_commander import IncidentCommander
    from quell.config.schema import QuellConfig

    cfg = QuellConfig()
    cmd = IncidentCommander(cfg, loaded_skills=[])
    prompt = cmd._render_system_prompt()
    assert "<specialized_knowledge>" not in prompt
