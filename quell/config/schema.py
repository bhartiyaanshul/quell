"""Pydantic v2 configuration models for Quell.

Every field maps directly to a TOML key. Secrets (api_key, webhook URLs) are
never stored in TOML; they are fetched from the OS keychain at load time and
injected into the models by `quell.config.loader`.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Monitor adapters
# ---------------------------------------------------------------------------


class LocalFileMonitorConfig(BaseModel):
    """Tail a local log file and emit events from each new line."""

    type: Literal["local-file"]
    path: str
    format: Literal["json", "regex"] = "json"
    pattern: str | None = None  # required when format == "regex"


class HttpPollMonitorConfig(BaseModel):
    """Poll an HTTP endpoint; fire an event on non-2xx or timeout."""

    type: Literal["http-poll"]
    url: str
    interval_seconds: int = 30
    timeout_seconds: int = 10
    expected_status: int = 200


class VercelMonitorConfig(BaseModel):
    """Stream logs from a Vercel deployment via the Vercel CLI."""

    type: Literal["vercel"]
    project_id: str
    interval_seconds: int = 60


class SentryMonitorConfig(BaseModel):
    """Poll the Sentry API for new issues."""

    type: Literal["sentry"]
    project_slug: str
    organization_slug: str
    interval_seconds: int = 60


MonitorConfig = Annotated[
    LocalFileMonitorConfig
    | HttpPollMonitorConfig
    | VercelMonitorConfig
    | SentryMonitorConfig,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Notifier channels
# ---------------------------------------------------------------------------


class DiscordNotifierConfig(BaseModel):
    """Send rich embeds to a Discord webhook."""

    type: Literal["discord"]
    webhook_url: str = ""  # injected from keyring at load time


class SlackNotifierConfig(BaseModel):
    """Send block messages to a Slack incoming webhook."""

    type: Literal["slack"]
    webhook_url: str = ""  # injected from keyring at load time


class TelegramNotifierConfig(BaseModel):
    """Send messages via a Telegram bot."""

    type: Literal["telegram"]
    chat_id: str
    bot_token: str = ""  # injected from keyring at load time


NotifierConfig = Annotated[
    DiscordNotifierConfig | SlackNotifierConfig | TelegramNotifierConfig,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# LLM provider
# ---------------------------------------------------------------------------


class LLMConfig(BaseModel):
    """LiteLLM model selection and connection settings."""

    model: str = "anthropic/claude-haiku-4-5"
    api_base: str | None = None  # for Ollama, LM Studio, etc.
    reasoning_effort: Literal["low", "medium", "high"] = "medium"
    max_context_tokens: int = 100_000
    # Populated from OS keychain at load time; never stored in TOML.
    api_key: str | None = None


# ---------------------------------------------------------------------------
# Docker sandbox
# ---------------------------------------------------------------------------


class ResourceLimitsConfig(BaseModel):
    """Resource limits applied to each sandbox container."""

    memory_mb: int = 2048
    cpus: float = 2.0
    disk_gb: int = 10


class SandboxConfig(BaseModel):
    """Docker sandbox image and resource configuration."""

    image: str = "ghcr.io/bhartiyaanshul/quell-sandbox:latest"
    limits: ResourceLimitsConfig = Field(default_factory=ResourceLimitsConfig)
    network_whitelist: list[str] = Field(default_factory=list)
    idle_timeout_seconds: int = 600


# ---------------------------------------------------------------------------
# Top-level config
# ---------------------------------------------------------------------------


class SkillsConfig(BaseModel):
    """User-managed skill state.

    ``disabled`` slugs are filtered out before ``select_applicable`` runs
    in the watch loop, so disabling a skill removes it from auto-pickup
    without deleting the runbook file.
    """

    disabled: list[str] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Runtime limits for every agent_loop invocation.

    These apply uniformly to the root :class:`~quell.agents.IncidentCommander`
    and any subagents it spawns (Phase 13).
    """

    max_iterations: int = 50
    """Hard stop on the number of tool-executing turns per agent."""

    max_cost_usd: float | None = None
    """Optional per-investigation budget in USD.  When the running cost
    estimate exceeds this value the loop transitions to ``FAILED`` with
    a ``"budget exceeded"`` error.  ``None`` disables the cap."""


class QuellConfig(BaseModel):
    """Root configuration object, loaded from .quell/config.toml."""

    repo_path: str = "."
    monitors: list[MonitorConfig] = Field(default_factory=list)
    notifiers: list[NotifierConfig] = Field(default_factory=list)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)


__all__ = [
    "QuellConfig",
    "MonitorConfig",
    "NotifierConfig",
    "LocalFileMonitorConfig",
    "HttpPollMonitorConfig",
    "VercelMonitorConfig",
    "SentryMonitorConfig",
    "DiscordNotifierConfig",
    "SlackNotifierConfig",
    "TelegramNotifierConfig",
    "LLMConfig",
    "AgentConfig",
    "SandboxConfig",
    "ResourceLimitsConfig",
    "SkillsConfig",
]
