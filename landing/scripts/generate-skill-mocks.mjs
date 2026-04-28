// Generates the 18 stylised SVG mock frames used by the SkillsShowcase
// hover slideshow. Each skill has 3 frames: terminal -> agent thought -> diff.
// Run with: node landing/scripts/generate-skill-mocks.mjs
// Output: landing/public/skills/<id>-{1,2,3}.svg
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = resolve(__dirname, "..", "public", "skills");
mkdirSync(OUT_DIR, { recursive: true });

const W = 1200;
const H = 800;
const BG = "#0a0a0f";
const PANEL = "#12121a";
const PANEL_BR = "#27272a";
const FG = "#fafafa";
const MUTED = "#a1a1aa";
const DIM = "#71717a";
const ACCENT = "#fb923c";
const COOL = "#a78bfa";
const GREEN = "#86efac";
const RED = "#fca5a5";

function escape(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function header(extra = "") {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, monospace">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0a0a0f"/>
      <stop offset="1" stop-color="#13131c"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.85" cy="0.05" r="0.7">
      <stop offset="0" stop-color="${ACCENT}" stop-opacity="0.18"/>
      <stop offset="1" stop-color="${ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowCool" cx="0.05" cy="0.95" r="0.7">
      <stop offset="0" stop-color="${COOL}" stop-opacity="0.16"/>
      <stop offset="1" stop-color="${COOL}" stop-opacity="0"/>
    </radialGradient>
    ${extra}
  </defs>
  <rect width="${W}" height="${H}" fill="url(#bg)"/>
  <rect width="${W}" height="${H}" fill="url(#glow)"/>
  <rect width="${W}" height="${H}" fill="url(#glowCool)"/>`;
}

function chrome(title, kind = "terminal") {
  const dot = (cx, c) =>
    `<circle cx="${cx}" cy="64" r="6.5" fill="${c}"/>`;
  return `
  <rect x="80" y="40" width="${W - 160}" height="${
    H - 80
  }" rx="14" fill="${PANEL}" stroke="${PANEL_BR}"/>
  <rect x="80" y="40" width="${W - 160}" height="44" rx="14" fill="#0d0d14"/>
  <rect x="80" y="78" width="${W - 160}" height="6" fill="${PANEL_BR}" opacity="0.6"/>
  ${dot(110, "#3f3f46")}${dot(132, "#3f3f46")}${dot(154, "#3f3f46")}
  <text x="${W / 2}" y="69" fill="${MUTED}" font-size="14" text-anchor="middle">${escape(
    title
  )}</text>
  <text x="${W - 110}" y="69" fill="${DIM}" font-size="12" text-anchor="end">${
    kind === "diff" ? "diff" : kind === "thought" ? "agent" : "tty"
  }</text>`;
}

function lines(rows, opts = {}) {
  const startY = opts.startY ?? 130;
  const lineH = opts.lineH ?? 26;
  const x = opts.x ?? 120;
  const fontSize = opts.fontSize ?? 16;
  return rows
    .map((r, i) => {
      const y = startY + i * lineH;
      const text =
        typeof r === "string"
          ? `<text x="${x}" y="${y}" fill="${FG}" font-size="${fontSize}">${escape(
              r
            )}</text>`
          : `<text x="${x}" y="${y}" fill="${
              r.color ?? FG
            }" font-size="${fontSize}" opacity="${
              r.opacity ?? 1
            }">${escape(r.text)}</text>`;
      return text;
    })
    .join("\n  ");
}

function badge(x, y, text, color = ACCENT) {
  const w = text.length * 7 + 22;
  return `<g><rect x="${x}" y="${y}" width="${w}" height="22" rx="11" fill="${color}" fill-opacity="0.16" stroke="${color}" stroke-opacity="0.45"/><text x="${
    x + w / 2
  }" y="${y + 15}" fill="${color}" font-size="12" text-anchor="middle">${escape(
    text
  )}</text></g>`;
}

function diffBlock(rows, opts = {}) {
  const startY = opts.startY ?? 130;
  const lineH = opts.lineH ?? 24;
  const x = opts.x ?? 120;
  const w = opts.w ?? W - 240;
  return rows
    .map((r, i) => {
      const y = startY + i * lineH;
      const fill =
        r.kind === "+"
          ? "rgba(134,239,172,0.10)"
          : r.kind === "-"
          ? "rgba(252,165,165,0.10)"
          : "transparent";
      const sign =
        r.kind === "+" ? "+" : r.kind === "-" ? "-" : r.kind === "@" ? "@" : " ";
      const colour =
        r.kind === "+"
          ? GREEN
          : r.kind === "-"
          ? RED
          : r.kind === "@"
          ? COOL
          : MUTED;
      return `<g>
      <rect x="${x}" y="${y - 18}" width="${w}" height="${lineH}" fill="${fill}"/>
      <text x="${x + 14}" y="${y}" fill="${colour}" font-size="14">${sign}</text>
      <text x="${x + 36}" y="${y}" fill="${
        r.kind === "@" ? COOL : FG
      }" font-size="14">${escape(r.text)}</text>
    </g>`;
    })
    .join("\n  ");
}

const close = `</svg>`;

const skills = {
  "postgres-deadlock": {
    title: "Postgres deadlock",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "10:02:45 INFO  monitor: postgres slow_log tail",
      { text: "10:02:47 ERROR  deadlock detected (txn 4218 ↔ txn 4219)", color: RED },
      "10:02:47 INFO  detector: skill=postgres_deadlock matched",
      "10:02:47 INFO  commander: spawning incident_commander (3 skills)",
      { text: "10:02:48 INFO  tool: psql -c 'SELECT * FROM pg_locks' (28ms)", color: MUTED },
      { text: "10:02:50 INFO  tool: psql -c '... pg_stat_activity ...' (42ms)", color: MUTED },
      "10:02:52 INFO  agent: building deadlock graph",
    ],
    thought: [
      { text: "agent ▸ analyse_deadlock_graph", color: COOL },
      "",
      "Two transactions blocking each other:",
      { text: "  • txn 4218 ← UPDATE orders SET ... WHERE id = $1", color: MUTED },
      { text: "  • txn 4219 ← UPDATE orders SET ... WHERE id = $2", color: MUTED },
      "",
      "Both lock rows in opposite order under contention.",
      "Skill runbook recommends:",
      { text: "  → sort target IDs before UPDATE", color: GREEN },
      { text: "  → wrap in retry-with-backoff (3 attempts)", color: GREEN },
      "",
      { text: "next ▸ propose_patch(orders_repo.py)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "src/orders_repo.py @@ -42,7 +42,12 @@" },
      { kind: " ", text: "def bulk_update_orders(ids, payload):" },
      { kind: "-", text: "    for oid in ids:" },
      { kind: "-", text: "        cur.execute(UPDATE_SQL, [payload, oid])" },
      { kind: "+", text: "    # sort to enforce a global lock order across workers" },
      { kind: "+", text: "    for oid in sorted(ids):" },
      { kind: "+", text: "        for attempt in range(3):" },
      { kind: "+", text: "            try:" },
      { kind: "+", text: "                cur.execute(UPDATE_SQL, [payload, oid])" },
      { kind: "+", text: "                break" },
      { kind: "+", text: "            except DeadlockDetected:" },
      { kind: "+", text: "                time.sleep(0.05 * (2 ** attempt))" },
    ],
  },
  "stripe-webhook": {
    title: "Stripe webhook failure",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "11:14:01 INFO  monitor: vercel functions / webhooks",
      { text: "11:14:03 ERROR  POST /api/stripe → 400 (50 last hour)", color: RED },
      "11:14:03 INFO  detector: skill=stripe_webhook matched",
      { text: "11:14:04 INFO  tool: stripe events list --type=payment_intent (218ms)", color: MUTED },
      { text: "11:14:06 INFO  tool: code_read api/stripe/route.ts", color: MUTED },
      "11:14:09 INFO  agent: 47/50 failures share signature mismatch",
    ],
    thought: [
      { text: "agent ▸ classify_webhook_failures", color: COOL },
      "",
      "47 of 50 failures share:",
      { text: "  signature_verification_failed", color: RED },
      "",
      "Working hypothesis:",
      "  STRIPE_WEBHOOK_SECRET was rotated 3 days ago",
      "  but only the live env var was updated.",
      "",
      { text: "  → preview env still holds prior secret", color: GREEN },
      { text: "  → handler order: verify BEFORE json parse", color: GREEN },
      "",
      { text: "next ▸ propose_patch(api/stripe/route.ts)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "api/stripe/route.ts @@ -7,9 +7,12 @@" },
      { kind: " ", text: "export async function POST(req: Request) {" },
      { kind: "-", text: "  const body = await req.json();" },
      { kind: "-", text: "  const sig = req.headers.get('stripe-signature');" },
      { kind: "-", text: "  // verify ..." },
      { kind: "+", text: "  const raw = await req.text();" },
      { kind: "+", text: "  const sig = req.headers.get('stripe-signature') ?? '';" },
      { kind: "+", text: "  let event;" },
      { kind: "+", text: "  try {" },
      { kind: "+", text: "    event = stripe.webhooks.constructEvent(raw, sig, env.STRIPE_WEBHOOK_SECRET);" },
      { kind: "+", text: "  } catch (e) {" },
      { kind: "+", text: "    return new Response('bad signature', { status: 400 });" },
      { kind: "+", text: "  }" },
    ],
  },
  "oom-kill": {
    title: "OOM kill",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "02:41:02 INFO  monitor: dmesg + cgroup memory.events",
      { text: "02:41:04 ERROR  OOM-killed: worker pid=4128 rss=2.1G", color: RED },
      "02:41:04 INFO  detector: skill=oom_kill matched",
      { text: "02:41:05 INFO  tool: cat /proc/4128/status (12ms)", color: MUTED },
      { text: "02:41:06 INFO  tool: docker stats worker (snapshots: 60)", color: MUTED },
      { text: "02:41:09 INFO  tool: git_log src/worker/queue.py", color: MUTED },
      "02:41:13 INFO  agent: rss climbs ~14MB / 30s — leak",
    ],
    thought: [
      { text: "agent ▸ correlate_rss_and_diff", color: COOL },
      "",
      "Container limit:           2.0 GiB",
      "Killed at:                 2.1 GiB",
      "Slope (last 60 minutes):   +14 MiB/30s, monotonic",
      "",
      "git_blame ▸ src/worker/queue.py:88",
      { text: "  PR #312 (yesterday) added Job cache without LRU bound", color: GREEN },
      "",
      "Skill recommends:",
      { text: "  → cap cache size (lru_cache(maxsize=1024))", color: GREEN },
      { text: "  → bump container limit to 2.5G as buffer", color: GREEN },
      "",
      { text: "next ▸ propose_patch(worker/queue.py)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "src/worker/queue.py @@ -80,7 +80,8 @@" },
      { kind: " ", text: "from functools import lru_cache" },
      { kind: " ", text: "" },
      { kind: "-", text: "_job_cache: dict[str, Job] = {}" },
      { kind: "+", text: "@lru_cache(maxsize=1024)" },
      { kind: "+", text: "def _job_cache(key: str) -> Job:" },
      { kind: " ", text: "    ..." },
      { kind: "@", text: "ops/worker.Dockerfile @@ -3,1 +3,1 @@" },
      { kind: "-", text: "ENV MEM_LIMIT=2g" },
      { kind: "+", text: "ENV MEM_LIMIT=2.5g" },
    ],
  },
  "ssl-expiry": {
    title: "SSL expiry",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "08:00:01 INFO  monitor: tls_probes (24 endpoints)",
      { text: "08:00:03 WARN   api.example.com expires in 4d 02h", color: ACCENT },
      "08:00:03 INFO  detector: skill=ssl_expiry matched",
      { text: "08:00:04 INFO  tool: openssl s_client -connect api.example.com:443", color: MUTED },
      { text: "08:00:05 INFO  tool: code_read ops/cron/renew-certs.sh", color: MUTED },
      { text: "08:00:07 INFO  tool: git_log ops/cron/renew-certs.sh", color: MUTED },
      "08:00:09 INFO  agent: cron last run 38 days ago (stalled)",
    ],
    thought: [
      { text: "agent ▸ trace_renewal_pipeline", color: COOL },
      "",
      "Cert: api.example.com",
      { text: "  notAfter: 2026-05-02 (4d 02h remaining)", color: ACCENT },
      "",
      "Renewal: ops/cron/renew-certs.sh",
      { text: "  last successful run: 2026-03-21 (stalled)", color: RED },
      "  reason: ACME challenge fails — port 80 blocked by new WAF rule",
      "",
      "Skill recommends:",
      { text: "  → add WAF allowlist for /.well-known/acme-challenge", color: GREEN },
      { text: "  → re-run renewal job; verify cert chain", color: GREEN },
      "",
      { text: "next ▸ propose_patch(ops/waf/rules.yaml)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "ops/waf/rules.yaml @@ -14,3 +14,7 @@" },
      { kind: " ", text: "rules:" },
      { kind: " ", text: "  - id: block-non-https" },
      { kind: " ", text: "    when: scheme == 'http'" },
      { kind: "+", text: "    except:" },
      { kind: "+", text: "      - path: /.well-known/acme-challenge/*" },
      { kind: "+", text: "        reason: 'ACME http-01 needs port 80'" },
      { kind: "@", text: "ops/cron/renew-certs.sh @@ -3,1 +3,1 @@" },
      { kind: "-", text: "/usr/bin/certbot renew --quiet" },
      { kind: "+", text: "/usr/bin/certbot renew --force-renewal --quiet" },
    ],
  },
  "k8s-crashloop": {
    title: "K8s crashloop",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "14:08:11 INFO  monitor: kube_events tail",
      { text: "14:08:13 ERROR  pod api-7b8 CrashLoopBackOff (exit 137)", color: RED },
      "14:08:13 INFO  detector: skill=k8s_crashloop matched",
      { text: "14:08:14 INFO  tool: kubectl describe pod api-7b8 (118ms)", color: MUTED },
      { text: "14:08:16 INFO  tool: kubectl logs api-7b8 -p (310ms)", color: MUTED },
      { text: "14:08:18 INFO  tool: kubectl get deploy api -o yaml", color: MUTED },
      "14:08:21 INFO  agent: liveness probe HTTPS, port 8080 serves HTTP",
    ],
    thought: [
      { text: "agent ▸ diagnose_crashloop", color: COOL },
      "",
      "Symptom:    exit 137 (SIGKILL by kubelet)",
      "Trigger:    livenessProbe failing 3× in a row",
      "Probe:      httpGet scheme=HTTPS, port=8080",
      "Reality:    api serves PLAIN HTTP on 8080",
      "",
      "PR #441 (today) flipped scheme HTTPS by mistake.",
      "",
      "Skill recommends:",
      { text: "  → set scheme: HTTP (or terminate TLS at the ingress)", color: GREEN },
      "",
      { text: "next ▸ propose_patch(deploy/api.yaml)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "deploy/api.yaml @@ -42,5 +42,5 @@" },
      { kind: " ", text: "        livenessProbe:" },
      { kind: " ", text: "          httpGet:" },
      { kind: " ", text: "            path: /healthz" },
      { kind: "-", text: "            port: 8080" },
      { kind: "-", text: "            scheme: HTTPS" },
      { kind: "+", text: "            port: 8080" },
      { kind: "+", text: "            scheme: HTTP" },
    ],
  },
  "openai-rate-limit": {
    title: "OpenAI rate-limit",
    terminal: [
      { text: "$ quell watch", color: ACCENT },
      "16:30:02 INFO  monitor: structured logs (json)",
      { text: "16:30:04 ERROR  openai 429 rate_limit_exceeded × 142 / 60s", color: RED },
      "16:30:04 INFO  detector: skill=openai_rate_limit matched",
      { text: "16:30:05 INFO  tool: code_read src/llm/client.ts", color: MUTED },
      { text: "16:30:07 INFO  tool: git_log src/llm/client.ts", color: MUTED },
      "16:30:09 INFO  agent: bursts align with deploy 16:28 UTC",
    ],
    thought: [
      { text: "agent ▸ correlate_429_with_deploys", color: COOL },
      "",
      "Bursts: clusters of 30+ 429s within 10s of each other",
      "Deploy: 16:28 UTC — PR #287 added a fan-out batch job",
      "",
      "Effective qps: 18 → 92 after deploy.",
      "OpenAI tier RPM cap: 60 for gpt-4o-mini.",
      "",
      "Skill recommends:",
      { text: "  → add p-queue (concurrency=4) around llm.complete", color: GREEN },
      { text: "  → wire LiteLLM fallback to anthropic/claude-haiku-4-5", color: GREEN },
      "",
      { text: "next ▸ propose_patch(src/llm/client.ts)", color: ACCENT },
    ],
    diff: [
      { kind: "@", text: "src/llm/client.ts @@ -3,9 +3,16 @@" },
      { kind: "+", text: "import PQueue from 'p-queue';" },
      { kind: " ", text: "import { completion } from 'litellm';" },
      { kind: " ", text: "" },
      { kind: "+", text: "const queue = new PQueue({ concurrency: 4, intervalCap: 50, interval: 60_000 });" },
      { kind: "+", text: "" },
      { kind: " ", text: "export async function complete(prompt: string) {" },
      { kind: "-", text: "  return completion({ model: 'gpt-4o-mini', messages });" },
      { kind: "+", text: "  return queue.add(() => completion({" },
      { kind: "+", text: "    model: 'gpt-4o-mini'," },
      { kind: "+", text: "    fallbacks: ['anthropic/claude-haiku-4-5']," },
      { kind: "+", text: "    messages," },
      { kind: "+", text: "  }));" },
      { kind: " ", text: "}" },
    ],
  },
};

for (const [id, data] of Object.entries(skills)) {
  // Frame 1 — terminal
  let svg = header();
  svg += chrome(`~/${id} — quell watch`, "terminal");
  svg += badge(120, 100, "MONITOR ▸ DETECT", ACCENT);
  svg += badge(296, 100, data.title.toUpperCase());
  svg += "\n  " + lines(data.terminal, { startY: 160, lineH: 28 });
  svg += close;
  writeFileSync(resolve(OUT_DIR, `${id}-1.svg`), svg);

  // Frame 2 — agent thought
  svg = header();
  svg += chrome(`agent ▸ incident_commander`, "thought");
  svg += badge(120, 100, "INVESTIGATE", COOL);
  svg += badge(240, 100, data.title.toUpperCase());
  svg += "\n  " + lines(data.thought, { startY: 160, lineH: 28 });
  svg += close;
  writeFileSync(resolve(OUT_DIR, `${id}-2.svg`), svg);

  // Frame 3 — diff
  svg = header();
  svg += chrome(`PR ▸ draft (no auto-merge)`, "diff");
  svg += badge(120, 100, "DRAFT PR", GREEN);
  svg += badge(220, 100, data.title.toUpperCase());
  svg += "\n  " + diffBlock(data.diff, { startY: 165, lineH: 30 });
  svg += close;
  writeFileSync(resolve(OUT_DIR, `${id}-3.svg`), svg);
}

console.log(`Wrote ${Object.keys(skills).length * 3} svg mocks to ${OUT_DIR}`);
