---
name: openai-rate-limit
category: incidents
description: OpenAI API 429 rate-limit errors and token-per-minute throttling
applicable_when:
  - error_contains: "rate_limit_exceeded"
  - error_contains: "RateLimitError"
  - error_contains: "openai.error.RateLimitError"
  - error_contains: "429"
  - error_contains: "tokens per minute"
severity_hint: high
---

# OpenAI rate-limit triage

## What it looks like
- `openai.RateLimitError: Rate limit reached for <model> in organization ...`
- HTTP 429 responses from `api.openai.com`.
- Per-model limits: requests per minute (RPM), tokens per minute (TPM),
  and tokens per day (TPD). The error message specifies which one hit.

## Usual root causes
1. **Traffic spike** — a batch job or a retry storm hammered the API.
2. **Unbounded retry** on 429 without exponential backoff, compounding
   the problem.
3. **Long prompts** — TPM is usage × tokens; a sudden shift to a larger
   prompt can trip TPM while RPM is fine.
4. **Shared org quota** — another team or service on the same key is
   consuming the budget.
5. **Recent model change** — e.g. switching from `gpt-4o-mini` to
   `gpt-4o` silently quadrupled TPM usage.

## Investigation checklist
- [ ] From the error, identify which limit (RPM/TPM/TPD) was hit.
- [ ] Graph API usage over the last hour. Is the spike gradual or a
      single batch?
- [ ] Check retry policy — are we re-issuing requests on 429 without
      backoff?
- [ ] Look for recent config/feature-flag changes that enabled more
      traffic or switched models.
- [ ] If usage looks normal, check the OpenAI status page and your org's
      dashboard — limits may have been lowered.

## Mitigation
- Exponential backoff on 429, honouring `retry-after` header.
- A single global rate-limit guard in the LLM client (token bucket).
- For batch jobs, a concurrency cap per worker.
