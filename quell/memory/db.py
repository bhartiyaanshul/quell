"""Async SQLAlchemy engine factory and schema migration for Quell.

Usage
-----
    engine = get_engine()          # default: quell data dir
    await create_tables(engine)    # idempotent — safe to call on every start-up
    factory = get_session_factory(engine)
    async with factory() as session:
        ...
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from quell.memory.models import Base

_DEFAULT_URL = "sqlite+aiosqlite:///{path}"


def get_engine(db_path: Path | None = None) -> AsyncEngine:
    """Create (or return) an async SQLAlchemy engine.

    Args:
        db_path: Path to the SQLite file. Defaults to the XDG data directory.
                 Pass ``None`` for the default, or an explicit Path for tests.

    Returns:
        A configured :class:`AsyncEngine` instance.
    """
    if db_path is None:
        from quell.config.paths import db_file

        db_path = db_file()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = _DEFAULT_URL.format(path=db_path.as_posix())
    return create_async_engine(url, echo=False, future=True)


def get_engine_memory() -> AsyncEngine:
    """Return an in-memory async engine — intended for tests only."""
    return create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Return an async session factory bound to *engine*.

    Args:
        engine: The :class:`AsyncEngine` to bind sessions to.

    Returns:
        An :class:`async_sessionmaker` that produces :class:`AsyncSession` objects.
    """
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables(engine: AsyncEngine) -> None:
    """Create all tables defined in the ORM metadata (idempotent).

    Safe to call on every application start-up. Existing tables are not
    modified. In v0.1 this is the entire migration strategy; Alembic will
    be introduced in a later version.

    Args:
        engine: The engine to run DDL against.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


__all__ = [
    "get_engine",
    "get_engine_memory",
    "get_session_factory",
    "create_tables",
]
