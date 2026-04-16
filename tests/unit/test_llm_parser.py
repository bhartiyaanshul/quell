"""Tests for quell.llm.parser — XML tool-call parser."""

from __future__ import annotations

from quell.llm.parser import parse_tool_invocations
from quell.llm.types import ToolInvocation

# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------


def test_parse_single_function_block() -> None:
    """Parses a single <function=name> block with one parameter."""
    text = """
<function=code_read>
<parameter=path>src/main.py</parameter>
</function>
"""
    result = parse_tool_invocations(text)
    assert len(result) == 1
    assert result[0].name == "code_read"
    assert result[0].parameters["path"] == "src/main.py"


def test_parse_multiple_function_blocks() -> None:
    """Parses multiple consecutive <function=...> blocks."""
    text = """
<function=git_log>
<parameter=limit>10</parameter>
</function>
<function=code_grep>
<parameter=pattern>TODO</parameter>
<parameter=path>src/</parameter>
</function>
"""
    result = parse_tool_invocations(text)
    assert len(result) == 2
    assert result[0].name == "git_log"
    assert result[1].name == "code_grep"
    assert result[1].parameters["pattern"] == "TODO"
    assert result[1].parameters["path"] == "src/"


def test_parse_invoke_format() -> None:
    """Parses alternate <invoke name="..."> format."""
    text = """
<invoke name="git_blame">
  <parameter name="path">src/checkout.py</parameter>
  <parameter name="start_line">40</parameter>
</invoke>
"""
    result = parse_tool_invocations(text)
    assert len(result) == 1
    assert result[0].name == "git_blame"
    assert result[0].parameters["path"] == "src/checkout.py"
    assert result[0].parameters["start_line"] == "40"


def test_parse_mixed_formats() -> None:
    """Both <function=...> and <invoke name=...> coexist in one response."""
    text = """
<function=code_read>
<parameter=path>app.py</parameter>
</function>
Some reasoning text here.
<invoke name="test_run">
  <parameter name="cmd">pytest</parameter>
</invoke>
"""
    result = parse_tool_invocations(text)
    assert len(result) == 2
    names = [r.name for r in result]
    assert "code_read" in names
    assert "test_run" in names


def test_parse_preserves_document_order() -> None:
    """Invocations are returned in the order they appear in the text."""
    text = """
<function=first_tool>
<parameter=x>1</parameter>
</function>
<invoke name="second_tool">
  <parameter name="y">2</parameter>
</invoke>
<function=third_tool>
<parameter=z>3</parameter>
</function>
"""
    result = parse_tool_invocations(text)
    assert [r.name for r in result] == ["first_tool", "second_tool", "third_tool"]


def test_parse_multiline_parameter_value() -> None:
    """Parameter values may contain newlines (e.g. code snippets)."""
    text = (
        "<function=propose_fix>\n"
        "<parameter=diff>--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x=1\n+x=2\n"
        "</parameter>\n"
        "</function>"
    )
    result = parse_tool_invocations(text)
    assert len(result) == 1
    assert "--- a/app.py" in result[0].parameters["diff"]


def test_parse_no_invocations() -> None:
    """Returns empty list when no tool calls are present."""
    text = "I have finished my analysis. No tools needed."
    assert parse_tool_invocations(text) == []


def test_parse_empty_string() -> None:
    """Returns empty list for an empty string."""
    assert parse_tool_invocations("") == []


def test_parse_raw_xml_preserved() -> None:
    """raw_xml on the result contains the verbatim matched block."""
    text = "<function=ping>\n<parameter=msg>hello</parameter>\n</function>"
    result = parse_tool_invocations(text)
    assert result[0].raw_xml == text.strip()


def test_parse_no_parameters() -> None:
    """A function block with no parameters yields an empty dict."""
    text = "<function=agent_finish>\n</function>"
    result = parse_tool_invocations(text)
    assert result[0].parameters == {}


def test_parse_returns_tool_invocation_type() -> None:
    """Each element is a ToolInvocation dataclass."""
    text = "<function=x>\n<parameter=k>v</parameter>\n</function>"
    result = parse_tool_invocations(text)
    assert isinstance(result[0], ToolInvocation)


def test_parse_case_insensitive_tags() -> None:
    """Tag matching is case-insensitive."""
    text = "<FUNCTION=shout>\n<PARAMETER=msg>LOUD</PARAMETER>\n</FUNCTION>"
    result = parse_tool_invocations(text)
    assert len(result) == 1
    assert result[0].parameters["msg"] == "LOUD"
