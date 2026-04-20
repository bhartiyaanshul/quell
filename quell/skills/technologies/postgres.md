---
name: postgres
category: technologies
description: PostgreSQL incidents — locks, slow queries, connection exhaustion
applicable_when:
  - tech_stack_includes: "postgres"
  - tech_stack_includes: "postgresql"
  - error_contains: "postgres"
  - error_contains: "psql"
  - error_contains: "psycopg"
  - error_contains: "asyncpg"
  - error_contains: "deadlock detected"
  - error_contains: "could not serialize access"
  - error_contains: "too many connections"
severity_hint: high
---

# PostgreSQL incident cheatsheet

## Quick diagnostics
- **Connection saturation** — `SELECT count(*) FROM pg_stat_activity;`.
  Compare to `SHOW max_connections`. Above ~80% is danger.
- **Long-running queries**:

      SELECT pid, now() - query_start AS runtime, state, query
      FROM pg_stat_activity
      WHERE state = 'active'
      ORDER BY runtime DESC
      LIMIT 10;

- **Locks / blockers**:

      SELECT blocked.pid AS blocked_pid,
             blocking.pid AS blocking_pid,
             blocked.query AS blocked_query,
             blocking.query AS blocking_query
      FROM pg_stat_activity blocked
      JOIN pg_stat_activity blocking
        ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));

## Common failure shapes
- **"too many connections"** — a leaked connection pool in the app, or a
  surge of short-lived clients. Use PgBouncer in transaction-pooling
  mode as a buffer. In the app, confirm every client is returned to the
  pool (`async with pool.acquire()` / `with Session()`).
- **Deadlock detected** — two transactions took locks in opposite
  orders. Identify via `pg_stat_activity` + server logs and impose a
  consistent lock order.
- **Slow query regression after a deploy** — a new query missing an
  index, or a plan flip from index scan to seq scan. `EXPLAIN (ANALYZE,
  BUFFERS)` the offending query; compare to the pre-deploy plan if you
  captured one.
- **Vacuum / bloat** — `SELECT relname, n_dead_tup FROM pg_stat_user_tables
  ORDER BY n_dead_tup DESC;` shows tables needing autovacuum attention.

## Before you kill a query
`pg_cancel_backend(pid)` sends SIGINT (polite). `pg_terminate_backend(pid)`
forcibly closes the connection. Always prefer cancel first.
