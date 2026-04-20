<div align="center">
  <img src="./landing/public/logo.svg" width="112" alt="Quell logo" />

  <h1 align="center">Quell</h1>

  <p align="center">
    <strong>Your production's autonomous on-call.</strong><br/>
    <em>Open-source multi-agent incident response. Draft the fix while you sleep.</em>
  </p>

  <p align="center">
    <a href="https://github.com/bhartiyaanshul/quell/releases/latest"><img src="https://img.shields.io/github/v/release/bhartiyaanshul/quell?color=fb923c&label=release&labelColor=0a0a0f" alt="Latest release"/></a>
    <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-a78bfa?labelColor=0a0a0f" alt="Apache 2.0"/></a>
    <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.12%2B-a78bfa?labelColor=0a0a0f" alt="Python 3.12+"/></a>
    <a href="https://github.com/bhartiyaanshul/quell/actions"><img src="https://img.shields.io/github/actions/workflow/status/bhartiyaanshul/quell/ci.yml?branch=main&label=CI&labelColor=0a0a0f&color=22c55e" alt="CI status"/></a>
    <img src="https://img.shields.io/badge/tests-242%20passing-22c55e?labelColor=0a0a0f" alt="242 tests passing"/>
  </p>

  <p align="center">
    <a href="https://quell.anshulbuilds.xyz"><strong>Website</strong></a> ·
    <a href="docs/getting-started.md"><strong>Getting started</strong></a> ·
    <a href="docs/commands.md"><strong>Commands</strong></a> ·
    <a href="docs/architecture.md"><strong>Architecture</strong></a> ·
    <a href="docs/extending.md"><strong>Extend</strong></a>
  </p>
</div>

---

## See it in action

<!-- The GIFs below are committed to `docs/media/`.  See docs/media/README.md
     for the capture recipe.  Until a real GIF lands the code-block
     storyboard directly underneath stays readable on GitHub. -->

<p align="center">
  <img src="./docs/media/hero-demo.gif" alt="Quell watching a log file, detecting an incident, and investigating it" width="720"/>
</p>

<details>
<summary><b>If the GIF hasn't loaded yet — here's a textual storyboard of the same run.</b></summary>

```console
$ quell watch
10:02:45  INFO  monitor: tailing /var/log/my-app/error.log
10:02:47  ERROR TypeError: Cannot read properties of null (reading 'id')
                  at processOrder (src/checkout.ts:42:18)
10:02:47  INFO  detector: new signature 7a9e42f8 — severity=high
10:02:47  INFO  commander: spawning incident_commander (5 skills matched)
10:02:49  INFO  tool: code_read src/checkout.ts lines 40-50
10:02:52  INFO  tool: git_blame src/checkout.ts:42
10:02:58  INFO  agent: finish_incident — null-deref on order.user
✓ incident inc_a1b2c3 resolved in 13s — see `quell show inc_a1b2c3`
```

</details>

---

## Install in one command

Pick whichever channel fits your environment — the end result is the same `quell` on your `PATH`.

```bash
# 1. curl — works today, zero prerequisites beyond Python 3.12 + git
curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash

# 2. npm — zero Python knowledge required (postinstall fetches a native binary)
npm i -g quell-agent

# 3. Homebrew (macOS / Linux)
brew install bhartiyaanshul/quell/quell

# 4. pipx (Python users)
pipx install quell-agent

# 5. Prebuilt binary — no runtime dependency at all
curl -sSL https://github.com/bhartiyaanshul/quell/releases/latest/download/quell-$(uname -s)-$(uname -m).tar.gz \
  | tar xz -C /usr/local/bin
```

> **Today** the curl installer works immediately; it probes for a prebuilt binary first and falls back to pipx + source if no release is published yet.  The other four channels go live the moment the first `v0.1.0` tag is pushed — `release.yml` and `build-binaries.yml` handle the rest.  Full status in [`packaging/README.md`](packaging/README.md).

## Quick start

<p align="center">
  <img src="./docs/media/quell-init.gif" alt="quell init interactive wizard walkthrough" width="680"/>
</p>

```bash
cd ~/src/my-app   # the project you want Quell to watch
quell init        # interactive wizard — stores API key in OS keychain
quell doctor      # verify Python, git, Docker, and your API key
quell watch       # start monitor → detector → agent loop
```

<p align="center">
  <img src="./docs/media/quell-doctor.png" alt="quell doctor output with every check green" width="640"/>
</p>

Inspect what Quell did after a run:

```bash
quell history              # recent incidents
quell show <incident-id>   # full detail on one
quell stats                # totals, MTTR, top signatures
```

<p align="center">
  <img src="./docs/media/quell-history.png" alt="quell history output" width="640"/>
</p>

Full walkthrough lives in [**docs/getting-started.md**](docs/getting-started.md).

## How it works

Four deliberate stages, one coherent watch loop.  No magic, no auto-merge.

```
┌──────────────┐   RawEvent   ┌───────────┐   Incident   ┌──────────────────┐   Tool calls   ┌──────────────────┐
│   Monitor    │ ───────────▶ │  Detector │ ───────────▶ │ IncidentCommander│ ─────────────▶ │  Docker sandbox  │
│  logs / http │              │ signature │              │  (BaseAgent +    │                │  FastAPI tool    │
│  vercel /    │              │  + rolling│              │   agent_loop)    │                │  server, your    │
│  sentry      │              │  baseline │              │                  │                │  repo mounted RO │
└──────────────┘              └───────────┘              └────────┬─────────┘                └────────┬─────────┘
                                                                  │                                   │
                                                                  │   LiteLLM                         │
                                                                  ▼                                   ▼
                                                            ┌──────────┐                       ┌──────────┐
                                                            │  OpenAI  │                       │  Reports │
                                                            │ Anthropic│                       │  (draft  │
                                                            │  Google  │                       │   PRs,   │
                                                            │  Ollama  │                       │   never  │
                                                            │   …any   │                       │  auto-   │
                                                            │  LiteLLM │                       │  merged) │
                                                            └──────────┘                       └──────────┘
```

Each box has its own page:

| Subsystem | Location | Docs |
|-----------|----------|------|
| Monitors | `quell/monitors/` | [configuration](docs/configuration.md#monitors--event-sources) |
| Detector | `quell/detector/` | [architecture](docs/architecture.md#detector--quelldetector) |
| Agents | `quell/agents/` | [architecture](docs/architecture.md#agents--quellagents) |
| Tools (11 built-ins) | `quell/tools/**` | [extending](docs/extending.md#writing-a-tool) |
| Skills (7 bundled runbooks) | `quell/skills/**` | [extending](docs/extending.md#writing-a-skill) |
| Sandbox | `quell/runtime/` + `quell/tool_server/` | [architecture](docs/architecture.md#runtime--quellruntime) |

## Features

- **Draft PRs only.**  Humans merge.  No silent changes.
- **Sandboxed by default.**  Every tool that touches code runs in Docker with your workspace mounted read-only, authenticated via a per-sandbox bearer token.
- **Bring your own model.**  LiteLLM under the hood — OpenAI, Anthropic, Google Gemini, Ollama, or any custom endpoint.  One line of TOML to switch.
- **Multi-agent.**  The `IncidentCommander` spawns specialist subagents (log analyst, code detective, git historian) that work in parallel through an `asyncio.Queue` message broker.
- **Skill runbooks.**  Markdown + YAML frontmatter runbooks get injected into the agent's prompt when their triggers match.  Seven come bundled.
- **No telemetry.**  Your code, your logs, your infrastructure — nothing leaves your machine unless you explicitly configure a remote endpoint.
- **Typed everywhere.**  Python 3.12+, `mypy --strict`, Pydantic v2, `ruff` clean.  242 tests.

## Documentation

| Guide | What it covers |
|-------|----------------|
| [**Getting started**](docs/getting-started.md) | First run — prerequisites, install, configure, watch. |
| [Installation](docs/installation.md) | All five install paths + fixing "command not found". |
| [Packaging](packaging/README.md) | How one tag push cascades into npm / brew / PyPI / binary releases. |
| [Commands](docs/commands.md) | CLI reference for every `quell` subcommand. |
| [Configuration](docs/configuration.md) | `.quell/config.toml` schema reference. |
| [Architecture](docs/architecture.md) | Subsystem-by-subsystem deep dive. |
| [Extending Quell](docs/extending.md) | Write a new skill or a new tool. |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and fixes. |

## Landing page

The marketing site at [**quell.anshulbuilds.xyz**](https://quell.anshulbuilds.xyz) is a Next.js + TailwindCSS + Framer Motion single-page app that lives under [`landing/`](landing/) in this repo.

```bash
cd landing
npm install
npm run dev      # http://localhost:3737 with hot reload
npm run build    # produces a static ./out/ directory
```

See [`landing/README.md`](landing/README.md) for the design system and component map.

## Development

```bash
# One-time editable install with dev deps
curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash -s -- --dev

# The stop-gate — all four must pass before merging
poetry run ruff format quell/ tests/ --check
poetry run ruff check  quell/ tests/
poetry run mypy        quell/
poetry run pytest      tests/ -q
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full dev loop and [`BUILD_PLAN.md`](BUILD_PLAN.md) for the 16-phase roadmap.

## Security

Found a vulnerability?  **Please don't file a public issue.**  Use the private [GitHub Security Advisory flow](https://github.com/bhartiyaanshul/quell/security/advisories/new) — details in [`SECURITY.md`](SECURITY.md).

## License

[Apache 2.0](./LICENSE) — built by [Anshul Bhartiya](https://x.com/Bhartiyaanshul).
