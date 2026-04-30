# Getting started

This guide takes you from zero to a running Quell investigation in about
ten minutes.  By the end you will have:

1. Quell installed and on your `PATH`.
2. A project configured with `.quell/config.toml` and an LLM API key in
   your OS keychain.
3. `quell doctor` reporting all checks green.
4. Your first `quell watch` loop running against a local log file.

---

## 0.  Prerequisites

You need these already installed:

| Requirement | Why | How to check |
|-------------|-----|--------------|
| **Python 3.12 or newer** | Quell is strictly-typed and uses `3.12+` features. | `python3.12 --version` |
| **git** | Several built-in tools (`git_log`, `git_blame`, `git_diff`) shell out to `git`. | `git --version` |
| **Docker** (optional for now) | The sandbox runtime uses Docker for the per-agent isolated environment.  Quell's unit test suite and a dry-run `watch` work without it, but real investigations of untrusted code should always run under Docker. | `docker info` |

If any of those is missing install it before continuing.  On macOS the
shortest path is:

```bash
brew install python@3.12 git
brew install --cask docker    # optional
```

## 1.  Install Quell

Until Quell is published to PyPI you install from the local source tree.
The recommended approach is [pipx](https://pipx.pypa.io) so the `quell`
command lands on your global `PATH` without touching your system
Python:

```bash
# one-time
brew install pipx
pipx ensurepath
exec $SHELL -l           # reload the shell so PATH picks up ~/.local/bin

# install quell
pipx install /Users/you/path/to/quell   # use YOUR checkout path

# verify
quell --version
quell --help
```

If `quell --version` prints `quell 0.2.0` you're done with install.

Prefer a venv or editable install?  See
[Installation](installation.md) for the full matrix.

## 2.  Initialise a project

`cd` into the project you want Quell to watch — this is usually one of
your application repos, not the Quell repo itself — and run:

```bash
cd ~/src/my-app
quell init
```

The wizard asks you:

* **Project path** (default: current directory).
* **LLM provider** — Anthropic, OpenAI, Google Gemini, Ollama, or a
  custom LiteLLM model string.  Pick the one you already have an API
  key for.
* **API key** — typed once; stored in the OS keychain (macOS Keychain,
  GNOME Keyring, Windows Credential Manager), never in TOML.
* **Monitor source** — by default a local log file; optionally one of
  the three remote adapters (HTTP poll, Vercel, Sentry).
* **Log path** (if you picked a local file monitor).

When it finishes you'll have:

```
my-app/
├── .quell/
│   └── config.toml      # non-secret config
└── .gitignore           # .quell/ automatically added
```

Open `.quell/config.toml` to sanity-check what the wizard wrote.  See
[Configuration](configuration.md) if you want to edit it manually.

## 3.  Verify the environment

```bash
quell doctor
```

You should see a table with ✓ marks next to each check:

```
┌─────────────────────────┬────┬──────────────────────────────┐
│ Check                   │ OK │ Detail                       │
├─────────────────────────┼────┼──────────────────────────────┤
│ Python ≥ 3.12           │ ✓  │ 3.12.12                      │
│ git installed           │ ✓  │ git found on PATH            │
│ Docker running          │ ✓  │ Docker Engine 27.3.1         │
│ Config loads            │ ✓  │ .quell/config.toml parsed    │
│ API key in keyring      │ ✓  │ anthropic key present        │
└─────────────────────────┴────┴──────────────────────────────┘
```

A red ✗ points you at exactly what to fix.  The most common problems
are covered in [Troubleshooting](troubleshooting.md).

## 4.  Your first investigation

The simplest way to see Quell work is to point it at a local log file
and append an error line.

### 4.1.  Dry-run with the bundled sample log

```bash
# From the quell repo itself:
cp /Users/you/path/to/quell/fixtures/sample_logs/app_error.log /tmp/demo.log
```

Edit `.quell/config.toml` of some project to watch that file:

```toml
[[monitors]]
type = "local-file"
path = "/tmp/demo.log"
format = "regex"
pattern = "ERROR"
```

Then:

```bash
quell watch
```

You should see log lines like:

```
2026-04-20 10:02:45 | INFO  | agent_loop start: agent=incident_commander ...
2026-04-20 10:02:45 | INFO  | launching investigation for incident inc_... (2 skills)
2026-04-20 10:02:47 | INFO  | agent_loop finished via finish_incident after 3 iterations
```

Hit `Ctrl-C` to stop the watch loop.

### 4.2.  Inspect what Quell found

```bash
quell history              # most recent incidents
quell show <incident-id>   # full detail on one
quell stats                # totals, MTTR, top signatures
```

## 5.  Next steps

- Read the [architecture overview](architecture.md) to understand the
  pieces you just ran.
- Browse [`quell/skills/`](../quell/skills/) — the bundled runbooks
  that get injected into the agent's system prompt when their triggers
  match an incident.  Write your own by following
  [Extending Quell](extending.md).
- Plug Quell into a real monitor (Sentry, Vercel, or an HTTP probe) by
  editing `.quell/config.toml` directly — see
  [Configuration](configuration.md).

If anything in this guide didn't work, please file an issue with the
exact command output; see
[Troubleshooting](troubleshooting.md) first for the quick fixes.
