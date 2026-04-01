"""
memory_tagging.py — Layer 2 of the three-layer memory architecture.

Maps planner_tags (parent-child hierarchy) to mirroring rows and AI events via the
unified mem_tags_relations table (replaces the dropped mem_mrr_tags, mem_ai_tags, and
mem_ai_tags_relations tables).  Also handles the AI tag suggestion workflow:
get_untagged → Haiku suggestion → apply or ignore, and the 3-level work-item-to-tag
matching pipeline (exact name → semantic embedding → Claude Haiku judgment).

Public API::

    tagging = MemoryTagging()
    tag_id = tagging.get_or_create_tag(project, name, category_id)
    tagging.link_to_mirroring(tag_id, 'prompt', prompt_uuid)
    tagging.link_to_event(tag_id, event_uuid, ai_suggested=True)
    tree = tagging.get_tag_tree(project)
    tagging.tag_from_context(project, prompt_id, context_tags, session_id, src_desc)

    # AI suggestion flow
    suggestions = await tagging.suggest_tags_for_untagged(project)
    await tagging.apply_suggestion(project, source_type, source_id, tag_name, ...)
    tagging.ignore_suggestion(source_type, source_id)

    # Work-item matching
    matches = await tagging.match_work_item_to_tags(project, work_item_id)
"""
from __future__ import annotations

import logging
from typing import Optional

import anthropic
import json
import openai

from core.config import settings
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
    ON CONFLICT (client_id, project, name, category_id) DO NOTHING
    RETURNING id
"""

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.lifecycle, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.short_desc, t.due_date, t.priority,
           (SELECT COUNT(*) FROM mem_tags_relations mr
            WHERE mr.tag_id = t.id) AS source_count
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
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

_SQL_REMAP_RELATIONS = """
    UPDATE mem_tags_relations SET tag_id=%s::uuid WHERE tag_id=%s::uuid
"""

_SQL_GET_BLOCKERS = """
    WITH project_tags AS (
        SELECT id, name FROM planner_tags WHERE client_id=1 AND project=%s AND status='active'
    )
    SELECT f.name AS from_name, r.related_type, t.name AS to_name, NULL AS note
    FROM mem_tags_relations r
    JOIN planner_tags f ON f.id = r.tag_id
    JOIN planner_tags t ON t.name = r.related_id
    WHERE r.related_type IN ('blocks', 'depends_on')
      AND r.tag_id IN (SELECT id FROM project_tags)
    ORDER BY r.related_type, f.name
"""

# Find mem_ai_events rows that have no mem_tags_relations entries yet
_SQL_GET_UNTAGGED_EVENTS = """
    SELECT me.id, me.project, me.summary, me.event_type
    FROM mem_ai_events me
    WHERE me.project = %s
      AND NOT EXISTS (
        SELECT 1 FROM mem_tags_relations r
        WHERE r.related_type = 'memory_event' AND r.related_id = me.id::TEXT
      )
    ORDER BY me.created_at DESC LIMIT %s
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
        source_type: str,
        source_id: str,
        auto_tagged: bool = False,
    ) -> None:
        """Link a tag to a mirrored source row (prompt, commit, item, message)."""
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id)
                    VALUES (%s, 'mirror', %s, %s)
                    ON CONFLICT (tag_id, related_type, related_id) DO NOTHING
                """, (tag_id, source_type, str(source_id)))
                conn.commit()

    def link_to_event(self, tag_id: str, event_id: str, ai_suggested: bool = False) -> None:
        """Link a tag to a memory event (prompt batch, commit, session summary).

        ai_suggested=True leaves related_approved as NULL (pending review).
        ai_suggested=False marks it immediately as 'approved' (manual assignment).
        """
        approved = None if ai_suggested else 'approved'
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, related_approved)
                    VALUES (%s, 'ai', 'memory_event', %s, %s)
                    ON CONFLICT (tag_id, related_type, related_id)
                    DO UPDATE SET related_approved = EXCLUDED.related_approved
                """, (tag_id, str(event_id), approved))
                conn.commit()

    # ── Internal relation helper ────────────────────────────────────────────

    def _upsert_relation(
        self,
        tag_id: str,
        layer: str,
        rel_type: str,
        rel_id: str,
        score: float = None,
        approved: str = None,
    ) -> None:
        """Insert or update a mem_tags_relations row."""
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mem_tags_relations
                        (tag_id, related_layer, related_type, related_id, related_type_score, related_approved)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tag_id, related_type, related_id) DO UPDATE SET
                        related_type_score = EXCLUDED.related_type_score,
                        related_approved   = EXCLUDED.related_approved
                """, (tag_id, layer, rel_type, str(rel_id), score, approved))
                conn.commit()

    # ── Tag tree / listing ──────────────────────────────────────────────────

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
                        cur.execute(_SQL_REMAP_RELATIONS, (into_id, from_id))
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
        """Create mem_tags_relations rows for each key:value in context_tags."""
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
                    self.link_to_mirroring(tag_id, "prompt", prompt_id, auto_tagged=True)
        except Exception as e:
            log.debug(f"MemoryTagging.tag_from_context error: {e}")

    def add_relation_by_name(
        self,
        project: str,
        from_name: str,
        relation: str,
        to_name: str,
        note: Optional[str] = None,
        source: str = "manual",
    ) -> bool:
        """Add a relation using tag names instead of UUIDs (creates tags if missing).

        Stores a mem_tags_relations row where the 'from' tag links to the 'to' tag
        name via related_type=relation and related_id=to_tag_uuid.
        Returns True if the relation was created/already existed.
        """
        from_id = self.get_or_create_tag(project, from_name)
        to_id   = self.get_or_create_tag(project, to_name)
        if not from_id or not to_id:
            return False
        try:
            self._upsert_relation(from_id, 'ai', relation, to_id, approved=source)
            return True
        except Exception as e:
            log.debug(f"MemoryTagging.add_relation_by_name error: {e}")
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
        """Return only blocks/depends_on relations for CLAUDE.md surface."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_BLOCKERS, (project,))
                    rows = cur.fetchall()
            return [
                {"from": r[0], "relation": r[1], "to": r[2], "note": r[3] or ""}
                for r in rows
            ]
        except Exception as e:
            log.debug(f"MemoryTagging.get_blockers_and_deps error: {e}")
            return []

    # ── AI suggestion flow ──────────────────────────────────────────────────

    async def suggest_tags_for_untagged(
        self, project: str, batch_size: int = 20
    ) -> list[dict]:
        """Suggest planner_tags for untagged rows in both mem_mrr_* and mem_ai_events.

        Steps:
        1. Query untagged rows across mem_mrr_* tables (ai_tags IS NULL)
        2. Query mem_ai_events with no mem_tags_relations entries (new AI events)
        3. Load existing planner_tags for project
        4. Call Haiku with ai_tag_suggestion prompt per row
        5. Return list of suggestion dicts

        Returns: [{source_type, source_id, content_preview, suggested_tag, is_new, reasoning}]
        source_type is 'prompt'|'commit'|'item' for mirroring rows,
        or the event_type string (e.g. 'prompt_batch'|'commit'|'item') for AI events
        (distinguished by an extra 'layer': 'mrr'|'ai' field).
        """
        if not db.is_available():
            return []

        # Gather untagged mirroring rows (ai_tags IS NULL)
        per_type = max(1, batch_size // 4)
        untagged: list[dict] = []
        for stype in ("prompt", "commit", "item"):
            untagged.extend(_mirroring.get_untagged(project, stype, limit=per_type))

        # Gather untagged mem_ai_events (no mem_tags_relations rows)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_UNTAGGED_EVENTS, (project, per_type))
                    for row in cur.fetchall():
                        untagged.append({
                            "id":              str(row[0]),
                            "source_type":     row[3],   # event_type as source_type
                            "content_preview": row[2] or "",
                            "layer":           "ai",     # marks this as a mem_ai_events row
                        })
        except Exception as e:
            log.debug(f"suggest_tags_for_untagged (events) error: {e}")

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
        layer: str = "mrr",
    ) -> bool:
        """Apply an AI suggestion: create/get tag, link to source, mark approved.

        layer='mrr'  → source_type is 'prompt'|'commit'|'item'|'message';
                       links to mem_tags_relations (mirror layer) and sets ai_tags='approved'.
        layer='ai'   → source_type is a mem_ai_events event_type string;
                       source_id is a mem_ai_events UUID;
                       links to mem_tags_relations (ai layer, ai_suggested=True).
        """
        if not db.is_available():
            return False
        try:
            # Resolve ai_suggestion category
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_AI_SUGGESTION_CAT)
                    cat_row = cur.fetchone()
            cat_id = cat_row[0] if cat_row else None

            tag_id = self.get_or_create_tag(project, tag_name, category_id=cat_id)
            if not tag_id:
                return False

            if layer == "ai":
                # Link directly to the mem_ai_events row
                self.link_to_event(tag_id, source_id, ai_suggested=True)
            else:
                # Link to the mirroring row and mark it approved
                self.link_to_mirroring(tag_id, source_type, source_id, auto_tagged=True)
                _mirroring.set_ai_tag_status(source_type, source_id, "approved")

            return True
        except Exception as e:
            log.debug(f"MemoryTagging.apply_suggestion error: {e}")
            return False

    def ignore_suggestion(self, source_type: str, source_id: str) -> None:
        """Mark a row as ignored by the AI tagging flow."""
        _mirroring.set_ai_tag_status(source_type, source_id, "ignored")

    # ── Work-item to tag matching ───────────────────────────────────────────

    async def match_work_item_to_tags(self, project: str, work_item_id: str) -> list[dict]:
        """3-level matching: exact name → semantic (>0.85 auto) → Claude judgment (0.70–0.85).

        Returns list of dicts: {tag_id, relation, confidence}
        """
        wi = self._load_work_item(work_item_id)
        if not wi:
            return []

        # Level 1 — exact name match
        tag = self._find_exact_tag(project, wi['name'])
        if tag:
            self._upsert_relation(tag['id'], 'ai', 'work_item', work_item_id, score=1.0, approved='approved')
            return [{'tag_id': tag['id'], 'relation': 'exact', 'confidence': 1.0}]

        # Level 2 — semantic similarity
        query = ' '.join(filter(None, [wi.get('name', ''), wi.get('description', ''), wi.get('summary', '')]))
        if not query.strip():
            return []

        try:
            emb = await self._embed_text(query)
        except Exception:
            return []

        candidates = self._vector_search_tags(project, emb, limit=15)
        strong = [c for c in candidates if c['score'] > 0.85]
        border = [c for c in candidates if 0.70 < c['score'] <= 0.85]

        results = []
        for c in strong:
            self._upsert_relation(c['id'], 'ai', 'work_item', work_item_id, score=c['score'], approved='approved')
            results.append({'tag_id': c['id'], 'relation': 'similar', 'confidence': c['score']})

        # Level 3 — Claude Haiku judgment for borderline candidates
        if border:
            try:
                judgments = await self._claude_judge_candidates(wi, border)
                for j in judgments:
                    if j.get('relation') not in (None, 'none'):
                        approved = 'approved' if j['relation'] == 'exact' else None
                        self._upsert_relation(
                            j['tag_id'], 'ai', 'work_item', work_item_id,
                            score=j.get('confidence'), approved=approved
                        )
                        results.append(j)
            except Exception:
                pass

        return results

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load_work_item(self, work_item_id: str) -> dict | None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, description, summary, category_name
                    FROM mem_ai_work_items WHERE id = %s
                """, (work_item_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {'id': str(row[0]), 'name': row[1], 'description': row[2] or '',
                        'summary': row[3] or '', 'category_name': row[4] or ''}

    def _find_exact_tag(self, project: str, name: str) -> dict | None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category_id FROM planner_tags
                    WHERE project = %s AND LOWER(name) = LOWER(%s)
                      AND status != 'archived' LIMIT 1
                """, (project, name))
                row = cur.fetchone()
                if not row:
                    return None
                return {'id': str(row[0]), 'name': row[1], 'category_id': row[2]}

    def _vector_search_tags(self, project: str, embedding: list, limit: int = 15) -> list[dict]:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category_id, short_desc,
                           1 - (embedding <=> %s::vector) AS score
                    FROM planner_tags
                    WHERE project = %s AND embedding IS NOT NULL AND status != 'archived'
                    ORDER BY embedding <=> %s::vector LIMIT %s
                """, (embedding, project, embedding, limit))
                rows = cur.fetchall()
                return [{'id': str(r[0]), 'name': r[1], 'category_id': r[2],
                         'short_desc': r[3], 'score': float(r[4])} for r in rows]

    async def _embed_text(self, text: str) -> list:
        """Embed text using OpenAI text-embedding-3-small."""
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(
            model='text-embedding-3-small',
            input=text[:8000]
        )
        return resp.data[0].embedding

    async def _claude_judge_candidates(self, wi: dict, candidates: list[dict]) -> list[dict]:
        """Use Claude Haiku to judge borderline tag candidates."""
        cand_text = '\n'.join(
            f"- {c['name']} (score:{c['score']:.2f}) | {c.get('short_desc','')}"
            for c in candidates
        )
        prompt = (
            f"WORK ITEM: name: {wi['name']}  summary: {wi.get('description','')}\n"
            f"CANDIDATE TAGS:\n{cand_text}\n\n"
            "For each candidate, determine if it matches this work item.\n"
            "Exact: same concept, scope, intent. Similar: overlapping but not identical. None: unrelated.\n"
            'Respond ONLY in JSON: {"matches":[{"tag_name":"...","relation":"exact|similar|none","confidence":0.0-1.0}]}'
        )
        system = (
            "You are a technical project memory assistant. "
            "Given an AI-generated work item and candidate tags, determine if any match. "
            "Respond ONLY in JSON."
        )

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        msg = await client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=512,
            system=system,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = msg.content[0].text.strip()
        data = json.loads(text)
        name_to_id = {c['name']: c['id'] for c in candidates}
        results = []
        for m in data.get('matches', []):
            tid = name_to_id.get(m.get('tag_name'))
            if tid:
                results.append({
                    'tag_id': tid,
                    'relation': m.get('relation', 'none'),
                    'confidence': float(m.get('confidence', 0.0))
                })
        return results
