"""Tests for providers/base.py — BaseProvider retry and fallback logic."""

import pytest
from unittest.mock import patch, MagicMock
from providers.base import BaseProvider, BACKOFF_DELAYS


# ---------------------------------------------------------------------------
# Concrete minimal subclass for testing
# ---------------------------------------------------------------------------

class EchoProvider(BaseProvider):
    """Always succeeds — returns the prompt."""
    name = "echo"

    def _call(self, prompt: str, system: str = "") -> str:
        return f"echo:{prompt}"


class FailProvider(BaseProvider):
    """Fails N times, then succeeds."""
    name = "fail"

    def __init__(self, fail_times: int = 0, error_msg: str = "API error"):
        self.fail_times = fail_times
        self.call_count = 0
        self.error_msg = error_msg
        self.max_retries = 3

    def _call(self, prompt: str, system: str = "") -> str:
        self.call_count += 1
        if self.call_count <= self.fail_times:
            raise RuntimeError(self.error_msg)
        return f"success_after_{self.fail_times}_failures"


class AlwaysFailProvider(BaseProvider):
    """Always raises."""
    name = "always_fail"

    def _call(self, prompt: str, system: str = "") -> str:
        raise RuntimeError("permanent failure")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSendRetry:
    def test_successful_first_call(self):
        p = EchoProvider()
        result = p.send("hello")
        assert result == "echo:hello"

    def test_retries_on_failure_then_succeeds(self):
        p = FailProvider(fail_times=2)
        # Patch sleep so test is instant
        with patch("providers.base.time.sleep"):
            result = p.send("hi")
        assert "success_after_2" in result
        assert p.call_count == 3

    def test_raises_after_all_retries_exhausted_no_fallback(self):
        p = AlwaysFailProvider()
        p.max_retries = 3
        with patch("providers.base.time.sleep"):
            with pytest.raises(RuntimeError, match="all 3 retries failed"):
                p.send("hi")

    def test_fallback_used_when_primary_fails(self):
        primary = AlwaysFailProvider()
        primary.max_retries = 2
        fallback = EchoProvider()
        primary.fallback = fallback

        with patch("providers.base.time.sleep"):
            result = primary.send("test")
        assert result == "echo:test"

    def test_fallback_not_called_when_primary_succeeds(self):
        primary = EchoProvider()
        fallback = MagicMock()
        primary.fallback = fallback

        primary.send("test")
        fallback.send.assert_not_called()

    def test_backoff_delays_applied(self):
        p = FailProvider(fail_times=2)
        p.max_retries = 3
        sleep_calls = []
        with patch("providers.base.time.sleep", side_effect=lambda s: sleep_calls.append(s)):
            p.send("hi")
        # Should have slept twice (after attempt 1 and 2)
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == BACKOFF_DELAYS[0]
        assert sleep_calls[1] == BACKOFF_DELAYS[1]


class TestStreamRetry:
    def test_stream_yields_chunks(self):
        p = EchoProvider()
        chunks = list(p.stream("hello"))
        assert chunks == ["echo:hello"]

    def test_stream_raises_after_all_retries_no_fallback(self):
        p = AlwaysFailProvider()
        p.max_retries = 2
        with patch("providers.base.time.sleep"):
            with pytest.raises(RuntimeError):
                list(p.stream("hi"))

    def test_stream_fallback_used(self):
        primary = AlwaysFailProvider()
        primary.max_retries = 2
        fallback = EchoProvider()
        primary.fallback = fallback

        with patch("providers.base.time.sleep"):
            chunks = list(primary.stream("test"))
        assert chunks == ["echo:test"]


class TestTokenCount:
    def test_rough_estimate(self):
        p = EchoProvider()
        # 400 chars → ~100 tokens
        result = p.count_tokens("x" * 400)
        assert result == 100

    def test_minimum_one_token(self):
        p = EchoProvider()
        assert p.count_tokens("") == 1
        assert p.count_tokens("a") == 1
