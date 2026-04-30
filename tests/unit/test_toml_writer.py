"""Tests for quell.utils.toml_writer.

Every test that emits TOML round-trips it through ``tomllib`` to prove
the output parses — that's the contract we care about, since the
loader uses ``tomllib`` to read it back.
"""

from __future__ import annotations

import tomllib

import pytest

from quell.utils.toml_writer import dumps


def test_dumps_simple_scalars() -> None:
    out = dumps({"name": "quell", "version": 0.2, "enabled": True, "retries": 3})
    parsed = tomllib.loads(out)
    assert parsed == {"name": "quell", "version": 0.2, "enabled": True, "retries": 3}


def test_dumps_windows_path_round_trips() -> None:
    """Regression: ``C:\\Users\\anshul`` was emitted unescaped — TOML reads
    ``\\U`` as a Unicode escape and aborts at the next non-hex char.
    """
    data = {"repo_path": r"C:\Users\anshul"}
    out = dumps(data)
    parsed = tomllib.loads(out)
    assert parsed["repo_path"] == r"C:\Users\anshul"


def test_dumps_path_with_single_quote_uses_basic_string() -> None:
    """Literal-string form can't contain ``'``; writer must fall back."""
    data = {"label": "user's home"}
    out = dumps(data)
    parsed = tomllib.loads(out)
    assert parsed["label"] == "user's home"


def test_dumps_string_with_embedded_double_quote() -> None:
    data = {"label": 'a "quoted" word'}
    out = dumps(data)
    parsed = tomllib.loads(out)
    assert parsed["label"] == 'a "quoted" word'


def test_dumps_nested_dict_emits_table_section() -> None:
    data = {"llm": {"model": "ollama/llama3", "max_context_tokens": 100000}}
    out = dumps(data)
    assert "[llm]" in out
    parsed = tomllib.loads(out)
    assert parsed == data


def test_dumps_list_of_dicts_emits_array_of_tables() -> None:
    """Regression: list[dict] was stringified via Python ``repr``."""
    data = {
        "monitors": [
            {"type": "local-file", "path": "/var/log/app.log"},
            {"type": "http-poll", "url": "https://api/health"},
        ]
    }
    out = dumps(data)
    assert "[[monitors]]" in out
    parsed = tomllib.loads(out)
    assert parsed == data


def test_dumps_list_of_scalars_emits_inline_array() -> None:
    data = {"keywords": ["incident", "sre", "agents"]}
    out = dumps(data)
    parsed = tomllib.loads(out)
    assert parsed == data


def test_dumps_full_config_shape_round_trips() -> None:
    """End-to-end: shape the wizard actually produces on Windows."""
    data = {
        "repo_path": r"C:\Users\anshul",
        "llm": {"model": "ollama/llama3"},
        "monitors": [{"type": "local-file", "path": "/var/log/app.log"}],
        "notifiers": [{"type": "slack"}],
    }
    parsed = tomllib.loads(dumps(data))
    assert parsed == data


def test_dumps_header_emitted_as_comment() -> None:
    out = dumps({"name": "quell"}, header="managed by quell init")
    assert out.startswith("# managed by quell init\n")
    parsed = tomllib.loads(out)
    assert parsed == {"name": "quell"}


def test_dumps_unsupported_type_raises_typeerror() -> None:
    with pytest.raises(TypeError, match="set"):
        dumps({"bad": {1, 2, 3}})  # type: ignore[dict-item]


def test_dumps_empty_list_treated_as_inline_array() -> None:
    """Empty list isn't an array-of-tables — emit ``key = []``."""
    out = dumps({"monitors": []})
    parsed = tomllib.loads(out)
    assert parsed == {"monitors": []}
