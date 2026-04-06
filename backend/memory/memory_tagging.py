"""
memory_tagging.py — Tag management for planner_tags and work-item matching.

Manages planner_tags (parent-child hierarchy) and the 3-level work-item-to-tag
matching pipeline (exact name → semantic embedding → Claude Haiku judgment).
MRR rows now use inline tags TEXT[] — no junction table needed.

Public API::

    tagging = MemoryTagging()
    tag_id = tagging.get_or_create_tag(project, name, category_id)
    tree = tagging.get_tag_tree(project)

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

log = logging.getLogger(__name__)

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_GET_TAG = """
    SELECT id FROM planner_tags
    WHERE project_id=%s AND name=%s
    LIMIT 1
"""

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (project_id, name, category_id, status)
    VALUES (%s, %s, %s, 'active')
    ON CONFLICT (project_id, name, category_id) DO NOTHING
    RETURNING id
"""

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.lifecycle, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.short_desc, t.due_date, t.priority, 0 AS source_count
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
            results.append({'tag_id': c['id'], 'relation': 'similar', 'confidence': c['score']})

        # Level 3 — Claude Haiku judgment for borderline candidates
        if border:
            try:
                judgments = await self._claude_judge_candidates(wi, border)
                for j in judgments:
                    if j.get('relation') not in (None, 'none'):
                        results.append(j)
            except Exception:
                pass

        return results

    # ── Private helpers ─────────────────────────────────────────────────────

    def _load_work_item(self, work_item_id: str) -> dict | None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, ai_name, ai_desc, summary, ai_category
                    FROM mem_ai_work_items WHERE id = %s
                """, (work_item_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {'id': str(row[0]), 'name': row[1], 'description': row[2] or '',
                        'summary': row[3] or '', 'category_name': row[4] or ''}

    def _find_exact_tag(self, project: str, name: str) -> dict | None:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category_id FROM planner_tags
                    WHERE project_id = %s AND LOWER(name) = LOWER(%s)
                      AND status != 'archived' LIMIT 1
                """, (project_id, name))
                row = cur.fetchone()
                if not row:
                    return None
                return {'id': str(row[0]), 'name': row[1], 'category_id': row[2]}

    def _vector_search_tags(self, project: str, embedding: list, limit: int = 15) -> list[dict]:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, category_id, short_desc,
                           1 - (embedding <=> %s::vector) AS score
                    FROM planner_tags
                    WHERE project_id = %s AND embedding IS NOT NULL AND status != 'archived'
                    ORDER BY embedding <=> %s::vector LIMIT %s
                """, (embedding, project_id, embedding, limit))
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
