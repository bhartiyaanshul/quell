"""XML tool-call parser for Quell's LLM layer.

LLMs emit tool invocations in this XML format (following the Strix pattern):

    <function=tool_name>
    <parameter=key>value</parameter>
    </function>

Two alternate spellings are also accepted for model compatibility:

    <invoke name="tool_name">
      <parameter name="key">value</parameter>
    </invoke>

The parser is intentionally permissive: it extracts as much as it can from
partial or malformed XML rather than failing hard.  This is the correct
tradeoff for streaming LLM output — a regex approach that degrades gracefully
beats a strict XML parser that errors on truncated tags.
"""

from __future__ import annotations

import re

from quell.llm.types import ToolInvocation

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Primary format:  <function=name> ... </function>
_FUNC_BLOCK = re.compile(
    r"<function=(?P<name>\w+)>\s*(?P<body>.*?)\s*</function>",
    re.DOTALL | re.IGNORECASE,
)

# Alternate format:  <invoke name="name"> ... </invoke>
_INVOKE_BLOCK = re.compile(
    r'<invoke\s+name=["\'](?P<name>[\w.-]+)["\']>\s*(?P<body>.*?)\s*</invoke>',
    re.DOTALL | re.IGNORECASE,
)

# Primary parameter:  <parameter=key>value</parameter>
_PARAM_PRIMARY = re.compile(
    r"<parameter=(?P<key>\w+)>\s*(?P<value>.*?)\s*</parameter>",
    re.DOTALL | re.IGNORECASE,
)

# Alternate parameter:  <parameter name="key">value</parameter>
_PARAM_ALTERNATE = re.compile(
    r'<parameter\s+name=["\'](?P<key>[\w.-]+)["\']>\s*(?P<value>.*?)\s*</parameter>',
    re.DOTALL | re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_tool_invocations(text: str) -> list[ToolInvocation]:
    """Extract all tool invocations from *text*.

    Searches for both ``<function=name>`` and ``<invoke name="name">``
    blocks and returns them in document order.

    Args:
        text: Raw LLM assistant turn content.

    Returns:
        Possibly-empty list of :class:`~quell.llm.types.ToolInvocation`.
    """
    results: list[ToolInvocation] = []

    for m in _FUNC_BLOCK.finditer(text):
        name = m.group("name")
        body = m.group("body")
        params = _extract_parameters(body)
        results.append(ToolInvocation(name=name, parameters=params, raw_xml=m.group(0)))

    for m in _INVOKE_BLOCK.finditer(text):
        name = m.group("name")
        body = m.group("body")
        params = _extract_parameters(body)
        results.append(ToolInvocation(name=name, parameters=params, raw_xml=m.group(0)))

    # Sort by position in the original text so invocations come out in order
    # even when both formats are mixed.
    results.sort(key=lambda inv: text.index(inv.raw_xml))
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_parameters(body: str) -> dict[str, str]:
    """Extract all ``<parameter=key>value</parameter>`` pairs from *body*."""
    params: dict[str, str] = {}
    for m in _PARAM_PRIMARY.finditer(body):
        params[m.group("key")] = m.group("value")
    for m in _PARAM_ALTERNATE.finditer(body):
        params.setdefault(m.group("key"), m.group("value"))
    return params


__all__ = ["parse_tool_invocations"]
