"""Tests for core/session_store.py — session persistence and handoff state."""

import json
import pytest
from pathlib import Path

from core.session_store import (
    SessionStore,
    load_session_state,
    save_session_state,
    format_session_state_for_prompt,
)


# ---------------------------------------------------------------------------
# SessionStore — message persistence
# ---------------------------------------------------------------------------

class TestSessionStore:
    def test_save_and_load_messages(self, tmp_path):
        store = SessionStore(tmp_path)
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        store.save_messages("claude", messages)
        loaded = store.load_messages("claude")
        assert loaded == messages

    def test_load_missing_returns_empty(self, tmp_path):
        store = SessionStore(tmp_path)
        assert store.load_messages("claude") == []

    def test_separate_storage_per_provider(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save_messages("claude", [{"role": "user", "content": "a"}])
        store.save_messages("deepseek", [{"role": "user", "content": "b"}])

        assert store.load_messages("claude")[0]["content"] == "a"
        assert store.load_messages("deepseek")[0]["content"] == "b"

    def test_saves_trimmed_to_max(self, tmp_path):
        store = SessionStore(tmp_path)
        from core.session_store import MAX_STORED_MESSAGES
        # Create more than the max
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(MAX_STORED_MESSAGES + 50)
        ]
        store.save_messages("openai", messages)
        loaded = store.load_messages("openai")
        assert len(loaded) == MAX_STORED_MESSAGES
        # Should be the LAST MAX messages
        assert loaded[-1]["content"] == messages[-1]["content"]

    def test_clear_single_provider(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save_messages("claude", [{"role": "user", "content": "x"}])
        store.save_messages("deepseek", [{"role": "user", "content": "y"}])
        store.clear("claude")
        assert store.load_messages("claude") == []
        assert store.load_messages("deepseek") != []

    def test_clear_all_providers(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save_messages("claude", [{"role": "user", "content": "x"}])
        store.save_messages("grok", [{"role": "user", "content": "y"}])
        store.clear()
        assert store.load_messages("claude") == []
        assert store.load_messages("grok") == []

    def test_providers_with_history(self, tmp_path):
        store = SessionStore(tmp_path)
        store.save_messages("claude", [{"role": "user", "content": "a"}])
        store.save_messages("deepseek", [{"role": "user", "content": "b"}])
        names = store.providers_with_history()
        assert "claude" in names
        assert "deepseek" in names

    def test_load_ignores_corrupt_file(self, tmp_path):
        store = SessionStore(tmp_path)
        corrupt = store.dir / "openai_messages.json"
        corrupt.write_text("not valid json {{{")
        result = store.load_messages("openai")
        assert result == []

    def test_load_filters_invalid_entries(self, tmp_path):
        store = SessionStore(tmp_path)
        path = store.dir / "claude_messages.json"
        path.write_text(json.dumps({
            "provider": "claude",
            "messages": [
                {"role": "user", "content": "valid"},
                {"content": "missing role — should be filtered"},
                42,  # not a dict
            ]
        }))
        loaded = store.load_messages("claude")
        assert len(loaded) == 1
        assert loaded[0]["content"] == "valid"


# ---------------------------------------------------------------------------
# session_state.json — handoff document
# ---------------------------------------------------------------------------

class TestSessionState:
    def test_save_and_load(self, tmp_path):
        save_session_state(
            tmp_path, "claude", "myproject", "auth", "v2",
            "How do I do X?", "You can do X by...", session_count=3
        )
        state = load_session_state(tmp_path)
        assert state["active_provider"] == "claude"
        assert state["active_project"] == "myproject"
        assert state["feature"] == "auth"
        assert state["tag"] == "v2"
        assert state["session_count"] == 3
        assert "How do I do X" in state["last_input_preview"]

    def test_load_missing_returns_empty(self, tmp_path):
        state = load_session_state(tmp_path)
        assert state == {}

    def test_last_input_truncated(self, tmp_path):
        long_input = "x" * 1000
        save_session_state(tmp_path, "claude", "proj", "", "", long_input, "", 0)
        state = load_session_state(tmp_path)
        assert len(state["last_input_preview"]) <= 250

    def test_last_output_truncated(self, tmp_path):
        long_output = "y" * 1000
        save_session_state(tmp_path, "claude", "proj", "", "", "", long_output, 0)
        state = load_session_state(tmp_path)
        assert len(state["last_output_preview"]) <= 400


# ---------------------------------------------------------------------------
# format_session_state_for_prompt
# ---------------------------------------------------------------------------

class TestFormatSessionState:
    def test_empty_state_returns_empty_string(self):
        assert format_session_state_for_prompt({}) == ""

    def test_includes_date_provider_project(self, tmp_path):
        save_session_state(tmp_path, "deepseek", "aicli", "", "", "ping", "pong", 1)
        state = load_session_state(tmp_path)
        result = format_session_state_for_prompt(state)
        assert "deepseek" in result
        assert "aicli" in result
        assert "PREVIOUS SESSION" in result

    def test_includes_feature_and_tag(self, tmp_path):
        save_session_state(tmp_path, "claude", "proj", "payments", "v3", "q", "a", 5)
        state = load_session_state(tmp_path)
        result = format_session_state_for_prompt(state)
        assert "payments" in result
        assert "v3" in result

    def test_includes_last_question_and_answer(self, tmp_path):
        save_session_state(tmp_path, "claude", "proj", "", "", "Why does X fail?", "Because of Y", 1)
        state = load_session_state(tmp_path)
        result = format_session_state_for_prompt(state)
        assert "Why does X fail" in result
        assert "Because of Y" in result

    def test_no_feature_no_section(self, tmp_path):
        save_session_state(tmp_path, "claude", "proj", "", "", "q", "a", 1)
        state = load_session_state(tmp_path)
        result = format_session_state_for_prompt(state)
        assert "Feature in progress" not in result
