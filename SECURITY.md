# Security policy

## Supported versions

Quell is pre-1.0; only the latest minor release receives security fixes.

| Version | Supported       |
|---------|-----------------|
| 0.1.x   | ✅ current line  |
| < 0.1   | ❌ unsupported   |

## Reporting a vulnerability

**Please do not file a public GitHub issue for security problems.**

Use GitHub's private Security Advisory flow:

- Open [**Report a vulnerability**](https://github.com/bhartiyaanshul/quell/security/advisories/new)
  on the repo.
- Include: a description of the issue and its impact, steps to reproduce
  (or a proof of concept), and your preferred disclosure timeline.

We will acknowledge your report within three business days and aim to
ship a fix within 14 days for high-severity issues.  Critical issues
that could leak user code or LLM credentials are prioritised.

## Security posture

A few specific points that follow from Quell's design:

- Every tool that touches code or the filesystem runs inside a
  Docker-based sandbox (see `quell/runtime/docker_runtime.py`).  The
  sandbox mounts the user's workspace read-only and enforces per-sandbox
  bearer-token authentication on its tool server.
- LLM API keys are stored in the OS keychain (via `keyring`) and never
  written to TOML configs.
- Quell never auto-merges code changes.  All PRs it proposes are draft
  and require human review.
- No telemetry is collected by default.  The "cloud" surface is
  strictly opt-in.

If you discover a case that violates any of the above guarantees please
treat it as a security issue and report it per the process above.
