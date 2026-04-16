"""Argument type-coercion and validation for Quell tools.

The XML parser always produces string values for every parameter.
:func:`coerce_arguments` converts those strings to the types declared in
:class:`~quell.llm.types.ToolParameterSpec` and returns a list of
human-readable error strings for any validation failures.

This keeps the executor clean — it just calls :func:`coerce_arguments` and
forwards the typed dict to the tool function.
"""

from __future__ import annotations

from collections.abc import Callable

from quell.llm.types import ToolMetadata

# Supported coercion targets (subset of JSON Schema primitive types).
_COERCIONS: dict[str, Callable[[str], object]] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "number": float,  # alias
}

_TRUE_VALUES: frozenset[str] = frozenset({"true", "1", "yes", "on"})
_FALSE_VALUES: frozenset[str] = frozenset({"false", "0", "no", "off"})


def _coerce_value(raw: str, target_type: str) -> object:
    """Convert *raw* string to *target_type*.

    Raises:
        ValueError: If coercion fails.
    """
    if target_type == "boolean":
        lower = raw.strip().lower()
        if lower in _TRUE_VALUES:
            return True
        if lower in _FALSE_VALUES:
            return False
        raise ValueError(f"Cannot coerce {raw!r} to boolean")

    if target_type in ("integer",):
        # Support "3.0" → 3 gracefully.
        return int(float(raw))

    python_type = _COERCIONS.get(target_type, str)
    return python_type(raw)


def coerce_arguments(
    raw: dict[str, str],
    metadata: ToolMetadata,
) -> tuple[dict[str, object], list[str]]:
    """Validate and coerce *raw* string arguments against *metadata*.

    Args:
        raw:      String-valued dict from the XML parser.
        metadata: Tool metadata declaring expected parameters.

    Returns:
        A 2-tuple of ``(coerced_dict, errors)``.  If ``errors`` is non-empty
        the coerced dict is partial and should not be used.
    """
    errors: list[str] = []
    coerced: dict[str, object] = {}

    for spec in metadata.parameters:
        if spec.name not in raw:
            if spec.required:
                errors.append(f"Missing required parameter: {spec.name!r}")
            continue

        raw_value = raw[spec.name]
        try:
            coerced[spec.name] = _coerce_value(raw_value, spec.type)
        except (ValueError, TypeError) as exc:
            errors.append(
                f"Parameter {spec.name!r}: cannot coerce {raw_value!r} "
                f"to {spec.type!r} — {exc}"
            )

    # Pass through any extra parameters not declared in the spec as strings.
    declared_names = {s.name for s in metadata.parameters}
    for k, v in raw.items():
        if k not in declared_names:
            coerced[k] = v

    return coerced, errors


__all__ = ["coerce_arguments"]
