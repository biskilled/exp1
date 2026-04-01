"""entities.py — Entity/relationship model for the aicli knowledge layer.

Manages the tag taxonomy and source-tag links connecting every prompt, commit,
document, and message to named features, bugs, and tasks.

Underlying tables:
  mng_tags_categories  — global category vocabulary
  planner_tags         — per-project tag registry, UUID PK
  planner_tags_meta    — tag description / due_date / priority metadata
  mem_mrr_tags         — unified junction: tag ↔ prompt | commit | item | message
  mem_mrr_prompts      — prompt log
  mem_mrr_commits      — commit log

Endpoints:
    Categories:
        GET    /entities/categories
        POST   /entities/categories
        PATCH  /entities/categories/{id}
        DELETE /entities/categories/{id}

    Tags / Values (named instances per category):
        GET    /entities/values          ?project=&category_id=&category_name=&status=
        GET    /entities/values/number/{seq_num}
        POST   /entities/values
        PATCH  /entities/values/{id}    (id = UUID string)
        DELETE /entities/values/{id}    (id = UUID string)
        GET    /entities/summary

    Session tagging:
        GET    /entities/session-tags
        POST   /entities/session-tag
        DELETE /entities/session-tag

    Per-entry tagging (History tab):
        POST   /entities/events/tag-by-source-id
        DELETE /entities/events/tag-by-source-id
        GET    /entities/events/source-tags

    GitHub sync:
        POST   /entities/github-sync
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.database import db, build_update
from data.dl_seq import next_seq

log = logging.getLogger(__name__)

# ── SQL ─────────────────────────────────────────────────────────────────────────

# mng_tags_categories is global (client-scoped, no project column)
_SQL_GET_CATEGORY_NAMES = """
    SELECT name FROM mng_tags_categories WHERE client_id=1
"""

_SQL_SEED_CATEGORY = """
    INSERT INTO mng_tags_categories (client_id, name, color, icon)
    VALUES (1, %s, %s, %s)
    ON CONFLICT (client_id, name) DO NOTHING
"""

_SQL_LIST_CATEGORIES = """
    SELECT tc.id, tc.name, tc.color, tc.icon,
           COUNT(t.id) AS value_count
    FROM mng_tags_categories tc
    LEFT JOIN planner_tags t ON t.category_id = tc.id AND t.client_id=1 AND t.project=%s
    WHERE tc.client_id=1
    GROUP BY tc.id ORDER BY tc.name
"""

_SQL_INSERT_CATEGORY = """
    INSERT INTO mng_tags_categories (client_id, name, color, icon)
    VALUES (1, %s, %s, %s)
    RETURNING id
"""

_SQL_DELETE_CATEGORY = """
    DELETE FROM mng_tags_categories WHERE id=%s RETURNING id
"""

# No project filter — categories are global
_SQL_GET_CATEGORY_ID = """
    SELECT id FROM mng_tags_categories WHERE client_id=1 AND name=%s
"""

# planner_tags (UUID PK) + planner_tags_meta (description/due_date) + mem_mrr_tags count
# {where} is injected at call site; caller always provides at least "t.client_id=1"
_SQL_LIST_VALUES = """
    SELECT t.id::text, t.category_id, t.name,
           COALESCE(tm.description,'') AS description, t.status,
           t.created_at, tm.due_date, t.parent_id::text, t.lifecycle AS lifecycle_status,
           t.seq_num,
           COUNT(st.id) AS event_count,
           tc.name AS category_name, tc.color, tc.icon
    FROM planner_tags t
    JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    LEFT JOIN mem_mrr_tags st ON st.tag_id = t.id
    WHERE {where}
    GROUP BY t.id, t.category_id, t.name, tm.description, t.status,
             t.created_at, tm.due_date, t.parent_id, t.lifecycle, t.seq_num,
             tc.name, tc.color, tc.icon
    ORDER BY t.parent_id NULLS FIRST, t.status, t.name
"""

# Used by entity_summary endpoint and /memory synthesis
_SQL_LIST_VALUES_SUMMARY = """
    SELECT tc.id AS cat_id, tc.name AS category, tc.color, tc.icon,
           t.id::text, t.name,
           COALESCE(tm.description,'') AS description, t.status,
           tm.due_date, t.parent_id::text, t.lifecycle AS lifecycle_status,
           COUNT(DISTINCT st.id) AS event_count,
           COUNT(DISTINCT CASE WHEN st.commit_id IS NOT NULL THEN st.id END) AS commit_count
    FROM mng_tags_categories tc
    JOIN planner_tags t ON t.category_id = tc.id AND t.client_id=1 AND t.project=%s
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    LEFT JOIN mem_mrr_tags st ON st.tag_id = t.id
    WHERE tc.client_id=1 AND t.status != 'archived'
    GROUP BY tc.id, tc.name, tc.color, tc.icon,
             t.id, t.name, tm.description, t.status, tm.due_date, t.parent_id, t.lifecycle
    ORDER BY tc.name, t.status, COUNT(DISTINCT st.id) DESC
"""

_SQL_INSERT_VALUE = """
    INSERT INTO planner_tags (client_id, project, name, category_id, parent_id, lifecycle, seq_num)
    VALUES (1, %s, %s, %s, %s::uuid, %s, %s)
    RETURNING id::text
"""

_SQL_GET_VALUE_BY_SEQ = """
    SELECT t.id::text, t.name, COALESCE(tm.description,''), t.status, t.created_at,
           tm.due_date, t.parent_id::text, t.lifecycle AS lifecycle_status, t.seq_num,
           tc.name AS category_name, tc.color, tc.icon
    FROM planner_tags t
    JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    WHERE t.client_id=1 AND t.project=%s AND t.seq_num=%s
    LIMIT 1
"""

_SQL_DELETE_VALUE = """
    DELETE FROM planner_tags WHERE id=%s::uuid RETURNING id
"""

# Sources (prompts + commits) tagged with a given tag
_SQL_GET_EVENTS_FOR_VALUE = """
    SELECT pr.source_id, 'prompt' AS event_type, pr.source_id AS source_id,
           left(pr.prompt, 120) AS title, pr.created_at
    FROM mem_mrr_tags st
    JOIN mem_mrr_prompts pr ON pr.id = st.prompt_id AND pr.client_id=1 AND pr.project=%s
    WHERE st.tag_id = %s::uuid
    UNION ALL
    SELECT c.commit_hash, 'commit', c.commit_hash,
           left(c.commit_msg, 120), c.committed_at
    FROM mem_mrr_tags st
    JOIN mem_mrr_commits c ON c.id = st.commit_id AND c.client_id=1 AND c.project=%s
    WHERE st.tag_id = %s::uuid
    ORDER BY 5 DESC LIMIT %s
"""

# Session tags: all tags applied to prompts or commits in a session
_SQL_GET_SESSION_ENTITY_TAGS = """
    SELECT DISTINCT t.id::text AS id, t.name, t.status,
           tc.id AS category_id, tc.name AS category_name, tc.color, tc.icon
    FROM mem_mrr_tags st
    JOIN planner_tags t ON t.id = st.tag_id AND t.client_id=1 AND t.project=%s
    JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
    LEFT JOIN mem_mrr_prompts p ON p.id = st.prompt_id
    LEFT JOIN mem_mrr_commits c ON c.id = st.commit_id
    WHERE (p.session_id = %s OR c.session_id = %s)
"""

# GitHub sync: upsert tag by name+project (no description — use planner_tags_meta for that)
_SQL_UPSERT_TAG_GITHUB = """
    INSERT INTO planner_tags (client_id, project, name, category_id)
    VALUES (1, %s, %s, %s)
    ON CONFLICT (client_id, project, name) DO NOTHING
    RETURNING (xmax = 0) AS was_inserted, id::text
"""

# ────────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# ── helpers ────────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

def _project(p: str | None) -> str:
    return p or settings.active_project or "default"

def _workspace(project: str) -> Path:
    return Path(settings.workspace_dir) / project

_DEFAULT_CATEGORIES = [
    ("feature",   "#27ae60", "⬡"),
    ("bug",       "#e74c3c", "⚠"),
    ("task",      "#4a90e2", "✓"),
    ("component", "#8e44ad", "◈"),
    ("doc_type",  "#2980b9", "📄"),
    ("customer",  "#f39c12", "👤"),
    ("phase",     "#16a085", "⏱"),
]

def _seed_defaults(project: str) -> None:
    """Idempotent: ensures every default category exists (categories are global)."""
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_CATEGORY_NAMES)
            existing = {r[0] for r in cur.fetchall()}
            for name, color, icon in _DEFAULT_CATEGORIES:
                if name not in existing:
                    cur.execute(_SQL_SEED_CATEGORY, (name, color, icon))


# ── Categories ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:    str
    color:   str = "#4a90e2"
    icon:    str = "⬡"
    project: Optional[str] = None

class CategoryPatch(BaseModel):
    name:  Optional[str] = None
    color: Optional[str] = None
    icon:  Optional[str] = None


@router.get("/categories")
async def list_categories(project: str | None = Query(None)):
    p = _project(project)
    if not db.is_available():
        return {
            "categories": [
                {"id": None, "name": n, "color": c, "icon": i, "project": p}
                for n, c, i in _DEFAULT_CATEGORIES
            ],
            "project": p,
            "fallback": True,
        }
    _seed_defaults(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_CATEGORIES, (p,))
            cols = [d[0] for d in cur.description]
            return {"categories": [dict(zip(cols, r)) for r in cur.fetchall()], "project": p}


@router.post("/categories", status_code=201)
async def create_category(body: CategoryCreate):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_INSERT_CATEGORY, (body.name, body.color, body.icon))
            return {"id": cur.fetchone()[0], "name": body.name}


@router.patch("/categories/{cat_id}")
async def patch_category(cat_id: int, body: CategoryPatch):
    _require_db()
    fields = {k: v for k, v in {"name": body.name, "color": body.color, "icon": body.icon}.items() if v is not None}
    if not fields:
        raise HTTPException(400, "Nothing to update")
    set_clause, vals = build_update(fields)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE mng_tags_categories SET {set_clause} WHERE id=%s RETURNING id",
                vals + [cat_id],
            )
            if not cur.fetchone():
                raise HTTPException(404, "Category not found")
    return {"ok": True}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_CATEGORY, (cat_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Category not found")
    return {"ok": True}


# ── Values / Tags ───────────────────────────────────────────────────────────────

_LIFECYCLE_STATES = ["idea", "design", "development", "testing", "review", "done"]

class ValueCreate(BaseModel):
    category_id:      int = 0
    name:             str
    description:      str = ""
    project:          Optional[str] = None
    due_date:         Optional[str] = None
    parent_id:        Optional[str] = None   # UUID string
    category_name:    Optional[str] = None   # alternative to category_id
    lifecycle_status: Optional[str] = None

class ValuePatch(BaseModel):
    name:             Optional[str] = None
    description:      Optional[str] = None
    status:           Optional[str] = None
    due_date:         Optional[str] = None
    parent_id:        Optional[str] = None   # UUID string
    lifecycle_status: Optional[str] = None


@router.get("/values")
async def list_values(
    project:       str | None = Query(None),
    category_id:   int | None = Query(None),
    category_name: str | None = Query(None),
    status:        str | None = Query(None),
):
    if not db.is_available():
        return {"values": [], "project": _project(project), "fallback": True}
    _require_db()
    p = _project(project)
    _seed_defaults(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if category_name and not category_id:
                cur.execute(_SQL_GET_CATEGORY_ID, (category_name,))
                row = cur.fetchone()
                if row:
                    category_id = row[0]

            where_parts = ["t.client_id=1", "t.project=%s"]
            params: list = [p]
            if category_id:
                where_parts.append("t.category_id=%s"); params.append(category_id)
            if status:
                where_parts.append("t.status=%s"); params.append(status)

            cur.execute(
                _SQL_LIST_VALUES.format(where=" AND ".join(where_parts)),
                params,
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                if row.get("due_date"):
                    row["due_date"] = row["due_date"].isoformat()
                rows.append(row)
            return {"values": rows, "project": p}


@router.get("/summary")
async def entity_summary(project: str | None = Query(None)):
    """Structured project management view: all active tags grouped by category.

    Returns features/bugs/tasks with descriptions, due dates, source counts and
    linked commit counts. Used by /memory synthesis and MCP get_project_state.
    """
    _require_db()
    p = _project(project)
    _seed_defaults(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_VALUES_SUMMARY, (p,))
            rows = cur.fetchall()

    cats: dict[str, dict] = {}
    for (cat_id, cat_name, color, icon, vid, vname, vdesc, vstatus, vdue,
         vparent, lc_status, event_count, commit_count) in rows:
        if cat_name not in cats:
            cats[cat_name] = {"id": cat_id, "name": cat_name,
                              "color": color, "icon": icon, "values": []}
        cats[cat_name]["values"].append({
            "id": vid,
            "name": vname,
            "description": vdesc or "",
            "status": vstatus,
            "due_date": vdue.isoformat() if vdue else None,
            "parent_id": vparent,
            "lifecycle_status": lc_status or "idea",
            "event_count": event_count,
            "commit_count": commit_count,
        })

    # Augment feature/bug/task categories with work_item agent_status
    _WORK_ITEM_CATS = {"feature", "bug", "task"}
    for cat_name, cat_data in cats.items():
        if cat_name not in _WORK_ITEM_CATS:
            continue
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT name, agent_status, acceptance_criteria,
                                  implementation_plan, lifecycle_status
                           FROM mem_ai_work_items
                           WHERE client_id=1 AND project=%s AND category_name=%s AND status != 'archived'""",
                        (p, cat_name),
                    )
                    wi_map = {r[0]: r for r in cur.fetchall()}
            for val in cat_data["values"]:
                wi = wi_map.get(val["name"])
                if wi:
                    _, agent_status, ac, impl, lc = wi
                    val["agent_status"]        = agent_status
                    val["has_acceptance"]      = bool(ac)
                    val["has_implementation"]  = bool(impl)
                    val["lifecycle_status"]    = lc or val.get("lifecycle_status", "idea")
        except Exception as _we:
            log.debug(f"work_items augment for {cat_name}: {_we}")

    return {"summary": list(cats.values()), "project": p}


@router.post("/values", status_code=201)
async def create_value(body: ValueCreate):
    _require_db()
    p = _project(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Resolve category
            cat_id = body.category_id
            if (not cat_id or cat_id == 0) and body.category_name:
                cur.execute(_SQL_GET_CATEGORY_ID, (body.category_name,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, f"Category '{body.category_name}' not found")
                cat_id = row[0]
            else:
                cur.execute("SELECT id FROM mng_tags_categories WHERE client_id=1 AND id=%s", (cat_id,))
                if not cur.fetchone():
                    raise HTTPException(404, "Category not found")

            cat_name_for_seq = body.category_name or ""
            if not cat_name_for_seq:
                cur.execute("SELECT name FROM mng_tags_categories WHERE client_id=1 AND id=%s", (cat_id,))
                r2 = cur.fetchone()
                if r2:
                    cat_name_for_seq = r2[0]

            seq = next_seq(cur, p, cat_name_for_seq)
            lc = body.lifecycle_status or "idea"
            cur.execute(
                _SQL_INSERT_VALUE,
                (p, body.name, cat_id, body.parent_id or None, lc, seq),
            )
            new_id = cur.fetchone()[0]

            if body.description or body.due_date:
                cur.execute(
                    """INSERT INTO planner_tags_meta (tag_id, client_id, project, description, due_date)
                       VALUES (%s::uuid, 1, %s, %s, %s)
                       ON CONFLICT (tag_id) DO NOTHING""",
                    (new_id, p, body.description, body.due_date or None),
                )

            return {"id": new_id, "name": body.name, "project": p, "category_id": cat_id, "seq_num": seq}


@router.get("/values/number/{seq_num}")
async def get_value_by_number(seq_num: int, project: str | None = Query(None)):
    """Resolve a short sequential number (e.g. #10005) to the full tag/value."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_VALUE_BY_SEQ, (p, seq_num))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, f"Tag #{seq_num} not found in project {p!r}")
            cols = [d[0] for d in cur.description]
            row = dict(zip(cols, r))
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            if row.get("due_date"):
                row["due_date"] = row["due_date"].isoformat()
            return row


@router.patch("/values/{val_id}")
async def patch_value(val_id: str, body: ValuePatch):
    """Update a tag (val_id is a UUID string)."""
    _require_db()
    tag_updates: dict[str, object] = {}
    if body.name             is not None: tag_updates["name"] = body.name
    if body.status           is not None: tag_updates["status"] = body.status
    if body.lifecycle_status is not None: tag_updates["lifecycle"] = body.lifecycle_status
    if body.parent_id        is not None: tag_updates["parent_id"] = body.parent_id or None

    meta_fields, meta_params = [], []
    if body.description is not None:
        meta_fields.append("description=%s"); meta_params.append(body.description)
    if body.due_date is not None:
        meta_fields.append("due_date=%s"); meta_params.append(body.due_date or None)

    if not tag_updates and not meta_fields:
        raise HTTPException(400, "Nothing to update")

    with db.conn() as conn:
        with conn.cursor() as cur:
            if tag_updates:
                # parent_id is a UUID — cast it
                set_parts, set_vals = [], []
                for k, v in tag_updates.items():
                    if k == "parent_id":
                        set_parts.append("parent_id=%s::uuid")
                    else:
                        set_parts.append(f"{k}=%s")
                    set_vals.append(v)
                set_vals.append(val_id)
                cur.execute(
                    f"UPDATE planner_tags SET {','.join(set_parts)} WHERE id=%s::uuid AND client_id=1 RETURNING id",
                    set_vals,
                )
                if not cur.fetchone():
                    raise HTTPException(404, "Tag not found")

            if meta_fields:
                meta_params_list = list(meta_params) + [val_id]
                cur.execute(
                    f"UPDATE planner_tags_meta SET {','.join(meta_fields)}, updated_at=NOW() WHERE tag_id=%s::uuid",
                    meta_params_list,
                )
                if cur.rowcount == 0:
                    # No meta row yet — insert it
                    cur.execute(
                        "SELECT client_id, project FROM planner_tags WHERE id=%s::uuid", (val_id,)
                    )
                    tr = cur.fetchone()
                    if tr:
                        field_names = [f.split("=")[0] for f in meta_fields]
                        placeholders = ",".join(["%s"] * len(meta_fields))
                        cur.execute(
                            f"INSERT INTO planner_tags_meta (tag_id, client_id, project, {','.join(field_names)}) "
                            f"VALUES (%s::uuid, %s, %s, {placeholders})",
                            [val_id, tr[0], tr[1]] + list(meta_params),
                        )
    return {"ok": True}


@router.delete("/values/{val_id}")
async def delete_value(val_id: str):
    """Delete a tag (val_id is a UUID string). CASCADE deletes planner_tags_meta + mem_mrr_tags."""
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_VALUE, (val_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Tag not found")
    return {"ok": True}


# ── Events list (now queries mem_mrr_prompts + mem_mrr_commits) ──────────────────────────

@router.get("/events")
async def list_events(
    project:    str | None = Query(None),
    event_type: str | None = Query(None),
    value_id:   str | None = Query(None),   # UUID string
    limit:      int        = Query(50),
):
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if value_id:
                cur.execute(
                    _SQL_GET_EVENTS_FOR_VALUE,
                    (p, value_id, p, value_id, limit),
                )
                rows_raw = cur.fetchall()
                rows = [
                    {"event_type": r[1], "source_id": r[2], "title": r[3],
                     "created_at": r[4].isoformat() if r[4] else None, "tags": []}
                    for r in rows_raw
                ]
            elif event_type == "commit":
                cur.execute(
                    """SELECT commit_hash, 'commit', commit_hash, left(commit_msg,120), committed_at
                       FROM mem_mrr_commits WHERE client_id=1 AND project=%s
                       ORDER BY committed_at DESC NULLS LAST LIMIT %s""",
                    (p, limit),
                )
                rows = [
                    {"event_type": "commit", "source_id": r[0], "title": r[3],
                     "created_at": r[4].isoformat() if r[4] else None, "tags": []}
                    for r in cur.fetchall()
                ]
            else:
                cur.execute(
                    """SELECT source_id, 'prompt', source_id, left(prompt,120), created_at
                       FROM mem_mrr_prompts WHERE client_id=1 AND project=%s AND event_type='prompt'
                       ORDER BY created_at DESC LIMIT %s""",
                    (p, limit),
                )
                rows = [
                    {"event_type": "prompt", "source_id": r[0], "title": r[3],
                     "created_at": r[4].isoformat() if r[4] else None, "tags": []}
                    for r in cur.fetchall()
                ]
            return {"events": rows, "project": p, "total": len(rows)}


_NOISE_PREFIXES = ("<task-notification>", "<tool-use-id>", "<task-id>", "<parameter>")


def _do_sync_events(p: str) -> dict[str, int]:
    """No-op stub — pr_events table was removed in the memory infra migration.

    Prompts live in mem_mrr_prompts; commits live in mem_mrr_commits.
    Tagging now uses mem_mrr_tags directly.
    """
    return {"prompt": 0, "commit": 0}


def _do_sync_phase5(p: str) -> dict[str, int]:
    """No-op stub — pr_event_links removed. Commit→prompt linking now uses mem_mrr_commits.prompt_id.

    Backfill for all commits:
        UPDATE mem_mrr_commits c SET prompt_id = (
            SELECT p.id FROM mem_mrr_prompts p WHERE p.client_id=1 AND p.project=c.project
              AND p.session_id=c.session_id ORDER BY p.created_at DESC LIMIT 1)
        WHERE c.session_id IS NOT NULL AND c.prompt_id IS NULL.
    """
    return {}


@router.post("/events/sync")
async def sync_events(
    background: BackgroundTasks,
    project: str | None = Query(None),
):
    """No-op stub — event sync is now handled via mem_mrr_prompts + mem_mrr_commits + mem_mrr_tags."""
    p = _project(project)
    return {"imported": {"prompt": 0, "commit": 0}, "project": p, "phase5": "noop"}


# ── Event tagging (deprecated — use tag-by-source-id) ─────────────────────────
# These endpoints used pr_events integer IDs which no longer exist.

class TagAdd(BaseModel):
    entity_value_id: str    # UUID string (was int)
    auto_tagged:     bool = False


@router.post("/events/{event_id}/tag")
async def add_event_tag(
    event_id: str, body: TagAdd, background: BackgroundTasks,
    project: str | None = Query(None),
):
    """Deprecated: use POST /entities/events/tag-by-source-id instead."""
    raise HTTPException(410, "Use POST /entities/events/tag-by-source-id")


@router.delete("/events/{event_id}/tag/{value_id}")
async def remove_event_tag(
    event_id: str, value_id: str, background: BackgroundTasks,
    project: str | None = Query(None),
):
    """Deprecated: use DELETE /entities/events/tag-by-source-id instead."""
    raise HTTPException(410, "Use DELETE /entities/events/tag-by-source-id")


@router.get("/values/{val_id}/events")
async def value_events(val_id: str, project: str | None = Query(None), limit: int = Query(50)):
    return await list_events(project=project, value_id=val_id, limit=limit)


# ── Auto-tag suggestions ────────────────────────────────────────────────────────

async def _auto_suggest_tags(prompt_id: str, project: str, content: str) -> None:
    """Apply session tags to a prompt via mem_mrr_tags. Silent on any error.

    NOTE: LLM-based suggestions are handled by generate_memory() in route_projects.py.
    This function only applies the active session's phase/feature/bug tags immediately.
    """
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Get active session tags
                cur.execute(
                    "SELECT phase, feature, bug_ref FROM mng_session_tags WHERE client_id=1 AND project=%s",
                    (project,),
                )
                st_row = cur.fetchone()
                if not st_row:
                    return
                phase, feature, bug_ref = st_row

                # Apply matching tags immediately
                for tag_value, cat_name in [
                    (phase, "phase"), (feature, "feature"), (bug_ref, "bug")
                ]:
                    if not tag_value:
                        continue
                    cur.execute(
                        """SELECT t.id FROM planner_tags t
                           JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
                           WHERE t.client_id=1 AND t.project=%s AND t.name=%s AND tc.name=%s
                           LIMIT 1""",
                        (project, tag_value, cat_name),
                    )
                    tag_row = cur.fetchone()
                    if tag_row:
                        cur.execute(
                            """INSERT INTO mem_mrr_tags (tag_id, prompt_id, auto_tagged)
                               VALUES (%s, %s::uuid, true) ON CONFLICT DO NOTHING""",
                            (tag_row[0], prompt_id),
                        )
    except Exception as e:
        log.debug(f"_auto_suggest_tags failed (prompt {prompt_id}): {e}")


@router.get("/suggestions")
async def get_suggestions(
    project:   str | None = Query(None),
    source_id: str | None = Query(None),
):
    """Suggestions are now generated by POST /projects/{name}/memory.
    This stub returns empty so legacy UI calls don't error.
    """
    return {"events": [], "project": _project(project)}


@router.post("/suggestions/{event_id}/dismiss")
async def dismiss_suggestions(event_id: str, project: str | None = Query(None)):
    """Stub — suggestions are now managed in generate_memory()."""
    return {"ok": True}


# ── Event links (dropped table — stubbed) ──────────────────────────────────────

_LINK_TYPES = {"implements", "fixes", "causes", "relates_to", "references", "closes"}

class LinkCreate(BaseModel):
    to_event_id: str
    link_type:   str


@router.post("/events/{event_id}/link")
async def add_event_link(event_id: str, body: LinkCreate, project: str | None = Query(None)):
    """Stub — pr_event_links table was removed."""
    raise HTTPException(410, "Event links removed — commit→prompt linking via mem_mrr_commits.prompt_id")


@router.delete("/events/{event_id}/link/{to_id}/{link_type}")
async def remove_event_link(event_id: str, to_id: str, link_type: str, project: str | None = Query(None)):
    """Stub — pr_event_links table was removed."""
    raise HTTPException(410, "Event links removed")


@router.get("/events/{event_id}/links")
async def get_event_links(event_id: str, project: str | None = Query(None)):
    """Stub — pr_event_links table was removed."""
    return {"outgoing": [], "incoming": [], "event_id": event_id}


# ── Session bulk-tag ─────────────────────────────────────────────────────────────

class SessionTagBody(BaseModel):
    session_id:    str
    project:       Optional[str] = None
    value_id:      Optional[str] = None           # UUID string of existing planner_tags row
    category_name: Optional[str] = None           # find/create tag in this category
    value_name:    Optional[str] = None           # tag name (used with category_name)
    description:   str = ""


@router.post("/session-tag")
async def session_bulk_tag(body: SessionTagBody):
    """Tag ALL prompts and commits belonging to a session with a given tag.

    - If value_id (UUID) is provided → use it directly.
    - If category_name + value_name → find or create the planner_tags row first.
    Returns count of sources tagged.
    """
    _require_db()
    p = _project(body.project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            tag_id = body.value_id
            if tag_id is None:
                if not body.category_name or not body.value_name:
                    raise HTTPException(400, "Provide value_id OR category_name+value_name")
                # Resolve category (global)
                cur.execute(_SQL_GET_CATEGORY_ID, (body.category_name,))
                cat_row = cur.fetchone()
                if not cat_row:
                    raise HTTPException(404, f"Category '{body.category_name}' not found")
                cat_id = cat_row[0]
                # Find or create tag
                cur.execute(
                    "SELECT id::text FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s",
                    (p, body.value_name),
                )
                val_row = cur.fetchone()
                if val_row:
                    tag_id = val_row[0]
                else:
                    seq = next_seq(cur, p, body.category_name)
                    cur.execute(
                        "INSERT INTO planner_tags (client_id, project, name, category_id, seq_num) "
                        "VALUES (1, %s, %s, %s, %s) RETURNING id::text",
                        (p, body.value_name, cat_id, seq),
                    )
                    tag_id = cur.fetchone()[0]
                    if body.description:
                        cur.execute(
                            "INSERT INTO planner_tags_meta (tag_id, client_id, project, description) "
                            "VALUES (%s::uuid, 1, %s, %s) ON CONFLICT (tag_id) DO NOTHING",
                            (tag_id, p, body.description),
                        )

            # Tag all prompts in this session
            cur.execute(
                """INSERT INTO mem_mrr_tags (tag_id, prompt_id, auto_tagged)
                   SELECT %s::uuid, id, false
                   FROM mem_mrr_prompts
                   WHERE client_id=1 AND project=%s AND session_id=%s
                   ON CONFLICT DO NOTHING""",
                (tag_id, p, body.session_id),
            )
            prompt_tagged = cur.rowcount

            # Tag all commits in this session
            cur.execute(
                """INSERT INTO mem_mrr_tags (tag_id, commit_id, auto_tagged)
                   SELECT %s::uuid, id, false
                   FROM mem_mrr_commits
                   WHERE client_id=1 AND project=%s AND session_id=%s
                   ON CONFLICT DO NOTHING""",
                (tag_id, p, body.session_id),
            )
            commit_tagged = cur.rowcount

    return {
        "ok": True,
        "value_id": tag_id,
        "session_id": body.session_id,
        "events_tagged": prompt_tagged + commit_tagged,
        "project": p,
    }


# ── Per-entry tagging (History tab) ───────────────────────────────────────────

class TagBySourceIdBody(BaseModel):
    source_id:       str   # prompt source_id (timestamp) or commit hash
    tag_id:          str   # UUID of planner_tags row
    project:         Optional[str] = None
    # Legacy field kept for backward compat — ignored (use tag_id)
    entity_value_id: Optional[int] = None


def _propagate_tags_phase4(p: str) -> None:
    """Background: copy prompt tags → commits in same session (via mem_mrr_tags).

    Called after every manual tag operation so commit tag chips stay in sync.
    """
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mem_mrr_tags (tag_id, commit_id, auto_tagged)
                       SELECT DISTINCT st.tag_id, c.id, TRUE
                       FROM mem_mrr_tags st
                       JOIN mem_mrr_prompts pr ON pr.id = st.prompt_id
                                         AND pr.client_id=1 AND pr.project=%s
                                         AND pr.session_id IS NOT NULL
                       JOIN mem_mrr_commits c ON c.session_id = pr.session_id
                                        AND c.client_id=1 AND c.project=%s
                       WHERE st.prompt_id IS NOT NULL
                       ON CONFLICT DO NOTHING""",
                    (p, p),
                )
    except Exception as exc:
        log.debug(f"Background tag propagation skipped: {exc}")


@router.post("/events/tag-by-source-id")
async def tag_event_by_source_id(body: TagBySourceIdBody, background: BackgroundTasks):
    """Tag a single prompt or commit by its source_id / commit hash.

    source_id is either:
      - a timestamp string (prompt) → looked up in mem_mrr_prompts.source_id
      - a 7-40 char hex string (commit hash) → looked up in mem_mrr_commits.commit_hash
    tag_id must be a valid planner_tags UUID for this project.
    """
    _require_db()
    p = _project(body.project)
    tag_id = body.tag_id

    is_commit = bool(re.match(r'^[0-9a-f]{7,40}$', body.source_id.lower()))

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Verify tag exists
            cur.execute(
                "SELECT id FROM planner_tags WHERE id=%s::uuid AND client_id=1 AND project=%s",
                (tag_id, p),
            )
            if not cur.fetchone():
                raise HTTPException(404, f"Tag {tag_id!r} not found in project {p!r}")

            if is_commit:
                cur.execute(
                    "SELECT id FROM mem_mrr_commits WHERE client_id=1 AND project=%s AND commit_hash=%s LIMIT 1",
                    (p, body.source_id),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, f"Commit {body.source_id!r} not found")
                cur.execute(
                    """INSERT INTO mem_mrr_tags (tag_id, commit_id, auto_tagged)
                       VALUES (%s::uuid, %s, false) ON CONFLICT DO NOTHING""",
                    (tag_id, row[0]),
                )
            else:
                cur.execute(
                    "SELECT id FROM mem_mrr_prompts WHERE client_id=1 AND project=%s AND source_id=%s LIMIT 1",
                    (p, body.source_id),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, f"Prompt with source_id={body.source_id!r} not found")
                cur.execute(
                    """INSERT INTO mem_mrr_tags (tag_id, prompt_id, auto_tagged)
                       VALUES (%s::uuid, %s, false) ON CONFLICT DO NOTHING""",
                    (tag_id, row[0]),
                )

    background.add_task(_propagate_tags_phase4, p)
    return {"ok": True, "source_id": body.source_id, "tag_id": tag_id, "project": p}


@router.delete("/events/tag-by-source-id")
async def untag_event_by_source_id(
    source_id: str = Query(...),
    value_id:  str = Query(...),   # UUID string (was int)
    project:   str | None = Query(None),
):
    """Remove a tag from a prompt or commit identified by its source_id / commit hash."""
    _require_db()
    p = _project(project)
    is_commit = bool(re.match(r'^[0-9a-f]{7,40}$', source_id.lower()))
    with db.conn() as conn:
        with conn.cursor() as cur:
            if is_commit:
                cur.execute(
                    """DELETE FROM mem_mrr_tags st
                       USING mem_mrr_commits c
                       WHERE st.commit_id = c.id
                         AND c.client_id=1 AND c.project=%s AND c.commit_hash=%s
                         AND st.tag_id = %s::uuid""",
                    (p, source_id, value_id),
                )
            else:
                cur.execute(
                    """DELETE FROM mem_mrr_tags st
                       USING mem_mrr_prompts pr
                       WHERE st.prompt_id = pr.id
                         AND pr.client_id=1 AND pr.project=%s AND pr.source_id=%s
                         AND st.tag_id = %s::uuid""",
                    (p, source_id, value_id),
                )
    return {"ok": True, "source_id": source_id, "value_id": value_id}


@router.delete("/session-tag")
async def remove_session_tag(
    session_id: str = Query(...),
    value_id:   str = Query(...),   # UUID string (was int)
    project:    str | None = Query(None),
):
    """Remove a tag from all prompts and commits in a session."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM mem_mrr_tags st
                   USING mem_mrr_prompts pr
                   WHERE st.prompt_id = pr.id
                     AND pr.client_id=1 AND pr.project=%s AND pr.session_id=%s
                     AND st.tag_id = %s::uuid""",
                (p, session_id, value_id),
            )
            deleted_p = cur.rowcount
            cur.execute(
                """DELETE FROM mem_mrr_tags st
                   USING mem_mrr_commits c
                   WHERE st.commit_id = c.id
                     AND c.client_id=1 AND c.project=%s AND c.session_id=%s
                     AND st.tag_id = %s::uuid""",
                (p, session_id, value_id),
            )
            deleted_c = cur.rowcount
    return {"ok": True, "session_id": session_id, "value_id": value_id,
            "deleted": deleted_p + deleted_c}


@router.get("/events/source-tags")
async def get_events_source_tags(project: str | None = Query(None)):
    """Return a map of source_id → [tag list] for all tagged prompts and commits.

    Used by the History tab to display persisted tags on each history entry.
    Returns {} (not 503) when DB is unavailable.
    """
    if not db.is_available():
        return {}
    p = _project(project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pr.source_id, t.id::text, t.name, tc.color, tc.icon, tc.name AS cat_name
                   FROM mem_mrr_tags st
                   JOIN planner_tags t ON t.id = st.tag_id AND t.client_id=1 AND t.project=%s
                   JOIN mng_tags_categories tc ON tc.id = t.category_id
                   JOIN mem_mrr_prompts pr ON pr.id = st.prompt_id AND pr.client_id=1 AND pr.project=%s
                   WHERE st.prompt_id IS NOT NULL
                   UNION ALL
                   SELECT c.commit_hash, t.id::text, t.name, tc.color, tc.icon, tc.name
                   FROM mem_mrr_tags st
                   JOIN planner_tags t ON t.id = st.tag_id AND t.client_id=1 AND t.project=%s
                   JOIN mng_tags_categories tc ON tc.id = t.category_id
                   JOIN mem_mrr_commits c ON c.id = st.commit_id AND c.client_id=1 AND c.project=%s
                   WHERE st.commit_id IS NOT NULL
                   ORDER BY 1, 3""",
                (p, p, p, p),
            )
            rows = cur.fetchall()

    result: dict = {}
    for source_id, vid, vname, color, icon, cat_name in rows:
        if source_id not in result:
            result[source_id] = []
        result[source_id].append({
            "value_id": vid,
            "name":     vname,
            "color":    color or "#4a90e2",
            "icon":     icon  or "⬡",
            "cat_name": cat_name,
        })
    return result


# ── Value dependency links (mng_entity_value_links was dropped) ────────────────

class ValueLinkCreate(BaseModel):
    to_value_id: str   # UUID string
    link_type:   str = "blocks"


@router.post("/values/{val_id}/links", status_code=201)
async def add_value_link(val_id: str, body: ValueLinkCreate, project: str | None = Query(None)):
    """Stub — mng_entity_value_links was removed. Tag dependencies not yet reimplemented."""
    raise HTTPException(410, "Tag dependency links not yet reimplemented in new schema")


@router.delete("/values/{val_id}/links/{to_id}")
async def remove_value_link(val_id: str, to_id: str, link_type: str = Query("blocks")):
    raise HTTPException(410, "Tag dependency links not yet reimplemented in new schema")


@router.get("/values/{val_id}/links")
async def get_value_links(val_id: str):
    """Stub — returns empty until tag links are reimplemented."""
    return {"outgoing": [], "incoming": [], "value_id": val_id}


# ── GitHub Issue Sync ───────────────────────────────────────────────────────────

@router.post("/github-sync")
async def github_sync(
    project:  str | None = Query(None),
    owner:    str = Query(...),
    repo:     str = Query(...),
    token:    str = Query(""),
    state:    str = Query("open"),
):
    """Import GitHub issues as planner_tags.

    Label mapping: 'bug' → bug category; 'enhancement'/'feature' → feature; else → task.
    Idempotent: re-running updates description without duplicating tags.
    """
    _require_db()
    import httpx

    p = _project(project)
    _seed_defaults(p)

    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": 100},
            headers=headers,
        )
        resp.raise_for_status()
        issues = resp.json()

    def _label_to_category(labels: list) -> str:
        names = {lbl["name"].lower() for lbl in labels}
        if "bug" in names:
            return "bug"
        if names & {"enhancement", "feature"}:
            return "feature"
        return "task"

    created = updated = skipped = 0

    with db.conn() as conn:
        with conn.cursor() as cur:
            for issue in issues:
                if issue.get("pull_request"):
                    skipped += 1
                    continue
                cat_name = _label_to_category(issue.get("labels", []))
                cur.execute(_SQL_GET_CATEGORY_ID, (cat_name,))
                cat_row = cur.fetchone()
                if not cat_row:
                    skipped += 1
                    continue
                cat_id = cat_row[0]
                name = f"#{issue['number']}: {issue['title'][:200]}"
                desc = (issue.get("body") or "")[:500]
                due = None
                if issue.get("milestone") and issue["milestone"].get("due_on"):
                    due = issue["milestone"]["due_on"][:10]

                # Upsert tag
                cur.execute(_SQL_UPSERT_TAG_GITHUB, (p, name, cat_id))
                row = cur.fetchone()
                if row and row[0]:
                    created += 1
                    # Insert metadata for new tags
                    if desc or due:
                        cur.execute(
                            """INSERT INTO planner_tags_meta (tag_id, client_id, project, description, due_date)
                               VALUES (%s::uuid, 1, %s, %s, %s) ON CONFLICT (tag_id) DO NOTHING""",
                            (row[1], p, desc, due),
                        )
                else:
                    updated += 1
                    # Update description on existing tag
                    if desc:
                        cur.execute(
                            """UPDATE planner_tags_meta SET description=%s, updated_at=NOW()
                               WHERE tag_id=(SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s)""",
                            (desc, p, name),
                        )

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(issues),
        "project": p,
    }


@router.get("/session-tags")
async def get_session_entity_tags(session_id: str, project: str | None = Query(None)):
    """Return all tags applied to prompts/commits in a session.

    Used by the frontend to reload the applied-tags chip bar when switching sessions.
    """
    _require_db()
    p = _project(project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SESSION_ENTITY_TAGS, (p, session_id, session_id))
            cols = [d[0] for d in cur.description]
            tags = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {"tags": tags, "session_id": session_id, "project": p}
