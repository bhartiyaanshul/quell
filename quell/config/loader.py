"""TOML config loader with keyring secret injection.

Load order (later values win):
  1. Built-in Pydantic defaults
  2. Global config  (~/.config/quell/config.toml)
  3. Local config   (.quell/config.toml in the current directory)

Secrets (API keys, webhook URLs) are never stored in TOML files. The loader
fetches them from the OS keychain via `quell.utils.keyring_utils` after the
TOML is parsed and injects them into the config models.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from quell.config.paths import global_config_file, local_config_file
from quell.config.schema import (
    DiscordNotifierConfig,
    QuellConfig,
    SlackNotifierConfig,
    TelegramNotifierConfig,
)
from quell.utils.errors import ConfigError
from quell.utils.keyring_utils import get_secret


def _load_toml(path: Path) -> dict[str, Any]:
    """Read a TOML file and return its contents as a dict.

    Returns an empty dict if the file does not exist.
    """
    if not path.exists():
        return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _inject_secrets(cfg: QuellConfig) -> QuellConfig:
    """Fetch secrets from the OS keychain and inject them into *cfg*.

    Each secret is looked up by a well-known service name. Missing keys are
    silently ignored (the user hasn't run `quell init` yet).
    """
    # LLM API key — service name derived from the model provider prefix
    provider = cfg.llm.model.split("/")[0] if "/" in cfg.llm.model else "openai"
    api_key = get_secret(f"quell/{provider}", "api_key")
    if api_key:
        new_llm = cfg.llm.model_copy(update={"api_key": api_key})
        cfg = cfg.model_copy(update={"llm": new_llm})

    # Notifier secrets
    injected_notifiers = []
    for notifier in cfg.notifiers:
        if isinstance(notifier, DiscordNotifierConfig) and not notifier.webhook_url:
            url = get_secret("quell/discord", "webhook_url") or ""
            notifier = notifier.model_copy(update={"webhook_url": url})
        elif isinstance(notifier, SlackNotifierConfig) and not notifier.webhook_url:
            url = get_secret("quell/slack", "webhook_url") or ""
            notifier = notifier.model_copy(update={"webhook_url": url})
        elif isinstance(notifier, TelegramNotifierConfig) and not notifier.bot_token:
            token = get_secret("quell/telegram", "bot_token") or ""
            notifier = notifier.model_copy(update={"bot_token": token})
        injected_notifiers.append(notifier)

    return cfg.model_copy(update={"notifiers": injected_notifiers})


def load_config(
    local_dir: Path | None = None,
    inject_secrets: bool = True,
) -> QuellConfig:
    """Load and return the merged Quell configuration.

    Args:
        local_dir:       Directory to search for ``.quell/config.toml``.
                         Defaults to ``Path.cwd()``.
        inject_secrets:  If True, fetch secrets from the OS keychain.
                         Set to False in tests.

    Returns:
        A fully-validated :class:`QuellConfig` instance.

    Raises:
        ConfigError: If a TOML file exists but cannot be parsed or fails
                     Pydantic validation.
    """
    global_raw = _load_toml(global_config_file())
    local_raw = _load_toml(local_config_file(local_dir))
    merged = _deep_merge(global_raw, local_raw)

    try:
        cfg = QuellConfig.model_validate(merged)
    except Exception as exc:
        raise ConfigError(f"Config validation failed: {exc}") from exc

    if inject_secrets:
        cfg = _inject_secrets(cfg)

    return cfg


__all__ = ["load_config"]
