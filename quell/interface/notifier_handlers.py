"""Handlers for ``quell notifier <verb>`` (Phase 3.4).

Notifier entries live in ``[[notifiers]]`` arrays in the local
``config.toml``; webhook URLs and bot tokens live in the OS keychain
and are never written to TOML. ``add`` writes the structural entry
only — the user runs ``quell init`` to store the secret.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from quell.config.loader import load_config
from quell.config.paths import local_config_file
from quell.config.schema import QuellConfig
from quell.interface.config_helpers import read_local_toml
from quell.interface.errors import (
    AlreadyExistsError,
    ConfigError,
    NotFoundError,
    UsageError,
)
from quell.interface.notifier_schemas import (
    NotifierAddData,
    NotifierListData,
    NotifierRemoveData,
    NotifierRow,
    NotifierTestData,
)
from quell.interface.output import Output
from quell.interface.prompts import confirm, is_interactive
from quell.memory.models import Incident
from quell.notifiers import create_notifier
from quell.utils.errors import NotifierError
from quell.utils.keyring_utils import get_secret
from quell.utils.toml_writer import dumps as toml_dumps

_SUPPORTED: tuple[str, ...] = ("slack", "discord", "telegram")
_SECRET_FIELD: dict[str, str] = {
    "slack": "webhook_url",
    "discord": "webhook_url",
    "telegram": "bot_token",
}


def _check_channel(channel: str) -> str:
    channel = channel.lower()
    if channel not in _SUPPORTED:
        raise UsageError(
            f"Unknown notifier channel {channel!r}.",
            fix=f"Use one of: {', '.join(_SUPPORTED)}.",
        )
    return channel


def _secret_present(channel: str) -> bool:
    field = _SECRET_FIELD[channel]
    return bool(get_secret(f"quell/{channel}", field))


def _build_test_incident() -> Incident:
    now = datetime.now(UTC)
    return Incident(
        id="inc_test_notifier",
        signature="test" + "a" * 12,
        severity="high",
        status="resolved",
        first_seen=now,
        last_seen=now,
        occurrence_count=1,
        root_cause=(
            "Test notification from `quell notifier test`. If you received "
            "this in your channel, the webhook is correctly configured."
        ),
        fix_pr_url="https://github.com/bhartiyaanshul/quell/pull/0",
        postmortem=None,
        agent_graph_id=None,
    )


def _confirm_destructive(out: Output, *, message: str, yes: bool, hint: str) -> bool:
    if yes:
        return True
    if not is_interactive():
        raise UsageError(
            "destructive command — pass --yes to apply non-interactively.",
            fix=hint,
        )
    if not confirm(message, default=False):
        out.info("(no changes)")
        return False
    return True


def _validate_or_raise(raw: dict[str, Any], action: str) -> None:
    try:
        QuellConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(
            f"{action} would invalidate the config: {exc}",
            fix="quell config show   # confirm the existing shape",
        ) from exc


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def list_handler(out: Output, path: Path | None) -> None:
    config = load_config(local_dir=path, inject_secrets=False)
    rows: list[NotifierRow] = []
    for entry in config.notifiers:
        settings = entry.model_dump(mode="json")
        # Drop fields that are always empty in pure-TOML view.
        for field in ("webhook_url", "bot_token"):
            settings.pop(field, None)
        rows.append(
            NotifierRow(
                type=entry.type,
                settings=settings,
                secret_configured=_secret_present(entry.type),
            )
        )
    payload = NotifierListData(notifiers=rows)
    out.json("notifier.list", payload)
    if out.is_json or out.is_quiet:
        return
    if not rows:
        out.info("No notifiers configured.")
        return
    table_rows = [
        [
            r.type,
            "yes" if r.secret_configured else "no",
            ", ".join(f"{k}={v!r}" for k, v in r.settings.items() if k != "type"),
        ]
        for r in rows
    ]
    out.table(table_rows, headers=["TYPE", "SECRET", "SETTINGS"])


async def test_handler(out: Output, channel: str, path: Path | None) -> None:
    channel = _check_channel(channel)
    config = load_config(local_dir=path, inject_secrets=True)
    match = next((c for c in config.notifiers if c.type == channel), None)
    if match is None:
        raise NotFoundError(
            f"No {channel!r} notifier is configured.",
            fix=f"quell notifier add {channel}   # then `quell init` for the secret",
        )
    try:
        notifier = create_notifier(match)
    except NotifierError as exc:
        raise ConfigError(
            f"Notifier setup failed: {exc}",
            fix="quell init   # re-runs the keychain step",
        ) from exc

    if not (out.is_json or out.is_quiet):
        out.info(f"Sending test incident via {channel}...")
    await notifier.notify(_build_test_incident())
    payload = NotifierTestData(type=channel, sent=True)
    out.json("notifier.test", payload)
    if not (out.is_json or out.is_quiet):
        out.success(f"Sent. Check your {channel} channel.")


def add_handler(
    out: Output,
    channel: str,
    *,
    chat_id: str | None,
    path: Path | None,
    yes: bool,
    dry_run: bool,
) -> None:
    channel = _check_channel(channel)
    if channel == "telegram" and not chat_id:
        raise UsageError(
            "telegram notifier requires --chat-id.",
            fix="quell notifier add telegram --chat-id <id> --yes",
        )

    file_path = local_config_file(path)
    raw = read_local_toml(file_path) or {}
    existing = raw.get("notifiers") or []
    if any(isinstance(e, dict) and e.get("type") == channel for e in existing):
        raise AlreadyExistsError(
            f"A {channel!r} notifier is already configured.",
            fix=f"quell notifier remove {channel} --yes   # then re-add",
        )

    new_entry: dict[str, Any] = {"type": channel}
    if channel == "telegram" and chat_id is not None:
        new_entry["chat_id"] = chat_id
    raw["notifiers"] = [*existing, new_entry]
    _validate_or_raise(raw, action=f"Adding {channel} notifier")

    payload = NotifierAddData(
        type=channel,
        file=str(file_path),
        applied=not dry_run,
    )

    if dry_run:
        out.json("notifier.add", payload)
        if not (out.is_json or out.is_quiet):
            out.info(f"(dry-run) would add {channel} notifier to {file_path}")
        return

    if not _confirm_destructive(
        out,
        message=f"Add {channel} notifier to {file_path}?",
        yes=yes,
        hint=f"quell notifier add {channel} --yes",
    ):
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(toml_dumps(raw), encoding="utf-8")
    out.json("notifier.add", payload)
    if not (out.is_json or out.is_quiet):
        out.success(f"Added {channel} notifier.")
        if not _secret_present(channel):
            out.info(
                f"Secret for {channel!r} is not in the keychain — "
                "run `quell init` before testing."
            )


def remove_handler(
    out: Output,
    channel: str,
    *,
    path: Path | None,
    yes: bool,
    dry_run: bool,
) -> None:
    channel = _check_channel(channel)
    file_path = local_config_file(path)
    raw = read_local_toml(file_path) or {}
    existing = raw.get("notifiers") or []
    filtered = [
        e for e in existing if not (isinstance(e, dict) and e.get("type") == channel)
    ]
    removed = len(filtered) != len(existing)

    if not removed:
        # Idempotent — exit 0 with removed=False so scripts can drive this.
        payload = NotifierRemoveData(type=channel, file=str(file_path), removed=False)
        out.json("notifier.remove", payload)
        if not (out.is_json or out.is_quiet):
            out.info(f"No {channel!r} notifier configured; nothing to do.")
        return

    raw["notifiers"] = filtered
    _validate_or_raise(raw, action=f"Removing {channel} notifier")

    payload = NotifierRemoveData(type=channel, file=str(file_path), removed=not dry_run)

    if dry_run:
        out.json("notifier.remove", payload)
        if not (out.is_json or out.is_quiet):
            out.info(f"(dry-run) would remove {channel} notifier from {file_path}")
        return

    if not _confirm_destructive(
        out,
        message=f"Remove {channel} notifier from {file_path}?",
        yes=yes,
        hint=f"quell notifier remove {channel} --yes",
    ):
        return

    file_path.write_text(toml_dumps(raw), encoding="utf-8")
    out.json("notifier.remove", payload)
    if not (out.is_json or out.is_quiet):
        out.success(f"Removed {channel} notifier.")


__all__ = ["add_handler", "list_handler", "remove_handler", "test_handler"]
