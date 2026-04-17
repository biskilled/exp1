"""
memory_promotion.py — Project fact conflict detection and resolution.

The only responsibility of this module is to detect when a newly-reported
project fact contradicts an existing fact for the same key, and to call an
LLM to decide how to resolve the conflict (supersede / merge / flag).

Work-item extraction, feature snapshots, and work-item promotion have been
moved to dedicated routers and background tasks.
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

_SQL_GET_CURRENT_FACTS = """
    SELECT id, fact_key, fact_value, created_at
    FROM mem_ai_project_facts
    WHERE project_id=%s AND valid_until IS NULL
    ORDER BY fact_key
"""

_SQL_MARK_FACT_CONFLICT = """
    UPDATE mem_ai_project_facts
    SET conflict_status=%s
    WHERE project_id=%s AND fact_key=%s AND valid_until IS NULL
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
        model = settings.claude_haiku_model if hasattr(settings, "claude_haiku_model") else "claude-haiku-4-5-20251001"
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=model, max_tokens=max_tokens, system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        _log_usage(model, getattr(resp.usage, "input_tokens", 0), getattr(resp.usage, "output_tokens", 0))
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_llm error: {e}")
        return ""


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    try:
        from core.auth import ADMIN_USER_ID
        from agents.providers.pr_pricing import calculate_cost
        cost = calculate_cost("claude", model, input_tokens, output_tokens, markup_pct=0)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_usage_logs
                       (user_id, provider, model, input_tokens, output_tokens, cost_usd, charged_usd, source)
                       VALUES (%s, 'claude', %s, %s, %s, %s, 0, 'memory')""",
                    (ADMIN_USER_ID, model, input_tokens, output_tokens, cost),
                )
    except Exception as _e:
        log.debug(f"memory_promotion._log_usage: {_e}")


# ── MemoryPromotion ───────────────────────────────────────────────────────────

class MemoryPromotion:
    """
    Detects and resolves conflicts between new and existing project facts.
    """

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
