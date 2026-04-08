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

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_TAG_ID = """
    SELECT id FROM planner_tags
    WHERE project_id=%s AND name=%s
    LIMIT 1
"""

_SQL_GET_WORK_ITEM = """
    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria
    FROM mem_ai_work_items wi
    WHERE wi.project_id=%s
    ORDER BY wi.created_at DESC LIMIT 10
"""

_SQL_GET_WORK_ITEM_BY_NAME = """
    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria,
           wi.action_items, wi.status_ai, wi.tag_id
    FROM mem_ai_work_items wi
    WHERE wi.project_id=%s AND wi.ai_name=%s
    LIMIT 1
"""

_SQL_UPDATE_WORK_ITEM_STATUS_AI = """
    UPDATE mem_ai_work_items SET status_ai=%s, updated_at=NOW()
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
        summary      = %s,
        action_items = %s,
        design       = %s,
        code_summary = %s,
        embedding    = %s,
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

# Find events not yet used as source for any work item extraction
_SQL_GET_UNEXTRACTED_EVENTS = """
    SELECT me.id, me.event_type, me.session_id, me.summary, me.action_items,
           me.created_at, me.tags
    FROM mem_ai_events me
    WHERE me.project_id=%s
      AND me.event_type IN ('prompt_batch', 'session_summary')
      AND me.summary IS NOT NULL AND me.summary != ''
      AND NOT EXISTS (
          SELECT 1 FROM mem_ai_work_items wi
          WHERE wi.project_id=me.project_id
            AND wi.source_event_id = me.id
      )
    ORDER BY me.created_at DESC
    LIMIT %s
"""

_SQL_INSERT_EXTRACTED_WORK_ITEM = """
    INSERT INTO mem_ai_work_items
        (project_id, ai_category, ai_name, ai_desc,
         source_event_id, seq_num)
    VALUES (%s, %s, %s, %s, %s::uuid,
            (SELECT COALESCE(MAX(seq_num),0)+1 FROM mem_ai_work_items WHERE project_id=%s))
    ON CONFLICT (project_id, ai_category, ai_name) DO UPDATE SET
        ai_desc    = EXCLUDED.ai_desc,
        updated_at = NOW()
    RETURNING id
"""


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


# ── MemoryPromotion ───────────────────────────────────────────────────────────

class MemoryPromotion:
    """
    Promotes raw memory events into structured artifacts:
      - Work item summaries (work_item_promotion)
      - 4-layer feature snapshots (feature_snapshot)
      - Project fact conflict detection (conflict_detection)
    """

    async def promote_work_item(
        self, project: str, tag_name: str
    ) -> Optional[dict]:
        """
        Summarise the work item associated with tag_name into a 2-4 sentence digest.
        Returns {summary, status} or None on failure.
        """
        if not db.is_available():
            return None

        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORK_ITEM_BY_NAME, (project_id, tag_name))
                row = cur.fetchone()

        if not row:
            log.debug(f"promote_work_item: no work item found for '{tag_name}'")
            return None

        wi_id, wi_name, desc, status_user, ac, action_items, status_ai, tag_id = row

        system_prompt = _prompts.content("work_item_promotion") or (
            "Given a work item, produce a 2-4 sentence summary capturing what it is, "
            "current status, and any notable progress. "
            "Return JSON only: {\"summary\": \"...\", \"status_ai\": \"active|in_progress|done\"}"
        )

        user_msg = (
            f"Work Item: {wi_name}\n"
            f"User Status: {status_user}\n"
            f"Description: {desc or '(none)'}\n"
            f"Acceptance Criteria:\n{ac or '(none)'}\n"
            f"Action Items:\n{action_items or '(none)'}"
        )

        raw = await _call_llm(system_prompt, user_msg, max_tokens=300)
        parsed = _parse_json(raw)
        if not parsed:
            log.debug(f"promote_work_item: LLM returned no JSON for '{tag_name}'")
            return None

        new_status_ai = parsed.get("status_ai", status_ai)
        # Persist AI status suggestion back to DB
        if new_status_ai != status_ai:
            project_id = db.get_or_create_project_id(tag_name)  # re-resolve not needed below
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(_SQL_UPDATE_WORK_ITEM_STATUS_AI,
                                    (new_status_ai, str(wi_id), project_id))
            except Exception as e:
                log.debug(f"promote_work_item: status_ai update failed: {e}")

        return {
            "work_item_id": str(wi_id),
            "tag_name": tag_name,
            "summary": parsed.get("summary", ""),
            "status_ai": new_status_ai,
        }

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
        design = parsed.get("design", {})
        code_summary = parsed.get("code_summary", {})
        requirements = parsed.get("requirements", "")
        action_items = parsed.get("action_items", "")

        embed_text = " ".join(filter(None, [requirements, action_items]))
        embedding = await _embed_text(embed_text) if embed_text.strip() else None

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPDATE_TAG_SNAPSHOT,
                    (
                        requirements,
                        action_items,
                        json.dumps(design),
                        json.dumps(code_summary),
                        embedding,
                        tag_id,
                        project_id,
                    ),
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
            "summary":            requirements,
            "action_items":       action_items,
            "design":             design,
            "code_summary":       code_summary,
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
        """
        Scan recent unprocessed events (prompt_batch + session_summary) and use
        Haiku to identify actionable work items (tasks, bugs, features).

        Each extracted item is stored in mem_ai_work_items with source_event_id
        and source_session_id set so it's not re-extracted on the next run.

        Returns count of work items created.
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

        system_prompt = _prompts.content("work_item_extraction") or (
            "You are a project memory analyst. Given a digest of recent development activity, "
            "identify actionable work items: bugs to fix, features to build, tasks to complete. "
            "Return JSON only:\n"
            "{\"items\": [\n"
            "  {\"category\": \"bug|feature|task\", \"name\": \"short-slug\", "
            "\"description\": \"1-2 sentence explanation\"}\n"
            "]}\n"
            "Return at most 5 items. Use lowercase-hyphenated slugs for name. "
            "Return {\"items\": []} if nothing actionable is found."
        )

        created = 0
        for ev_id, event_type, session_id, summary, action_items, created_at, tags in events:
            content_parts = [p for p in [summary, action_items] if p and p.strip()]
            content = "\n\n".join(content_parts)[:3000]
            if not content.strip():
                continue

            event_label = "session summary" if event_type == "session_summary" else "prompt batch"
            user_msg = f"Event type: {event_label}\nDate: {str(created_at)[:10]}\n\n{content}"

            raw = await _call_llm(system_prompt, user_msg, max_tokens=500)
            if not raw:
                continue

            parsed = _parse_json(raw)
            items = parsed.get("items", []) if parsed else []
            if not items:
                continue

            for item in items[:5]:
                category = item.get("category", "task")
                name = (item.get("name") or "").strip().lower()[:200]
                description = (item.get("description") or "").strip()[:1000]
                if not name or not description:
                    continue
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                _SQL_INSERT_EXTRACTED_WORK_ITEM,
                                (project_id, category, name, description,
                                 str(ev_id), project_id),
                            )
                            if cur.fetchone():
                                created += 1
                except Exception as e:
                    log.debug(f"extract_work_items insert error: {e}")

        log.info(f"extract_work_items_from_events: created {created} items for '{project}'")
        return created
