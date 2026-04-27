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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml

from core.config import settings
from core.database import db
from memory.memory_code_parser import get_file_hotspots

log = logging.getLogger(__name__)

# ── Prompt path ───────────────────────────────────────────────────────────────
_WI_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "command_work_items.yaml"

# ── Table map ─────────────────────────────────────────────────────────────────
_TABLE: dict[str, str] = {
    "prompts":  "mem_mrr_prompts",
    "commits":  "mem_mrr_commits",
    "messages": "mem_mrr_messages",
    "items":    "mem_mrr_items",
}

# ── Type → (seq_key, display_prefix) ─────────────────────────────────────────
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


def _use_case_slug(name: str) -> str:
    """Convert a use case name to a URL-safe slug for MD filenames."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:60]


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
        log.warning("_call_haiku: no Claude API key found")
        return ""
    try:
        import anthropic
        # Use async context manager to ensure the httpx client is properly closed,
        # which prevents 'RuntimeError: Event loop is closed' on GC cleanup.
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
    """Rough token estimate: word count × 1.3."""
    return int(len(text.split()) * 1.3)


def _generate_wi_id(cur, project_id: int, wi_type: str) -> str:
    """Allocate the next seq_counter value and return a formatted ID like BU0003."""
    from data.dl_seq import next_seq
    seq_key, prefix = _TYPE_SEQ.get(wi_type, _DEFAULT_SEQ)
    val = next_seq(cur, project_id, seq_key)
    return f"{prefix}{val:04d}"


def _insert_wi(cur, item: dict, pid: int, parent_id: Optional[str]) -> str:
    """Insert a single work item row with a temp AI-prefixed wi_id. Returns new UUID string.

    wi_id is set to AI{n:04d} (e.g. AI0001) at classification time.
    It is replaced by the real ID (US/BU/FE/…) when the user approves.
    tags are populated later by _update_item_tags() after all items are saved.
    """
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
            score_imp,  # user_importance defaults to AI score
            "open",     # user_status always starts as 'open' (TEXT after m079)
            json.dumps(item.get("mrr_ids") or {}),
            parent_id if parent_id else None,
            temp_wi_id,
        ),
    )
    row = cur.fetchone()
    return row[0] if row else ""


# Only these keys are user-intent tags — everything else (source, llm, …) is system metadata
_USER_TAG_KEYS = {"phase", "feature", "bug", "work-item"}


def _merge_tags(existing: dict, incoming: dict) -> dict:
    """Merge two tag dicts — for each key keep all values as a set if multiple."""
    result = dict(existing)
    for k, v in incoming.items():
        if not v:
            continue
        if k not in result:
            result[k] = v
        elif result[k] != v:
            # Store as comma-joined string when multiple values for same key
            existing_vals = set(str(result[k]).split(","))
            existing_vals.add(str(v))
            result[k] = ",".join(sorted(existing_vals))
    return result


def _update_item_tags(saved_items: list[dict], tag_lookup: dict[str, dict]) -> None:
    """Populate mem_work_items.tags by merging tags from all referenced events.

    tag_lookup: mrr_id → tags dict (built from all fetched events before classification).
    For use cases: also merges tags from all children after children are saved.
    """
    if not db.is_available() or not saved_items:
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                for item in saved_items:
                    item_id = item.get("id")
                    if not item_id:
                        continue
                    mrr = item.get("mrr_ids") or {}
                    merged: dict = {}
                    for ref_list in mrr.values():
                        for ref_id in (ref_list or []):
                            raw_tags = tag_lookup.get(ref_id) or {}
                            # Strip system keys — only keep user-intent tags
                            user_tags = {k: v for k, v in raw_tags.items() if k in _USER_TAG_KEYS}
                            merged = _merge_tags(merged, user_tags)
                    if merged:
                        cur.execute(
                            "UPDATE mem_work_items SET tags=%s WHERE id=%s::uuid",
                            (json.dumps(merged), item_id),
                        )
            conn.commit()
    except Exception as e:
        log.debug(f"_update_item_tags error: {e}")


def _rollup_uc_tags(pid: int, uc_ids: list[str]) -> None:
    """Aggregate all children tags up into each use case row."""
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
    """Compute embedding for an approved work item and store in DB."""
    try:
        text = " | ".join(filter(None, [
            fields.get("name", ""),
            fields.get("wi_type", ""),
            fields.get("summary", ""),
            fields.get("deliveries", ""),
            fields.get("delivery_type", ""),
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
        log.debug(f"_embed_work_item({item_id}) skipped: {e}")



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
                                  c.prompt_id::text AS prompt_id,
                                  c.commit_type
                           FROM mem_mrr_commits c
                           WHERE c.project_id=%s AND c.wi_id IS NULL
                           ORDER BY c.created_at ASC
                           LIMIT 100""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    commit_hashes: list[str] = []
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["commits"].append(d)
                        commit_hashes.append(d["commit_hash"])

                    # Attach hotspot file data to commits that touch risky files
                    if commit_hashes:
                        cur.execute(
                            """SELECT DISTINCT commit_hash, file_path
                               FROM mem_mrr_commits_code
                               WHERE commit_hash = ANY(%s)""",
                            (commit_hashes,),
                        )
                        hash_to_files: dict[str, list[str]] = {}
                        for chash, fpath in cur.fetchall():
                            hash_to_files.setdefault(chash, []).append(fpath)

                        all_files = [fp for fps in hash_to_files.values() for fp in fps]
                        if all_files:
                            hotspot_map = {
                                h["file_path"]: h
                                for h in get_file_hotspots(pid, file_paths=all_files)
                                if h["hotspot_score"] >= 1.0
                            }
                            for commit in result["commits"]:
                                files = hash_to_files.get(commit["commit_hash"], [])
                                hs = [hotspot_map[f] for f in files if f in hotspot_map]
                                if hs:
                                    commit["_hotspot_files"] = hs

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

        All event types are interleaved in chronological order so commits
        appear alongside the prompts from the same time window.
        Each batch stays under ~3000 tokens so LLM responses fit in 8000 tokens.
        """
        MAX_TOKENS = 3000

        # Flatten all events with their table key and timestamp, sort chronologically
        flat: list[tuple[str, dict, str]] = []
        for p in events["prompts"]:
            flat.append(("prompts",  p,  p.get("created_at") or ""))
        for c in events["commits"]:
            flat.append(("commits",  c,  c.get("created_at") or ""))
        for m in events["messages"]:
            flat.append(("messages", m,  m.get("created_at") or ""))
        for it in events["items"]:
            flat.append(("items",    it, it.get("created_at") or ""))
        flat.sort(key=lambda x: x[2])

        groups: list[dict] = []
        current: dict = {"prompts": [], "commits": [], "messages": [], "items": []}
        current_tokens = 0

        def _flush():
            nonlocal current, current_tokens
            if any(v for v in current.values()):
                groups.append({k: list(v) for k, v in current.items()})
            current["prompts"].clear(); current["commits"].clear()
            current["messages"].clear(); current["items"].clear()
            current_tokens = 0

        for tbl, data, _ in flat:
            if tbl == "prompts":
                t = _count_tokens((data.get("prompt") or "") + " " + (data.get("response") or ""))
            elif tbl == "commits":
                t = _count_tokens((data.get("commit_msg") or "") + " " + (data.get("summary") or ""))
            elif tbl == "messages":
                t = _count_tokens(data.get("messages_text") or "")
            else:
                t = _count_tokens((data.get("title") or "") + " " + (data.get("summary") or ""))

            if current_tokens + t > MAX_TOKENS and current_tokens > 0:
                _flush()
            current[tbl].append(data)
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
            ctype = f" type={c['commit_type']}" if c.get("commit_type") else ""
            lines.append(f"[COMMIT {c['commit_hash'][:8]} {ts}{ctype}{linked}]")
            lines.append(f"  {c.get('commit_msg', '')}")
            if c.get("summary"):
                lines.append(f"  Summary: {c['summary'][:400]}")
            hotspots = c.get("_hotspot_files") or []
            if hotspots:
                lines.append("  [FILE HOTSPOTS — high-risk files touched by this commit]")
                for h in hotspots[:5]:
                    lines.append(
                        f"    {h['file_path']}: score={h['hotspot_score']:.1f} "
                        f"changes={h['change_count']} bug_commits={h['bug_commit_count']} "
                        f"lines={h['current_lines']} reverts={h['revert_count']}"
                    )
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
        """Load recently approved AND draft use cases with children as LLM context.

        Including AI-draft use cases allows subsequent groups in the same classify
        run to attach children to use cases already created by earlier groups,
        instead of creating duplicate/similar use cases.
        """
        if not db.is_available():
            return "(no existing work items)"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Fetch approved + AI-draft use cases (exclude rejected)
                    cur.execute(
                        """SELECT id::text, wi_id, name, LEFT(summary, 300) AS summary, tags
                           FROM mem_work_items
                           WHERE project_id=%s AND wi_type='use_case'
                             AND wi_id IS NOT NULL
                             AND wi_id NOT LIKE 'REJ%%'
                           ORDER BY approved_at DESC NULLS LAST, created_at DESC
                           LIMIT 20""",
                        (pid,),
                    )
                    uc_rows = cur.fetchall()
                    if not uc_rows:
                        return "(no existing use cases)"

                    # Fetch approved children for those use cases
                    uc_ids = [r[0] for r in uc_rows]
                    cur.execute(
                        """SELECT wi_id, wi_type, name, wi_parent_id::text, score_status
                           FROM mem_work_items
                           WHERE project_id=%s AND wi_parent_id = ANY(%s::uuid[])
                             AND wi_id IS NOT NULL
                             AND wi_id NOT LIKE 'REJ%%'
                             AND wi_id NOT LIKE 'AI%%'
                           ORDER BY created_at ASC""",
                        (pid, uc_ids),
                    )
                    child_rows = cur.fetchall()

            # Build map: uc_id → children list
            children_map: dict[str, list] = {uid: [] for uid in uc_ids}
            for c in child_rows:
                parent = c[3]
                if parent in children_map:
                    status_label = "done" if c[4] == 5 else ("in_progress" if c[4] else "requirement")
                    children_map[parent].append(f"{c[0]} {c[2]} [{status_label}]")

            lines = ["## Approved Use Cases"]
            for r in uc_rows:
                uid, wi_id, name, summary, uc_tags = r
                lines.append(f"### {wi_id} · {name}")
                lines.append(summary or "")
                if uc_tags:
                    tag_str = " ".join(f"{k}:{v}" for k, v in (uc_tags or {}).items() if v)
                    if tag_str:
                        lines.append(f"Tags: {tag_str}")
                ch = children_map.get(uid, [])
                if ch:
                    lines.append(f"Children: {', '.join(ch)}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            log.debug(f"_load_existing_context error: {e}")
            return "(no existing work items)"

    # ── LLM classification call ────────────────────────────────────────────────

    async def _classify_group(self, group: dict, existing_ctx: str,
                               max_use_cases: int = 8) -> list[dict]:
        """Call Haiku to classify one event group. Returns list of item dicts."""
        cfg = self._prompts_cfg().get("classification", {})
        system = cfg.get("system", "Classify development events into work items.")
        # Append max-use-cases constraint + granularity instruction
        system += (
            f"\n\nIMPORTANT CONSTRAINTS:"
            f"\n1. USE CASES: The entire project should have at most {max_use_cases} use cases total."
            f"\n   - Check the existing use cases listed in the context first."
            f"\n   - If the events fit an existing use case, set existing_wi_id to that use case's ID and do NOT emit a new use_case entry."
            f"\n   - Only create a new use_case entry when events genuinely don't fit any existing one."
            f"\n2. ITEMS: Every distinct feature, bug, task, or change in the events must become its own item."
            f"\n   - Each item covers ONE specific piece of work — do NOT bundle unrelated changes into a single item."
            f"\n   - A use case with 5–15 items is normal and expected."
            f"\n   - Items must be granular: one commit that fixes a bug → one bug item; one prompt session that designs a feature → one feature/requirement item."
            f"\n   - EVERY event in this batch must be covered by at least one item."
        )
        template = cfg.get("event_prompt", "{existing_context}\n\n{events_block}")

        events_block = self._format_group_for_prompt(group)
        # Use plain replacement — template contains literal { } in JSON examples
        # so str.format() would raise KeyError on them.
        user_prompt = (
            template
            .replace("{existing_context}", existing_ctx)
            .replace("{events_block}", events_block)
        )

        raw = await _call_haiku(system, user_prompt, max_tokens=8000)
        if not raw:
            log.warning("_classify_group: _call_haiku returned empty string")
            return []

        log.info(f"_classify_group: raw response preview (first 300): {raw[:300]!r}")
        # Extract JSON array from response
        text = raw.strip()
        if "```" in text:
            # Strip markdown fences
            text = re.sub(r"```[a-z]*\n?", "", text).strip()

        # Find the outermost JSON array
        start = text.find("[")
        end   = text.rfind("]") + 1
        if start == -1 or end == 0:
            log.warning(f"_classify_group: no JSON array in response (len={len(text)}): {text[:400]}")
            return []

        try:
            items = json.loads(text[start:end])
        except json.JSONDecodeError as e:
            log.warning(f"_classify_group: JSON parse error: {e} — {text[start:end][:400]}")
            return []

        if not isinstance(items, list):
            return []

        valid = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                continue
            wi_type = raw_item.get("wi_type", "task")
            if wi_type not in _TYPE_SEQ:
                wi_type = "task"
            # Use only the mrr_ids the LLM specifically assigned to this item.
            # (Previously we merged ALL group IDs into every item, which was wrong —
            #  it made each item look like it covered every prompt in the group.)
            mrr = raw_item.get("mrr_ids") or {}
            merged_mrr = {
                "prompts":  list(set(mrr.get("prompts")  or [])),
                "commits":  list(set(mrr.get("commits")  or [])),
                "messages": list(set(mrr.get("messages") or [])),
                "items":    list(set(mrr.get("items")    or [])),
            }
            valid.append({
                "wi_type":              wi_type,
                "item_level":           int(raw_item.get("item_level", 2)),
                "name":                 (raw_item.get("name") or "")[:200],
                "existing_wi_id":       (raw_item.get("existing_wi_id") or "").strip(),
                "summary":              raw_item.get("summary") or "",
                "deliveries":           raw_item.get("deliveries") or "",
                "delivery_type":        raw_item.get("delivery_type") or "",
                "score_importance":     min(5, max(0, int(raw_item.get("score_importance", 0)))),
                "score_status":         min(5, max(0, int(raw_item.get("score_status", 0)))),
                "mrr_ids":              merged_mrr,
                "suggested_parent_name": raw_item.get("suggested_parent_name"),
            })
        return valid

    # ── Save to DB ─────────────────────────────────────────────────────────────

    def _save_classifications(
        self,
        items: list[dict],
        pid: int,
        existing_uc_map: Optional[dict[str, str]] = None,
    ) -> tuple[list[dict], dict[str, str]]:
        """Two-phase insert: use_cases first, then children with parent FK.

        Accepts an existing uc_map (name→UUID) built from previous groups so
        children in later groups can link to use_cases from earlier groups.
        Returns (saved_items, updated_uc_map).
        """
        if not items or not db.is_available():
            return [], dict(existing_uc_map or {})
        uc_map: dict[str, str] = dict(existing_uc_map or {})  # copy — don't mutate caller
        saved: list[dict] = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Phase 1: resolve or create use_cases
                    for item in items:
                        if item.get("wi_type") != "use_case":
                            continue
                        existing = (item.get("existing_wi_id") or "").strip()
                        if existing:
                            cur.execute(
                                "SELECT id::text FROM mem_work_items "
                                "WHERE project_id=%s AND wi_id=%s",
                                (pid, existing),
                            )
                            row = cur.fetchone()
                            if row:
                                uc_map[item["name"]] = row[0]
                                continue
                        uc_id = _insert_wi(cur, item, pid, parent_id=None)
                        if uc_id:
                            uc_map[item["name"]] = uc_id
                            item["id"] = uc_id
                            saved.append(item)

                    # Phase 2: create children
                    for item in items:
                        if item.get("wi_type") == "use_case":
                            continue
                        existing = (item.get("existing_wi_id") or "").strip()
                        if existing:
                            cur.execute(
                                "SELECT id::text FROM mem_work_items "
                                "WHERE project_id=%s AND wi_id=%s",
                                (pid, existing),
                            )
                            if cur.fetchone():
                                continue  # already approved, skip
                        parent_id = uc_map.get(item.get("suggested_parent_name") or "")
                        child_id = _insert_wi(cur, item, pid, parent_id=parent_id)
                        if child_id:
                            item["id"] = child_id
                            saved.append(item)

                conn.commit()
        except Exception as e:
            log.warning(f"_save_classifications error: {e}")
        return saved, uc_map

    # ── Main classify entry point ─────────────────────────────────────────────

    async def classify(self, max_use_cases: Optional[int] = None) -> dict:
        """Classify all pending mirror events into mem_work_items.

        Each run first deletes all existing AI-temp rows (unapproved draft
        classification), then re-classifies all unprocessed events from scratch.
        Approved rows (real IDs like US/BU/FE) are never touched.

        max_use_cases: hint passed to LLM to consolidate into N use cases.
                       None = read from work_items.yaml classification.max_use_cases (default 8).

        Returns {"classified": N, "groups": M, "items": [...]}
        """
        # Read max_use_cases from YAML config when not explicitly provided
        if max_use_cases is None or max_use_cases <= 0:
            max_use_cases = int(
                self._prompts_cfg().get("classification", {}).get("max_use_cases", 8)
            )
        pid = self._get_project_id()
        if not pid:
            return {"classified": 0, "groups": 0, "items": [], "error": "project not found"}

        # Delete all unapproved draft rows from previous classification run
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM mem_work_items WHERE project_id=%s AND wi_id LIKE 'AI%%'",
                        (pid,),
                    )
                    deleted = cur.rowcount
                conn.commit()
            if deleted:
                log.info(f"classify: cleared {deleted} draft AI rows for project {pid}")
        except Exception as e:
            log.warning(f"classify: failed to clear draft rows: {e}")

        events = self._fetch_pending_events(pid)
        total_events = sum(len(v) for v in events.values())
        if total_events == 0:
            return {"classified": 0, "groups": 0, "items": [], "message": "no pending events"}

        # Build a flat id→tags lookup for post-save tag merging.
        # Keyed by the ID used in mrr_ids (UUID for prompts/messages/items, hash for commits).
        tag_lookup: dict[str, dict] = {}
        for p in events.get("prompts", []):
            tag_lookup[p["id"]] = p.get("tags") or {}
        for c in events.get("commits", []):
            tag_lookup[c["commit_hash"]] = c.get("tags") or {}
        for m in events.get("messages", []):
            tag_lookup[m["id"]] = m.get("tags") or {}
        for it in events.get("items", []):
            tag_lookup[it["id"]] = it.get("tags") or {}

        groups = self._group_events(events)
        log.info(f"classify: {total_events} events → {len(groups)} groups for project {pid} (max_use_cases={max_use_cases})")

        all_items: list[dict] = []
        uc_map: dict[str, str] = {}  # accumulated name→UUID across all groups
        for idx, group in enumerate(groups, 1):
            try:
                log.info(f"classify: processing group {idx}/{len(groups)}")
                # Reload context before each group so the LLM sees use cases
                # created by earlier groups in this run and can reuse them.
                existing_ctx = self._load_existing_context(pid)
                items = await self._classify_group(group, existing_ctx, max_use_cases)
                if items:
                    saved, uc_map = self._save_classifications(items, pid, uc_map)
                    # Merge event tags into each saved item's tags column
                    _update_item_tags(saved, tag_lookup)
                    all_items.extend(saved)
                    log.info(f"classify: group {idx} → {len(saved)} items saved")
            except Exception as e:
                log.warning(f"classify: group {idx} error: {e}")

        # Roll up children tags into their parent use cases
        uc_ids = [item["id"] for item in all_items if item.get("wi_type") == "use_case" and item.get("id")]
        if uc_ids:
            _rollup_uc_tags(pid, uc_ids)

        return {
            "classified":     len(all_items),
            "groups":         len(groups),
            "items":          all_items,
            "events_in":      total_events,
            "max_use_cases":  max_use_cases,
        }

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def get_pending(self, pid: int) -> list[dict]:
        """Return all work items pending approval (wi_id LIKE 'AI%')."""
        return self._list_items(pid, where="wi_id LIKE 'AI%%'")

    def get_pending_grouped(self, pid: int) -> list[dict]:
        """Return pending items grouped as use_cases with their children nested.

        Each entry in the returned list is a use_case dict with an extra
        'children' key containing its pending child items.
        Items with no parent use_case are returned under a synthetic
        '__unlinked__' group at the end.
        """
        all_pending = self._list_items(pid, where="wi_id LIKE 'AI%%'")

        use_cases: list[dict] = []
        children_map: dict[str, list[dict]] = {}  # uc UUID → child list
        unlinked: list[dict] = []

        for item in all_pending:
            if item.get("wi_type") == "use_case":
                item["children"] = []
                use_cases.append(item)
                children_map[item["id"]] = item["children"]
            # children handled in second pass

        for item in all_pending:
            if item.get("wi_type") == "use_case":
                continue
            parent_id = item.get("wi_parent_id")
            if parent_id and parent_id in children_map:
                children_map[parent_id].append(item)
            else:
                unlinked.append(item)

        result = use_cases
        if unlinked:
            result.append({
                "id": "__unlinked__",
                "wi_id": "__unlinked__",
                "wi_type": "use_case",
                "name": "Unlinked Items",
                "summary": "Items not matched to any use case",
                "children": unlinked,
            })
        return result

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

    def get_one(self, item_id: str, pid: int) -> Optional[dict]:
        """Return a single work item by UUID (including deleted items)."""
        if not db.is_available():
            return None
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT w.id::text, w.wi_id, w.wi_type, w.item_level, w.name, w.summary,
                                  w.deliveries, w.delivery_type,
                                  w.score_importance, w.score_status,
                                  w.user_importance, w.user_status,
                                  w.mrr_ids, w.wi_parent_id::text,
                                  p.wi_id AS wi_parent_wi_id,
                                  w.tags, w.approved_at, w.created_at, w.updated_at,
                                  w.start_date, w.due_date, w.completed_at, w.deleted_at,
                                  w.acceptance_criteria, w.implementation_plan,
                                  w.pipeline_status, w.pipeline_run_id
                           FROM mem_work_items w
                           LEFT JOIN mem_work_items p ON p.id = w.wi_parent_id
                           WHERE w.project_id=%s AND w.id=%s::uuid""",
                        (pid, item_id),
                    )
                    cols = [d[0] for d in cur.description]
                    row = cur.fetchone()
            if not row:
                return None
            d = dict(zip(cols, row))
            for key in ("approved_at", "created_at", "updated_at", "start_date",
                        "due_date", "completed_at", "deleted_at"):
                if d.get(key):
                    d[key] = d[key].isoformat() if hasattr(d[key], "isoformat") else str(d[key])
            return d
        except Exception as e:
            log.warning("get_one error: %s", e)
            return None

    def _list_items(self, pid: int, where: str = "TRUE") -> list[dict]:
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""SELECT w.id::text, w.wi_id, w.wi_type, w.item_level, w.name, w.summary,
                                   w.deliveries, w.delivery_type,
                                   w.score_importance, w.score_status,
                                   w.user_importance, w.user_status,
                                   w.mrr_ids, w.wi_parent_id::text,
                                   p.wi_id AS wi_parent_wi_id,
                                   w.tags,
                                   w.approved_at, w.created_at, w.updated_at,
                                   w.start_date, w.due_date, w.completed_at,
                                   w.acceptance_criteria, w.implementation_plan,
                                   w.pipeline_status, w.pipeline_run_id
                            FROM mem_work_items w
                            LEFT JOIN mem_work_items p ON p.id = w.wi_parent_id
                            WHERE w.project_id=%s AND {where} AND w.deleted_at IS NULL
                            ORDER BY COALESCE(w.user_importance, w.score_importance, 0) DESC,
                                     w.created_at DESC
                            LIMIT 500""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            result = []
            for row in rows:
                d = dict(zip(cols, row))
                for key in ("approved_at", "created_at", "updated_at", "start_date", "due_date", "completed_at"):
                    if d.get(key):
                        d[key] = d[key].isoformat() if hasattr(d[key], 'isoformat') else str(d[key])
                result.append(d)
            return result
        except Exception as e:
            log.warning(f"_list_items error: {e}")
            return []

    def get_approved_use_cases(self, pid: int) -> list[dict]:
        """Return approved use cases with recursive descendants + event/item stats."""
        if not db.is_available():
            return []
        try:
            ucs = self._list_items(
                pid,
                where="w.wi_type='use_case' AND w.wi_id IS NOT NULL "
                      "AND w.wi_id NOT LIKE 'AI%%' AND w.wi_id NOT LIKE 'REJ%%'",
            )
            if not ucs:
                return []

            uc_ids = [u["id"] for u in ucs]

            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        WITH RECURSIVE desc_tree AS (
                          SELECT id, wi_parent_id, 0 AS depth,
                                 wi_parent_id AS uc_id
                          FROM mem_work_items
                          WHERE wi_parent_id = ANY(%s::uuid[]) AND project_id = %s
                            AND wi_type != 'use_case' AND deleted_at IS NULL
                          UNION ALL
                          SELECT c.id, c.wi_parent_id, dt.depth + 1, dt.uc_id
                          FROM mem_work_items c
                          JOIN desc_tree dt ON c.wi_parent_id = dt.id
                          WHERE c.project_id = %s AND c.wi_type != 'use_case'
                            AND c.deleted_at IS NULL AND dt.depth < 10
                        )
                        SELECT w.id::text, w.wi_id, w.wi_type, w.item_level,
                               w.name, w.summary, w.deliveries, w.delivery_type,
                               w.score_importance, w.score_status,
                               w.user_importance, w.user_status,
                               w.mrr_ids, w.wi_parent_id::text,
                               p.wi_id AS wi_parent_wi_id, w.tags,
                               w.approved_at, w.created_at, w.updated_at,
                               w.start_date, w.due_date, w.completed_at,
                               dt.depth, dt.uc_id::text AS uc_id
                        FROM desc_tree dt
                        JOIN mem_work_items w ON w.id = dt.id
                        LEFT JOIN mem_work_items p ON p.id = w.wi_parent_id
                        ORDER BY dt.depth ASC,
                                 COALESCE(w.user_importance, w.score_importance, 0) DESC
                    """, (uc_ids, pid, pid))
                    cols = [d[0] for d in cur.description]
                    all_desc: list[dict] = []
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        for k in ("approved_at", "created_at", "updated_at", "start_date", "due_date", "completed_at"):
                            if d.get(k):
                                d[k] = d[k].isoformat() if hasattr(d[k], 'isoformat') else str(d[k])
                        all_desc.append(d)

            # Group descendants by their ancestor UC id
            desc_by_uc: dict[str, list[dict]] = {uid: [] for uid in uc_ids}
            for d in all_desc:
                uc_key = d.get("uc_id")
                if uc_key and uc_key in desc_by_uc:
                    desc_by_uc[uc_key].append(d)

            # Attach file hotspot data to items whose commits touched risky files
            all_commit_ids: list[str] = []
            for d in all_desc:
                mrr = d.get("mrr_ids") or {}
                all_commit_ids.extend(mrr.get("commits") or [])
            if all_commit_ids:
                try:
                    from memory.memory_code_parser import get_file_hotspots
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """SELECT DISTINCT commit_hash, file_path
                                   FROM mem_mrr_commits_code
                                   WHERE commit_hash = ANY(%s)""",
                                (all_commit_ids,),
                            )
                            hash_to_files: dict[str, list[str]] = {}
                            for chash, fpath in cur.fetchall():
                                hash_to_files.setdefault(chash, []).append(fpath)
                    all_files = list({fp for fps in hash_to_files.values() for fp in fps})
                    if all_files:
                        hotspot_map = {
                            h["file_path"]: h
                            for h in get_file_hotspots(pid, file_paths=all_files)
                            if h["hotspot_score"] >= 1.0
                        }
                        for d in all_desc:
                            commits = (d.get("mrr_ids") or {}).get("commits") or []
                            files = [fp for ch in commits for fp in hash_to_files.get(ch, [])]
                            hs = [hotspot_map[fp] for fp in files if fp in hotspot_map]
                            if hs:
                                d["_hotspot_files"] = hs
                except Exception as e:
                    log.debug(f"get_approved_use_cases hotspot attach error: {e}")

            def _mrr_count(item: dict, key: str) -> int:
                return len((item.get("mrr_ids") or {}).get(key, []))

            result = []
            for uc in ucs:
                kids = desc_by_uc.get(uc["id"], [])
                tp = sum(_mrr_count(c, "prompts")  for c in kids) + _mrr_count(uc, "prompts")
                tc = sum(_mrr_count(c, "commits")  for c in kids) + _mrr_count(uc, "commits")
                tm = sum(_mrr_count(c, "messages") for c in kids) + _mrr_count(uc, "messages")
                ti = sum(_mrr_count(c, "items")    for c in kids) + _mrr_count(uc, "items")

                approved_kids = [
                    c for c in kids
                    if c.get("wi_id") and
                    not c["wi_id"].startswith("AI") and
                    not c["wi_id"].startswith("REJ")
                ]

                # Tag each child with its UC id for frontend convenience
                for c in kids:
                    c["_uc_id"] = uc["id"]

                uc["children"] = kids  # flat list, depth included
                uc["stats"] = {
                    "total_prompts":     tp,
                    "total_commits":     tc,
                    "total_messages":    tm,
                    "total_events":      tp + tc + tm + ti,
                    "total_children":    len(kids),
                    "approved_children": len(approved_kids),
                    "pending_children":  len(kids) - len(approved_kids),
                }
                result.append(uc)

            result.sort(key=lambda u: u.get("approved_at") or "", reverse=True)
            return result
        except Exception as e:
            log.warning(f"get_approved_use_cases error: {e}")
            return []

    # ── Versioning helpers ─────────────────────────────────────────────────────

    def _snapshot_uc(self, uc_id: str, pid: int) -> tuple[dict, list[dict]]:
        """Return (uc_row, ordered_descendants) for versioning."""
        uc_items = self._list_items(pid, where=f"w.id='{uc_id}'::uuid")
        uc = uc_items[0] if uc_items else {}
        if not uc:
            return {}, []
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH RECURSIVE desc_tree AS (
                      SELECT id, wi_parent_id, 0 AS depth
                      FROM mem_work_items
                      WHERE wi_parent_id = %s::uuid AND project_id = %s
                        AND wi_type != 'use_case'
                      UNION ALL
                      SELECT c.id, c.wi_parent_id, dt.depth + 1
                      FROM mem_work_items c
                      JOIN desc_tree dt ON c.wi_parent_id = dt.id
                      WHERE c.project_id = %s AND c.wi_type != 'use_case'
                        AND dt.depth < 10
                    )
                    SELECT w.id::text, w.wi_id, w.wi_type, w.name, w.summary,
                           w.user_status, w.score_status,
                           w.user_importance, w.score_importance,
                           w.wi_parent_id::text, dt.depth
                    FROM desc_tree dt
                    JOIN mem_work_items w ON w.id = dt.id
                    ORDER BY dt.depth ASC,
                             COALESCE(w.user_importance, w.score_importance, 0) DESC
                """, (uc_id, pid, pid))
                cols = [d[0] for d in cur.description]
                desc = [dict(zip(cols, row)) for row in cur.fetchall()]
        return uc, desc

    def create_version(self, uc_id: str, pid: int, created_by: str = "user",
                       status: str = "active",
                       override_name: Optional[str] = None,
                       override_summary: Optional[str] = None,
                       override_snapshot: Optional[list] = None) -> dict:
        """Snapshot current UC state into mem_wi_versions. Returns {id, version_num}."""
        uc, desc = self._snapshot_uc(uc_id, pid)
        if not uc and override_name is None:
            return {"error": "Use case not found"}
        name    = override_name    or uc.get("name", "")
        summary = override_summary or uc.get("summary", "")
        snapshot = override_snapshot or [
            {k: item.get(k) for k in
             ("id", "wi_id", "wi_type", "name", "summary", "user_status",
              "score_status", "user_importance", "score_importance",
              "wi_parent_id", "depth")}
            for item in desc
        ]
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(version_num),0)+1 FROM mem_wi_versions WHERE uc_id=%s::uuid",
                    (uc_id,)
                )
                next_num = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO mem_wi_versions
                      (project_id, uc_id, version_num, name, summary, snapshot, created_by, status)
                    VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s)
                    RETURNING id::text, version_num
                """, (pid, uc_id, next_num, name, summary,
                      json.dumps(snapshot), created_by, status))
                row = cur.fetchone()
            conn.commit()
        return {"id": row[0], "version_num": row[1], "status": status}

    def get_versions(self, uc_id: str, pid: int) -> list[dict]:
        """List versions for a UC, newest first."""
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id::text, version_num, name, summary, created_by, status,
                           jsonb_array_length(snapshot) AS item_count,
                           created_at
                    FROM mem_wi_versions
                    WHERE uc_id=%s::uuid AND project_id=%s
                    ORDER BY version_num DESC
                """, (uc_id, pid))
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(zip(cols, r))
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            result.append(d)
        return result

    def apply_version(self, version_id: str, uc_id: str, pid: int) -> dict:
        """Apply a version snapshot to live data.

        1. Archive current state as a new version
        2. Update UC name+summary from snapshot
        3. Bulk-update user_importance on items from snapshot order
        4. Mark the applied version as archived
        """
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT name, summary, snapshot FROM mem_wi_versions "
                    "WHERE id=%s::uuid AND uc_id=%s::uuid",
                    (version_id, uc_id)
                )
                row = cur.fetchone()
        if not row:
            return {"error": "Version not found"}
        name, summary, snapshot = row

        # 1. Archive current state
        self.create_version(uc_id, pid, created_by="user", status="archived")

        # 2–4. Apply snapshot
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE mem_work_items SET name=%s, summary=%s, updated_at=NOW() "
                    "WHERE id=%s::uuid AND project_id=%s",
                    (name, summary, uc_id, pid)
                )
                updated = 0
                for idx, item in enumerate(snapshot):
                    priority = len(snapshot) - idx
                    cur.execute(
                        "UPDATE mem_work_items SET user_importance=%s, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (priority, item["id"], pid)
                    )
                    updated += cur.rowcount
                cur.execute(
                    "UPDATE mem_wi_versions SET status='archived' WHERE id=%s::uuid",
                    (version_id,)
                )
            conn.commit()
        return {"applied": True, "items_updated": updated}

    async def ai_summarise_uc(self, uc_id: str, pid: int) -> dict:
        """Call Haiku → rewrite summary + reorder items → save as draft version."""
        uc, desc = self._snapshot_uc(uc_id, pid)
        if not uc:
            return {"error": "Use case not found"}

        items_for_prompt = [
            {
                "id":         d["id"],
                "wi_id":      d.get("wi_id", ""),
                "wi_type":    d["wi_type"],
                "name":       d["name"],
                "summary":    (d.get("summary") or "")[:200],
                "status":     d.get("user_status") or d.get("score_status") or 0,
                "importance": d.get("user_importance") or d.get("score_importance") or 0,
            }
            for d in desc
        ]

        cfg      = self._prompts_cfg().get("summarise", {})
        system   = cfg.get("system", "")
        user_tmpl = cfg.get("user_prompt", "")
        user_msg = user_tmpl.format(
            name=uc.get("name", ""),
            summary=uc.get("summary", ""),
            items_json=json.dumps(items_for_prompt, indent=2),
        )

        raw = await _call_haiku(system, user_msg, max_tokens=2000)
        if not raw:
            return {"error": "AI returned empty response"}
        try:
            cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
            parsed = json.loads(cleaned)
        except Exception:
            return {"error": f"AI returned invalid JSON: {raw[:200]}"}

        new_summary = parsed.get("new_summary", uc.get("summary", ""))
        in_progress = parsed.get("in_progress", [])
        completed   = parsed.get("completed", [])

        all_ordered = in_progress + completed
        id_to_item  = {d["id"]: d for d in desc}
        snapshot: list[dict] = []
        for entry in all_ordered:
            item = id_to_item.get(entry["id"])
            if item:
                snapshot.append({k: item.get(k) for k in
                                  ("id", "wi_id", "wi_type", "name", "summary",
                                   "user_status", "score_status", "user_importance",
                                   "score_importance", "wi_parent_id", "depth")})
        ai_ids = {e["id"] for e in all_ordered}
        for d in desc:
            if d["id"] not in ai_ids:
                snapshot.append({k: d.get(k) for k in
                                  ("id", "wi_id", "wi_type", "name", "summary",
                                   "user_status", "score_status", "user_importance",
                                   "score_importance", "wi_parent_id", "depth")})

        # Delete previous drafts then save new draft
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM mem_wi_versions WHERE uc_id=%s::uuid AND status='draft'",
                    (uc_id,)
                )
            conn.commit()

        ver = self.create_version(
            uc_id, pid, created_by="ai", status="draft",
            override_name=uc.get("name", ""),
            override_summary=new_summary,
            override_snapshot=snapshot,
        )

        return {
            "version_id":       ver["id"],
            "version_num":      ver["version_num"],
            "new_summary":      new_summary,
            "in_progress_count": len(in_progress),
            "completed_count":   len(completed),
            "snapshot":          snapshot,
        }

    def get_stats(self, pid: int) -> dict:
        """Return counts by status and type."""
        if not db.is_available():
            return {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT
                             COUNT(*) FILTER (WHERE wi_id LIKE 'AI%%') AS pending,
                             COUNT(*) FILTER (WHERE wi_id IS NOT NULL
                                               AND wi_id NOT LIKE 'REJ%%'
                                               AND wi_id NOT LIKE 'AI%%') AS approved,
                             COUNT(*) FILTER (WHERE wi_id LIKE 'REJ%%') AS rejected,
                             COUNT(*) FILTER (WHERE wi_type='bug') AS bugs,
                             COUNT(*) FILTER (WHERE wi_type='feature') AS features,
                             COUNT(*) FILTER (WHERE wi_type='task') AS tasks,
                             COUNT(*) FILTER (WHERE wi_type='policy') AS policies,
                             COUNT(*) FILTER (WHERE wi_type='use_case') AS use_cases,
                             COUNT(*) FILTER (WHERE wi_type='requirement') AS requirements,
                             COUNT(*) FILTER (
                               WHERE due_date < CURRENT_DATE
                               AND wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'
                               AND COALESCE(user_status, score_status, 0) < 5
                             ) AS overdue
                           FROM mem_work_items
                           WHERE project_id=%s AND deleted_at IS NULL""",
                        (pid,),
                    )
                    row = cur.fetchone()
                    cols = [d[0] for d in cur.description]
            if row:
                return dict(zip(cols, row))
        except Exception as e:
            log.warning(f"get_stats error: {e}")
        return {}

    def get_pending_mrr_counts(self, pid: int) -> dict:
        """Return unclassified (wi_id IS NULL) counts from each mem_mrr_* table."""
        if not db.is_available():
            return {"pending_prompts": 0, "pending_commits": 0,
                    "pending_messages": 0, "pending_items": 0, "pending_total": 0}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT
                             (SELECT COUNT(*) FROM mem_mrr_prompts  WHERE project_id=%s AND wi_id IS NULL) AS pending_prompts,
                             (SELECT COUNT(*) FROM mem_mrr_commits  WHERE project_id=%s AND wi_id IS NULL) AS pending_commits,
                             (SELECT COUNT(*) FROM mem_mrr_messages WHERE project_id=%s AND wi_id IS NULL) AS pending_messages,
                             (SELECT COUNT(*) FROM mem_mrr_items    WHERE project_id=%s AND wi_id IS NULL) AS pending_items
                        """,
                        (pid, pid, pid, pid),
                    )
                    row = cur.fetchone()
                    cols = [d[0] for d in cur.description]
                    if row:
                        d = dict(zip(cols, row))
                        d["pending_total"] = sum(d.values())
                        return d
        except Exception as e:
            log.warning(f"get_pending_mrr_counts error: {e}")
        return {"pending_prompts": 0, "pending_commits": 0,
                "pending_messages": 0, "pending_items": 0, "pending_total": 0}

    # ── Approval ──────────────────────────────────────────────────────────────

    def approve(self, item_id: str, pid: int) -> dict:
        """Approve a work item: assign wi_id, mark linked mirror rows."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Load the item (must still be a draft AI row)
                    cur.execute(
                        """SELECT wi_type, name, summary, mrr_ids, wi_parent_id::text,
                                  deliveries, delivery_type
                           FROM mem_work_items
                           WHERE id=%s::uuid AND project_id=%s AND wi_id LIKE 'AI%%'""",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "item not found or already approved/rejected"}
                    wi_type, name, summary, mrr_ids, parent_id, deliveries, delivery_type = row

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

            # Compute embedding
            _embed_work_item(item_id, {
                "name": name, "wi_type": wi_type, "summary": summary or "",
                "deliveries": deliveries or "", "delivery_type": delivery_type or "",
            })

            # For use_cases: cascade-approve all pending children, then refresh MD
            if wi_type == "use_case":
                try:
                    self.approve_all_under(item_id, pid)
                except Exception as cascade_err:
                    log.debug(f"approve: cascade to children skipped: {cascade_err}")
                try:
                    self.refresh_md(item_id, pid)
                except Exception as md_err:
                    log.debug(f"approve: refresh_md skipped: {md_err}")

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
                        "WHERE id=%s::uuid AND project_id=%s AND wi_id LIKE 'AI%%'",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "item not found or already approved/rejected"}
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
        """Update editable fields on a work item.

        Date cascade rules:
        - Setting due_date also auto-sets start_date=today (unless start_date provided).
        - Child due_date cannot exceed parent UC due_date.
        - Re-parenting to a non-UC item sets child start_date = parent's due_date.
        - Setting UC due_date caps all active children whose due_date exceeds the new value.
        """
        allowed = {
            "name", "summary", "deliveries", "delivery_type",
            "score_importance", "score_status",
            "user_importance", "user_status",
            "wi_type", "wi_parent_id",
            "due_date", "start_date",
            # pipeline output fields (written by run-pipeline endpoint)
            "acceptance_criteria", "implementation_plan",
            "pipeline_status", "pipeline_run_id",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return {"error": "no valid fields"}
        if not db.is_available():
            return {"error": "db not available"}

        # score_status auto-sync: mark as fully complete when user marks done
        if updates.get("user_status") == "done" and "score_status" not in updates:
            updates["score_status"] = 5
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Load current row (include due_date for conflict detection)
                    cur.execute(
                        "SELECT wi_type, wi_parent_id::text, due_date FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid)
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "item not found"}
                    wi_type, parent_id, current_due_date = row

                    # When due_date is set (not cleared) → also set start_date = today
                    if "due_date" in updates and updates["due_date"]:
                        updates.setdefault("start_date", str(date.today()))

                    # Validate child due_date <= parent UC due_date
                    if "due_date" in updates and updates["due_date"] and wi_type != "use_case" and parent_id:
                        cur.execute(
                            "SELECT due_date FROM mem_work_items WHERE id=%s::uuid",
                            (parent_id,)
                        )
                        parent_row = cur.fetchone()
                        if parent_row and parent_row[0]:
                            new_due = date.fromisoformat(updates["due_date"])
                            if new_due > parent_row[0]:
                                return {"error": f"due_date cannot be after parent due_date ({parent_row[0]})"}

                    # Re-parent: validate same type for non-UC parents; set start_date
                    date_conflict_resolved = False
                    if "wi_parent_id" in updates and updates["wi_parent_id"]:
                        cur.execute(
                            "SELECT wi_type, due_date FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                            (updates["wi_parent_id"], pid)
                        )
                        np = cur.fetchone()
                        # Same-type check only when reparenting to a non-UC item
                        if np and np[0] != "use_case" and np[0] != wi_type:
                            return {"error": f"cannot link items of different types ({wi_type} ≠ {np[0]})"}
                        if np and np[0] != "use_case" and np[1]:
                            parent_due = np[1]  # date object from DB
                            updates["start_date"] = str(parent_due)
                            # Conflict: child has no work window (start_date >= due_date)
                            if current_due_date and current_due_date <= parent_due:
                                new_parent_due = parent_due - timedelta(days=1)
                                cur.execute(
                                    "UPDATE mem_work_items SET due_date=%s, updated_at=NOW() "
                                    "WHERE id=%s::uuid AND project_id=%s",
                                    (str(new_parent_due), updates["wi_parent_id"], pid)
                                )
                                updates["start_date"] = str(new_parent_due)
                                date_conflict_resolved = True

                    # Apply main UPDATE
                    set_clause = ", ".join(f"{k}=%s" for k in updates)
                    vals = list(updates.values()) + [item_id, pid]
                    cur.execute(
                        f"UPDATE mem_work_items SET {set_clause}, updated_at=NOW() "
                        f"WHERE id=%s::uuid AND project_id=%s",
                        vals,
                    )

                    # UC due_date cascade: set ALL direct children to UC due_date
                    cascade_count = 0
                    if "due_date" in updates and wi_type == "use_case" and updates["due_date"]:
                        cur.execute(
                            """UPDATE mem_work_items
                               SET due_date=%s, updated_at=NOW()
                               WHERE project_id=%s AND wi_parent_id=%s::uuid
                                 AND wi_type != 'use_case'
                                 AND wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'""",
                            (updates["due_date"], pid, item_id)
                        )
                        cascade_count = cur.rowcount
                conn.commit()
            result: dict = {"updated": True, "fields": list(updates.keys())}
            if cascade_count:
                result["cascaded_children"] = cascade_count
            if date_conflict_resolved:
                result["date_conflict_resolved"] = True

            # Re-embed if semantic content changed (name, summary, deliveries, delivery_type)
            _embed_fields = {"name", "summary", "deliveries", "delivery_type"}
            if _embed_fields & set(updates.keys()):
                try:
                    with db.conn() as _conn:
                        with _conn.cursor() as _cur:
                            _cur.execute(
                                "SELECT name, wi_type, summary, deliveries, delivery_type, approved_at "
                                "FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                                (item_id, pid),
                            )
                            _row = _cur.fetchone()
                    if _row and _row[5]:  # only re-embed if approved
                        _embed_work_item(item_id, {
                            "name": _row[0] or "", "wi_type": _row[1] or "",
                            "summary": _row[2] or "", "deliveries": _row[3] or "",
                            "delivery_type": _row[4] or "",
                        })
                        result["re_embedded"] = True
                except Exception as _e:
                    log.debug(f"update: re-embed skipped for {item_id}: {_e}")

            return result
        except Exception as e:
            log.warning(f"update({item_id}) error: {e}")
            return {"error": str(e)}

    async def reclassify(self, item_id: str, pid: int) -> dict:
        """Re-run Haiku classification on an existing item's current text.

        Useful when summary has drifted from its original events — refreshes
        wi_type, score_importance, and score_status without touching user_status.
        Returns the updated fields.
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name, wi_type, summary, deliveries, delivery_type, approved_at "
                        "FROM mem_work_items WHERE id=%s::uuid AND project_id=%s AND deleted_at IS NULL",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if not row:
                return {"error": "item not found"}
            name, wi_type, summary, deliveries, delivery_type, approved_at = row
        except Exception as e:
            return {"error": str(e)}

        system = (
            "You are a work item classifier for a software project. "
            "Given an existing work item, re-classify it and return ONLY valid JSON with these fields:\n"
            '{"wi_type": "use_case|feature|bug|task|requirement", '
            '"score_importance": 0-5, "score_status": 0-5}\n\n'
            "score_importance: 0=trivial, 5=critical/blocking\n"
            "score_status: 0=not started, 5=fully done\n"
            "Return no other text."
        )
        user_msg = (
            f"Name: {name or ''}\n"
            f"Current type: {wi_type or ''}\n"
            f"Summary: {(summary or '')[:500]}\n"
            f"Deliveries: {(deliveries or '')[:300]}"
        )
        raw = await _call_haiku(system, user_msg, max_tokens=120)
        if not raw:
            return {"error": "AI returned empty response"}
        try:
            import re as _re
            cleaned = _re.sub(r"```[a-z]*\n?", "", raw.strip()).strip().rstrip("`")
            m = _re.search(r"\{.*?\}", cleaned, _re.DOTALL)
            parsed = json.loads(m.group()) if m else {}
        except Exception:
            return {"error": f"AI returned invalid JSON: {raw[:200]}"}

        new_wi_type      = parsed.get("wi_type", wi_type)
        new_importance   = parsed.get("score_importance")
        new_score_status = parsed.get("score_status")

        valid_types = {"use_case", "feature", "bug", "task", "requirement"}
        if new_wi_type not in valid_types:
            new_wi_type = wi_type

        fields: dict = {"wi_type": new_wi_type}
        if new_importance is not None:
            fields["score_importance"] = int(new_importance)
        if new_score_status is not None:
            fields["score_status"] = int(new_score_status)

        return self.update(item_id, pid, fields)

    def merge(self, source_id: str, target_id: str, pid: int) -> dict:
        """Merge source item into target: append source summary, soft-delete source.

        - Target summary += source name + source summary (as italic footnote)
        - Source gets deleted_at=NOW() and merged_into=target_id
        """
        if source_id == target_id:
            return {"error": "cannot merge item with itself"}
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id::text, name, summary, wi_type FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND deleted_at IS NULL",
                        (source_id, pid),
                    )
                    src = cur.fetchone()
                    cur.execute(
                        "SELECT id::text, name, summary, wi_type FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND deleted_at IS NULL",
                        (target_id, pid),
                    )
                    tgt = cur.fetchone()
                    if not src:
                        return {"error": "source item not found"}
                    if not tgt:
                        return {"error": "target item not found"}
                    if src[3] != tgt[3]:
                        return {"error": f"cannot merge items of different types ({src[3]} ≠ {tgt[3]})"}

                    src_name, src_summary = src[1] or "", src[2] or ""
                    tgt_summary          = tgt[2] or ""

                    # Append source content as italic footnote to target summary
                    appendix = f"_Merged from **{src_name}**"
                    if src_summary.strip():
                        appendix += f": {src_summary.strip()}"
                    appendix += "_"
                    merged_summary = (tgt_summary + "\n\n" + appendix).strip()

                    cur.execute(
                        "UPDATE mem_work_items SET summary=%s, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (merged_summary, target_id, pid),
                    )
                    cur.execute(
                        "UPDATE mem_work_items "
                        "SET merged_into=%s::uuid, deleted_at=NOW(), updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (target_id, source_id, pid),
                    )
                conn.commit()
            return {"merged": True, "target_id": target_id, "source_id": source_id}
        except Exception as e:
            log.warning(f"merge({source_id}->{target_id}) error: {e}")
            return {"error": str(e)}

    def unmerge(self, source_id: str, pid: int) -> dict:
        """Partial undo of a merge: restore the soft-deleted source item.

        The target's summary is kept as-is (the merged footnote stays).
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id::text, merged_into::text FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND merged_into IS NOT NULL",
                        (source_id, pid),
                    )
                    src = cur.fetchone()
                    if not src:
                        return {"error": "source item not found or not merged"}
                    target_id = src[1]

                    cur.execute(
                        "UPDATE mem_work_items "
                        "SET deleted_at=NULL, merged_into=NULL, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (source_id, pid),
                    )
                conn.commit()
            return {"unmerged": True, "source_id": source_id, "target_id": target_id}
        except Exception as e:
            log.warning(f"unmerge({source_id}) error: {e}")
            return {"error": str(e)}

    def reorder_items(self, pid: int, items: list[dict]) -> dict:
        """Bulk-update user_importance for a list of items (drag-to-reorder).

        Each dict in items must have {id: str, user_importance: int}.
        """
        if not items:
            return {"updated": 0}
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for entry in items:
                        iid = entry.get("id", "")
                        imp = int(entry.get("user_importance", 0))
                        if not iid:
                            continue
                        cur.execute(
                            "UPDATE mem_work_items SET user_importance=%s, updated_at=NOW() "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (imp, iid, pid),
                        )
                conn.commit()
            return {"updated": len(items)}
        except Exception as e:
            log.warning(f"reorder_items error: {e}")
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
                        "WHERE id=%s::uuid AND project_id=%s AND wi_id LIKE 'AI%%'",
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
        """Approve all pending (AI-prefixed) items under a parent — recursively."""
        if not db.is_available():
            return {"error": "db not available"}
        # Collect ALL descendants (recursive) with AI-prefixed wi_id
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """WITH RECURSIVE tree AS (
                             SELECT id::text, wi_id
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id::text, w.wi_id
                             FROM mem_work_items w
                             JOIN tree d ON w.wi_parent_id = d.id::uuid
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                           )
                           SELECT id FROM tree
                           WHERE wi_id LIKE 'AI%%'""",
                        (parent_id, pid, pid),
                    )
                    pending_ids = [r[0] for r in cur.fetchall()]
        except Exception as e:
            return {"error": str(e)}

        approved = []
        errors   = []
        for item_id in pending_ids:
            result = self.approve(item_id, pid)
            if "error" in result:
                errors.append(result)
            else:
                approved.append(result)
        return {"approved": len(approved), "errors": errors}

    # ── MD file methods ───────────────────────────────────────────────────────

    def _status_label(self, score_status: int) -> str:
        if not score_status or score_status == 0:
            return "requirement"
        if score_status >= 5:
            return "done"
        return "in_progress"

    def get_md(self, item_id: str, pid: int) -> str:
        """Render a use_case work item as clean Markdown (no HTML comment tags).

        Uses a recursive CTE to capture all descendants (not just direct children).
        Format is designed to be human-editable — save_md() parses it back to DB.
        """
        if not db.is_available():
            return ""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT wi_id, name, summary, score_status, created_at, updated_at
                           FROM mem_work_items
                           WHERE id=%s::uuid AND project_id=%s""",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return ""
                    wi_id, name, summary, score_status, created_at, updated_at = row
                    created_str = created_at.strftime("%Y-%m-%d") if created_at else ""
                    updated_str = updated_at.strftime("%Y-%m-%d") if updated_at else ""

                    # Recursive CTE — all descendants (direct + nested), excluding deleted/rejected
                    cur.execute(
                        """WITH RECURSIVE descendants AS (
                             SELECT id, wi_id, wi_type, name, summary,
                                    COALESCE(user_status, score_status, 0) AS eff_status
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.wi_type, w.name, w.summary,
                                    COALESCE(w.user_status, w.score_status, 0)
                             FROM mem_work_items w
                             JOIN descendants d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                           )
                           SELECT wi_id, wi_type, name, summary, eff_status
                           FROM descendants
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'
                           ORDER BY wi_id""",
                        (item_id, pid, pid),
                    )
                    cols = [d[0] for d in cur.description]
                    all_items = [dict(zip(cols, r)) for r in cur.fetchall()]

            _TYPE_LABEL = {
                "bug": "bug", "feature": "feature", "task": "task",
                "policy": "policy", "requirement": "requirement", "use_case": "use case",
            }
            _TYPE_ORDER = ["bug", "feature", "task", "requirement", "policy"]

            # Separate requirements from other items
            req_items  = [c for c in all_items if c["wi_type"] == "requirement"]
            work_items = [c for c in all_items if c["wi_type"] != "requirement"]

            done_items = [c for c in work_items if (c["eff_status"] or 0) >= 5]
            open_items = [c for c in work_items if (c["eff_status"] or 0) < 5]

            # Build type-count summary for header line (all items including requirements)
            type_counts: dict[str, int] = {}
            for c in all_items:
                type_counts[c["wi_type"]] = type_counts.get(c["wi_type"], 0) + 1
            stat_parts = [
                f"{type_counts[t]} {_TYPE_LABEL.get(t, t)}{'s' if type_counts[t] != 1 else ''}"
                for t in _TYPE_ORDER if t in type_counts
            ]
            stats_str = " · ".join(stat_parts) if stat_parts else "no items"

            def _item_block(ch: dict) -> list[str]:
                """#### WKID — title (no type line — already grouped by ### header)."""
                wid   = ch["wi_id"] or "pending"
                lines = [f"#### {wid} — {ch['name']}"]
                if ch.get("summary"):
                    lines += ["", ch["summary"]]
                return lines

            def _group_section(items: list) -> list[str]:
                """Group items by type, skip requirements (they go in ## Requirements)."""
                _ORDER = ["bug", "feature", "task", "policy"]
                _SKIP  = {"requirement", "use_case"}
                by_type: dict = {}
                for c in items:
                    if c["wi_type"] not in _SKIP:
                        by_type.setdefault(c["wi_type"], []).append(c)
                lines: list[str] = []
                for t in _ORDER + [k for k in by_type if k not in _ORDER]:
                    grp = by_type.get(t, [])
                    if not grp:
                        continue
                    t_plural = _TYPE_LABEL.get(t, t).capitalize() + "s"
                    if lines:                     # blank between type groups
                        lines.append("")
                    lines += [f"### {t_plural} ({len(grp)})", ""]
                    for i, ch in enumerate(grp):
                        lines += _item_block(ch)
                        if i < len(grp) - 1:     # blank between items, not after last
                            lines.append("")
                return lines

            # Build ## Requirements section
            req_lines: list[str] = []
            if req_items:
                for r in req_items:
                    req_lines += _item_block(r)
                    req_lines.append("")
            else:
                req_lines += ["_Add requirements here_", ""]

            L: list[str] = [
                f"# {wi_id or 'pending'} — {name}",
                "",
                f"created: {created_str} | updated: {updated_str} | {stats_str}",
                "",
                "## Summary",
                "",
                summary or "_No summary yet. Click ⟳ Summarise in the Use Cases tab to generate._",
                "",
                "## Requirements",
                "",
            ]
            L += req_lines

            L += ["---", "", f"## Completed ({len(done_items)})", ""]

            if done_items:
                L += _group_section(done_items)
                L.append("")
            else:
                L += ["_No completed items yet._", ""]

            L += ["---", "", f"## Open Items ({len(open_items)})", ""]

            if open_items:
                L += _group_section(open_items)
            else:
                L += ["_No open items._"]

            return "\n".join(L)
        except Exception as e:
            log.warning(f"get_md({item_id}) error: {e}")
            return ""

    @staticmethod
    def _parse_md_items(content: str) -> dict[str, dict]:
        """Parse #### WKID — title / *type* / summary blocks from MD content.

        Returns {wi_id: {'name': str, 'summary': str}}.
        The *type* line is skipped (type is authoritative in DB).
        """
        items: dict[str, dict] = {}
        current_id: Optional[str] = None
        current_name: str = ""
        current_lines: list[str] = []
        skip_type_line: bool = False

        for line in content.splitlines():
            # Stop accumulating at section boundaries
            if line.startswith("## ") or line.startswith("---"):
                if current_id:
                    items[current_id] = {
                        "name": current_name,
                        "summary": "\n".join(current_lines).strip(),
                    }
                current_id = None
                current_lines = []
                skip_type_line = False
                continue
            m = re.match(r'^#### (\S+) — (.+)$', line)
            if m:
                if current_id:
                    items[current_id] = {
                        "name": current_name,
                        "summary": "\n".join(current_lines).strip(),
                    }
                current_id   = m.group(1)
                current_name = m.group(2).strip()
                current_lines = []
                skip_type_line = True
                continue
            if skip_type_line:
                # Skip the *type* line immediately after the header
                if re.match(r'^\*\w+\*$', line.strip()):
                    skip_type_line = False
                    continue
                if line.strip() == "":
                    skip_type_line = False  # blank line after header without *type* — stop skipping
            if current_id:
                current_lines.append(line)

        if current_id:
            items[current_id] = {
                "name": current_name,
                "summary": "\n".join(current_lines).strip(),
            }
        return items

    def save_md(self, item_id: str, pid: int, content: str) -> dict:
        """Parse MD content and persist changes to DB + file.

        Syncs:
          - ## Summary section → UC summary field
          - #### WKID — title blocks → child name + summary
          - Items removed from MD → marked deleted_at=NOW() (approved) or deleted (pending)

        The header info line (created/updated/stats) is read-only — changes ignored.
        The ## Requirements section lives in the file only (no DB column).
        """
        if not db.is_available():
            return {"error": "db not available"}

        updated = 0
        deleted_count = 0
        embedded = 0
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # 1. UC summary
                    summary_match = re.search(
                        r'## Summary\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL
                    )
                    if summary_match:
                        new_summary = summary_match.group(1).strip()
                        if new_summary.startswith("_No summary"):
                            new_summary = ""
                        cur.execute(
                            "UPDATE mem_work_items SET summary=%s, updated_at=NOW() "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (new_summary, item_id, pid),
                        )
                        if cur.rowcount:
                            updated += 1

                    # 2. Parse all #### WKID blocks from the file
                    md_items = self._parse_md_items(content)

                    # 3. Load all DB children (non-deleted, non-rejected)
                    cur.execute(
                        """WITH RECURSIVE tree AS (
                             SELECT id, wi_id, wi_type, name, summary
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.wi_type, w.name, w.summary
                             FROM mem_work_items w JOIN tree d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                           )
                           SELECT id::text, wi_id, wi_type, name, summary
                           FROM tree
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'""",
                        (item_id, pid, pid),
                    )
                    db_children = {
                        r[1]: {"id": r[0], "wi_type": r[2], "name": r[3], "summary": r[4]}
                        for r in cur.fetchall()
                    }

                    # 4. Update items present in MD, mark missing ones as deleted
                    for wi_id_key, db_child in db_children.items():
                        if wi_id_key in md_items:
                            md = md_items[wi_id_key]
                            new_name    = md["name"]
                            new_summary = md["summary"]
                            if new_name != db_child["name"] or new_summary != (db_child["summary"] or ""):
                                cur.execute(
                                    """UPDATE mem_work_items
                                       SET name=%s, summary=%s, updated_at=NOW()
                                       WHERE wi_id=%s AND project_id=%s""",
                                    (new_name, new_summary, wi_id_key, pid),
                                )
                                if cur.rowcount:
                                    updated += 1
                        else:
                            # Item removed from MD — soft-delete or hard-delete
                            if wi_id_key.startswith("AI"):
                                cur.execute(
                                    "DELETE FROM mem_work_items WHERE wi_id=%s AND project_id=%s",
                                    (wi_id_key, pid),
                                )
                            else:
                                cur.execute(
                                    "UPDATE mem_work_items SET deleted_at=NOW(), updated_at=NOW() "
                                    "WHERE wi_id=%s AND project_id=%s",
                                    (wi_id_key, pid),
                                )
                            deleted_count += 1

                conn.commit()

            # Re-embed UC (summary may have changed) — fire-and-forget
            try:
                with db.conn() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute(
                            "SELECT name, wi_type, summary FROM mem_work_items "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (item_id, pid),
                        )
                        uc_row = cur2.fetchone()
                if uc_row:
                    _embed_work_item(item_id, {
                        "name": uc_row[0], "wi_type": uc_row[1], "summary": uc_row[2] or ""
                    })
                    embedded += 1
            except Exception:
                pass

            # Write file as-is (requirements section preserved in file)
            self._write_md_file(item_id, pid, content)

            return {"updated": updated, "deleted": deleted_count, "embedded": embedded}
        except Exception as e:
            log.warning(f"save_md({item_id}) error: {e}")
            return {"error": str(e)}

    def refresh_md(self, item_id: str, pid: int) -> str:
        """Ensure the MD file exists. Generates from DB only if file not yet created.

        If the file already exists (user has edited it), returns the existing content
        without overwriting user's changes.
        """
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if row:
                slug    = _use_case_slug(row[0])
                uc_path = Path(settings.workspace_dir) / self.project / "documents" / "use_cases" / f"{slug}.md"
                if uc_path.exists():
                    return uc_path.read_text(encoding="utf-8")
        except Exception:
            pass
        # File doesn't exist yet — generate fresh from DB and write
        content = self.get_md(item_id, pid)
        if content:
            self._write_md_file(item_id, pid, content)
        return content

    def _write_md_file(self, item_id: str, pid: int, content: str) -> None:
        """Write MD content to workspace/{project}/documents/use_cases/{slug}.md.

        Uses workspace_dir (same root the Documents API serves from) so the file
        is immediately visible in the Documents view after refresh_md().
        """
        try:
            # Get use_case name to derive slug
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if not row:
                return
            slug   = _use_case_slug(row[0])
            uc_dir = Path(settings.workspace_dir) / self.project / "documents" / "use_cases"
            uc_dir.mkdir(parents=True, exist_ok=True)
            (uc_dir / f"{slug}.md").write_text(content, encoding="utf-8")
            log.debug(f"_write_md_file({item_id}): wrote {slug}.md → {uc_dir}")
        except Exception as e:
            log.debug(f"_write_md_file({item_id}) error: {e}")

    def _move_md_file(self, name: str, from_folder: str, to_folder: str) -> None:
        """Move a use-case MD file between documents sub-folders."""
        try:
            slug    = _use_case_slug(name)
            base    = Path(settings.workspace_dir) / self.project / "documents"
            src     = base / from_folder / f"{slug}.md"
            dst_dir = base / to_folder
            dst_dir.mkdir(parents=True, exist_ok=True)
            if src.exists():
                src.rename(dst_dir / f"{slug}.md")
        except Exception as e:
            log.debug(f"_move_md_file({name}) error: {e}")

    def complete_use_case(self, item_id: str, pid: int) -> dict:
        """Mark a use case as completed.

        Validates all recursive descendants have eff_status >= 5, then sets
        completed_at = NOW() and moves the MD file to documents/completed/.
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT wi_id, name FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND wi_type='use_case'",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "use case not found"}
                    wi_id, name = row

                    # Check all descendants are done
                    cur.execute(
                        """WITH RECURSIVE tree AS (
                             SELECT id, wi_id, name, COALESCE(user_status, score_status, 0) AS eff
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.name, COALESCE(w.user_status, w.score_status, 0)
                             FROM mem_work_items w JOIN tree d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                           )
                           SELECT name FROM tree
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%' AND eff < 5
                           LIMIT 10""",
                        (item_id, pid, pid),
                    )
                    incomplete = [r[0] for r in cur.fetchall()]
                    if incomplete:
                        return {
                            "error": "not all items completed",
                            "incomplete": incomplete,
                        }

                    cur.execute(
                        "UPDATE mem_work_items SET completed_at=NOW(), updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                conn.commit()

            self._move_md_file(name, "use_cases", "completed")
            return {"completed": True, "wi_id": wi_id}
        except Exception as e:
            log.warning(f"complete_use_case({item_id}) error: {e}")
            return {"error": str(e)}

    def reopen_use_case(self, item_id: str, pid: int) -> dict:
        """Reopen a completed use case — clears completed_at, moves MD back."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "use case not found"}
                    name = row[0]
                    cur.execute(
                        "UPDATE mem_work_items SET completed_at=NULL, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                conn.commit()
            self._move_md_file(name, "completed", "use_cases")
            return {"reopened": True}
        except Exception as e:
            log.warning(f"reopen_use_case({item_id}) error: {e}")
            return {"error": str(e)}

    def get_completed_use_cases(self, pid: int) -> list[dict]:
        """Return all completed use cases with summary, dates, total_days."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT id::text, wi_id, name, summary,
                                  start_date, completed_at,
                                  CASE WHEN start_date IS NOT NULL
                                       THEN (completed_at::date - start_date)
                                       ELSE NULL END AS total_days
                           FROM mem_work_items
                           WHERE project_id=%s AND wi_type='use_case'
                             AND completed_at IS NOT NULL
                           ORDER BY completed_at DESC""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(zip(cols, r))
                for k in ("start_date", "completed_at"):
                    if d.get(k):
                        d[k] = d[k].isoformat() if hasattr(d[k], 'isoformat') else str(d[k])
                if d.get("total_days") is not None:
                    d["total_days"] = int(d["total_days"])
                slug = _use_case_slug(d["name"])
                d["md_path"] = f"completed/{slug}.md"
                result.append(d)
            return result
        except Exception as e:
            log.warning(f"get_completed_use_cases error: {e}")
            return []

    # ── Direct create ─────────────────────────────────────────────────────────

    def create_item(self, pid: int, fields: dict) -> dict:
        """Insert a work item directly (wi_id=NULL). Returns the row as dict."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            wi_type = fields.get("wi_type", "task")
            if wi_type not in _TYPE_SEQ:
                wi_type = "task"
            parent_id = fields.get("wi_parent_id") or None
            if parent_id and not _UUID_RE.match(str(parent_id)):
                parent_id = None

            with db.conn() as conn:
                with conn.cursor() as cur:
                    item_id = _insert_wi(cur, {
                        "wi_type":         wi_type,
                        "item_level":      3 if wi_type == "use_case" else 2,
                        "name":            (fields.get("name") or "")[:200],
                        "summary":         fields.get("summary") or "",
                        "deliveries":      fields.get("deliveries") or "",
                        "delivery_type":   fields.get("delivery_type") or "",
                        "score_importance": int(fields.get("score_importance", 2)),
                        "score_status":    int(fields.get("score_status", 0)),
                        "mrr_ids":         {},
                    }, pid, parent_id)
                conn.commit()
            return {"id": item_id, "wi_type": wi_type, "name": fields.get("name", "")}
        except Exception as e:
            log.warning(f"create_item error: {e}")
            return {"error": str(e)}

    def reset_pending(self, pid: int) -> dict:
        """Delete all AI-temp draft rows and reset mirror-table wi_id references.

        Clears all unapproved classification work (wi_id LIKE 'AI%') from
        mem_work_items and resets mem_mrr_* wi_id fields so events can be
        re-classified from scratch on the next classify run.
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            deleted_wi = 0
            reset_counts: dict = {}
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Delete draft work items
                    cur.execute(
                        "DELETE FROM mem_work_items WHERE project_id=%s AND wi_id LIKE 'AI%%'",
                        (pid,),
                    )
                    deleted_wi = cur.rowcount

                    # Reset mem_mrr_* so all non-approved events are re-classified
                    for src, tbl in _TABLE.items():
                        cur.execute(
                            f"UPDATE {tbl} SET wi_id=NULL "
                            f"WHERE project_id=%s AND wi_id IS NOT NULL AND wi_id != 'SKIP' "
                            f"AND wi_id NOT LIKE 'REJ%%'",
                            (pid,),
                        )
                        reset_counts[src] = cur.rowcount
                conn.commit()
            return {"deleted_work_items": deleted_wi, "reset_mrr": reset_counts}
        except Exception as e:
            log.warning(f"reset_pending error: {e}")
            return {"error": str(e)}
