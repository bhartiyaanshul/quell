# Quell documentation

New to Quell?  Start with [**Getting started**](getting-started.md) — it
walks from zero to a running investigation in ten minutes.

## Guides

| Guide | When to read it |
|-------|-----------------|
| [Getting started](getting-started.md) | First run — install, configure, watch.  **Start here.** |
| [Installation](installation.md) | Pick between venv, pipx, and editable dev installs.  Covers the "command not found" issue. |
| [Commands](commands.md) | Reference for every `quell <subcommand>` — flags, examples, exit codes. |
| [Configuration](configuration.md) | Full TOML reference for `.quell/config.toml`. |
| [Architecture](architecture.md) | How monitors, detector, agents, tools, sandbox fit together. |
| [Extending Quell](extending.md) | Add a new skill (markdown runbook) or a new tool. |
| [Troubleshooting](troubleshooting.md) | Common errors and fixes. |
| [Launch checklist](LAUNCH.md) | Phase 16 — manual steps before publishing Quell itself. |

## The short version

```bash
# Install (one-time, from a fresh clone of this repo)
pipx install /Users/you/path/to/quell     # or: python3.12 -m venv .venv && .venv/bin/pip install -e .

# Configure
quell init       # interactive wizard — writes .quell/config.toml + stores API key in keyring
quell doctor     # verifies Python, git, Docker, and your API key

# Run
quell watch      # start monitor → detector → agent investigation loop

# Inspect
quell history    # recent incidents
quell show <id>  # one incident's detail
quell stats      # totals, MTTR, top signatures
```

For any step that didn't work the way you expected, see
[Troubleshooting](troubleshooting.md).
