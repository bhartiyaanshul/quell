# Quell

> **Your production's autonomous on-call.**

[![Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

Quell watches your production logs, investigates incidents via
LLM-backed agents running in a Docker sandbox, and produces a
structured report (root cause, evidence, proposed fix) for a human to
review — all while you sleep.

The root `IncidentCommander` reasons via **LiteLLM** (pick any model),
spawns specialist subagents through an agent graph, and coordinates
them with a message broker.  Every proposed fix is a draft PR; Quell
never auto-merges.

---

## Install — pick your package

```bash
# 1. npm — zero Python knowledge required
npm i -g quell-agent

# 2. Homebrew tap (macOS / Linux)
brew install bhartiyaanshul/quell/quell

# 3. One-shot curl installer (any POSIX shell)
curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash

# 4. pipx (Python users)
pipx install quell-agent

# 5. Standalone binary (no runtime dep)
curl -sSL https://github.com/bhartiyaanshul/quell/releases/latest/download/quell-$(uname -s)-$(uname -m).tar.gz \
  | tar xz -C /usr/local/bin
```

All five channels are wired.  **Today** only the curl installer runs
out of the box — it probes for the prebuilt binary first, falls back
to a pipx install from source when no release exists yet.  The other
four channels go live the moment the first `v0.1.0` tag is pushed:
`release.yml` publishes to PyPI, `build-binaries.yml` uploads the
four platform archives, and the npm wrapper + Homebrew formula
reference those releases.  Details in
[`packaging/README.md`](packaging/README.md).

Regardless of channel, the result is the same: `quell` on your `PATH`.
See [docs/installation.md](docs/installation.md) for venv / editable
dev installs and troubleshooting.

## Quick start

```bash
cd ~/src/my-app   # the project you want Quell to watch
quell init        # interactive wizard — stores API key in OS keychain
quell doctor      # verify Python, git, Docker, and your API key
quell watch       # start monitor → detector → agent loop
```

Inspect what Quell did:

```bash
quell history              # recent incidents
quell show <incident-id>   # full detail on one
quell stats                # totals, MTTR, top signatures
```

Full walkthrough in [**docs/getting-started.md**](docs/getting-started.md).

## Documentation

| Guide | What it covers |
|-------|----------------|
| [Getting started](docs/getting-started.md) | First run — install, configure, watch. |
| [Installation](docs/installation.md) | All five install paths + fixing "command not found". |
| [Packaging](packaging/README.md) | How one tag push cascades into npm / brew / PyPI / binary releases. |
| [Commands](docs/commands.md) | CLI reference for every subcommand. |
| [Configuration](docs/configuration.md) | `.quell/config.toml` reference. |
| [Architecture](docs/architecture.md) | How monitors, detector, agents, tools, sandbox fit together. |
| [Extending Quell](docs/extending.md) | Add a skill (markdown runbook) or a tool. |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and fixes. |

## Architecture

```
┌─────────────┐   RawEvent   ┌──────────┐   Incident   ┌──────────────────┐
│  Monitors   │ ───────────▶ │ Detector │ ───────────▶ │ IncidentCommander│
│ local-file  │              │ signature│              │  (BaseAgent)     │
│ http-poll   │              │ +        │              │                  │
│ vercel      │              │ baseline │              │  ┌────────────┐  │
│ sentry      │              └──────────┘              │  │ agent_loop │  │
└─────────────┘                                        │  └─────┬──────┘  │
                                                       │        │         │
                                                       │  ┌─────┴──────┐  │
                                                       │  │    LLM     │  │
                                                       │  │ (LiteLLM)  │  │
                                                       │  └─────┬──────┘  │
                                                       │        │         │
                                                       │  ┌─────┴──────┐  │
                                                       │  │ Tool calls │  │
                                                       │  └─────┬──────┘  │
                                                       └────────┼─────────┘
                                                                │
                                                                ▼
                                                       ┌──────────────────┐
                                                       │  Docker sandbox  │
                                                       │  FastAPI tool    │
                                                       │  server, tools   │
                                                       │  run read-only   │
                                                       │  in your repo    │
                                                       └──────────────────┘
```

## Principles

- **Draft PRs only.** Humans merge.
- **Sandboxed.** Every tool that touches code runs in a Docker
  container with the workspace mounted read-only.
- **Bring your own model.** LiteLLM — OpenAI, Anthropic, Ollama, or
  anything else.  No lock-in.
- **No telemetry by default.** Opt-in only.

## Development

```bash
# One-time editable install with dev deps
curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash -s -- --dev

# The usual stop-gate — all four must pass before merging
poetry run ruff format quell/ tests/ --check
poetry run ruff check  quell/ tests/
poetry run mypy        quell/
poetry run pytest      tests/ -q
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full dev loop.

## License

[Apache 2.0](./LICENSE) — built by
[Anshul Bhartiya](https://x.com/Bhartiyaanshul).
