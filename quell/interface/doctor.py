"""`quell doctor` health check — verifies the environment is correctly set up.

Each check is a small async function that returns a :class:`CheckResult`.
Results are printed as a Rich table with green/red status icons.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

from quell.utils.errors import ConfigError
from quell.utils.keyring_utils import get_secret
from quell.utils.shell import command_exists, run_command

_console = Console()

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single doctor check."""

    name: str
    ok: bool
    detail: str = ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


async def check_python_version() -> CheckResult:
    """Verify Python is 3.12+."""
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 12)
    return CheckResult(
        name="Python ≥ 3.12",
        ok=ok,
        detail=f"{major}.{minor}.{sys.version_info.micro}",
    )


async def check_git() -> CheckResult:
    """Verify git is installed and on PATH."""
    exists = await command_exists("git")
    return CheckResult(
        name="git installed",
        ok=exists,
        detail="git found on PATH" if exists else "git not found — install git",
    )


async def check_docker() -> CheckResult:
    """Verify Docker daemon is running and reachable."""
    try:
        result = await run_command("docker", "info", "--format", "{{.ServerVersion}}")
        if result.ok:
            return CheckResult(
                name="Docker running",
                ok=True,
                detail=f"Docker Engine {result.stdout}",
            )
        return CheckResult(
            name="Docker running",
            ok=False,
            detail="Docker daemon not responding — is Docker Desktop running?",
        )
    except (FileNotFoundError, TimeoutError):
        return CheckResult(
            name="Docker running",
            ok=False,
            detail="docker not found — install Docker Desktop",
        )


async def check_config(project_dir: Path) -> CheckResult:
    """Verify .quell/config.toml exists and is valid."""
    from quell.config.loader import load_config

    try:
        load_config(local_dir=project_dir, inject_secrets=False)
        return CheckResult(
            name="Config valid", ok=True, detail=".quell/config.toml parsed OK"
        )
    except ConfigError as exc:
        return CheckResult(name="Config valid", ok=False, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        return CheckResult(name="Config valid", ok=False, detail=str(exc))


async def check_llm(project_dir: Path) -> CheckResult:
    """Verify the configured LLM provider is reachable."""
    from quell.config.loader import load_config

    try:
        cfg = load_config(local_dir=project_dir, inject_secrets=False)
    except ConfigError:
        return CheckResult(
            name="LLM reachable",
            ok=False,
            detail="Config invalid — fix config first",
        )

    provider = cfg.llm.model.split("/")[0] if "/" in cfg.llm.model else "openai"
    api_key = get_secret(f"quell/{provider}", "api_key")

    if not api_key:
        return CheckResult(
            name="LLM reachable",
            ok=False,
            detail=f"No API key for '{provider}' — run `quell init`",
        )

    # Simple reachability check: hit the provider's base URL
    _provider_urls: dict[str, str] = {
        "anthropic": "https://api.anthropic.com",
        "openai": "https://api.openai.com",
        "google": "https://generativelanguage.googleapis.com",
    }
    url = _provider_urls.get(provider)
    if url is None:
        return CheckResult(
            name="LLM reachable",
            ok=True,
            detail=f"Skipped — no reachability check for '{provider}'",
        )

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
        reachable = resp.status_code < 500
        return CheckResult(
            name="LLM reachable",
            ok=reachable,
            detail=f"{url} -> HTTP {resp.status_code}",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(name="LLM reachable", ok=False, detail=str(exc))


async def check_github_token() -> CheckResult:
    """Verify the GitHub token is set and valid."""
    token = get_secret("quell/github", "token")
    if not token:
        return CheckResult(
            name="GitHub token",
            ok=False,
            detail="Not set — run `quell init` to add your token",
        )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
        if resp.status_code == 200:
            login = resp.json().get("login", "unknown")
            return CheckResult(
                name="GitHub token", ok=True, detail=f"Authenticated as @{login}"
            )
        return CheckResult(
            name="GitHub token",
            ok=False,
            detail=f"HTTP {resp.status_code} — check token permissions",
        )
    except Exception as exc:  # noqa: BLE001
        return CheckResult(name="GitHub token", ok=False, detail=str(exc))


# ---------------------------------------------------------------------------
# Runner + display
# ---------------------------------------------------------------------------


async def _run_all_checks(project_dir: Path) -> list[CheckResult]:
    """Run all doctor checks concurrently and return results."""
    results = await asyncio.gather(
        check_python_version(),
        check_git(),
        check_docker(),
        check_config(project_dir),
        check_llm(project_dir),
        check_github_token(),
    )
    return list(results)


def run_doctor(project_dir: Path | None = None) -> bool:
    """Run all health checks, print a Rich table, and return True if all pass.

    Args:
        project_dir: Project root to check. Defaults to cwd.

    Returns:
        True if every check passed, False otherwise.
    """
    results = asyncio.run(_run_all_checks(project_dir or Path.cwd()))

    table = Table(title="Quell Doctor", show_header=True, header_style="bold cyan")
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for r in results:
        status = "[green]✓ OK[/green]" if r.ok else "[red]✗ FAIL[/red]"
        table.add_row(r.name, status, r.detail)

    _console.print()
    _console.print(table)
    _console.print()

    all_ok = all(r.ok for r in results)
    if all_ok:
        _console.print("[green]All checks passed — Quell is ready.[/green]\n")
    else:
        failed = sum(1 for r in results if not r.ok)
        _console.print(
            f"[yellow]{failed} check(s) failed.[/yellow] "
            "Fix the issues above, then run [bold]quell doctor[/bold] again.\n"
        )
    return all_ok


__all__ = ["CheckResult", "run_doctor"]
