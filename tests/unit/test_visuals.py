"""Tests for quell.interface.visuals."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from quell.interface.output import Output
from quell.interface.visuals import (
    badge,
    diff,
    divider,
    empty_state,
    markdown,
    next_step,
    step_indicator,
    welcome_panel,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


# ---------------------------------------------------------------------------
# badge — returns markup string, no printing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected_style"),
    [
        ("success", "success"),
        ("resolved", "success"),
        ("warning", "warning"),
        ("detected", "warning"),
        ("error", "error"),
        ("info", "info"),
        ("investigating", "info"),
        ("unknown-status", "info"),  # fallback
    ],
)
def test_badge_maps_status_to_color(status: str, expected_style: str) -> None:
    result = badge("test", status=status)
    assert f"[{expected_style}]" in result
    assert "test" in result


def test_badge_returns_string_does_not_print(capsys: CaptureFixture[str]) -> None:
    badge("foo", status="success")
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


def test_diff_renders_filename_header(capsys: CaptureFixture[str]) -> None:
    diff(Output(no_color=True), "checkout.py", [])
    assert "checkout.py" in capsys.readouterr().out


def test_diff_renders_add_and_rm_lines(capsys: CaptureFixture[str]) -> None:
    diff(
        Output(no_color=True),
        "x.py",
        [("rm", "old line"), ("add", "new line"), ("context", "ctx line")],
    )
    out = capsys.readouterr().out
    assert "- old line" in out
    assert "+ new line" in out
    assert "ctx line" in out


def test_diff_silenced_in_quiet(capsys: CaptureFixture[str]) -> None:
    diff(Output(quiet=True, no_color=True), "x.py", [("add", "y")])
    assert capsys.readouterr().out == ""


def test_diff_silenced_in_json(capsys: CaptureFixture[str]) -> None:
    diff(Output(json_mode=True), "x.py", [("add", "y")])
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# markdown
# ---------------------------------------------------------------------------


def test_markdown_renders_text(capsys: CaptureFixture[str]) -> None:
    markdown(Output(no_color=True), "# Heading\n\nA paragraph.")
    out = capsys.readouterr().out
    assert "Heading" in out
    assert "paragraph" in out


def test_markdown_silenced_in_json(capsys: CaptureFixture[str]) -> None:
    markdown(Output(json_mode=True), "# x")
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# divider
# ---------------------------------------------------------------------------


def test_divider_with_label(capsys: CaptureFixture[str]) -> None:
    divider(Output(no_color=True), label="LLM provider")
    out = capsys.readouterr().out
    assert "LLM provider" in out
    assert "───" in out


def test_divider_without_label_emits_rule(capsys: CaptureFixture[str]) -> None:
    divider(Output(no_color=True))
    # Rich's Rule renders some box character — just confirm something
    # came out.
    assert capsys.readouterr().out != ""


# ---------------------------------------------------------------------------
# step_indicator
# ---------------------------------------------------------------------------


def test_step_indicator_format(capsys: CaptureFixture[str]) -> None:
    step_indicator(Output(no_color=True), 2, 5, "LLM provider")
    out = capsys.readouterr().out
    assert "2" in out
    assert "5" in out
    assert "LLM provider" in out


# ---------------------------------------------------------------------------
# next_step
# ---------------------------------------------------------------------------


def test_next_step_action_only(capsys: CaptureFixture[str]) -> None:
    next_step(Output(no_color=True), "Run quell doctor")
    out = capsys.readouterr().out
    assert "→" in out
    assert "Run quell doctor" in out


def test_next_step_with_command(capsys: CaptureFixture[str]) -> None:
    next_step(Output(no_color=True), "Verify your setup", command="quell doctor")
    out = capsys.readouterr().out
    assert "Verify your setup" in out
    assert "quell doctor" in out


# ---------------------------------------------------------------------------
# empty_state
# ---------------------------------------------------------------------------


def test_empty_state_renders_message_and_hint(capsys: CaptureFixture[str]) -> None:
    empty_state(
        Output(no_color=True),
        "(no incidents recorded yet)",
        hint="Try `quell watch` to start monitoring",
    )
    out = capsys.readouterr().out
    assert "no incidents" in out
    assert "→" in out
    assert "quell watch" in out


def test_empty_state_message_only(capsys: CaptureFixture[str]) -> None:
    empty_state(Output(no_color=True), "(empty)")
    out = capsys.readouterr().out
    assert "empty" in out
    assert "→" not in out


# ---------------------------------------------------------------------------
# welcome_panel
# ---------------------------------------------------------------------------


def test_welcome_panel_includes_title_and_body(
    capsys: CaptureFixture[str],
) -> None:
    welcome_panel(Output(no_color=True), "Quell", "Setup takes 90 seconds.")
    out = capsys.readouterr().out
    assert "Quell" in out
    assert "Setup takes 90 seconds" in out


def test_welcome_panel_silenced_in_json(capsys: CaptureFixture[str]) -> None:
    welcome_panel(Output(json_mode=True), "Quell", "body")
    assert capsys.readouterr().out == ""
