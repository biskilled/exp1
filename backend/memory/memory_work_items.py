"""
memory_work_items.py — DB-first work item classification pipeline.

Classification and markdown file management are split into mixin modules:
  _wi_classify.py  — classify(), _fetch_pending_events(), _group_events(), etc.
  _wi_markdown.py  — get_md(), save_md(), complete_use_case(), etc.
  _wi_helpers.py   — shared module-level constants and helper functions

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
from memory._wi_classify import _ClassifyMixin
from memory._wi_helpers import (
    _TABLE, _TYPE_SEQ, _UUID_RE, _WI_PROMPTS_PATH,
    _call_haiku, _embed_work_item, _generate_wi_id,
    _insert_wi, _merge_tags, _rollup_uc_tags,
    _update_item_tags, _use_case_slug,
)
from memory._wi_markdown import _MarkdownMixin

log = logging.getLogger(__name__)



# ─────────────────────────────────────────────────────────────────────────────
# Main class
# ─────────────────────────────────────────────────────────────────────────────

class MemoryWorkItems(_ClassifyMixin, _MarkdownMixin):
    """DB-first work item classification pipeline.

    Classification pipeline: see memory/_wi_classify.py (_ClassifyMixin)
    Markdown file management: see memory/_wi_markdown.py (_MarkdownMixin)
    Shared helpers: see memory/_wi_helpers.py
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

    # NOTE: classify(), check_and_trigger(), _fetch_pending_events(), etc.
    # are inherited from _ClassifyMixin (memory/_wi_classify.py).

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

                    # Mark linked mirror rows (batch updates — one query per table)
                    mrr = mrr_ids if isinstance(mrr_ids, dict) else {}
                    prompt_ids = [p for p in mrr.get("prompts") or [] if _UUID_RE.match(str(p))]
                    if prompt_ids:
                        cur.execute(
                            "UPDATE mem_mrr_prompts SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (new_wi_id, prompt_ids, pid),
                        )
                    commit_hashes = mrr.get("commits") or []
                    if commit_hashes:
                        cur.execute(
                            "UPDATE mem_mrr_commits SET wi_id=%s WHERE commit_hash = ANY(%s) AND project_id=%s",
                            (new_wi_id, commit_hashes, pid),
                        )
                    msg_ids = [m for m in mrr.get("messages") or [] if _UUID_RE.match(str(m))]
                    if msg_ids:
                        cur.execute(
                            "UPDATE mem_mrr_messages SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (new_wi_id, msg_ids, pid),
                        )
                    item_ids = [i for i in mrr.get("items") or [] if _UUID_RE.match(str(i))]
                    if item_ids:
                        cur.execute(
                            "UPDATE mem_mrr_items SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (new_wi_id, item_ids, pid),
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
                    # Mark linked mirror rows so they aren't re-classified (batch updates)
                    mrr = mrr_ids if isinstance(mrr_ids, dict) else {}
                    prompt_ids = [p for p in mrr.get("prompts") or [] if _UUID_RE.match(str(p))]
                    if prompt_ids:
                        cur.execute(
                            "UPDATE mem_mrr_prompts SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (rej_id, prompt_ids, pid),
                        )
                    commit_hashes = mrr.get("commits") or []
                    if commit_hashes:
                        cur.execute(
                            "UPDATE mem_mrr_commits SET wi_id=%s WHERE commit_hash = ANY(%s) AND project_id=%s",
                            (rej_id, commit_hashes, pid),
                        )
                    msg_ids = [m for m in mrr.get("messages") or [] if _UUID_RE.match(str(m))]
                    if msg_ids:
                        cur.execute(
                            "UPDATE mem_mrr_messages SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (rej_id, msg_ids, pid),
                        )
                    item_ids = [i for i in mrr.get("items") or [] if _UUID_RE.match(str(i))]
                    if item_ids:
                        cur.execute(
                            "UPDATE mem_mrr_items SET wi_id=%s WHERE id = ANY(%s::uuid[]) AND project_id=%s",
                            (rej_id, item_ids, pid),
                        )
                conn.commit()
            return {"wi_id": rej_id, "item_id": item_id}
        except Exception as e:
            log.warning(f"reject({item_id}) error: {e}")
            return {"error": str(e)}

    def _apply_date_rules(
        self,
        cur,
        pid: int,
        wi_type: str,
        parent_id: Optional[str],
        current_due_date,
        updates: dict,
    ) -> Optional[dict]:
        """Validate + apply date cascade rules, mutating `updates` in place.

        Returns an error dict if validation fails, else None.
        Sets updates['_date_conflict_resolved'] = True when a conflict is auto-resolved.
        """
        # Setting due_date (not clearing) → also set start_date = today
        if updates.get("due_date"):
            updates.setdefault("start_date", str(date.today()))

        # Child due_date cannot exceed parent UC's due_date
        if updates.get("due_date") and wi_type != "use_case" and parent_id:
            cur.execute(
                "SELECT due_date FROM mem_work_items WHERE id=%s::uuid",
                (parent_id,),
            )
            parent_row = cur.fetchone()
            if parent_row and parent_row[0]:
                new_due = date.fromisoformat(updates["due_date"])
                if new_due > parent_row[0]:
                    return {"error": f"due_date cannot be after parent due_date ({parent_row[0]})"}

        # Re-parent: same-type check + auto-set start_date from new parent
        if updates.get("wi_parent_id"):
            cur.execute(
                "SELECT wi_type, due_date FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                (updates["wi_parent_id"], pid),
            )
            np = cur.fetchone()
            if np and np[0] != "use_case" and np[0] != wi_type:
                return {"error": f"cannot link items of different types ({wi_type} ≠ {np[0]})"}
            if np and np[0] != "use_case" and np[1]:
                parent_due = np[1]
                updates["start_date"] = str(parent_due)
                # Auto-resolve: child would have no work window → pull parent back 1 day
                if current_due_date and current_due_date <= parent_due:
                    new_parent_due = parent_due - timedelta(days=1)
                    cur.execute(
                        "UPDATE mem_work_items SET due_date=%s, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (str(new_parent_due), updates["wi_parent_id"], pid),
                    )
                    updates["start_date"] = str(new_parent_due)
                    updates["_date_conflict_resolved"] = True

        return None

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

                    # Apply date rules (validation + cascade); may modify `updates` in place
                    date_conflict_resolved = False
                    date_err = self._apply_date_rules(
                        cur, pid, wi_type, parent_id, current_due_date, updates
                    )
                    if date_err:
                        return date_err
                    date_conflict_resolved = updates.pop("_date_conflict_resolved", False)

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
                    log.warning(f"update: re-embed failed for {item_id} — semantic search may be stale: {_e}")

            return result
        except Exception as e:
            log.warning(f"update({item_id}) error: {e}")
            return {"error": str(e)}

    async def reclassify(self, item_id: str, pid: int) -> dict:
        """Re-run Haiku classification on an existing item's current text.

        Useful when summary has drifted from its original events — refreshes
        wi_type, score_importance, and score_status without touching user_status.
        Passes user_status to Haiku so score_status reflects actual progress.
        Returns the updated fields.
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name, wi_type, summary, deliveries, delivery_type, "
                        "approved_at, user_status "
                        "FROM mem_work_items WHERE id=%s::uuid AND project_id=%s AND deleted_at IS NULL",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if not row:
                return {"error": "item not found"}
            name, wi_type, summary, deliveries, delivery_type, approved_at, user_status = row
        except Exception as e:
            return {"error": str(e)}

        # Map user_status to score_status hint so Haiku aligns AI score with reality
        _status_score_hint = {
            "open": "0 (not started)", "pending": "1 (acknowledged)",
            "in-progress": "2-3 (actively being worked on)", "review": "4 (nearly complete)",
            "done": "5 (fully done)", "blocked": "1 (blocked/not progressing)",
        }
        status_hint = _status_score_hint.get(user_status or "open", "unknown")

        system = (
            "You are a work item classifier for a software project. "
            "Given an existing work item, re-classify it and return ONLY valid JSON with these fields:\n"
            '{"wi_type": "use_case|feature|bug|task|requirement", '
            '"score_importance": 0-5, "score_status": 0-5}\n\n'
            "score_importance: 0=trivial, 5=critical/blocking\n"
            "score_status: 0=not started, 5=fully done — align with the user_status hint provided\n"
            "Return no other text."
        )
        user_msg = (
            f"Name: {name or ''}\n"
            f"Current type: {wi_type or ''}\n"
            f"User status: {user_status or 'open'} (score_status hint: {status_hint})\n"
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
                             SELECT id::text, wi_id, 0 AS depth
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id::text, w.wi_id, d.depth + 1
                             FROM mem_work_items w
                             JOIN tree d ON w.wi_parent_id = d.id::uuid
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                               AND d.depth < 20
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

    # NOTE: get_md(), save_md(), refresh_md(), complete_use_case(), etc.
    # are inherited from _MarkdownMixin (memory/_wi_markdown.py).

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
