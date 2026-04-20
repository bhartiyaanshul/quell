---
name: unhandled-null
category: incidents
description: NoneType / null dereference crashes, often from optional fields
applicable_when:
  - error_contains: "NoneType"
  - error_contains: "attribute of None"
  - error_contains: "Cannot read propert"
  - error_contains: "null is not an object"
  - error_contains: "TypeError"
severity_hint: medium
---

# Unhandled null / None dereference

## What it looks like
- Python: `AttributeError: 'NoneType' object has no attribute 'X'`
- JavaScript: `TypeError: Cannot read properties of null (reading 'X')`
- Rust/Go/Kotlin equivalents of nil-panic / unwrap-on-None.

## Usual root causes
1. An optional field was assumed to be present. Often introduced when a
   new schema field is added but older records in the DB don't have it.
2. A remote API returned a partial response (e.g. `{"user": null}`) that
   a happy-path code branch didn't expect.
3. A cache miss returned `None` and the code treated it as a cache hit.
4. A migration backfilled only new rows; legacy rows still have `NULL`.

## Investigation checklist
- [ ] Find the exact file + line of the dereference from the traceback.
- [ ] `git blame` that line — when was it changed? Who changed it?
- [ ] Identify the expression that returned null. Is it a DB query, an
      API response, or a cache read?
- [ ] Look for a recent schema change or migration that could have
      introduced optional-ness.
- [ ] Check whether the failing request has anything unusual in its
      payload (empty ID, missing header, old client version).

## Proposed fix shape
- Explicit null-check with a typed fallback (not `try/except`).
- If the data genuinely should never be null, fix the producer — don't
  paper over it with a default in the consumer.
