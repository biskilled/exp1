"""
memory_promotion.py — Promotion pipeline from raw AI events to structured artifacts.

Handles three promotion operations:
  - promote_work_item: summarise a tag's work item into a 2-4 sentence status digest
  - promote_feature_snapshot: build the full 4-layer snapshot from all 6 batch types
    (prompt batches, commits, items, meetings, messages, agent actions)
  - detect_fact_conflicts: detect and resolve conflicts between new and existing facts

Also provides a relevance scoring utility (time-decay weighted importance).
"""
from __future__ import annotations

import json
import logging
import math
import re
from datetime import datetime, timezone
from typing import Optional

from core.database import db
from core.prompt_loader import prompts as _prompts

log = logging.getLogger(__name__)


async def _match_new_work_item(project: str, work_item_id: str) -> None:
    """Queue AI tag matching for a newly extracted work item."""
    try:
        from memory.memory_tagging import MemoryTagging
        from routers.route_work_items import _persist_matches
        matches = await MemoryTagging().match_work_item_to_tags(project, work_item_id)
        if matches:
            _persist_matches(work_item_id, matches)
    except Exception as e:
        log.debug(f"_match_new_work_item error: {e}")


# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_TAG_ID = """
    SELECT id FROM planner_tags
    WHERE project_id=%s AND name=%s
    LIMIT 1
"""

_SQL_GET_WORK_ITEM = """
    SELECT wi.id, wi.name_ai, wi.status_user, wi.acceptance_criteria_ai
    FROM mem_ai_work_items wi
    WHERE wi.project_id=%s
    ORDER BY wi.created_at DESC LIMIT 10
"""

_SQL_GET_WORK_ITEM_BY_NAME = """
    SELECT wi.id, wi.name_ai, wi.status_user, wi.acceptance_criteria_ai,
           wi.action_items_ai, wi.tag_id_user
    FROM mem_ai_work_items wi
    WHERE wi.project_id=%s AND wi.name_ai=%s
    LIMIT 1
"""

_SQL_PROMOTE_WORK_ITEM_FIELDS = """
    UPDATE mem_ai_work_items SET
        summary_ai             = CASE WHEN %s != '' THEN %s ELSE summary_ai END,
        acceptance_criteria_ai = CASE WHEN %s != '' THEN %s ELSE acceptance_criteria_ai END,
        action_items_ai        = CASE WHEN %s != '' THEN %s ELSE action_items_ai END,
        score_ai               = %s,
        updated_at             = NOW()
    WHERE id=%s AND project_id=%s
"""

_SQL_LIST_ACTIVE_WORK_ITEMS = """
    SELECT name_ai FROM mem_ai_work_items
    WHERE project_id=%s AND status_user NOT IN ('done', 'archived')
    ORDER BY created_at DESC
    LIMIT 50
"""

_SQL_GET_LINKED_EVENTS = """
    SELECT summary, action_items
    FROM mem_ai_events
    WHERE work_item_id=%s::uuid AND summary IS NOT NULL AND summary != ''
    ORDER BY created_at DESC
    LIMIT 5
"""


_SQL_UPDATE_WORK_ITEM_EMBEDDING = """
    UPDATE mem_ai_work_items SET embedding=%s::vector, updated_at=NOW()
    WHERE id=%s AND project_id=%s
"""

_SQL_GET_MEMORY_EVENTS = """
    SELECT me.id, me.summary, me.event_type, me.created_at, me.action_items
    FROM mem_ai_events me
    WHERE me.project_id=%s
    ORDER BY me.created_at DESC LIMIT 50
"""

_SQL_UPDATE_TAG_SNAPSHOT = """
    UPDATE planner_tags SET
        action_items = %s,
        updater      = 'ai',
        updated_at   = NOW()
    WHERE id = %s AND project_id = %s
"""

_SQL_GET_CURRENT_FACTS = """
    SELECT id, fact_key, fact_value, created_at
    FROM mem_ai_project_facts
    WHERE project_id=%s AND valid_until IS NULL
    ORDER BY fact_key
"""

_SQL_UPSERT_FACT = """
    INSERT INTO mem_ai_project_facts (project_id, fact_key, fact_value, category, valid_from)
    VALUES (%s, %s, %s, %s, NOW())
    ON CONFLICT (project_id, fact_key) WHERE valid_until IS NULL
    DO UPDATE SET
        fact_value = EXCLUDED.fact_value,
        category   = COALESCE(EXCLUDED.category, mem_ai_project_facts.category)
"""

_SQL_MARK_FACT_CONFLICT = """
    UPDATE mem_ai_project_facts
    SET conflict_status=%s
    WHERE project_id=%s AND fact_key=%s AND valid_until IS NULL
"""

_SQL_MARK_EVENTS_PROCESSED = """
    UPDATE mem_ai_events SET processed_at=NOW()
    WHERE id=ANY(%s::uuid[]) AND processed_at IS NULL
"""

# Find events not yet processed for work item extraction.
# processed_at is set after extract_work_items_from_events() handles the event —
# this prevents reprocessing while still allowing events to update existing work items.
_SQL_GET_UNEXTRACTED_EVENTS = """
    SELECT me.id, me.event_type, me.session_id, me.summary, me.action_items,
           me.created_at, me.tags
    FROM mem_ai_events me
    WHERE me.project_id=%s
      AND me.event_type IN ('prompt_batch', 'session_summary', 'commit')
      AND me.summary IS NOT NULL AND me.summary != ''
      AND me.processed_at IS NULL
      AND me.is_system = FALSE
    ORDER BY me.created_at DESC
    LIMIT %s
"""

_SQL_MARK_EVENT_EXTRACTED = """
    UPDATE mem_ai_events SET processed_at = NOW()
    WHERE id = %s::uuid AND processed_at IS NULL
"""

_SQL_UPDATE_EVENT_AI_TAGS = """
    UPDATE mem_ai_events
    SET tags = tags || jsonb_build_object(
        'ai_phase',   %s::text,
        'ai_feature', %s::text
    )
    WHERE id = %s::uuid
"""

_SQL_INSERT_EXTRACTED_WORK_ITEM = """
    INSERT INTO mem_ai_work_items
        (project_id, category_ai, name_ai,
         acceptance_criteria_ai, action_items_ai, tags, seq_num,
         quality_stage, dedup_status)
    VALUES (%s, %s, %s, %s, %s, %s::jsonb,
            (SELECT COALESCE(MAX(seq_num),0)+1 FROM mem_ai_work_items WHERE project_id=%s),
            'staging', 'new')
    ON CONFLICT (project_id, category_ai, name_ai) DO UPDATE SET
        acceptance_criteria_ai = CASE WHEN EXCLUDED.acceptance_criteria_ai != ''
                                      THEN EXCLUDED.acceptance_criteria_ai
                                      ELSE mem_ai_work_items.acceptance_criteria_ai END,
        action_items_ai      = CASE
                                    WHEN EXCLUDED.action_items_ai = '' THEN mem_ai_work_items.action_items_ai
                                    WHEN mem_ai_work_items.action_items_ai = '' THEN EXCLUDED.action_items_ai
                                    ELSE mem_ai_work_items.action_items_ai || E'\n---\n' || EXCLUDED.action_items_ai
                               END,
        tags                 = CASE WHEN EXCLUDED.tags != '{}'::jsonb
                                    THEN mem_ai_work_items.tags || EXCLUDED.tags
                                    ELSE mem_ai_work_items.tags END,
        updated_at           = NOW()
    RETURNING id, (xmax = 0) AS inserted
"""

_SQL_GET_ACTIVE_PLANNER_TAGS = """
    SELECT pt.name, tc.name AS category, pt.id
    FROM planner_tags pt
    JOIN mng_tags_categories tc ON tc.id = pt.category_id
    WHERE pt.project_id=%s AND pt.status NOT IN ('archived', 'done')
    ORDER BY tc.name, pt.name
"""

_SQL_DEDUP_TAG_CHECK = """
    SELECT id, name_ai FROM mem_ai_work_items
    WHERE project_id=%s AND category_ai=%s
      AND created_at > NOW() - INTERVAL '30 days'
      AND (tags @> %s::jsonb OR name_ai = %s)
    LIMIT 1
"""

_SQL_DEDUP_EMBED_CHECK = """
    SELECT id, name_ai, 1 - (embedding <=> %s::vector) AS sim
    FROM mem_ai_work_items
    WHERE project_id=%s AND category_ai=%s AND id != %s::uuid
      AND embedding IS NOT NULL
      AND created_at > NOW() - INTERVAL '30 days'
    ORDER BY embedding <=> %s::vector LIMIT 1
"""

_SQL_UPDATE_QUALITY_GATE = """
    UPDATE mem_ai_work_items
    SET quality_stage=%s, quality_issues=%s::jsonb, dedup_status=%s, updated_at=NOW()
    WHERE id=%s::uuid AND project_id=%s
"""

_SQL_COUNT_LINKED_EVENTS = """
    SELECT COUNT(*) FROM mem_ai_events
    WHERE work_item_id=%s::uuid AND project_id=%s
"""

# Link a single event row to a work item
_SQL_LINK_EVENT_TO_WI = """
    UPDATE mem_ai_events SET work_item_id = %s::uuid
    WHERE id = %s::uuid AND project_id = %s
"""

# Find work items that share the same feature tag (for dedup)
_SQL_WI_GROUPS_BY_FEATURE = """
    SELECT
        tags->>'feature' AS tag_val,
        'feature'        AS tag_key,
        array_agg(id::text ORDER BY
            CASE WHEN tag_id_user IS NOT NULL THEN 0 ELSE 1 END ASC,
            created_at ASC
        ) AS ids
    FROM mem_ai_work_items wi
    WHERE project_id = %s
      AND tags->>'feature' IS NOT NULL AND tags->>'feature' != ''
    GROUP BY 1
    HAVING COUNT(*) > 1
"""

_SQL_WI_GROUPS_BY_BUG = """
    SELECT
        tags->>'bug'  AS tag_val,
        'bug'         AS tag_key,
        array_agg(id::text ORDER BY
            CASE WHEN tag_id_user IS NOT NULL THEN 0 ELSE 1 END ASC,
            created_at ASC
        ) AS ids
    FROM mem_ai_work_items wi
    WHERE project_id = %s
      AND tags->>'bug' IS NOT NULL AND tags->>'bug' != ''
    GROUP BY 1
    HAVING COUNT(*) > 1
"""

# Keys considered "user intent" tags — copied from event tags to work item tags
_USER_TAG_KEYS = frozenset({"source", "phase", "feature", "bug", "component",
                             "doc_type", "design", "decision", "meeting", "customer"})


# ── Helpers ───────────────────────────────────────────────────────────────────

def compute_relevance(
    importance: int,
    created_at: datetime,
    is_foundational: bool = False,
) -> float:
    """
    Time-decayed relevance score. Formula: importance * exp(-0.01 * age_days).
    Foundational facts receive a floor of 50% importance.
    Returns a float in roughly [0, 10].
    """
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = (now - created_at).total_seconds() / 86400.0
    score = importance * math.exp(-0.01 * age_days)
    if is_foundational:
        floor = importance * 0.5
        score = max(score, floor)
    return round(score, 3)


def _relevance_sql_expr(importance_col: str = "importance",
                        created_col: str = "created_at") -> str:
    """SQL expression for time-decayed relevance (for ORDER BY in queries)."""
    return (
        f"{importance_col} * EXP(-0.01 * "
        f"EXTRACT(EPOCH FROM (NOW() - {created_col})) / 86400.0)"
    )


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


async def _call_llm(system_prompt: str, user_message: str, max_tokens: int = 1000) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return ""
        import anthropic
        from core.config import settings
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=settings.claude_haiku_model if hasattr(settings, "claude_haiku_model")
                  else "claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_llm error: {e}")
        return ""


async def _embed_text(text: str) -> Optional[list]:
    try:
        from memory.memory_embedding import get_embedding
        return await get_embedding(text)
    except Exception:
        return None


async def _embed_work_item(project_id: int, wi_id: str, name_ai: str,
                           summary_ai: str = "") -> None:
    """Embed a work item's text fields and persist to embedding column."""
    text = " ".join(filter(None, [name_ai, summary_ai])).strip()
    if not text:
        return
    try:
        vec = await _embed_text(text)
        if vec is None:
            return
        with db.conn() as conn:
            with conn.cursor() as cur:
                import json as _json
                cur.execute(
                    _SQL_UPDATE_WORK_ITEM_EMBEDDING,
                    (_json.dumps(vec), wi_id, project_id),
                )
    except Exception as e:
        log.debug(f"_embed_work_item error ({wi_id[:8]}): {e}")


# ── MemoryPromotion ───────────────────────────────────────────────────────────

class MemoryPromotion:
    """
    Promotes raw memory events into structured artifacts:
      - Work item summaries (work_item_promotion)
      - 4-layer feature snapshots (feature_snapshot)
      - Project fact conflict detection (conflict_detection)
    """

    async def promote_work_item(
        self, project: str, name_ai: str
    ) -> Optional[dict]:
        """
        Refresh all 4 AI text fields for a work item from its linked events + commits.
        Returns {work_item_id, name_ai, summary_ai} or None on failure.
        """
        if not db.is_available():
            return None

        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORK_ITEM_BY_NAME, (project_id, name_ai))
                row = cur.fetchone()

        if not row:
            log.debug(f"promote_work_item: no work item found for '{name_ai}'")
            return None

        wi_id, wi_name, status_user, ac, action_items, tag_id_user = row

        # Fetch up to 5 linked event summaries for richer context
        linked_events: list[str] = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_LINKED_EVENTS, (str(wi_id),))
                    for ev_summary, ev_actions in cur.fetchall():
                        parts = [p for p in [ev_summary, ev_actions] if p and p.strip()]
                        if parts:
                            linked_events.append(" | ".join(parts))
        except Exception as e:
            log.debug(f"promote_work_item: linked events fetch error: {e}")

        system_prompt = _prompts.content("work_item_promotion") or (
            "Given a work item, produce a structured PM update. "
            "Return JSON only: {\"summary_ai\": \"...\", \"acceptance_criteria_ai\": \"...\", "
            "\"action_items_ai\": \"...\"}"
        )

        events_section = ""
        if linked_events:
            events_section = "\n\nLinked Events (recent):\n" + "\n".join(
                f"- {e[:200]}" for e in linked_events
            )

        user_msg = (
            f"Work Item: {wi_name}\n"
            f"User Status: {status_user}\n"
            f"Acceptance Criteria:\n{ac or '(none)'}\n"
            f"Action Items:\n{action_items or '(none)'}"
            + events_section
        )

        raw = await _call_llm(system_prompt, user_msg, max_tokens=600)
        parsed = _parse_json(raw)
        if not parsed:
            log.debug(f"promote_work_item: LLM returned no JSON for '{name_ai}'")
            return None

        new_summary_ai   = (parsed.get("summary_ai") or "").strip()
        new_ac           = (parsed.get("acceptance_criteria_ai") or "").strip()
        new_action_items = (parsed.get("action_items_ai") or "").strip()
        try:
            new_score_ai = max(0, min(5, int(parsed.get("score_ai") or 0)))
        except (TypeError, ValueError):
            new_score_ai = 0

        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_PROMOTE_WORK_ITEM_FIELDS,
                        (
                            new_summary_ai,   new_summary_ai,
                            new_ac,           new_ac,
                            new_action_items, new_action_items,
                            new_score_ai,
                            str(wi_id),       project_id,
                        ),
                    )
        except Exception as e:
            log.debug(f"promote_work_item: DB update failed: {e}")

        # Re-embed with updated text
        await _embed_work_item(project_id, str(wi_id), wi_name, new_summary_ai)

        return {
            "work_item_id": str(wi_id),
            "name_ai":      name_ai,
            "summary_ai":   new_summary_ai,
            "score_ai":     new_score_ai,
        }

    async def promote_all_work_items(self, project: str) -> dict:
        """
        Refresh all active work items via promote_work_item().
        Called automatically at the end of /memory POST.
        Returns {"promoted": N, "total": M}.
        """
        if not db.is_available():
            return {"promoted": 0, "total": 0}

        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_LIST_ACTIVE_WORK_ITEMS, (project_id,))
                    names = [r[0] for r in cur.fetchall()]
        except Exception as e:
            log.debug(f"promote_all_work_items: list query failed: {e}")
            return {"promoted": 0, "total": 0}

        total = len(names)
        promoted = 0
        for name in names:
            try:
                result = await self.promote_work_item(project, name)
                if result:
                    promoted += 1
            except Exception as e:
                log.debug(f"promote_all_work_items: failed for '{name}': {e}")

        log.info(f"promote_all_work_items: promoted={promoted}/{total} for '{project}'")
        return {"promoted": promoted, "total": total}

    async def promote_feature_snapshot(
        self, project: str, tag_name: str
    ) -> Optional[dict]:
        """
        Build the full 4-layer snapshot for a feature tag from all 6 batch types.
        Stores the result inline on planner_tags (summary, action_items, design, code_summary,
        embedding) and marks events as processed.
        Returns the snapshot dict or None on failure.
        """
        if not db.is_available():
            return None

        # Resolve tag
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_TAG_ID, (project_id, tag_name))
                tag_row = cur.fetchone()
        if not tag_row:
            log.debug(f"promote_feature_snapshot: tag '{tag_name}' not found")
            return None
        tag_id = str(tag_row[0])

        # Load recent memory events for this project
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_MEMORY_EVENTS, (project_id,))
                events = cur.fetchall()

        if not events:
            log.debug(f"promote_feature_snapshot: no events for project '{project}'")
            return None

        # Load recent work items for this project
        work_item_status = None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORK_ITEM, (project_id,))
                wi_rows = cur.fetchall()
        if wi_rows:
            work_item_status = wi_rows[0][3]  # lifecycle_status from first linked work item

        # Load current project facts (for context)
        facts_context: dict = {}
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_CURRENT_FACTS, (project_id,))
                for f_id, f_key, f_val, _ in cur.fetchall():
                    facts_context[f_key] = f_val

        # Group events by source type (all 6 batch types)
        batch_types = {
            "prompt_batch": [],
            "commit":       [],
            "item":         [],
            "message":      [],
            "session":      [],
            "workflow":     [],
        }
        event_ids: list[str] = []
        for ev_id, summary, event_type, created_at, action_items in events:
            event_ids.append(str(ev_id))
            rel = compute_relevance(1, created_at)
            bucket = event_type if event_type in batch_types else "prompt_batch"
            content = summary or ""
            if action_items:
                content += f" | actions: {action_items}"
            batch_types[bucket].append(f"[relevance={rel:.2f}] {content}")

        # Build user message with all 6 batch type sections
        sections = []
        type_labels = {
            "prompt_batch": "Prompt Batches",
            "commit":       "Commits",
            "item":         "Requirements / Decisions / Meetings",
            "message":      "Messages",
            "session":      "Sessions",
            "workflow":     "Agent Actions",
        }
        for stype, items in batch_types.items():
            if items:
                sections.append(
                    f"## {type_labels[stype]}\n"
                    + "\n".join(f"- {i}" for i in items)
                )

        if facts_context:
            facts_lines = "\n".join(f"- {k}: {v}" for k, v in facts_context.items())
            sections.append(f"## Current Project Facts\n{facts_lines}")

        user_msg = (
            f"Feature: **{tag_name}**\nProject: {project}\n"
            + (f"Work Item Status: {work_item_status}\n" if work_item_status else "")
            + "\n\n".join(sections)
        )

        system_prompt = _prompts.content("feature_snapshot") or (
            "Produce a 4-layer feature snapshot as JSON with keys: "
            "requirements (str), action_items (str), "
            "design ({high_level, low_level, patterns_used}), "
            "code_summary ({files, key_classes, key_methods, dependencies_added, dependencies_removed}), "
            "relations (array of {from, relation, to, note}). "
            "Return ONLY valid JSON."
        )

        raw = await _call_llm(system_prompt, user_msg, max_tokens=2500)
        if not raw:
            return None

        parsed = _parse_json(raw)
        if not parsed:
            log.warning(f"promote_feature_snapshot: could not parse LLM JSON for '{tag_name}'")
            return None

        ai_relations: list[dict] = parsed.pop("relations", []) or []
        action_items = parsed.get("action_items", "")

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPDATE_TAG_SNAPSHOT,
                    (action_items, tag_id, project_id),
                )

                if event_ids:
                    cur.execute(_SQL_MARK_EVENTS_PROCESSED, (event_ids,))

        # Upsert AI-detected relations
        relations_upserted = 0
        if ai_relations:
            try:
                from memory.memory_tagging import MemoryTagging
                relations_upserted = MemoryTagging().upsert_relations_from_list(
                    project, ai_relations, source="ai_snapshot"
                )
            except Exception as e:
                log.debug(f"relation upsert error: {e}")

        log.info(
            f"Feature snapshot promoted for '{tag_name}': "
            f"{len(event_ids)} events, {relations_upserted} relations"
        )
        return {
            "tag_id":             tag_id,
            "tag_name":           tag_name,
            "project":            project,
            "action_items":       action_items,
            "events_processed":   len(event_ids),
            "relations_upserted": relations_upserted,
            "relations":          ai_relations,
        }

    async def detect_fact_conflicts(
        self,
        project: str,
        fact_key: str,
        fact_value: str,
        category: Optional[str] = None,
    ) -> dict:
        """
        Check if a new fact_value conflicts with existing facts for the same key.
        Uses semantic similarity (if embeddings available) or string comparison.
        If a conflict is detected, calls Claude for resolution.

        Returns {action, conflict_status, conflicting_fact_key, merged_value, reasoning}.
        action: 'ok' | 'supersede' | 'merge' | 'flag'
        """
        if not db.is_available():
            return {"action": "ok", "conflict_status": None}

        # Load existing facts
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_CURRENT_FACTS, (project_id,))
                existing = cur.fetchall()

        if not existing:
            return {"action": "ok", "conflict_status": None}

        # Find the most directly related existing fact (same key is an obvious update)
        existing_map = {row[1]: {"id": str(row[0]), "value": row[2]} for row in existing}

        if fact_key in existing_map:
            old_value = existing_map[fact_key]["value"]
            old_id = existing_map[fact_key]["id"]
            if old_value.strip().lower() == fact_value.strip().lower():
                return {"action": "ok", "conflict_status": "ok"}

            # Values differ — call LLM to resolve
            resolution = await self._resolve_conflict(
                fact_key, old_value, fact_value
            )
            if resolution:
                action = resolution.get("resolution", "flag")
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            _SQL_MARK_FACT_CONFLICT,
                            (action, project, fact_key),
                        )
                return {
                    "action": action,
                    "conflict_status": "pending_review" if action == "flag" else action,
                    "conflicting_fact_key": fact_key,
                    "old_value": old_value,
                    "merged_value": resolution.get("merged_value"),
                    "reasoning": resolution.get("reasoning"),
                }

        return {"action": "ok", "conflict_status": None}

    async def _resolve_conflict(
        self, fact_key: str, old_value: str, new_value: str
    ) -> Optional[dict]:
        system_prompt = _prompts.content("conflict_detection") or (
            "You are a project memory conflict resolver. Given two versions of a fact, "
            "decide whether the new value supersedes, merges with, or conflicts with the old. "
            "Return JSON only: "
            "{\"conflict\": true|false, \"conflicting_fact_key\": \"...\", "
            "\"resolution\": \"supersede|merge|flag\", "
            "\"merged_value\": \"...\", \"reasoning\": \"one sentence\"}"
        )
        user_msg = (
            f"Fact key: {fact_key}\n"
            f"Old value: {old_value}\n"
            f"New value: {new_value}"
        )
        raw = await _call_llm(system_prompt, user_msg, max_tokens=300)
        if not raw:
            return None
        return _parse_json(raw) or None

    async def extract_work_items_from_events(
        self,
        project: str,
        batch_size: int = 10,
    ) -> int:
        """Scan unprocessed events and map them to work items.

        Priority:
          1. User-tag first — if the event carries a 'feature' or 'bug' tag,
             use that tag value AS the work item name.  All events with the same
             feature/bug value are collapsed into ONE work item via the UNIQUE
             (project_id, category_ai, name_ai) constraint.
          2. AI fallback — only for events with no user tag. Haiku extracts
             up to 2 slugs per event; limited proportionally to planner tag count.

        Improvements over baseline:
          - Scope contract: existing planner tags injected into AI prompt context
          - matched_tag: AI can anchor to an existing tag → direct tag_id_ai set
          - Cap: max new items = max(5, int(total_planner_tags * 1.5))
          - Dedup tier 1: tag-set hash check before INSERT
          - Quality gate: name specificity + evidence count gate post-INSERT

        The work_item_id is set on the event row so the link is queryable.
        Returns count of work items created (inserts only, not updates).
        """
        if not db.is_available():
            return 0

        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_UNEXTRACTED_EVENTS, (project_id, batch_size))
                    events = cur.fetchall()
        except Exception as e:
            log.debug(f"extract_work_items_from_events query error: {e}")
            return 0

        if not events:
            return 0

        # ── 3a. Load planner tags once per run ────────────────────────────────
        tag_lookup: dict[str, tuple[str, str]] = {}  # name.lower() → (id, category)
        scope_context = ""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_ACTIVE_PLANNER_TAGS, (project_id,))
                    tag_rows = cur.fetchall()

            if tag_rows:
                by_cat: dict[str, list[str]] = {}
                for t_name, t_cat, t_id in tag_rows:
                    tag_lookup[t_name.lower()] = (str(t_id), t_cat)
                    by_cat.setdefault(t_cat, []).append(t_name)

                lines = ["EXISTING PLANNER TAGS (match to these FIRST — use exact name if work relates to it):"]
                for cat, names in sorted(by_cat.items()):
                    lines.append(f"  {cat}: {', '.join(names)}")
                lines += [
                    "",
                    "SCOPE RULES:",
                    "- Return matched_tag: \"<name>\" when work clearly relates to an existing tag",
                    "- If no match, return matched_tag: null — a new work item will be proposed",
                    "- MAX 1 new work item per event (matched items do not count toward this limit)",
                    "- Be specific: reject vague titles like \"fix bug\", \"add feature\", \"update code\"",
                    "",
                ]
                scope_context = "\n".join(lines)
        except Exception as e:
            log.debug(f"extract_work_items: tag load error: {e}")

        # ── 3b. Cap: max new items proportional to planner tag count ─────────
        total_planner_tags = len(tag_lookup)
        max_new_items = max(5, int(total_planner_tags * 1.5))
        new_items_this_run = 0

        ai_fallback_prompt = _prompts.content("work_item_extraction") or (
            "Given a digest of development activity, identify at most 2 actionable work items. "
            "Return JSON only: {\"items\": [{\"category\": \"bug|feature|task\", "
            "\"name\": \"short-slug\", \"matched_tag\": null, "
            "\"acceptance_criteria\": \"- [ ] ...\", \"action_items\": \"- ...\"}]}. "
            "Use lowercase-hyphenated slugs. Return {\"items\": []} if nothing actionable."
        )

        created = 0

        for ev_id, event_type, session_id, summary, action_items, created_at, tags in events:
            content_parts = [p for p in [summary, action_items] if p and p.strip()]
            content = "\n\n".join(content_parts)[:3000]
            ev_id_str = str(ev_id)

            # Always mark processed so we don't retry
            def _mark():
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(_SQL_MARK_EVENT_EXTRACTED, (ev_id_str,))
                except Exception:
                    pass

            if not content.strip():
                _mark()
                continue

            event_tags = tags or {}
            # Filter to user-intent keys only
            wi_tags: dict = {k: v for k, v in event_tags.items()
                             if k in _USER_TAG_KEYS and v}

            feature_val = event_tags.get("feature", "").strip()
            bug_val     = event_tags.get("bug", "").strip()

            wi_id: Optional[str] = None
            wi_name_for_embed: str = ""

            # ── Path 1: user tag exists → 1 work item per tag value ──────────
            if feature_val or bug_val:
                # Prefer bug over feature when both present (more specific)
                if bug_val:
                    category, tag_name = "bug", bug_val
                else:
                    category, tag_name = "feature", feature_val

                canonical_name = tag_name.lower().strip()[:200]
                wi_name_for_embed = canonical_name

                # Tier 1 dedup: same-name or matching tags already exist
                existing_wi_id = self._dedup_tier1(
                    project_id, category, canonical_name, wi_tags
                )
                if existing_wi_id:
                    wi_id = existing_wi_id
                else:
                    try:
                        with db.conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    _SQL_INSERT_EXTRACTED_WORK_ITEM,
                                    (project_id, category, canonical_name,
                                     "", action_items or "", json.dumps(wi_tags),
                                     project_id),
                                )
                                row = cur.fetchone()
                                if row:
                                    wi_id = str(row[0])
                                    was_inserted = row[1] if len(row) > 1 else True
                                    if was_inserted:
                                        created += 1
                                        # Link to planner tag if present in lookup
                                        matched_id = tag_lookup.get(canonical_name, (None, None))[0]
                                        if matched_id:
                                            self._set_tag_id_ai(wi_id, matched_id)
                    except Exception as e:
                        log.debug(f"extract_work_items tag-path insert error: {e}")

            # ── Path 2: no user tag → limited AI extraction (prompt_batch/session_summary only) ──
            # Commit events without explicit feature/bug tags are skipped — they generate noise.
            # Only human-authored prompt batches and session summaries get AI extraction.
            elif event_type in ("prompt_batch", "session_summary"):
                # 3b. Cap gate — skip AI if we've already created too many new items this run
                if new_items_this_run >= max_new_items:
                    log.debug(
                        f"extract_work_items: cap reached ({new_items_this_run}/{max_new_items}), "
                        "skipping AI extraction for this event"
                    )
                    _mark()
                    continue

                # 3c. Prepend scope context to user message
                event_digest = f"Event type: {event_type}\nDate: {str(created_at)[:10]}\n\n{content}"
                if scope_context:
                    user_msg = scope_context + "\n---\n\nEVENT TO ANALYSE:\n" + event_digest
                else:
                    user_msg = event_digest

                raw = await _call_llm(ai_fallback_prompt, user_msg, max_tokens=600)
                parsed = _parse_json(raw) if raw else {}
                items = (parsed.get("items") or [])[:2]  # hard cap: 2 items max per untagged event

                for item in items:
                    name = (item.get("name") or "").strip().lower()[:200]
                    if not name:
                        continue
                    # Confidence gate
                    confidence = float(item.get("confidence") or 0.0)
                    if confidence < 0.75:
                        log.debug(f"extract_work_items: skipping '{name}' (confidence={confidence:.2f} < 0.75)")
                        continue
                    category = item.get("category", "task")
                    ac = (item.get("acceptance_criteria") or "").strip()[:1000]
                    ai_actions = (item.get("action_items") or "").strip()[:1000]

                    # 3d. matched_tag handling — directly link to planner tag
                    matched_tag_name = (item.get("matched_tag") or "").strip().lower()
                    pre_linked_tag_id: Optional[str] = None
                    pre_linked_category: Optional[str] = None
                    if matched_tag_name and matched_tag_name in tag_lookup:
                        pre_linked_tag_id, pre_linked_category = tag_lookup[matched_tag_name]
                        if pre_linked_category:
                            category = pre_linked_category

                    # Tier 1 dedup check before INSERT
                    existing_wi_id = self._dedup_tier1(project_id, category, name, wi_tags)
                    if existing_wi_id:
                        wi_id = existing_wi_id
                        # Still link event, but don't count as new
                    else:
                        try:
                            with db.conn() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        _SQL_INSERT_EXTRACTED_WORK_ITEM,
                                        (project_id, category, name,
                                         ac, ai_actions, json.dumps(wi_tags),
                                         project_id),
                                    )
                                    row = cur.fetchone()
                                    if row:
                                        wi_id = str(row[0])
                                        was_inserted = row[1] if len(row) > 1 else True
                                        if was_inserted:
                                            # Set tag_id_ai if matched
                                            if pre_linked_tag_id:
                                                self._set_tag_id_ai(wi_id, pre_linked_tag_id)
                                            else:
                                                # Count only unmatched new items toward the cap
                                                new_items_this_run += 1
                                                created += 1
                                            wi_name_for_embed = name
                        except Exception as e:
                            log.debug(f"extract_work_items ai-path insert error: {e}")

            # ── Link event → work item ────────────────────────────────────────
            if wi_id:
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(_SQL_LINK_EVENT_TO_WI,
                                        (wi_id, ev_id_str, project_id))
                    import asyncio as _aio
                    loop = _aio.get_event_loop()
                    if loop.is_running():
                        if wi_name_for_embed:
                            loop.create_task(_embed_work_item(
                                project_id, wi_id, wi_name_for_embed,
                            ))
                        # Only run async tag matching for newly inserted items (not dedup-merged)
                        loop.create_task(_match_new_work_item(project, wi_id))
                        loop.create_task(self._run_quality_gate_async(project_id, wi_id))
                except Exception as e:
                    log.debug(f"extract_work_items link error: {e}")

            _mark()

        log.info(
            f"extract_work_items_from_events: created={created} "
            f"events={len(events)} for '{project}'"
        )
        return created

    def _dedup_tier1(
        self,
        project_id: int,
        category: str,
        name: str,
        wi_tags: dict,
    ) -> Optional[str]:
        """Check for tag-set or name duplicate before INSERT. Returns existing id or None."""
        try:
            # Only check if there are meaningful tags to match on
            tag_filter = {k: v for k, v in wi_tags.items() if k in ("feature", "bug") and v}
            if not tag_filter and not name:
                return None
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_DEDUP_TAG_CHECK,
                        (project_id, category, json.dumps(tag_filter), name),
                    )
                    row = cur.fetchone()
            if row:
                existing_id = str(row[0])
                log.debug(f"_dedup_tier1: merged '{name}' into existing '{row[1]}' ({existing_id[:8]})")
                self._mark_dedup(existing_id, project_id, "merged")
                return existing_id
        except Exception as e:
            log.debug(f"_dedup_tier1 error: {e}")
        return None

    def _mark_dedup(self, wi_id: str, project_id: int, status: str) -> None:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mem_ai_work_items SET dedup_status=%s, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (status, wi_id, project_id),
                    )
        except Exception as e:
            log.debug(f"_mark_dedup error: {e}")

    def _set_tag_id_ai(self, wi_id: str, tag_id: str) -> None:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mem_ai_work_items SET tag_id_ai=%s::uuid, updated_at=NOW() "
                        "WHERE id=%s::uuid",
                        (tag_id, wi_id),
                    )
        except Exception as e:
            log.debug(f"_set_tag_id_ai error: {e}")

    async def _run_quality_gate_async(self, project_id: int, wi_id: str) -> None:
        """Async wrapper so quality gate can be fire-and-forget from event loop."""
        try:
            await self.run_quality_gate(project_id, wi_id)
        except Exception as e:
            log.debug(f"_run_quality_gate_async error ({wi_id[:8]}): {e}")

    async def run_quality_gate(self, project_id: int, wi_id: str) -> str:
        """Apply quality checks to a single work item. Returns final quality_stage."""
        _GENERIC_NAMES = frozenset({
            'fix', 'bug', 'feature', 'task', 'update', 'add', 'change', 'improve',
            'refactor', 'test', 'review', 'cleanup', 'remove', 'delete',
        })
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name_ai, dedup_status FROM mem_ai_work_items "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (wi_id, project_id),
                    )
                    row = cur.fetchone()
            if not row:
                return "staging"
            name, dedup_status = row[0], row[1]

            # Count linked events
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_COUNT_LINKED_EVENTS, (wi_id, project_id))
                    event_count = cur.fetchone()[0] or 0

            issues: dict = {}
            stage = "approved"

            # Name specificity check
            name_lower = name.lower().strip()
            first_word = name_lower.split("-")[0] if "-" in name_lower else name_lower
            if len(name) < 8 or name_lower in _GENERIC_NAMES or first_word in _GENERIC_NAMES:
                issues["scope"] = f"Name too generic: '{name}'"
                stage = "rejected"

            # Evidence: at least 2 linked events required
            if event_count < 2:
                issues["evidence"] = f"Only {event_count} linked event(s) — need ≥ 2"
                if stage != "rejected":
                    stage = "staging"

            # Dedup flag carries over
            if dedup_status == "flagged":
                if stage != "rejected":
                    stage = "staging"
                issues["coverage"] = "Potential duplicate — similarity > 0.88"

            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_UPDATE_QUALITY_GATE,
                        (stage, json.dumps(issues), dedup_status, wi_id, project_id),
                    )
            return stage
        except Exception as e:
            log.debug(f"run_quality_gate error ({wi_id[:8]}): {e}")
            return "staging"

    async def dedup_work_items(self, project: str) -> dict:
        """Merge duplicate work items that share the same feature or bug tag.

        For each tag value (e.g. feature='work_items') that has multiple work items:
          1. Pick the canonical item (prefer one with tag_id_user, then most linked events,
             then oldest).
          2. Rename canonical to use the tag value as name_ai (so future inserts via
             UNIQUE (project_id, category_ai, name_ai) hit it directly).
          3. Append action_items_ai from duplicates into the canonical.
          4. Re-point all mem_ai_events.work_item_id from duplicates → canonical.
          5. Delete duplicates.

        Returns {"merged_groups": N, "deleted": M, "canonical_renamed": K}.
        """
        if not db.is_available():
            return {"merged_groups": 0, "deleted": 0, "canonical_renamed": 0}

        project_id = db.get_or_create_project_id(project)
        merged_groups = deleted = canonical_renamed = 0

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_WI_GROUPS_BY_FEATURE, (project_id,))
                feature_groups = cur.fetchall()
                cur.execute(_SQL_WI_GROUPS_BY_BUG, (project_id,))
                bug_groups = cur.fetchall()

        all_groups = [(tv, tk, ids) for tv, tk, ids in feature_groups + bug_groups
                      if tv and ids and len(ids) > 1]

        for tag_val, tag_key, ids in all_groups:
            canonical_id = ids[0]
            dup_ids = ids[1:]
            canonical_name = tag_val.lower().strip()[:200]
            category = "bug" if tag_key == "bug" else "feature"

            # Collect content from all duplicates
            combined_actions: list[str] = []
            for dup_id in dup_ids:
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "SELECT action_items_ai FROM mem_ai_work_items WHERE id=%s::uuid",
                                (dup_id,),
                            )
                            row = cur.fetchone()
                            if row and row[0] and row[0].strip():
                                combined_actions.append(row[0].strip())

                            # Re-link events to canonical
                            cur.execute(
                                "UPDATE mem_ai_events SET work_item_id=%s::uuid "
                                "WHERE work_item_id=%s::uuid AND project_id=%s",
                                (canonical_id, dup_id, project_id),
                            )
                            # Delete duplicate
                            cur.execute(
                                "DELETE FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s",
                                (dup_id, project_id),
                            )
                            deleted += 1
                except Exception as e:
                    log.debug(f"dedup_work_items dup merge error ({dup_id}): {e}")

            # Merge collected action_items into canonical and rename to tag value
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        # Check if canonical_name conflicts with another existing item
                        cur.execute(
                            "SELECT id FROM mem_ai_work_items "
                            "WHERE project_id=%s AND category_ai=%s AND name_ai=%s "
                            "AND id != %s::uuid LIMIT 1",
                            (project_id, category, canonical_name, canonical_id),
                        )
                        conflict = cur.fetchone()
                        if conflict:
                            # There's already an item with the canonical name — merge into that one
                            target_id = str(conflict[0])
                            cur.execute(
                                "UPDATE mem_ai_events SET work_item_id=%s::uuid "
                                "WHERE work_item_id=%s::uuid AND project_id=%s",
                                (target_id, canonical_id, project_id),
                            )
                            cur.execute(
                                "DELETE FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s",
                                (canonical_id, project_id),
                            )
                            deleted += 1
                            canonical_id = target_id  # target is now the real canonical

                        append_text = "\n---\n".join(combined_actions)
                        cur.execute(
                            """UPDATE mem_ai_work_items SET
                                name_ai         = %s,
                                category_ai     = %s,
                                action_items_ai = CASE
                                    WHEN %s = '' THEN action_items_ai
                                    WHEN action_items_ai = '' OR action_items_ai IS NULL THEN %s
                                    ELSE action_items_ai || E'\n---\n' || %s
                                END,
                                updated_at      = NOW()
                               WHERE id = %s::uuid AND project_id = %s""",
                            (canonical_name, category,
                             append_text, append_text, append_text,
                             canonical_id, project_id),
                        )
                        canonical_renamed += 1
            except Exception as e:
                log.debug(f"dedup_work_items canonical update error ({canonical_id}): {e}")

            merged_groups += 1

        log.info(
            f"dedup_work_items: merged_groups={merged_groups} deleted={deleted} "
            f"renamed={canonical_renamed} for '{project}'"
        )
        return {
            "merged_groups": merged_groups,
            "deleted": deleted,
            "canonical_renamed": canonical_renamed,
        }
