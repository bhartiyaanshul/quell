---
name: ssl-certificate-expired
category: incidents
description: TLS handshakes fail with expired / invalid / self-signed certificate errors
applicable_when:
  - error_contains: "CERTIFICATE_VERIFY_FAILED"
  - error_contains: "certificate has expired"
  - error_contains: "certificate verify failed"
  - error_contains: "self signed certificate"
  - error_contains: "unable to get local issuer certificate"
  - error_contains: "x509: certificate"
  - error_contains: "SEC_ERROR_EXPIRED_CERTIFICATE"
severity_hint: high
---

# Expired / invalid TLS certificate runbook

## What it looks like
- Every client starts refusing the TLS handshake simultaneously.
- Browsers show the red lock / "Your connection is not private".
- `curl` emits `SSL certificate problem: certificate has expired`.
- Automated probes + monitors fire together because they all hit the
  same endpoint at the same time the cert expired.

## Usual root causes
1. **Renewal cron did not fire.** Certbot / acme.sh was disabled, or
   the cron user lost permission. The cert simply expired on its
   `not_after` date.
2. **Renewal succeeded but the web server never reloaded.** The new
   cert is on disk at `/etc/letsencrypt/live/...` but nginx/haproxy is
   still holding the old one in memory. `nginx -s reload` fixes it.
3. **Intermediate chain missing.** The leaf cert is fine but the
   intermediate "Let's Encrypt R3" went away — clients that don't
   carry it fail verification. Serve the full chain.
4. **Clock skew on the client.** If the client's wall clock is wildly
   wrong (e.g. fresh VM without NTP), even a valid cert looks expired.
5. **Corporate MITM proxy** (only inside enterprise networks) — the
   company CA is not trusted by the process's truststore. Python
   `certifi` is out of date; Node's `NODE_EXTRA_CA_CERTS` is unset.

## Investigation checklist
- [ ] `echo | openssl s_client -servername HOST -connect HOST:443 2>/dev/null | openssl x509 -noout -dates`
- [ ] Cross-check with `curl -vI https://HOST` — the error message is usually specific.
- [ ] `ls -lh /etc/letsencrypt/live/<domain>/` — is the symlink fresh?
- [ ] `systemctl status certbot.timer` (if certbot) — did it run?
- [ ] `date -u` on both client + server — NTP sane?
- [ ] If it's your cert, rotate now: `certbot renew --force-renewal && nginx -s reload`.
