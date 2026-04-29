"""
deepseek.py — DeepSeek provider via OpenAI-compatible async client.
"""
from __future__ import annotations

import openai

from core.config import settings
from agents.providers.pr_base import AsyncProvider


async def call_deepseek(
    messages: list,
    system: str = "",
    tools: list | None = None,
    tool_choice: str = "auto",
    max_tokens: int = 4096,
    reasoner: bool = False,
    api_key: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Async DeepSeek call via AsyncOpenAI."""
    key = api_key or settings.deepseek_api_key
    if not key:
        raise ValueError("No DeepSeek API key — set DEEPSEEK_API_KEY or configure via Admin panel")
    client = openai.AsyncOpenAI(api_key=key, base_url="https://api.deepseek.com")

    chosen_model = settings.deepseek_reasoner_model if reasoner else settings.deepseek_model
    full_msgs = []
    if system:
        full_msgs.append({"role": "system", "content": system})
    full_msgs.extend(messages)

    kwargs: dict = {"model": chosen_model, "max_tokens": max_tokens, "messages": full_msgs}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    if temperature is not None:
        kwargs["temperature"] = temperature

    response = await client.chat.completions.create(**kwargs)
    msg = response.choices[0].message
    usage = response.usage

    return {
        "content": msg.content or "",
        "tool_calls": msg.tool_calls or [],
        "stop_reason": response.choices[0].finish_reason,
        "llm": "deepseek",
        "model": chosen_model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "raw": response,
    }


class DeepSeekProvider(AsyncProvider):
    async def call(self, messages, system="", model=None, tools=None,
                   max_tokens=4096, api_key=None, temperature=None) -> dict:
        return await call_deepseek(messages, system=system, tools=tools,
                                   max_tokens=max_tokens, api_key=api_key,
                                   temperature=temperature)
