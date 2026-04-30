"""Handlers for ``quell config <verb>``.

Phase 3.2 of the v0.3.0 redesign (see ``docs/cli-design.md`` §3.2 + §14).
The Typer commands in ``config_cmd.py`` are thin shims that build an
``Output`` from universal flags and call the matching handler here.

Secrets (``llm.api_key`` and notifier webhooks/tokens) live in the OS
keychain rather than the TOML file — ``show`` redacts them in output
and ``set`` refuses to write them, directing the user to ``quell init``
instead of letting them leak into ``config.toml``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer
from pydantic import BaseModel, ValidationError

from quell.config.loader import load_config
from quell.config.paths import local_config_file
from quell.config.schema import QuellConfig
from quell.interface.config_helpers import (
    coerce_value,
    get_dotted,
    read_local_toml,
    redact,
    resolve_field_type,
    set_in_dict,
)
from quell.interface.config_schemas import (
    ConfigGetData,
    ConfigSetData,
    ConfigShowData,
    ConfigValidateData,
)
from quell.interface.errors import ConfigError, UsageError, handle_cli_error
from quell.interface.output import Output
from quell.interface.prompts import confirm, is_interactive
from quell.utils.errors import ConfigError as RuntimeConfigError
from quell.utils.toml_writer import dumps as toml_dumps

# Dotted keys we refuse to ``set`` because they live in the keychain.
_SECRET_KEYS: frozenset[str] = frozenset({"llm.api_key"})


def show_handler(out: Output, path: Path | None) -> None:
    config = load_config(local_dir=path, inject_secrets=False)
    file_path = local_config_file(path)
    payload = ConfigShowData(config=redact(config), file=str(file_path))
    out.json("config.show", payload)
    if out.is_json or out.is_quiet:
        return
    out.header(f"Config (from {file_path})")
    out.line(toml_dumps(payload.config))


def get_handler(out: Output, key: str, path: Path | None) -> None:
    config = load_config(local_dir=path, inject_secrets=False)
    value = get_dotted(config, key)
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    payload = ConfigGetData(key=key, value=value)
    out.json("config.get", payload)
    if out.is_json or out.is_quiet:
        return
    out.line(str(value))


def set_handler(
    out: Output,
    key: str,
    value: str,
    *,
    path: Path | None,
    yes: bool,
    dry_run: bool,
) -> None:
    if key in _SECRET_KEYS:
        raise UsageError(
            f"Refusing to write {key!r} to TOML — it's stored in the OS keychain.",
            fix="quell init   # re-runs the keychain step",
        )

    annotation = resolve_field_type(QuellConfig, key)
    new_value = coerce_value(value, annotation)

    config_before = load_config(local_dir=path, inject_secrets=False)
    old_value = get_dotted(config_before, key)
    if isinstance(old_value, BaseModel):
        old_value = old_value.model_dump(mode="json")

    file_path = local_config_file(path)
    raw = read_local_toml(file_path)
    set_in_dict(raw, key, new_value)

    # Refuse to write a file that wouldn't reload cleanly.
    try:
        QuellConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(
            f"Setting {key}={new_value!r} would invalidate the config: {exc}",
            fix="quell config show   # confirm the existing shape",
        ) from exc

    payload = ConfigSetData(
        key=key,
        old_value=old_value,
        new_value=new_value,
        file=str(file_path),
        applied=not dry_run,
    )

    if dry_run:
        out.json("config.set", payload)
        if not (out.is_json or out.is_quiet):
            out.info(f"(dry-run) would set {key} = {new_value!r} in {file_path}")
        return

    if not yes:
        if not is_interactive():
            raise UsageError(
                "`config set` is destructive — pass --yes to apply non-interactively.",
                fix=f"quell config set {key} {value} --yes",
            )
        if not confirm(f"Set {key} = {new_value!r} in {file_path}?", default=False):
            out.info("(no changes)")
            return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(toml_dumps(raw), encoding="utf-8")
    out.json("config.set", payload)
    if not (out.is_json or out.is_quiet):
        out.success(f"Set {key} = {new_value!r}")


def validate_handler(out: Output, path: Path | None) -> None:
    file_path = local_config_file(path)
    errors: list[str] = []
    try:
        load_config(local_dir=path, inject_secrets=False)
    except RuntimeConfigError as exc:
        # ``load_config`` raises ``quell.utils.errors.ConfigError`` —
        # the runtime-layer cousin of our CLI ``ConfigError`` — so it
        # has to be caught explicitly here.
        errors.append(str(exc))
    valid = not errors
    payload = ConfigValidateData(valid=valid, errors=errors, file=str(file_path))
    out.json("config.validate", payload)
    if valid:
        if not (out.is_json or out.is_quiet):
            out.success(f"{file_path} is valid.")
        return

    code = handle_cli_error(ConfigError(errors[0]), out)
    raise typer.Exit(code=code)


def edit_handler(out: Output, path: Path | None) -> None:
    if out.is_json:
        raise UsageError(
            "`config edit` is interactive and cannot run in --json mode.",
            fix="quell config set <key> <value> --yes   # for non-interactive edits",
        )
    file_path = local_config_file(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        # ``$EDITOR`` may refuse to open a missing file — write a stub.
        file_path.write_text("", encoding="utf-8")

    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    result = subprocess.run([editor, str(file_path)], check=False)  # noqa: S603
    if result.returncode != 0:
        out.warn("editor exited non-zero — leaving file unchanged.")
        return

    try:
        load_config(local_dir=path, inject_secrets=False)
    except RuntimeConfigError as exc:
        raise ConfigError(
            f"After edit, {file_path} is invalid: {exc}",
            fix=f"$EDITOR {file_path}   # fix the syntax",
        ) from exc
    out.success(f"Saved {file_path}")


__all__ = [
    "edit_handler",
    "get_handler",
    "set_handler",
    "show_handler",
    "validate_handler",
]
