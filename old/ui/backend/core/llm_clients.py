"""
Unified LLM client wrappers for Claude, DeepSeek, Gemini, Grok.

All functions are truly async — they use the provider's async client so they
never block the asyncio event loop during the LLM API call.

Each function accepts an optional `api_key` parameter.
  - Cloud mode: client sends their own key in X-*-Key headers; the key is
    passed here per-call and never stored server-side.
  - Local dev mode: falls back to settings.* keys from .env when no key supplied.

Each returns a standard dict:
  {"content": str, "llm": str, "model": str,
   "input_tokens": int, "output_tokens": int}
"""
import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import anthropic
import openai
from google import genai as google_genai
from google.genai import types as genai_types

from config import settings


def _async_anthropic_client(api_key: str | None) -> anthropic.AsyncAnthropic:
    key = api_key or settings.anthropic_api_key
    if not key:
        raise ValueError("No Anthropic API key — set ANTHROPIC_API_KEY or send X-Anthropic-Key header")
    return anthropic.AsyncAnthropic(api_key=key)


def _async_openai_client(api_key: str | None, base_url: str | None = None) -> openai.AsyncOpenAI:
    if base_url:
        return openai.AsyncOpenAI(api_key=api_key or "x", base_url=base_url)
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("No OpenAI API key — set OPENAI_API_KEY or send X-OpenAI-Key header")
    return openai.AsyncOpenAI(api_key=key)


# Keep sync helpers for non-async callers (chat.py etc.)
def _anthropic_client(api_key: str | None) -> anthropic.Anthropic:
    key = api_key or settings.anthropic_api_key
    if not key:
        raise ValueError("No Anthropic API key — set ANTHROPIC_API_KEY or send X-Anthropic-Key header")
    return anthropic.Anthropic(api_key=key)


def _openai_client(api_key: str | None, base_url: str | None = None) -> openai.OpenAI:
    if base_url:
        return openai.OpenAI(api_key=api_key or "x", base_url=base_url)
    key = api_key or settings.openai_api_key
    if not key:
        raise ValueError("No OpenAI API key — set OPENAI_API_KEY or send X-OpenAI-Key header")
    return openai.OpenAI(api_key=key)


# ── Claude ────────────────────────────────────────────────────────────────────

async def call_claude(
    messages: list,
    system: str = "",
    tools: list = None,
    max_tokens: int = 4096,
    model: str = None,
    api_key: str | None = None,
) -> dict:
    """Async Claude call — uses AsyncAnthropic to avoid blocking the event loop."""
    client = _async_anthropic_client(api_key)
    chosen_model = model or settings.claude_model

    kwargs = {
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


# ── DeepSeek ──────────────────────────────────────────────────────────────────

async def call_deepseek(
    messages: list,
    system: str = "",
    tools: list = None,
    tool_choice: str = "auto",
    max_tokens: int = 4096,
    reasoner: bool = False,
    api_key: str | None = None,
) -> dict:
    """Async DeepSeek call via AsyncOpenAI."""
    key = api_key or settings.deepseek_api_key
    if not key:
        raise ValueError("No DeepSeek API key — set DEEPSEEK_API_KEY or send X-DeepSeek-Key header")
    client = openai.AsyncOpenAI(api_key=key, base_url="https://api.deepseek.com")

    chosen_model = settings.deepseek_reasoner_model if reasoner else settings.deepseek_model
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    kwargs: dict = {"model": chosen_model, "max_tokens": max_tokens, "messages": full_messages}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice

    response = await client.chat.completions.create(**kwargs)
    msg = response.choices[0].message
    usage = response.usage

    return {
        "content": msg.content or "",
        "tool_calls": msg.tool_calls or [],
        "llm": "deepseek",
        "model": chosen_model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "raw": response,
    }


# ── Gemini ────────────────────────────────────────────────────────────────────

async def call_gemini(
    prompt: str,
    system: str = "",
    tools: list = None,
    model: str = None,
    api_key: str | None = None,
) -> dict:
    """Async Gemini call via asyncio.to_thread (google-genai uses sync I/O)."""
    key = api_key or settings.gemini_api_key
    if not key:
        raise ValueError("No Gemini API key — set GEMINI_API_KEY or send X-Gemini-Key header")

    model_name = model or settings.gemini_model

    def _sync_call() -> dict:
        client = google_genai.Client(api_key=key)
        cfg = genai_types.GenerateContentConfig(system_instruction=system) if system else None
        kwargs: dict = {"model": model_name, "contents": prompt}
        if cfg:
            kwargs["config"] = cfg
        response = client.models.generate_content(**kwargs)
        usage = getattr(response, "usage_metadata", None)
        return {
            "content": response.text,
            "tool_calls": [],
            "llm": "gemini",
            "model": model_name,
            "input_tokens": getattr(usage, "prompt_token_count", 0) if usage else 0,
            "output_tokens": getattr(usage, "candidates_token_count", 0) if usage else 0,
        }

    return await asyncio.to_thread(_sync_call)


# ── Grok ──────────────────────────────────────────────────────────────────────

async def call_grok(
    messages: list,
    system: str = "",
    max_tokens: int = 2048,
    api_key: str | None = None,
) -> dict:
    """Async Grok call via AsyncOpenAI."""
    key = api_key or settings.grok_api_key
    if not key:
        raise ValueError("No Grok API key — set XAI_API_KEY or send X-Grok-Key header")
    client = openai.AsyncOpenAI(api_key=key, base_url="https://api.x.ai/v1")

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    response = await client.chat.completions.create(
        model=settings.grok_model,
        max_tokens=max_tokens,
        messages=full_messages,
    )
    usage = response.usage

    return {
        "content": response.choices[0].message.content,
        "tool_calls": [],
        "llm": "grok",
        "model": settings.grok_model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
        "raw": response,
    }
