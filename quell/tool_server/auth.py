"""Bearer-token authentication middleware for the tool server.

The tool server is only ever reached from the host side via the random
host port bound by :class:`~quell.runtime.DockerRuntime`.  Even so, we
require a per-sandbox bearer token so that a compromised sidecar can't
make cross-container calls.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.responses import JSONResponse, Response

_AUTH_HEADER = "Authorization"


def _unauthorized(detail: str) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": detail})


class BearerAuthMiddleware:
    """ASGI middleware that enforces ``Authorization: Bearer <token>``.

    The ``/health`` endpoint is exempt so the runtime's health check
    can confirm the server is up before the bearer token is known to
    the client (it isn't, in practice — but exempting ``/health`` keeps
    the contract simple).
    """

    def __init__(self, app: object, *, bearer_token: str) -> None:
        self._app = app
        self._token = bearer_token

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        header = request.headers.get(_AUTH_HEADER, "")
        if not header.startswith("Bearer "):
            return _unauthorized("Missing bearer token")
        token = header[len("Bearer ") :].strip()
        if token != self._token:
            return _unauthorized("Invalid bearer token")
        return await call_next(request)


__all__ = ["BearerAuthMiddleware"]
