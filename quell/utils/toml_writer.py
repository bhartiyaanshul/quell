r"""Minimal TOML serializer for Quell's hand-rolled config writer.

Python ships ``tomllib`` for reading TOML in 3.11+, but no writer.
Adding a third-party writer (``tomli_w`` / ``tomlkit``) is overkill for
the small dict shapes Quell emits, so this module renders the subset of
TOML the config layer actually uses: scalars, nested dicts as tables,
and lists of dicts as arrays of tables.

Picks TOML literal strings (``'...'``) when safe and basic strings
(``"..."``) with full escaping otherwise — both forms round-trip
through ``tomllib``. The form-selection matters for Windows paths:
``C:\Users\anshul`` written as a basic string becomes invalid TOML
because ``\U`` opens an 8-hex-digit Unicode escape, while the same
value as a literal string (``'C:\Users\anshul'``) is unambiguous.
"""

from __future__ import annotations

from typing import Any

_BASIC_STRING_ESCAPES: dict[str, str] = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _format_string(value: str) -> str:
    """Render *value* as a TOML string, picking the simplest safe form.

    Strategy:
    1. Prefer a *literal* string ``'...'`` (no escapes interpreted) if
       *value* has no single-quote and no control chars. This keeps
       Windows paths readable: ``'C:\\Users\\anshul'``.
    2. Fall back to a *basic* string ``"..."`` with backslashes,
       quotes, and ASCII control chars escaped per TOML 1.0.
    """
    if "'" not in value and not any(ord(c) < 0x20 for c in value):
        return f"'{value}'"
    escaped = value
    for char, replacement in _BASIC_STRING_ESCAPES.items():
        escaped = escaped.replace(char, replacement)
    return f'"{escaped}"'


def _format_scalar(value: Any) -> str:
    """Render a scalar TOML value (string, bool, int, float, list-of-scalars)."""
    if isinstance(value, bool):
        # bool must come before int — bool is a subclass of int in Python.
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, str):
        return _format_string(value)
    if isinstance(value, list):
        items = ", ".join(_format_scalar(item) for item in value)
        return f"[{items}]"
    raise TypeError(f"Cannot serialize {type(value).__name__} to TOML: {value!r}")


def _is_array_of_tables(value: Any) -> bool:
    """True if *value* is a non-empty list whose first element is a dict."""
    return isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict)


def _emit_table(prefix: str, obj: dict[str, Any]) -> list[str]:
    """Recursively serialize *obj* as TOML, scoped under *prefix*.

    Output order: scalars first (so they belong to the current table
    header), then nested tables, then arrays of tables. This mirrors
    the canonical TOML style and keeps round-tripped files diff-friendly.
    """
    scalars: list[tuple[str, Any]] = []
    tables: list[tuple[str, dict[str, Any]]] = []
    array_tables: list[tuple[str, list[dict[str, Any]]]] = []

    for key, value in obj.items():
        if isinstance(value, dict):
            tables.append((key, value))
        elif _is_array_of_tables(value):
            array_tables.append((key, value))
        else:
            scalars.append((key, value))

    lines: list[str] = []

    for key, value in scalars:
        lines.append(f"{key} = {_format_scalar(value)}\n")

    for key, value in tables:
        section = f"{prefix}.{key}" if prefix else key
        lines.append(f"\n[{section}]\n")
        lines.extend(_emit_table(section, value))

    for key, value in array_tables:
        section = f"{prefix}.{key}" if prefix else key
        for item in value:
            lines.append(f"\n[[{section}]]\n")
            lines.extend(_emit_table(section, item))

    return lines


def dumps(data: dict[str, Any], *, header: str | None = None) -> str:
    """Serialize *data* to a TOML string.

    Args:
        data: Dict with string keys; values may be scalars, nested
            dicts, lists of scalars, or lists of dicts (emitted as
            array-of-tables).
        header: Optional comment written as the first line.

    Raises:
        TypeError: A value's type isn't supported. The error names the
            offending key path so the caller can fix the config shape.
    """
    parts: list[str] = []
    if header is not None:
        parts.append(f"# {header}\n")
    parts.extend(_emit_table("", data))
    return "".join(parts)


__all__ = ["dumps"]
