"""Event signature — a stable, 16-char hex fingerprint of an error event.

The signature collapses cosmetic variation (memory addresses, UUIDs,
timestamps, line numbers in frames) so that repeated occurrences of the
*same* underlying bug map to the same ``Incident`` row.
"""

from __future__ import annotations

import hashlib
import re

from quell.monitors.base import RawEvent

# Patterns that should be treated as equivalent across occurrences.
_MEMORY_ADDR_RE = re.compile(r"0x[0-9a-fA-F]{4,}")
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
_ISO_TS_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
_EPOCH_RE = re.compile(r"\b1[5-9]\d{8}\b")  # plausible unix epoch seconds
_NUMBER_RE = re.compile(r"\b\d{3,}\b")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Collapse cosmetic variation in *text* before hashing."""
    text = _MEMORY_ADDR_RE.sub("<addr>", text)
    text = _UUID_RE.sub("<uuid>", text)
    text = _ISO_TS_RE.sub("<ts>", text)
    text = _EPOCH_RE.sub("<epoch>", text)
    text = _NUMBER_RE.sub("<n>", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _first_content_line(text: str) -> str:
    """Return the first non-blank line of *text*, trimmed."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _error_type(text: str) -> str:
    """Best-effort extraction of the exception class name.

    Looks for patterns like ``TypeError:`` at the start of a line. Falls
    back to the first token of the first content line.
    """
    first = _first_content_line(text)
    # "TypeError: foo" -> "TypeError"
    if ":" in first:
        head = first.split(":", 1)[0].strip()
        if head and head.replace("_", "").isalnum():
            return head
    # Fall back to the first whitespace-delimited token.
    return first.split(None, 1)[0] if first else ""


def compute_signature(event: RawEvent) -> str:
    """Return a stable 16-char hex signature for *event*.

    Algorithm:

    1. Extract the error type (first token or ``ClassName`` before colon).
    2. Take the first non-blank line of the raw text.
    3. Normalise both (strip memory addresses, UUIDs, timestamps, numbers).
    4. SHA-256 the concatenation; return the first 16 hex chars.

    Signatures are intentionally coarse: two occurrences of the same bug
    must collide even if the stack trace addresses differ.
    """
    err = _normalise(_error_type(event.raw))
    first = _normalise(_first_content_line(event.raw))
    digest = hashlib.sha256(f"{err}|{first}".encode()).hexdigest()
    return digest[:16]


__all__ = ["compute_signature"]
