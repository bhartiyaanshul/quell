"""FastAPI app factory for the sandbox tool server.

The server runs *inside* the Docker sandbox.  Its three routes are:

* ``GET  /health``          — runtime health probe (no auth).
* ``POST /register_agent``  — announce a new agent ID (auth required).
* ``POST /execute``         — dispatch a tool invocation (auth required).

All non-health endpoints require the ``Authorization: Bearer <token>``
header matching the token passed to :func:`create_app`.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from quell.tool_server.auth import BearerAuthMiddleware
from quell.tool_server.routes import execute, health, register


def create_app(bearer_token: str) -> FastAPI:
    """Build the FastAPI app bound to *bearer_token*.

    Args:
        bearer_token: The per-sandbox token the host passes via the
                      ``Authorization: Bearer <token>`` header.  Must be
                      the same token the runtime generated for this
                      sandbox.

    Returns:
        A configured :class:`fastapi.FastAPI` app ready to serve.
    """
    app = FastAPI(title="Quell Tool Server", version="0.1.0")
    app.add_middleware(
        BaseHTTPMiddleware,
        dispatch=BearerAuthMiddleware(app, bearer_token=bearer_token).__call__,
    )
    app.include_router(health.router)
    app.include_router(register.router)
    app.include_router(execute.router)
    return app


__all__ = ["create_app"]
