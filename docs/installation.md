# Installation

Three supported install paths.  Pick the one that matches how you plan
to use Quell.

| Use case | Install |
|----------|---------|
| Day-to-day use, want `quell` on `PATH` everywhere | [pipx](#pipx-recommended) |
| Trying it out briefly, don't want a system-wide install | [Project-local venv](#project-local-venv) |
| Contributing to Quell itself | [Editable dev install](#editable-dev-install) |

---

## pipx (recommended)

`pipx` isolates each Python CLI tool in its own venv and symlinks its
entry point into `~/.local/bin`, which `pipx ensurepath` adds to your
shell's `PATH`.

```bash
# 1. Install pipx (macOS shown; Linux: `apt install pipx` or your distro equivalent)
brew install pipx
pipx ensurepath

# 2. Reload the shell so the new PATH entry takes effect.
exec $SHELL -l

# 3. Install quell from a local checkout.
pipx install /Users/you/path/to/quell

# 4. Sanity-check.
quell --version
which quell                # → ~/.local/bin/quell
```

After Quell is published to PyPI the last step becomes:

```bash
pipx install quell-agent
```

### Upgrading

From a local checkout:

```bash
pipx install /Users/you/path/to/quell --force
```

From PyPI (after publish):

```bash
pipx upgrade quell-agent
```

### Uninstalling

```bash
pipx uninstall quell-agent
```

---

## Project-local venv

Useful if you don't want `quell` on your global `PATH` and you're happy
to activate a venv in the terminal where you want it.

```bash
cd /Users/you/path/to/quell
python3.12 -m venv .venv
.venv/bin/pip install -e .
```

Then either:

```bash
source .venv/bin/activate    # `quell` is now on PATH in THIS shell
quell init
deactivate                   # to exit the venv
```

…or call the binary directly without activating:

```bash
.venv/bin/quell init
```

---

## Editable dev install

For contributing.  Installs Quell + all dev dependencies (`pytest`,
`ruff`, `mypy`) and keeps the source mutable so edits take effect
immediately.

```bash
cd /Users/you/path/to/quell
poetry install
# or, without poetry:
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pip install pytest pytest-asyncio pytest-cov ruff mypy
```

Run the test suite to confirm everything works:

```bash
poetry run pytest -q
# or:
.venv/bin/pytest -q
```

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full dev loop and
the stop-gate commands (`ruff`, `mypy`, `pytest`).

---

## Runtime extras

- **Docker** — required for real sandboxed investigations.  Not
  required for unit tests or the "dry run" walkthrough in
  [Getting started](getting-started.md).  Install
  [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or
  `docker.io` on Linux) and make sure `docker info` prints a server
  version.
- **ripgrep** (`rg`) — speeds up the `code_grep` tool.  Quell falls
  back to plain `grep -rn` if `rg` isn't present, so this is optional.
  Install with `brew install ripgrep`.

---

## Where does Quell store things?

Quell follows the [XDG Base Directory](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
convention.

| Kind | macOS / Linux | Windows |
|------|---------------|---------|
| Non-secret config (global defaults) | `~/.config/quell/config.toml` | `%APPDATA%\quell\config.toml` |
| Per-project config (overrides global) | `.quell/config.toml` in the project | same |
| Incident database (SQLite) | `~/.local/share/quell/incidents.db` | `%LOCALAPPDATA%\quell\incidents.db` |
| API keys | OS keychain (macOS Keychain / GNOME Keyring / Windows Credential Manager) | |

Nothing is written outside those paths.  Nothing leaves your machine
unless you explicitly configure a remote monitor or LLM endpoint.
