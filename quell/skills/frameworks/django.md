---
name: django
category: frameworks
description: Django ORM, middleware, migrations, and request-cycle patterns
applicable_when:
  - framework_is: "django"
  - tech_stack_includes: "django"
  - error_contains: "django"
  - error_contains: "DoesNotExist"
  - error_contains: "IntegrityError"
  - error_contains: "OperationalError"
  - error_contains: "MultipleObjectsReturned"
  - error_contains: "MiddlewareNotUsed"
severity_hint: medium
---

# Django investigation cheatsheet

## Where to look first
- **Traceback framing.** Django tracebacks include the *request*
  middleware chain. The innermost frame is almost always in the view
  or a model method; the outer frames (middleware, handlers) are
  plumbing. Jump to the innermost user-code frame first.
- **`settings.DEBUG`.** Confirm it's `False` in production. A
  `DEBUG=True` deploy leaks stack traces and SQL.
- **`MIDDLEWARE` order.** Top-down on the request, bottom-up on the
  response. Auth must sit above anything that reads `request.user`.

## Common failure shapes
- **`DoesNotExist`** from `.get()`. Either the record was hard-deleted,
  or the caller assumed it existed. Switch to `.filter().first()` +
  a null check, or `get_object_or_404` in views.
- **`IntegrityError` on save** — usually a unique constraint hit on
  a field you forgot carried `unique=True`, or a race where two
  requests inserted the same natural key. Wrap with
  `transaction.atomic()` + `try/except IntegrityError`.
- **`OperationalError: too many clients already`** — connection
  pool exhaustion. With `CONN_MAX_AGE > 0`, stale persistent
  connections accumulate. See the `postgres` skill too.
- **Migration divergence.** `showmigrations` reveals unapplied or
  missing-on-disk migrations. `sqlmigrate <app> <nnnn>` inspects
  generated SQL without running it.
- **Cold-start N+1.** A template renders a relation inside a loop
  without `prefetch_related`. `django-debug-toolbar` or
  `django.db.connection.queries` surfaces the count.

## Useful commands
- `python manage.py shell_plus --print-sql` — ad-hoc ORM with SQL echoed.
- `python manage.py check --deploy` — settings audit (HSTS, DEBUG, SECRET_KEY).
- `python manage.py showmigrations` / `makemigrations --dry-run`.
- `python manage.py dbshell` — raw psql session with your settings.
- Heavy production debug: `CAPTURE_SQL = True` + `LOGGING` django.db.backends.
