"""
claude.py — Anthropic Claude provider (async).

Wraps AsyncAnthropic so calls never block the event loop.
Returns standard dict: {content, tool_calls, stop_reason, llm, model, input_tokens, output_tokens}
"""
from __future__ import annotations

import anthropic

from core.config import settings
from agents.providers.base import AsyncProvider


def _client(api_key: str | None) -> anthropic.AsyncAnthropic:
    key = api_key or settings.anthropic_api_key
    if not key:
        raise ValueError("No Anthropic API key — set ANTHROPIC_API_KEY or configure via Admin panel")
    return anthropic.AsyncAnthropic(api_key=key)


def _sync_client(api_key: str | None) -> anthropic.Anthropic:
    key = api_key or settings.anthropic_api_key
    if not key:
        raise ValueError("No Anthropic API key — set ANTHROPIC_API_KEY or configure via Admin panel")
    return anthropic.Anthropic(api_key=key)


async def call_claude(
    messages: list,
    system: str = "",
    tools: list | None = None,
    max_tokens: int = 4096,
    model: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Async Claude call — uses AsyncAnthropic to avoid blocking the event loop."""
    client = _client(api_key)
    chosen_model = model or settings.claude_model

    kwargs: dict = {
        "model": chosen_model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    response = await client.messages.create(**kwargs)

    content_blocks = response.content
    text_parts = [b.text for b in content_blocks if hasattr(b, "text")]
    tool_calls = [b for b in content_blocks if b.type == "tool_use"]

    return {
        "content": "\n".join(text_parts),
        "tool_calls": tool_calls,
        "stop_reason": response.stop_reason,
        "llm": "claude",
        "model": chosen_model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "raw": response,
    }


class ClaudeProvider(AsyncProvider):
    async def call(self, messages, system="", model=None, tools=None,
                   max_tokens=4096, api_key=None) -> dict:
        return await call_claude(messages, system=system, model=model,
                                 tools=tools, max_tokens=max_tokens, api_key=api_key)
