"""
OpenAI provider using the openai Python SDK (chat completions API).

Inherits BaseProvider for retry/fallback support.
Maintains a conversation messages list for multi-turn context.
"""

import os
from typing import Generator

from openai import OpenAI

from providers.base import BaseProvider


class OpenAIAgent(BaseProvider):

    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4.1",
        api_key_env: str = "OPENAI_API_KEY",
        logger=None,
        **kwargs,
    ):
        self.model = model
        self.logger = logger
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"OpenAI API key not found in env var: {api_key_env}")
        self.client = OpenAI(api_key=api_key)

        # Conversation history for multi-turn use
        self.messages: list[dict] = []

    # ------------------------------------------------------------------
    # Legacy interface: send(system_prompt, user_prompt) → str
    # Used by git_supervisor, docs, summary modules which pass both args.
    # ------------------------------------------------------------------

    def send(self, system_prompt: str, user_prompt: str = "") -> str:  # type: ignore[override]
        """
        Two-arg send for backward compatibility: send(system, user) → str.
        Does NOT use conversation history (one-shot utility calls).
        """
        if self.logger:
            self.logger.info("openai_request", model=self.model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        elif system_prompt:
            # Single-arg call: treat system_prompt as the full prompt
            messages = [{"role": "user", "content": system_prompt}]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        output = response.choices[0].message.content or ""

        if self.logger:
            usage = response.usage
            if usage:
                self.logger.info(
                    "openai_response",
                    length=len(output),
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                )
        return output

    # ------------------------------------------------------------------
    # BaseProvider interface (used by WorkflowRunner + /compare)
    # ------------------------------------------------------------------

    def _call(self, prompt: str, system: str = "") -> str:
        """Single non-streaming call. Appends to conversation history."""
        if self.messages or system:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.extend(self.messages)
            messages.append({"role": "user", "content": prompt})
        else:
            messages = [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        output = response.choices[0].message.content or ""

        # Maintain history
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": output})

        if self.logger:
            usage = response.usage
            if usage:
                self.logger.info(
                    "openai_response",
                    model=self.model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                )
        return output

    def _stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        """Stream tokens. Appends completed response to conversation history."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(self.messages)
        messages.append({"role": "user", "content": prompt})

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )

        full_output = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_output += delta
                yield delta

        # Maintain history
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": full_output})

    def clear_history(self) -> None:
        self.messages = []
