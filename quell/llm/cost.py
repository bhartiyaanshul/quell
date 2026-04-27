"""LLM cost estimation.

Each major LLM provider publishes its rates as $ / million tokens,
separately for input and output.  :func:`estimate_cost` looks up the
rate for a given model string and returns an estimate in USD.

Unknown models cost zero — conservative, so budget checks never
trigger just because we don't have a rate card for a new model.
The lookup is forgiving: ``"anthropic/claude-haiku-4-5"`` and
``"claude-haiku-4-5"`` both match.
"""

from __future__ import annotations

# (input_usd_per_mtok, output_usd_per_mtok).  Source: each provider's
# public pricing page as of v0.2.  Update as needed.
MODEL_RATES: dict[str, tuple[float, float]] = {
    # Anthropic
    "anthropic/claude-haiku-4-5": (0.80, 4.00),
    "anthropic/claude-sonnet-4-5": (3.00, 15.00),
    "anthropic/claude-opus-4-5": (15.00, 75.00),
    # OpenAI
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-5": (10.00, 30.00),
    "openai/gpt-5-mini": (0.50, 2.00),
    # Google
    "google/gemini-2.0-flash": (0.10, 0.40),
    "google/gemini-2.0-pro": (1.25, 5.00),
    # Ollama + any local runtime is free.
    "ollama/default": (0.0, 0.0),
}


def _normalise(model: str) -> str:
    """Lower-case + keep the provider/slug shape as-is."""
    return model.strip().lower()


def _lookup(model: str) -> tuple[float, float] | None:
    """Return ``(input_rate, output_rate)`` or ``None`` if unknown."""
    key = _normalise(model)
    if key in MODEL_RATES:
        return MODEL_RATES[key]
    # Fall back to provider-free match: strip "<provider>/" prefix.
    if "/" in key:
        bare = key.split("/", 1)[1]
        for known, rates in MODEL_RATES.items():
            if known.endswith("/" + bare):
                return rates
    # Ollama / local: always free.
    if key.startswith("ollama/"):
        return (0.0, 0.0)
    return None


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return an estimated USD cost for one LLM call.

    Args:
        model:         LiteLLM-style model string
                       (e.g. ``"anthropic/claude-haiku-4-5"``).
        input_tokens:  Token count for the prompt (from the provider response).
        output_tokens: Token count for the completion.

    Returns:
        Cost estimate in USD.  Zero when the model has no registered rate.
    """
    rates = _lookup(model)
    if rates is None:
        return 0.0
    input_rate, output_rate = rates
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


def has_rate_card(model: str) -> bool:
    """Return ``True`` when we have pricing data for *model*."""
    return _lookup(model) is not None


__all__ = ["MODEL_RATES", "estimate_cost", "has_rate_card"]
