"""Tests for quell.llm — compression, types, and LLM wrapper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from quell.config.schema import LLMConfig
from quell.llm.compression import compress_messages
from quell.llm.llm import LLM
from quell.llm.types import (
    LLMMessage,
    LLMResponse,
    ToolMetadata,
    ToolParameterSpec,
)
from quell.utils.errors import LLMError

# ---------------------------------------------------------------------------
# LLMMessage
# ---------------------------------------------------------------------------


def test_llm_message_fields() -> None:
    """LLMMessage stores role and content."""
    m = LLMMessage(role="user", content="hello")
    assert m.role == "user"
    assert m.content == "hello"


# ---------------------------------------------------------------------------
# LLMResponse.from_litellm
# ---------------------------------------------------------------------------


def _fake_litellm_response(content: str, model: str = "x") -> MagicMock:
    """Build a minimal mock that looks like a LiteLLM ModelResponse."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 5
    raw = MagicMock()
    raw.choices = [choice]
    raw.usage = usage
    raw.model = model
    return raw


def test_llm_response_from_litellm_content() -> None:
    """from_litellm extracts content correctly."""
    resp = LLMResponse.from_litellm(_fake_litellm_response("hello world"))
    assert resp.content == "hello world"


def test_llm_response_from_litellm_tokens() -> None:
    """from_litellm extracts token counts."""
    resp = LLMResponse.from_litellm(_fake_litellm_response("hi"))
    assert resp.input_tokens == 10
    assert resp.output_tokens == 5


def test_llm_response_from_litellm_model() -> None:
    """from_litellm captures the model string."""
    resp = LLMResponse.from_litellm(_fake_litellm_response("hi", model="gpt-4o"))
    assert resp.model == "gpt-4o"


# ---------------------------------------------------------------------------
# compress_messages
# ---------------------------------------------------------------------------


def _msgs(n: int, include_system: bool = True) -> list[LLMMessage]:
    """Build a message list of length *n* (optionally with a system message)."""
    out: list[LLMMessage] = []
    if include_system:
        out.append(LLMMessage(role="system", content="sys"))
    for i in range(n - (1 if include_system else 0)):
        role = "user" if i % 2 == 0 else "assistant"
        out.append(LLMMessage(role=role, content=f"message {i}"))
    return out


def test_compress_no_op_below_threshold() -> None:
    """No compression when token estimate is below max_tokens."""
    msgs = _msgs(5)
    result = compress_messages(msgs, max_tokens=999_999)
    assert result == msgs


def test_compress_reduces_length() -> None:
    """Compression reduces a long history."""
    # Create a history where characters >> threshold
    big_msgs = [LLMMessage(role="system", content="sys")]
    for i in range(40):
        big_msgs.append(
            LLMMessage(role="user" if i % 2 == 0 else "assistant", content="x" * 400)
        )
    result = compress_messages(big_msgs, max_tokens=100, keep_last=5)
    assert len(result) < len(big_msgs)


def test_compress_preserves_system_message() -> None:
    """The system message is always the first element after compression."""
    big_msgs = [LLMMessage(role="system", content="SYSTEM")]
    for _ in range(30):
        big_msgs.append(LLMMessage(role="user", content="x" * 500))
    result = compress_messages(big_msgs, max_tokens=10, keep_last=3)
    assert result[0].role == "system"
    assert result[0].content == "SYSTEM"


def test_compress_preserves_tail() -> None:
    """The last keep_last messages are always preserved verbatim."""
    tail_content = [f"tail-{i}" for i in range(5)]
    big_msgs = [LLMMessage(role="system", content="sys")]
    big_msgs += [LLMMessage(role="user", content="x" * 500) for _ in range(20)]
    big_msgs += [LLMMessage(role="user", content=c) for c in tail_content]
    result = compress_messages(big_msgs, max_tokens=10, keep_last=5)
    result_tail_contents = [m.content for m in result[-5:]]
    assert result_tail_contents == tail_content


def test_compress_summary_message_injected() -> None:
    """A summary message is injected when compression occurs."""
    big_msgs = [LLMMessage(role="system", content="sys")]
    big_msgs += [LLMMessage(role="user", content="x" * 1000) for _ in range(10)]
    result = compress_messages(big_msgs, max_tokens=10, keep_last=3)
    # Second message (after system) should be the summary
    assert "[Compressed conversation history]" in result[1].content


def test_compress_no_op_when_already_small() -> None:
    """Does not compress when history is already at minimum size."""
    msgs = _msgs(4)
    result = compress_messages(msgs, max_tokens=1, keep_last=10)
    assert result == msgs


# ---------------------------------------------------------------------------
# LLM.generate (mocked litellm)
# ---------------------------------------------------------------------------


async def test_llm_generate_returns_response() -> None:
    """generate() returns a LLMResponse on success."""
    config = LLMConfig(model="anthropic/claude-haiku-4-5", api_key="test-key")
    llm = LLM(config)

    fake_raw = _fake_litellm_response("I found the bug.")

    with patch(
        "quell.llm.llm.litellm.acompletion", new=AsyncMock(return_value=fake_raw)
    ):
        resp = await llm.generate([LLMMessage(role="user", content="What broke?")])

    assert resp.content == "I found the bug."


async def test_llm_generate_raises_llm_error_on_exception() -> None:
    """generate() wraps provider errors in LLMError."""
    config = LLMConfig(model="openai/gpt-4o", api_key="bad-key")
    llm = LLM(config)

    with (
        patch(
            "quell.llm.llm.litellm.acompletion",
            new=AsyncMock(side_effect=RuntimeError("rate limited")),
        ),
        pytest.raises(LLMError, match="rate limited"),
    ):
        await llm.generate([LLMMessage(role="user", content="hello")])


async def test_llm_generate_passes_api_key() -> None:
    """generate() forwards api_key to litellm when configured."""
    config = LLMConfig(model="openai/gpt-4o", api_key="sk-test")
    llm = LLM(config)
    fake_raw = _fake_litellm_response("ok")

    with patch(
        "quell.llm.llm.litellm.acompletion", new=AsyncMock(return_value=fake_raw)
    ) as mock_call:
        await llm.generate([LLMMessage(role="user", content="hi")])

    call_kwargs = mock_call.call_args.kwargs
    assert call_kwargs.get("api_key") == "sk-test"


async def test_llm_generate_with_tools_injects_catalogue() -> None:
    """generate() with tools appends the tool catalogue to the system message."""
    config = LLMConfig(model="anthropic/claude-haiku-4-5")
    llm = LLM(config)
    tools = [
        ToolMetadata(
            name="code_read",
            description="Read a file.",
            parameters=[
                ToolParameterSpec(name="path", type="string", description="File path")
            ],
        )
    ]
    fake_raw = _fake_litellm_response("done")
    messages = [
        LLMMessage(role="system", content="You are an agent."),
        LLMMessage(role="user", content="read app.py"),
    ]

    with patch(
        "quell.llm.llm.litellm.acompletion", new=AsyncMock(return_value=fake_raw)
    ) as mock_call:
        await llm.generate(messages, tools=tools)

    sent = mock_call.call_args.kwargs["messages"]
    system_content = sent[0]["content"]
    assert "<available_tools>" in system_content
    assert "code_read" in system_content


async def test_llm_generate_passes_api_base() -> None:
    """generate() forwards api_base when configured (e.g. for Ollama)."""
    config = LLMConfig(model="ollama/llama3", api_base="http://localhost:11434")
    llm = LLM(config)
    fake_raw = _fake_litellm_response("local response")

    with patch(
        "quell.llm.llm.litellm.acompletion", new=AsyncMock(return_value=fake_raw)
    ) as mock_call:
        await llm.generate([LLMMessage(role="user", content="hi")])

    call_kwargs = mock_call.call_args.kwargs
    assert call_kwargs.get("api_base") == "http://localhost:11434"
