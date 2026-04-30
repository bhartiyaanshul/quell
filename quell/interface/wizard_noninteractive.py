"""Non-interactive ``quell init`` (Phase 3.6 — flag-first).

Runs without prompts when the user passes ``--yes`` and (optionally)
the structural flags (``--monitor``, ``--log-path``, ``--llm-provider``,
…). Defaults fill in the gaps so ``quell init --yes`` alone produces a
minimal-but-valid config: local-file monitor at ``/var/log/app.log``,
no notifier, ``anthropic/claude-haiku-4-5`` as the LLM model.

Secrets are not prompted for — the user passes them via environment
variables (``QUELL_<PROVIDER>_API_KEY``,
``QUELL_<NOTIFIER>_WEBHOOK_URL``, ``QUELL_TELEGRAM_BOT_TOKEN``,
``QUELL_GITHUB_TOKEN``). Anything missing is reported as a warning so
the user knows what to set; the structural config still gets written
so subsequent invocations of ``quell init`` (interactive) only need to
fill in the keychain step.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from quell.interface.errors import UsageError
from quell.interface.output import Output
from quell.interface.wizard import ensure_gitignore, write_config_toml
from quell.utils.keyring_utils import set_secret

_SUPPORTED_MONITORS: tuple[str, ...] = (
    "local-file",
    "http-poll",
    "vercel",
    "sentry",
)
_SUPPORTED_NOTIFIERS: tuple[str, ...] = ("discord", "slack", "telegram", "none")
_PROVIDER_TO_DEFAULT_MODEL: dict[str, str] = {
    "anthropic": "anthropic/claude-haiku-4-5",
    "openai": "openai/gpt-4o",
    "google": "google/gemini-2.0-flash",
    "ollama": "ollama/llama3",
}


def _build_monitor(
    monitor: str,
    *,
    log_path: str | None,
    http_url: str | None,
    vercel_project_id: str | None,
    sentry_org: str | None,
    sentry_project: str | None,
) -> dict[str, Any]:
    if monitor == "local-file":
        return {"type": "local-file", "path": log_path or "/var/log/app.log"}
    if monitor == "http-poll":
        if not http_url:
            raise UsageError(
                "--http-url is required for --monitor http-poll.",
                fix="quell init --yes --monitor http-poll --http-url https://...",
            )
        return {"type": "http-poll", "url": http_url}
    if monitor == "vercel":
        if not vercel_project_id:
            raise UsageError(
                "--vercel-project-id is required for --monitor vercel.",
                fix="quell init --yes --monitor vercel --vercel-project-id prj_...",
            )
        return {"type": "vercel", "project_id": vercel_project_id}
    if monitor == "sentry":
        if not (sentry_org and sentry_project):
            raise UsageError(
                "--sentry-org and --sentry-project are required for --monitor sentry.",
                fix=(
                    "quell init --yes --monitor sentry "
                    "--sentry-org <slug> --sentry-project <slug>"
                ),
            )
        return {
            "type": "sentry",
            "organization_slug": sentry_org,
            "project_slug": sentry_project,
        }
    raise UsageError(
        f"Unknown monitor type {monitor!r}.",
        fix=f"Use one of: {', '.join(_SUPPORTED_MONITORS)}.",
    )


def _build_notifier(
    notifier: str,
    *,
    telegram_chat_id: str | None,
) -> dict[str, Any] | None:
    if notifier == "none":
        return None
    if notifier in ("discord", "slack"):
        return {"type": notifier}
    if notifier == "telegram":
        if not telegram_chat_id:
            raise UsageError(
                "--telegram-chat-id is required for --notifier telegram.",
                fix=("quell init --yes --notifier telegram --telegram-chat-id <id>"),
            )
        return {"type": "telegram", "chat_id": telegram_chat_id}
    raise UsageError(
        f"Unknown notifier {notifier!r}.",
        fix=f"Use one of: {', '.join(_SUPPORTED_NOTIFIERS)}.",
    )


def _store_env_secrets(
    out: Output,
    *,
    llm_provider: str,
    notifier_type: str | None,
) -> list[str]:
    """Read QUELL_* env vars and persist matching secrets to the keychain.

    Returns a list of human-readable warnings about missing secrets,
    so ``run_noninteractive_init`` can surface them in the final report.
    """
    missing: list[str] = []

    api_env = f"QUELL_{llm_provider.upper()}_API_KEY"
    api_key = os.environ.get(api_env)
    if api_key:
        set_secret(f"quell/{llm_provider}", "api_key", api_key)
        out.success(f"Stored {llm_provider} API key from ${api_env}.")
    elif llm_provider != "ollama":
        missing.append(f"set ${api_env} or run `quell init` interactively")

    if notifier_type in ("discord", "slack"):
        env = f"QUELL_{notifier_type.upper()}_WEBHOOK_URL"
        url = os.environ.get(env)
        if url:
            set_secret(f"quell/{notifier_type}", "webhook_url", url)
            out.success(f"Stored {notifier_type} webhook from ${env}.")
        else:
            missing.append(f"set ${env}")
    elif notifier_type == "telegram":
        token = os.environ.get("QUELL_TELEGRAM_BOT_TOKEN")
        if token:
            set_secret("quell/telegram", "bot_token", token)
            out.success("Stored Telegram bot token from $QUELL_TELEGRAM_BOT_TOKEN.")
        else:
            missing.append("set $QUELL_TELEGRAM_BOT_TOKEN")

    github_token = os.environ.get("QUELL_GITHUB_TOKEN")
    if github_token:
        set_secret("quell/github", "token", github_token)
        out.success("Stored GitHub token from $QUELL_GITHUB_TOKEN.")

    return missing


def run_noninteractive_init(
    project_dir: Path,
    *,
    out: Output,
    monitor: str,
    log_path: str | None,
    http_url: str | None,
    vercel_project_id: str | None,
    sentry_org: str | None,
    sentry_project: str | None,
    notifier: str,
    telegram_chat_id: str | None,
    llm_provider: str,
    llm_model: str | None,
) -> None:
    """Build a config from flags + env vars and write it to ``.quell/config.toml``.

    Designed for ``quell init --yes`` and CI / agent flows. Validates
    flag combinations up front; raises ``UsageError`` (exit 2) on any
    missing or invalid combination so scripts get a clean error.
    """
    if monitor not in _SUPPORTED_MONITORS:
        raise UsageError(
            f"Unknown monitor {monitor!r}.",
            fix=f"Use one of: {', '.join(_SUPPORTED_MONITORS)}.",
        )
    if notifier not in _SUPPORTED_NOTIFIERS:
        raise UsageError(
            f"Unknown notifier {notifier!r}.",
            fix=f"Use one of: {', '.join(_SUPPORTED_NOTIFIERS)}.",
        )
    if llm_provider not in _PROVIDER_TO_DEFAULT_MODEL:
        raise UsageError(
            f"Unknown llm provider {llm_provider!r}.",
            fix=f"Use one of: {', '.join(_PROVIDER_TO_DEFAULT_MODEL)}.",
        )

    monitor_cfg = _build_monitor(
        monitor,
        log_path=log_path,
        http_url=http_url,
        vercel_project_id=vercel_project_id,
        sentry_org=sentry_org,
        sentry_project=sentry_project,
    )
    notifier_cfg = _build_notifier(notifier, telegram_chat_id=telegram_chat_id)

    model = llm_model or _PROVIDER_TO_DEFAULT_MODEL[llm_provider]

    config_data: dict[str, Any] = {
        "repo_path": str(project_dir),
        "llm": {"model": model},
        "monitors": [monitor_cfg],
    }
    if notifier_cfg is not None:
        config_data["notifiers"] = [notifier_cfg]

    write_config_toml(project_dir, config_data)
    ensure_gitignore(project_dir)

    missing_secrets = _store_env_secrets(
        out, llm_provider=llm_provider, notifier_type=notifier
    )

    config_file = project_dir / ".quell" / "config.toml"
    out.success(f"Config written to {config_file}")
    if missing_secrets:
        out.warn("Some secrets are not yet stored in the keychain:")
        for hint in missing_secrets:
            out.line(f"  • {hint}")


__all__ = ["run_noninteractive_init"]
