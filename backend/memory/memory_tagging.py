"""
memory_tagging.py — Tag management for planner_tags.

Manages planner_tags (parent-child hierarchy): create, list, merge, and
relation helpers. MRR rows use inline tags TEXT[] — no junction table needed.

Public API::

    tagging = MemoryTagging()
    tag_id = tagging.get_or_create_tag(project, name, category_id)
    tree = tagging.get_tag_tree(project)
"""
from __future__ import annotations

import logging
from typing import Optional

from core.database import db

log = logging.getLogger(__name__)

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_GET_TAG = """
    SELECT id FROM planner_tags
    WHERE project_id=%s AND name=%s
    LIMIT 1
"""

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (project_id, name, category_id, status, creator)
    VALUES (%s, %s, %s, 'active', 'ai')
    ON CONFLICT (project_id, name, category_id) DO NOTHING
    RETURNING id
"""

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.description, t.due_date, t.priority, 0 AS source_count
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.project_id = %s
      AND t.merged_into IS NULL
    ORDER BY t.created_at
"""

_SQL_MERGE_TAGS = """
    UPDATE planner_tags SET merged_into=%s::uuid, updated_at=NOW()
    WHERE project_id=%s AND name=%s
    RETURNING id
"""



class MemoryTagging:
    """Maps planner_tags to mirroring rows and AI events via mem_tags_relations."""

    # ── Core tag operations ─────────────────────────────────────────────────

    def get_or_create_tag(
        self,
        project: str,
        name: str,
        category_id: Optional[int] = None,
    ) -> Optional[str]:
        """Return existing tag UUID or create a new one. Returns UUID string."""
        if not db.is_available():
            return None
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_TAG, (project_id, name))
                    row = cur.fetchone()
                    if row:
                        return str(row[0])
                    cur.execute(_SQL_INSERT_TAG, (project_id, name, category_id))
                    row = cur.fetchone()
                    if row:
                        return str(row[0])
                    # Race: another session inserted first
                    cur.execute(_SQL_GET_TAG, (project_id, name))
                    row = cur.fetchone()
                    return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryTagging.get_or_create_tag error: {e}")
            return None

    # ── Tag tree / listing ──────────────────────────────────────────────────

    def get_tag_tree(self, project: str) -> list[dict]:
        """Return planner_tags as a nested parent→children tree."""
        if not db.is_available():
            return []
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_LIST_TAGS, (project_id,))
                    rows = cur.fetchall()
        except Exception:
            return []

        tags = [
            {
                "id":            str(r[0]),
                "name":          r[1],
                "category_id":   r[2],
                "parent_id":     str(r[3]) if r[3] else None,
                "merged_into":   str(r[4]) if r[4] else None,
                "status":        r[5],
                "created_at":    r[6].isoformat() if r[6] else None,
                "category_name": r[7],
                "color":         r[8] or "#4a90e2",
                "icon":          r[9] or "⬡",
                "description":   r[10] or "",
                "due_date":      r[11].isoformat() if r[11] else None,
                "priority":      r[12] or 3,
                "source_count":  r[13] if len(r) > 13 else 0,
                "children":      [],
            }
            for r in rows
        ]
        by_id = {t["id"]: t for t in tags}
        roots = []
        for tag in tags:
            pid = tag.get("parent_id")
            if pid and pid in by_id:
                by_id[pid]["children"].append(tag)
            else:
                roots.append(tag)
        return roots

    def merge_tags(self, project: str, from_name: str, into_name: str) -> None:
        """Mark from_name as merged into into_name."""
        if not db.is_available():
            return
        into_id = self.get_or_create_tag(project, into_name)
        if not into_id:
            return
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_MERGE_TAGS, (into_id, project_id, from_name))
        except Exception as e:
            log.debug(f"MemoryTagging.merge_tags error: {e}")

    def tag_from_context(
        self,
        project: str,
        prompt_id: str,
        context_tags: dict,
        session_id: str,
        session_src_desc: Optional[str] = None,
    ) -> None:
        """No-op: MRR rows now use inline tags[]; context tagging via hook_log_prompt."""
        pass

    def add_relation_by_name(
        self,
        project: str,
        from_name: str,
        relation: str,
        to_name: str,
        note: Optional[str] = None,
        source: str = "manual",
    ) -> bool:
        """No-op: mem_tags_relations table dropped. Returns False."""
        return False

    def upsert_relations_from_list(
        self,
        project: str,
        relations: list[dict],
        source: str = "ai_snapshot",
    ) -> int:
        """Batch-upsert relations extracted by LLM (from snapshot, item, or session).

        Each dict: {from: str, relation: str, to: str, note: str|None}.
        Creates tags via get_or_create_tag if they don't exist.
        Returns count of relations upserted.
        """
        count = 0
        for rel in relations:
            from_name = (rel.get("from") or rel.get("from_tag") or "").strip()
            to_name   = (rel.get("to")   or rel.get("to_tag")   or "").strip()
            relation  = (rel.get("relation") or "relates_to").strip()
            note      = rel.get("note")
            if not from_name or not to_name:
                continue
            if self.add_relation_by_name(project, from_name, relation, to_name,
                                          note=note, source=source):
                count += 1
        return count

    def get_blockers_and_deps(self, project: str) -> list[dict]:
        """Return blocks/depends_on relations. Placeholder — returns [] after mem_tags_relations drop."""
        return []
