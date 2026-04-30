"""CLI error class + top-level handler.

Per ``docs/cli-design.md`` §6 + §7: every error has a class, an exit
code, and a corrective action. The top-level handler catches
``QuellCLIError`` (and subclasses), formats it via ``Output``, and
returns the right exit code.

The exit-code taxonomy lives on the subclasses so commands write::

    raise ConfigError(
        "Config file not found at .quell/config.toml",
        fix="quell init",
    )

instead of having to remember that "config not found" is exit 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quell.interface.output import Output


class QuellCLIError(Exception):
    """Base class for CLI errors with corrective actions.

    Args:
        message: Single sentence describing what went wrong.
        fix: Optional corrective action — exact command(s) the user
            should run, or a specific instruction. Multi-line allowed;
            the first line becomes ``fix_command`` in JSON mode.
        exit_code: Override the class default. Useful when one error
            class covers multiple sub-cases with different codes.
    """

    exit_code: int = 1

    def __init__(
        self,
        message: str,
        *,
        fix: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.fix: str | None = fix
        if exit_code is not None:
            self.exit_code = exit_code


class UsageError(QuellCLIError):
    """Bad flag, missing required arg, unknown command. Exit 2."""

    exit_code = 2


class ConfigError(QuellCLIError):
    """Invalid TOML, schema violation, missing required field. Exit 3."""

    exit_code = 3


class ExternalServiceError(QuellCLIError):
    """Network failure, LLM provider 5xx, GitHub API down. Exit 4."""

    exit_code = 4


class SandboxError(QuellCLIError):
    """Docker not running, container failed to start. Exit 5."""

    exit_code = 5


class AuthError(QuellCLIError):
    """Missing or invalid API key, expired token. Exit 6."""

    exit_code = 6


class NotFoundError(QuellCLIError):
    """Incident ID, skill name, config key not present. Exit 7."""

    exit_code = 7


class AlreadyExistsError(QuellCLIError):
    """Add of something that already exists. Exit 8 (idempotent commands return 0)."""

    exit_code = 8


def handle_cli_error(error: QuellCLIError, output: Output) -> int:
    """Render *error* via *output* and return its exit code.

    Caller is responsible for actually exiting (``sys.exit`` or
    ``raise typer.Exit``) — this function is pure I/O so it can be
    unit-tested without sys-exit gymnastics.
    """
    output.error(error.message, fix=error.fix, exit_code=error.exit_code)
    return error.exit_code


__all__ = [
    "AlreadyExistsError",
    "AuthError",
    "ConfigError",
    "ExternalServiceError",
    "NotFoundError",
    "QuellCLIError",
    "SandboxError",
    "UsageError",
    "handle_cli_error",
]
