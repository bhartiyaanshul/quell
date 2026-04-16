# Quell — Rules for Claude Code

## Project conventions
- Python 3.12+, strict typing, Pydantic v2 for all data models
- Poetry for dependency management
- Ruff + mypy strict are non-negotiable
- Every module has a typed interface and pytest tests
- Errors throw subclasses of `QuellError` from `quell/utils/errors.py`
- Config is TOML, validated with Pydantic
- File length cap: 300 lines

## What this project is
An open-source multi-agent incident response system. A root "IncidentCommander" agent runs inside a Docker sandbox, investigates production incidents by calling tools, and spawns specialized subagents with domain-specific skills. All LLM calls go through LiteLLM. Every tool execution is routed through a FastAPI tool server running inside the sandbox.

## What this project is NOT
- A monitoring tool (Sentry, Datadog, etc. already do that)
- A chatbot — Quell is autonomous, not interactive
- An auto-merger — PRs are always draft, humans always review
- A Slack bot for incident communication

## Architectural rules
- The agent loop lives in `quell/agents/base_agent.py`. Don't bypass it.
- Tools communicate via the `ToolResult` type — no raw dicts across module boundaries.
- New tool? Add a file, register it with `@register_tool`, done. Don't touch the executor.
- New monitor? Implement the `Monitor` ABC, register it. Don't touch the detector.
- The Claude Code subprocess pattern is allowed but NOT the primary LLM path. Default is LiteLLM → user-chosen provider.
- Every tool that touches code or filesystem runs in the sandbox. No exceptions.

## Forbidden
- Direct calls to `openai` or `anthropic` SDK — use LiteLLM only
- Auto-merging PRs
- Telemetry of any kind by default (opt-in only)
- Storing user code or logs anywhere outside their machine
- `# type: ignore` without an explaining comment
- Any feature that requires the user to sign up for Quell Cloud to use the CLI

## Performance budget
- Agent iteration loop: < 2s overhead beyond LLM call latency
- Tool call dispatch: < 100ms overhead
- Docker sandbox startup: < 10s (on a warm image)
- Cold CLI startup: < 500ms
- Memory footprint (idle watch loop): < 200MB

## Build phases
This is a 16-phase build. **Stop after each phase and wait for the user to test before continuing.**
Current phase: see the latest git commit message or `quell/version.py`.

## Tech stack (locked — do not add dependencies outside this list without approval)
| Layer | Choice |
|-------|--------|
| Language | Python 3.12+ |
| Package management | Poetry |
| CLI | Typer |
| Interactive prompts | Questionary |
| LLM abstraction | LiteLLM |
| Data validation | Pydantic v2 |
| Config format | TOML (tomllib stdlib) |
| Database | SQLite via SQLAlchemy 2.0 |
| Logging | Loguru |
| HTTP client | httpx |
| HTTP server (tool server) | FastAPI + uvicorn |
| GitHub API | PyGithub |
| Docker | docker (Python SDK) |
| Templates | Jinja2 |
| YAML parsing | PyYAML |
| Tree-sitter | tree-sitter + language packs |
| Testing | pytest + pytest-asyncio + pytest-cov |
| Linting | Ruff |
| Type checking | mypy (strict) |
| Secrets storage | keyring |
