"""
memory_work_items.py — DB-first work item classification pipeline.

Replaces the file-based backlog pipeline (memory_backlog.py + backlog.md +
use_cases/*.md) with a single DB table (mem_work_items) as the source of truth.

Public API::

    wi = MemoryWorkItems(project)

    # classify all pending mirror rows into mem_work_items
    result = await wi.classify()
    # {"classified": N, "items": [...]}

    # CRUD
    items   = wi.get_pending(pid)
    all_    = wi.get_all(pid, wi_type="bug")
    stats   = wi.get_stats(pid)

    # Approval workflow
    item = wi.approve(item_id, pid)   # assigns BU0001 / FE0002 etc.
    item = wi.reject(item_id, pid)    # assigns REJxxxxx
    item = wi.update(item_id, pid, fields)
    wi.delete(item_id, pid)
    wi.move_event(item_id, pid, mrr_type, mrr_id, target_id)
    wi.approve_all_under(parent_id, pid)

    # Threshold-based trigger (keeps route_git/route_chat working)
    await wi.check_and_trigger(source_type)
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from core.config import settings
from core.database import db

log = logging.getLogger(__name__)

# ── Prompt path ───────────────────────────────────────────────────────────────
_WI_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "work_items.yaml"

# ── Table map ─────────────────────────────────────────────────────────────────
_TABLE: dict[str, str] = {
    "prompts":  "mem_mrr_prompts",
    "commits":  "mem_mrr_commits",
    "messages": "mem_mrr_messages",
    "items":    "mem_mrr_items",
}

# ── Type → (seq_key, display_prefix) ─────────────────────────────────────────
_TYPE_SEQ: dict[str, tuple[str, str]] = {
    "use_case": ("WI_US", "US"),
    "feature":  ("WI_FE", "FE"),
    "bug":      ("WI_BU", "BU"),
    "task":     ("WI_TA", "TA"),
    "policy":   ("WI_PO", "PO"),
}
_DEFAULT_SEQ = ("WI_TA", "TA")
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────────

def _claude_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("claude") or get_key("anthropic") or None
    except Exception:
        return None


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    try:
        from core.auth import ADMIN_USER_ID
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
        return ""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
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
        log.debug(f"_call_haiku error: {e}")
        return ""


def _get_code_dir(project: str) -> Optional[Path]:
    try:
        from pipelines.pipeline_git import get_project_code_dir
        cd = get_project_code_dir(project)
        return Path(cd) if cd else None
    except Exception:
        return None


def _count_tokens(text: str) -> int:
    """Rough token estimate: word count × 1.3."""
    return int(len(text.split()) * 1.3)


def _generate_wi_id(cur, project_id: int, wi_type: str) -> str:
    """Allocate the next seq_counter value and return a formatted ID like BU0003."""
    from data.dl_seq import next_seq
    seq_key, prefix = _TYPE_SEQ.get(wi_type, _DEFAULT_SEQ)
    val = next_seq(cur, project_id, seq_key)
    return f"{prefix}{val:04d}"


def _upsert_planner_tag(
    project: str,
    project_id: int,
    name: str,
    wi_type: str,
    description: str = "",
    parent_id: Optional[str] = None,
) -> Optional[tuple[str, int]]:
    """Find or create a planner_tag for this work item.

    Maps wi_type → mng_tags_categories.name (reuses existing mapping).
    Returns (tag_id: str, seq_num: int) or None on failure.
    """
    if not db.is_available():
        return None

    # wi_type → category name
    cat_name_map = {
        "use_case": "use_case",
        "feature":  "feature",
        "bug":      "bug",
        "task":     "task",
        "policy":   "policy",
    }
    # planner seq category (reuse existing uc/feat/bug ranges from m055)
    seq_cat_map = {
        "use_case": "uc",
        "feature":  "feat",
        "bug":      "bug",
        "task":     "feat",   # tasks fall into feature range
        "policy":   "feat",
    }
    cat_name = cat_name_map.get(wi_type, "use_case")
    seq_cat  = seq_cat_map.get(wi_type, "feat")

    try:
        from data.dl_seq import next_seq
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM mng_tags_categories WHERE client_id=1 AND name=%s",
                    (cat_name,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                cat_id = row[0]

                # Check existing
                cur.execute(
                    "SELECT id::text, seq_num FROM planner_tags "
                    "WHERE project_id=%s AND name=%s AND category_id=%s",
                    (project_id, name, cat_id),
                )
                existing = cur.fetchone()
                if existing:
                    tag_id, seq_num = existing
                    return (tag_id, seq_num)

                seq_num = next_seq(cur, project_id, seq_cat)
                cur.execute(
                    """INSERT INTO planner_tags
                       (project_id, name, category_id, description, status,
                        creator, seq_num, parent_id)
                       VALUES (%s, %s, %s, %s, 'open', 'ai', %s, %s::uuid)
                       ON CONFLICT (project_id, name, category_id) DO UPDATE SET
                           seq_num   = COALESCE(planner_tags.seq_num, EXCLUDED.seq_num),
                           parent_id = COALESCE(planner_tags.parent_id, EXCLUDED.parent_id),
                           updated_at = NOW()
                       RETURNING id::text, seq_num""",
                    (project_id, name, cat_id, description or name, seq_num,
                     parent_id if parent_id else None),
                )
                result = cur.fetchone()
                conn.commit()
                if result:
                    return (result[0], result[1])
    except Exception as e:
        log.warning(f"_upsert_planner_tag({name!r}, {wi_type}) error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main class
# ─────────────────────────────────────────────────────────────────────────────

class MemoryWorkItems:
    """DB-first work item classification pipeline.

    Replaces the file-based backlog pipeline (backlog.md + use_cases/*.md)
    with mem_work_items as the single source of truth for all classified work.
    """

    def __init__(self, project: str) -> None:
        self.project   = project
        self.project_id: Optional[int] = None
        self._cfg: Optional[dict] = None
        self._prompts: Optional[dict] = None

    # ── Config ─────────────────────────────────────────────────────────────────

    def _config(self) -> dict:
        """Load project.yaml work_items section."""
        if self._cfg is not None:
            return self._cfg
        self._cfg = {}
        try:
            from pipelines.pipeline_git import get_project_code_dir
            code_dir_str = get_project_code_dir(self.project)
            if code_dir_str:
                project_yaml = Path(code_dir_str) / "project.yaml"
            else:
                project_yaml = Path(settings.workspace_dir) / self.project / "project.yaml"
            if project_yaml.exists():
                data = yaml.safe_load(project_yaml.read_text()) or {}
                self._cfg = data.get("work_items", {})
        except Exception as e:
            log.debug(f"work_items config load error: {e}")
        return self._cfg

    def _prompts_cfg(self) -> dict:
        """Load backend/prompts/work_items.yaml."""
        if self._prompts is not None:
            return self._prompts
        self._prompts = {}
        if _WI_PROMPTS_PATH.exists():
            try:
                self._prompts = yaml.safe_load(_WI_PROMPTS_PATH.read_text()) or {}
            except Exception as e:
                log.debug(f"work_items.yaml load error: {e}")
        return self._prompts

    def _get_project_id(self) -> Optional[int]:
        if self.project_id:
            return self.project_id
        if not db.is_available():
            return None
        try:
            self.project_id = db.get_or_create_project_id(self.project)
            return self.project_id
        except Exception:
            return None

    def _mode(self) -> str:
        return self._config().get("classification", {}).get("mode", "manual")

    def _threshold(self, source_type: str) -> int:
        thresholds = self._config().get("classification", {}).get("thresholds", {})
        defaults = {"prompts": 2000, "commits": 1000, "messages": 5000, "items": 500}
        return int(thresholds.get(source_type, defaults.get(source_type, 9999)))

    # ── Threshold trigger (backward-compat with route_git / route_chat) ────────

    async def check_and_trigger(self, source_type: str) -> None:
        """Trigger auto-classification if mode=threshold and token count is met.

        In mode=manual (default) this is a no-op — classification is only
        triggered explicitly via POST /memory/{project}/wi/classify.
        """
        if self._mode() != "threshold":
            return
        pid = self._get_project_id()
        if not pid:
            return
        count = self._pending_count(pid, source_type)
        threshold = self._threshold(source_type)
        if count >= threshold:
            log.info(
                f"wi: {count} pending {source_type} >= threshold {threshold}, classifying"
            )
            await self.classify()

    def _pending_count(self, pid: int, source_type: str) -> int:
        tbl = _TABLE.get(source_type)
        if not tbl:
            return 0
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE project_id=%s AND wi_id IS NULL",
                        (pid,),
                    )
                    return cur.fetchone()[0] or 0
        except Exception as e:
            log.debug(f"_pending_count({source_type}) error: {e}")
            return 0

    # ── Pending events fetch ───────────────────────────────────────────────────

    def _fetch_pending_events(self, pid: int) -> dict:
        """Return all pending (wi_id IS NULL) rows from every mem_mrr_* table."""
        result: dict[str, list[dict]] = {
            "prompts": [], "commits": [], "messages": [], "items": []
        }
        if not db.is_available():
            return result
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Prompts
                    cur.execute(
                        """SELECT id::text, session_id, source_id,
                                  LEFT(prompt, 1000) AS prompt,
                                  LEFT(response, 2000) AS response,
                                  tags, created_at
                           FROM mem_mrr_prompts
                           WHERE project_id=%s AND wi_id IS NULL
                           ORDER BY created_at ASC
                           LIMIT 200""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["prompts"].append(d)

                    # Commits — include linked code symbols
                    cur.execute(
                        """SELECT c.commit_hash, c.commit_msg,
                                  LEFT(c.summary, 800) AS summary,
                                  LEFT(c.diff_summary, 1000) AS diff_summary,
                                  c.tags, c.author, c.created_at,
                                  c.prompt_id::text AS prompt_id
                           FROM mem_mrr_commits c
                           WHERE c.project_id=%s AND c.wi_id IS NULL
                           ORDER BY c.created_at ASC
                           LIMIT 100""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["commits"].append(d)

                    # Messages
                    cur.execute(
                        """SELECT id::text, platform, channel,
                                  LEFT(messages::text, 800) AS messages_text,
                                  tags, created_at
                           FROM mem_mrr_messages
                           WHERE project_id=%s AND wi_id IS NULL
                           ORDER BY created_at ASC
                           LIMIT 50""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["messages"].append(d)

                    # Items
                    cur.execute(
                        """SELECT id::text, item_type, title,
                                  LEFT(summary, 800) AS summary,
                                  tags, created_at
                           FROM mem_mrr_items
                           WHERE project_id=%s AND wi_id IS NULL
                           ORDER BY created_at ASC
                           LIMIT 50""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["items"].append(d)
        except Exception as e:
            log.warning(f"_fetch_pending_events error: {e}")
        return result

    # ── Event grouping ─────────────────────────────────────────────────────────

    def _group_events(self, events: dict) -> list[dict]:
        """Group events into token-bounded batches for LLM classification.

        Each batch stays under ~6000 tokens to fit in Haiku's context.
        Linked prompts+commits are kept together in the same group.
        """
        MAX_TOKENS = 6000
        groups: list[dict] = []
        current: dict = {
            "prompts": [], "commits": [], "messages": [], "items": [],
        }
        current_tokens = 0

        def _flush():
            nonlocal current, current_tokens
            total = sum(len(v) for v in current.values())
            if total:
                groups.append(dict(current))
            current = {"prompts": [], "commits": [], "messages": [], "items": []}
            current_tokens = 0

        # Track which prompts link to commits (to keep them in same group)
        prompt_ids_in_current: set[str] = set()

        for p in events["prompts"]:
            t = _count_tokens(
                (p.get("prompt") or "") + " " + (p.get("response") or "")
            )
            if current_tokens + t > MAX_TOKENS and current_tokens > 0:
                _flush()
            current["prompts"].append(p)
            prompt_ids_in_current.add(p["id"])
            current_tokens += t

        # Attach commits to the same group as their linked prompt (if any)
        standalone_commits = []
        for c in events["commits"]:
            if c.get("prompt_id") and c["prompt_id"] in prompt_ids_in_current:
                current["commits"].append(c)
            else:
                standalone_commits.append(c)

        _flush()

        # Standalone commits in their own groups
        for c in standalone_commits:
            t = _count_tokens((c.get("commit_msg") or "") + " " + (c.get("summary") or ""))
            if current_tokens + t > MAX_TOKENS and current_tokens > 0:
                _flush()
            current["commits"].append(c)
            current_tokens += t

        _flush()

        # Messages and items appended to their own groups
        for m in events["messages"]:
            t = _count_tokens(m.get("messages_text") or "")
            if current_tokens + t > MAX_TOKENS and current_tokens > 0:
                _flush()
            current["messages"].append(m)
            current_tokens += t
        _flush()

        for it in events["items"]:
            t = _count_tokens((it.get("title") or "") + " " + (it.get("summary") or ""))
            if current_tokens + t > MAX_TOKENS and current_tokens > 0:
                _flush()
            current["items"].append(it)
            current_tokens += t
        _flush()

        return [g for g in groups if any(v for v in g.values())]

    # ── Format events for LLM ─────────────────────────────────────────────────

    def _format_group_for_prompt(self, group: dict) -> str:
        """Render one event group as a text block for the classification prompt."""
        lines: list[str] = []

        for p in group.get("prompts", []):
            ts = (p.get("created_at") or "")[:16]
            tags_str = json.dumps(p.get("tags") or {}) if p.get("tags") else ""
            lines.append(f"[PROMPT {p['id'][:8]} {ts}] {tags_str}")
            lines.append(f"  User: {(p.get('prompt') or '')[:500]}")
            lines.append(f"  AI:   {(p.get('response') or '')[:1000]}")
            lines.append("")

        for c in group.get("commits", []):
            ts = (c.get("created_at") or "")[:16]
            linked = f" (linked to prompt {c['prompt_id'][:8]})" if c.get("prompt_id") else ""
            lines.append(f"[COMMIT {c['commit_hash'][:8]} {ts}{linked}]")
            lines.append(f"  {c.get('commit_msg', '')}")
            if c.get("summary"):
                lines.append(f"  Summary: {c['summary'][:400]}")
            lines.append("")

        for m in group.get("messages", []):
            ts = (m.get("created_at") or "")[:16]
            lines.append(f"[MESSAGE {m['id'][:8]} {ts} platform={m.get('platform','')}]")
            lines.append(f"  {(m.get('messages_text') or '')[:500]}")
            lines.append("")

        for it in group.get("items", []):
            ts = (it.get("created_at") or "")[:16]
            lines.append(f"[ITEM {it['id'][:8]} {ts} type={it.get('item_type','')}]")
            lines.append(f"  {it.get('title', '')}: {(it.get('summary') or '')[:400]}")
            lines.append("")

        return "\n".join(lines)

    # ── Existing context ───────────────────────────────────────────────────────

    def _load_existing_context(self, pid: int) -> str:
        """Load recently approved work items as context for the LLM."""
        if not db.is_available():
            return "(no existing work items)"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT wi_id, wi_type, name, LEFT(summary, 200) AS summary
                           FROM mem_work_items
                           WHERE project_id=%s AND wi_id IS NOT NULL
                             AND wi_id NOT LIKE 'REJ%%'
                           ORDER BY approved_at DESC NULLS LAST
                           LIMIT 20""",
                        (pid,),
                    )
                    rows = cur.fetchall()
            if not rows:
                return "(no existing work items)"
            return "\n".join(
                f"- [{r[0]}] {r[1]}: {r[2]} — {r[3]}"
                for r in rows
            )
        except Exception as e:
            log.debug(f"_load_existing_context error: {e}")
            return "(no existing work items)"

    # ── LLM classification call ────────────────────────────────────────────────

    async def _classify_group(self, group: dict, existing_ctx: str) -> list[dict]:
        """Call Haiku to classify one event group. Returns list of item dicts."""
        cfg = self._prompts_cfg().get("classification", {})
        system = cfg.get("system", "Classify development events into work items.")
        template = cfg.get("event_prompt", "{existing_context}\n\n{events_block}")

        events_block = self._format_group_for_prompt(group)
        user_prompt = template.format(
            existing_context=existing_ctx,
            events_block=events_block,
        )

        raw = await _call_haiku(system, user_prompt, max_tokens=4000)
        if not raw:
            return []

        # Extract JSON array from response
        text = raw.strip()
        if "```" in text:
            # Strip markdown fences
            text = re.sub(r"```[a-z]*\n?", "", text).strip()

        # Find the outermost JSON array
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start == -1 or end == 0:
            log.debug(f"_classify_group: no JSON array in response: {text[:200]}")
            return []

        try:
            items = json.loads(text[start:end])
        except json.JSONDecodeError as e:
            log.debug(f"_classify_group: JSON parse error: {e} — {text[start:end][:300]}")
            return []

        if not isinstance(items, list):
            return []

        # Attach source IDs from the group
        prompt_ids   = [p["id"]           for p in group.get("prompts", [])]
        commit_hashes= [c["commit_hash"]  for c in group.get("commits", [])]
        message_ids  = [m["id"]           for m in group.get("messages", [])]
        item_ids     = [i["id"]           for i in group.get("items", [])]

        valid = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            wi_type = raw_item.get("wi_type", "task")
            if wi_type not in _TYPE_SEQ:
                wi_type = "task"
            # Merge LLM-provided mrr_ids with the full group IDs
            mrr = raw_item.get("mrr_ids") or {}
            merged_mrr = {
                "prompts":  list(set((mrr.get("prompts")  or []) + prompt_ids)),
                "commits":  list(set((mrr.get("commits")  or []) + commit_hashes)),
                "messages": list(set((mrr.get("messages") or []) + message_ids)),
                "items":    list(set((mrr.get("items")    or []) + item_ids)),
            }
            valid.append({
                "wi_type":         wi_type,
                "item_level":      int(raw_item.get("item_level", 2)),
                "name":            (raw_item.get("name") or "")[:200],
                "summary":         raw_item.get("summary") or "",
                "deliveries":      raw_item.get("deliveries") or "",
                "delivery_type":   raw_item.get("delivery_type") or "",
                "score_importance":min(5, max(0, int(raw_item.get("score_importance", 0)))),
                "score_status":    min(5, max(0, int(raw_item.get("score_status", 0)))),
                "mrr_ids":         merged_mrr,
                "suggested_parent_name": raw_item.get("suggested_parent_name"),
            })
        return valid

    # ── Save to DB ─────────────────────────────────────────────────────────────

    def _save_classifications(self, items: list[dict], pid: int) -> list[dict]:
        """Insert classified items into mem_work_items. Returns saved items."""
        if not items or not db.is_available():
            return []
        saved = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for item in items:
                        cur.execute(
                            """INSERT INTO mem_work_items
                               (client_id, project_id, wi_type, item_level, name, summary,
                                deliveries, delivery_type, score_importance, score_status,
                                mrr_ids)
                               VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               RETURNING id::text""",
                            (
                                pid,
                                item["wi_type"],
                                item["item_level"],
                                item["name"],
                                item["summary"],
                                item["deliveries"],
                                item["delivery_type"],
                                item["score_importance"],
                                item["score_status"],
                                json.dumps(item["mrr_ids"]),
                            ),
                        )
                        row = cur.fetchone()
                        if row:
                            item["id"] = row[0]
                            saved.append(item)
                conn.commit()
        except Exception as e:
            log.warning(f"_save_classifications error: {e}")
        return saved

    # ── Main classify entry point ─────────────────────────────────────────────

    async def classify(self) -> dict:
        """Classify all pending mirror events into mem_work_items.

        Returns {"classified": N, "groups": M, "items": [...]}
        """
        pid = self._get_project_id()
        if not pid:
            return {"classified": 0, "groups": 0, "items": [], "error": "project not found"}

        events = self._fetch_pending_events(pid)
        total_events = sum(len(v) for v in events.values())
        if total_events == 0:
            return {"classified": 0, "groups": 0, "items": [], "message": "no pending events"}

        groups = self._group_events(events)
        existing_ctx = self._load_existing_context(pid)

        all_items: list[dict] = []
        for group in groups:
            try:
                items = await self._classify_group(group, existing_ctx)
                if items:
                    saved = self._save_classifications(items, pid)
                    all_items.extend(saved)
            except Exception as e:
                log.warning(f"classify: group error: {e}")

        return {
            "classified": len(all_items),
            "groups":     len(groups),
            "items":      all_items,
            "events_in":  total_events,
        }

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def get_pending(self, pid: int) -> list[dict]:
        """Return all work items pending approval (wi_id IS NULL)."""
        return self._list_items(pid, where="wi_id IS NULL")

    def get_all(self, pid: int, wi_type: Optional[str] = None,
                item_level: Optional[int] = None) -> list[dict]:
        """Return all work items, optionally filtered."""
        conditions = []
        if wi_type:
            conditions.append(f"wi_type = '{wi_type}'")
        if item_level is not None:
            conditions.append(f"item_level = {item_level}")
        where = " AND ".join(conditions) if conditions else "TRUE"
        return self._list_items(pid, where=where)

    def _list_items(self, pid: int, where: str = "TRUE") -> list[dict]:
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT id::text, wi_id, wi_type, item_level, name, summary,
                                   deliveries, delivery_type,
                                   score_importance, score_status,
                                   mrr_ids, wi_parent_id::text, tags,
                                   approved_at, created_at, updated_at
                            FROM mem_work_items
                            WHERE project_id=%s AND {where}
                            ORDER BY created_at DESC
                            LIMIT 500""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            result = []
            for row in rows:
                d = dict(zip(cols, row))
                for key in ("approved_at", "created_at", "updated_at"):
                    if d.get(key):
                        d[key] = d[key].isoformat()
                result.append(d)
            return result
        except Exception as e:
            log.warning(f"_list_items error: {e}")
            return []

    def get_stats(self, pid: int) -> dict:
        """Return counts by status and type."""
        if not db.is_available():
            return {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT
                             COUNT(*) FILTER (WHERE wi_id IS NULL) AS pending,
                             COUNT(*) FILTER (WHERE wi_id IS NOT NULL
                                               AND wi_id NOT LIKE 'REJ%%') AS approved,
                             COUNT(*) FILTER (WHERE wi_id LIKE 'REJ%%') AS rejected,
                             COUNT(*) FILTER (WHERE wi_type='bug') AS bugs,
                             COUNT(*) FILTER (WHERE wi_type='feature') AS features,
                             COUNT(*) FILTER (WHERE wi_type='task') AS tasks,
                             COUNT(*) FILTER (WHERE wi_type='policy') AS policies,
                             COUNT(*) FILTER (WHERE wi_type='use_case') AS use_cases
                           FROM mem_work_items
                           WHERE project_id=%s""",
                        (pid,),
                    )
                    row = cur.fetchone()
                    cols = [d[0] for d in cur.description]
            if row:
                return dict(zip(cols, row))
        except Exception as e:
            log.warning(f"get_stats error: {e}")
        return {}

    # ── Approval ──────────────────────────────────────────────────────────────

    def approve(self, item_id: str, pid: int) -> dict:
        """Approve a work item: assign wi_id, mark linked mirror rows, upsert planner_tag."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Load the item
                    cur.execute(
                        """SELECT wi_type, name, summary, mrr_ids, wi_parent_id::text
                           FROM mem_work_items
                           WHERE id=%s::uuid AND project_id=%s AND wi_id IS NULL""",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "item not found or already processed"}
                    wi_type, name, summary, mrr_ids, parent_id = row

                    # Generate ID
                    new_wi_id = _generate_wi_id(cur, pid, wi_type)

                    # Update work item
                    cur.execute(
                        """UPDATE mem_work_items
                           SET wi_id=%s, approved_at=NOW(), updated_at=NOW()
                           WHERE id=%s::uuid""",
                        (new_wi_id, item_id),
                    )

                    # Mark linked mirror rows (skip invalid IDs)
                    mrr = mrr_ids if isinstance(mrr_ids, dict) else {}
                    for prompt_id in mrr.get("prompts") or []:
                        if not _UUID_RE.match(str(prompt_id)):
                            log.debug(f"approve: skipping invalid prompt_id: {prompt_id!r}")
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_prompts SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (new_wi_id, prompt_id, pid),
                        )
                    for commit_hash in mrr.get("commits") or []:
                        cur.execute(
                            "UPDATE mem_mrr_commits SET wi_id=%s WHERE commit_hash=%s AND project_id=%s",
                            (new_wi_id, commit_hash, pid),
                        )
                    for msg_id in mrr.get("messages") or []:
                        if not _UUID_RE.match(str(msg_id)):
                            log.debug(f"approve: skipping invalid msg_id: {msg_id!r}")
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_messages SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (new_wi_id, msg_id, pid),
                        )
                    for it_id in mrr.get("items") or []:
                        if not _UUID_RE.match(str(it_id)):
                            log.debug(f"approve: skipping invalid item_id: {it_id!r}")
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_items SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (new_wi_id, it_id, pid),
                        )

                conn.commit()

            # Create / update planner_tag
            _upsert_planner_tag(
                project=self.project,
                project_id=pid,
                name=name or new_wi_id,
                wi_type=wi_type,
                description=summary or "",
                parent_id=parent_id,
            )

            return {"wi_id": new_wi_id, "item_id": item_id, "wi_type": wi_type, "name": name}
        except Exception as e:
            log.warning(f"approve({item_id}) error: {e}")
            return {"error": str(e)}

    def reject(self, item_id: str, pid: int) -> dict:
        """Reject a work item: assign REJxxxxxx wi_id, mark linked mirror rows."""
        import uuid
        rej_id = "REJ" + uuid.uuid4().hex[:6].upper()
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT mrr_ids FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND wi_id IS NULL",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "item not found or already processed"}
                    mrr_ids = row[0] or {}

                    cur.execute(
                        "UPDATE mem_work_items SET wi_id=%s, updated_at=NOW() WHERE id=%s::uuid",
                        (rej_id, item_id),
                    )
                    # Mark linked mirror rows so they aren't re-classified
                    mrr = mrr_ids if isinstance(mrr_ids, dict) else {}
                    for prompt_id in mrr.get("prompts") or []:
                        if not _UUID_RE.match(str(prompt_id)):
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_prompts SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (rej_id, prompt_id, pid),
                        )
                    for commit_hash in mrr.get("commits") or []:
                        cur.execute(
                            "UPDATE mem_mrr_commits SET wi_id=%s WHERE commit_hash=%s AND project_id=%s",
                            (rej_id, commit_hash, pid),
                        )
                    for msg_id in mrr.get("messages") or []:
                        if not _UUID_RE.match(str(msg_id)):
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_messages SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (rej_id, msg_id, pid),
                        )
                    for it_id in mrr.get("items") or []:
                        if not _UUID_RE.match(str(it_id)):
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_items SET wi_id=%s WHERE id=%s::uuid AND project_id=%s",
                            (rej_id, it_id, pid),
                        )
                conn.commit()
            return {"wi_id": rej_id, "item_id": item_id}
        except Exception as e:
            log.warning(f"reject({item_id}) error: {e}")
            return {"error": str(e)}

    def update(self, item_id: str, pid: int, fields: dict) -> dict:
        """Update editable fields on a work item."""
        allowed = {
            "name", "summary", "deliveries", "delivery_type",
            "score_importance", "score_status", "wi_type", "wi_parent_id",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return {"error": "no valid fields"}
        if not db.is_available():
            return {"error": "db not available"}
        try:
            set_clause = ", ".join(f"{k}=%s" for k in updates)
            vals = list(updates.values()) + [item_id, pid]
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE mem_work_items SET {set_clause}, updated_at=NOW() "
                        f"WHERE id=%s::uuid AND project_id=%s",
                        vals,
                    )
                conn.commit()
            return {"updated": True, "fields": list(updates.keys())}
        except Exception as e:
            log.warning(f"update({item_id}) error: {e}")
            return {"error": str(e)}

    def delete(self, item_id: str, pid: int) -> dict:
        """Delete a work item (pending only; approved items should be rejected instead)."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND wi_id IS NULL",
                        (item_id, pid),
                    )
                    deleted = cur.rowcount
                conn.commit()
            return {"deleted": deleted > 0}
        except Exception as e:
            log.warning(f"delete({item_id}) error: {e}")
            return {"error": str(e)}

    def move_event(self, item_id: str, pid: int,
                   mrr_type: str, mrr_id: str, target_id: str) -> dict:
        """Move a mirror event from one work item to another.

        Removes mrr_id from item_id.mrr_ids and adds it to target_id.mrr_ids.
        """
        if mrr_type not in _TABLE:
            return {"error": f"invalid mrr_type: {mrr_type}"}
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Remove from source item
                    cur.execute(
                        f"""UPDATE mem_work_items
                            SET mrr_ids = jsonb_set(
                                mrr_ids,
                                '{{{mrr_type}}}',
                                COALESCE(mrr_ids->%s, '[]'::jsonb) - %s
                            ), updated_at=NOW()
                            WHERE id=%s::uuid AND project_id=%s""",
                        (mrr_type, mrr_id, item_id, pid),
                    )
                    # Add to target item
                    cur.execute(
                        f"""UPDATE mem_work_items
                            SET mrr_ids = jsonb_set(
                                mrr_ids,
                                '{{{mrr_type}}}',
                                COALESCE(mrr_ids->%s, '[]'::jsonb) || to_jsonb(%s)
                            ), updated_at=NOW()
                            WHERE id=%s::uuid AND project_id=%s""",
                        (mrr_type, mrr_id, target_id, pid),
                    )
                conn.commit()
            return {"moved": True, "mrr_type": mrr_type, "mrr_id": mrr_id}
        except Exception as e:
            log.warning(f"move_event error: {e}")
            return {"error": str(e)}

    def approve_all_under(self, parent_id: str, pid: int) -> dict:
        """Approve all pending items under a parent work item."""
        items = self._list_items(
            pid,
            where=f"wi_parent_id='{parent_id}'::uuid AND wi_id IS NULL",
        )
        approved = []
        errors   = []
        for item in items:
            result = self.approve(item["id"], pid)
            if "error" in result:
                errors.append(result)
            else:
                approved.append(result)
        return {"approved": len(approved), "errors": errors}

    def reset_pending(self, pid: int) -> dict:
        """Reset all pending mir rows by setting wi_id=NULL on non-SKIP, non-approved rows."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            counts = {}
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for src, tbl in _TABLE.items():
                        cur.execute(
                            f"UPDATE {tbl} SET wi_id=NULL "
                            f"WHERE project_id=%s AND wi_id IS NOT NULL AND wi_id!='SKIP'",
                            (pid,),
                        )
                        counts[src] = cur.rowcount
                conn.commit()
            return {"reset": counts}
        except Exception as e:
            log.warning(f"reset_pending error: {e}")
            return {"error": str(e)}
