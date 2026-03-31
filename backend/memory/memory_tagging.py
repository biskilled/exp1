"""
memory_tagging.py — Layer 2 of the three-layer memory architecture.

Maps planner_tags (parent-child hierarchy) to mirroring rows via mem_mrr_tags,
and to AI events via mem_ai_tags.  Also handles the AI tag suggestion workflow:
get_untagged → Haiku suggestion → apply or ignore.

Public API::

    tagging = MemoryTagging()
    tag_id = tagging.get_or_create_tag(project, name, category_id)
    tagging.link_to_mirroring(tag_id, session_id, session_src_desc='claude_cli', prompt_id=uuid)
    tagging.link_to_mirroring(tag_id, session_id, commit_id=42, commit_created=ts, event_id=evt_uuid)
    tagging.update_event_id_for_prompts(event_id, [prompt_uuid1, prompt_uuid2])
    tagging.link_to_event(event_id, tag_id)
    tagging.add_relation(from_tag_id, 'depends_on', to_tag_id)
    tree = tagging.get_tag_tree(project)
    tagging.tag_from_context(project, prompt_id, context_tags, session_id, src_desc)

    # AI suggestion flow
    suggestions = await tagging.suggest_tags_for_untagged(project)
    await tagging.apply_suggestion(project, source_type, source_id, tag_name, ...)
    tagging.ignore_suggestion(source_type, source_id)
"""
from __future__ import annotations

import logging
from typing import Optional

from core.database import db
from memory.memory_mirroring import MemoryMirroring

log = logging.getLogger(__name__)

_mirroring = MemoryMirroring()

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_GET_TAG = """
    SELECT id FROM planner_tags
    WHERE client_id=1 AND project=%s AND name=%s
    LIMIT 1
"""

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (client_id, project, name, category_id, status)
    VALUES (1, %s, %s, %s, 'active')
    ON CONFLICT (client_id, project, name) DO NOTHING
    RETURNING id
"""

# Per-source-type UPSERT SQL — one row per (tag, source) combination.
# ON CONFLICT updates the *_updated timestamp and backfills event_id/work_item_id when available.
_SQL_UPSERT_MRR_TAG_PROMPT = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            prompt_id, prompt_created, prompt_updated,
            work_item_id, work_item_created, work_item_updated,
            event_id, event_created, event_updated, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s, %s)
    ON CONFLICT (tag_id, prompt_id) WHERE prompt_id IS NOT NULL
    DO UPDATE SET
        prompt_updated    = COALESCE(EXCLUDED.prompt_updated,    NOW()),
        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
        updated_at        = NOW()
    RETURNING id
"""

_SQL_UPSERT_MRR_TAG_COMMIT = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            commit_id, commit_created, commit_updated,
            work_item_id, work_item_created, work_item_updated,
            event_id, event_created, event_updated, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s,
            %s, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s, %s)
    ON CONFLICT (tag_id, commit_id) WHERE commit_id IS NOT NULL
    DO UPDATE SET
        commit_updated    = COALESCE(EXCLUDED.commit_updated,    NOW()),
        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
        updated_at        = NOW()
    RETURNING id
"""

_SQL_UPSERT_MRR_TAG_ITEM = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            item_id, item_created, item_updated,
            work_item_id, work_item_created, work_item_updated,
            event_id, event_created, event_updated, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s, %s)
    ON CONFLICT (tag_id, item_id) WHERE item_id IS NOT NULL
    DO UPDATE SET
        item_updated      = COALESCE(EXCLUDED.item_updated,      NOW()),
        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
        updated_at        = NOW()
    RETURNING id
"""

_SQL_UPSERT_MRR_TAG_MESSAGE = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            message_id, message_created, message_updated,
            work_item_id, work_item_created, work_item_updated,
            event_id, event_created, event_updated, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s,
            %s::uuid, %s, %s, %s)
    ON CONFLICT (tag_id, message_id) WHERE message_id IS NOT NULL
    DO UPDATE SET
        message_updated   = COALESCE(EXCLUDED.message_updated,   NOW()),
        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
        updated_at        = NOW()
    RETURNING id
"""

# Session-level link (no source FK) — plain insert, no uniqueness conflict expected
_SQL_INSERT_MRR_TAG_SESSION = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            work_item_id, work_item_created, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s, %s::uuid, %s, %s)
    RETURNING id
"""

# Backfill event_id on existing mem_mrr_tags rows after a batch event is created
_SQL_UPDATE_MRR_TAG_EVENT = """
    UPDATE mem_mrr_tags
       SET event_id = %s::uuid, event_updated = NOW(), updated_at = NOW()
     WHERE prompt_id = ANY(%s::uuid[])
       AND event_id IS NULL
"""

_SQL_INSERT_AI_TAG = """
    INSERT INTO mem_ai_tags (event_id, tag_id)
    VALUES (%s::uuid, %s::uuid)
    ON CONFLICT (event_id, tag_id) DO NOTHING
"""

_SQL_INSERT_RELATION = """
    INSERT INTO mem_ai_tags_relations (from_tag_id, relation, to_tag_id, note, source)
    VALUES (%s::uuid, %s, %s::uuid, %s, %s)
    ON CONFLICT (from_tag_id, relation, to_tag_id) DO NOTHING
"""

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.lifecycle, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           tm.description, tm.due_date, tm.priority,
           (SELECT COUNT(*) FROM mem_mrr_tags mt WHERE mt.tag_id = t.id) AS source_count
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    WHERE t.client_id = 1 AND t.project = %s
      AND t.merged_into IS NULL
    ORDER BY t.created_at
"""

_SQL_GET_AI_SUGGESTION_CAT = """
    SELECT id FROM mng_tags_categories
    WHERE client_id=1 AND name='ai_suggestion'
    LIMIT 1
"""

_SQL_LIST_PROJECT_TAGS = """
    SELECT name FROM planner_tags
    WHERE client_id=1 AND project=%s AND status='active'
    ORDER BY name
"""

_SQL_LOAD_AI_TAG_PROMPT = """
    SELECT content FROM mng_system_roles
    WHERE client_id=1 AND name='ai_tag_suggestion' AND is_active=TRUE
    LIMIT 1
"""

_SQL_MERGE_TAGS = """
    UPDATE planner_tags SET merged_into=%s::uuid, updated_at=NOW()
    WHERE client_id=1 AND project=%s AND name=%s
    RETURNING id
"""

_SQL_REMAP_MRR_TAGS = """
    UPDATE mem_mrr_tags SET tag_id=%s::uuid WHERE tag_id=%s::uuid
"""

_SQL_GET_RELATIONS = """
    SELECT id, from_tag_id, relation, to_tag_id, note, source, created_at
    FROM mem_ai_tags_relations
    WHERE from_tag_id IN (
        SELECT id FROM planner_tags WHERE client_id=1 AND project=%s
    )
    ORDER BY created_at DESC
"""

_SQL_DELETE_RELATION = """
    DELETE FROM mem_ai_tags_relations WHERE id=%s::uuid
    RETURNING id
"""


class MemoryTagging:
    """Maps planner_tags to mirroring rows and AI events."""

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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_TAG, (project, name))
                    row = cur.fetchone()
                    if row:
                        return str(row[0])
                    cur.execute(_SQL_INSERT_TAG, (project, name, category_id))
                    row = cur.fetchone()
                    if row:
                        return str(row[0])
                    # Race: another session inserted first
                    cur.execute(_SQL_GET_TAG, (project, name))
                    row = cur.fetchone()
                    return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryTagging.get_or_create_tag error: {e}")
            return None

    def link_to_mirroring(
        self,
        tag_id: str,
        session_id: Optional[str] = None,
        *,
        session_src_id: Optional[str] = None,
        session_src_desc: Optional[str] = None,
        # Prompt FK + timestamps
        prompt_id: Optional[str] = None,
        prompt_created: Optional[object] = None,
        prompt_updated: Optional[object] = None,
        # Commit FK + timestamps
        commit_id: Optional[int] = None,
        commit_created: Optional[object] = None,
        commit_updated: Optional[object] = None,
        # Item FK + timestamps
        item_id: Optional[str] = None,
        item_created: Optional[object] = None,
        item_updated: Optional[object] = None,
        # Message FK + timestamps
        message_id: Optional[str] = None,
        message_created: Optional[object] = None,
        message_updated: Optional[object] = None,
        # Work-item FK + timestamps
        work_item_id: Optional[str] = None,
        work_item_created: Optional[object] = None,
        work_item_updated: Optional[object] = None,
        # AI-event FK + timestamps (Phase-2 — stored, no FK constraint yet)
        event_id: Optional[str] = None,
        event_created: Optional[object] = None,
        event_updated: Optional[object] = None,
        auto_tagged: bool = False,
    ) -> Optional[str]:
        """Insert or update a mem_mrr_tags row linking a tag to a source event.

        Routes to the appropriate per-source UPSERT SQL based on which FK is non-null.
        ON CONFLICT updates *_updated and backfills event_id/work_item_id if supplied.
        Returns the mem_mrr_tags.id as a string.
        """
        if not db.is_available():
            return None
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if prompt_id is not None:
                        cur.execute(_SQL_UPSERT_MRR_TAG_PROMPT, (
                            tag_id, session_id, session_src_id, session_src_desc,
                            prompt_id, prompt_created, prompt_updated,
                            work_item_id, work_item_created, work_item_updated,
                            event_id, event_created, event_updated, auto_tagged,
                        ))
                    elif commit_id is not None:
                        cur.execute(_SQL_UPSERT_MRR_TAG_COMMIT, (
                            tag_id, session_id, session_src_id, session_src_desc,
                            commit_id, commit_created, commit_updated,
                            work_item_id, work_item_created, work_item_updated,
                            event_id, event_created, event_updated, auto_tagged,
                        ))
                    elif item_id is not None:
                        cur.execute(_SQL_UPSERT_MRR_TAG_ITEM, (
                            tag_id, session_id, session_src_id, session_src_desc,
                            item_id, item_created, item_updated,
                            work_item_id, work_item_created, work_item_updated,
                            event_id, event_created, event_updated, auto_tagged,
                        ))
                    elif message_id is not None:
                        cur.execute(_SQL_UPSERT_MRR_TAG_MESSAGE, (
                            tag_id, session_id, session_src_id, session_src_desc,
                            message_id, message_created, message_updated,
                            work_item_id, work_item_created, work_item_updated,
                            event_id, event_created, event_updated, auto_tagged,
                        ))
                    else:
                        # Session-level link — no specific source FK
                        cur.execute(_SQL_INSERT_MRR_TAG_SESSION, (
                            tag_id, session_id, session_src_id, session_src_desc,
                            work_item_id, work_item_created, auto_tagged,
                        ))
                    row = cur.fetchone()
            return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryTagging.link_to_mirroring error: {e}")
            return None

    def update_event_id_for_prompts(
        self,
        event_id: str,
        prompt_ids: list[str],
    ) -> None:
        """Backfill event_id on mem_mrr_tags rows for the given prompt_ids.

        Called by MemoryEmbedding after process_prompt_batch creates a mem_ai_events
        row, so that mirroring-layer tag links know which AI event they rolled up into.
        Only updates rows where event_id IS NULL to avoid overwriting existing links.
        """
        if not db.is_available() or not prompt_ids:
            return
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_UPDATE_MRR_TAG_EVENT, (event_id, prompt_ids))
        except Exception as e:
            log.debug(f"MemoryTagging.update_event_id_for_prompts error: {e}")

    def link_to_event(self, event_id: str, tag_id: str) -> None:
        """Insert a row into mem_ai_tags linking a tag to an AI event."""
        if not db.is_available():
            return
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_INSERT_AI_TAG, (event_id, tag_id))
        except Exception as e:
            log.debug(f"MemoryTagging.link_to_event error: {e}")

    def add_relation(
        self,
        from_tag_id: str,
        relation: str,
        to_tag_id: str,
        note: Optional[str] = None,
        source: str = "manual",
    ) -> None:
        """Add a relationship between two planner_tags."""
        if not db.is_available():
            return
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_INSERT_RELATION, (from_tag_id, relation, to_tag_id, note, source))
        except Exception as e:
            log.debug(f"MemoryTagging.add_relation error: {e}")

    def get_tag_tree(self, project: str) -> list[dict]:
        """Return planner_tags as a nested parent→children tree."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_LIST_TAGS, (project,))
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
                "lifecycle":     r[6],
                "seq_num":       r[7],
                "created_at":    r[8].isoformat() if r[8] else None,
                "category_name": r[9],
                "color":         r[10] or "#4a90e2",
                "icon":          r[11] or "⬡",
                "description":   r[12] or "",
                "due_date":      r[13].isoformat() if r[13] else None,
                "priority":      r[14] or 3,
                "source_count":  r[15] if len(r) > 15 else 0,
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
        """Mark from_name as merged into into_name; remap junction rows."""
        if not db.is_available():
            return
        into_id = self.get_or_create_tag(project, into_name)
        if not into_id:
            return
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_MERGE_TAGS, (into_id, project, from_name))
                    row = cur.fetchone()
                    if row:
                        from_id = str(row[0])
                        cur.execute(_SQL_REMAP_MRR_TAGS, (into_id, from_id))
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
        """Create mem_mrr_tags rows for each key:value in context_tags."""
        if not context_tags or not db.is_available():
            return
        try:
            for key, value in context_tags.items():
                tag_name = (
                    f"{key}:{value}"
                    if key not in ("feature", "bug_ref")
                    else str(value)
                )
                tag_id = self.get_or_create_tag(project, tag_name)
                if tag_id:
                    self.link_to_mirroring(
                        tag_id,
                        session_id=session_id,
                        session_src_desc=session_src_desc,
                        prompt_id=prompt_id,
                        auto_tagged=True,
                    )
        except Exception as e:
            log.debug(f"MemoryTagging.tag_from_context error: {e}")

    def get_relations(self, project: str) -> list[dict]:
        """Return all tag relations for tags belonging to a project."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_RELATIONS, (project,))
                    rows = cur.fetchall()
            return [
                {
                    "id":           str(r[0]),
                    "from_tag_id":  str(r[1]),
                    "relation":     r[2],
                    "to_tag_id":    str(r[3]),
                    "note":         r[4],
                    "source":       r[5],
                    "created_at":   r[6].isoformat() if r[6] else None,
                }
                for r in rows
            ]
        except Exception as e:
            log.debug(f"MemoryTagging.get_relations error: {e}")
            return []

    def delete_relation(self, relation_id: str) -> bool:
        """Delete a tag relation by UUID. Returns True if deleted."""
        if not db.is_available():
            return False
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_DELETE_RELATION, (relation_id,))
                    return cur.fetchone() is not None
        except Exception as e:
            log.debug(f"MemoryTagging.delete_relation error: {e}")
            return False

    # ── AI suggestion flow ──────────────────────────────────────────────────

    async def suggest_tags_for_untagged(
        self, project: str, batch_size: int = 20
    ) -> list[dict]:
        """Suggest planner_tags for rows with ai_tags IS NULL.

        Steps:
        1. Query untagged rows across prompts / commits / items
        2. Load existing planner_tags for project
        3. Call Haiku with ai_tag_suggestion prompt per row
        4. Return list of suggestion dicts

        Returns: [{source_type, source_id, content_preview, suggested_tag, is_new, reasoning}]
        """
        if not db.is_available():
            return []

        # Gather untagged rows
        per_type = max(1, batch_size // 3)
        untagged: list[dict] = []
        for stype in ("prompt", "commit", "item"):
            untagged.extend(_mirroring.get_untagged(project, stype, limit=per_type))

        if not untagged:
            return []

        # Load existing tag names
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_LIST_PROJECT_TAGS, (project,))
                    existing_tags = [r[0] for r in cur.fetchall()]
        except Exception:
            existing_tags = []

        # Load AI prompt
        sys_prompt = (
            "Given a content snippet and a list of existing project tags, "
            "suggest the best matching tag (or a new name if none fits). "
            'Return JSON: {"tag": str, "is_new": bool, "reasoning": str}'
        )
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_LOAD_AI_TAG_PROMPT)
                    row = cur.fetchone()
                    if row:
                        sys_prompt = row[0]
        except Exception:
            pass

        try:
            from data.dl_api_keys import get_key
            import anthropic
            import json
            from core.config import settings

            api_key = get_key("claude") or get_key("anthropic")
            if not api_key:
                return []

            client = anthropic.AsyncAnthropic(api_key=api_key)
            suggestions = []
            tags_list = ", ".join(existing_tags[:50]) if existing_tags else "(none yet)"

            for row in untagged:
                user_content = (
                    f"Existing tags: {tags_list}\n\n"
                    f"Content preview:\n{row['content_preview']}"
                )
                try:
                    resp = await client.messages.create(
                        model=settings.haiku_model,
                        max_tokens=150,
                        system=sys_prompt,
                        messages=[{"role": "user", "content": user_content}],
                    )
                    text = (resp.content[0].text if resp.content else "").strip()
                    parsed = json.loads(text)
                    suggestions.append({
                        "source_type":     row["source_type"],
                        "source_id":       row["id"],
                        "content_preview": row["content_preview"],
                        "suggested_tag":   parsed.get("tag", ""),
                        "is_new":          parsed.get("is_new", True),
                        "reasoning":       parsed.get("reasoning", ""),
                    })
                except Exception:
                    pass

            return suggestions
        except Exception as e:
            log.debug(f"MemoryTagging.suggest_tags_for_untagged error: {e}")
            return []

    async def apply_suggestion(
        self,
        project: str,
        source_type: str,
        source_id: str,
        tag_name: str,
        session_id: Optional[str] = None,
        session_src_desc: Optional[str] = None,
    ) -> bool:
        """Apply an AI suggestion: create/get tag, link to source, mark approved."""
        if not db.is_available():
            return False
        try:
            # Get the ai_suggestion category id
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_AI_SUGGESTION_CAT)
                    cat_row = cur.fetchone()
            cat_id = cat_row[0] if cat_row else None

            tag_id = self.get_or_create_tag(project, tag_name, category_id=cat_id)
            if not tag_id:
                return False

            # Link to mirroring row
            kwargs: dict = {"session_id": session_id, "session_src_desc": session_src_desc, "auto_tagged": True}
            if source_type == "prompt":
                kwargs["prompt_id"] = source_id
            elif source_type == "commit":
                try:
                    kwargs["commit_id"] = int(source_id)
                except ValueError:
                    pass
            elif source_type == "item":
                kwargs["item_id"] = source_id

            self.link_to_mirroring(tag_id, **kwargs)
            _mirroring.set_ai_tag_status(source_type, source_id, "approved")
            return True
        except Exception as e:
            log.debug(f"MemoryTagging.apply_suggestion error: {e}")
            return False

    def ignore_suggestion(self, source_type: str, source_id: str) -> None:
        """Mark a row as ignored by the AI tagging flow."""
        _mirroring.set_ai_tag_status(source_type, source_id, "ignored")
