"""Tests for core/context_builder.py — ContextBuilder."""

import pytest
from pathlib import Path

from core.context_builder import ContextBuilder


@pytest.fixture
def dirs(tmp_path):
    """Create project_dir and code_dir with some test files."""
    project_dir = tmp_path / "workspace" / "myproject"
    code_dir = tmp_path / "code"
    project_dir.mkdir(parents=True)
    code_dir.mkdir(parents=True)

    # Seed files
    (project_dir / "PROJECT.md").write_text("# Project\nThis is the project.")
    (code_dir / "main.py").write_text("def main():\n    pass\n")
    (code_dir / "utils.py").write_text("def helper():\n    return 42\n")

    return project_dir, code_dir


class TestBuildBasic:
    def test_empty_returns_empty_string(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build()
        assert result == ""

    def test_inject_project_md(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["PROJECT.md"])
        assert "PROJECT.md" in result or "This is the project" in result

    def test_inject_code_dir_file(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["{{code_dir}}/main.py"])
        assert "main.py" in result
        assert "def main" in result

    def test_inject_directory_injects_all_py_files(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["{{code_dir}}/"])
        assert "main.py" in result
        assert "utils.py" in result

    def test_missing_file_returns_not_found_block(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["nonexistent.md"])
        assert "not found" in result.lower()


class TestTemplateVars:
    def test_code_dir_var_resolved(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["{{code_dir}}/main.py"])
        assert "def main" in result

    def test_project_dir_var_resolved(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(inject_files=["{{project_dir}}/PROJECT.md"])
        assert "This is the project" in result


class TestCharLimits:
    def test_large_file_is_truncated(self, dirs):
        project_dir, code_dir = dirs
        big_file = code_dir / "big.py"
        big_file.write_text("x = 1\n" * 5000)  # ~30k chars
        cb = ContextBuilder(project_dir, code_dir)
        cb.MAX_FILE_CHARS = 500
        result = cb.build(inject_files=["{{code_dir}}/big.py"])
        assert "truncated" in result

    def test_total_chars_reset_between_build_calls(self, dirs):
        """Bug fix: _total_chars must reset on each build() call."""
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        cb.MAX_TOTAL_CHARS = 100  # tiny cap

        # First build fills up the budget
        cb.build(inject_files=["PROJECT.md"])

        # Second build should work from scratch, not from leftover total
        cb.MAX_TOTAL_CHARS = 100_000  # restore generous cap
        result2 = cb.build(inject_files=["PROJECT.md"])
        assert "This is the project" in result2


class TestMemoryAndSummaryInjection:
    def test_memory_injected_when_context_includes_memory(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(
            inject_context=["memory"],
            memory_entries=["[2026-01-01] claude — did the auth feature"],
        )
        assert "MEMORY" in result
        assert "auth feature" in result

    def test_summary_injected(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(
            inject_context=["summary"],
            summary_text="We built the payments module.",
        )
        assert "SUMMARY" in result
        assert "payments module" in result

    def test_no_injection_when_context_key_missing(self, dirs):
        project_dir, code_dir = dirs
        cb = ContextBuilder(project_dir, code_dir)
        result = cb.build(
            inject_context=["summary"],
            memory_entries=["should not appear"],
        )
        assert "should not appear" not in result
