---
name: memory-leak
category: incidents
description: Process RSS grows unbounded, eventually OOM-killed by the kernel or runtime
applicable_when:
  - error_contains: "MemoryError"
  - error_contains: "OutOfMemoryError"
  - error_contains: "Killed"
  - error_contains: "OOMKilled"
  - error_contains: "JavaScript heap out of memory"
  - error_contains: "cannot allocate memory"
  - error_contains: "fatal error: runtime: out of memory"
severity_hint: high
---

# Memory leak / OOM runbook

## What it looks like
- Process memory climbs hour-over-hour until the kernel's OOM killer
  steps in (`dmesg | grep -i oom-kill`).
- Container is evicted with `OOMKilled` or `Status: OOMKilled` in
  Kubernetes.
- Restart fixes the immediate problem but the pattern recurs every N
  hours.
- Sawtooth graph on RSS / heap size in your metrics.

## Usual root causes
1. **Unbounded cache.** A module-level `dict` keyed by request id,
   user id, or a timestamp never evicts. Fix with an LRU
   (`functools.lru_cache(maxsize=1024)`, `cachetools.LRUCache`,
   `node-lru-cache`).
2. **Listener / subscription leak.** Adding an event listener each
   request without `.remove()`. Common in Node EventEmitter, Python
   signal handlers, Vue/React effect cleanup forgotten.
3. **Closures capturing large objects.** A handler returned from a
   factory captures the whole request context; GC can't free it.
4. **Connection pool without a max.** asyncpg / HikariCP / pg-pool
   grows one connection per concurrent request and never shrinks.
5. **Native leak.** C extension (`psycopg2`, `pillow`, image codecs,
   `onnxruntime`) holds memory outside the managed heap. Python's
   tracemalloc won't see it.

## Investigation checklist
- [ ] `ps -o pid,rss,vsz,cmd -p <pid>` snapshots over 10 minutes — linear
      growth confirms a leak.
- [ ] Python: `tracemalloc.start()` early, then dump top stats
      periodically. Compare snapshots with `take_snapshot().compare_to`.
- [ ] Node: `--inspect` + Chrome DevTools heap snapshots, or
      `heapdump` library.
- [ ] JVM: `jmap -histo <pid> | head -50`, or GC logs with
      `-XX:+PrintGCDetails`.
- [ ] Container: `kubectl top pod`, or `docker stats`. Bump limits
      only as a stopgap — fix the leak.
- [ ] Check recent deploys — when did RSS growth start?
