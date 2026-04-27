---
name: database-deadlock
category: incidents
description: Transactions abort with deadlock-detected or lock-wait-timeout errors
applicable_when:
  - error_contains: "deadlock detected"
  - error_contains: "Deadlock found when trying to get lock"
  - error_contains: "lock wait timeout"
  - error_contains: "ORA-00060"
  - error_contains: "could not obtain lock"
  - error_contains: "SerializationFailure"
severity_hint: high
---

# Database deadlock runbook

## What it looks like
- Postgres: `ERROR: deadlock detected` with two or more PIDs named in
  the server log. One transaction is aborted; the client sees an
  exception.
- MySQL / InnoDB: `Deadlock found when trying to get lock; try
  restarting transaction`.
- Oracle: `ORA-00060: deadlock detected while waiting for resource`.
- Retries succeed because the blocking transaction has rolled back,
  so the issue is intermittent under load.

## Usual root causes
1. **Inconsistent lock ordering.** Transaction A locks rows `(42, 17)`
   in that order; transaction B locks them `(17, 42)`. Always lock in
   the same deterministic order — sort your primary keys before any
   `SELECT ... FOR UPDATE`.
2. **Gap / next-key locks under REPEATABLE READ** (MySQL InnoDB's
   default). Range scans take more locks than you expect.
3. **Bulk updates contending with single-row writers.** The bulk
   statement holds many row locks; individual writers get starved.
4. **Foreign key cascade locks.** A delete on the parent cascades
   locks onto children that another transaction is already writing.
5. **Retries that retake locks in the wrong order.** The retry loop
   needs to start a *fresh* transaction, not keep locks from the
   first attempt.

## Investigation checklist
- [ ] Postgres: `SELECT * FROM pg_stat_activity WHERE waiting;` plus
      `pg_blocking_pids()` (see the `postgres` skill).
- [ ] Postgres server log: `log_lock_waits = on` surfaces any wait
      > `deadlock_timeout` (default 1s) — even ones that resolve without
      a full deadlock.
- [ ] MySQL: `SHOW ENGINE INNODB STATUS\G` → "LATEST DETECTED DEADLOCK"
      section gives both transactions verbatim.
- [ ] Reproduce under load: `pgbench -c 16 -t 100` with your offending
      SQL; the deadlock often becomes deterministic.
- [ ] Consider exponential-backoff retries at the ORM layer — some
      deadlocks are unavoidable and harmless if retried.
