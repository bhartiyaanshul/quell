"""Tests for quell.tools — ToolResult, registry, arguments, and formatting."""

from __future__ import annotations

import pytest

from quell.llm.types import ToolParameterSpec
from quell.tools.arguments import coerce_arguments
from quell.tools.formatting import format_observations
from quell.tools.registry import (
    clear_registry,
    get_tool,
    list_tools,
    register_tool,
)
from quell.tools.result import ToolResult
from quell.utils.errors import ToolError

# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


def test_tool_result_success_factory() -> None:
    r = ToolResult.success("ping", "pong")
    assert r.ok is True
    assert r.output == "pong"
    assert r.error == ""
    assert r.tool_name == "ping"


def test_tool_result_failure_factory() -> None:
    r = ToolResult.failure("ping", "connection refused")
    assert r.ok is False
    assert r.error == "connection refused"
    assert r.output == ""


def test_tool_result_truncate_short_output_unchanged() -> None:
    r = ToolResult.success("t", "hello")
    assert r.truncate(max_bytes=1000) is r  # same object — no copy needed


def test_tool_result_truncate_long_output() -> None:
    big = "x" * 200_000
    r = ToolResult.success("t", big)
    capped = r.truncate(max_bytes=1000)
    assert capped.truncated is True
    assert len(capped.output.encode()) <= 1100  # some slack for the notice text
    assert "truncated" in capped.output


def test_tool_result_truncate_preserves_head_and_tail() -> None:
    content = "HEAD" + ("m" * 200_000) + "TAIL"
    r = ToolResult.success("t", content)
    capped = r.truncate(max_bytes=100)
    assert "HEAD" in capped.output
    assert "TAIL" in capped.output


# ---------------------------------------------------------------------------
# Registry — register_tool / get_tool / list_tools
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_registry() -> None:  # type: ignore[return]
    """Wipe the registry before and after every test to avoid pollution."""
    clear_registry()
    yield
    clear_registry()


def test_register_and_get_tool() -> None:
    @register_tool(name="greet", description="Say hello.", execute_in_sandbox=False)
    async def greet() -> ToolResult:
        return ToolResult.success("greet", "hello")

    entry = get_tool("greet")
    assert entry is not None
    fn, meta = entry
    assert meta.name == "greet"
    assert meta.description == "Say hello."
    assert meta.execute_in_sandbox is False


def test_register_duplicate_raises() -> None:
    @register_tool(name="dup", description="first", execute_in_sandbox=False)
    async def dup1() -> ToolResult:
        return ToolResult.success("dup", "1")

    with pytest.raises(ToolError, match="already registered"):

        @register_tool(name="dup", description="second", execute_in_sandbox=False)
        async def dup2() -> ToolResult:
            return ToolResult.success("dup", "2")


def test_list_tools_sorted() -> None:
    @register_tool(name="zebra", description="z", execute_in_sandbox=False)
    async def _z() -> ToolResult:
        return ToolResult.success("zebra", "")

    @register_tool(name="alpha", description="a", execute_in_sandbox=False)
    async def _a() -> ToolResult:
        return ToolResult.success("alpha", "")

    names = [m.name for m in list_tools()]
    assert names == ["alpha", "zebra"]


def test_get_unknown_tool_returns_none() -> None:
    assert get_tool("does_not_exist") is None


# ---------------------------------------------------------------------------
# coerce_arguments
# ---------------------------------------------------------------------------


def _meta(params: list[ToolParameterSpec]) -> object:
    """Build a minimal ToolMetadata-like object with just parameters."""
    from quell.llm.types import ToolMetadata  # noqa: PLC0415

    return ToolMetadata(name="t", description="", parameters=params)


def test_coerce_string_passthrough() -> None:
    meta = _meta([ToolParameterSpec(name="path", type="string", description="")])
    coerced, errors = coerce_arguments({"path": "src/main.py"}, meta)  # type: ignore[arg-type]
    assert errors == []
    assert coerced["path"] == "src/main.py"


def test_coerce_integer() -> None:
    meta = _meta([ToolParameterSpec(name="limit", type="integer", description="")])
    coerced, errors = coerce_arguments({"limit": "10"}, meta)  # type: ignore[arg-type]
    assert errors == []
    assert coerced["limit"] == 10


def test_coerce_float() -> None:
    meta = _meta([ToolParameterSpec(name="ratio", type="float", description="")])
    coerced, errors = coerce_arguments({"ratio": "3.14"}, meta)  # type: ignore[arg-type]
    assert errors == []
    assert abs(float(coerced["ratio"]) - 3.14) < 0.001


def test_coerce_boolean_true_variants() -> None:
    meta = _meta([ToolParameterSpec(name="flag", type="boolean", description="")])
    for val in ("true", "True", "1", "yes", "on"):
        coerced, errors = coerce_arguments({"flag": val}, meta)  # type: ignore[arg-type]
        assert errors == [], f"Expected no error for {val!r}"
        assert coerced["flag"] is True


def test_coerce_boolean_false_variants() -> None:
    meta = _meta([ToolParameterSpec(name="flag", type="boolean", description="")])
    for val in ("false", "False", "0", "no", "off"):
        coerced, errors = coerce_arguments({"flag": val}, meta)  # type: ignore[arg-type]
        assert coerced["flag"] is False


def test_coerce_missing_required_param() -> None:
    meta = _meta([ToolParameterSpec(name="path", type="string", description="")])
    _, errors = coerce_arguments({}, meta)  # type: ignore[arg-type]
    assert any("Missing required parameter" in e for e in errors)


def test_coerce_missing_optional_param_ok() -> None:
    meta = _meta(
        [
            ToolParameterSpec(
                name="limit", type="integer", description="", required=False
            )
        ]
    )
    coerced, errors = coerce_arguments({}, meta)  # type: ignore[arg-type]
    assert errors == []
    assert "limit" not in coerced


def test_coerce_bad_integer_produces_error() -> None:
    meta = _meta([ToolParameterSpec(name="n", type="integer", description="")])
    _, errors = coerce_arguments({"n": "not_a_number"}, meta)  # type: ignore[arg-type]
    assert any("cannot coerce" in e for e in errors)


def test_coerce_extra_params_passed_through() -> None:
    meta = _meta([ToolParameterSpec(name="path", type="string", description="")])
    coerced, errors = coerce_arguments(  # type: ignore[arg-type]
        {"path": "x", "undeclared": "y"}, meta
    )
    assert errors == []
    assert coerced["undeclared"] == "y"


# ---------------------------------------------------------------------------
# format_observations
# ---------------------------------------------------------------------------


def test_format_observations_success() -> None:
    r = ToolResult.success("code_read", "def main(): pass")
    out = format_observations([r])
    assert 'name="code_read"' in out
    assert 'status="ok"' in out
    assert "def main(): pass" in out


def test_format_observations_failure() -> None:
    r = ToolResult.failure("git_log", "git not found")
    out = format_observations([r])
    assert 'status="error"' in out
    assert "git not found" in out


def test_format_observations_multiple() -> None:
    results = [
        ToolResult.success("a", "output_a"),
        ToolResult.success("b", "output_b"),
    ]
    out = format_observations(results)
    assert 'name="a"' in out
    assert 'name="b"' in out


def test_format_observations_empty_list() -> None:
    out = format_observations([])
    assert "no tool results" in out
