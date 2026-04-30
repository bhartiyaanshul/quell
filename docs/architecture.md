# Architecture

Quell is eight cooperating subsystems.  This page walks through each in
the order events flow through them.

```
  Monitor ──▶ Detector ──▶ IncidentCommander ──▶ agent_loop ──▶ Tool
             (sig + base-    (BaseAgent)           (LLM calls      (runs in
              line rules)                           + XML parse)    Docker)
```

## Config — `quell/config/`

TOML + Pydantic v2.  Two files are merged (global + project-local) and
validated once at startup.  Secrets are injected from the OS keychain
at load time; they never land in TOML.

- `schema.py` — every Pydantic model (LLMConfig, MonitorConfig union,
  SandboxConfig, QuellConfig root).
- `loader.py` — `load_config()` merges + validates.
- `paths.py` — XDG-compliant path helpers.

See [Configuration](configuration.md) for the reference.

## Memory — `quell/memory/`

Async SQLAlchemy 2.0 ORM.  SQLite via `aiosqlite` by default.

- `models.py` — `Incident`, `AgentRun`, `Event`, `Finding` tables.
- `db.py` — `get_engine()`, `get_session_factory()`, `create_tables()`.
- `incidents.py` — typed CRUD helpers.
- `stats.py` — aggregate queries for `quell stats`.

## Monitors — `quell/monitors/`

Each monitor emits a stream of `RawEvent` dataclasses.  Four adapters:

- `local_file` — tails a file, one event per new line.
- `http_poll` — polls a URL; emits on non-matching status or timeout.
- `vercel` — Vercel Deployments log API.
- `sentry` — Sentry Issues API.

All of them implement the `Monitor` ABC; `create_monitor(config)` is
the factory.

## Detector — `quell/detector/`

Turns the raw event stream into `Incident` records without calling the
LLM.

- `signature.py` — `compute_signature(event)` returns a 16-char hex
  fingerprint that normalises memory addresses, UUIDs, timestamps, and
  large numbers.
- `baseline.py` — `RollingBaseline` keeps a 24-hour deque of event
  timestamps per signature and exposes `current_rate` and `mean_rate`.
- `detector.py` — `Detector.process(event)` emits an `Incident` when
  the signature is new, the current rate spikes to 3× the mean, or
  the severity is `error` / `critical`; otherwise returns `None`.

## LLM layer — `quell/llm/`

Single choke-point for every model call.

- `llm.py` — `LLM` class wraps `litellm.acompletion`.
- `parser.py` — `parse_tool_invocations()` extracts XML
  `<function=name>…</function>` blocks out of LLM responses.
- `compression.py` — shrinks history when it exceeds
  `max_context_tokens`.
- `types.py` — `LLMMessage`, `LLMResponse`, `ToolInvocation`,
  `ToolMetadata`, `ToolParameterSpec`.

No direct use of the `openai` or `anthropic` SDKs is allowed anywhere
in the codebase.

## Tool system — `quell/tools/`

- `registry.py` — `@register_tool(name=…, parameters=…)` decorator and
  the global registry.
- `result.py` — `ToolResult` is the one canonical return type; no raw
  dicts cross tool boundaries.
- `executor.py` — `execute_tool(invocation)` validates arguments,
  routes to sandbox or local, and enforces the 50 KB output cap.
- `arguments.py` — string → typed argument coercion.
- `formatting.py` — render a list of `ToolResult` as a single XML
  observation string for the next LLM turn.
- `builtins.py` — idempotent bootstrap that (re-)registers every built-in
  tool.  Called from `quell watch` and from tests.

Built-in tools live in:

| Category | Tools |
|----------|-------|
| `tools/code/` | `code_read`, `code_grep` |
| `tools/git/` | `git_log`, `git_blame`, `git_diff` |
| `tools/monitoring/` | `logs_query`, `http_probe` |
| `tools/reporting/` | `create_incident_report`, `create_postmortem` |
| `tools/agents_graph/` | `agent_finish`, `finish_incident` |
| `quell/agents/graph_tools.py` | `create_agent`, `send_message`, `wait_for_message`, `view_graph` |

See [Extending Quell](extending.md) to add your own.

## Agents — `quell/agents/`

- `types.py` — `AgentStatus` enum and Phase 14 persistence types
  (`AgentMessage`, `ToolObservation`).
- `state.py` — `AgentState` (Pydantic v2) — the per-run mutable state
  object carried around inside each agent.
- `base_agent.py` — `BaseAgent` ABC and the `agent_loop()` driver.
- `incident_commander/` — `IncidentCommander` concrete class +
  `system_prompt.jinja` template.
- `subagent.py` — `GenericSubagent` spawned by the `create_agent` tool.
- `graph.py` — `AgentGraph` tracking parent/child relationships.
- `messages.py` — per-agent `asyncio.Queue` broker for inter-agent
  messages.
- `graph_tools.py` — the four coordination tools exposed to the LLM.

### The agent_loop

```python
while state.status == RUNNING:
    if state.iteration >= state.max_iterations:
        break                          # FAILED
    response = await self.llm.generate(state.messages)
    state.messages.append(LLMMessage("assistant", response.content))

    tool_calls = parse_tool_invocations(response.content)
    if not tool_calls:
        state.status = COMPLETED       # prose-only turn = done reasoning
        break

    results = [await execute_tool(inv, agent_state=state) for inv in tool_calls]
    state.messages.append(LLMMessage("user", format_observations(results)))
    state.iteration += 1

    for r in results:
        if self._is_finish_tool(r.tool_name):
            state.status = COMPLETED
            state.final_result = {"summary": r.output, **r.metadata}
            break
```

A successful turn appends four messages: `system`, `user`, `assistant`,
`user (observations)`.  Errors and max-iterations transition to
`FAILED` and append to `state.errors` rather than raising.

## Runtime — `quell/runtime/`

- `sandbox_info.py` — `SandboxInfo` (container id, host port, bearer
  token, workspace path, agent id).
- `runtime.py` — `AbstractRuntime` protocol (create / destroy / URL).
- `docker_runtime.py` — production implementation backed by the Docker
  SDK.  Starts the container with the workspace mounted read-only,
  polls `/health` for 30s, returns a typed `SandboxInfo`.
- `errors.py` — `SandboxStartError`, `SandboxHealthCheckError`,
  `SandboxNotFoundError`.

## Tool server — `quell/tool_server/`

A FastAPI app that runs *inside* each sandbox container.  Three routes:

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /health` | none | Runtime readiness probe. |
| `POST /register_agent` | bearer | Announce a subagent to the server. |
| `POST /execute` | bearer | Dispatch a tool invocation and return a JSON `ToolResult`. |

The executor on the host side posts to `/execute` whenever the tool
registers with `execute_in_sandbox=True` and a `sandbox_url` is
configured.  Inside the sandbox the executor detects
`QUELL_INSIDE_SANDBOX=1` and runs locally.

## CLI + watch loop

- `quell/interface/cli.py` — Typer entry points for global verbs
  (`init`, `doctor`, `watch`, `dashboard`, `version`) plus deprecated
  aliases (`history`, `show`, `stats`, `replay`, `test-notifier`)
  that forward to the resource handlers.
- `quell/interface/cli_helpers.py` — `build_output` and `safe_run`,
  shared across every command file (Phase 3.7).
- `quell/interface/wizard.py` — the interactive `quell init` flow.
- `quell/interface/wizard_noninteractive.py` — `quell init --yes` flag-
  driven setup (Phase 3.6); reads `$QUELL_*` env vars for secrets.
- `quell/interface/doctor.py` — the `quell doctor` checks; emits a
  `doctor.run` JSON envelope under `--json`.
- `quell/interface/<resource>_cmd.py` /  `<resource>_handlers.py` /
  `<resource>_schemas.py` — Phase 3 resource modules. One trio per
  resource (`incident`, `config`, `skill`, `notifier`).
- `quell/watch.py` — the main event loop wiring Monitor → Detector →
  IncidentCommander and scheduling investigations as background tasks.

## What happens when `quell watch` runs

```text
1. register_builtin_tools()               – idempotent tool bootstrap
2. get_engine() + create_tables()         – ensure the DB is ready
3. create_monitor(config.monitors[0])     – factory pick by "type"
4. list_skills()                          – load all bundled markdown runbooks
5. async for event in monitor.events():
     incident = await detector.process(event)
     if incident:
         skills = select_applicable(all_skills, context_from(event))
         commander = IncidentCommander(config, loaded_skills=skills)
         asyncio.create_task(commander.agent_loop(incident_prompt(incident)))
```

On `Ctrl-C` the outer coroutine is cancelled, the finally-block
cancels any in-flight investigation tasks, and the engine is disposed.
