"""_wi_helpers.py — Shared module-level constants and helpers for work item modules.

Imported by memory_work_items.py, _wi_classify.py, and _wi_markdown.py.
No class-level dependencies — pure functions and constants only.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ── Prompt path ────────────────────────────────────────────────────────────────
_WI_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "command_work_items.yaml"

# ── Table map ──────────────────────────────────────────────────────────────────
_TABLE: dict[str, str] = {
    "prompts":  "mem_mrr_prompts",
    "commits":  "mem_mrr_commits",
    "messages": "mem_mrr_messages",
    "items":    "mem_mrr_items",
}

# ── Type → (seq_key, display_prefix) ──────────────────────────────────────────
_TYPE_SEQ: dict[str, tuple[str, str]] = {
    "use_case":    ("WI_US", "US"),
    "feature":     ("WI_FE", "FE"),
    "bug":         ("WI_BU", "BU"),
    "task":        ("WI_TA", "TA"),
    "policy":      ("WI_PO", "PO"),
    "requirement": ("WI_RE", "RE"),
}
_DEFAULT_SEQ = ("WI_TA", "TA")
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)

# Only these keys are user-intent tags — everything else is system metadata
_USER_TAG_KEYS = {"phase", "feature", "bug", "work-item"}


def _use_case_slug(name: str) -> str:
    """Convert a use case name to a URL-safe slug for MD filenames."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:60]


def _claude_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("claude") or get_key("anthropic") or None
    except Exception:
        return None


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    try:
        from core.auth import ADMIN_USER_ID
        from core.database import db
        _RATES = {
            "claude-haiku-4-5-20251001": (0.00025, 0.00125),
            "claude-haiku-4-5":          (0.00025, 0.00125),
        }
        in_r, out_r = _RATES.get(model, (0.00025, 0.00125))
        cost = (input_tokens * in_r + output_tokens * out_r) / 1000.0
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_usage_logs
                       (user_id, provider, model, input_tokens, output_tokens,
                        cost_usd, charged_usd, source)
                       VALUES (%s, 'claude', %s, %s, %s, %s, 0, 'memory')""",
                    (ADMIN_USER_ID, model, input_tokens, output_tokens, cost),
                )
    except Exception as _e:
        log.debug(f"_log_usage error: {_e}")


async def _call_haiku(system: str, user: str, model: str = "claude-haiku-4-5-20251001",
                      max_tokens: int = 4000) -> str:
    """Call Claude Haiku and return raw text. Returns '' on failure."""
    key = _claude_key()
    if not key:
        log.warning("_call_haiku: no Claude API key found")
        return ""
    try:
        import anthropic
        async with anthropic.AsyncAnthropic(api_key=key) as client:
            resp = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        if hasattr(resp, "usage"):
            _log_usage(
                model,
                getattr(resp.usage, "input_tokens", 0),
                getattr(resp.usage, "output_tokens", 0),
            )
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.warning(f"_call_haiku error: {e}")
        return ""


def _get_code_dir(project: str) -> Optional[Path]:
    try:
        from pipelines.pipeline_git import get_project_code_dir
        cd = get_project_code_dir(project)
        return Path(cd) if cd else None
    except Exception:
        return None


def _count_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (closer to Claude's actual tokenizer)."""
    return max(1, len(text) // 4)


def _generate_wi_id(cur, project_id: int, wi_type: str) -> str:
    """Allocate the next seq_counter value and return a formatted ID like BU0003."""
    from data.dl_seq import next_seq
    seq_key, prefix = _TYPE_SEQ.get(wi_type, _DEFAULT_SEQ)
    val = next_seq(cur, project_id, seq_key)
    return f"{prefix}{val:04d}"


def _insert_wi(cur, item: dict, pid: int, parent_id: Optional[str]) -> str:
    """Insert a single work item row with a temp AI-prefixed wi_id. Returns new UUID string."""
    from data.dl_seq import next_seq
    temp_val = next_seq(cur, pid, "WI_AI")
    temp_wi_id = f"AI{temp_val:04d}"
    score_imp = min(5, max(0, int(item.get("score_importance", 0))))
    score_st  = min(5, max(0, int(item.get("score_status", 0))))
    cur.execute(
        """INSERT INTO mem_work_items
           (client_id, project_id, wi_type, item_level, name, summary,
            deliveries, delivery_type, score_importance, score_status,
            user_importance, user_status,
            mrr_ids, wi_parent_id, wi_id)
           VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::uuid, %s)
           RETURNING id::text""",
        (
            pid,
            item.get("wi_type", "task"),
            item.get("item_level", 2),
            (item.get("name") or "")[:200],
            item.get("summary") or "",
            item.get("deliveries") or "",
            item.get("delivery_type") or "",
            score_imp,
            score_st,
            score_imp,
            "open",
            json.dumps(item.get("mrr_ids") or {}),
            parent_id if parent_id else None,
            temp_wi_id,
        ),
    )
    row = cur.fetchone()
    return row[0] if row else ""


def _merge_tags(existing: dict, incoming: dict) -> dict:
    """Merge two tag dicts — for each key keep all values as a set if multiple."""
    result = dict(existing)
    for k, v in incoming.items():
        if not v:
            continue
        if k not in result:
            result[k] = v
        elif result[k] != v:
            existing_vals = set(str(result[k]).split(","))
            existing_vals.add(str(v))
            result[k] = ",".join(sorted(existing_vals))
    return result


def _update_item_tags(saved_items: list[dict], tag_lookup: dict[str, dict]) -> None:
    """Populate mem_work_items.tags by merging tags from all referenced events."""
    from core.database import db
    if not db.is_available() or not saved_items:
        return
    try:
        # Build all (tags_json, item_id) pairs in Python, then batch-update
        updates: list[tuple[str, str]] = []
        for item in saved_items:
            item_id = item.get("id")
            if not item_id:
                continue
            mrr = item.get("mrr_ids") or {}
            merged: dict = {}
            for ref_list in mrr.values():
                for ref_id in (ref_list or []):
                    raw_tags = tag_lookup.get(ref_id) or {}
                    user_tags = {k: v for k, v in raw_tags.items() if k in _USER_TAG_KEYS}
                    merged = _merge_tags(merged, user_tags)
            if merged:
                updates.append((json.dumps(merged), item_id))
        if not updates:
            return
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE mem_work_items SET tags=%s WHERE id=%s::uuid",
                    updates,
                )
            conn.commit()
    except Exception as e:
        log.debug(f"_update_item_tags error: {e}")


def _rollup_uc_tags(pid: int, uc_ids: list[str]) -> None:
    """Aggregate all children tags up into each use case row."""
    from core.database import db
    if not db.is_available() or not uc_ids:
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                for uc_id in uc_ids:
                    cur.execute(
                        """SELECT tags FROM mem_work_items
                           WHERE project_id=%s AND wi_parent_id=%s::uuid""",
                        (pid, uc_id),
                    )
                    merged: dict = {}
                    for (child_tags,) in cur.fetchall():
                        merged = _merge_tags(merged, child_tags or {})
                    if merged:
                        cur.execute(
                            """UPDATE mem_work_items
                               SET tags = tags || %s::jsonb
                               WHERE id=%s::uuid""",
                            (json.dumps(merged), uc_id),
                        )
            conn.commit()
    except Exception as e:
        log.debug(f"_rollup_uc_tags error: {e}")


def _embed_work_item(item_id: str, fields: dict) -> None:
    """Compute embedding for an approved work item and store in DB.

    Embeds: name + wi_type + summary + deliveries + delivery_type
            + acceptance_criteria + implementation_plan (truncated to 500 chars each)
    so AC/plan text is findable via semantic search.
    """
    from core.database import db
    try:
        text = " | ".join(filter(None, [
            fields.get("name", ""),
            fields.get("wi_type", ""),
            fields.get("summary", ""),
            fields.get("deliveries", ""),
            fields.get("delivery_type", ""),
            fields.get("acceptance_criteria", ""),
            fields.get("implementation_plan", ""),
        ]))
        if not text.strip():
            return
        from agents.tools.tool_memory import _embed_sync
        vector = _embed_sync(text)
        if not vector:
            return
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE mem_work_items SET embedding=%s WHERE id=%s::uuid",
                    (vector, item_id),
                )
            conn.commit()
    except Exception as e:
        log.warning(f"_embed_work_item({item_id}) failed — semantic search will return stale results: {e}")
