# CLI reference

Quell exposes seven subcommands.  All read/write happens through these;
Quell has no background daemon.

| Command | Purpose |
|---------|---------|
| [`quell init`](#quell-init) | Interactive wizard — writes `.quell/config.toml` + stores API key. |
| [`quell doctor`](#quell-doctor) | Environment & config health check. |
| [`quell watch`](#quell-watch) | Start the monitor → detector → agent loop. |
| [`quell history`](#quell-history) | Print recent incidents. |
| [`quell show`](#quell-show) | Print one incident's detail. |
| [`quell stats`](#quell-stats) | Aggregate statistics (totals, MTTR, top signatures). |
| [`quell version`](#quell-version) | Print the installed version and exit. |

`quell --help` prints the same list; `quell <subcommand> --help` prints
per-command flag help.

---

## `quell init`

Interactive setup wizard.  Detects project type, prompts for an LLM
provider and API key, lets you add a monitor, and writes
`.quell/config.toml` plus updates `.gitignore`.

```
quell init [--path PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--path / -p PATH` | `$PWD` | Project directory to configure. |

Side effects:

- Creates `.quell/config.toml` (non-secret config).
- Adds `.quell/` to `.gitignore` (creates the file if missing).
- Stores your API key (and any webhook URLs you configure) in the OS
  keychain, **never** in TOML.

Safe to re-run.  Existing values are offered as the default for each
prompt so you can accept the current setting with Return.

---

## `quell doctor`

Verifies that the environment, config, and API key are all set up.
Prints a coloured results table.

```
quell doctor [--path PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--path / -p PATH` | `$PWD` | Project whose config to load. |

Exit code is non-zero if any check failed.  Typical CI usage:

```bash
quell doctor || { echo "Quell not ready"; exit 1; }
```

---

## `quell watch`

Runs the main investigation loop indefinitely.  Wires together:

- The first monitor from `config.monitors` (events source).
- The built-in `Detector` (signature + rolling baseline → Incident).
- An `IncidentCommander` agent launched as a background task per
  detected incident.

```
quell watch [--path PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--path / -p PATH` | `$PWD` | Project whose config to load. |

Press `Ctrl-C` to stop — in-flight investigations are cancelled
cleanly.  If no monitors are configured, the command logs a warning
and exits immediately.

---

## `quell history`

Prints the most recent incidents in reverse-chronological order.

```
quell history [--limit / -n N]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-n / --limit` | 10 | Maximum rows to show. |

Example output:

```
ID                   STATUS         SEV       LAST_SEEN
inc_a1b2c3d4e5f6     resolved       high      2026-04-20T11:04:12+00:00
inc_ba9c8d7e6f5a     detected       medium    2026-04-20T10:23:08+00:00
```

No output means no incidents have been recorded yet (the loop hasn't
detected anything, or `quell watch` has never been run against this
project's database).

---

## `quell show`

Prints every field of a single incident by ID (the `inc_…` strings from
`quell history`).

```
quell show <incident_id>
```

Exit code 1 if no incident matches the given ID.

Example:

```
Incident inc_a1b2c3d4e5f6
  signature:         7a9e42f8b1c0d3e5
  severity:          high
  status:            resolved
  first_seen:        2026-04-20T10:02:45+00:00
  last_seen:         2026-04-20T11:04:12+00:00
  occurrence_count:  17
  root_cause:        Unchecked null on order.user in src/checkout.ts
  fix_pr_url:        https://github.com/you/my-app/pull/421
```

---

## `quell stats`

Aggregate summary of the whole incident database.

```
quell stats
```

Example output:

```
Incident statistics
  total incidents:   42
  detected:          6
  investigating:     2
  resolved:          34
  MTTR:              23.4 minutes
  top signatures:
    7a9e42f8b1c0d3e5  x17
    2bb33f19ce01a4d7  x11
    c4e7dd07a81b62f9  x8
```

MTTR is computed across resolved incidents only; `None` means nothing
has been resolved yet.

---

## `quell version`

Prints the installed version string and exits.

```
$ quell version
quell 0.2.0
```

Useful in bug reports — include this plus `poetry show` / `pip list`
output so we can tell which dep versions you're on.
