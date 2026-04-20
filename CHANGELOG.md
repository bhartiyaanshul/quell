# Changelog

All notable changes to Quell are documented here.  The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.1] — 2026-04-21

Patch release covering CI + packaging + documentation fixes that
landed after `v0.1.0` was tagged.  No breaking changes.

### Added

- **Landing page.** Next.js 14 + TailwindCSS + Framer Motion
  marketing site under `landing/`.  Dark-first palette, word-by-word
  hero reveal, live typing terminal demo, scroll-triggered pipeline
  animation, mouse-follow feature highlight, animated install tabs.
  Deploys as a static export to any host; dev server runs on
  `localhost:3000`.
- **README v2.** Hero banner SVG, `docs/media/flow-diagram.svg`,
  mermaid architecture + pipeline diagrams (GitHub-native), 2x2
  screenshot grid for the four main commands, tool + skill tables,
  FAQ section, GitHub-native `> [!NOTE]` alerts throughout.  No
  emojis — typography carries the visual hierarchy.

### Changed

- **Install section** is now stacked per-channel (curl / npm /
  Homebrew / pipx / binary) with fenced code blocks instead of an
  HTML table.  Long URLs no longer push the page into horizontal
  scroll.
- **CI pipelines** opt into the Node 24 runtime for JavaScript-based
  actions via the `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` env
  variable (Node 20 was deprecated in Sept 2025).  Bumped
  `actions/checkout@v4` to `@v5` across all three workflows.
- **Landing page port** defaults to `3000` (was 3737) to match the
  Next.js convention.

### Fixed

- **Terminal clipping** in the landing hero on narrow viewports — the
  body used a fixed `h-[320px] overflow-hidden` that cut off the last
  output line when text wrapped.  Now `min-h-[360px]` with no clip.
- **MetaMask dev overlay** popups ("Failed to connect to MetaMask")
  no longer interrupt the landing page.  A sync inline script in the
  layout `<head>` swallows errors originating from
  `chrome-extension://` URLs in the capture phase before Next's dev
  overlay sees them.
- **CI: ruff version drift.** Pinned `ruff = "~0.15.11"` so local
  and CI install the same formatter version and produce byte-identical
  output.  Previously `^0.6` meant CI resolved 0.6.x while local had
  0.15.
- **CI: Windows poetry not recognised.** `build-binaries.yml` now
  uses `python -m pip install .` instead of Poetry, avoiding the
  PowerShell PATH issue with `snok/install-poetry@v1`.
- **CI: macOS Intel runner starvation.** Dropped the `macos-13` x86_64
  build matrix entry (GitHub is draining those runners).  Ship arm64
  on `macos-latest` plus Linux x86_64 and Windows x86_64.
- **CI: binary smoke-test SIGPIPE.** The Unix smoke-test piped
  `quell --help` to `head -5` which triggered SIGPIPE under
  `set -eo pipefail`.  Dropped the pipe.
- **Windows UnicodeEncodeError on `quell --help`.** Rich couldn't
  encode the `→` arrow through `cp1252`.  Added UTF-8 reconfigure
  in `quell/__main__.py` and replaced stray arrows with ASCII `->`
  in CLI docstrings.

## [0.1.0] — 2026-04-20

### Added

- **Phase 7 — Agent system.** `BaseAgent` ABC, `AgentState` (Pydantic v2),
  `IncidentCommander` root agent, Jinja2 system-prompt template, the
  `agent_loop()` driver with configurable max-iterations and finish-tool
  detection.
- **Phase 8 — Skills system.** Markdown skill files with YAML
  frontmatter, loader + selector modules, seven bundled skills
  (stripe-webhook-timeout, unhandled-null, openai-rate-limit, fastapi,
  nextjs-app-router, postgres, redis).  `pyyaml` runtime dependency.
- **Phase 9 — Detector.** `compute_signature()`, `RollingBaseline`, and
  `Detector` turn `RawEvent` streams into `Incident` records via simple
  anomaly rules (new / spike / high-severity).
- **Phase 10 — Docker runtime.** `AbstractRuntime` protocol and
  `DockerRuntime` implementation for sandbox lifecycle (create, health,
  destroy) with a per-sandbox bearer token.  `docker` runtime dependency.
- **Phase 11 — Tool server.** FastAPI app that runs inside the sandbox:
  `GET /health`, `POST /register_agent`, `POST /execute`.  Executor now
  does real HTTP dispatch when a sandbox URL + token are present.
- **Phase 12 — Built-in tools.** Eleven tools across five families —
  `code_read`, `code_grep`, `git_log`, `git_blame`, `git_diff`,
  `logs_query`, `http_probe`, `create_incident_report`,
  `create_postmortem`, `agent_finish`, `finish_incident` — plus
  `register_builtin_tools()` for idempotent bootstrap.
- **Phase 13 — Agent graph.** `AgentGraph`, per-agent message queues,
  and four coordination tools (`create_agent`, `send_message`,
  `wait_for_message`, `view_graph`) that let the commander spawn
  subagents in parallel.
- **Phase 14 — End-to-end.** `quell watch` CLI command drives the full
  pipeline (monitor → detector → commander).  Bundled fixtures
  (`fixtures/sample_logs`, `fixtures/vulnerable_app`) and an e2e test
  (`tests/e2e/test_full_incident_flow.py`).
- **Phase 15 — Polish.** `quell history`, `quell show <id>`, `quell
  stats` commands.  GitHub Actions `release.yml` pipeline (tag → PyPI +
  GitHub release).  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, this changelog.

### Stop-gate

- `ruff check`, `ruff format --check`, and `mypy --strict` all clean.
- `pytest tests/ -q` green across unit + e2e suites.

Initial pre-alpha release covering Phases 1-15.  See the feature list
above for the full scope.  Phase 16 (public launch) is tracked
separately in `docs/LAUNCH.md`.
