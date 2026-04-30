"""Interactive `quell init` setup wizard.

Uses Questionary for prompts. Writes non-secret config to
``.quell/config.toml`` and stores secrets in the OS keychain.
Never called directly — invoked via the ``init`` CLI command.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import questionary
import typer

from quell.interface.output import Output
from quell.interface.visuals import next_step, step_indicator, welcome_panel
from quell.utils.keyring_utils import set_secret
from quell.utils.toml_writer import dumps as toml_dumps

# ---------------------------------------------------------------------------
# Project detection helpers
# ---------------------------------------------------------------------------

_PROJECT_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "Python (Poetry / setuptools)"),
    ("requirements.txt", "Python (pip)"),
    ("package.json", "Node.js"),
    ("Gemfile", "Ruby"),
    ("go.mod", "Go"),
    ("Cargo.toml", "Rust"),
]

_LLM_PROVIDERS: list[dict[str, str]] = [
    {
        "name": "Anthropic (Claude)",
        "prefix": "anthropic",
        "model": "anthropic/claude-haiku-4-5",
    },
    {"name": "OpenAI (GPT-4o)", "prefix": "openai", "model": "openai/gpt-4o"},
    {"name": "Google (Gemini)", "prefix": "google", "model": "google/gemini-2.0-flash"},
    {"name": "Ollama (local)", "prefix": "ollama", "model": "ollama/llama3"},
    {"name": "Other (enter manually)", "prefix": "custom", "model": ""},
]


def _detect_project_type(path: Path) -> str:
    """Return a human-readable project type string based on files present."""
    for marker, label in _PROJECT_MARKERS:
        if (path / marker).exists():
            return label
    return "Unknown"


def _detect_git_remote(path: Path) -> str | None:
    """Return the first git remote URL, or None if not a git repo."""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "remote", "get-url", "origin"],  # noqa: S607
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _ensure_gitignore(path: Path) -> None:
    """Ensure .quell/ is listed in the project .gitignore."""
    gitignore = path / ".gitignore"
    entry = ".quell/\n"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".quell/" not in content and ".quell" not in content:
            with gitignore.open("a", encoding="utf-8") as fh:
                header = "\n# Quell local config (secrets stored in OS keychain)\n"
                fh.write(header + entry)
    else:
        gitignore.write_text(
            f"# Quell local config (secrets stored in OS keychain)\n{entry}",
            encoding="utf-8",
        )


def _write_config_toml(path: Path, data: dict[str, Any]) -> None:
    """Write *data* to ``<path>/.quell/config.toml`` as valid TOML."""
    quell_dir = path / ".quell"
    quell_dir.mkdir(exist_ok=True)
    config_file = quell_dir / "config.toml"
    rendered = toml_dumps(data, header="Quell configuration — managed by `quell init`")
    config_file.write_text(rendered, encoding="utf-8")


# ---------------------------------------------------------------------------
# Wizard entry point
# ---------------------------------------------------------------------------


def run_init(project_dir: Path | None = None) -> None:
    """Run the interactive Quell init wizard synchronously.

    Args:
        project_dir: Root of the project to configure. Defaults to cwd.
    """
    asyncio.run(_run_init_async(project_dir or Path.cwd()))


async def _run_init_async(project_dir: Path) -> None:
    """Async implementation of the init wizard."""
    out = Output()
    welcome_panel(
        out,
        title="Quell",
        body=(
            "an on-call engineer that never sleeps.\n\nSetup takes about 90 seconds."
        ),
    )

    # --- [1/5] Project summary ---
    project_type = _detect_project_type(project_dir)
    git_remote = _detect_git_remote(project_dir)

    step_indicator(out, 1, 5, f"Project type: {project_type}")
    out.key_value(
        [
            ("Git remote", git_remote or "(not detected)"),
            ("Directory", str(project_dir)),
        ]
    )
    out.line("")

    # --- [2/5] Monitor selection ---
    step_indicator(out, 2, 5, "Log source")
    monitor_type: str = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: questionary.select(
            "Which log source should Quell watch?",
            choices=[
                questionary.Choice(
                    "Local log file (tail a file on disk)", "local-file"
                ),
                questionary.Choice(
                    "HTTP endpoint polling (health check URL)", "http-poll"
                ),
                questionary.Choice("Vercel logs (requires Vercel CLI)", "vercel"),
                questionary.Choice("Sentry (poll Sentry API)", "sentry"),
            ],
        ).ask(),
    )

    if monitor_type is None:
        out.line("Init cancelled.")
        raise typer.Exit(0)

    monitor_config: dict[str, Any] = {"type": monitor_type}

    if monitor_type == "local-file":
        log_path: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.path(
                    "Path to the log file:",
                    default="/var/log/app.log",
                ).ask(),
            )
            or "/var/log/app.log"
        )
        monitor_config["path"] = log_path

    elif monitor_type == "http-poll":
        url: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text(
                    "Health check URL:",
                    default="https://your-app.com/health",
                ).ask(),
            )
            or "https://your-app.com/health"
        )
        monitor_config["url"] = url

    elif monitor_type == "vercel":
        project_id: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text("Vercel project ID (prj_...):").ask(),
            )
            or ""
        )
        monitor_config["project_id"] = project_id

    elif monitor_type == "sentry":
        org_slug: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text("Sentry organisation slug:").ask(),
            )
            or ""
        )
        proj_slug: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text("Sentry project slug:").ask(),
            )
            or ""
        )
        monitor_config["organization_slug"] = org_slug
        monitor_config["project_slug"] = proj_slug

    # --- [3/5] Notifier selection ---
    step_indicator(out, 3, 5, "Notifications")
    notifier_type: str = (
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "Where should Quell send incident notifications?",
                choices=[
                    questionary.Choice("Discord webhook", "discord"),
                    questionary.Choice("Slack incoming webhook", "slack"),
                    questionary.Choice("Telegram bot", "telegram"),
                    questionary.Choice("None — skip notifications", "none"),
                ],
            ).ask(),
        )
        or "none"
    )

    notifier_config: dict[str, Any] | None = None

    if notifier_type == "discord":
        webhook_url: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.password("Discord webhook URL:").ask(),
            )
            or ""
        )
        notifier_config = {"type": "discord"}
        set_secret("quell/discord", "webhook_url", webhook_url)
        out.success("Discord webhook stored in OS keychain.")

    elif notifier_type == "slack":
        webhook_url = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.password("Slack webhook URL:").ask(),
            )
            or ""
        )
        notifier_config = {"type": "slack"}
        set_secret("quell/slack", "webhook_url", webhook_url)
        out.success("Slack webhook stored in OS keychain.")

    elif notifier_type == "telegram":
        bot_token: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.password("Telegram bot token:").ask(),
            )
            or ""
        )
        chat_id: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text("Telegram chat ID:").ask(),
            )
            or ""
        )
        notifier_config = {"type": "telegram", "chat_id": chat_id}
        set_secret("quell/telegram", "bot_token", bot_token)
        out.success("Telegram bot token stored in OS keychain.")

    # --- [4/5] LLM provider ---
    step_indicator(out, 4, 5, "LLM provider")
    provider_names = [p["name"] for p in _LLM_PROVIDERS]
    chosen_provider_name: str = (
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.select(
                "Which LLM provider should Quell use?",
                choices=provider_names,
            ).ask(),
        )
        or provider_names[0]
    )

    provider_info = next(
        (p for p in _LLM_PROVIDERS if p["name"] == chosen_provider_name),
        _LLM_PROVIDERS[0],
    )
    model_string = provider_info["model"]

    if provider_info["prefix"] == "custom":
        model_string = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.text(
                    "Enter LiteLLM model string (e.g. anthropic/claude-haiku-4-5):"
                ).ask(),
            )
            or ""
        )

    if provider_info["prefix"] != "ollama":
        api_key: str = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: questionary.password(
                    f"API key for {chosen_provider_name} (stored in OS keychain):"
                ).ask(),
            )
            or ""
        )
        if api_key:
            set_secret(f"quell/{provider_info['prefix']}", "api_key", api_key)
            out.success(f"{chosen_provider_name} API key stored in OS keychain.")

    # --- [5/5] GitHub token (optional) ---
    step_indicator(out, 5, 5, "GitHub token (optional, for draft PRs)")
    github_token: str = (
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: questionary.password(
                "GitHub personal access token (for draft PRs — press Enter to skip):"
            ).ask(),
        )
        or ""
    )
    if github_token:
        set_secret("quell/github", "token", github_token)
        out.success("GitHub token stored in OS keychain.")

    # --- Build and write config ---
    config_data: dict[str, Any] = {
        "repo_path": str(project_dir),
        "llm": {"model": model_string},
        "monitors": [monitor_config],
    }
    if notifier_config is not None:
        config_data["notifiers"] = [notifier_config]

    _write_config_toml(project_dir, config_data)
    _ensure_gitignore(project_dir)

    out.line("")
    out.success(f"Config written to {project_dir / '.quell' / 'config.toml'}")
    out.success(".quell/ added to .gitignore")
    out.line("")
    next_step(out, "Verify your setup", command="quell doctor")
    out.line("")


__all__ = ["run_init"]
