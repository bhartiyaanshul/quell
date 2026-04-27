---
name: rails
category: frameworks
description: Ruby on Rails ActiveRecord, asset pipeline, and request-cycle errors
applicable_when:
  - framework_is: "rails"
  - framework_is: "ruby-on-rails"
  - tech_stack_includes: "rails"
  - error_contains: "ActiveRecord::"
  - error_contains: "ActionController::"
  - error_contains: "ActionView::"
  - error_contains: "NoMethodError"
  - error_contains: "undefined method"
severity_hint: medium
---

# Ruby on Rails investigation cheatsheet

## Where to look first
- **`log/production.log`** — every request logs the route, params,
  and total / DB / view breakdown. A 500 line includes the full
  traceback.
- **`config/routes.rb`.** `bin/rails routes | grep <name>` is the
  canonical answer to "does this URL exist?". `routes -g` filters.
- **Gem versions.** `bundle outdated` surfaces any gem with a known
  security advisory; `Gemfile.lock` is the source of truth for what
  actually ran.

## Common failure shapes
- **`ActiveRecord::RecordNotFound`** from `find()`. Switch to
  `find_by(...)` + nil check if legitimate absence is a valid state.
- **`ActiveRecord::StatementInvalid: PG::UndefinedColumn`** — code
  references a column that exists in dev but not in prod. Did the
  migration deploy? `bin/rails db:migrate:status`.
- **`NoMethodError: undefined method '...' for nil:NilClass`.**
  A chained call like `user.profile.avatar.url` blew up because one
  link was `nil`. Use `&.` (safe-nav) or guard earlier.
- **N+1 queries.** `log/development.log` logs each SQL; the
  `bullet` gem or `rack-mini-profiler` surface them in the browser.
  Fix with `includes(:association)` / `preload`.
- **Asset pipeline 404 after deploy.** Propshaft / Sprockets didn't
  compile, or the CDN cache is serving the previous manifest.
  `bin/rails assets:precompile RAILS_ENV=production` then invalidate
  the CDN.
- **Sidekiq job dies silently.** Worker class loaded but the job
  body raised. Check the Sidekiq "dead" queue; usually a missing
  env var in the worker process.

## Useful commands
- `bin/rails console -e production` — careful; read-only unless you
  need to mutate.
- `bin/rails dbconsole` — direct psql/mysql with prod credentials.
- `bin/rails notes` — TODO / FIXME / HACK across the repo.
- `bin/rails runner 'puts Rails.application.credentials.dig(:aws, :bucket)'`
  — inspect production credentials without dumping the whole file.
