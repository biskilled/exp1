"""
Google Gemini provider — uses google-genai SDK (v1+).

Install: pip install google-genai
Models: gemini-2.0-flash, gemini-2.0-flash-thinking, gemini-1.5-pro

Uses client.chats.create(history=...) for multi-turn conversations.
History format (native): list of google.genai.types.Content objects.
Stored internally as plain dicts for JSON serialisation and SessionStore
compatibility; converted to Content objects on each call.
"""

import os
from typing import Generator

from providers.base import BaseProvider


class GeminiAgent(BaseProvider):

    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        api_key_env: str = "GEMINI_API_KEY",
        logger=None,
        **kwargs,
    ):
        self.model = model
        self.logger = logger

        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"Gemini API key not found in env var: {api_key_env}")

        try:
            from google import genai
            from google.genai import types as genai_types
            self._client = genai.Client(api_key=api_key)
            self._types = genai_types
        except ImportError:
            raise ImportError(
                "google-genai not installed. Run: pip install google-genai"
            )

        # Conversation history stored as plain dicts for JSON serialisation.
        # Format: [{"role": "user"/"model", "parts": [{"text": "..."}]}]
        self._history: list[dict] = []

    # ------------------------------------------------------------------

    def _to_content_list(self, history: list[dict]):
        """Convert plain dict history to google.genai.types.Content objects."""
        result = []
        for m in history:
            role = m.get("role", "user")
            parts_raw = m.get("parts", [])
            parts = [self._types.Part(text=p.get("text", "")) for p in parts_raw]
            result.append(self._types.Content(role=role, parts=parts))
        return result

    def _make_config(self, system: str = ""):
        if system:
            return self._types.GenerateContentConfig(system_instruction=system)
        return None

    def _call(self, prompt: str, system: str = "") -> str:
        cfg = self._make_config(system)
        kwargs = {"model": self.model, "history": self._to_content_list(self._history)}
        if cfg:
            kwargs["config"] = cfg
        chat = self._client.chats.create(**kwargs)
        response = chat.send_message(prompt)
        output = response.text or ""

        self._history.append({"role": "user", "parts": [{"text": prompt}]})
        self._history.append({"role": "model", "parts": [{"text": output}]})

        if self.logger:
            self.logger.info("gemini_response", model=self.model, length=len(output))

        return output

    def _stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        cfg = self._make_config(system)
        kwargs = {"model": self.model, "history": self._to_content_list(self._history)}
        if cfg:
            kwargs["config"] = cfg
        chat = self._client.chats.create(**kwargs)

        full_output = ""
        for chunk in chat.send_message_stream(prompt):
            if chunk.text:
                full_output += chunk.text
                yield chunk.text

        self._history.append({"role": "user", "parts": [{"text": prompt}]})
        self._history.append({"role": "model", "parts": [{"text": full_output}]})

    def clear_history(self) -> None:
        self._history = []

    # ------------------------------------------------------------------
    # SessionStore compatibility: expose .messages in a uniform format
    # ------------------------------------------------------------------

    @property
    def messages(self) -> list[dict]:
        """Return history as plain dicts (Gemini native format) for SessionStore."""
        return self._history

    @messages.setter
    def messages(self, history: list[dict]) -> None:
        """Restore history from SessionStore (accepts OpenAI or Gemini format)."""
        converted = []
        for m in history:
            role = m.get("role", "user")
            if role == "assistant":
                role = "model"
            parts = m.get("parts")
            if parts is None:
                parts = [{"text": m.get("content", "")}]
            converted.append({"role": role, "parts": parts})
        self._history = converted
