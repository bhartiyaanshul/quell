"""LiteLLM wrapper for the Quell LLM layer.

:class:`LLM` is the single point of contact with any language model.
All LLM calls in Quell route through this class.  Direct use of the
``openai``, ``anthropic``, or any other provider SDK is forbidden.

Usage::

    from quell.config.schema import LLMConfig
    from quell.llm.llm import LLM
    from quell.llm.types import LLMMessage

    llm = LLM(config)
    response = await llm.generate([
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="What broke?"),
    ])
    print(response.content)
"""

from __future__ import annotations

import litellm

from quell.config.schema import LLMConfig
from quell.llm.compression import compress_messages
from quell.llm.types import LLMMessage, LLMResponse, ToolMetadata
from quell.utils.errors import LLMError

# Silence litellm's verbose startup logging.
litellm.suppress_debug_info = True


class LLM:
    """Async LiteLLM wrapper.

    Args:
        config: The :class:`~quell.config.schema.LLMConfig` for this
                instance (model string, api_key, api_base, etc.).
    """

    def __init__(self, config: LLMConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[ToolMetadata] | None = None,
    ) -> LLMResponse:
        """Send *messages* to the configured LLM and return the response.

        Automatically compresses the conversation history when it
        approaches the model's context window.

        Args:
            messages: Conversation history (system + user/assistant turns).
            tools:    Optional tool catalogue injected into the system
                      prompt as a reference (not used for JSON function
                      calling — we use XML tool calls instead).

        Returns:
            :class:`~quell.llm.types.LLMResponse` with content and usage.

        Raises:
            :exc:`~quell.utils.errors.LLMError` on provider errors.
        """
        compressed = compress_messages(
            messages,
            max_tokens=self._config.max_context_tokens,
        )

        if tools:
            compressed = self._inject_tool_catalogue(compressed, tools)

        litellm_messages = [{"role": m.role, "content": m.content} for m in compressed]

        kwargs: dict[str, object] = {
            "model": self._config.model,
            "messages": litellm_messages,
        }
        if self._config.api_key:
            kwargs["api_key"] = self._config.api_key
        if self._config.api_base:
            kwargs["api_base"] = self._config.api_base

        try:
            raw = await litellm.acompletion(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"LiteLLM call failed: {exc}") from exc

        return LLMResponse.from_litellm(raw)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _inject_tool_catalogue(
        messages: list[LLMMessage],
        tools: list[ToolMetadata],
    ) -> list[LLMMessage]:
        """Append an XML tool catalogue to the system message content."""
        if not messages:
            return messages

        catalogue_lines = ["<available_tools>"]
        for tool in tools:
            catalogue_lines.append(f"  <tool name={tool.name!r}>")
            catalogue_lines.append(f"    <description>{tool.description}</description>")
            for p in tool.parameters:
                req = "required" if p.required else "optional"
                catalogue_lines.append(
                    f"    <parameter name={p.name!r} type={p.type!r}"
                    f" required={req!r}>{p.description}</parameter>"
                )
            catalogue_lines.append("  </tool>")
        catalogue_lines.append("</available_tools>")
        catalogue = "\n".join(catalogue_lines)

        updated = list(messages)
        if updated[0].role == "system":
            updated[0] = LLMMessage(
                role="system",
                content=f"{updated[0].content}\n\n{catalogue}",
            )
        else:
            updated.insert(0, LLMMessage(role="system", content=catalogue))
        return updated


__all__ = ["LLM"]
