export const REPO_URL = "https://github.com/bhartiyaanshul/quell";
export const REPO_RAW = "https://raw.githubusercontent.com/bhartiyaanshul/quell/main";
export const DOCS_URL = `${REPO_URL}/tree/main/docs`;
export const INSTALL_URL = `${REPO_RAW}/install.sh`;

export const INSTALL_COMMANDS = [
  {
    id: "curl",
    label: "curl",
    sublabel: "one-liner",
    command: `curl -fsSL ${INSTALL_URL} | bash`,
    hint: "Probes for a prebuilt binary, falls back to pipx + source. Today's default.",
  },
  {
    id: "npm",
    label: "npm",
    sublabel: "for JS devs",
    command: "npm i -g quell-agent",
    hint: "Postinstall hook downloads the native binary — zero Python needed.",
  },
  {
    id: "brew",
    label: "brew",
    sublabel: "macOS / Linux",
    command: "brew install bhartiyaanshul/quell/quell",
    hint: "Uses the Homebrew tap built from the PyPI release.",
  },
  {
    id: "pipx",
    label: "pipx",
    sublabel: "Python users",
    command: "pipx install quell-agent",
    hint: "Isolated Python environment under ~/.local — recommended if you already have pipx.",
  },
  {
    id: "binary",
    label: "binary",
    sublabel: "zero runtime",
    command: `curl -sSL https://github.com/bhartiyaanshul/quell/releases/latest/download/quell-$(uname -s)-$(uname -m).tar.gz | tar xz -C /usr/local/bin`,
    hint: "Prebuilt standalone binary for macOS (arm64/x64), Linux (x64), Windows (x64).",
  },
] as const;

export const FEATURES = [
  {
    title: "Draft PRs, never auto-merge",
    body: "Quell produces a structured report and draft PR. Humans always ship the fix. No silent changes, no 3am surprises.",
    icon: "git-pull-request",
  },
  {
    title: "Docker-sandboxed tools",
    body: "Every tool that touches code runs inside a Docker container with your workspace mounted read-only. Bearer-token auth per sandbox.",
    icon: "shield-check",
  },
  {
    title: "Bring your own model",
    body: "LiteLLM under the hood — OpenAI, Anthropic, Google, Ollama, anything. Swap models with one line of TOML.",
    icon: "brain",
  },
  {
    title: "Multi-agent coordination",
    body: "The IncidentCommander spawns specialist subagents (log analyst, code detective, git historian) that work in parallel.",
    icon: "network",
  },
  {
    title: "19 skill runbooks built in",
    body: "Markdown + YAML runbooks for Stripe, OpenAI, DNS, SSL, memory, disk, deadlocks, Django/Flask/Rails/Spring/Express, Postgres, Redis, Docker, Kubernetes — auto-injected when triggers match.",
    icon: "book-open",
  },
  {
    title: "No telemetry by default",
    body: "Your code, your logs, your infrastructure — nothing leaves your machine unless you explicitly configure a remote endpoint.",
    icon: "lock",
  },
  {
    title: "Slack, Discord, Telegram",
    body: "Fan an investigation summary out to every channel in parallel the moment the agent finishes. Verify webhooks with quell test-notifier.",
    icon: "bell",
  },
  {
    title: "Web dashboard + replay",
    body: "quell dashboard boots a local Next.js + FastAPI UI; quell replay <id> prints the same event timeline in your terminal. Read-only.",
    icon: "layout-dashboard",
  },
  {
    title: "Cost tracking + budgets",
    body: "Per-model rate card across Anthropic / OpenAI / Google / Ollama. Every run records tokens + USD; max_cost_usd halts a runaway investigation before it lights money on fire.",
    icon: "wallet",
  },
] as const;

export const PIPELINE_STEPS = [
  {
    title: "Monitor",
    body: "Tail a log file, poll an HTTP endpoint, or stream Vercel / Sentry events.",
    tag: "quell/monitors",
  },
  {
    title: "Detect",
    body: "Signature + 24h rolling baseline — flag what's new, spiking, or critical.",
    tag: "quell/detector",
  },
  {
    title: "Investigate",
    body: "IncidentCommander reads logs, greps code, traces git history, and reasons.",
    tag: "quell/agents",
  },
  {
    title: "Report + Notify",
    body: "Structured root-cause + draft PR; fanned to Slack / Discord / Telegram in parallel.",
    tag: "quell/notifiers",
  },
] as const;

export const TERMINAL_LINES = [
  { prompt: "~/src/my-app", cmd: "quell watch", output: null },
  {
    prompt: null,
    cmd: null,
    output: "10:02:45 INFO  monitor: tailing /var/log/my-app/error.log",
  },
  {
    prompt: null,
    cmd: null,
    output:
      "10:02:47 ERROR TypeError: Cannot read properties of null (reading 'id')",
  },
  {
    prompt: null,
    cmd: null,
    output: "10:02:47 INFO  detector: new signature 7a9e42f8 — severity=high",
  },
  {
    prompt: null,
    cmd: null,
    output: "10:02:47 INFO  commander: spawning incident_commander (5 skills)",
  },
  {
    prompt: null,
    cmd: null,
    output: "10:02:49 INFO  tool: code_read src/checkout.ts lines 40-50",
  },
  {
    prompt: null,
    cmd: null,
    output: "10:02:52 INFO  tool: git_blame src/checkout.ts:42",
  },
  {
    prompt: null,
    cmd: null,
    output: "10:02:58 INFO  agent: finish_incident — null-deref on order.user",
  },
  {
    prompt: null,
    cmd: null,
    output: "\u2713 incident inc_a1b2c3 resolved in 13s",
  },
] as const;
