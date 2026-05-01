# Migrating from Quell 0.2 to 0.3

Quell 0.3 reshapes the CLI around a `resource verb` grammar so the surface
is discoverable from `--help` alone, every command speaks JSON for tool
integration, and exit codes carry meaning. This guide walks through what
changed, how to update existing scripts, and what to expect from the
deprecated v0.2 commands while you migrate.

> **TL;DR** — every command in v0.2 still works in 0.3 (with a one-line
> `[deprecation]` warning to stderr). Old scripts keep running. New
> scripts should use the v0.3 grammar.

---

## 1. Command map

| 0.2 (still works in 0.3, deprecated) | 0.3 canonical |
|---|---|
| `quell history`                    | `quell incident list` |
| `quell show <id>`                  | `quell incident show <id>` |
| `quell stats`                      | `quell incident stats` |
| `quell replay <id>`                | `quell incident replay <id>` |
| `quell test-notifier <channel>`    | `quell notifier test <channel>` |
| `quell version`                    | `quell --version` (subcommand kept as alias) |
| `quell init` *(interactive only)*  | `quell init [flags]` *(now flag-driven under `--yes`)* |
| `quell doctor`                     | `quell doctor [--json]` *(unchanged grammar)* |
| `quell watch`                      | `quell watch` *(unchanged grammar)* |
| `quell dashboard`                  | `quell dashboard` *(unchanged grammar)* |

**New in 0.3** — entirely new command surfaces with no v0.2 equivalent:

| New command | What it does |
|---|---|
| `quell config show / get / set / validate / edit` | Read & mutate `.quell/config.toml` with type-checked dotted keys. |
| `quell skill list / show / enable / disable`      | List the bundled runbooks; toggle whether the watch loop auto-loads each. |
| `quell notifier list / add / remove`              | Add and remove notifier entries in `.quell/config.toml`. |
| `quell explain <command>`                         | Long-form, agent-friendly docs for any command. |
| `quell --help-json`                               | Emit the full command tree as JSON. |

The deprecated aliases will be **removed in 0.4.0**. Migrate at your
leisure during the 0.3 cycle; CI scripts should switch sooner so the
deprecation noise on stderr doesn't bury real warnings.

---

## 2. Universal flags

Every 0.3 command (resource verbs and global verbs) accepts these. Flag
precedence: `--json` wins over `--quiet` and `--verbose`; `--no-color`
is unconditional.

| Flag | Type | Behavior |
|---|---|---|
| `--json`            | bool | Emit a `{kind, version, data}` JSON envelope on stdout. Disables animations, colors, prompts. Errors → stderr as JSON. |
| `--quiet` / `-q`    | bool | Suppress non-error output. Disables animations. |
| `--verbose` / `-v`  | bool | Show debug-level logs on stderr. |
| `--yes` / `-y`      | bool | Skip confirmation prompts (destructive verbs only). |
| `--dry-run`         | bool | Show what would happen, don't write. |
| `--path PATH`       | path | Project directory to operate on. |
| `--no-color`        | bool | Disable ANSI colors. Auto-on under `NO_COLOR=1` or non-TTY. |
| `--help` / `-h`     | bool | Per-command help with `Examples:` block. |
| `--version` / `-V`  | bool | Print `quell <ver> (<binary path>)` and exit. |

Plus a new env var: **`QUELL_NO_ANIM=1`** disables spinners and progress
bars regardless of TTY state. Useful for terminals where the spinner
looks broken.

---

## 3. JSON output contract

Every command that produces output supports `--json`. The shape is stable:

```json
{
  "kind": "<resource>.<verb>",
  "version": "0.3",
  "data": { ... }
}
```

`kind` is the canonical identifier — `incident.list`, `config.show`,
`skill.show`, `notifier.add`, `doctor.run`, `help.tree`, etc. Errors go
to **stderr** as a separate envelope so `stdout` stays parseable:

```json
{"error": "No incident with ID 'inc_xyz'", "fix_command": "quell incident list", "exit_code": 7, "kind": "error.v1"}
```

Pipe to `jq` without ceremony:

```bash
quell incident list --json | jq '.data.incidents[] | select(.severity == "high") | .id'
```

---

## 4. Exit codes

0.3 ships a stable exit-code taxonomy. Scripts that previously checked
`exit_code != 0` keep working. Scripts that grep for exact codes need
updating:

| Code | Meaning |
|---|---|
| 0   | Success |
| 1   | Generic error (catch-all) |
| 2   | Usage error — bad flag, missing arg, unknown command |
| 3   | Configuration error — invalid TOML, schema violation |
| 4   | External service error — network, LLM provider 5xx |
| 5   | Sandbox error — Docker not running |
| 6   | Auth error — missing or invalid API key |
| 7   | Not found — incident ID, skill, config key |
| 8   | Already exists — `add` of something already configured |

For example, `quell incident show inc_missing` returned exit 1 in 0.2
and returns exit 7 in 0.3.

---

## 5. `quell init` is now flag-first

The interactive wizard is unchanged. New: `quell init --yes` runs
non-interactively from flags + `$QUELL_*` env vars, suitable for CI:

```bash
quell init --yes \
  --monitor local-file --log-path /var/log/app.log \
  --llm-provider anthropic
```

Secrets come from environment variables when `--yes` is passed:

| Env var | Stored as |
|---|---|
| `QUELL_<PROVIDER>_API_KEY`         | LLM API key (e.g. `QUELL_ANTHROPIC_API_KEY`) |
| `QUELL_SLACK_WEBHOOK_URL`           | Slack notifier webhook |
| `QUELL_DISCORD_WEBHOOK_URL`         | Discord notifier webhook |
| `QUELL_TELEGRAM_BOT_TOKEN`          | Telegram bot token |
| `QUELL_GITHUB_TOKEN`                | GitHub personal access token |

Anything missing is reported as a final warning so you know what to set
without reading source.

---

## 6. Migration recipes

### Replace a watch / history pipeline

```diff
- quell history --limit 50
+ quell incident list --limit 50
```

### Filter incidents from a script

0.2 had no filters; you piped through `grep`. 0.3 has structured filters:

```bash
# Resolved high-severity incidents from the last week
quell incident list --status resolved --severity high --since "1 week ago"
```

### Detect an outdated install

0.3's `quell doctor` includes a `Single install` check (flags duplicate
`quell` binaries on PATH) and a `PyPI freshness` check (suggests
`pipx upgrade quell` when outdated). For CI:

```bash
quell doctor --quiet || exit 1
```

### Verify config in CI

```bash
quell config validate || exit 3
```

### Read a single config value

```bash
MODEL=$(quell config get llm.model)
echo "Quell will call ${MODEL}"
```

### Set a config value non-interactively

```bash
quell config set llm.model "anthropic/claude-haiku-4-5" --yes
quell config set agent.max_iterations 100 --yes
```

`config set` refuses to write `llm.api_key` to TOML — that lives in the
OS keychain. Use `quell init` to update secrets.

### Drive `quell` from an agent

```bash
quell --help-json | jq '.data.commands.incident.commands.list.params'
quell explain incident list   # human-readable long form for the agent
```

---

## 7. Rollback

If 0.3 breaks something for you, downgrade cleanly:

```bash
pipx install --force quell==0.2.1
```

Your `.quell/config.toml` from 0.2 still loads on 0.2 — 0.3 added the
optional `[skills] disabled = [...]` block but doesn't require it. If
you never disabled a skill you'll see no diff.

Open an issue at <https://github.com/bhartiyaanshul/quell/issues> when
you do — the deprecation cycle was sized assuming the new grammar would
be net-positive, and counter-evidence is useful.
