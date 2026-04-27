---
name: disk-full
category: incidents
description: Writes fail with ENOSPC / No space left on device / disk full errors
applicable_when:
  - error_contains: "ENOSPC"
  - error_contains: "No space left on device"
  - error_contains: "write ENOSPC"
  - error_contains: "disk full"
  - error_contains: "could not extend file"
  - error_contains: "out of disk space"
severity_hint: high
---

# Disk full runbook

## What it looks like
- Anything that writes (logs, temp files, DB writes, uploads) fails.
- Postgres emits `could not extend file ...: No space left on device`
  and refuses new writes.
- `docker` stops accepting image pulls; `apt`, `yum`, `npm install`
  all fail mid-way.
- `df -h` shows a partition at 100%.

## Usual root causes
1. **Log rotation broken.** `/var/log/*` grew without bound. Common
   after a syslogd / rsyslog / logrotate upgrade.
2. **Docker disk accumulation.** Stopped containers + dangling images
   + unused volumes. `docker system df` reveals the damage.
3. **Temp files in `/tmp` not cleaned.** Especially common with
   Python `tempfile.NamedTemporaryFile(delete=False)` forgotten.
4. **Database WAL / PITR archive piling up.** If WAL archiving lags
   or the replica fell behind, the primary can't recycle segments.
5. **Inode exhaustion (not bytes).** `df -h` shows space free but
   `df -i` shows inodes at 100%. Usually millions of tiny cache
   files in one dir — `find /path -xdev -type f | wc -l`.

## Investigation checklist
- [ ] `df -h` — which partition?
- [ ] `df -i` — if inodes, not bytes, say so; different cleanup.
- [ ] `sudo du -xhd 1 /var 2>/dev/null | sort -h | tail -10` — largest
      directories on the full partition. Replace `/var` with wherever
      you're full.
- [ ] `sudo journalctl --disk-usage` — journal ballooning?
      `sudo journalctl --vacuum-size=500M` trims safely.
- [ ] `docker system df` + `docker system prune -af --volumes` if it's
      the docker data dir.
- [ ] `lsof | grep deleted | head -20` — deleted files still held
      open; restarting the owning process actually reclaims space.
