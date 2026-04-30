"""CLI command definitions for Quell.

Imports the shared Typer ``app`` from ``quell.interface.main`` and
registers global verbs (``init``, ``doctor``, ``watch``, ``dashboard``,
``version``) plus resource sub-apps. Phase 3.1 adds the ``incident``
resource (see ``docs/cli-design.md`` §3); the old top-level ``history``
/ ``show`` / ``stats`` / ``replay`` commands remain as deprecated
aliases that emit a stderr warning and forward to the same handlers.

This module must be imported by ``main.py`` to activate the commands.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from quell.interface.cli_helpers import build_output, safe_run
from quell.interface.config_cmd import config_app
from quell.interface.incident_cmd import incident_app
from quell.interface.incident_handlers import (
    list_handler,
    replay_handler,
    show_handler,
    stats_handler,
)
from quell.interface.main import app
from quell.interface.notifier_cmd import notifier_app
from quell.interface.notifier_handlers import test_handler as notifier_test_handler
from quell.interface.output import Output
from quell.interface.skill_cmd import skill_app
from quell.version import __version__

# Resource sub-apps for the v0.3 grammar.
app.add_typer(incident_app, name="incident")
app.add_typer(config_app, name="config")
app.add_typer(skill_app, name="skill")
app.add_typer(notifier_app, name="notifier")


def _emit_deprecation(old: str, new: str) -> None:
    """Print a deprecation warning to stderr.

    Goes to stderr regardless of ``--json`` / ``--quiet`` so JSON output
    on stdout stays clean and CI logs still surface the migration hint.
    Stable prefix (``[deprecation]``) so parsers can grep for it.

    Uses ``typer.echo(err=True)`` rather than raw ``sys.stderr.write`` so
    Click's ``CliRunner`` captures it correctly under ``mix_stderr=False``.
    """
    typer.echo(
        f"[deprecation] '{old}' is deprecated; use '{new}' instead. "
        "(will be removed in v0.4.0)",
        err=True,
    )


@app.command()
def init(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to configure (defaults to current directory).",
            exists=False,
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Run non-interactively from flags + $QUELL_* env vars (no prompts).",
        ),
    ] = False,
    monitor: Annotated[
        str | None,
        typer.Option(
            "--monitor",
            help="Monitor type: local-file, http-poll, vercel, sentry. (--yes only)",
        ),
    ] = None,
    log_path: Annotated[
        str | None,
        typer.Option("--log-path", help="Log path for --monitor local-file."),
    ] = None,
    http_url: Annotated[
        str | None,
        typer.Option("--http-url", help="Health URL for --monitor http-poll."),
    ] = None,
    vercel_project_id: Annotated[
        str | None,
        typer.Option(
            "--vercel-project-id", help="Project ID for --monitor vercel (prj_...)."
        ),
    ] = None,
    sentry_org: Annotated[
        str | None,
        typer.Option("--sentry-org", help="Org slug for --monitor sentry."),
    ] = None,
    sentry_project: Annotated[
        str | None,
        typer.Option("--sentry-project", help="Project slug for --monitor sentry."),
    ] = None,
    notifier: Annotated[
        str | None,
        typer.Option(
            "--notifier",
            help="Notifier: discord, slack, telegram, or none. (--yes only)",
        ),
    ] = None,
    telegram_chat_id: Annotated[
        str | None,
        typer.Option(
            "--telegram-chat-id",
            help="Telegram chat ID (required for --notifier telegram).",
        ),
    ] = None,
    llm_provider: Annotated[
        str | None,
        typer.Option(
            "--llm-provider",
            help="LLM provider: anthropic, openai, google, or ollama.",
        ),
    ] = None,
    llm_model: Annotated[
        str | None,
        typer.Option(
            "--llm-model",
            help="Full LiteLLM model string (overrides provider default).",
        ),
    ] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Errors only.")] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Configure Quell for a project.

    Without ``--yes``, runs the interactive wizard (legacy behaviour).
    With ``--yes``, runs non-interactively from the flags below and
    ``$QUELL_*`` env vars for secrets — suitable for CI and agents.

    Examples:
      quell init                                              # interactive
      quell init --yes                                        # all defaults
      quell init --yes --monitor local-file --log-path /var/log/app.log \\
                 --llm-provider anthropic
      QUELL_ANTHROPIC_API_KEY=sk-... quell init --yes
    """
    out = build_output(quiet=quiet, no_color=no_color)
    if yes:
        from quell.interface.wizard_noninteractive import run_noninteractive_init

        safe_run(
            out,
            lambda: run_noninteractive_init(
                project_dir=(path or Path.cwd()),
                out=out,
                monitor=monitor or "local-file",
                log_path=log_path,
                http_url=http_url,
                vercel_project_id=vercel_project_id,
                sentry_org=sentry_org,
                sentry_project=sentry_project,
                notifier=notifier or "none",
                telegram_chat_id=telegram_chat_id,
                llm_provider=llm_provider or "anthropic",
                llm_model=llm_model,
            ),
        )
        return

    from quell.interface.wizard import run_init

    run_init(path)


@app.command()
def doctor(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to check (defaults to current directory).",
        ),
    ] = None,
    json_mode: Annotated[
        bool, typer.Option("--json", help="Emit a doctor.run JSON envelope.")
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet", "-q", help="Suppress the table; exit code is the signal."
        ),
    ] = False,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Check your environment and configuration for issues.

    Examples:
      quell doctor
      quell doctor --json | jq '.data.failed == 0'
      quell doctor --quiet || echo "something is wrong"
    """
    from quell.interface.doctor import run_doctor

    out = build_output(json_mode=json_mode, quiet=quiet, no_color=no_color)
    ok = run_doctor(path, out=out)
    if not ok:
        raise typer.Exit(code=1)


@app.command(name="explain")
def explain_cmd(
    command: Annotated[
        list[str] | None,
        typer.Argument(
            help="Command path to explain, e.g. 'incident list'. Omit for root.",
        ),
    ] = None,
    no_color: Annotated[
        bool, typer.Option("--no-color", help="Disable ANSI colors.")
    ] = False,
) -> None:
    """Verbose, agent-friendly docs for a single command or resource.

    Where `--help` is terse and `--help-json` is machine output,
    `explain` is the long-form variant: prints every flag with type
    and default, every documented example, and a closing reminder of
    the universal flag set. Designed for agents that need to use a
    command correctly on the first try.

    Examples:
      quell explain                       # root command tree
      quell explain incident list         # one verb in detail
      quell explain config                # whole sub-app
    """
    from quell.interface.explain import explain

    out = build_output(no_color=no_color)
    safe_run(out, lambda: explain(out, command or []))


@app.command(name="version")
def show_version() -> None:
    """Print the installed Quell version and exit.

    Includes the resolved binary path so users can tell which install
    is running (pipx vs. brew vs. pip) without running `which -a quell`.

    Examples:
      quell version
      quell --version    # canonical alias
    """
    from quell.interface.main import _resolve_binary_path

    Output().line(f"quell {__version__} ({_resolve_binary_path()})")


@app.command()
def watch(
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory to watch (defaults to current directory).",
        ),
    ] = None,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress the interrupted notice.")
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable ANSI colors in the wrapper notice."),
    ] = False,
) -> None:
    """Start the monitor -> detector -> agent investigation loop.

    Loop output is structured logging via Loguru and is unaffected by
    ``--quiet`` / ``--no-color`` for now (a JSONL stream is on the
    Phase 4 roadmap). The flags currently scope to the wrapper-level
    ``interrupted`` notice the CLI emits on Ctrl-C.

    Examples:
      quell watch                              # use cwd
      quell watch --path ~/projects/myapp      # different project
      quell watch 2>&1 | tee quell.log         # capture loguru output
    """
    from quell.config.loader import load_config
    from quell.watch import watch as run_watch

    out = build_output(quiet=quiet, no_color=no_color)
    config = load_config(local_dir=path, inject_secrets=True)
    try:
        asyncio.run(run_watch(config))
    except KeyboardInterrupt:
        out.info("(quell watch: interrupted)")


@app.command()
def dashboard(
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to bind the dashboard on."),
    ] = 7777,
    host: Annotated[
        str,
        typer.Option("--host", help="Interface to bind to (default localhost)."),
    ] = "127.0.0.1",
    no_open: Annotated[
        bool,
        typer.Option("--no-open", help="Do not auto-open the browser."),
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Suppress the interrupted notice.")
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable ANSI colors in the wrapper notice."),
    ] = False,
) -> None:
    """Launch the read-only web dashboard on the local machine.

    The dashboard is a Next.js app — its own logging is unaffected by
    ``--quiet`` / ``--no-color``. The flags currently scope to the
    wrapper-level ``interrupted`` notice on Ctrl-C.

    Examples:
      quell dashboard                          # http://localhost:7777
      quell dashboard --port 8080 --no-open    # custom port, no browser
      quell dashboard --host 0.0.0.0           # bind on every interface
    """
    from quell.dashboard.launcher import run_dashboard_sync

    out = build_output(quiet=quiet, no_color=no_color)
    try:
        run_dashboard_sync(host=host, port=port, open_browser=not no_open)
    except KeyboardInterrupt:
        out.info("(quell dashboard: interrupted)")


@app.command(name="test-notifier")
def test_notifier(
    channel: Annotated[
        str,
        typer.Argument(
            help="Notifier type to exercise: 'slack', 'discord', or 'telegram'."
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Project directory whose config to load.",
        ),
    ] = None,
) -> None:
    """[deprecated] Use ``quell notifier test <channel>`` instead."""
    _emit_deprecation("quell test-notifier", "quell notifier test")
    out = build_output()
    safe_run(out, lambda: asyncio.run(notifier_test_handler(out, channel, path)))


# ---------------------------------------------------------------------------
# Deprecated aliases — forward to the ``incident`` sub-app handlers.
# Removed in v0.4.0 per docs/cli-design.md §3.4.
# ---------------------------------------------------------------------------


@app.command()
def history(
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max rows to show.")] = 10,
) -> None:
    """[deprecated] Use ``quell incident list`` instead."""
    _emit_deprecation("quell history", "quell incident list")
    asyncio.run(
        list_handler(
            Output(),
            limit=limit,
            status=None,
            severity=None,
            since_dt=None,
        )
    )


@app.command()
def show(incident_id: str) -> None:
    """[deprecated] Use ``quell incident show <id>`` instead."""
    _emit_deprecation("quell show", "quell incident show")
    asyncio.run(show_handler(Output(), incident_id))


@app.command()
def stats() -> None:
    """[deprecated] Use ``quell incident stats`` instead."""
    _emit_deprecation("quell stats", "quell incident stats")
    asyncio.run(stats_handler(Output()))


@app.command()
def replay(incident_id: str) -> None:
    """[deprecated] Use ``quell incident replay <id>`` instead."""
    _emit_deprecation("quell replay", "quell incident replay")
    asyncio.run(replay_handler(Output(), incident_id))


__all__ = [
    "dashboard",
    "doctor",
    "history",
    "init",
    "replay",
    "show",
    "show_version",
    "stats",
    "test_notifier",
    "watch",
]
