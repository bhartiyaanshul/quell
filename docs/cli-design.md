# CLI Design — v0.3.0

> **Status:** Spec. No code yet. Locks the contract for the Phase 2+ rewrite.
> Comment via PR review. Once merged to `develop`, this doc is binding —
> any deviation in implementation requires a PR back to this file first.

---

## 1. Goals

Optimized for, in priority order:

1. **Agent-friendly.** Non-interactive, flag-driven, structured output, predictable.
   An LLM agent should be able to drive Quell from `--help` alone, with no out-of-band knowledge.
2. **Human-respectful.** Interactive fallback when flags are missing on a TTY,
   animated feedback for long operations, sensible defaults visible at every prompt.
3. **Discoverable.** `--help` everywhere with examples. `quell` with no args
   shows the resource list, not a wall of text.
4. **Composable.** Accepts stdin where useful. Emits machine-readable output
   for piping. Idempotent commands so retries are safe.
5. **Self-documenting.** Errors include the corrective command. `--version`
   shows the binary path. Help text explains *why* a flag matters, not just *what* it does.

## 2. Non-goals

- Sub-commands deeper than `quell <resource> <verb>`. No `quell incident analysis show`.
- Interactive REPL mode (no `quell shell`).
- TUI / curses-based UI. The dashboard is a separate Next.js app.
- Translations / i18n. English only.
- Plugin system for third-party commands. Out of scope for 0.3.

---

## 3. Command grammar

### 3.1 Shape

```
quell <resource> <verb> [args] [--flags]
quell <verb>                     [args] [--flags]   # global verbs only
```

Global verbs are reserved for operations that don't fit a single resource:
`init`, `doctor`, `watch`, `dashboard`.

### 3.2 Resources & verbs

| Resource | Verbs |
|---|---|
| `incident` | `list`, `show <id>`, `stats`, `replay <id>` |
| `config` | `show`, `get <key>`, `set <key> <value>`, `validate`, `edit` |
| `skill` | `list`, `show <name>`, `enable <name>`, `disable <name>` |
| `notifier` | `list`, `test <channel>`, `add`, `remove <channel>` |

### 3.3 Standard verb semantics

`list` always supports `--limit`, `--filter <key>=<value>`, `--since`, `--json`.
`show` always supports `--json`.
`add` / `remove` / `set` are destructive — require `--yes` to skip confirmation,
support `--dry-run` to preview.

### 3.4 Migration table (0.2 → 0.3)

| Old (0.2.x) | New (0.3.0) | Status in 0.3.0 |
|---|---|---|
| `quell history` | `quell incident list` | Old kept as deprecated alias, prints warning to stderr |
| `quell show <id>` | `quell incident show <id>` | Deprecated alias |
| `quell stats` | `quell incident stats` | Deprecated alias |
| `quell replay <id>` | `quell incident replay <id>` | Deprecated alias |
| `quell test-notifier <channel>` | `quell notifier test <channel>` | Deprecated alias |
| `quell version` | `quell --version` | Subcommand kept as alias; `--version` is canonical |
| `quell init` | `quell init [--flags]` | Same name, becomes flag-first |
| `quell doctor` | `quell doctor [--json]` | Unchanged grammar, gains `--json` |
| `quell watch` | `quell watch` | Unchanged grammar |
| `quell dashboard` | `quell dashboard` | Unchanged grammar |

In 0.4.0: deprecated aliases removed.

---

## 4. Universal flags

Every command accepts these. Defaults are conservative.

| Flag | Type | Default | Behavior |
|---|---|---|---|
| `--json` | bool | `false` | Emit machine-readable JSON to stdout. Disables animations, colors, prompts. Errors → stderr as JSON. |
| `--quiet` / `-q` | bool | `false` | Suppress all non-error output. Disables animations. |
| `--verbose` / `-v` | bool | `false` | Show debug-level logging on stderr. |
| `--yes` / `-y` | bool | `false` | Skip all confirmation prompts. Equivalent to answering "yes" to every prompt. |
| `--dry-run` | bool | `false` | Show what would happen, do nothing. Available on every destructive command. |
| `--path PATH` | path | `cwd` | Project directory to operate on. |
| `--no-color` | bool | auto | Disable ANSI colors. Auto-on if `NO_COLOR` env or not a TTY. |
| `--config FILE` | path | `<path>/.quell/config.toml` | Override config file location. |
| `--help` / `-h` | bool | — | Print context-sensitive help with examples. |
| `--version` / `-V` | bool | — | Print `quell <version> (<binary path>)` and exit. |

### 4.1 Flag precedence

When multiple universal flags conflict (e.g. `--quiet --verbose`):

1. `--json` wins over `--quiet` and `--verbose` (forces deterministic JSON)
2. `--quiet` wins over `--verbose`
3. `--no-color` always wins (it's unconditional)

### 4.2 Per-command flag examples

```bash
quell incident list --status resolved --severity high --since "1 week ago" --limit 50
quell config set llm.model "anthropic/claude-haiku-4-5" --yes
quell skill enable postgres-deadlock
quell init --monitor local-file --log-path /var/log/app.log --llm-provider ollama --yes
quell notifier test slack --dry-run
```

---

## 5. Output formats

### 5.1 Default — human, TTY

Tables, panels, colors, icons. Smart truncation when terminal is narrow.
Tables align numerically and respect `--no-color`.

```
$ quell incident list --limit 3

  ID                STATUS     SEV     LAST SEEN          
  ────────────────────────────────────────────────────────
  inc_a1b2c3d4      resolved   high    2h ago             
  inc_e5f6g7h8      detected   medium  4h ago             
  inc_i9j0k1l2      resolved   low     yesterday          

  Showing 3 of 47. Use --limit to see more.
```

### 5.2 `--json` — machine, structured

Stable schema. Every response wraps:

```json
{
  "kind": "incident.list",
  "version": "0.3",
  "data": [ ... ]
}
```

`kind` is `<resource>.<verb>`. `version` is the schema version (independent of CLI version).
`data` is the payload — shape defined per `kind` in `quell/interface/output_schemas.py`.

Errors in `--json` mode go to stderr:

```json
{
  "error": "Config file not found at .quell/config.toml",
  "fix_command": "quell init",
  "exit_code": 3,
  "kind": "error.v1"
}
```

### 5.3 `--quiet`

Errors only. Successful output is suppressed; the exit code is the signal.
Useful in CI: `quell doctor --quiet || exit 1`.

### 5.4 Streaming (JSONL)

Long-running commands stream events one per line. With `--json` each line is a
discrete JSON object (JSONL format):

```
{"kind":"watch.event.v1","ts":"...","level":"INFO","msg":"monitor: tailing..."}
{"kind":"watch.event.v1","ts":"...","level":"INFO","msg":"detector: signature..."}
```

Without `--json` the same stream is human-formatted.

---

## 6. Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Generic error (catch-all) |
| 2 | Usage error — bad flag, missing required arg, unknown command |
| 3 | Configuration error — invalid TOML, schema violation, missing required field |
| 4 | External service error — network failure, LLM provider 5xx, GitHub API down |
| 5 | Sandbox error — Docker not running, container failed to start |
| 6 | Authentication error — missing or invalid API key |
| 7 | Not found — incident ID, skill name, config key not present |
| 8 | Already exists — `add` of something that already exists (idempotent commands return 0 here) |
| 64+ | Reserved for future use; never used by 0.3 |

Stable across patch and minor releases. Adding a new code in a patch is allowed.
Repurposing a code is a major-version change.

---

## 7. Error messages

### 7.1 Style rules

Every error includes:

1. **What went wrong** — one sentence, no jargon.
2. **Why it matters** — optional, when not obvious from the message.
3. **How to fix it** — exact command, or a specific instruction.

### 7.2 Format (default mode)

```
Error: Config file not found at .quell/config.toml.

Quell needs a project config to know what to watch and how.

Fix:
  quell init                                # interactive setup
  quell init --yes --monitor local-file ... # non-interactive (see --help)
```

Error word in red; "Fix:" header in muted; commands in monospace accent color.

### 7.3 Format (JSON mode)

See §5.2.

### 7.4 Common error catalogue

The implementation should ship with a fixed catalogue of error templates so
messages stay consistent. Examples:

| Error class | Message template | Fix template |
|---|---|---|
| `ConfigNotFound` | `Config file not found at {path}` | `quell init` |
| `ConfigInvalid` | `Invalid TOML in {path}: {detail}` | `quell config validate` then fix the file |
| `IncidentNotFound` | `No incident with ID '{id}'` | `quell incident list` to see existing IDs |
| `LLMUnreachable` | `LLM provider '{provider}' returned {code}` | `quell doctor` to diagnose |
| `APIKeyMissing` | `No API key for provider '{provider}' in keychain` | `quell init` (re-runs the keychain step) |
| `DockerNotRunning` | `Docker daemon not reachable` | Start Docker Desktop or `sudo systemctl start docker` |
| `MultipleInstalls` | `Multiple quell binaries on PATH ({n})` | `pip uninstall -y quell` (keeps the pipx install) |

---

## 8. Interactive prompts

### 8.1 Rules

**Never prompt when:**
1. `--yes` is passed (answer "yes" / accept default for everything)
2. `--quiet` or `--json` is passed (no UI at all)
3. stdin is not a TTY (e.g. piped, in CI)
4. The required value was supplied as a flag

**Prompt only when:** TTY is available AND no flag was passed for the value AND
the value is required.

When required + non-TTY + no flag: error fast with the corrective command.
Never hang waiting for input that can't arrive.

### 8.2 Style

- Question in default foreground, bold
- Default value shown in muted brackets: `[default]`
- Choices in muted foreground; selected in accent (orange)
- Cursor symbol: `▸`
- Inline error in red, one line below the prompt

```
? Path to log file: [/var/log/app.log] _

? Which LLM provider should Quell use?
  ▸ Anthropic (Claude)
    OpenAI (GPT-4o)
    Google (Gemini)
    Ollama (local)
    Other (enter manually)
```

### 8.3 Confirmation prompts

For destructive actions, default to "no". User must explicitly type `y` or pass `--yes`:

```
This will delete 47 incidents older than 30 days. Continue? [y/N] _
```

---

## 9. Visual design

### 9.1 Palette

Matches the landing page so the brand is consistent across web and terminal.

| Role | Color | Hex | Use |
|---|---|---|---|
| Primary | Accent orange | `#fb923c` | Branding, success bullets, prompts cursor |
| Success | Green | `#22c55e` | ✓ checkmarks, "OK" status |
| Warning | Amber | `#fcd34d` | ! warnings |
| Error | Red | `#ef4444` | ✗ failures, error messages |
| Info | Blue-gray | `#94a3b8` | Hints, secondary text, "Showing X of Y" |
| Muted | Dim gray | `#64748b` | Timestamps, metadata, table separators |

Colors auto-disable when `NO_COLOR=1` env or stdout is not a TTY or `--no-color`.

### 9.2 Icons

Unicode-safe, no emoji. Used sparingly.

| Icon | Codepoint | Meaning |
|---|---|---|
| `✓` | U+2713 | Success |
| `✗` | U+2717 | Failure |
| `!` | ASCII | Warning |
| `→` | U+2192 | Action / pointer |
| `▸` | U+25B8 | Prompt cursor |
| `…` | U+2026 | In progress / continuation |

### 9.3 Typography

- Headers: bold, no color (let the content speak).
- Code, paths, identifiers: monospace where Rich allows (`[code]...[/code]`).
- Tables: borderless by default. `╴` separator only when columns aren't visually distinct.
- Quotes around user-supplied strings in messages: `'value'` (single quotes).

---

## 10. Animations

### 10.1 When animations run

All of these must be true:

1. stdout is a TTY
2. `--quiet`, `--json`, `--no-color` are all unset
3. `QUELL_NO_ANIM=1` env var is unset
4. The operation is expected to take > 200ms

If any condition fails: emit a single static line equivalent.

### 10.2 Components

#### Spinner — for "thinking" / unknown duration

```
⠋ Calling LLM (claude-haiku-4-5)… 2.4s
```

Honest, specific labels — not `Loading…`. Update the label when the underlying
operation changes phase. Show elapsed time after 1s.

#### Progress bar — for known-length operations

```
Loading skills  ━━━━━━━━━━━━━━━━━━━━ 19/19 done
```

Used for: skill loading, dashboard build, batch processing.

#### Live status — for `quell watch`

Bottom-anchored, single-line, updates in place. The scrolling log goes above.

```
⠋ monitoring 1 source · 3 incidents · uptime 4m12s · last event 2s ago
```

### 10.3 First-run welcome panel

`quell init` on its first interactive line shows a brand panel:

```
┌────────────────────────────────────────────────┐
│                                                │
│  Quell — an on-call engineer that              │
│          never sleeps.                         │
│                                                │
│  Setup takes about 90 seconds.                 │
│                                                │
└────────────────────────────────────────────────┘
```

Skipped under `--yes` / `--quiet` / non-TTY.

### 10.4 Streaming agent output

When `--verbose` is set on `quell watch` or `quell incident replay`, LLM output
streams token-by-token rather than buffering until the call finishes.
Default mode shows summarized status only.

---

## 11. `--help` content

### 11.1 Top-level (`quell` with no args, or `quell --help`)

Shows the resource list and the 3–4 most common commands. NOT a wall of text.

```
Quell — an on-call engineer that never sleeps.

Usage: quell [resource] [verb] [flags]
       quell <verb> [flags]    # global verbs

Common commands:
  quell init                  Configure Quell for a project
  quell watch                 Start the investigation loop
  quell incident list         Show recent incidents
  quell doctor                Verify your setup

Resources:
  incident   Past investigations
  config     Configuration management
  skill      Runbook management
  notifier   Output channel management

Run `quell <command> --help` for examples and flag details.
```

### 11.2 Per-command help

Every subcommand's `--help` includes:

1. One-line summary
2. Synopsis with all positional args and required flags
3. Flag table (one line per flag)
4. **`Examples:` section with at least 2 examples** — one happy path, one realistic edge case

Example:

```
$ quell incident list --help

Show recent incidents.

Usage:
  quell incident list [--status STATUS] [--severity SEV] [--since WHEN]
                      [--limit N] [--json] [--quiet]

Options:
  --status STATUS    Filter by status (detected, investigating, resolved, failed)
  --severity SEV     Filter by severity (low, medium, high, critical)
  --since WHEN       Filter to incidents seen since WHEN (e.g. "1 hour ago", "2026-04-29")
  --limit N          Max rows to return [default: 10]
  --json             Emit JSON instead of a table
  ... universal flags ...

Examples:
  quell incident list                                          # 10 most recent
  quell incident list --status resolved --severity high        # filter
  quell incident list --json --limit 100 | jq '.data[].id'     # pipe to jq
  quell incident list --since "1 week ago" --quiet             # CI use
```

---

## 12. End-to-end examples

### 12.1 Human flow (first-time setup)

```
$ quell init
┌────────────────────────────────────────────────┐
│  Quell — an on-call engineer that never sleeps │
└────────────────────────────────────────────────┘

[1/5] Project type: Python (Poetry / setuptools) detected
[2/5] Log source — where should Quell watch?
  ▸ Local log file
    HTTP endpoint
    Vercel
    Sentry
[3/5] Path to log file: [/var/log/app.log] _
[4/5] LLM provider:
  ▸ Anthropic (Claude)
    ...
[5/5] API key for Anthropic (Claude): ********

✓ Config written to .quell/config.toml
✓ .quell/ added to .gitignore

→ Next: run `quell doctor` to verify your setup.
```

### 12.2 Agent flow (non-interactive setup)

```bash
$ quell init \
    --yes \
    --monitor local-file \
    --log-path /var/log/app.log \
    --llm-provider anthropic \
    --llm-model "anthropic/claude-haiku-4-5"

# Agent reads the API key from an env var or pipes it in:
$ echo "$ANTHROPIC_API_KEY" | quell config set --secret anthropic --stdin

$ quell doctor --json
{
  "kind": "doctor.run",
  "version": "0.3",
  "data": {
    "checks": [
      {"name": "python", "status": "ok", "detail": "3.12.10"},
      {"name": "git", "status": "ok", "detail": "git found"},
      {"name": "docker", "status": "ok", "detail": "Docker Engine 27.3.1"},
      {"name": "config", "status": "ok", "detail": ".quell/config.toml parsed"},
      {"name": "llm", "status": "ok", "detail": "anthropic key present"},
      {"name": "single_install", "status": "ok", "detail": "C:\\Users\\you\\.local\\bin\\quell.exe"}
    ],
    "passed": 6,
    "failed": 0
  }
}
```

### 12.3 Recovery from error

```
$ quell incident show inc_xyz
Error: No incident with ID 'inc_xyz'.

Fix:
  quell incident list                  # see existing IDs
  quell incident list --since "1d ago" # narrower search
```

```
$ quell incident show inc_xyz --json
{"error":"No incident with ID 'inc_xyz'","fix_command":"quell incident list","exit_code":7,"kind":"error.v1"}
```

---

## 13. Implementation notes (for Phase 2+)

These are guideposts for the rewrite, not part of the user-facing contract.

- **Output facade lives in `quell/interface/output.py`.** Every command writes
  through it; commands never `print()` or `typer.echo()` directly.
- **Output schemas are Pydantic v2 models in `quell/interface/output_schemas.py`.**
  They are the source of truth for JSON shapes. JSON output is
  `model.model_dump_json()`.
- **Prompts live in `quell/interface/prompts.py`.** Wraps Questionary with the
  locked theme. `prompt_or_flag()` helper enforces the §8.1 rules.
- **Errors raise `QuellCLIError(message, fix_command=..., exit_code=...)`.**
  A top-level handler in `main.py` catches and formats them per §7.
- **Animations live in `quell/interface/spinner.py` and `progress.py`.**
  Both check the §10.1 rules before doing anything.
- **No new runtime dependencies.** `rich` ships with `typer[all]`, `questionary`
  is already in the lock file.

---

## 14. Open questions

Things this spec deliberately leaves unanswered. To be resolved by Phase 2 PRs.

1. **Config edit verb (`quell config edit`)** — does it open `$EDITOR` or
   provide a structured TUI? Recommendation: open `$EDITOR` for simplicity, validate on save.
2. **Streaming JSONL on stdout vs. stderr** — JSONL events go to stdout, but
   the human progress goes to stderr. Need to verify this composes with `jq` and `tee`.
3. **Should `quell config set` accept dotted keys (`llm.model`) or require
   nested syntax?** Recommendation: dotted keys, with `--type str|int|bool|list` to
   disambiguate when needed.
4. **Width-detection for tables on resize** — Rich handles this; need to confirm
   it's smooth for `quell watch`'s live status during a window resize.

---

## 15. Acceptance criteria for v0.3.0

The redesign is "done" when:

- [ ] Every command in §3.2 ships and passes its `--help` examples.
- [ ] Every command supports the universal flags in §4.
- [ ] Every error matches the templates in §7.4 (or a documented extension).
- [ ] Snapshot tests cover output in default, `--json`, and `--quiet` modes for at least one command per resource.
- [ ] `quell incident list --json | jq '.data[0].id'` works end-to-end on macOS, Linux, and Windows (PowerShell).
- [ ] CI runs all tests with `NO_COLOR=1` and `QUELL_NO_ANIM=1` to verify deterministic output.
- [ ] `docs/migrating-to-0.3.md` exists with the §3.4 table expanded to full examples.
- [ ] Landing page install tabs and demo terminal updated.
- [ ] Tag `v0.3.0` published; `pipx install quell` resolves to it.

---

*Last updated: 2026-04-30 — initial spec for review.*
