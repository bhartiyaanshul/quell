"""JSON output envelopes for the Quell CLI.

Stable, schema-versioned shapes that ``--json`` output is wrapped in.
Per ``docs/cli-design.md`` §5.2: every JSON response is

    {"kind": "<resource>.<verb>", "version": "0.3", "data": <payload>}

Errors use a separate envelope routed to stderr; see ``ErrorEnvelope``.

Resource-specific ``data`` schemas live alongside their commands as
they migrate to the new output layer (Phase 3+) — defining them up
front would be speculative.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Schema version for the envelope itself. Bumped on backwards-incompatible
# changes to the envelope (not to individual ``data`` payloads).
ENVELOPE_VERSION: str = "0.3"


class ErrorEnvelope(BaseModel):
    """Envelope for ``--json`` mode error output (always to stderr).

    Pinned ``kind = "error.v1"`` so consumers can demultiplex stderr.
    """

    error: str
    fix_command: str | None = None
    exit_code: int = 1
    kind: Literal["error.v1"] = "error.v1"


def make_envelope(
    kind: str,
    data: object,
    *,
    version: str = ENVELOPE_VERSION,
) -> dict[str, object]:
    """Build a success envelope dict for ``--json`` output.

    Args:
        kind: ``<resource>.<verb>`` identifier (e.g. ``"incident.list"``).
        data: The payload — typically a Pydantic model dump or a list/dict.
        version: Schema version, defaults to the current envelope version.
    """
    return {"kind": kind, "version": version, "data": data}


__all__ = ["ENVELOPE_VERSION", "ErrorEnvelope", "make_envelope"]
