"""Message history compressor for the Quell LLM layer.

When a conversation grows long enough to risk hitting a model's context
window, ``compress_messages`` trims the middle of the history while
preserving:

1. The system prompt (always kept verbatim — position 0).
2. The most recent ``keep_last`` messages (always kept verbatim).
3. A single synthetic "context summary" message injected just after the
   system prompt that summarises the dropped messages in plain text.

This is a *token-free* heuristic approach: it counts characters rather than
tokens to avoid a heavyweight tiktoken/transformers dependency in the core
library.  The rough conversion factor used is 4 chars ≈ 1 token.

The compressor never touches the system message or the recent tail, and it
never reduces the list below ``keep_last + 1`` messages.
"""

from __future__ import annotations

from quell.llm.types import LLMMessage

# Approximate chars-per-token ratio (GPT-4 / Claude family).
_CHARS_PER_TOKEN: int = 4

# Default thresholds.
_DEFAULT_MAX_TOKENS: int = 80_000  # compress when > 80 % of a 100 k window
_DEFAULT_KEEP_LAST: int = 10  # always keep the N most recent messages
_DEFAULT_SUMMARY_BATCH: int = 20  # summarise this many messages at a time


def _estimate_tokens(messages: list[LLMMessage]) -> int:
    """Rough token count estimate for a list of messages."""
    total_chars = sum(len(m.content) for m in messages)
    return total_chars // _CHARS_PER_TOKEN


def _summarise_batch(messages: list[LLMMessage]) -> str:
    """Produce a compact plain-text summary of a batch of messages.

    This is a *structural* summary — it records which roles spoke and
    the first 120 characters of each turn.  A real production version
    would call an LLM summariser; for now a deterministic stub is
    sufficient and keeps the compressor testable without network access.
    """
    lines: list[str] = ["[Compressed conversation history]"]
    for msg in messages:
        snippet = msg.content[:120].replace("\n", " ")
        if len(msg.content) > 120:
            snippet += "…"
        lines.append(f"  [{msg.role}]: {snippet}")
    return "\n".join(lines)


def compress_messages(
    messages: list[LLMMessage],
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    keep_last: int = _DEFAULT_KEEP_LAST,
    summary_batch: int = _DEFAULT_SUMMARY_BATCH,
) -> list[LLMMessage]:
    """Return a (possibly compressed) copy of *messages*.

    If the estimated token count of *messages* is below *max_tokens*, the
    list is returned unchanged.  Otherwise messages in the "middle" range
    are replaced with a single summary message.

    Args:
        messages:     Full conversation history including the system prompt.
        max_tokens:   Compression threshold in (estimated) tokens.
        keep_last:    How many recent messages to always preserve verbatim.
        summary_batch: How many messages per summary chunk (informational
                        for future batched-summary implementations).

    Returns:
        A new list (never mutates the input).
    """
    if _estimate_tokens(messages) <= max_tokens:
        return list(messages)

    if len(messages) <= keep_last + 1:
        # Nothing to compress — already at minimum useful size.
        return list(messages)

    # Split into: system | compressible middle | recent tail
    system_msgs = [m for m in messages[:1] if m.role == "system"]
    tail = messages[-keep_last:]

    # The middle is everything after the system prompt, before the tail.
    start = len(system_msgs)
    end = len(messages) - keep_last
    middle = messages[start:end]

    if not middle:
        return list(messages)

    summary_content = _summarise_batch(middle)
    summary_msg = LLMMessage(role="user", content=summary_content)

    return [*system_msgs, summary_msg, *tail]


__all__ = ["compress_messages"]
