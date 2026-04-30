# Quell local dashboard

Read-only web UI launched by `quell dashboard`.  Next.js 14 (App
Router, static export) + TailwindCSS + Framer Motion, served by a
small FastAPI backend in `quell/dashboard/`.

## Run it locally (two terminals)

```bash
# Terminal 1 — FastAPI backend on :7777 (also starts the browser).
poetry run quell dashboard --no-open

# Terminal 2 — Next.js dev server on :3001 with hot reload.
cd dashboard
npm install
npm run dev
```

Now open <http://localhost:3001>.  A rewrite in `next.config.mjs`
proxies every `/api/*` request to `http://127.0.0.1:7777`, so the
frontend + backend talk to each other without CORS drama.

## Production build

```bash
cd dashboard
npm run build      # writes ./out/
cp -r out ../quell/dashboard/static
```

`out/` is gitignored; the release workflow runs those steps and
bundles `quell/dashboard/static/` into the wheel so `pipx install
quell` users get the UI for free.

## What it shows

* **`/`** — incident list with severity + status + cost + last-seen
  filters.  Rows link to the detail page.
* **`/incidents/[id]`** — root cause, every agent run with tokens +
  cost, structured findings, link to the draft PR.
* **`/incidents/[id]/replay`** — full event timeline per run (LLM
  calls, tool calls, errors) with icons + timestamps.
* **`/stats`** — totals by status, MTTR, top recurring signatures.

All data comes from `quell/dashboard/api/*.py` — four tiny routers
over the SQLAlchemy incident DB.  No write operations.
