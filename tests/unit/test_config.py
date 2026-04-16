"""Tests for quell.config — schema validation, path resolution, and loading."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from quell.config.loader import load_config
from quell.config.paths import (
    config_dir,
    data_dir,
    global_config_file,
    local_config_file,
)
from quell.config.schema import (
    DiscordNotifierConfig,
    HttpPollMonitorConfig,
    LLMConfig,
    LocalFileMonitorConfig,
    QuellConfig,
    SandboxConfig,
    SentryMonitorConfig,
    VercelMonitorConfig,
)
from quell.utils.errors import ConfigError

# ---------------------------------------------------------------------------
# Schema — valid configs
# ---------------------------------------------------------------------------


def test_default_quell_config() -> None:
    """QuellConfig builds with all defaults when given an empty dict."""
    cfg = QuellConfig.model_validate({})
    assert cfg.repo_path == "."
    assert cfg.monitors == []
    assert cfg.notifiers == []
    assert isinstance(cfg.llm, LLMConfig)
    assert isinstance(cfg.sandbox, SandboxConfig)


def test_local_file_monitor() -> None:
    """LocalFileMonitorConfig validates and defaults format to json."""
    raw = {"type": "local-file", "path": "/var/log/app.log"}
    cfg = LocalFileMonitorConfig.model_validate(raw)
    assert cfg.path == "/var/log/app.log"
    assert cfg.format == "json"
    assert cfg.pattern is None


def test_http_poll_monitor() -> None:
    """HttpPollMonitorConfig applies default interval and timeout."""
    raw = {"type": "http-poll", "url": "https://example.com/health"}
    cfg = HttpPollMonitorConfig.model_validate(raw)
    assert cfg.url == "https://example.com/health"
    assert cfg.interval_seconds == 30
    assert cfg.timeout_seconds == 10


def test_llm_config_defaults() -> None:
    """LLMConfig has sensible defaults and no api_key stored."""
    cfg = LLMConfig()
    assert "claude" in cfg.model
    assert cfg.api_key is None
    assert cfg.reasoning_effort == "medium"


def test_sandbox_config_defaults() -> None:
    """SandboxConfig and its nested ResourceLimitsConfig have correct defaults."""
    cfg = SandboxConfig()
    assert cfg.limits.memory_mb == 2048
    assert cfg.limits.cpus == 2.0
    assert cfg.idle_timeout_seconds == 600


def test_quell_config_with_monitors_and_notifiers() -> None:
    """QuellConfig parses discriminated unions for monitors and notifiers."""
    raw = {
        "repo_path": "/home/user/myapp",
        "monitors": [
            {"type": "local-file", "path": "/var/log/app.log"},
            {"type": "http-poll", "url": "https://api.example.com/health"},
            {"type": "vercel", "project_id": "prj_abc"},
            {"type": "sentry", "project_slug": "myapp", "organization_slug": "myorg"},
        ],
        "notifiers": [
            {"type": "discord", "webhook_url": "https://discord.com/api/webhooks/x"},
        ],
    }
    cfg = QuellConfig.model_validate(raw)
    assert len(cfg.monitors) == 4
    assert isinstance(cfg.monitors[0], LocalFileMonitorConfig)
    assert isinstance(cfg.monitors[1], HttpPollMonitorConfig)
    assert isinstance(cfg.monitors[2], VercelMonitorConfig)
    assert isinstance(cfg.monitors[3], SentryMonitorConfig)
    assert isinstance(cfg.notifiers[0], DiscordNotifierConfig)


# ---------------------------------------------------------------------------
# Schema — invalid configs
# ---------------------------------------------------------------------------


def test_invalid_monitor_type_raises() -> None:
    """Unknown monitor type raises ValidationError."""
    with pytest.raises(ValidationError):
        QuellConfig.model_validate(
            {"monitors": [{"type": "datadog", "api_key": "secret"}]}
        )


def test_missing_monitor_required_field_raises() -> None:
    """LocalFileMonitorConfig without 'path' raises ValidationError."""
    with pytest.raises(ValidationError):
        LocalFileMonitorConfig.model_validate({"type": "local-file"})


# ---------------------------------------------------------------------------
# Loader — TOML parsing
# ---------------------------------------------------------------------------


def test_load_config_empty_directory_returns_defaults() -> None:
    """load_config returns defaults when no config files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = load_config(local_dir=Path(tmpdir), inject_secrets=False)
    assert isinstance(cfg, QuellConfig)
    assert cfg.monitors == []


def test_load_config_local_toml_parsed() -> None:
    """load_config reads and validates a local .quell/config.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        quell_dir = Path(tmpdir) / ".quell"
        quell_dir.mkdir()
        config_file = quell_dir / "config.toml"
        config_file.write_text('[llm]\nmodel = "openai/gpt-4o"\n', encoding="utf-8")
        cfg = load_config(local_dir=Path(tmpdir), inject_secrets=False)
    assert cfg.llm.model == "openai/gpt-4o"


def test_load_config_invalid_toml_raises_config_error() -> None:
    """Malformed TOML raises ConfigError (not a raw tomllib error)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        quell_dir = Path(tmpdir) / ".quell"
        quell_dir.mkdir()
        (quell_dir / "config.toml").write_text("not = [valid toml", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(local_dir=Path(tmpdir), inject_secrets=False)


def test_load_config_global_overridden_by_local() -> None:
    """Local config values override global config values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch global config file to a temp location
        global_cfg = Path(tmpdir) / "global_config.toml"
        global_cfg.write_text('[llm]\nmodel = "openai/gpt-4o"\n', encoding="utf-8")
        local_dir = Path(tmpdir) / "project"
        local_dir.mkdir()
        local_quell = local_dir / ".quell"
        local_quell.mkdir()
        (local_quell / "config.toml").write_text(
            '[llm]\nmodel = "anthropic/claude-3-5-haiku-20241022"\n',
            encoding="utf-8",
        )
        with patch("quell.config.loader.global_config_file", return_value=global_cfg):
            cfg = load_config(local_dir=local_dir, inject_secrets=False)
    assert cfg.llm.model == "anthropic/claude-3-5-haiku-20241022"


# ---------------------------------------------------------------------------
# Keyring — mock round-trip
# ---------------------------------------------------------------------------


def test_keyring_secret_injected_into_llm_config() -> None:
    """API key from keyring is injected into LLMConfig at load time."""
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        patch("quell.config.loader.get_secret") as mock_get,
    ):
        mock_get.return_value = "sk-test-key-from-keyring"
        cfg = load_config(local_dir=Path(tmpdir), inject_secrets=True)
    assert cfg.llm.api_key == "sk-test-key-from-keyring"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def test_paths_return_path_objects() -> None:
    """Path helpers return Path instances with 'quell' in the name."""
    assert isinstance(config_dir(), Path)
    assert isinstance(data_dir(), Path)
    assert isinstance(global_config_file(), Path)
    assert isinstance(local_config_file(), Path)
    assert "quell" in str(config_dir()).lower()
