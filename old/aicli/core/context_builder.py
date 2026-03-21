"""
ContextBuilder — collects and formats files/memory for LLM injection.

Resolves inject_files directives from workflow YAML:
  - "PROJECT.md"              → from project workspace dir
  - "{{code_dir}}/cli.py"    → from code dir
  - "{{code_dir}}/providers/" → all .py files in folder
  - "auto"                    → recently modified files in code_dir

Template vars:
  {{code_dir}}    → resolved code directory
  {{project_dir}} → resolved project workspace directory
"""

import os
import time
from pathlib import Path
from typing import Optional


class ContextBuilder:

    AUTO_EXTENSIONS = {".py", ".ts", ".js", ".yaml", ".yml", ".md", ".json", ".toml"}
    MAX_FILE_CHARS = 20_000     # truncate individual large files
    MAX_TOTAL_CHARS = 120_000   # total context cap

    def __init__(
        self,
        project_dir: Path,
        code_dir: Optional[Path] = None,
    ):
        self.project_dir = project_dir.resolve()
        self.code_dir = code_dir.resolve() if code_dir else None
        self._total_chars = 0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build(
        self,
        inject_files: list[str] | None = None,
        inject_context: list[str] | None = None,
        memory_entries: list[str] | None = None,
        summary_text: str | None = None,
    ) -> str:
        """
        Build the full context block to prepend to a step prompt.
        Returns an empty string if nothing to inject.
        """
        # Reset per-call so multiple workflow steps don't share the budget
        self._total_chars = 0
        sections: list[str] = []

        # --- Files ---
        if inject_files:
            file_blocks = self._collect_files(inject_files)
            if file_blocks:
                sections.append("--- FILES ---\n" + "\n\n".join(file_blocks))

        # --- Memory ---
        if inject_context and "memory" in inject_context and memory_entries:
            mem_text = "\n\n".join(memory_entries[:10])
            sections.append(f"--- MEMORY (last {min(10, len(memory_entries))}) ---\n{mem_text}")

        # --- Summary ---
        if inject_context and "summary" in inject_context and summary_text:
            sections.append(f"--- SUMMARY ---\n{summary_text}")

        if not sections:
            return ""

        return "\n\n".join(sections) + "\n\n"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_var(self, path_str: str) -> str:
        s = path_str
        if self.code_dir:
            s = s.replace("{{code_dir}}", str(self.code_dir))
        s = s.replace("{{project_dir}}", str(self.project_dir))
        return s

    def _collect_files(self, directives: list[str]) -> list[str]:
        blocks: list[str] = []
        for directive in directives:
            if self._total_chars >= self.MAX_TOTAL_CHARS:
                break
            directive = directive.strip()
            if directive == "auto":
                blocks.extend(self._auto_files())
            else:
                resolved = self._resolve_var(directive)
                path = Path(resolved)
                # Try project_dir relative if not absolute or found
                if not path.is_absolute():
                    path = self.project_dir / resolved
                blocks.extend(self._path_to_blocks(path, label=directive))
        return blocks

    def _path_to_blocks(self, path: Path, label: str) -> list[str]:
        blocks: list[str] = []
        if not path.exists():
            return [f"### {label}\n[file not found: {path}]"]
        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.suffix in self.AUTO_EXTENSIONS:
                    blocks.extend(self._read_file_block(child))
        else:
            blocks.extend(self._read_file_block(path))
        return blocks

    def _read_file_block(self, path: Path) -> list[str]:
        if self._total_chars >= self.MAX_TOTAL_CHARS:
            return []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > self.MAX_FILE_CHARS:
                content = content[: self.MAX_FILE_CHARS] + "\n... [truncated]"
            self._total_chars += len(content)
            rel = self._rel_label(path)
            return [f"### {rel}\n```\n{content}\n```"]
        except Exception as e:
            return [f"### {path.name}\n[error reading file: {e}]"]

    def _rel_label(self, path: Path) -> str:
        """Return a short label (relative to project or code dir)."""
        try:
            if self.code_dir and path.is_relative_to(self.code_dir):
                return str(path.relative_to(self.code_dir))
        except ValueError:
            pass
        try:
            if path.is_relative_to(self.project_dir):
                return str(path.relative_to(self.project_dir))
        except ValueError:
            pass
        return path.name

    def _auto_files(self, top_n: int = 8, max_age_secs: int = 86400) -> list[str]:
        """Inject recently modified files from code_dir."""
        if not self.code_dir or not self.code_dir.exists():
            return []

        cutoff = time.time() - max_age_secs
        candidates: list[tuple[float, Path]] = []

        for p in self.code_dir.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix not in self.AUTO_EXTENSIONS:
                continue
            # Skip hidden dirs and __pycache__
            parts = p.parts
            if any(part.startswith(".") or part == "__pycache__" for part in parts):
                continue
            mtime = p.stat().st_mtime
            if mtime >= cutoff:
                candidates.append((mtime, p))

        candidates.sort(reverse=True)
        blocks: list[str] = []
        for _, path in candidates[:top_n]:
            blocks.extend(self._read_file_block(path))
        return blocks
