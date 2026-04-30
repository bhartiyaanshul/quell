# Troubleshooting

Common problems and the fastest fix for each.  If your issue isn't
listed, please open a GitHub issue with:

1. The command you ran.
2. The full output (including stderr).
3. `quell version`, `python3.12 --version`, and your OS.

---

## `zsh: command not found: quell`

Quell is installed but not on your `PATH`.

**Fix (recommended):** install via `pipx`, which puts `quell` in
`~/.local/bin`:

```bash
brew install pipx
pipx ensurepath
exec $SHELL -l                              # reload the shell
pipx install /Users/you/path/to/quell       # or the PyPI name, once published
```

**Fix (alternative):** run the binary directly out of the project
venv:

```bash
/path/to/quell/.venv/bin/quell init
```

See [Installation](installation.md) for all three supported paths.

---

## `quell doctor` reports Python version too old

You're on Python 3.11 or older.  Quell requires 3.12+.

```bash
brew install python@3.12                # macOS
# or use pyenv:
pyenv install 3.12.12
pyenv global 3.12.12

python3.12 --version                    # confirm
pipx reinstall quell --python python3.12
```

---

## `quell doctor` reports Docker not running

Either Docker Desktop isn't running, or Docker isn't installed.

```bash
# Check whether the daemon is up:
docker info

# macOS — start Docker Desktop:
open -a Docker
# then wait ~30s and re-run `quell doctor`
```

You can run `quell watch` without Docker for local-file monitor
scenarios, but real investigations sandboxed against untrusted code
need a running Docker daemon.

---

## `quell doctor` reports missing API key

Either the LLM `model` prefix doesn't match what's in your keychain, or
the key was never stored.

```bash
# Check what's in the keychain:
python3 -c "from quell.utils.keyring_utils import get_secret; print(get_secret('anthropic'))"

# Store a key:
python3 -c "from quell.utils.keyring_utils import set_secret; set_secret('anthropic', input('key: '))"
```

The lookup key comes from `llm.model` — e.g. `"openai/gpt-4o"` looks up
the `openai` keychain entry.

---

## `quell watch` exits immediately with "no monitors configured"

Your `.quell/config.toml` has no `[[monitors]]` entries.  Either run
`quell init` (which adds one) or add one manually:

```toml
[[monitors]]
type = "local-file"
path = "/var/log/my-app/error.log"
format = "regex"
pattern = "ERROR"
```

See [Configuration](configuration.md#monitors--event-sources).

---

## `quell watch` runs but never fires an investigation

Either nothing your monitor is reading matches the detector's rules,
or the signatures for repeated events are being deduplicated.

- `local-file` in `json` mode requires each line to parse as JSON.  Use
  `regex` if your logs are plaintext.
- The detector suppresses repeats of a signature it has already
  investigated — restart `quell watch` to clear the in-memory
  deduplication table.
- Set log level to DEBUG to see every event the monitor emits:

  ```bash
  QUELL_LOG_LEVEL=DEBUG quell watch
  ```

---

## `LLMError: LiteLLM call failed: ...`

The LLM provider returned an error.  Common causes:

- **Bad API key** — reset with `set_secret` (see above).
- **Rate limit (HTTP 429)** — back off, switch to a smaller model, or
  raise the request limit on your account.
- **Wrong model name** — LiteLLM validates the `model` string; see
  [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers)
  for the canonical list.
- **Custom endpoint unreachable** — if you set `llm.api_base`, make
  sure it's running and responds to `POST /v1/chat/completions`.

The full provider error is in the `LLMError` message, and the failed
investigation is recorded with `status="failed"` in the incident
database so you can see it via `quell history`.

---

## `fastapi.exceptions.HTTPException: 401` from the tool server

The sandbox's bearer token and the one the executor is posting don't
match.  This almost always means the sandbox container was started by
a previous process and orphaned.

```bash
docker ps --filter label=quell.agent_id     # list Quell-owned containers
docker rm -f <container-id>                 # force-remove
```

The next `quell watch` invocation will mint a fresh token and
container.

---

## Tests pass locally but CI fails

CI runs Python 3.12 on Linux.  Two things commonly differ:

- Timezone — every test that uses timestamps should create them in UTC
  (`datetime.now(UTC)`).  Local clocks in other zones cause flakes.
- Docker availability — runtime tests use a fake Docker SDK and do not
  require a daemon.  If a test is trying to hit `docker.from_env()`,
  it's missing the `client=fake` injection.

If neither explains it, paste the full CI output into an issue.

---

## "File too long" lint error when adding a big module

The project cap is 300 lines per file (see `CLAUDE.md`).  Split your
module along single-responsibility lines.  Examples:

- `quell/skills/` — split into `model.py`, `loader.py`, `selector.py`.
- `quell/agents/graph_tools.py` — one file per family of tools, if it
  grows further.

---

## "registered tool ... already exists" when running tests

You're importing a tool module at module load time while another
fixture clears the registry between tests.  Use
`register_builtin_tools()` from `quell.tools.builtins` in an autouse
fixture instead — it's idempotent:

```python
@pytest.fixture(autouse=True)
def _bootstrap_builtins():
    register_builtin_tools()
    yield
```

See the pattern in
[`tests/unit/test_builtin_tools.py`](../tests/unit/test_builtin_tools.py).
