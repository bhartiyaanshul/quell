# Quell

> **Your production's autonomous on-call.**

[![Work In Progress](https://img.shields.io/badge/status-WIP-orange)](https://github.com/quellhq/quell)
[![Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

Quell is an open-source multi-agent system that watches your production systems, investigates incidents via specialized AI agents running in a Docker sandbox, and opens a draft PR with a fix and regression test — all while you sleep. A root `IncidentCommander` agent reasons about the problem via LiteLLM, spawns parallel specialist subagents (log analyst, code detective, git historian, test engineer, fix author), and coordinates them through a shared agent graph. Every fix is a draft PR; Quell never auto-merges.

---

> 🚧 **This project is under active construction.** Phase 1 of 16 in progress.
> See the [master plan](docs/MASTER_PLAN.md) for the full architecture and roadmap.

---

## Quick start (coming in Phase 3)

```bash
pipx install quell-agent
quell init     # interactive setup wizard
quell doctor   # verify everything is configured
quell watch    # start watching production
```

## License

[Apache 2.0](./LICENSE) — built by [Anshul Bhartiya](https://x.com/Bhartiyaanshul)
