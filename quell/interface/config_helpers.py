"""Dotted-key helpers for ``quell config <verb>``.

Split from ``config_handlers`` so each module stays under the project's
300-line cap. These helpers traverse a Pydantic model by a dotted path
(``llm.model``) and coerce CLI strings into the type the schema expects
— useful for ``config get`` and ``config set`` and reusable from any
future command that wants the same shape.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel

from quell.interface.errors import ConfigError, NotFoundError, UsageError


def redact(model: BaseModel) -> dict[str, Any]:
    """Return ``model.model_dump`` with secrets replaced and ``None`` dropped.

    TOML has no ``null`` literal, so leaving ``None``-valued keys would
    crash the TOML writer when ``config show`` renders the result.
    Dropping them is equivalent to "key not set" in TOML semantics.
    """
    data = model.model_dump(mode="json")
    if isinstance(data.get("llm"), dict) and data["llm"].get("api_key"):
        data["llm"]["api_key"] = "***"
    for entry in data.get("notifiers") or []:
        if not isinstance(entry, dict):
            continue
        for field in ("webhook_url", "bot_token"):
            if entry.get(field):
                entry[field] = "***"
    cleaned = _drop_nones(data)
    assert isinstance(cleaned, dict)  # noqa: S101 — guard for the type narrowing
    return cleaned


def _drop_nones(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, dict):
        return {k: _drop_nones(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_nones(item) for item in value]
    return value


def get_dotted(model: BaseModel, key: str) -> Any:  # noqa: ANN401
    """Walk *model* by dotted *key*. Raises ``NotFoundError`` on missing path."""
    parts = key.split(".")
    current: Any = model
    for part in parts:
        if not isinstance(current, BaseModel):
            raise NotFoundError(
                f"Cannot traverse into {key!r} (intermediate is not a section).",
                fix="quell config show   # see available keys",
            )
        if part not in type(current).model_fields:
            raise NotFoundError(
                f"No config key {key!r}.",
                fix="quell config show   # see available keys",
            )
        current = getattr(current, part)
    return current


def resolve_field_type(model: type[BaseModel], key: str) -> Any:  # noqa: ANN401
    """Return the type annotation of the field at the dotted *key* path."""
    parts = key.split(".")
    current_type: Any = model
    for index, part in enumerate(parts):
        if not (isinstance(current_type, type) and issubclass(current_type, BaseModel)):
            traversed = ".".join(parts[:index]) or "<root>"
            raise NotFoundError(
                f"Cannot set into {key!r} — {traversed} is not a config section.",
                fix="quell config show   # see settable keys",
            )
        if part not in current_type.model_fields:
            raise NotFoundError(
                f"No config key {key!r}.",
                fix="quell config show   # see available keys",
            )
        current_type = current_type.model_fields[part].annotation
    return current_type


def coerce_value(value: str, annotation: Any) -> Any:  # noqa: ANN401
    """Coerce a CLI string to the type *annotation* expects.

    Supports the scalar types used by ``QuellConfig``: ``str`` / ``int``
    / ``float`` / ``bool`` / ``Literal[...]`` / ``X | None``. Lists and
    nested models are refused — those go through resource subcommands.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, UnionType):
        if value.lower() in {"null", "none", ""} and type(None) in args:
            return None
        for candidate in (a for a in args if a is not type(None)):
            try:
                return coerce_value(value, candidate)
            except (ValueError, UsageError):
                continue
        raise UsageError(
            f"Could not parse {value!r} for field type {annotation}.",
            fix="See `quell config show` for the current value's shape.",
        )

    if origin is Literal:
        if value in args:
            return value
        choices = ", ".join(repr(a) for a in args)
        raise UsageError(
            f"Value {value!r} is not one of {choices}.",
            fix=f"Re-run with one of {choices}.",
        )

    if annotation is bool:
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
        raise UsageError(
            f"Could not parse {value!r} as a boolean.",
            fix="Use one of: true / false / yes / no / 1 / 0.",
        )
    if annotation is int:
        try:
            return int(value)
        except ValueError as exc:
            raise UsageError(f"Could not parse {value!r} as an integer.") from exc
    if annotation is float:
        try:
            return float(value)
        except ValueError as exc:
            raise UsageError(f"Could not parse {value!r} as a float.") from exc
    if annotation is str:
        return value

    raise UsageError(
        f"Cannot set {annotation!r}-typed fields from the command line.",
        fix="Use `quell init` or `quell notifier add` for structured fields.",
    )


def set_in_dict(data: dict[str, Any], key: str, value: Any) -> None:  # noqa: ANN401
    """Set *value* at the dotted *key* path, creating tables as needed."""
    parts = key.split(".")
    current: dict[str, Any] = data
    for part in parts[:-1]:
        nested = current.get(part)
        if not isinstance(nested, dict):
            nested = {}
            current[part] = nested
        current = nested
    current[parts[-1]] = value


def read_local_toml(file_path: Path) -> dict[str, Any]:
    """Read *file_path* as TOML, or return ``{}`` if it doesn't exist."""
    if not file_path.exists():
        return {}
    try:
        with file_path.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            f"Invalid TOML in {file_path}: {exc}",
            fix="quell config validate   # then fix the file",
        ) from exc


__all__ = [
    "coerce_value",
    "get_dotted",
    "read_local_toml",
    "redact",
    "resolve_field_type",
    "set_in_dict",
]
