"""Tests for quell.interface.prompts.

Most of the behavior under test is the ``prompt_or_flag()`` precedence
ladder. The actual prompt rendering is questionary's job; we don't
re-test it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from quell.interface.errors import UsageError
from quell.interface.prompts import is_interactive, prompt_or_flag

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


# ---------------------------------------------------------------------------
# is_interactive
# ---------------------------------------------------------------------------


def test_is_interactive_false_under_pytest_capture(
    monkeypatch: MonkeyPatch,
) -> None:
    """pytest captures stdin/stdout, so this should always be False here."""
    # Under default pytest capture, sys.stdin.isatty() is False — proves
    # the helper detects a non-TTY context.
    assert is_interactive() is False


# ---------------------------------------------------------------------------
# prompt_or_flag — flag wins
# ---------------------------------------------------------------------------


def test_flag_value_returned_directly() -> None:
    """When the flag is supplied, never call fallback or look at TTY."""

    def fallback() -> str:
        raise AssertionError("fallback must not be called when flag is set")

    result = prompt_or_flag("user-supplied", flag_name="path", fallback=fallback)
    assert result == "user-supplied"


def test_flag_value_returned_when_yes_set() -> None:
    """``--yes`` doesn't override an explicitly supplied flag."""
    result = prompt_or_flag("user-supplied", flag_name="path", yes=True)
    assert result == "user-supplied"


# ---------------------------------------------------------------------------
# prompt_or_flag — non-interactive modes use default
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["yes", "quiet", "json_mode"])
def test_default_used_when_non_interactive_flag_set(flag: str) -> None:
    kwargs: dict[str, object] = {flag: True, "default": "fallback-value"}
    result = prompt_or_flag(
        None,
        flag_name="path",
        fallback=lambda: "prompt-value",
        **kwargs,
    )
    assert result == "fallback-value"


@pytest.mark.parametrize("flag", ["yes", "quiet", "json_mode"])
def test_usage_error_when_no_default_and_non_interactive(flag: str) -> None:
    kwargs: dict[str, object] = {flag: True}
    with pytest.raises(UsageError) as exc_info:
        prompt_or_flag(None, flag_name="log-path", **kwargs)
    assert "--log-path" in exc_info.value.message
    assert exc_info.value.fix is not None
    assert "--log-path" in exc_info.value.fix


# ---------------------------------------------------------------------------
# prompt_or_flag — non-TTY path
# ---------------------------------------------------------------------------


def test_usage_error_when_non_tty_and_no_default() -> None:
    """Pytest's capture makes is_interactive() False — should error fast."""
    with pytest.raises(UsageError) as exc_info:
        prompt_or_flag(
            None,
            flag_name="model",
            fallback=lambda: "would-prompt",
        )
    assert "--model" in exc_info.value.message


def test_default_used_when_non_tty_and_default_provided() -> None:
    """Falls back to the default rather than erroring when one's available."""
    result = prompt_or_flag(
        None,
        flag_name="model",
        default="anthropic/claude-haiku-4-5",
        fallback=lambda: "would-prompt",
    )
    assert result == "anthropic/claude-haiku-4-5"
