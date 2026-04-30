"""Tests for quell.interface.spinner.

Under pytest capture, ``Output.supports_animation`` is always False
(stdout isn't a TTY), so every test here exercises the static-fallback
path. The animated path is exercised by integration / smoke tests on
real terminals — unit-testing rich.Status would just verify rich.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from quell.interface.output import Output
from quell.interface.spinner import spinner

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


def test_spinner_yields_object_with_update_method() -> None:
    out = Output(no_color=True)
    with spinner(out, "Working…") as status:
        assert hasattr(status, "update")


def test_spinner_initial_message_emitted_in_static_mode(
    capsys: CaptureFixture[str],
) -> None:
    """Non-TTY: the initial message goes to stderr immediately."""
    out = Output(no_color=True)
    with spinner(out, "Calling LLM"):
        pass
    err = capsys.readouterr().err
    assert "Calling LLM" in err


def test_spinner_update_emits_new_line_in_static_mode(
    capsys: CaptureFixture[str],
) -> None:
    out = Output(no_color=True)
    with spinner(out, "Phase 1") as status:
        status.update("Phase 2")
        status.update("Phase 3")
    err = capsys.readouterr().err
    assert "Phase 1" in err
    assert "Phase 2" in err
    assert "Phase 3" in err


def test_spinner_silent_under_quiet_mode(capsys: CaptureFixture[str]) -> None:
    """Quiet mode disables animation; the static fallback still emits
    so users know something's happening — but writes to stderr, not stdout.
    """
    out = Output(quiet=True, no_color=True)
    with spinner(out, "Working"):
        pass
    captured = capsys.readouterr()
    assert captured.out == ""
    # Static fallback still emits to stderr — quiet mode suppresses
    # *info-level stdout*, not progress on stderr. This matches how
    # `make` and `cargo` behave.
    assert "Working" in captured.err


def test_spinner_yields_static_under_json_mode(capsys: CaptureFixture[str]) -> None:
    """JSON mode forces animation off so output stays parseable."""
    out = Output(json_mode=True)
    with spinner(out, "Working") as status:
        status.update("Done")
    captured = capsys.readouterr()
    # stdout must remain empty — the consumer is parsing JSON there.
    assert captured.out == ""


def test_quell_spinner_shape_registered() -> None:
    """``quell`` spinner is registered with Rich's global SPINNERS dict."""
    from rich.spinner import SPINNERS

    assert "quell" in SPINNERS
    shape = SPINNERS["quell"]
    assert shape["frames"], "expected non-empty frames"
    assert isinstance(shape["interval"], int)


def test_spinner_disabled_when_quell_no_anim_env_set(
    capsys: CaptureFixture[str], monkeypatch: object
) -> None:
    """``QUELL_NO_ANIM=1`` forces the static fallback even on a TTY."""
    # ``monkeypatch`` is a pytest fixture; we restore via its API.
    import pytest

    mp = pytest.MonkeyPatch()
    try:
        mp.setenv("QUELL_NO_ANIM", "1")
        out = Output(no_color=True)
        assert out.supports_animation is False
        with spinner(out, "Working"):
            pass
        # Static fallback emits the message to stderr.
        assert "Working" in capsys.readouterr().err
    finally:
        mp.undo()
