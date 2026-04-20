---
name: fastapi
category: frameworks
description: FastAPI-specific patterns for request handling, middleware, and errors
applicable_when:
  - framework_is: "fastapi"
  - error_contains: "fastapi"
  - error_contains: "starlette"
  - error_contains: "uvicorn"
  - tech_stack_includes: "fastapi"
severity_hint: medium
---

# FastAPI investigation cheatsheet

## Where to look first
- **Route table** — `app.routes` lists every registered path. If a URL
  returns 404 it may be that the router was never `include_router`'d.
- **Dependency graph** — FastAPI `Depends(...)` chains can make failures
  look like they come from the wrong place. Read the traceback
  bottom-up, then walk up through the dependency tree.
- **Middleware order** — middlewares execute in reverse of registration
  on the way out. An exception raised in a middleware is caught by
  whichever one registered earlier.

## Common failure shapes
- `RequestValidationError` — the Pydantic model rejected the body. The
  response contains a JSON field-path array pointing at each offender.
- `ResponseValidationError` — the *response* model's types don't match
  what the handler actually returned. Often a nullable field the
  response schema said was required.
- `HTTPException` raised from a dependency — shows up with the
  dependency file in the traceback, not the route. Check `Depends(...)`.
- **Async / sync mix** — a blocking call inside an `async def` handler
  stalls the event loop. Look for `time.sleep`, `requests.get`, raw
  `psycopg2` calls; those should be `asyncio.sleep`, `httpx.AsyncClient`,
  `asyncpg`.

## Useful commands
- Dump the OpenAPI spec: `curl http://<host>/openapi.json | jq`.
- Check what uvicorn is serving: `uvicorn module:app --reload --log-level debug`.
- Starlette's TestClient works synchronously inside `pytest` — but for
  async lifespan events use `httpx.AsyncClient(app=app, base_url=...)`.
