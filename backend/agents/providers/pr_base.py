"""
base.py — Abstract async LLM provider interface.

Every provider adapter must subclass AsyncProvider and implement call().
The standard return dict shape:
  {"content": str, "tool_calls": list, "stop_reason": str,
   "llm": str, "model": str, "input_tokens": int, "output_tokens": int}
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AsyncProvider(ABC):
    """Abstract base for all LLM provider adapters."""

    @abstractmethod
    async def call(
        self,
        messages: list[dict],
        system: str = "",
        model: str | None = None,
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Send messages to the LLM and return a standard response dict."""
        ...
