---
name: express
category: frameworks
description: Express.js middleware order, async handlers, and request-cycle errors
applicable_when:
  - framework_is: "express"
  - framework_is: "expressjs"
  - tech_stack_includes: "express"
  - error_contains: "express"
  - error_contains: "UnhandledPromiseRejection"
  - error_contains: "Cannot set headers after they are sent"
  - error_contains: "PayloadTooLargeError"
severity_hint: medium
---

# Express.js investigation cheatsheet

## Where to look first
- **Middleware order.** Express runs `app.use(...)` handlers in
  registration order. `body-parser` (or `express.json()`) before any
  route that reads `req.body`. Error-handlers — the 4-arg
  `(err, req, res, next)` signature — must be registered **last**.
- **Route table.** `app._router.stack` enumerates every registered
  handler if you log it during boot. Routers mounted under a prefix
  hide behind a `Layer` with `regexp`.
- **`process.on('unhandledRejection')`** — install it *and* log; a
  silently-rejected Promise is the single most common source of
  ghost 500s in Express apps.

## Common failure shapes
- **`Cannot set headers after they are sent`.** Handler called
  `res.send()` then `return next()` — `next()` hit the next
  middleware which also responded. Or an async handler forgot to
  `return` after sending. Audit every handler for early-return
  on the happy path.
- **Unhandled promise rejection crashes the process.** `async`
  handlers that throw bypass Express's error-handling unless you
  either use `express-async-errors` or wrap each handler with
  `asyncHandler((req, res) => ...)`.
- **`PayloadTooLargeError`.** Body exceeds default 100 KB. Bump
  with `express.json({ limit: '5mb' })` or paginate uploads.
- **CORS preflight fails silently.** `OPTIONS` requests don't hit
  your route handler; they're caught by the CORS middleware. If
  the browser shows "CORS error" but the server has no log line, the
  preflight was blocked before it reached your router.
- **Session lost between requests.** `SESSION_SECRET` rotated, or
  `cookie.secure: true` behind an HTTP-only proxy (set
  `app.set('trust proxy', 1)`).

## Useful commands
- `DEBUG=express:* node server.js` — Express's own request-cycle log.
- `node --inspect server.js` — Chrome DevTools. `--inspect-brk` if
  it crashes before you can connect.
- `curl -v -XOPTIONS <url> -H 'Origin: https://example.com' -H 'Access-Control-Request-Method: POST'`
  — manually trigger CORS preflight.
