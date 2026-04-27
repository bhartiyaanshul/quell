"""Backend for ``quell test-notifier <channel>``.

Constructs a synthetic :class:`Incident` (never touches the DB),
instantiates the matching notifier from the loaded config, and fires
one :meth:`~quell.notifiers.base.Notifier.notify` call.  Prints a
green tick on success or a red cross + error detail on failure.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from quell.config.loader import load_config
from quell.memory.models import Incident
from quell.notifiers import create_notifier
from quell.utils.errors import NotifierError

_console = Console()

_SUPPORTED = ("slack", "discord", "telegram")


def _build_test_incident() -> Incident:
    """Return an in-memory Incident that never touches the DB."""
    now = datetime.now(UTC)
    inc = Incident(
        id="inc_test_notifier",
        signature="test" + "a" * 12,
        severity="high",
        status="resolved",
        first_seen=now,
        last_seen=now,
        occurrence_count=1,
        root_cause=(
            "Test notification from `quell test-notifier`. If you received "
            "this in your channel, the webhook is correctly configured."
        ),
        fix_pr_url="https://github.com/bhartiyaanshul/quell/pull/0",
        postmortem=None,
        agent_graph_id=None,
    )
    return inc


async def run_test_notifier(channel: str, project_dir: Path | None = None) -> bool:
    """Send a synthetic incident to the named notifier channel.

    Args:
        channel:     ``"slack"`` / ``"discord"`` / ``"telegram"``.
        project_dir: Project whose config to load (defaults to cwd).

    Returns:
        True on success (webhook accepted the payload), False otherwise.
    """
    channel = channel.lower()
    if channel not in _SUPPORTED:
        _console.print(
            f"[red]Unknown channel:[/red] {channel!r}. "
            f"Supported: {', '.join(_SUPPORTED)}."
        )
        return False

    try:
        config = load_config(local_dir=project_dir, inject_secrets=True)
    except Exception as exc:  # noqa: BLE001
        _console.print(f"[red]Failed to load config:[/red] {exc}")
        return False

    match = next(
        (c for c in config.notifiers if c.type == channel),
        None,
    )
    if match is None:
        _console.print(
            f"[yellow]No {channel!r} notifier is configured.[/yellow] "
            f"Add one to .quell/config.toml and re-run `quell init` to "
            f"store the webhook secret."
        )
        return False

    try:
        notifier = create_notifier(match)
    except NotifierError as exc:
        _console.print(f"[red]Notifier setup failed:[/red] {exc}")
        return False

    incident = _build_test_incident()
    _console.print(f"Sending test incident via [cyan]{channel}[/cyan]...")
    await notifier.notify(incident)
    _console.print(f"[green]Sent.[/green] Check your {channel} channel.")
    return True


__all__ = ["run_test_notifier"]
