"""Tests for quell.interface.errors — CLI error classes + handler."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from quell.interface.errors import (
    AlreadyExistsError,
    AuthError,
    ConfigError,
    ExternalServiceError,
    NotFoundError,
    QuellCLIError,
    SandboxError,
    UsageError,
    handle_cli_error,
)
from quell.interface.output import Output

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


# ---------------------------------------------------------------------------
# Exit code taxonomy — pinned by the spec, must stay stable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("error_class", "expected_code"),
    [
        (QuellCLIError, 1),
        (UsageError, 2),
        (ConfigError, 3),
        (ExternalServiceError, 4),
        (SandboxError, 5),
        (AuthError, 6),
        (NotFoundError, 7),
        (AlreadyExistsError, 8),
    ],
)
def test_exit_code_per_class(
    error_class: type[QuellCLIError], expected_code: int
) -> None:
    assert error_class.exit_code == expected_code
    assert error_class("msg").exit_code == expected_code


def test_exit_code_can_be_overridden_per_instance() -> None:
    err = ConfigError("msg", exit_code=99)
    assert err.exit_code == 99


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_message_stored_on_instance() -> None:
    err = QuellCLIError("something broke")
    assert err.message == "something broke"
    assert str(err) == "something broke"


def test_fix_stored_on_instance() -> None:
    err = ConfigError("bad config", fix="quell init")
    assert err.fix == "quell init"


def test_fix_defaults_to_none() -> None:
    assert QuellCLIError("msg").fix is None


# ---------------------------------------------------------------------------
# handle_cli_error — renders via Output
# ---------------------------------------------------------------------------


def test_handler_emits_error_via_output(capsys: CaptureFixture[str]) -> None:
    err = ConfigError("Config file not found", fix="quell init")
    code = handle_cli_error(err, Output(no_color=True))
    captured = capsys.readouterr()
    assert code == 3
    assert "Config file not found" in captured.err
    assert "quell init" in captured.err
    assert captured.out == ""


def test_handler_returns_exit_code(capsys: CaptureFixture[str]) -> None:
    assert handle_cli_error(NotFoundError("inc_xyz"), Output(no_color=True)) == 7


def test_handler_emits_json_envelope_in_json_mode(
    capsys: CaptureFixture[str],
) -> None:
    err = ConfigError("bad", fix="quell init", exit_code=3)
    handle_cli_error(err, Output(json_mode=True))
    payload = json.loads(capsys.readouterr().err)
    assert payload == {
        "error": "bad",
        "fix_command": "quell init",
        "exit_code": 3,
        "kind": "error.v1",
    }


def test_handler_works_for_quiet_mode(capsys: CaptureFixture[str]) -> None:
    """Errors must surface even with --quiet."""
    handle_cli_error(UsageError("missing flag"), Output(quiet=True, no_color=True))
    assert "missing flag" in capsys.readouterr().err
