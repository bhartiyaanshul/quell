# `quell` on npm

Thin wrapper that installs the native Quell binary on `npm install` so
that JS-oriented developers can install without ever touching Python:

```bash
npm i -g quell
quell --help
```

## How it works

1. `npm install` runs `scripts/download.js` (the `postinstall` hook).
2. The script fetches the platform-matching `quell-<os>-<arch>.tar.gz`
   asset from the GitHub release matching this package's version and
   extracts it to `~/.cache/quell-npm/<version>/`.
3. `bin/quell.js` — the file npm adds to the user's `PATH` as `quell`
   — is a tiny Node shim that `spawn`s the extracted binary with the
   user's arguments and forwards stdio + signals.

No Python, no pipx, no venv on the user's machine.

## Publish flow

1. Cut a git tag `vX.Y.Z` on the Quell repo.  The `build-binaries.yml`
   workflow runs and attaches `quell-Darwin-arm64.tar.gz` etc. to the
   GitHub release.
2. Bump `"version": "X.Y.Z"` in this package's `package.json` to match
   the tag.
3. From this directory: `npm publish --access public`.

## Troubleshooting

- **"Unsupported platform"** — we currently ship macOS (arm64, x64),
  Linux (x64), and Windows (x64).  Other platforms can install via
  `pipx install quell` or the curl-pipe installer.
- **"Binary not found" at runtime** — the postinstall failed.  Re-run
  `npm install -g quell` with `--loglevel=verbose` to see why.
