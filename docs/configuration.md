# Configuration reference

Quell is configured via TOML files validated against a Pydantic v2
schema (`quell.config.schema.QuellConfig`).  Two files are consulted at
startup, merged, and then validated:

1. **Global:** `~/.config/quell/config.toml` (macOS/Linux) or
   `%APPDATA%\quell\config.toml` (Windows).  Holds defaults you want
   applied to every project.  Optional.
2. **Local:** `.quell/config.toml` at the project root.  Overrides the
   global file on a per-project basis.  Created by `quell init`.

Anything not listed in either file uses the built-in defaults from the
schema.

## Minimal example

```toml
# .quell/config.toml
repo_path = "."

[llm]
model = "anthropic/claude-haiku-4-5"

[[monitors]]
type = "local-file"
path = "/var/log/my-app/error.log"
format = "regex"
pattern = "ERROR|CRITICAL"
```

The API key for the LLM is **not** in this file — it lives in the OS
keychain, injected at load time.

---

## Top-level fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repo_path` | `str` | `"."` | Directory Quell is watching.  Relative paths resolve against the project root. |
| `monitors` | `list` | `[]` | One or more monitor configs.  The watch loop uses the first entry. |
| `notifiers` | `list` | `[]` | (Reserved) notifiers for future Slack / Discord / Telegram integrations. |
| `llm` | table | see below | LLM provider + model selection. |
| `sandbox` | table | see below | Docker sandbox image + resource limits. |

---

## `[llm]` — LLM provider

```toml
[llm]
model = "anthropic/claude-haiku-4-5"
reasoning_effort = "medium"     # "low" | "medium" | "high"
max_context_tokens = 100000
# api_base = "http://localhost:11434"   # only for local providers like Ollama
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | `str` | `"anthropic/claude-haiku-4-5"` | Any [LiteLLM model string](https://docs.litellm.ai/docs/providers).  Pattern: `"<provider>/<model>"`. |
| `api_base` | `str \| null` | `null` | Override endpoint — e.g. `"http://localhost:11434"` for Ollama. |
| `reasoning_effort` | `"low" \| "medium" \| "high"` | `"medium"` | Hint for reasoning-capable models. |
| `max_context_tokens` | `int` | `100_000` | Triggers history compression above this threshold. |
| `api_key` | (never in TOML) | — | Loaded from the OS keychain using the provider prefix. |

The API key is looked up by the **provider prefix** of `model`.  If
`model = "openai/gpt-4o"`, Quell reads the `openai` secret from your
keychain.

### Switching providers

```toml
[llm]
model = "openai/gpt-4o"
```

then store your key once:

```bash
python3 -c "from quell.utils.keyring_utils import set_secret; set_secret('openai', input('key: '))"
```

---

## `[[monitors]]` — event sources

Quell supports four monitor types.  Each is an inline-tagged Pydantic
variant — the `type = "..."` key picks the discriminator.

### `local-file`

Tails a log file and emits an event per new line.

```toml
[[monitors]]
type = "local-file"
path = "/var/log/my-app/error.log"
format = "regex"                 # "json" | "regex"
pattern = "ERROR|CRITICAL"       # required when format == "regex"
```

| Field | Required | Description |
|-------|----------|-------------|
| `path` | ✓ | Absolute path to the log file. |
| `format` | | `"json"` treats each line as JSON; `"regex"` matches `pattern`. |
| `pattern` | When `format = "regex"` | Python regex compiled once. |

### `http-poll`

Polls an HTTP endpoint; emits an event when the status code is wrong
or the request times out.

```toml
[[monitors]]
type = "http-poll"
url = "https://my-app.com/health"
interval_seconds = 30
timeout_seconds = 10
expected_status = 200
```

### `vercel`

Polls the Vercel Deployments API and streams logs.

```toml
[[monitors]]
type = "vercel"
project_id = "prj_abc123..."
interval_seconds = 60
```

API token: stored in the OS keychain under the `vercel` key.

### `sentry`

Polls the Sentry Issues API.

```toml
[[monitors]]
type = "sentry"
project_slug = "my-app"
organization_slug = "acme"
interval_seconds = 60
```

API token: stored in the OS keychain under the `sentry` key.

---

## `[sandbox]` — Docker runtime

Controls the sandbox container spawned per investigation.

```toml
[sandbox]
image = "ghcr.io/bhartiyaanshul/quell-sandbox:latest"
idle_timeout_seconds = 600
network_whitelist = []    # empty = default isolation

[sandbox.limits]
memory_mb = 2048
cpus = 2.0
disk_gb = 10
```

| Field | Default | Notes |
|-------|---------|-------|
| `image` | `ghcr.io/bhartiyaanshul/quell-sandbox:latest` | Any OCI image with Quell's tool server baked in. |
| `idle_timeout_seconds` | 600 | How long an idle sandbox survives before being destroyed. |
| `network_whitelist` | `[]` | (Reserved) allow-list of domains reachable from inside the sandbox. |
| `limits.memory_mb` | 2048 | Hard memory cap passed as `--memory`. |
| `limits.cpus` | 2.0 | Fractional CPUs passed as `--cpus`. |
| `limits.disk_gb` | 10 | (Reserved) disk size for the overlay. |

---

## Where secrets live

No secret ever belongs in TOML.  The loader injects them from the OS
keychain at startup:

| Keyring entry | Source |
|---------------|--------|
| `anthropic` / `openai` / `google` / `ollama` / custom | LLM provider, matched against the `llm.model` prefix. |
| `vercel` | Vercel API token (when a `vercel` monitor is configured). |
| `sentry` | Sentry API token. |
| `slack` / `discord` / `telegram` | Notifier webhook URLs / bot tokens (reserved). |

You can set these outside the wizard with the `keyring` CLI:

```bash
python3 -c "from quell.utils.keyring_utils import set_secret; set_secret('anthropic', input('key: '))"
```

On macOS you can also inspect or edit them in `Keychain Access.app`
under the `quell-agent` service.
