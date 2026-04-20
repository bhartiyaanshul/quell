"""Tests for the Phase 15 ``quell history | show | stats`` commands.

These tests run synchronously because ``CliRunner.invoke`` itself calls
``asyncio.run()`` inside the CLI handlers — mixing a pytest-asyncio
event loop with another nested ``asyncio.run()`` crashes.  The seeded
database is built inside a one-shot event loop instead of via an async
fixture.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.memory.incidents import create_incident, list_incidents, update_incident

runner = CliRunner()


async def _seed(db_path: Path) -> list[str]:
    engine = get_engine(db_path)
    await create_tables(engine)
    factory = get_session_factory(engine)
    ids: list[str] = []
    async with factory() as session:
        a = await create_incident(
            session,
            signature="sig-a",
            severity="high",
            first_seen=datetime.now(UTC) - timedelta(minutes=10),
        )
        b = await create_incident(
            session,
            signature="sig-b",
            severity="medium",
            first_seen=datetime.now(UTC) - timedelta(minutes=5),
        )
        await update_incident(session, b.id, status="resolved")
        await session.commit()
        ids = [a.id, b.id]
    await engine.dispose()
    return ids


@pytest.fixture
def seeded_db(tmp_path: Path) -> tuple[Path, list[str]]:
    db_file = tmp_path / "incidents.db"
    ids = asyncio.run(_seed(db_file))
    return db_file, ids


def _patch_db(db_path: Path):  # type: ignore[no-untyped-def]
    """Redirect ``db_file()`` (the XDG data-dir helper) to *db_path*."""
    return patch("quell.config.paths.db_file", return_value=db_path)


# ---------------------------------------------------------------------------
# history
# ---------------------------------------------------------------------------


def test_history_lists_incidents(seeded_db: tuple[Path, list[str]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["history", "--limit", "5"])
    assert result.exit_code == 0, result.stdout
    assert result.stdout.count("inc_") == 2


def test_show_prints_incident_details(seeded_db: tuple[Path, list[str]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["show", ids[0]])
    assert result.exit_code == 0, result.stdout
    assert ids[0] in result.stdout
    assert "signature:" in result.stdout


def test_show_unknown_id_exits_nonzero(seeded_db: tuple[Path, list[str]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["show", "inc_nonexistent"])
    assert result.exit_code != 0


def test_stats_prints_aggregate(seeded_db: tuple[Path, list[str]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0, result.stdout
    assert "total incidents:" in result.stdout
    assert "resolved:" in result.stdout
    assert "top signatures:" in result.stdout


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "quell-agent" in result.stdout


# Keep an import reference so mypy / ruff don't complain about the unused
# ``list_incidents`` import above — it's useful to callers of the fixture.
_ = list_incidents
