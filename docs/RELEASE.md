# Releasing Quell

Quell ships through five channels and one tag push fans out to all of
them. This page is the runbook.

## One-time setup

These steps are required once per channel, before the first release.
Skip any channel you don't want to publish on — the matching CI job
will simply log a warning and exit cleanly when its secret is missing.

| Channel | What to set up | Where |
|---------|----------------|-------|
| **PyPI** | Generate an [API token](https://pypi.org/manage/account/token/) scoped to `quell-agent`. | Add as `PYPI_TOKEN` repository secret. |
| **npm** | Create an npm account; generate an "Automation" access token. | Add as `NPM_TOKEN` repository secret. |
| **Homebrew** | Create the empty repo `bhartiyaanshul/homebrew-quell`. Generate a fine-grained PAT with `Contents: write` on that repo. | Add as `HOMEBREW_TAP_TOKEN` repository secret. |
| **Prebuilt binaries** | Nothing — `build-binaries.yml` uses the default `GITHUB_TOKEN`. | — |
| **curl `install.sh`** | Nothing — it lives at the repo root and is fetched directly from GitHub. | — |

## Cutting a release

1. **Pick a version.** Decide the new semver string, e.g. `0.3.0`.

2. **Bump every version string in one shot:**

   ```bash
   python scripts/check_versions.py --bump 0.3.0
   ```

   This rewrites `pyproject.toml`, `quell/version.py`,
   `packaging/npm/package.json`, and `packaging/homebrew/quell.rb`
   so they stay in lockstep. CI fails the release if they don't.

3. **Open a PR to `develop`** with the bump, get it merged, then
   merge `develop` → `main` as usual.

4. **Tag from `main`:**

   ```bash
   git checkout main && git pull
   git tag v0.3.0 && git push --tags
   ```

5. **Watch the Actions tab.** Three workflows light up on the tag:

   - `release.yml` → publishes to PyPI, creates the GitHub release,
     waits for binaries, publishes to npm, pushes the Homebrew formula.
   - `build-binaries.yml` → builds standalone binaries on
     macOS arm64 / Linux x86_64 / Windows x86_64 and attaches each
     archive to the release.

6. **Verify each channel** on a clean machine (or VM):

   ```bash
   pipx install quell-agent==0.3.0           # PyPI
   npm i -g quell-agent@0.3.0                # npm
   brew install bhartiyaanshul/quell/quell    # Homebrew
   curl -fsSL https://github.com/bhartiyaanshul/quell/releases/latest/download/quell-$(uname -s)-$(uname -m).tar.gz | tar xz   # binary
   curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash   # curl-pipe
   ```

   Every channel should converge on the same `quell --version` output.

## Troubleshooting

**npm publish fails with "version already exists":** npm doesn't
allow republishing a tag — bump the patch version and redo the
release. Same for PyPI.

**Homebrew job hangs on "Resolve sdist url + sha256":** PyPI's JSON
API can lag the publish call by 60-90 seconds. The job retries for
five minutes; if it still fails, check
[pypi.org/pypi/quell-agent/json](https://pypi.org/pypi/quell-agent/json)
manually and re-run the workflow.

**npm postinstall fails with "HTTP 404":** the binary archive isn't
on the release yet. The `publish-npm` job waits up to 30 minutes for
all three archives; if `build-binaries.yml` is taking longer than
that, re-run `publish-npm` after the binaries finish.

**Versions out of sync:** run `python scripts/check_versions.py` —
it prints a table showing exactly which file is out of step.
