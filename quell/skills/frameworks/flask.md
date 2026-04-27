---
name: flask
category: frameworks
description: Flask request / app / test contexts, blueprint wiring, and extension errors
applicable_when:
  - framework_is: "flask"
  - tech_stack_includes: "flask"
  - error_contains: "flask"
  - error_contains: "werkzeug"
  - error_contains: "RuntimeError: Working outside of application context"
  - error_contains: "RuntimeError: Working outside of request context"
  - error_contains: "jinja2"
severity_hint: medium
---

# Flask investigation cheatsheet

## Where to look first
- **Context errors.** "Working outside of application context" /
  "request context" means the caller tried to use `g`, `current_app`,
  `request`, or `session` outside a dispatched request. Common in
  background threads, CLI commands, test fixtures. Wrap with
  `with app.app_context():` (or `app.test_request_context()`).
- **Blueprint registration.** A 404 on a route that "obviously" exists
  usually means the blueprint was defined but never
  `app.register_blueprint(...)`'d — or the import is gated behind a
  `if __name__ == "__main__"`.
- **Extension init order.** `SQLAlchemy(app)`, `Migrate(app, db)`,
  `Login(app)` etc. must run before any request fires. Factory
  pattern users: remember to call every `ext.init_app(app)` inside
  `create_app()`.

## Common failure shapes
- **`TemplateNotFound`.** Jinja2 looked in `templates/` relative to
  the blueprint's folder; the template lives elsewhere. Set
  `template_folder=` on the blueprint, or move the file.
- **Unhandled `werkzeug.exceptions.*`.** `abort(403)` inside a
  handler raises; caught by the error-handler you registered for
  403. If no handler, default HTML page is returned — sometimes users
  claim "blank page" when it's the stock 500.
- **`RequestEntityTooLarge`.** Incoming body exceeds
  `MAX_CONTENT_LENGTH`; raise the limit or paginate uploads.
- **Session state lost between requests.** `SECRET_KEY` rotated, or
  not set in prod. Cookies are signed with it; rotating invalidates
  every session.
- **Thread-local `g` leak in threaded WSGI servers.** `g` is
  per-request in Flask 2.x — but long-lived greenlets (gevent) can
  confuse it. Prefer passing state explicitly.

## Useful commands
- `flask routes` — list every registered rule with its endpoint.
- `flask shell` — REPL with app + db preloaded.
- `FLASK_ENV=development flask run --debugger` — Werkzeug's in-browser
  debugger. Never in production.
- `gunicorn 'myapp:create_app()' --access-logfile -` — what prod
  actually runs; reproduces context issues dev server hides.
