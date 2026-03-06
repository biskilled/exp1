"""Tests for core/memory.py — MemoryStore."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# MemoryStore reads/writes relative to cwd, so we patch Path used internally
import core.memory as mem_module
from core.memory import MemoryStore


@pytest.fixture
def mem(tmp_path):
    """MemoryStore backed by a tmp directory."""
    # Patch the hardcoded Path(".aicli/memory.jsonl") to a temp path
    with patch.object(mem_module.Path, "__new__", side_effect=None):
        pass
    store = MemoryStore(config={"memory_enabled": True, "memory_top_k": 5})
    store.path = tmp_path / "memory.jsonl"
    return store


class TestMemoryAdd:
    def test_add_creates_file(self, mem):
        mem.add_entry("claude", "architect", "hello", "world")
        assert mem.path.exists()

    def test_add_writes_valid_jsonl(self, mem):
        mem.add_entry("claude", "architect", "hello", "world")
        lines = [l for l in mem.path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["provider"] == "claude"
        assert parsed["user_input"] == "hello"
        assert parsed["output"] == "world"

    def test_add_multiple(self, mem):
        for i in range(5):
            mem.add_entry("claude", None, f"q{i}", f"a{i}")
        assert mem.count() == 5

    def test_disabled_store_does_not_write(self, tmp_path):
        store = MemoryStore(config={"memory_enabled": False})
        store.path = tmp_path / "memory.jsonl"
        store.add_entry("claude", None, "hello", "world")
        assert not store.path.exists()


class TestMemorySearch:
    def test_keyword_search_finds_match(self, mem):
        mem.add_entry("claude", None, "implement streaming", "use generator pattern")
        results = mem.search("streaming generator")
        assert len(results) >= 1
        assert "streaming" in results[0].lower() or "generator" in results[0].lower()

    def test_keyword_search_no_match_returns_empty(self, mem):
        mem.add_entry("claude", None, "fix login bug", "updated auth")
        results = mem.search("quantum physics")
        assert results == []

    def test_search_respects_top_k(self, mem):
        for i in range(10):
            mem.add_entry("claude", None, f"feature {i}", f"output {i}")
        results = mem.search("feature", top_k=3)
        assert len(results) <= 3

    def test_search_by_tag(self, mem):
        mem.add_entry("claude", None, "q1", "a1", tag="auth")
        mem.add_entry("claude", None, "q2", "a2", tag="billing")
        results = mem.search_by_tag("auth")
        assert len(results) == 1
        assert "auth" in results[0]

    def test_search_by_feature(self, mem):
        mem.add_entry("claude", None, "q1", "a1", feature="payments")
        mem.add_entry("claude", None, "q2", "a2", feature="auth")
        results = mem.search_by_feature("payments")
        assert len(results) == 1

    def test_recent_returns_last_n(self, mem):
        for i in range(8):
            mem.add_entry("claude", None, f"q{i}", f"a{i}")
        results = mem.recent(top_k=3)
        assert len(results) == 3
        # Last entry should appear
        assert "q7" in results[-1]


class TestMemoryCount:
    def test_count_empty(self, mem):
        assert mem.count() == 0

    def test_count_after_adds(self, mem):
        mem.add_entry("claude", None, "a", "b")
        mem.add_entry("openai", None, "c", "d")
        assert mem.count() == 2

    def test_count_skips_blank_lines(self, mem):
        mem.path.parent.mkdir(parents=True, exist_ok=True)
        mem.path.write_text('{"ts":"x","provider":"claude","role":"","feature":"","tag":"","user_input":"hi","output":"ok","commit_hash":""}\n\n\n')
        assert mem.count() == 1
