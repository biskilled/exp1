"""
BaseProvider — abstract base class for all LLM providers.

Provides:
- stream(prompt, system) → AsyncGenerator or sync generator
- send(prompt, system) → str  (non-streaming convenience)
- Retry logic: 3 attempts with exponential backoff (1s / 3s / 10s)
- Fallback: if all retries fail, delegate to fallback_provider
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Generator

logger = logging.getLogger(__name__)

BACKOFF_DELAYS = [1, 3, 10]


class BaseProvider(ABC):
    """Abstract base for all LLM providers."""

    name: str = "base"
    fallback: "BaseProvider | None" = None
    max_retries: int = 3

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _call(self, prompt: str, system: str = "") -> str:
        """Make a single (non-streaming) call. Raise on error."""
        ...

    def _stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        """Stream tokens. Default: single-chunk from _call()."""
        yield self._call(prompt, system)

    # ------------------------------------------------------------------
    # Public interface (with retry + fallback)
    # ------------------------------------------------------------------

    def send(self, prompt: str, system: str = "") -> str:
        """Send a prompt and return the full response string."""
        last_error: Exception | None = None
        for attempt, delay in enumerate(BACKOFF_DELAYS[: self.max_retries]):
            try:
                return self._call(prompt, system)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.name}] attempt {attempt + 1} failed: {e}"
                    + (f" — retrying in {delay}s" if attempt + 1 < self.max_retries else "")
                )
                if attempt + 1 < self.max_retries:
                    time.sleep(delay)

        # All retries exhausted — try fallback
        if self.fallback:
            logger.warning(f"[{self.name}] all retries failed, using fallback: {self.fallback.name}")
            return self.fallback.send(prompt, system)

        raise RuntimeError(
            f"[{self.name}] all {self.max_retries} retries failed: {last_error}"
        ) from last_error

    def stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        """Stream tokens with retry. Falls back to send() on failure."""
        last_error: Exception | None = None
        for attempt, delay in enumerate(BACKOFF_DELAYS[: self.max_retries]):
            try:
                yield from self._stream(prompt, system)
                return
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.name}] stream attempt {attempt + 1} failed: {e}")
                if attempt + 1 < self.max_retries:
                    time.sleep(delay)

        if self.fallback:
            logger.warning(f"[{self.name}] streaming fallback to: {self.fallback.name}")
            yield from self.fallback.stream(prompt, system)
            return

        raise RuntimeError(
            f"[{self.name}] stream failed after {self.max_retries} retries: {last_error}"
        ) from last_error

    # ------------------------------------------------------------------
    # Token counting (override in providers that support it)
    # ------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)
