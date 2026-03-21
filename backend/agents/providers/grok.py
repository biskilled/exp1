"""
grok.py — xAI Grok provider via OpenAI-compatible async client.
"""
from __future__ import annotations

import openai

from core.config import settings
from agents.providers.base import AsyncProvider


async def call_grok(
    messages: list,
    system: str = "",
    max_tokens: int = 2048,
    model: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Async Grok call via AsyncOpenAI."""
    key = api_key or settings.grok_api_key
    if not key:
        raise ValueError("No Grok API key — set XAI_API_KEY or configure via Admin panel")
    client = openai.AsyncOpenAI(api_key=key, base_url="https://api.x.ai/v1")

    chosen_model = model or settings.grok_model
    full_msgs = []
    if system:
        full_msgs.append({"role": "system", "content": system})
    full_msgs.extend(messages)

    response = await client.chat.completions.create(
        model=chosen_model,
        max_tokens=max_tokens,
        messages=full_msgs,
    )
    usage = response.usage

    return {
        "content": response.choices[0].message.content or "",
        "tool_calls": [],
        "stop_reason": response.choices[0].finish_reason,
        "llm": "grok",
        "model": chosen_model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "raw": response,
    }


class GrokProvider(AsyncProvider):
    async def call(self, messages, system="", model=None, tools=None,
                   max_tokens=2048, api_key=None) -> dict:
        return await call_grok(messages, system=system, model=model,
                               max_tokens=max_tokens, api_key=api_key)
