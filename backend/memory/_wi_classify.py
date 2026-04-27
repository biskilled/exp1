"""_wi_classify.py — Classification pipeline mixin for MemoryWorkItems.

Contains all methods related to fetching pending events, grouping them,
calling the LLM classifier, and saving results to DB.

Mixed into MemoryWorkItems via class inheritance.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from core.database import db
from memory._wi_helpers import (
    _TABLE, _TYPE_SEQ, _call_haiku, _count_tokens,
    _insert_wi, _update_item_tags, _rollup_uc_tags,
)
from memory.memory_code_parser import get_file_hotspots

log = logging.getLogger(__name__)


class _ClassifyMixin:
    """Classification pipeline methods — fetching, grouping, calling Haiku, saving."""

    # ── Threshold trigger (backward-compat with route_git / route_chat) ────────

    async def check_and_trigger(self, source_type: str) -> None:
        """Trigger auto-classification if mode=threshold and token count is met.

        In mode=manual (default) this is a no-op.
        """
        if self._mode() != "threshold":  # type: ignore[attr-defined]
            return
        pid = self._get_project_id()  # type: ignore[attr-defined]
        if not pid:
            return
        count = self._pending_count(pid, source_type)
        threshold = self._threshold(source_type)  # type: ignore[attr-defined]
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
        """Return all pending (wi_id IS NULL) rows from every mem_mrr_* table.

        Applies a configurable event horizon (project.yaml work_items.event_horizon_days,
        default 90) to exclude very old events from classification.
        """
        result: dict[str, list[dict]] = {
            "prompts": [], "commits": [], "messages": [], "items": []
        }
        if not db.is_available():
            return result
        horizon_days = int(self._config().get("event_horizon_days", 90))  # type: ignore[attr-defined]
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
                             AND created_at > NOW() - INTERVAL '1 day' * %s
                           ORDER BY created_at ASC
                           LIMIT 200""",
                        (pid, horizon_days),
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
                             AND c.created_at > NOW() - INTERVAL '1 day' * %s
                           ORDER BY c.created_at ASC
                           LIMIT 100""",
                        (pid, horizon_days),
                    )
                    cols = [d[0] for d in cur.description]
                    commit_hashes: list[str] = []
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["commits"].append(d)
                        commit_hashes.append(d["commit_hash"])

                    # Single query: file paths + symbol summaries for all commits
                    if commit_hashes:
                        cur.execute(
                            """SELECT commit_hash, file_path, class_name, method_name,
                                      LEFT(llm_summary, 120) AS llm_summary
                               FROM mem_mrr_commits_code
                               WHERE commit_hash = ANY(%s)
                               ORDER BY commit_hash, file_path
                               LIMIT 300""",
                            (commit_hashes,),
                        )
                        hash_to_files: dict[str, list[str]] = {}
                        hash_to_symbols: dict[str, list[dict]] = {}
                        for chash, fpath, cls, meth, sym_sum in cur.fetchall():
                            hash_to_files.setdefault(chash, []).append(fpath)
                            if sym_sum:
                                hash_to_symbols.setdefault(chash, []).append({
                                    "file_path": fpath,
                                    "class_name": cls or "",
                                    "method_name": meth or "",
                                    "summary": sym_sum,
                                })

                        # Attach hotspot data for files touched by each commit
                        all_files = list({fp for fps in hash_to_files.values() for fp in fps})
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

                        # Attach symbol summaries
                        for commit in result["commits"]:
                            syms = hash_to_symbols.get(commit["commit_hash"])
                            if syms:
                                commit["_symbol_summaries"] = syms

                    # Messages
                    cur.execute(
                        """SELECT id::text, platform, channel,
                                  LEFT(messages::text, 800) AS messages_text,
                                  tags, created_at
                           FROM mem_mrr_messages
                           WHERE project_id=%s AND wi_id IS NULL
                             AND created_at > NOW() - INTERVAL '1 day' * %s
                           ORDER BY created_at ASC
                           LIMIT 50""",
                        (pid, horizon_days),
                    )
                    cols = [d[0] for d in cur.description]
                    for row in cur.fetchall():
                        d = dict(zip(cols, row))
                        d["created_at"] = d["created_at"].isoformat() if d["created_at"] else None
                        result["messages"].append(d)

                    # Items — same event horizon as other sources
                    cur.execute(
                        """SELECT id::text, item_type, title,
                                  LEFT(summary, 800) AS summary,
                                  tags, created_at
                           FROM mem_mrr_items
                           WHERE project_id=%s AND wi_id IS NULL
                             AND created_at > NOW() - INTERVAL '1 day' * %s
                           ORDER BY created_at ASC
                           LIMIT 50""",
                        (pid, horizon_days),
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

        All event types are interleaved chronologically. Each batch stays
        under ~3000 tokens so LLM responses fit in 8000 tokens.
        """
        MAX_TOKENS = 3000

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
            symbols = c.get("_symbol_summaries") or []
            if symbols:
                lines.append("  [CHANGED SYMBOLS]")
                for s in symbols[:8]:
                    if s.get("method_name"):
                        label = f"{s['class_name']}.{s['method_name']}" if s.get("class_name") else s["method_name"]
                    else:
                        label = s.get("class_name") or s.get("file_path", "")
                    lines.append(f"    {label}: {s['summary'][:120]}")
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
        run to attach children to use cases already created by earlier groups.
        """
        if not db.is_available():
            return "(no existing work items)"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
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
        cfg = self._prompts_cfg().get("classification", {})  # type: ignore[attr-defined]
        system = cfg.get("system", "Classify development events into work items.")
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
        text = raw.strip()
        if "```" in text:
            text = re.sub(r"```[a-z]*\n?", "", text).strip()

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
            mrr = raw_item.get("mrr_ids") or {}
            merged_mrr = {
                "prompts":  list(set(mrr.get("prompts")  or [])),
                "commits":  list(set(mrr.get("commits")  or [])),
                "messages": list(set(mrr.get("messages") or [])),
                "items":    list(set(mrr.get("items")    or [])),
            }
            valid.append({
                "wi_type":               wi_type,
                "item_level":            int(raw_item.get("item_level", 2)),
                "name":                  (raw_item.get("name") or "")[:200],
                "existing_wi_id":        (raw_item.get("existing_wi_id") or "").strip(),
                "summary":               raw_item.get("summary") or "",
                "deliveries":            raw_item.get("deliveries") or "",
                "delivery_type":         raw_item.get("delivery_type") or "",
                "score_importance":      min(5, max(0, int(raw_item.get("score_importance", 0)))),
                "score_status":          min(5, max(0, int(raw_item.get("score_status", 0)))),
                "mrr_ids":               merged_mrr,
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

        Returns (saved_items, updated_uc_map).
        """
        if not items or not db.is_available():
            return [], dict(existing_uc_map or {})
        uc_map: dict[str, str] = dict(existing_uc_map or {})
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
                                continue
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

        Deletes existing AI-temp draft rows, then re-classifies all unprocessed
        events from scratch. Approved rows (real IDs) are never touched.

        Returns {"classified": N, "groups": M, "items": [...]}
        """
        if max_use_cases is None or max_use_cases <= 0:
            max_use_cases = int(
                self._prompts_cfg().get("classification", {}).get("max_use_cases", 8)  # type: ignore[attr-defined]
            )
        pid = self._get_project_id()  # type: ignore[attr-defined]
        if not pid:
            return {"classified": 0, "groups": 0, "items": [], "error": "project not found"}

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
        uc_map: dict[str, str] = {}
        for idx, group in enumerate(groups, 1):
            try:
                log.info(f"classify: processing group {idx}/{len(groups)}")
                existing_ctx = self._load_existing_context(pid)
                items = await self._classify_group(group, existing_ctx, max_use_cases)
                if items:
                    saved, uc_map = self._save_classifications(items, pid, uc_map)
                    _update_item_tags(saved, tag_lookup)
                    all_items.extend(saved)
                    log.info(f"classify: group {idx} → {len(saved)} items saved")
            except Exception as e:
                log.warning(f"classify: group {idx} error: {e}")

        uc_ids = [item["id"] for item in all_items if item.get("wi_type") == "use_case" and item.get("id")]
        if uc_ids:
            _rollup_uc_tags(pid, uc_ids)

        return {
            "classified":    len(all_items),
            "groups":        len(groups),
            "items":         all_items,
            "events_in":     total_events,
            "max_use_cases": max_use_cases,
        }
