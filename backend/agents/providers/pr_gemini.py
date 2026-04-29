"""
gemini.py — Google Gemini provider via asyncio.to_thread (google-genai uses sync I/O).
"""
from __future__ import annotations

import asyncio

from core.config import settings
from agents.providers.pr_base import AsyncProvider


async def call_gemini(
    prompt: str,
    system: str = "",
    tools: list | None = None,
    model: str | None = None,
    api_key: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Async Gemini call via asyncio.to_thread."""
    key = api_key or settings.gemini_api_key
    if not key:
        raise ValueError("No Gemini API key — set GEMINI_API_KEY or configure via Admin panel")

    model_name = model or settings.gemini_model

    def _sync_call() -> dict:
        from google import genai as google_genai
        from google.genai import types as genai_types

        client = google_genai.Client(api_key=key)
        cfg_kwargs: dict = {}
        if system:
            cfg_kwargs["system_instruction"] = system
        if temperature is not None:
            cfg_kwargs["temperature"] = temperature
        cfg = genai_types.GenerateContentConfig(**cfg_kwargs) if cfg_kwargs else None
        kwargs: dict = {"model": model_name, "contents": prompt}
        if cfg:
            kwargs["config"] = cfg
        response = client.models.generate_content(**kwargs)
        usage = getattr(response, "usage_metadata", None)
        return {
            "content": response.text,
            "tool_calls": [],
            "stop_reason": "end_turn",
            "llm": "gemini",
            "model": model_name,
            "input_tokens": getattr(usage, "prompt_token_count", 0) if usage else 0,
            "output_tokens": getattr(usage, "candidates_token_count", 0) if usage else 0,
        }

    return await asyncio.to_thread(_sync_call)


class GeminiProvider(AsyncProvider):
    async def call(self, messages, system="", model=None, tools=None,
                   max_tokens=4096, api_key=None, temperature=None) -> dict:
        # Gemini takes a string prompt; combine messages into one string
        user_text = " ".join(
            m["content"] for m in messages if m.get("role") == "user"
        )
        return await call_gemini(user_text, system=system, model=model,
                                 api_key=api_key, temperature=temperature)
