---
name: redis
category: technologies
description: Redis incidents — memory pressure, eviction, connection churn
applicable_when:
  - tech_stack_includes: "redis"
  - error_contains: "redis"
  - error_contains: "OOM command not allowed"
  - error_contains: "CROSSSLOT"
  - error_contains: "MOVED"
  - error_contains: "LOADING Redis"
severity_hint: medium
---

# Redis incident cheatsheet

## First commands to run
- `INFO memory` — `used_memory_human`, `maxmemory_policy`, `evicted_keys`.
  A non-zero and growing `evicted_keys` means Redis is shedding data.
- `INFO clients` — `connected_clients`, `blocked_clients`. A sudden
  spike suggests a connection leak or a thundering herd.
- `CLIENT LIST` — who is connected, from where, and for how long.
- `SLOWLOG GET 20` — the 20 slowest recent commands. Look for `KEYS *`,
  `HGETALL` on huge hashes, `LRANGE 0 -1` on huge lists.

## Common failure shapes
- **`OOM command not allowed when used memory > 'maxmemory'`** — Redis
  hit its memory cap and eviction is disabled or ineffective. Either
  raise `maxmemory`, switch policy to `allkeys-lru`, or find what's
  filling memory (`redis-cli --bigkeys`, MEMORY USAGE on suspects).
- **Connection storm after a reconnect** — every app pod reconnects at
  once. Stagger reconnection, and enable TCP keepalives.
- **`CROSSSLOT` in cluster mode** — a multi-key command hit keys on
  different slots. Use hash tags (`{user:42}`) or split the command.
- **`LOADING Redis is loading the dataset in memory`** — a replica is
  syncing. Reads will fail until RDB/AOF finishes. Route reads to the
  primary during this window.

## Memory triage
- Identify large keys: `redis-cli --bigkeys` (sampling; safe on prod).
- Sample TTLs: `redis-cli --scan --pattern '*' | head -100 | xargs -I K redis-cli TTL K`.
- If a single key dominates (`MEMORY USAGE key`), investigate the code
  path that writes it — a forgotten accumulator, an unbounded sorted set.

## Before flushing
Never `FLUSHALL` / `FLUSHDB` in production without an explicit incident
commander approval. Prefer targeted deletion by pattern.
