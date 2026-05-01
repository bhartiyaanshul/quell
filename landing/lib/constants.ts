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
    command: "npm i -g quell",
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
    command: "pipx install quell",
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
    body: "Fan an investigation summary out to every channel in parallel the moment the agent finishes. Verify webhooks with quell notifier test.",
    icon: "bell",
  },
  {
    title: "Web dashboard + replay",
    body: "quell dashboard boots a local Next.js + FastAPI UI; quell incident replay <id> prints the same event timeline in your terminal. Read-only.",
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

/**
 * Per-skill data for the SkillsShowcase. Each skill has:
 *  - accent: tailwind text-color class for badges/icons (gives each card its
 *    own visual identity — they used to all look identical at thumbnail size)
 *  - icon: Lucide icon name resolved in SkillsShowcase
 *  - frames: three mini-mocks rendered as HTML/CSS (no images). The hover
 *    cycler steps terminal → analysis → diff.
 */
export const SKILLS_SHOWCASE = [
  {
    id: "postgres-deadlock",
    title: "Postgres deadlock",
    tags: ["pg_locks", "psql", "PgBouncer"],
    year: "2026",
    description:
      "Detects two transactions blocking each other; pulls the deadlock graph + offending statements; drafts a retry-with-backoff patch.",
    accent: "sky",
    icon: "database",
    frames: {
      terminal: {
        cmd: "psql -c 'SELECT * FROM pg_locks'",
        lines: [
          { kind: "err", text: "ERROR  deadlock detected (txn 4218 ↔ 4219)" },
          { kind: "info", text: "detector: skill=postgres_deadlock matched" },
          { kind: "muted", text: "tool: pg_stat_activity (42ms)" },
        ],
      },
      analysis: {
        title: "deadlock graph",
        bullets: [
          "txn 4218 → row id=$1",
          "txn 4219 → row id=$2",
          "→ sort ids before UPDATE",
        ],
      },
      diff: {
        file: "orders_repo.py",
        lines: [
          { kind: "rm", text: "for oid in ids:" },
          { kind: "add", text: "for oid in sorted(ids):" },
          { kind: "add", text: "  for attempt in range(3):" },
          { kind: "add", text: "    backoff(attempt)" },
        ],
      },
    },
  },
  {
    id: "stripe-webhook",
    title: "Stripe webhook failure",
    tags: ["webhooks", "Stripe API", "signature"],
    year: "2026",
    description:
      "Replays the last 50 failed webhook deliveries, classifies signature vs handler errors, and proposes the missing endpoint or signing-secret rotation.",
    accent: "violet",
    icon: "credit-card",
    frames: {
      terminal: {
        cmd: "stripe events list --type=payment_intent",
        lines: [
          { kind: "err", text: "ERROR  POST /api/stripe → 400 (50 last hour)" },
          { kind: "info", text: "detector: skill=stripe_webhook matched" },
          { kind: "muted", text: "47/50 share signature mismatch" },
        ],
      },
      analysis: {
        title: "root cause",
        bullets: [
          "STRIPE_WEBHOOK_SECRET rotated 2026-04-22",
          "deploy didn't pull new env",
          "→ rotate or pin signing secret",
        ],
      },
      diff: {
        file: "api/stripe/route.ts",
        lines: [
          { kind: "rm", text: "const sig = req.headers['stripe-sig']" },
          { kind: "add", text: "const sig = req.headers.get('stripe-sig')" },
          { kind: "add", text: "verify(req.body, sig, env.STRIPE_SECRET)" },
        ],
      },
    },
  },
  {
    id: "oom-kill",
    title: "OOM kill (Linux + container)",
    tags: ["dmesg", "cgroups", "metrics"],
    year: "2026",
    description:
      "Correlates dmesg OOM lines with cgroup limits and process RSS history; identifies the leaking allocator and suggests a memory-limit bump or fix.",
    accent: "rose",
    icon: "hard-drive",
    frames: {
      terminal: {
        cmd: "dmesg | grep -i oom",
        lines: [
          { kind: "err", text: "Out of memory: Killed process 8421 (node)" },
          { kind: "info", text: "cgroup: limit=512MiB rss=518MiB" },
          { kind: "muted", text: "tool: rss_history --pid=8421" },
        ],
      },
      analysis: {
        title: "leak profile",
        bullets: [
          "RSS climb 2.1MiB/min for 4h",
          "GC pauses spike at /api/upload",
          "→ stream uploads, don't buffer",
        ],
      },
      diff: {
        file: "api/upload.ts",
        lines: [
          { kind: "rm", text: "const buf = await readAll(req.body)" },
          { kind: "add", text: "await pipeline(req.body, writeStream)" },
          { kind: "add", text: "// memory now O(chunk), not O(file)" },
        ],
      },
    },
  },
  {
    id: "ssl-expiry",
    title: "SSL certificate expiry",
    tags: ["openssl", "ACME", "Let's Encrypt"],
    year: "2026",
    description:
      "Probes every public endpoint for cert chain + expiry; spots near-expiry certs, points to the renewal job, and drafts a one-line cron fix.",
    accent: "emerald",
    icon: "lock",
    frames: {
      terminal: {
        cmd: "openssl s_client -connect api.example.com:443",
        lines: [
          { kind: "warn", text: "WARN   cert expires in 4 days (api.*)" },
          { kind: "info", text: "detector: skill=ssl_expiry matched" },
          { kind: "muted", text: "renewal cron last run: 31 days ago" },
        ],
      },
      analysis: {
        title: "renewal chain",
        bullets: [
          "certbot installed, cron disabled",
          "deploy 2026-03-30 wiped /etc/cron.d",
          "→ restore cron + force renew now",
        ],
      },
      diff: {
        file: "infra/cron.tf",
        lines: [
          { kind: "add", text: '+ resource "cron" "certbot" {' },
          { kind: "add", text: '+   schedule = "0 3 * * *"' },
          { kind: "add", text: '+   command  = "certbot renew"' },
          { kind: "add", text: "+ }" },
        ],
      },
    },
  },
  {
    id: "k8s-crashloop",
    title: "K8s pod crashloop",
    tags: ["kubectl", "events", "probes"],
    year: "2026",
    description:
      "Runs kubectl describe/logs/events across the failing pod; isolates the failing container, surfaces the readiness probe diff, and drafts a manifest patch.",
    accent: "amber",
    icon: "boxes",
    frames: {
      terminal: {
        cmd: "kubectl describe pod api-7d49 -n prod",
        lines: [
          { kind: "err", text: "CrashLoopBackOff (restarts: 17)" },
          { kind: "info", text: "Readiness probe failed: 503 /healthz" },
          { kind: "muted", text: "tool: kubectl logs --previous" },
        ],
      },
      analysis: {
        title: "probe diff",
        bullets: [
          "/healthz boots in ~12s",
          "readiness initialDelay = 3s",
          "→ raise to 20s, add startup probe",
        ],
      },
      diff: {
        file: "k8s/api.yaml",
        lines: [
          { kind: "rm", text: "  initialDelaySeconds: 3" },
          { kind: "add", text: "  initialDelaySeconds: 20" },
          { kind: "add", text: "startupProbe:" },
          { kind: "add", text: "  failureThreshold: 30" },
        ],
      },
    },
  },
  {
    id: "openai-rate-limit",
    title: "OpenAI rate-limit storm",
    tags: ["LiteLLM", "retries", "queueing"],
    year: "2026",
    description:
      "Spots 429-burst patterns; correlates with deploy windows; suggests a token-bucket + provider-failover patch grounded in your existing client.",
    accent: "lime",
    icon: "zap",
    frames: {
      terminal: {
        cmd: "tail -f logs/api.log | grep 429",
        lines: [
          { kind: "err", text: "429 Too Many Requests (487 in 60s)" },
          { kind: "info", text: "burst correlates w/ deploy 14:02" },
          { kind: "muted", text: "tool: rate_card --provider=openai" },
        ],
      },
      analysis: {
        title: "queue strategy",
        bullets: [
          "spike: 12k req/min after deploy",
          "single-tenant token bucket",
          "→ failover to anthropic/* on 429",
        ],
      },
      diff: {
        file: "lib/llm.ts",
        lines: [
          { kind: "add", text: "const limiter = tokenBucket({ rps: 50 })" },
          { kind: "add", text: "providers: ['openai/*', 'anthropic/*']" },
          { kind: "rm", text: "await openai.chat(...)" },
          { kind: "add", text: "await limiter.run(() => llm.chat(...))" },
        ],
      },
    },
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
