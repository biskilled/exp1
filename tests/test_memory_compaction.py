"""Tests for memory compaction and summary loading."""

import json
from unittest.mock import MagicMock
import pytest

from core.memory import MemoryStore


@pytest.fixture
def mem(tmp_path):
    store = MemoryStore(config={"memory_enabled": True, "memory_top_k": 5})
    store.path = tmp_path / "memory.jsonl"
    return store


def _fill_memory(mem, n: int):
    for i in range(n):
        mem.add_entry("claude", None, f"question {i}", f"answer {i}")


class TestMaybeCompact:
    def test_no_compaction_below_threshold(self, mem):
        _fill_memory(mem, 10)
        result = mem.maybe_compact(llm_agent=None, threshold=100)
        assert result is False
        assert mem.count() == 10

    def test_no_compaction_without_agent(self, mem):
        _fill_memory(mem, 50)
        result = mem.maybe_compact(llm_agent=None, threshold=10)
        assert result is False

    def test_compaction_runs_when_over_threshold(self, mem):
        _fill_memory(mem, 60)
        mock_agent = MagicMock()
        mock_agent.send.return_value = "## Summary\n- Built feature X\n- Fixed bug Y"

        result = mem.maybe_compact(mock_agent, threshold=30, keep_recent=10)

        assert result is True
        mock_agent.send.assert_called_once()

    def test_compaction_keeps_recent_entries(self, mem):
        _fill_memory(mem, 60)
        mock_agent = MagicMock()
        mock_agent.send.return_value = "Summary content here"

        mem.maybe_compact(mock_agent, threshold=30, keep_recent=15)

        assert mem.count() == 15  # only the last 15 remain

    def test_compaction_writes_summary_file(self, mem):
        _fill_memory(mem, 50)
        mock_agent = MagicMock()
        mock_agent.send.return_value = "## Key decisions\n- Used JSONL for storage"

        mem.maybe_compact(mock_agent, threshold=20, keep_recent=5)

        summary_path = mem.path.parent / "memory_summary.md"
        assert summary_path.exists()
        content = summary_path.read_text()
        assert "Key decisions" in content
        assert "JSONL for storage" in content

    def test_compaction_appends_to_existing_summary(self, mem):
        _fill_memory(mem, 50)
        mock_agent = MagicMock()
        mock_agent.send.side_effect = ["First summary", "Second summary"]

        # First compaction
        mem.maybe_compact(mock_agent, threshold=20, keep_recent=5)
        _fill_memory(mem, 30)  # refill

        # Second compaction
        mem.maybe_compact(mock_agent, threshold=20, keep_recent=5)

        summary_path = mem.path.parent / "memory_summary.md"
        content = summary_path.read_text()
        assert "First summary" in content
        assert "Second summary" in content

    def test_compaction_does_not_corrupt_on_llm_failure(self, mem):
        _fill_memory(mem, 50)
        original_count = mem.count()

        mock_agent = MagicMock()
        mock_agent.send.side_effect = RuntimeError("LLM unavailable")

        result = mem.maybe_compact(mock_agent, threshold=20, keep_recent=5)

        assert result is False
        assert mem.count() == original_count  # memory unchanged


class TestLoadSummary:
    def test_returns_empty_when_no_summary_file(self, mem):
        assert mem.load_summary() == ""

    def test_returns_content_when_exists(self, mem):
        summary_path = mem.path.parent / "memory_summary.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("## Summary\n- Point 1\n- Point 2")

        result = mem.load_summary()
        assert "Point 1" in result
        assert "Point 2" in result

    def test_truncates_to_max_chars(self, mem):
        summary_path = mem.path.parent / "memory_summary.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("x" * 5000)

        result = mem.load_summary(max_chars=100)
        assert len(result) == 100
