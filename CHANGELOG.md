# Changelog

All notable changes to Quell are documented here.  The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

## [0.1.0] — 2026-04-20

Initial pre-alpha release covering Phases 1-15.  See the section above
for the full feature set.  Phase 16 (public launch) is tracked
separately in `docs/LAUNCH.md`.
