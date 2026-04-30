# Changelog

All notable changes to Quell are documented here.  The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.3.0] — 2026-05-01

Theme: **agent-friendly CLI**. The 0.2 flat-verb surface (`quell history`,
`quell show`, `quell stats`, `quell test-notifier`) is replaced by the
v0.3 `resource verb` grammar: every command is now discoverable from
`--help` alone, every command speaks `--json` for tool integration, and
exit codes carry meaning. Old commands keep working as deprecated aliases
that emit a one-line stderr warning — they will be removed in 0.4.0.

See [`docs/migrating-to-0.3.md`](docs/migrating-to-0.3.md) for the full
upgrade path.

### Breaking changes

- **Exit codes are now stable + meaningful** (see `docs/cli-design.md` §6).
  `0` success, `2` usage error, `3` config error, `4` external service,
  `5` sandbox, `6` auth, `7` not-found, `8` already-exists. Scripts that
  checked `exit_code != 0` keep working; scripts that grep for exact
  codes need updating. Most notably, `quell incident show <missing-id>`
  now exits `7` (was `1`).
- **`quell history`, `quell show <id>`, `quell stats`, `quell replay <id>`,
  `quell test-notifier <channel>`** still run but print
  `[deprecation] '<old>' is deprecated; use '<new>' instead. (will be
  removed in v0.4.0)` to stderr. Migrate to the resource-verb form to
  silence the warning.

### Added — v0.3 command surface

- **`quell incident list / show / stats / replay`** — replaces the four
  v0.2 top-level history/show/stats/replay verbs. `list` accepts
  `--status`, `--severity`, `--since "1 week ago"`, `--limit`. Emits
  `incident.list` / `incident.show` / `incident.stats` /
  `incident.replay` JSON envelopes under `--json`.
- **`quell config show / get / set / validate / edit`** — read & mutate
  `.quell/config.toml` with type-checked dotted keys. `set` is
  destructive — requires `--yes` or interactive confirmation, supports
  `--dry-run`. Refuses to write `llm.api_key` (lives in the keychain).
  `edit` opens `$EDITOR` and revalidates on save.
- **`quell skill list / show / enable / disable`** — list bundled
  runbooks and toggle whether the watch loop auto-loads each. Disabled
  state persists in `.quell/config.toml` under `[skills] disabled`.
- **`quell notifier list / test / add / remove`** — manage notifier
  entries in `.quell/config.toml`. `add` and `remove` are destructive
  (`--yes` / `--dry-run`); `add` of an already-configured channel
  exits `8` (`AlreadyExists`); `remove` is idempotent (exits `0` with
  `removed=false` when there's nothing to do).
- **`quell explain <command>`** — long-form, agent-friendly docs for
  any command or sub-app. Lists every flag with type and default,
  inlines the `Examples:` block, closes with the universal flag set.
- **`quell --help-json`** — emits the full Click introspection tree as
  a `help.tree` JSON envelope. Designed for editor plugins and agents.

### Added — universal flag set

Every command (resource verbs and global verbs) now accepts:

- `--json` — machine-readable output. Disables animations, colors,
  prompts. Errors → stderr as `error.v1` JSON.
- `--quiet` / `-q` — suppress non-error output (exit code is the signal).
- `--no-color` — disable ANSI colors. Auto-on under `NO_COLOR=1` or
  non-TTY.
- `--yes` / `-y` — skip confirmation prompts on destructive verbs.
- `--dry-run` — preview without writing on destructive verbs.
- `--path PATH` — project directory to operate on (defaults to cwd).

Plus a new env var: **`QUELL_NO_ANIM=1`** disables spinners + progress
bars regardless of TTY state.

### Added — `quell init --yes`

Non-interactive init for CI / agents:

```bash
quell init --yes --monitor local-file --log-path /var/log/app.log \
                 --llm-provider anthropic
```

Reads `$QUELL_<PROVIDER>_API_KEY` / `$QUELL_<NOTIFIER>_WEBHOOK_URL` /
`$QUELL_TELEGRAM_BOT_TOKEN` / `$QUELL_GITHUB_TOKEN` for secrets and
persists them to the OS keychain. The structural part of the config is
written either way; missing secrets surface as a final warning.

### Added — `quell doctor` improvements

- **`--json`** emits a `doctor.run` envelope with a stable
  `{name, status, detail}` per check plus aggregate `passed` / `failed`
  counts.
- **`--quiet`** suppresses the table; the exit code is the signal
  (`quell doctor --quiet || exit 1`).
- **`Single install` check** flags multiple `quell` binaries on PATH
  with the corrective `pip uninstall -y quell` baked into the detail
  string.
- **`PyPI freshness` check** hits `pypi.org/pypi/quell/json` and
  suggests `pipx upgrade quell` when outdated. Network errors and
  unparseable versions both pass — `doctor` doesn't go red because
  PyPI was slow.
- **Per-check progress bar** during `quell doctor` in interactive
  mode (Quell-orange braille pulse spinner, advances per
  `asyncio.wait` completion). Silenced under `--json` / `--quiet` /
  non-TTY / `QUELL_NO_ANIM`.

### Added — visual polish

- **Quell-branded spinner shape** registered with Rich (12-frame
  braille pulse, accent orange).
- **Progress bar API** (`quell.interface.progress.progress`) for
  known-length operations — Rich bar under animation, single trailing
  summary line otherwise.
- **First-run welcome panel** (`quell init` shows a rounded panel
  with the brand line on first run).

### Added — `quell --version` shows binary path

`quell --version` and `quell version` both print
`quell <ver> (<binary path>)`. Resolves through symlinks so pipx /
brew shims show the real underlying binary — diagnoses
multiple-install confusion in one command.

### Added — auto-generated CLI reference

`scripts/gen_commands_md.py` walks the live Typer app and emits
`docs/commands.md`. The committed doc is verified in-tree by a pytest
test (`test_committed_doc_is_in_sync_with_generator`) so docstring +
flag drift is caught before review.

### Changed

- Errors raised by every Quell-CLI command are subclasses of
  `QuellCLIError` and ship with a `fix=` corrective action — the
  fix is rendered as a "Fix:" block in human mode and as
  `fix_command` in `--json` mode.
- `quell` invoked with no arguments now shows a small resource list
  + four common commands (instead of the verbose Typer dump).
- `docs/cli-design.md` is the binding spec for the new CLI surface.

### Removed

- The `_` prefix on `_ensure_gitignore` / `_write_config_toml` in
  `quell.interface.wizard` — promoted to public API
  (`ensure_gitignore` / `write_config_toml`) so the non-interactive
  init can reuse them.

## [0.2.1] — 2026-04-30

Patch release. Fixes a `quell init` regression on Windows.

### Fixed

- **`quell init` wrote invalid TOML on Windows.** The wizard's
  hand-rolled config writer emitted strings unescaped, so a Windows
  `repo_path` like `C:\Users\you` produced `repo_path = "C:\Users\you"`
  — TOML reads `\U` as the start of an 8-hex-digit Unicode escape and
  rejected the file with `Invalid hex value`. The same writer also
  stringified `[[monitors]]`/`[[notifiers]]` lists via Python's
  `repr` instead of TOML's array-of-tables syntax. The serializer
  has been extracted into `quell/utils/toml_writer.py`, picks TOML
  literal strings (`'...'`) when safe and basic strings with full
  escaping otherwise, and emits arrays-of-tables correctly. Round-trip
  tests through `tomllib` cover the regression.
- If you hit this bug on 0.2.0, re-run `quell init` after upgrading
  to overwrite the broken file (or delete `.quell/config.toml`
  manually first).

## [0.2.0] — 2026-04-23

Theme: **observability + integration**.  You can now *see* what Quell
did (dashboard + replay), *tell your team* (notifiers), *know what it
cost* (cost tracking + budgets), and *match more incident types*
(expanded skill library).

No breaking changes to `BaseAgent` / `AgentState` / `QuellConfig` /
the sandbox protocol.  v0.1.x configs keep working untouched.

### Added

- **Phase 17 — Notifiers.** `quell/notifiers/` with a `Notifier`
  ABC and three concrete implementations: Slack (rich blocks via
  incoming webhook), Discord (coloured embed via incoming webhook),
  Telegram (Bot API `sendMessage` with MarkdownV2).  `quell
  test-notifier <channel>` fires a synthetic incident end-to-end.
  The `quell watch` loop fans out to every configured notifier in
  parallel once an investigation completes; any transient network
  failure on one channel no longer blocks the others.
- **Phase 18 — 12 new skill runbooks.** Five new incident skills
  (`dns-resolution-failure`, `ssl-certificate-expired`,
  `memory-leak`, `disk-full`, `database-deadlock`), five new
  framework skills (`django`, `flask`, `spring-boot`, `rails`,
  `express`), and two new technology skills (`kubernetes`,
  `docker`).  Bundled library is now **19 skills**.
- **Phase 19 — Event persistence.** New `quell.memory.agent_runs`,
  `quell.memory.events`, and `quell.memory.findings` CRUD modules.
  The agent loop now writes one `AgentRun` row per investigation
  plus `Event` rows for every LLM call, tool call, and error, and
  `Finding` rows for structured evidence — all behind an optional
  `session_factory` constructor argument so tests without
  persistence still work.
- **Phase 20 — Cost tracking + budget enforcement.** New
  `quell.llm.cost` module with a per-model rate card (Anthropic,
  OpenAI, Google, Ollama).  `AgentState` tracks running token +
  cost totals; the return dict now includes `input_tokens`,
  `output_tokens`, and `cost_usd`.  New `AgentConfig.max_cost_usd`
  halts investigations when they exceed the budget.
  `Incident.cost_usd` accumulates across every run for the incident.
- **Phase 21 — Web dashboard.** A read-only local dashboard
  launched with `quell dashboard`.  Next.js 14 SPA (static-exported,
  bundled in the wheel) served by a small FastAPI backend with
  four routers:
  - `GET /api/incidents` / `/api/incidents/{id}`
  - `GET /api/runs/{run_id}/events`
  - `GET /api/stats`
  - `GET /api/incidents/{id}/replay`

  Pages: incident list with filters, incident detail with run
  metrics and findings, replay timeline, aggregate stats.  Design
  system matches the landing site (ember + violet on deep indigo).
- **Phase 22 — Investigation replay.** `quell replay <incident_id>`
  renders the full event stream for every agent run as a terminal
  timeline — costs, latencies, tool calls, errors.  The dashboard
  shows the same data interactively.

### Changed

- `release.yml` now builds the Next.js dashboard and copies
  `dashboard/out/` into `quell/dashboard/static/` before `poetry
  build` so the compiled SPA ships inside the wheel.
- `pyproject.toml` `tool.poetry.include` explicitly packages the
  dashboard static dir, Jinja2 templates, and skill markdown.
- `tests/unit/test_agent_loop.py` uses `AgentConfig(max_iterations=3)`
  instead of the deprecated `_build_initial_state` override.

### Stop-gate

- `ruff check`, `ruff format --check`, and `mypy --strict` all clean
  across 111 source files.
- **302 tests** passing (was 242 in v0.1.0 / v0.1.1 — +60 new: 20
  notifier, 10 persistence, 14 cost, 10 dashboard, 6 replay).

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
