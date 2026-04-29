# Packaging

Distribution matrix.  Every channel ships the same Quell build — pick
whichever your users' environment prefers.

| Channel | Status | User install command | Source |
|---------|--------|----------------------|--------|
| **npm** | ⏳ ready (waits for first release) | `npm i -g quell-agent` | [`npm/`](npm/) |
| **Prebuilt binary** | ⏳ ready (waits for first release) | `curl -sSL https://github.com/bhartiyaanshul/quell/releases/latest/download/quell-$(uname -s)-$(uname -m).tar.gz \| tar xz` | [`pyinstaller/quell.spec`](pyinstaller/quell.spec) |
| **curl install.sh** | ✅ live | `curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh \| bash` | [`../install.sh`](../install.sh) |
| **Homebrew tap** | ⏳ ready (waits for PyPI) | `brew install bhartiyaanshul/quell/quell` | [`homebrew/quell.rb`](homebrew/quell.rb) |
| **PyPI** | ⏳ wired in `release.yml` (waits for first tag) | `pipx install quell-agent` | `.github/workflows/release.yml` |
| **Docker sandbox** | ⏳ manual push in Phase 16 | `docker pull ghcr.io/bhartiyaanshul/quell-sandbox` | — |

"Ready" means the recipe is committed; "live" means users can run it
today.  Everything marked ⏳ flips to ✅ the moment the first `v0.1.0`
tag is pushed and `release.yml` + `build-binaries.yml` run.

**See [`docs/RELEASE.md`](../docs/RELEASE.md)** for the end-to-end
release runbook (one-time secret setup, version-bump, tag push,
verification).

---

## How one tag push cascades through every channel

```
           ┌─────────────────────────────┐
           │  git tag v0.1.0 && git push │
           └──────────────┬──────────────┘
                          │
           ┌──────────────┼──────────────────────────────┐
           ▼              ▼                              ▼
   release.yml     build-binaries.yml             (manual, once)
    (PyPI + gh        (4 platforms →                  ▼
     release)       attached to gh release)    publish npm wrapper
           │              │                              │
           ▼              ▼                              ▼
  pipx install   curl | tar xz                 npm i -g quell-agent
  quell-agent    prebuilt binary               (postinstall fetches
                 on user's PATH                 the same binary)
```

All user-facing channels converge on the same sha-pinned artefacts.

---

## Per-channel details

### `install.sh` (curl-pipe, live today)

The canonical installer.  Probes for a prebuilt binary first — once
the first release exists, installs are instant (one curl + one tar,
no Python/pipx).  Falls back to pipx + source when the binary isn't
published yet.  Safe to re-run for upgrades.

```bash
curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash
curl -fsSL … | bash -s -- --yes          # non-interactive
curl -fsSL … | bash -s -- --dev          # editable dev install (for contributors)
curl -fsSL … | bash -s -- --from-source  # skip the prebuilt-binary fast path
curl -fsSL … | bash -s -- --ref=v0.1     # pin to a tag
```

Source: [`../install.sh`](../install.sh).

### `pyinstaller/quell.spec` (standalone binary)

Builds a self-contained directory — `dist/quell/` — containing the
`quell` executable plus the Python runtime and every dep.  Users
install zero runtimes.

```bash
pip install pyinstaller
pyinstaller packaging/pyinstaller/quell.spec --clean --noconfirm
./packaging/pyinstaller/dist/quell/quell --help     # works without Python installed
```

Verified locally — produces a ~25 MB binary that passes `--version`
and `--help`.  CI (`.github/workflows/build-binaries.yml`) runs the
same command on four runners (macOS arm64 + x86_64, Linux x86_64,
Windows x86_64) on every tag push and uploads each archive to the
matching GitHub release.

### `npm/` (wrapper package)

Tiny JS package whose `postinstall` hook downloads the prebuilt
binary for the current platform and whose `bin` shim forwards
stdio/signals.  Kept at version parity with Quell.

```bash
cd packaging/npm
npm publish --access public    # after bumping "version" to match the tag
```

Publishes to [`npmjs.com/package/quell-agent`](https://www.npmjs.com/package/quell-agent).
Users then install with:

```bash
npm i -g quell-agent
```

### `homebrew/quell.rb` (Homebrew tap)

Template formula.  Fill in the `url` / `sha256` / `resource` blocks
after the first PyPI release and commit to a `bhartiyaanshul/homebrew-tap`
(or `homebrew-quell`) repo.  Users then install with:

```bash
brew install bhartiyaanshul/quell/quell
# or
brew tap bhartiyaanshul/quell && brew install quell
```

### PyPI (via `release.yml`)

Already wired.  On `v*` tag push:

1. Runs the full test suite on Python 3.12.
2. `poetry build` → wheel + sdist.
3. `poetry publish` using the `POETRY_PYPI_TOKEN_PYPI` secret.
4. Creates the GitHub release with auto-generated notes + dist
   artefacts.

Users then install with:

```bash
pipx install quell-agent       # recommended, isolated
pip  install --user quell-agent  # alternative, if pipx isn't available
```

### Docker sandbox image

Separate from the user-facing install — this is the image Quell
*uses* to run tools in, not the image users *install* Quell as.
Build + push is deferred to Phase 16 (see
[`../docs/LAUNCH.md`](../docs/LAUNCH.md)).

---

## Release checklist

The full end-to-end runbook is [`docs/RELEASE.md`](../docs/RELEASE.md).
The two-line summary:

1. `python scripts/check_versions.py --bump X.Y.Z` — bumps every version
   string in lockstep.
2. Tag from `main`: `git tag vX.Y.Z && git push --tags` — CI cascades
   to PyPI, npm, Homebrew, and the prebuilt binaries automatically.
