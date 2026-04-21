"""
memory_tagging.py — Tag management for planner_tags.

Manages planner_tags (parent-child hierarchy): create, list, and merge.
MRR rows use inline tags TEXT[] — no junction table.

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
    """Manages planner_tags: create, list, merge."""

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

