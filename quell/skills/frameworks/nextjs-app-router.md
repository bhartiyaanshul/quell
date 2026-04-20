---
name: nextjs-app-router
category: frameworks
description: Next.js App Router (13+) server components, actions, and middleware
applicable_when:
  - framework_is: "nextjs"
  - error_contains: "next.js"
  - error_contains: "server component"
  - error_contains: "app router"
  - error_contains: "RSC"
  - tech_stack_includes: "next"
severity_hint: medium
---

# Next.js App Router investigation cheatsheet

## Rendering model — know which one you're in
- **Server Components** (`page.tsx`, `layout.tsx` by default) — run on
  the server only. Cannot use `useState`, `useEffect`, event handlers,
  or browser APIs. A `"use client"` directive at the top of a file flips
  a component into the client bundle.
- **Client Components** — shipped to the browser. Can read from hooks
  and the DOM. Cannot directly call server-only APIs (DB, fs).
- **Server Actions** — async functions marked `"use server"`. Invoked
  from forms or client components; execute on the server.

## Common failure shapes
- **"Error: You're importing a component that needs ..."** — usually a
  server-only API (`fs`, `process.env`, a DB driver) imported into a
  client component. Check the import chain.
- **Hydration mismatch** — server-rendered HTML differs from the
  client's first render. Common causes: `Date.now()`, `Math.random()`,
  locale-dependent formatting, reading `window` at render time.
- **`revalidatePath` / `revalidateTag` not taking effect** — check the
  cache config (`fetch` with `{ next: { revalidate: N } }` or
  `{ cache: "no-store" }`). Middleware running `no-cache` headers can
  also defeat Next's data cache.
- **Server Action 500s** — look in the server logs, not the browser.
  The client only sees a generic error by default.

## Useful commands
- `npm run build` — surfaces Server/Client boundary issues that
  `npm run dev` may mask.
- Enable route info: set `NEXT_DEBUG=*` or use the built-in logger
  (`experimental.logging` in `next.config.js`).
- `next info` — prints platform + dependency versions; include this in
  any bug report.
