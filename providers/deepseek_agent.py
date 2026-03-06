"""
DeepSeek provider — uses OpenAI-compatible API.

DeepSeek's API is compatible with the OpenAI SDK.
Models: deepseek-chat (DeepSeek-V3), deepseek-reasoner (R1).
"""

import os
from typing import Generator

from openai import OpenAI

from providers.base import BaseProvider


class DeepSeekAgent(BaseProvider):

    name = "deepseek"

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key_env: str = "DEEPSEEK_API_KEY",
        logger=None,
        **kwargs,
    ):
        self.model = model
        self.logger = logger
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"DeepSeek API key not found in env var: {api_key_env}")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        # Conversation history for multi-turn sessions
        self.messages: list[dict] = []

    def _build_messages(self, prompt: str, system: str = "") -> list[dict]:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def _call(self, prompt: str, system: str = "") -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(prompt, system),
        )
        output = response.choices[0].message.content or ""

        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": output})

        if self.logger:
            usage = response.usage
            if usage:
                self.logger.info(
                    "deepseek_response",
                    model=self.model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                )
        return output

    def _stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self._build_messages(prompt, system),
            stream=True,
        )
        full_output = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_output += delta
                yield delta

        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": full_output})

    def clear_history(self) -> None:
        self.messages = []
