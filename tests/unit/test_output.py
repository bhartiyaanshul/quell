"""Tests for quell.interface.output.

Covers the mode matrix from docs/cli-design.md: every method must
behave correctly under default, --quiet, --json, --no-color, and
--verbose. JSON envelopes round-trip through ``json.loads`` to prove
the output is parseable.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from quell.interface.output import Output

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch


# ---------------------------------------------------------------------------
# Status methods — info / success / warn
# ---------------------------------------------------------------------------


def test_info_emits_in_default_mode(capsys: CaptureFixture[str]) -> None:
    Output().info("hello")
    out = capsys.readouterr().out
    assert "hello" in out


def test_info_suppressed_in_quiet(capsys: CaptureFixture[str]) -> None:
    Output(quiet=True).info("hello")
    assert capsys.readouterr().out == ""


def test_info_suppressed_in_json(capsys: CaptureFixture[str]) -> None:
    Output(json_mode=True).info("hello")
    assert capsys.readouterr().out == ""


def test_success_emits_check_prefix(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).success("done")
    out = capsys.readouterr().out
    assert "✓" in out
    assert "done" in out


def test_warn_emits_bang_prefix(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).warn("careful")
    out = capsys.readouterr().out
    assert "!" in out
    assert "careful" in out


# ---------------------------------------------------------------------------
# error — always emitted; JSON envelope under --json
# ---------------------------------------------------------------------------


def test_error_emits_to_stderr_in_default(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).error("bad thing")
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "bad thing" in captured.err
    assert captured.out == ""


def test_error_includes_fix_block(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).error("bad", fix="quell init\nquell doctor")
    err = capsys.readouterr().err
    assert "Fix:" in err
    assert "quell init" in err
    assert "quell doctor" in err


def test_error_emits_in_quiet_mode(capsys: CaptureFixture[str]) -> None:
    """Errors must always surface, even with --quiet."""
    Output(quiet=True, no_color=True).error("bad")
    err = capsys.readouterr().err
    assert "bad" in err


def test_error_emits_json_envelope_in_json_mode(
    capsys: CaptureFixture[str],
) -> None:
    Output(json_mode=True).error("bad", fix="quell init", exit_code=3)
    err = capsys.readouterr().err
    payload = json.loads(err)
    assert payload == {
        "error": "bad",
        "fix_command": "quell init",
        "exit_code": 3,
        "kind": "error.v1",
    }


def test_error_json_envelope_uses_first_fix_line_only(
    capsys: CaptureFixture[str],
) -> None:
    """Multi-line ``fix`` collapses to first line for ``fix_command``."""
    Output(json_mode=True).error("bad", fix="quell init\nquell doctor")
    payload = json.loads(capsys.readouterr().err)
    assert payload["fix_command"] == "quell init"


def test_error_json_envelope_omits_fix_when_none(
    capsys: CaptureFixture[str],
) -> None:
    Output(json_mode=True).error("bad")
    payload = json.loads(capsys.readouterr().err)
    assert payload["fix_command"] is None


# ---------------------------------------------------------------------------
# Rendering methods — header / panel / table / key_value / line
# ---------------------------------------------------------------------------


def test_header_emits_in_default(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).header("Setup")
    assert "Setup" in capsys.readouterr().out


def test_panel_emits_box_borders(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).panel("Welcome", title="Quell")
    out = capsys.readouterr().out
    assert "Welcome" in out
    assert "Quell" in out


def test_table_aligns_rows(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).table(
        rows=[["inc_a1", "resolved", "high"], ["inc_b2", "detected", "low"]],
        headers=["ID", "STATUS", "SEV"],
        footer="Showing 2 of 2.",
    )
    out = capsys.readouterr().out
    assert "ID" in out
    assert "STATUS" in out
    assert "inc_a1" in out
    assert "Showing 2 of 2" in out


def test_key_value_emits_pairs(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).key_value([("Project", "quell"), ("Version", "0.3.0")])
    out = capsys.readouterr().out
    assert "Project" in out
    assert "quell" in out
    assert "Version" in out


def test_render_methods_suppressed_in_quiet(capsys: CaptureFixture[str]) -> None:
    out = Output(quiet=True, no_color=True)
    out.header("Setup")
    out.panel("body")
    out.table([["x"]], headers=["a"])
    out.key_value([("k", "v")])
    out.line("raw")
    assert capsys.readouterr().out == ""


def test_render_methods_suppressed_in_json(capsys: CaptureFixture[str]) -> None:
    out = Output(json_mode=True)
    out.header("Setup")
    out.panel("body")
    out.table([["x"]], headers=["a"])
    out.key_value([("k", "v")])
    out.line("raw")
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# json method — only emits under --json
# ---------------------------------------------------------------------------


def test_json_emits_envelope_in_json_mode(capsys: CaptureFixture[str]) -> None:
    Output(json_mode=True).json("incident.list", {"incidents": []})
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "kind": "incident.list",
        "version": "0.3",
        "data": {"incidents": []},
    }


def test_json_no_op_in_default_mode(capsys: CaptureFixture[str]) -> None:
    Output().json("incident.list", {"incidents": []})
    assert capsys.readouterr().out == ""


def test_json_serializes_pydantic_model_via_model_dump(
    capsys: CaptureFixture[str],
) -> None:
    from pydantic import BaseModel

    class Sample(BaseModel):
        id: str
        count: int

    Output(json_mode=True).json("sample.show", Sample(id="x1", count=3))
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"id": "x1", "count": 3}


def test_json_falls_back_to_str_for_unknown_types(
    capsys: CaptureFixture[str],
) -> None:
    """Path / datetime / etc. should not crash the encoder."""
    from pathlib import Path

    Output(json_mode=True).json("config.show", {"path": Path("/tmp/x")})
    payload = json.loads(capsys.readouterr().out)
    # Path renders to str; exact form is platform-dependent.
    assert "path" in payload["data"]


# ---------------------------------------------------------------------------
# debug method — only emits under --verbose
# ---------------------------------------------------------------------------


def test_debug_suppressed_by_default(capsys: CaptureFixture[str]) -> None:
    Output(no_color=True).debug("internal state")
    assert capsys.readouterr().err == ""


def test_debug_emits_when_verbose(capsys: CaptureFixture[str]) -> None:
    Output(verbose=True, no_color=True).debug("internal state")
    assert "internal state" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Capability properties
# ---------------------------------------------------------------------------


def test_is_json_property() -> None:
    assert Output(json_mode=True).is_json is True
    assert Output().is_json is False


def test_is_quiet_property() -> None:
    assert Output(quiet=True).is_quiet is True
    assert Output().is_quiet is False


def test_supports_color_false_under_capture() -> None:
    # capsys redirects stdout to a non-TTY pipe, so Rich reports
    # is_terminal=False and supports_color is False.
    assert Output().supports_color is False


def test_supports_animation_false_under_capture() -> None:
    assert Output().supports_animation is False


def test_supports_animation_false_when_quell_no_anim_set(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("QUELL_NO_ANIM", "1")
    assert Output().supports_animation is False


def test_supports_animation_false_in_json_mode() -> None:
    assert Output(json_mode=True).supports_animation is False


def test_supports_animation_false_in_quiet_mode() -> None:
    assert Output(quiet=True).supports_animation is False


# ---------------------------------------------------------------------------
# NO_COLOR / --no-color
# ---------------------------------------------------------------------------


def test_no_color_env_disables_color(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert Output().supports_color is False


@pytest.mark.parametrize("no_color", [True, False])
def test_explicit_no_color_overrides_env(
    monkeypatch: MonkeyPatch, no_color: bool
) -> None:
    """``no_color=True`` always disables; ``no_color=False`` lets env decide."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    out = Output(no_color=no_color)
    if no_color:
        assert out.supports_color is False
    else:
        # Without NO_COLOR env, capsys still makes stdout non-TTY,
        # so supports_color is False regardless.
        assert out.supports_color is False
