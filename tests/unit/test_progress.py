"""Tests for ``quell.interface.progress``.

Under pytest capture ``Output.supports_animation`` is always False
(stdout isn't a TTY), so every test here exercises the static-fallback
path. The Rich-rendered animated bar is exercised by manual smoke
testing on a real terminal — unit-testing it would just verify Rich.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from quell.interface.output import Output
from quell.interface.progress import progress

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


def test_progress_yields_object_with_advance_and_update() -> None:
    out = Output(no_color=True)
    with progress(out, "Working", total=3) as p:
        assert hasattr(p, "advance")
        assert hasattr(p, "update")


def test_progress_static_fallback_emits_summary(capsys: CaptureFixture[str]) -> None:
    out = Output(no_color=True)
    with progress(out, "Loading skills", total=3) as p:
        p.advance()
        p.advance()
        p.advance()
    err = capsys.readouterr().err
    assert "Loading skills" in err
    assert "3/3 done" in err


def test_progress_advance_with_partial_total(capsys: CaptureFixture[str]) -> None:
    """Summary reflects whatever was completed, even on partial progress."""
    out = Output(no_color=True)
    with progress(out, "Step", total=5) as p:
        p.advance(2)
    err = capsys.readouterr().err
    assert "2/5 done" in err


def test_progress_update_changes_label_in_summary(
    capsys: CaptureFixture[str],
) -> None:
    out = Output(no_color=True)
    with progress(out, "Phase 1", total=2) as p:
        p.advance()
        p.update("Phase 2")
        p.advance()
    err = capsys.readouterr().err
    assert "Phase 2" in err
    assert "Phase 1" not in err


def test_progress_silent_in_json_mode(capsys: CaptureFixture[str]) -> None:
    """JSON mode: stdout stays empty so consumers can parse it."""
    out = Output(json_mode=True)
    with progress(out, "Working", total=2) as p:
        p.advance()
        p.advance()
    captured = capsys.readouterr()
    assert captured.out == ""
