"""
openai.py — OpenAI provider (async).

Wraps AsyncOpenAI for standard chat completions.
"""
from __future__ import annotations

import openai

from core.config import settings
from agents.providers.base import AsyncProvider


def _async_client(api_key: str | None, base_url: str | None = None) -> openai.AsyncOpenAI:
    if base_url:
        return openai.AsyncOpenAI(api_key=api_key or "x", base_url=base_url)
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("No OpenAI API key — set OPENAI_API_KEY or configure via Admin panel")
    return openai.AsyncOpenAI(api_key=key)


def _sync_client(api_key: str | None, base_url: str | None = None) -> openai.OpenAI:
    if base_url:
        return openai.OpenAI(api_key=api_key or "x", base_url=base_url)
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("No OpenAI API key — set OPENAI_API_KEY or configure via Admin panel")
    return openai.OpenAI(api_key=key)


async def call_openai(
    messages: list,
    system: str = "",
    tools: list | None = None,
    max_tokens: int = 4096,
    model: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Async OpenAI chat completion."""
    client = _async_client(api_key)
    chosen_model = model or settings.openai_model

    full_msgs = []
    if system:
        full_msgs.append({"role": "system", "content": system})
    full_msgs.extend(messages)

    kwargs: dict = {"model": chosen_model, "max_tokens": max_tokens, "messages": full_msgs}
    if tools:
        kwargs["tools"] = tools

    response = await client.chat.completions.create(**kwargs)
    msg = response.choices[0].message
    usage = response.usage

    return {
        "content": msg.content or "",
        "tool_calls": msg.tool_calls or [],
        "stop_reason": response.choices[0].finish_reason,
        "llm": "openai",
        "model": chosen_model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "raw": response,
    }


class OpenAIProvider(AsyncProvider):
    async def call(self, messages, system="", model=None, tools=None,
                   max_tokens=4096, api_key=None) -> dict:
        return await call_openai(messages, system=system, model=model,
                                 tools=tools, max_tokens=max_tokens, api_key=api_key)
