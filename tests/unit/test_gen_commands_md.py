"""Tests for ``scripts/gen_commands_md.py`` (Phase 5.6).

Locks the generator's output shape so accidental drift in the
introspection path is caught before a noisy ``docs/commands.md`` diff
lands. The ``--check`` mode is exercised by CI; this file unit-tests
the in-process rendering.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "gen_commands_md.py"


def _load_generator() -> ModuleType:
    """Import the script as a module — it isn't installable as a package."""
    spec = importlib.util.spec_from_file_location("gen_commands_md", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_render_produces_non_empty_markdown() -> None:
    rendered = _load_generator().render()
    assert rendered.startswith("# Quell CLI reference")
    assert "## Global verbs" in rendered
    assert "## Resources" in rendered


def test_render_includes_every_resource() -> None:
    rendered = _load_generator().render()
    for resource in ("incident", "config", "skill", "notifier"):
        assert f"## `{resource}` resource" in rendered, f"missing {resource}"


def test_render_includes_global_verbs() -> None:
    rendered = _load_generator().render()
    for verb in ("init", "doctor", "watch", "dashboard", "version"):
        assert f"`quell {verb}`" in rendered, f"missing global verb {verb}"


def test_render_propagates_examples_block() -> None:
    """The Examples: section in each docstring must round-trip into the doc."""
    rendered = _load_generator().render()
    assert "**Examples:**" in rendered
    # A representative example from `quell incident list`.
    assert "quell incident list" in rendered


def test_committed_doc_is_in_sync_with_generator() -> None:
    """`docs/commands.md` must match what the generator currently emits."""
    repo_root = _SCRIPT.parent.parent
    doc = (repo_root / "docs" / "commands.md").read_text(encoding="utf-8")
    rendered = _load_generator().render()
    assert doc == rendered, (
        "docs/commands.md is out of sync — "
        "run `python scripts/gen_commands_md.py` to regenerate."
    )
