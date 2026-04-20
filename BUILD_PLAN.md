# Quell — Full Build Plan (16 Phases)

> **Repo:** https://github.com/bhartiyaanshul/quell  
> **Stack:** Python 3.12, Poetry, Typer, LiteLLM, Pydantic v2, SQLAlchemy 2.0, FastAPI, Docker  
> **License:** Apache 2.0  
> **Rule:** Stop after every phase, run the stop-gate checks, then continue.

---

## How to use this document in a new session

Paste this into Claude Code at the start of a new session:

> "I'm building Quell — an open-source autonomous incident response system.
> Read `BUILD_PLAN.md` in the project root. Phase N is the last completed phase.
> Continue from Phase N+1. Follow all rules in `CLAUDE.md`."

Then check `git log --oneline -5` to confirm which phase is actually current.

---

## Project overview

Quell watches production systems, detects incidents, spawns a team of
AI agents in a Docker sandbox to investigate root cause, and opens a
draft PR with a fix — all autonomously. The user reviews and merges.

Architecture layers (bottom → top):
```
Memory (SQLite/SQLAlchemy) + Config (TOML/Pydantic)
Monitors (log sources) → Detector (anomaly detection)
LLM layer (LiteLLM wrapper + XML parser + compression)
Tool system (registry + executor + sandbox routing)
Agent system (BaseAgent + AgentState + agent_loop)
Skills (Jinja2 markdown files injected into system prompts)
Docker runtime (sandbox lifecycle + tool server)
CLI (Typer) + Doctor (health checks) + Init wizard (Questionary)
```

---

## Conventions — never deviate from these

- **Python 3.12+**, strict typing, `mypy --strict` must pass on every commit
- **Pydantic v2** for all data models
- **Poetry** for dependency management
- **Ruff** for lint + format (`line-length = 88`)
- **No `# type: ignore`** without an explaining comment
- **File length cap: 300 lines** — split if longer
- **Errors** are subclasses of `QuellError` from `quell/utils/errors.py`
- **No direct SDK calls** to `openai`/`anthropic` — use LiteLLM only
- **All tool output** crosses boundaries as `ToolResult` — no raw dicts/strings
- **Every tool touching code/filesystem** runs in the Docker sandbox
- **PRs are always draft** — humans always review, never auto-merge
- **Tests**: `pytest --asyncio-mode=auto`, all async tests just `async def`

### Stop-gate (run before every commit)
```bash
poetry run ruff check quell/ tests/        # zero errors
poetry run ruff format quell/ tests/ --check  # zero reformats
poetry run mypy quell/                     # zero errors
poetry run pytest tests/ --tb=short -q    # all pass
```

### Windows note
Poetry virtualenv is at `C:\venvs` (short path — avoids Windows MAX_PATH issues with litellm).
Set `$env:POETRY_VIRTUALENVS_PATH = 'C:\venvs'` before running poetry commands in PowerShell.
Poetry binary: `C:\Users\anshul\.local\bin\poetry.exe`

---

## Current state of the codebase

### Git log
```
30e24d8  ci: replace Node.js workflow with Python/Poetry CI
9d7f6d7  feat(phase-6): add tool system
dd809fc  feat(phase-5): add LLM layer
c90233e  feat(phase-4): add monitor adapters
119a509  feat(phase-3): add quell init wizard, doctor health checks
086033a  feat: Phase 2 — config + memory
a7fdda2  feat: Phase 1 — Python project skeleton
```

### Test count: 132 tests passing

### Package structure (as of Phase 6)
```
quell/
├── __init__.py
├── __main__.py
├── version.py                    # __version__ = "0.1.0"
├── interface/
│   ├── main.py                   # Typer app entry point
│   ├── cli.py                    # init / doctor / version commands
│   ├── wizard.py                 # quell init interactive wizard
│   └── doctor.py                 # quell doctor health checks
├── config/
│   ├── schema.py                 # Pydantic v2 models (MonitorConfig, etc.)
│   ├── loader.py                 # TOML load + merge + secret injection
│   └── paths.py                  # XDG-compliant config/data paths
├── memory/
│   ├── models.py                 # SQLAlchemy 2.0 Incident/AgentRun/Event/Finding
│   ├── db.py                     # async engine + session factory
│   ├── incidents.py              # CRUD operations
│   └── stats.py                  # aggregate queries
├── monitors/
│   ├── base.py                   # RawEvent dataclass + Monitor ABC + factory
│   ├── local_file.py             # tail a log file (json + regex modes)
│   ├── http_poll.py              # poll HTTP endpoint
│   ├── vercel.py                 # poll Vercel deployments API
│   └── sentry.py                 # poll Sentry Issues API
├── llm/
│   ├── types.py                  # LLMMessage, LLMResponse, ToolInvocation, ToolMetadata
│   ├── parser.py                 # XML tool-call parser (<function=name> format)
│   ├── compression.py            # message history compressor
│   └── llm.py                    # async LiteLLM wrapper (LLM class)
├── tools/
│   ├── result.py                 # ToolResult dataclass (success/failure/truncate)
│   ├── registry.py               # @register_tool decorator + global registry
│   ├── arguments.py              # string→type coercion + validation
│   ├── executor.py               # dispatch: local or sandbox stub
│   └── formatting.py             # XML observation formatter for LLM turns
└── utils/
    ├── errors.py                 # QuellError hierarchy
    ├── logger.py                 # Loguru setup
    ├── shell.py                  # CommandResult + run_command + command_exists
    └── keyring_utils.py          # get_secret / set_secret (OS keychain)
```

### Dependencies (pyproject.toml)
```toml
[tool.poetry.dependencies]
python = "^3.12"
typer = {extras = ["all"], version = ">=0.12"}
loguru = "^0.7"
pydantic = ">=2.0,<3.0"
sqlalchemy = {extras = ["asyncio"], version = ">=2.0,<3.0"}
aiosqlite = ">=0.17"
keyring = ">=24.0"
questionary = ">=2.0"
httpx = ">=0.27"
litellm = ">=1.40"
```

### mypy overrides
```toml
[[tool.mypy.overrides]]
module = ["loguru"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["questionary"]
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = ["litellm"]
ignore_missing_imports = true
```

---

## Phase completion status

| Phase | Name | Status | Tests |
|-------|------|--------|-------|
| 1 | Project skeleton + tooling | ✅ Done | 3 |
| 2 | Config + memory | ✅ Done | 24 |
| 3 | Init wizard + doctor | ✅ Done | 23 |
| 4 | Monitor adapters | ✅ Done | 24 |
| 5 | LLM layer | ✅ Done | 27 |
| 6 | Tool system | ✅ Done | 31 |
| 7 | Agent system | 🔲 Next | — |
| 8 | Skills system | 🔲 | — |
| 9 | Detector | 🔲 | — |
| 10 | Docker runtime | 🔲 | — |
| 11 | Tool server (FastAPI) | 🔲 | — |
| 12 | Built-in tools | 🔲 | — |
| 13 | Agent graph (multi-agent) | 🔲 | — |
| 14 | End-to-end integration | 🔲 | — |
| 15 | Polish + docs + CI/CD | 🔲 | — |
| 16 | Public launch prep | 🔲 | — |

---

## Phase 7 — Agent System

**Goal:** `BaseAgent`, `AgentState`, `agent_loop()`, `IncidentCommander` root agent.
This is the core engine that drives all investigation logic.

### Files to create
```
quell/agents/__init__.py
quell/agents/state.py           # AgentState Pydantic model
quell/agents/types.py           # AgentStatus enum, AgentMessage, ToolObservation
quell/agents/base_agent.py      # BaseAgent ABC + agent_loop()
quell/agents/incident_commander/
    __init__.py
    commander.py                # IncidentCommander(BaseAgent)
    system_prompt.jinja         # Jinja2 system prompt template
tests/unit/test_agent_state.py
tests/unit/test_agent_loop.py
```

### Key design decisions
- `AgentState` is a **Pydantic v2 model** (not dataclass) — enables `.model_copy()` for immutable-style updates
- `agent_loop()` is an `async` method on `BaseAgent`; it calls `self.llm.generate()`, parses XML tool calls via `parse_tool_invocations()`, dispatches via `execute_tool()`, formats observations via `format_observations()`, and appends to `state.messages`
- The loop runs **indefinitely** until the agent calls the `agent_finish` or `finish_incident` tool (or hits max iterations)
- `IncidentCommander` is the **only** concrete agent in Phase 7 — subagents come in Phase 13
- System prompt is a **Jinja2 template** rendered at agent creation time with incident context injected

### AgentState fields
```python
class AgentState(BaseModel):
    agent_id: str                        # uuid4
    parent_id: str | None = None
    name: str
    task: str
    status: AgentStatus                  # idle|running|waiting|completed|failed
    messages: list[LLMMessage]
    iteration: int = 0
    max_iterations: int = 50
    errors: list[str]
    sandbox_url: str | None = None
    sandbox_token: str | None = None
    final_result: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime
```

### agent_loop() skeleton
```python
async def agent_loop(self, task: str) -> dict[str, object]:
    self.state = AgentState(task=task, ...)
    self.state.messages.append(LLMMessage("system", self._render_system_prompt()))
    self.state.messages.append(LLMMessage("user", task))

    while self.state.status == AgentStatus.RUNNING:
        if self.state.iteration >= self.state.max_iterations:
            self.state.status = AgentStatus.FAILED
            break

        response = await self.llm.generate(self.state.messages)
        self.state.messages.append(LLMMessage("assistant", response.content))

        tool_calls = parse_tool_invocations(response.content)
        if not tool_calls:
            # No tool calls = agent is done reasoning, treat as finish
            break

        results = [await execute_tool(inv) for inv in tool_calls]
        obs = format_observations(results)
        self.state.messages.append(LLMMessage("user", obs))
        self.state.iteration += 1

        # Check for finish signal
        for result in results:
            if result.tool_name in ("agent_finish", "finish_incident"):
                self.state.status = AgentStatus.COMPLETED
                break

    return self.state.final_result or {}
```

### Dependencies to add
```toml
jinja2 = ">=3.1"
```

### mypy override to add
```toml
[[tool.mypy.overrides]]
module = ["jinja2"]
ignore_missing_imports = true
```

### Stop-gate
- `mypy quell/` — 0 errors
- `pytest tests/unit/test_agent_state.py tests/unit/test_agent_loop.py -v` — all pass
- Full suite still green

---

## Phase 8 — Skills System

**Goal:** Markdown skill files with YAML frontmatter, loaded and injected into agent system prompts via Jinja2.

### Files to create
```
quell/skills/__init__.py
quell/skills/loader.py          # load_skill(name), list_skills(), SkillFile dataclass
quell/skills/incidents/
    stripe-webhook-timeout.md
    unhandled-null.md
    openai-rate-limit.md
quell/skills/frameworks/
    fastapi.md
    nextjs-app-router.md
quell/skills/technologies/
    postgres.md
    redis.md
tests/unit/test_skills.py
```

### SkillFile dataclass
```python
@dataclass
class SkillFile:
    name: str           # slug from filename
    category: str       # "incidents" | "frameworks" | "technologies"
    description: str    # from YAML frontmatter
    content: str        # full markdown body (after frontmatter)
    applicable_when: list[dict[str, str]]  # frontmatter triggers
    severity_hint: str  # "low" | "medium" | "high"
```

### Skill frontmatter format
```yaml
---
name: stripe-webhook-timeout
category: incidents
description: Stripe webhook endpoints timing out or returning 500
applicable_when:
  - error_contains: "stripe-signature"
  - error_contains: "webhook timeout"
severity_hint: high
---
```

### Jinja2 injection in system prompt
```jinja
{% if loaded_skills %}
<specialized_knowledge>
{% for skill in loaded_skills %}
<{{ skill.name }}>
{{ skill.content }}
</{{ skill.name }}>
{% endfor %}
</specialized_knowledge>
{% endif %}
```

### Dependencies to add
```toml
pyyaml = ">=6.0"
```

### mypy override to add
```toml
[[tool.mypy.overrides]]
module = ["yaml"]
ignore_missing_imports = true
```

---

## Phase 9 — Detector

**Goal:** Turn `RawEvent` objects from monitors into `Incident` records.
Simple anomaly detection — no LLM involved.

### Files to create
```
quell/detector/__init__.py
quell/detector/signature.py     # compute_signature(event) → str
quell/detector/baseline.py      # RollingBaseline — rolling 24h event counts
quell/detector/detector.py      # Detector class — main entry point
tests/unit/test_detector.py
```

### Detector logic
```python
class Detector:
    async def process(self, event: RawEvent) -> Incident | None:
        sig = compute_signature(event)
        baseline = self._baselines[sig]
        baseline.record(event)

        is_new = baseline.occurrence_count == 1
        is_spike = baseline.current_rate > baseline.mean_rate * 3.0
        above_threshold = event.severity in ("error", "critical")

        if is_new or is_spike or above_threshold:
            return await self._create_incident(sig, event)
        return None
```

### compute_signature
- Hash of: error type (first word) + first non-whitespace line of stack trace
- Normalised: strip memory addresses, UUIDs, timestamps
- Result: 16-char hex string (sha256[:16])

---

## Phase 10 — Docker Runtime

**Goal:** `AbstractRuntime` protocol + `DockerRuntime` implementation.
Manages sandbox container lifecycle (create, wait for ready, destroy).

### Files to create
```
quell/runtime/__init__.py
quell/runtime/runtime.py        # AbstractRuntime Protocol
quell/runtime/sandbox_info.py   # SandboxInfo dataclass
quell/runtime/docker_runtime.py # DockerRuntime
quell/runtime/errors.py         # SandboxError subclasses
tests/unit/test_runtime.py      # mocked docker SDK tests
```

### SandboxInfo
```python
@dataclass
class SandboxInfo:
    container_id: str
    host_port: int          # random allocated port on host
    bearer_token: str       # 32-byte URL-safe token, generated per sandbox
    workspace_path: Path    # user's project root (mounted read-only)
    agent_id: str
```

### AbstractRuntime protocol
```python
class AbstractRuntime(Protocol):
    async def create_sandbox(self, workspace: Path, agent_id: str) -> SandboxInfo: ...
    async def destroy_sandbox(self, info: SandboxInfo) -> None: ...
    async def get_tool_server_url(self, info: SandboxInfo) -> str: ...
```

### DockerRuntime container spec
- Image: `ghcr.io/bhartiyaanshul/quell-sandbox:latest`
- Mount: workspace at `/workspace` read-only
- Port: random host port → container port 48081
- Env: `QUELL_INSIDE_SANDBOX=1`, `QUELL_BEARER_TOKEN=<token>`
- Resource limits: 2GB RAM, 2 CPUs (configurable via `SandboxConfig`)
- Health check: GET `/health` until 200 or 30s timeout

### Dependencies to add
```toml
docker = ">=7.0"
```

### mypy override to add
```toml
[[tool.mypy.overrides]]
module = ["docker", "docker.*"]
ignore_missing_imports = true
```

---

## Phase 11 — Tool Server (FastAPI inside sandbox)

**Goal:** FastAPI app that runs **inside** the Docker container and exposes
`POST /execute`, `POST /register_agent`, `GET /health`.

### Files to create
```
quell/tool_server/__init__.py
quell/tool_server/server.py         # FastAPI app factory
quell/tool_server/auth.py           # bearer token middleware
quell/tool_server/context.py        # ContextVar for current agent_id
quell/tool_server/routes/
    __init__.py
    execute.py                      # POST /execute
    register.py                     # POST /register_agent
    health.py                       # GET /health
tests/unit/test_tool_server.py
```

### /execute request schema
```python
class ExecuteRequest(BaseModel):
    tool_name: str
    args: dict[str, str]
    agent_id: str
```

### Wire up executor HTTP dispatch
Update `quell/tools/executor.py` — replace the Phase-6 stub:
```python
async def _execute_via_sandbox(...):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{sandbox_url}/execute",
            json={"tool_name": tool_name, "args": kwargs_as_strings, "agent_id": "..."},
            headers={"Authorization": f"Bearer {sandbox_token}"},
            timeout=120.0,
        )
    data = resp.json()
    return ToolResult(tool_name=tool_name, ok=data["ok"], output=data["output"], ...)
```

### Dependencies to add
```toml
fastapi = ">=0.111"
uvicorn = {extras = ["standard"], version = ">=0.30"}
```

---

## Phase 12 — Built-in Tools

**Goal:** Implement all the tools the agent can actually call.
Each tool is a separate file in `quell/tools/<category>/`.

### Files to create
```
quell/tools/monitoring/
    __init__.py
    logs_query.py               # query configured log source
    http_probe.py               # hit HTTP endpoint, return status + body

quell/tools/code/
    __init__.py
    read.py                     # read file with optional line range
    grep.py                     # ripgrep-backed search

quell/tools/git/
    __init__.py
    log.py                      # recent commits
    blame.py                    # who last touched each line
    diff.py                     # diff between two refs

quell/tools/reporting/
    __init__.py
    incident_report.py          # create_incident_report tool
    postmortem.py               # create_postmortem tool

quell/tools/agents_graph/
    __init__.py
    agent_finish.py             # signal this agent is done
    finish_incident.py          # root agent: end the investigation
```

### Tool registration pattern (every tool follows this exactly)
```python
from quell.tools.registry import register_tool
from quell.tools.result import ToolResult
from quell.llm.types import ToolParameterSpec

@register_tool(
    name="code_read",
    description="Read a file from the workspace.",
    parameters=[
        ToolParameterSpec("path", "string", "Relative path", required=True),
        ToolParameterSpec("start_line", "integer", "1-indexed start", required=False),
        ToolParameterSpec("end_line", "integer", "Inclusive end", required=False),
    ],
    execute_in_sandbox=True,
)
async def code_read(path: str, start_line: int = 1, end_line: int = -1) -> ToolResult:
    ...
```

---

## Phase 13 — Agent Graph (multi-agent)

**Goal:** Root agent can spawn subagents, send messages between them,
wait for results, and coordinate parallel investigation.

### Files to create
```
quell/agents/graph.py           # AgentGraph — tracks parent/child relationships
quell/agents/messages.py        # inter-agent message queue (asyncio.Queue)
quell/tools/agents_graph/
    create_agent.py             # spawn a subagent with task + skills
    send_message.py             # post to another agent's queue
    wait_for_message.py         # block until message arrives
    view_graph.py               # inspect current investigation graph
tests/unit/test_agent_graph.py
```

### create_agent tool
When the IncidentCommander calls `create_agent`:
1. Instantiate a new `BaseAgent` subclass (or generic agent)
2. Set `parent_id = commander.agent_id`
3. Register in `AgentGraph`
4. Start `agent_loop()` as a background `asyncio.Task`
5. Return the new `agent_id` to the commander

---

## Phase 14 — End-to-end Integration

**Goal:** Wire everything together: monitor → detector → IncidentCommander →
subagents → tools → PR → notify.

### Files to create/update
```
quell/watch.py                  # main watch loop (async)
quell/interface/cli.py          # add `quell watch` command
tests/e2e/test_full_incident_flow.py   # integration test with mock LLM
fixtures/sample_logs/app_error.log
fixtures/vulnerable_app/         # deliberately broken app for e2e testing
```

### watch loop
```python
async def watch(config: QuellConfig) -> None:
    monitor = create_monitor(config.monitors[0])
    detector = Detector(config)
    async for event in monitor.events():
        incident = await detector.process(event)
        if incident:
            commander = IncidentCommander(config=config)
            asyncio.create_task(commander.agent_loop(task=incident_prompt(incident)))
```

---

## Phase 15 — Polish, Docs, CI/CD

**Goal:** Everything needed for a clean public launch.

### Tasks
- Update `README.md` with full install instructions, demo GIF, architecture diagram
- Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`
- GitHub Actions: add `release.yml` (tag → PyPI publish)
- Add `quell history`, `quell show <id>`, `quell stats` CLI commands
- Add `--version` flag that reads from `quell/version.py`
- Coverage report: `pytest --cov=quell --cov-report=html`
- Bump version to `0.1.0` in `pyproject.toml` and `version.py`

### release.yml
```yaml
on:
  push:
    tags: ["v*"]
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: snok/install-poetry@v1
      - run: poetry build
      - run: poetry publish --username __token__ --password ${{ secrets.PYPI_TOKEN }}
```

---

## Phase 16 — Public Launch

**Goal:** Soft launch to 10 developers, gather feedback, fix critical issues,
then public launch on Hacker News + X + Product Hunt.

### Checklist
- [ ] `poetry run quell --help` works cleanly from a fresh `pipx install quell-agent`
- [ ] `quell init` wizard runs end-to-end on macOS, Linux, Windows
- [ ] `quell doctor` passes with a real API key configured
- [ ] `quell watch` runs against a local log file and spawns an agent
- [ ] Docker sandbox image pushed to `ghcr.io/bhartiyaanshul/quell-sandbox:latest`
- [ ] README has a 90-second demo video linked
- [ ] `quell.anshulbuilds.xyz` DNS record live and redirects to GitHub
- [ ] Discord server created, link in README
- [ ] Hacker News: "Show HN: Quell – open-source autonomous on-call engineer"

---

## Key technical decisions (locked — do not relitigate)

| Decision | Choice | Reason |
|----------|--------|--------|
| LLM calls | LiteLLM only | 100+ providers, no vendor lock |
| Tool call format | XML `<function=name>` | Model-agnostic, streaming-friendly |
| Sandbox | Docker | Isolation guarantee for all code-touching tools |
| Config | TOML + Pydantic v2 | Human-readable, strongly typed |
| Secrets | OS keychain (keyring) | Never plaintext on disk |
| DB | SQLite + SQLAlchemy 2.0 async | Zero-config, cross-platform |
| CLI | Typer | Type-annotated, built on Click |
| Prompts | Questionary | Best DX for terminal UIs |
| HTTP client | httpx | Async-native |
| Logging | Loguru | Single-import, structured |
| Templates | Jinja2 | Standard, battle-tested |

---

## Known gotchas and solutions

### Windows MAX_PATH with litellm
litellm has deeply nested file paths that exceed Windows 260-char limit.
**Fix:** Set `POETRY_VIRTUALENVS_PATH=C:\venvs` (short base path).

### Poetry not in PATH after install
**Fix:** `python -m pipx ensurepath` then restart terminal, or refresh with:
`$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")`

### StopAsyncIteration in async generators
Python 3.7+ converts `StopAsyncIteration` raised inside an async generator to `RuntimeError`.
**Fix:** Use a custom sentinel exception class (e.g. `class _HaltError(Exception): pass`) to terminate mock loops in tests.

### litellm mypy errors
litellm ships without complete type stubs.
**Fix:** `ignore_missing_imports = true` in `[[tool.mypy.overrides]]` for module `litellm`.

### Nested `with` blocks (SIM117)
Ruff requires combining nested `with` into a single `with (a, b):` parenthesised form.

### docker + questionary mypy
Both need `ignore_missing_imports = true` overrides (no py.typed markers).

---

## Dependency additions per phase

| Phase | Package | Version |
|-------|---------|---------|
| 1-6 | (already in pyproject.toml) | — |
| 7 | `jinja2` | `>=3.1` |
| 8 | `pyyaml` | `>=6.0` |
| 9 | (no new deps) | — |
| 10 | `docker` | `>=7.0` |
| 11 | `fastapi`, `uvicorn[standard]` | `>=0.111`, `>=0.30` |
| 12 | (no new deps) | — |
| 13 | (no new deps) | — |
| 14 | (no new deps) | — |
| 15 | `pygithub` | `>=2.0` (for PR creation tools) |
| 16 | — | — |
