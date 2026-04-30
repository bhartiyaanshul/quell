"""Tests for ``quell incident <verb>`` (Phase 3.1).

These tests run synchronously because ``CliRunner.invoke`` itself calls
``asyncio.run()`` inside the CLI handlers — mixing a pytest-asyncio
event loop with another nested ``asyncio.run()`` crashes. The seeded
database is built inside a one-shot event loop instead of via an async
fixture; same pattern as ``tests/unit/test_cli_history.py``.

Coverage targets the v0.3.0 CLI contract (``docs/cli-design.md`` §3.2):
the new resource-style commands, the ``--json`` envelope, ``--quiet``
suppression, filter flags on ``list``, and exit codes for the
not-found path on ``show`` / ``replay``.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app
from quell.memory.agent_runs import create_run, finish_run
from quell.memory.db import create_tables, get_engine, get_session_factory
from quell.memory.events import create_event
from quell.memory.incidents import create_incident, update_incident

# CliRunner with mix_stderr=False so we can assert deprecation warnings
# (stderr) separately from the command's stdout.
runner = CliRunner(mix_stderr=False)


async def _seed(db_path: Path) -> dict[str, object]:
    """Build a fixture DB with two incidents + an agent run + events."""
    engine = get_engine(db_path)
    await create_tables(engine)
    factory = get_session_factory(engine)
    async with factory() as session:
        now = datetime.now(UTC).replace(microsecond=0)
        a = await create_incident(
            session,
            signature="sig-a",
            severity="high",
            first_seen=now - timedelta(minutes=10),
        )
        b = await create_incident(
            session,
            signature="sig-b",
            severity="medium",
            first_seen=now - timedelta(minutes=5),
        )
        await update_incident(session, b.id, status="resolved")
        c = await create_incident(
            session,
            signature="sig-c",
            severity="low",
            first_seen=now - timedelta(days=10),
        )
        # ``c`` is intentionally older than the default --since fixture window.

        run = await create_run(
            session,
            incident_id=a.id,
            name="incident_commander",
            skills=["postgres"],
            started_at=now,
        )
        await create_event(
            session,
            agent_run_id=run.id,
            event_type="llm_call",
            payload={"model": "anthropic/claude-haiku-4-5", "input_tokens": 100},
            timestamp=now + timedelta(seconds=1),
        )
        await finish_run(
            session,
            run.id,
            status="completed",
            final_result={"summary": "ok", "_metrics": {"cost_usd": 0.0042}},
            finished_at=now + timedelta(seconds=2),
        )

        await session.commit()
        ids = {"a": a.id, "b": b.id, "c": c.id, "run": run.id}
    await engine.dispose()
    return ids


@pytest.fixture
def seeded_db(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    db_file = tmp_path / "incidents.db"
    ids = asyncio.run(_seed(db_file))
    return db_file, ids


def _patch_db(db_path: Path):  # type: ignore[no-untyped-def]
    """Redirect ``db_file()`` (the XDG data-dir helper) to *db_path*."""
    return patch("quell.config.paths.db_file", return_value=db_path)


# ---------------------------------------------------------------------------
# incident list
# ---------------------------------------------------------------------------


def test_list_default_shows_table(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list"])
    assert result.exit_code == 0, result.stdout
    assert result.stdout.count("inc_") == 3
    # Column headers are uppercase per the spec example.
    assert "ID" in result.stdout
    assert "STATUS" in result.stdout
    assert "SEV" in result.stdout


def test_list_filters_by_status(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--status", "resolved"])
    assert result.exit_code == 0, result.stdout
    assert ids["b"] in result.stdout  # type: ignore[operator]
    assert ids["a"] not in result.stdout  # type: ignore[operator]


def test_list_filters_by_severity(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--severity", "high"])
    assert result.exit_code == 0, result.stdout
    assert ids["a"] in result.stdout  # type: ignore[operator]
    assert ids["b"] not in result.stdout  # type: ignore[operator]
    assert ids["c"] not in result.stdout  # type: ignore[operator]


def test_list_since_filter(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--since", "1 hour ago"])
    assert result.exit_code == 0, result.stdout
    # Older c incident is filtered out; a + b should survive.
    assert ids["a"] in result.stdout  # type: ignore[operator]
    assert ids["b"] in result.stdout  # type: ignore[operator]
    assert ids["c"] not in result.stdout  # type: ignore[operator]


def test_list_invalid_since_returns_usage_error(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--since", "nonsense"])
    assert result.exit_code == 2, result.stderr
    assert "since" in result.stderr.lower()


def test_list_json_envelope(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["kind"] == "incident.list"
    assert payload["version"] == "0.3"
    assert payload["data"]["total"] == 3
    assert payload["data"]["limit"] == 10
    assert len(payload["data"]["incidents"]) == 3


def test_list_quiet_suppresses_output(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "list", "--quiet"])
    assert result.exit_code == 0
    assert result.stdout.strip() == ""


def test_list_empty_db_emits_friendly_message(tmp_path: Path) -> None:
    empty_db = tmp_path / "empty.db"
    with _patch_db(empty_db):
        result = runner.invoke(app, ["incident", "list"])
    assert result.exit_code == 0, result.stdout
    assert "No incidents recorded yet." in result.stdout


# ---------------------------------------------------------------------------
# incident show
# ---------------------------------------------------------------------------


def test_show_prints_details(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "show", str(ids["a"])])
    assert result.exit_code == 0, result.stdout
    assert ids["a"] in result.stdout  # type: ignore[operator]
    assert "signature:" in result.stdout
    assert "severity:" in result.stdout


def test_show_unknown_id_exits_with_not_found(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "show", "inc_nope"])
    # Exit code 7 = NotFoundError (docs/cli-design.md §6).
    assert result.exit_code == 7, result.stderr
    assert "inc_nope" in result.stderr


def test_show_json_envelope(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "show", str(ids["a"]), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["kind"] == "incident.show"
    assert payload["data"]["id"] == ids["a"]
    assert payload["data"]["severity"] == "high"


def test_show_unknown_id_json_emits_error_envelope(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "show", "inc_nope", "--json"])
    assert result.exit_code == 7
    err = json.loads(result.stderr)
    assert err["kind"] == "error.v1"
    assert err["exit_code"] == 7
    assert "inc_nope" in err["error"]


# ---------------------------------------------------------------------------
# incident stats
# ---------------------------------------------------------------------------


def test_stats_default_renders_summary(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "stats"])
    assert result.exit_code == 0, result.stdout
    assert "total incidents:" in result.stdout
    assert "resolved:" in result.stdout
    assert "top signatures:" in result.stdout


def test_stats_json_envelope(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "stats", "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["kind"] == "incident.stats"
    assert payload["data"]["total"] == 3
    assert payload["data"]["by_status"]["resolved"] == 1


# ---------------------------------------------------------------------------
# incident replay
# ---------------------------------------------------------------------------


def test_replay_prints_timeline(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "replay", str(ids["a"])])
    assert result.exit_code == 0, result.stdout
    assert ids["a"] in result.stdout  # type: ignore[operator]
    assert "incident_commander" in result.stdout
    assert "llm_call" in result.stdout


def test_replay_unknown_id_exits_with_not_found(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "replay", "inc_nope"])
    assert result.exit_code == 7, result.stderr
    assert "inc_nope" in result.stderr


def test_replay_json_envelope(seeded_db: tuple[Path, dict[str, object]]) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["incident", "replay", str(ids["a"]), "--json"])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["kind"] == "incident.replay"
    assert payload["data"]["incident"]["id"] == ids["a"]
    runs = payload["data"]["runs"]
    assert len(runs) == 1
    assert runs[0]["events"][0]["type"] == "llm_call"


# ---------------------------------------------------------------------------
# Deprecated aliases — old commands still work + emit a stderr warning.
# Per docs/cli-design.md §3.4: removed in v0.4.0.
# ---------------------------------------------------------------------------


def test_history_alias_warns_and_lists(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["history"])
    assert result.exit_code == 0, result.stdout
    assert "[deprecation]" in result.stderr
    assert "quell incident list" in result.stderr
    assert result.stdout.count("inc_") == 3


def test_show_alias_warns_and_prints(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["show", str(ids["a"])])
    assert result.exit_code == 0, result.stdout
    assert "[deprecation]" in result.stderr
    assert "quell incident show" in result.stderr


def test_stats_alias_warns_and_prints(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, _ = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0, result.stdout
    assert "[deprecation]" in result.stderr
    assert "quell incident stats" in result.stderr


def test_replay_alias_warns_and_prints(
    seeded_db: tuple[Path, dict[str, object]],
) -> None:
    db_path, ids = seeded_db
    with _patch_db(db_path):
        result = runner.invoke(app, ["replay", str(ids["a"])])
    assert result.exit_code == 0, result.stdout
    assert "[deprecation]" in result.stderr
    assert "quell incident replay" in result.stderr
