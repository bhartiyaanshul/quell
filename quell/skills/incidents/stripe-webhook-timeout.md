---
name: stripe-webhook-timeout
category: incidents
description: Stripe webhook endpoints timing out or returning 500
applicable_when:
  - error_contains: "stripe-signature"
  - error_contains: "webhook timeout"
  - error_contains: "/webhooks/stripe"
severity_hint: high
---

# Stripe webhook timeout runbook

## What it looks like
- The handler for `POST /webhooks/stripe` (or equivalent) exceeds Stripe's
  10-second execution budget and Stripe retries with the same
  `Stripe-Signature` header.
- Logs show 500s on the webhook route, often with "read timeout" or
  "connection closed" near the Stripe SDK.
- Duplicate side effects downstream (double-charged users, duplicated
  emails) because Stripe retried.

## Usual root causes
1. **Synchronous work in the request path** — charging a card or updating
   a DB row inline. Move it to a background queue; the webhook should
   only verify the signature, enqueue a job, and return 200.
2. **Missing idempotency** on the job that handles the webhook. Use the
   Stripe event ID as the idempotency key so retries are safe.
3. **Upstream dependency latency** — the webhook calls a slow internal
   service synchronously. Trace where the time goes with a profiler or
   APM span.
4. **Signature verification failing silently** and falling into a slow
   error path. Confirm `STRIPE_WEBHOOK_SECRET` matches the endpoint
   configured in Stripe.

## Investigation checklist
- [ ] Fetch the last 5 minutes of logs for the webhook route; what was
      the p95 response time?
- [ ] Search for `Stripe-Signature` in request headers — did the handler
      log a successful verification?
- [ ] Inspect the deployment history: was the webhook handler touched in
      the last 24 hours?
- [ ] Check the background queue depth — is job processing backed up?
- [ ] Confirm the Stripe dashboard shows the same event IDs retrying.
