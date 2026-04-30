"""Tests for ``quell --help-json`` (Phase 5.5).

The shape under ``data`` is whatever Click's ``to_info_dict()``
produces — we don't pin it. What we *do* pin: the envelope contract
(``kind: "help.tree"``, ``version: "0.3"``), the resource sub-apps
appearing under the root command, and a couple of representative
fields so a regression in the introspection path is caught early.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from quell.interface import cli  # noqa: F401 — registers commands on app
from quell.interface.main import app

runner = CliRunner(mix_stderr=False)


def test_help_json_emits_envelope_and_exits_zero() -> None:
    result = runner.invoke(app, ["--help-json"])
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["kind"] == "help.tree"
    assert payload["version"] == "0.3"
    assert "data" in payload


def test_help_json_lists_root_command() -> None:
    result = runner.invoke(app, ["--help-json"])
    payload = json.loads(result.stdout)
    assert payload["data"]["name"] == "quell"


def test_help_json_includes_resource_subapps() -> None:
    result = runner.invoke(app, ["--help-json"])
    payload = json.loads(result.stdout)
    commands = payload["data"].get("commands") or {}
    # Every Phase 3 resource must be reachable from the root.
    for resource in ("incident", "config", "skill", "notifier"):
        assert resource in commands, f"missing resource {resource}"


def test_help_json_includes_global_verbs() -> None:
    result = runner.invoke(app, ["--help-json"])
    payload = json.loads(result.stdout)
    commands = payload["data"].get("commands") or {}
    for verb in ("init", "doctor", "watch", "dashboard", "version"):
        assert verb in commands, f"missing global verb {verb}"


def test_help_json_includes_incident_verbs() -> None:
    result = runner.invoke(app, ["--help-json"])
    payload = json.loads(result.stdout)
    incident = payload["data"]["commands"]["incident"]
    verbs = incident.get("commands") or {}
    for verb in ("list", "show", "stats", "replay"):
        assert verb in verbs, f"missing incident verb {verb}"
