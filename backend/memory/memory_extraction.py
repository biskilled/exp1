"""
memory_extraction.py — Work item code intelligence extraction.

Aggregates commits linked to a work item and runs LLM extraction to populate
tags_ai JSONB with structured code summary, design patterns, test coverage,
and architectural decisions.

Public API::

    extractor = MemoryExtraction()
    result = await extractor.extract_work_item_code_summary(project, work_item_id)
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from core.config import settings
from core.database import db

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_WORK_ITEM_NAME = """
    SELECT name_ai FROM mem_ai_work_items
    WHERE id=%s::uuid AND project_id=%s
"""

_SQL_GET_LINKED_COMMITS = """
    SELECT commit_hash, commit_msg, summary, tags, committed_at
    FROM mem_mrr_commits
    WHERE project_id=%s AND tags @> jsonb_build_object('work-item', %s)
    ORDER BY committed_at
"""

_SQL_AGGREGATE_CODE = """
    SELECT file_path, file_ext, file_language,
           SUM(rows_added)::int   AS rows_added,
           SUM(rows_removed)::int AS rows_removed
    FROM mem_mrr_commits_code
    WHERE commit_hash = ANY(%s)
    GROUP BY file_path, file_ext, file_language
"""

_SQL_MERGE_TAGS_AI = """
    UPDATE mem_ai_work_items
    SET tags_ai = tags_ai || %s::jsonb, updated_at = NOW()
    WHERE id=%s::uuid AND project_id=%s
"""


# ── Prompt loader ─────────────────────────────────────────────────────────────

def _load_prompt_file(name: str) -> str:
    """Load a system prompt from workspace/_templates/memory/prompts/system/{name}.md."""
    path = Path(settings.workspace_dir) / "_templates" / "memory" / "prompts" / "system" / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    return ""


# ── MemoryExtraction class ────────────────────────────────────────────────────

class MemoryExtraction:
    """Aggregate commit data and run LLM extraction for work item code intelligence."""

    @staticmethod
    def aggregate_commits(commits: list[dict]) -> dict:
        """Aggregate file/line stats across all commits linked to a work item.

        Queries mem_mrr_commits_code for structured per-symbol stats when available;
        falls back to parsing tags["files"] / tags["rows_changed"] for older commits.

        Returns a dict with all_files, test_files, source_files, total_added,
        total_removed, and commit_count.
        """
        commit_hashes = [c["commit_hash"] for c in commits if c.get("commit_hash")]

        # Try mem_mrr_commits_code first (populated by tree-sitter parser)
        if commit_hashes and db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(_SQL_AGGREGATE_CODE, (commit_hashes,))
                        rows = cur.fetchall()
                if rows:
                    all_files: set[str] = set()
                    test_files_seen: set[str] = set()
                    total_added = 0
                    total_removed = 0
                    for file_path, _ext, _lang, ra, rr in rows:
                        all_files.add(file_path)
                        total_added += ra or 0
                        total_removed += rr or 0
                        if ".test." in file_path or ".spec." in file_path or "/test" in file_path or "tests/" in file_path:
                            test_files_seen.add(file_path)
                    test_files = sorted(test_files_seen)
                    source_files = sorted(all_files - test_files_seen)
                    return {
                        "all_files":     sorted(all_files),
                        "test_files":    test_files,
                        "source_files":  source_files,
                        "total_added":   total_added,
                        "total_removed": total_removed,
                        "commit_count":  len(commits),
                    }
            except Exception as e:
                log.debug(f"aggregate_commits code table query failed, falling back: {e}")

        # Fallback: parse tags["files"] / tags["rows_changed"] (pre-016 commits)
        all_files_fb: set[str] = set()
        test_files_seen_fb: set[str] = set()
        total_added_fb = 0
        total_removed_fb = 0

        for c in commits:
            tags = c.get("tags") or {}
            files = tags.get("files") or {}
            names = list(files.keys()) if isinstance(files, dict) else list(files)
            all_files_fb.update(names)

            rc = tags.get("rows_changed") or {}
            total_added_fb   += rc.get("added", 0)
            total_removed_fb += rc.get("removed", 0)

            for f in names:
                if ".test." in f or ".spec." in f or "/test" in f or "tests/" in f:
                    test_files_seen_fb.add(f)

        test_files_fb   = sorted(test_files_seen_fb)
        source_files_fb = sorted(all_files_fb - test_files_seen_fb)

        return {
            "all_files":    sorted(all_files_fb),
            "test_files":   test_files_fb,
            "source_files": source_files_fb,
            "total_added":  total_added_fb,
            "total_removed": total_removed_fb,
            "commit_count": len(commits),
        }

    async def extract_work_item_code_summary(self, project: str, work_item_id: str) -> dict:
        """Aggregate commits + LLM extraction → populate tags_ai on the work item.

        Steps:
          1. Fetch work item name
          2. Fetch all commits tagged with work-item=<id>
          3. Aggregate file/line stats
          4. Run LLM (Haiku) to extract structured code intelligence
          5. Merge result into mem_ai_work_items.tags_ai (JSONB ||)
          6. Return the extracted result
        """
        if not db.is_available():
            return {"error": "Database not available"}

        project_id = db.get_or_create_project_id(project)

        # 1. Fetch work item name
        ai_name = ""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WORK_ITEM_NAME, (work_item_id, project_id))
                    row = cur.fetchone()
                    if not row:
                        return {"error": f"Work item {work_item_id} not found"}
                    ai_name = row[0]
        except Exception as e:
            log.warning(f"extract_work_item_code_summary: DB fetch failed: {e}")
            return {"error": str(e)}

        # 2. Fetch linked commits
        commits: list[dict] = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_LINKED_COMMITS, (project_id, work_item_id))
                    cols = [d[0] for d in cur.description]
                    for r in cur.fetchall():
                        row_d = dict(zip(cols, r))
                        if row_d.get("committed_at"):
                            row_d["committed_at"] = row_d["committed_at"].isoformat()
                        commits.append(row_d)
        except Exception as e:
            log.warning(f"extract_work_item_code_summary: commit fetch failed: {e}")
            return {"error": str(e)}

        # 3. Aggregate stats
        agg = self.aggregate_commits(commits)

        # 4. LLM extraction
        result: dict = {}
        sys_prompt = _load_prompt_file("feature_extraction") or (
            "You are a technical project memory assistant. "
            "Given a list of commits for a feature, extract structured outcomes. "
            "Infer classes and methods from file names and commit messages. "
            "Respond ONLY in JSON with keys: code_summary, design, test_coverage, decisions."
        )

        commit_lines = "\n".join(
            f"- [{c.get('committed_at','')[:10]}] {c.get('commit_msg','')}"
            + (f" | files: {', '.join(list((c.get('tags') or {}).get('files', {}).keys())[:5])}" if (c.get('tags') or {}).get('files') else "")
            for c in commits
        )
        user_msg = (
            f"Feature: {ai_name}\n\n"
            f"Commits ({agg['commit_count']}):\n{commit_lines or '(none)'}\n\n"
            f"AGGREGATED:\n"
            f"  source_files: {agg['source_files'][:20]}\n"
            f"  test_files: {agg['test_files']}\n"
            f"  total_added: {agg['total_added']} lines\n"
            f"  total_removed: {agg['total_removed']} lines\n"
        )

        if commits:
            try:
                from memory.memory_embedding import _haiku
                raw = await _haiku(sys_prompt, user_msg, max_tokens=800)
                if raw:
                    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
                    result = json.loads(cleaned)
            except Exception as e:
                log.debug(f"extract_work_item_code_summary LLM error: {e}")

        result["aggregated"] = agg

        # 5. Merge into tags_ai
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_MERGE_TAGS_AI, (json.dumps(result), work_item_id, project_id))
        except Exception as e:
            log.warning(f"extract_work_item_code_summary: tags_ai update failed: {e}")

        return result
