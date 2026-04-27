"""FastAPI app factory for the Quell dashboard.

Runs on the *host* (not the sandbox).  Read-only — no write endpoints,
no auth (localhost-only by default).  If you need to expose the
dashboard on a LAN, front it with a reverse proxy + basic auth; v0.2
deliberately does not build that in.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from quell.dashboard.api import events, incidents, replay, stats

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


_STATIC_DIR = Path(__file__).parent / "static"


def create_dashboard_app(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    static_dir: Path | None = None,
) -> FastAPI:
    """Build the FastAPI app.

    Args:
        session_factory: Async SQLAlchemy session factory bound to the
                         incidents DB the ``quell watch`` loop wrote to.
        static_dir:      Override the bundled Next.js export location.
                         Only set this in tests or for local dev with
                         the Next.js dev server running separately.

    Returns:
        A configured FastAPI app ready for ``uvicorn.run``.
    """
    app = FastAPI(
        title="Quell Dashboard",
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url=None,
    )

    # The SPA calls ``/api/*`` from the same origin; CORS is only
    # interesting for dev where Next runs on :3000 and FastAPI on :7777.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # Hang the session factory on app state so routes can reach it via
    # ``request.app.state.session_factory``.
    app.state.session_factory = session_factory

    app.include_router(incidents.router, prefix="/api")
    app.include_router(events.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")
    app.include_router(replay.router, prefix="/api")

    # Static Next.js export.  If the static dir does not exist (source
    # checkout without a build step), we skip mounting and just serve
    # the API — users will hit ``/api/docs`` for OpenAPI.
    mount_dir = static_dir or _STATIC_DIR
    if mount_dir.is_dir():
        app.mount(
            "/_next",
            StaticFiles(directory=mount_dir / "_next"),
            name="next-assets",
        )

        @app.get("/", include_in_schema=False)
        async def _root() -> FileResponse:
            return FileResponse(mount_dir / "index.html")

        @app.get("/{path:path}", include_in_schema=False)
        async def _spa(path: str) -> FileResponse:
            # Next.js export lays out pages as <path>.html or
            # <path>/index.html — try both then fall back to index.
            candidate_html = mount_dir / f"{path}.html"
            candidate_dir = mount_dir / path / "index.html"
            if candidate_html.is_file():
                return FileResponse(candidate_html)
            if candidate_dir.is_file():
                return FileResponse(candidate_dir)
            return FileResponse(mount_dir / "index.html")

    return app


__all__ = ["create_dashboard_app"]
