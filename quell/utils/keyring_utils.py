"""OS keychain helpers for Quell secrets.

All secrets (API keys, webhook URLs, tokens) are stored in the OS keychain
via the ``keyring`` library — never in plaintext files and never logged.

Keychain layout
---------------
Each secret is stored under a *service* name and a *username*:

    service  = "quell/{provider}"   e.g. "quell/anthropic", "quell/discord"
    username = the field name       e.g. "api_key", "webhook_url", "bot_token"
"""

from __future__ import annotations

import keyring
import keyring.errors

_APP = "quell"


def get_secret(service: str, username: str) -> str | None:
    """Retrieve a secret from the OS keychain.

    Args:
        service:  Full service string (e.g. ``"quell/anthropic"``).
        username: Field name within the service (e.g. ``"api_key"``).

    Returns:
        The secret string, or ``None`` if not set.
    """
    try:
        return keyring.get_password(service, username)
    except keyring.errors.KeyringError:
        return None


def set_secret(service: str, username: str, value: str) -> None:
    """Store a secret in the OS keychain.

    Args:
        service:  Full service string.
        username: Field name within the service.
        value:    The secret to store.

    Raises:
        QuellError: If the keychain write fails.
    """
    from quell.utils.errors import ConfigError

    try:
        keyring.set_password(service, username, value)
    except keyring.errors.KeyringError as exc:
        raise ConfigError(f"Failed to store secret in keychain: {exc}") from exc


def delete_secret(service: str, username: str) -> None:
    """Delete a secret from the OS keychain (no-op if not set)."""
    try:
        keyring.delete_password(service, username)
    except keyring.errors.PasswordDeleteError:
        pass  # already absent — fine
    except keyring.errors.KeyringError:
        pass  # best-effort


def provider_service(provider: str) -> str:
    """Return the keychain service name for an LLM provider.

    Args:
        provider: Provider prefix (e.g. ``"anthropic"``, ``"openai"``).
    """
    return f"{_APP}/{provider}"


__all__ = ["get_secret", "set_secret", "delete_secret", "provider_service"]
