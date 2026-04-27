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

_SQL_GET_FACT_BY_KEY = """
    SELECT fact_value FROM mem_ai_project_facts
    WHERE project_id=%s AND fact_key=%s AND valid_until IS NULL
    LIMIT 1
"""

_SQL_MARK_FACT_CONFLICT = """
    UPDATE mem_ai_project_facts
    SET conflict_status=%s
    WHERE project_id=%s AND fact_key=%s AND valid_until IS NULL
"""

_SQL_EXPIRE_BY_KEY = """
    UPDATE mem_ai_project_facts SET valid_until=NOW()
    WHERE project_id=%s AND fact_key=%s AND valid_until IS NULL
"""

_SQL_EXPIRE_STALE = """
    UPDATE mem_ai_project_facts SET valid_until=NOW()
    WHERE project_id=%s AND valid_until IS NULL AND category <> 'code'
    AND fact_key <> ALL(%s::text[])
"""

_SQL_INSERT_FACT = """
    INSERT INTO mem_ai_project_facts
        (project_id, fact_key, fact_value, category, embedding, conflict_status)
    VALUES (%s, %s, %s, %s, %s, %s)
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
                            (action, project_id, fact_key),  # use int project_id, not name
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

    async def save_fact(
        self,
        project_id: int,
        fact_key: str,
        fact_value: str,
        category: str = "general",
    ) -> str:
        """Upsert one project fact with conflict detection.

        Returns: 'inserted' | 'unchanged' | 'superseded' | 'merged' | 'flagged'
        """
        # Load existing fact for this key
        existing_value: Optional[str] = None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_FACT_BY_KEY, (project_id, fact_key))
                row = cur.fetchone()
        if row:
            existing_value = row[0]

        # Same value → nothing to do
        if existing_value is not None and existing_value.strip().lower() == fact_value.strip().lower():
            return "unchanged"

        # Resolve conflicts when key already exists with a different value
        action = "insert"
        embed_value = fact_value
        conflict_status: Optional[str] = None

        if existing_value is not None:
            resolution = await self._resolve_conflict(fact_key, existing_value, fact_value)
            action = resolution.get("resolution", "supersede") if resolution else "supersede"
            if action == "merge" and resolution and resolution.get("merged_value"):
                embed_value = resolution["merged_value"]
            conflict_status = "pending_review" if action == "flag" else None

        # Embed the (possibly merged) value
        vec_param: Optional[str] = None
        try:
            from agents.tools.tool_memory import _embed_sync, _vec_str as _vs
            emb = _embed_sync(f"{fact_key}: {embed_value}")
            if emb:
                vec_param = f"[{','.join(str(x) for x in emb)}]"
        except Exception:
            pass

        with db.conn() as conn:
            with conn.cursor() as cur:
                if existing_value is not None:
                    if action == "flag":
                        # Mark old fact as flagged but keep it; insert new alongside
                        cur.execute(_SQL_MARK_FACT_CONFLICT, ("pending_review", project_id, fact_key))
                    else:
                        # Supersede or merge: expire the old fact
                        cur.execute(_SQL_EXPIRE_BY_KEY, (project_id, fact_key))
                cur.execute(
                    _SQL_INSERT_FACT,
                    (project_id, fact_key, embed_value, category, vec_param, conflict_status),
                )

        return "inserted" if action == "insert" else action

    async def auto_populate_from_synthesis(
        self,
        project_name: str,
        project_id: int,
        project_md: str,
        synthesis: Optional[dict],
    ) -> int:
        """Extract stable facts from PROJECT.md + synthesis, save each with conflict detection.

        Replaces _auto_populate_project_facts() in route_projects.py.
        Returns count of facts changed (inserted or updated).
        """
        import re as _re

        # Build LLM input
        text_for_llm = ""
        if project_md:
            text_for_llm += project_md[:3000]
        if synthesis:
            if synthesis.get("tech_stack"):
                text_for_llm += "\n\n## Tech Stack (from synthesis)\n"
                for k, v in synthesis["tech_stack"].items():
                    text_for_llm += f"- {k}: {v}\n"
            if synthesis.get("key_decisions"):
                text_for_llm += "\n## Key Decisions (from synthesis)\n"
                for d in synthesis["key_decisions"]:
                    text_for_llm += f"- {d}\n"
        if not text_for_llm.strip():
            return 0

        # Call LLM to extract facts
        system_prompt = _prompts.content("fact_extraction") or (
            "You extract stable project facts as JSON. "
            "Respond ONLY with a JSON array of objects with keys: "
            "fact_key (snake_case), fact_value (concise string), "
            "category (stack|pattern|convention|constraint|general). "
            "No explanation, no markdown."
        )
        raw = await _call_llm(
            system_prompt,
            f"Extract stable project facts from this context:\n\n{text_for_llm[:3000]}",
            max_tokens=400,
        )
        if not raw:
            return 0

        m = _re.search(r"\[.*\]", raw, _re.DOTALL)
        if not m:
            return 0
        try:
            facts = json.loads(m.group())
        except Exception:
            return 0
        if not isinstance(facts, list):
            return 0

        # Normalise keys + deduplicate
        def _norm_key(k: str) -> str:
            k = k.lower().strip()
            k = _re.sub(r"[^a-z0-9]+", "_", k)
            return k[:80].strip("_")

        valid_cats = {"stack", "pattern", "convention", "constraint", "general"}
        seen: set[str] = set()
        cleaned: list[dict] = []
        for f in facts:
            if not isinstance(f, dict) or not f.get("fact_key") or not f.get("fact_value"):
                continue
            nk = _norm_key(str(f["fact_key"]))
            if not nk or nk in seen:
                continue
            seen.add(nk)
            cat = f.get("category", "general")
            if cat not in valid_cats:
                cat = "general"
            cleaned.append({"fact_key": nk, "fact_value": str(f["fact_value"])[:500], "category": cat})
            if len(cleaned) >= 12:
                break

        if not cleaned:
            return 0

        # Save each fact (with conflict detection per key)
        count = 0
        for f in cleaned:
            try:
                action = await self.save_fact(project_id, f["fact_key"], f["fact_value"], f["category"])
                if action != "unchanged":
                    count += 1
            except Exception as e:
                log.debug(f"auto_populate: save_fact failed for '{f['fact_key']}': {e}")

        # Expire facts whose keys are no longer in the new extraction (stale)
        new_keys = [f["fact_key"] for f in cleaned]
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_EXPIRE_STALE, (project_id, new_keys))
        except Exception as e:
            log.debug(f"auto_populate: expire_stale failed: {e}")

        log.info("auto_populate_from_synthesis: %d facts changed for project_id=%d", count, project_id)
        return count

    async def _resolve_conflict(
        self, fact_key: str, old_value: str, new_value: str
    ) -> Optional[dict]:
        system_prompt = _prompts.content("conflict_detection") or ""
        user_msg = (
            f"Fact key: {fact_key}\n"
            f"Old value: {old_value}\n"
            f"New value: {new_value}"
        )
        raw = await _call_llm(system_prompt, user_msg, max_tokens=300)
        if not raw:
            return None
        return _parse_json(raw) or None
