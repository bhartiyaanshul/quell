---
name: dns-resolution-failure
category: incidents
description: Hostname lookups fail with ENOTFOUND / NXDOMAIN / name-resolution errors
applicable_when:
  - error_contains: "ENOTFOUND"
  - error_contains: "getaddrinfo"
  - error_contains: "Name or service not known"
  - error_contains: "no such host"
  - error_contains: "NXDOMAIN"
  - error_contains: "Temporary failure in name resolution"
severity_hint: high
---

# DNS resolution failure runbook

## What it looks like
- `getaddrinfo ENOTFOUND <host>` in Node.js / Python / Go logs.
- `Temporary failure in name resolution` on Linux hosts after a network
  blip.
- An outbound HTTPS call to a known-good domain (Stripe, AWS, your own
  API) suddenly fails for minutes, then recovers.
- Timeouts pile up on the caller; the callee itself is healthy.

## Usual root causes
1. **DNS provider incident.** Route53 / Cloudflare / GoDaddy had a
   regional blip. Check their status page; usually 5-30 min.
2. **Stale cached record.** TTL already expired and the upstream
   resolver returned SERVFAIL. `systemd-resolved` or the container's
   `nscd` may be holding onto a stale NXDOMAIN — `resolvectl flush-caches`
   clears it.
3. **Container `/etc/resolv.conf` points at a dead resolver.** Common
   after a Kubernetes CoreDNS restart; pods keep pointing at an old
   cluster IP.
4. **Egress firewall blocking UDP/53** — especially after a SecOps
   change. `dig @1.1.1.1 example.com` works but `dig example.com` does
   not.
5. **IPv6 AAAA hang.** The host tries AAAA, the resolver takes 5s, then
   falls back to A. Fix by disabling IPv6 on the client or adding
   `single-request-reopen` to resolv.conf.

## Investigation checklist
- [ ] `dig +short <failing-host>` on the affected machine.
- [ ] `dig @1.1.1.1 +short <failing-host>` — bypasses local resolver;
      if this works, the local resolver is the fault.
- [ ] `cat /etc/resolv.conf` — is it pointing at anything sane?
- [ ] `journalctl -u systemd-resolved --since "10 min ago"`.
- [ ] If Kubernetes: `kubectl -n kube-system logs -l k8s-app=kube-dns`.
- [ ] If Docker: restart the container — it picks up fresh resolv.conf.
