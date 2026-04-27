"""Launch the dashboard — spawn uvicorn + optionally open a browser."""

from __future__ import annotations

import asyncio
import webbrowser
from pathlib import Path

import uvicorn
from loguru import logger

from quell.dashboard.server import create_dashboard_app
from quell.memory.db import create_tables, get_engine, get_session_factory


async def launch_dashboard(
    *,
    host: str = "127.0.0.1",
    port: int = 7777,
    open_browser: bool = True,
    db_path: Path | None = None,
) -> None:
    """Start the dashboard FastAPI app on *host:port*.

    Blocks until the server exits (e.g. on Ctrl-C).
    """
    engine = get_engine(db_path=db_path)
    await create_tables(engine)
    factory = get_session_factory(engine)

    app = create_dashboard_app(factory)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)

    url = f"http://{host}:{port}"
    logger.info("dashboard: serving at {}", url)

    if open_browser:
        # Don't crash if there is no display / no browser on the box.
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:  # noqa: BLE001
            logger.info("dashboard: could not auto-open browser: {}", exc)

    try:
        await server.serve()
    finally:
        await engine.dispose()


def run_dashboard_sync(**kwargs: object) -> None:
    """Sync wrapper for the CLI."""
    asyncio.run(launch_dashboard(**kwargs))  # type: ignore[arg-type]


__all__ = ["launch_dashboard", "run_dashboard_sync"]
