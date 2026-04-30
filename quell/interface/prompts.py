"""Themed Questionary wrapper enforcing the interactive-prompt rules.

Per ``docs/cli-design.md`` §8.1: never prompt when a flag was supplied,
when ``--yes`` / ``--quiet`` / ``--json`` is set, or when stdin / stdout
isn't a TTY. ``prompt_or_flag()`` is the helper that enforces this so
no command has to rewrite the same precondition checks.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

import questionary
from questionary import Style

from quell.interface.errors import UsageError

# Theme — uses the Quell palette per docs/cli-design.md §9.1.
QUELL_STYLE: Style = Style(
    [
        ("qmark", "fg:#fb923c bold"),
        ("question", "bold"),
        ("answer", "fg:#fb923c bold"),
        ("pointer", "fg:#fb923c bold"),
        ("highlighted", "fg:#fb923c bold"),
        ("selected", "fg:#22c55e"),
        ("separator", "fg:#64748b"),
        ("instruction", "fg:#94a3b8"),
        ("text", ""),
        ("disabled", "fg:#64748b italic"),
    ]
)


def is_interactive() -> bool:
    """True when both stdin and stdout are TTYs (we can prompt safely)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def text(prompt: str, *, default: str = "") -> str:
    """Free-text prompt. Returns the entered value or ``default`` on empty."""
    answer = questionary.text(prompt, default=default, style=QUELL_STYLE).ask()
    return answer if answer is not None else default


def password(prompt: str) -> str:
    """Masked password / secret prompt."""
    answer = questionary.password(prompt, style=QUELL_STYLE).ask()
    return answer if answer is not None else ""


def select(
    prompt: str,
    choices: list[str] | list[tuple[str, str]],
    *,
    default: str | None = None,
) -> str:
    """Single-select from a list. ``choices`` may be plain strings or
    ``(label, value)`` pairs.

    Returns the selected value (or label, when no value was given).
    """
    qchoices = [
        questionary.Choice(label, value=value) if isinstance(c, tuple) else c
        for c in choices
        for label, value in ([c] if isinstance(c, tuple) else [(c, c)])
    ]
    answer = questionary.select(
        prompt, choices=qchoices, default=default, style=QUELL_STYLE
    ).ask()
    return answer if answer is not None else (default or "")


def confirm(prompt: str, *, default: bool = False) -> bool:
    """Yes/no prompt. Defaults to *default* if the user just presses Return."""
    answer = questionary.confirm(prompt, default=default, style=QUELL_STYLE).ask()
    return answer if answer is not None else default


def prompt_or_flag[T](
    flag_value: T | None,
    *,
    flag_name: str,
    yes: bool = False,
    quiet: bool = False,
    json_mode: bool = False,
    default: T | None = None,
    fallback: Callable[[], T] | None = None,
) -> T:
    """Resolve a value from a flag, falling back to an interactive prompt.

    Order of precedence:
      1. *flag_value* if not ``None`` — return it directly.
      2. *default* if ``--yes`` / ``--quiet`` / ``--json`` is set —
         skip prompts entirely and return the default.
      3. *fallback()* if running on a TTY — call the prompt.
      4. Otherwise — raise ``UsageError`` naming the missing flag, so
         agents and CI scripts get a clean error instead of a hang.

    Args:
        flag_value: The value the user supplied via the corresponding flag.
        flag_name: Flag name (without ``--``) for error messages.
        yes / quiet / json_mode: Universal flag state.
        default: Value to use when prompts are skipped (``--yes`` etc.).
        fallback: Zero-arg callable that runs the prompt on a TTY.
    """
    if flag_value is not None:
        return flag_value

    if yes or quiet or json_mode:
        if default is None:
            raise UsageError(
                f"--{flag_name} is required in non-interactive mode.",
                fix=f"Re-run with --{flag_name} <value>",
            )
        return default

    if not is_interactive():
        if default is None:
            raise UsageError(
                f"--{flag_name} is required (not running in a TTY).",
                fix=f"Re-run with --{flag_name} <value>",
            )
        return default

    if fallback is None:
        if default is None:
            raise UsageError(
                f"--{flag_name} is required.",
                fix=f"Re-run with --{flag_name} <value>",
            )
        return default

    return fallback()


__all__ = [
    "QUELL_STYLE",
    "confirm",
    "is_interactive",
    "password",
    "prompt_or_flag",
    "select",
    "text",
]
