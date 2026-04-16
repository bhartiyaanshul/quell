"""Subprocess helpers for Quell.

Thin wrappers around asyncio.subprocess for running external commands
(git, docker, etc.) used by the doctor check and monitors.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Result of a shell command execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """True if the command exited with code 0."""
        return self.returncode == 0


async def run_command(
    *args: str,
    timeout: float = 10.0,
) -> CommandResult:
    """Run an external command and return its output.

    Args:
        *args:   Command and arguments (e.g. ``"git", "--version"``).
        timeout: Maximum seconds to wait before raising TimeoutError.

    Returns:
        :class:`CommandResult` with returncode, stdout, and stderr.

    Raises:
        TimeoutError: If the command does not complete within *timeout* seconds.
        FileNotFoundError: If the executable is not found on PATH.
    """
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError as exc:
        proc.kill()
        await proc.communicate()
        raise TimeoutError(f"Command {args!r} timed out after {timeout}s") from exc

    return CommandResult(
        returncode=proc.returncode or 0,
        stdout=stdout_b.decode(errors="replace").strip(),
        stderr=stderr_b.decode(errors="replace").strip(),
    )


async def command_exists(name: str) -> bool:
    """Return True if *name* is available on the system PATH.

    Args:
        name: Executable name (e.g. ``"git"``, ``"docker"``).
    """
    try:
        result = await run_command(name, "--version", timeout=5.0)
        return result.ok
    except (FileNotFoundError, TimeoutError, OSError):
        return False


__all__ = ["CommandResult", "run_command", "command_exists"]
