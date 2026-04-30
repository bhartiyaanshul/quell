"""``quell doctor`` health check — verifies the environment is set up.

Each check is a small async function that returns a :class:`CheckResult`.
Phase 3.5 adds the v0.3 universal-flag surface: results render via the
``Output`` facade in default mode, or as a single ``doctor.run`` JSON
envelope under ``--json``. The exit code is 0 when every check passes
and 1 otherwise — same contract as before.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import httpx
from pydantic import BaseModel

from quell.interface.output import Output
from quell.interface.progress import progress
from quell.utils.errors import ConfigError
from quell.utils.keyring_utils import get_secret
from quell.utils.shell import command_exists, run_command


class _Tracker(Protocol):
    """Subset of progress.* trackers we need for per-check advancement."""

    def advance(self, n: int = 1) -> None: ...
    def update(self, label: str | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single doctor check."""

    name: str
    ok: bool
    detail: str = ""


class CheckResultPayload(BaseModel):
    """JSON-serializable form of a single check result."""

    name: str
    status: str  # "ok" | "fail"
    detail: str


class DoctorRunData(BaseModel):
    """Data payload for ``doctor.run``."""

    checks: list[CheckResultPayload]
    passed: int
    failed: int


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


async def check_python_version() -> CheckResult:
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 12)
    return CheckResult(
        name="Python ≥ 3.12",
        ok=ok,
        detail=f"{major}.{minor}.{sys.version_info.micro}",
    )


async def check_git() -> CheckResult:
    exists = await command_exists("git")
    return CheckResult(
        name="git installed",
        ok=exists,
        detail="git found on PATH" if exists else "git not found — install git",
    )


async def check_docker() -> CheckResult:
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


async def _run_all_checks(
    project_dir: Path,
    *,
    tracker: _Tracker | None = None,
) -> list[CheckResult]:
    """Run every doctor check concurrently; advance *tracker* on each finish.

    Without *tracker* the implementation matches the legacy ``gather``
    behaviour. With one supplied, checks still run concurrently but
    we ``asyncio.wait`` per completion so the spinner label can show
    each result as it lands rather than only at the end.
    """
    coros: list[Coroutine[Any, Any, CheckResult]] = [
        check_python_version(),
        check_git(),
        check_docker(),
        check_config(project_dir),
        check_llm(project_dir),
        check_github_token(),
    ]

    if tracker is None:
        results = await asyncio.gather(*coros)
        return list(results)

    tasks: list[asyncio.Task[CheckResult]] = [asyncio.create_task(c) for c in coros]
    pending = set(tasks)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            result = task.result()
            tracker.advance()
            mark = "✓" if result.ok else "✗"
            tracker.update(f"{mark} {result.name}")
    return [t.result() for t in tasks]


def _run_with_progress(output: Output, project_dir: Path) -> list[CheckResult]:
    """Wrap ``_run_all_checks`` in a progress bar when animation is on.

    Without animation the bar adds nothing — the table emits at the end
    anyway — so we skip the wrapper and avoid the trailing static
    summary line that would otherwise duplicate the table's content.
    """
    if not output.supports_animation:
        return asyncio.run(_run_all_checks(project_dir))

    with progress(output, "Running checks", total=6) as tracker:
        return asyncio.run(_run_all_checks(project_dir, tracker=tracker))


def _to_payload(results: list[CheckResult]) -> DoctorRunData:
    return DoctorRunData(
        checks=[
            CheckResultPayload(
                name=r.name, status="ok" if r.ok else "fail", detail=r.detail
            )
            for r in results
        ],
        passed=sum(1 for r in results if r.ok),
        failed=sum(1 for r in results if not r.ok),
    )


def run_doctor(
    project_dir: Path | None = None,
    *,
    out: Output | None = None,
) -> bool:
    """Run every health check, render via *out*, return True if all pass.

    Args:
        project_dir: Project root to check. Defaults to cwd.
        out:         Output facade. Built fresh in default mode if omitted —
                     keeps the legacy ``run_doctor()`` call sites working.

    Returns:
        ``True`` if every check passed, ``False`` otherwise. The CLI
        layer in ``cli.py`` translates that to exit 0 / exit 1.
    """
    output = out or Output()
    results = _run_with_progress(output, project_dir or Path.cwd())
    payload = _to_payload(results)

    output.json("doctor.run", payload)
    if output.is_json or output.is_quiet:
        return payload.failed == 0

    output.header("Quell Doctor")
    table_rows = [[r.name, "OK" if r.ok else "FAIL", r.detail] for r in results]
    output.table(table_rows, headers=["CHECK", "STATUS", "DETAILS"])

    if payload.failed == 0:
        output.success("All checks passed — Quell is ready.")
    else:
        output.warn(
            f"{payload.failed} check(s) failed. "
            "Fix the issues above, then run `quell doctor` again."
        )
    return payload.failed == 0


__all__ = ["CheckResult", "CheckResultPayload", "DoctorRunData", "run_doctor"]
