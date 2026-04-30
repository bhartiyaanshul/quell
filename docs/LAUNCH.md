# Phase 16 — Public launch checklist

Phase 16 is deliberately **not** automated: it requires human judgment
calls, real hardware for cross-platform smoke tests, and timing-sensitive
community actions.  This doc is the runbook.

## Pre-launch — verify the package is shippable

- [ ] `poetry run quell --help` works cleanly from a fresh
      `pipx install quell`.
- [ ] `quell init` wizard runs end-to-end on **macOS**, **Linux**, and
      **Windows**.  (Use a VM or CI matrix — do not skip any OS.)
- [ ] `quell doctor` passes with a real API key configured.
- [ ] `quell watch` runs against a local log file and spawns a real
      agent.  Confirm the LLM is actually called (check the bill at
      the end).
- [ ] Docker sandbox image has been built locally and pushed to
      `ghcr.io/bhartiyaanshul/quell-sandbox:latest`.  The image's
      tool server responds to `GET /health` within the 30-second
      runtime timeout.

## Documentation

- [ ] README has a 90-second demo video linked above the fold.
- [ ] Architecture diagram (mermaid or hand-drawn) is rendered in the
      README.
- [ ] `CHANGELOG.md` notes the 0.1.0 release.
- [ ] `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` are
      present and reviewed.

## Infrastructure

- [ ] `quell.anshulbuilds.xyz` DNS record live — either redirects to
      the GitHub repo or serves a one-pager.
- [ ] Discord server created; invite link pinned in the README.
- [ ] PyPI account + trusted-publishing configured so tags push
      releases automatically (see `.github/workflows/release.yml`).

## Launch day

- [ ] Cut the `v0.1.0` git tag; CI publishes to PyPI and creates the
      GitHub release.
- [ ] Verify `pipx install quell==0.2.0` on a clean machine.
- [ ] Submit HN post: **"Show HN: Quell — open-source autonomous on-call
      engineer"**.  Time around 9am PT Tuesday through Thursday.
- [ ] X announcement thread with the demo video embedded.
- [ ] Product Hunt launch (schedule for the day after HN so buzz
      compounds).
- [ ] Be actively available in the Discord and GitHub issues for the
      first 48 hours — response time matters more than anything else
      in the launch window.

## Post-launch follow-up

- [ ] Triage every issue and discussion within 24 hours.
- [ ] Ship a 0.1.1 patch within the first week addressing the three
      highest-signal bug reports.
- [ ] Write a retrospective blog post at the two-week mark summarising
      usage data (opt-in only) and roadmap adjustments.
