"""
work_items.py — AI-detected work item management linked to planner tags.

Endpoints:
    GET    /work-items                    ?project=&category=&status=
    GET    /work-items/unlinked           ?project=
    POST   /work-items                    {ai_category, ai_name, ai_desc, ...}
    PATCH  /work-items/{id}               {ai_name?, ai_desc?, tag_id?, ...}
    DELETE /work-items/{id}
    GET    /work-items/{id}/interactions  ?limit=20
    GET    /work-items/number/{seq_num}
    GET    /work-items/search             ?query=&project=&category=&limit=
    GET    /work-items/facts              ?project=
    GET    /work-items/facts/search       ?query=&project=&limit=
    GET    /work-items/memory-items       ?project=&scope=session|feature
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.database import db
from data.dl_seq import next_seq

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_WORK_ITEMS_BASE = (
    """WITH ev_count AS (
         SELECT work_item_id::text AS wi_id,
                COUNT(*) AS event_count,
                COUNT(*) FILTER (WHERE event_type = 'prompt_batch') AS prompt_count
         FROM mem_ai_events
         WHERE project_id=%s AND work_item_id IS NOT NULL
         GROUP BY 1
       ),
       cm_count AS (
         SELECT e.work_item_id::text AS wi_id, COUNT(*) AS commit_count
         FROM mem_mrr_commits c
         JOIN mem_ai_events e ON e.id = c.event_id
         WHERE c.project_id=%s AND e.work_item_id IS NOT NULL
         GROUP BY 1
       ),
       mcount AS (
         SELECT merged_into::text AS wi_id, COUNT(*) AS cnt
         FROM mem_ai_work_items
         WHERE project_id=%s AND merged_into IS NOT NULL
         GROUP BY 1
       )
       SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
              w.requirements, w.code_summary, w.summary,
              w.tags, w.ai_tags, w.tag_id, w.ai_tag_id, w.source_event_id,
              w.merged_into, w.start_date,
              w.created_at, w.updated_at, w.seq_num,
              tc.color, tc.icon,
              COALESCE(ev_count.event_count,  0) AS event_count,
              COALESCE(ev_count.prompt_count, 0) AS prompt_count,
              COALESCE(cm_count.commit_count, 0) AS commit_count,
              COALESCE(mcount.cnt, 0) AS merge_count
       FROM mem_ai_work_items w
       LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.ai_category
       LEFT JOIN ev_count ON ev_count.wi_id = w.id::text
       LEFT JOIN cm_count ON cm_count.wi_id = w.id::text
       LEFT JOIN mcount ON mcount.wi_id = w.id::text
       WHERE {where}
       ORDER BY w.created_at DESC
       LIMIT %s"""
)

_SQL_UNLINKED_WORK_ITEMS = """
    SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
           w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
           w.start_date, w.created_at, w.seq_num,
           pt.name AS ai_tag_name,
           (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count
    FROM mem_ai_work_items w
    LEFT JOIN planner_tags pt ON pt.id = w.ai_tag_id
    WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
    ORDER BY w.created_at DESC
"""

_SQL_INSERT_WORK_ITEM = (
    """INSERT INTO mem_ai_work_items
           (project_id, ai_category, ai_name, ai_desc,
            requirements, acceptance_criteria, action_items,
            code_summary, summary, tags, status_user, status_ai, seq_num)
       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
       ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
       RETURNING id, ai_name, ai_category, created_at, seq_num"""
)

_SQL_GET_WORK_ITEM = (
    """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
              w.requirements, w.code_summary, w.summary,
              w.tags, w.tag_id, w.ai_tag_id, w.source_event_id,
              w.created_at, w.updated_at, w.seq_num
       FROM mem_ai_work_items w
       WHERE w.project_id=%s AND w.id=%s::uuid"""
)

_SQL_GET_COMMITS = (
    """SELECT c.commit_hash, c.commit_msg, c.summary, c.committed_at
       FROM mem_mrr_commits c
       WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s::text)
       ORDER BY c.committed_at DESC LIMIT %s"""
)

_SQL_DELETE_WORK_ITEM = (
    "DELETE FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s RETURNING id"
)

_SQL_GET_WORK_ITEM_BY_SEQ = (
    """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
              w.requirements, w.code_summary, w.summary,
              w.tags, w.tag_id, w.ai_tag_id,
              w.created_at, w.updated_at, w.seq_num
       FROM mem_ai_work_items w
       WHERE w.project_id=%s AND w.seq_num=%s
       LIMIT 1"""
)

_SQL_GET_INTERACTIONS = (
    """SELECT i.id, i.session_id, i.source_id,
              i.prompt, i.response, i.created_at
       FROM mem_mrr_prompts i
       WHERE i.tags @> jsonb_build_object('work-item', %s::text) AND i.project_id=%s
       ORDER BY i.created_at DESC LIMIT %s"""
)

_SQL_WORK_ITEM_STATS = """
    SELECT
        (SELECT COUNT(*) FROM mem_mrr_prompts p
         WHERE p.project_id=%s AND p.tags @> jsonb_build_object('work-item', %s)) AS prompt_count,
        (SELECT COUNT(*) FROM mem_mrr_commits c
         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS commit_count,
        (SELECT COUNT(DISTINCT cc.file_path)
         FROM mem_mrr_commits_code cc
         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS files_changed,
        (SELECT COALESCE(SUM(cc.rows_added), 0)
         FROM mem_mrr_commits_code cc
         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS rows_added,
        (SELECT COALESCE(SUM(cc.rows_removed), 0)
         FROM mem_mrr_commits_code cc
         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS rows_removed,
        (SELECT COUNT(DISTINCT cc.full_symbol)
         FROM mem_mrr_commits_code cc
         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)
           AND cc.full_symbol IS NOT NULL) AS symbols_changed,
        (SELECT jsonb_object_agg(lang, cnt) FROM (
            SELECT cc.file_language AS lang, COUNT(*) AS cnt
            FROM mem_mrr_commits_code cc
            JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
            WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)
              AND cc.file_language != ''
            GROUP BY cc.file_language
         ) t) AS languages
"""

_SQL_GET_FACTS = (
    """SELECT id, fact_key, fact_value, valid_from
       FROM mem_ai_project_facts
       WHERE project_id=%s AND valid_until IS NULL
       ORDER BY fact_key"""
)

_SQL_GET_MEMORY_ITEMS = (
    """SELECT id, event_type, source_id::text, content, importance, created_at
       FROM mem_ai_events
       WHERE {where}
       ORDER BY created_at DESC LIMIT %s"""
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()
log = logging.getLogger(__name__)


def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")


def _project(p: str | None) -> str:
    return p or settings.active_project or "default"


async def _trigger_memory_regen(project: str) -> None:
    """Background task: regenerate root context files after work item changes."""
    try:
        from memory.memory_files import MemoryFiles
        import asyncio as _aio
        await _aio.get_event_loop().run_in_executor(
            None, MemoryFiles().write_root_files, project
        )
    except Exception as e:
        log.debug(f"_trigger_memory_regen error: {e}")


async def _embed_work_item(
    project_id: int, item_id: str,
    ai_name: str, ai_desc: str, requirements: str, summary: str,
    code_summary: str = "",
) -> None:
    """Embed work item content and store the vector on the row.
    Embedding = ai_name + ai_desc + requirements + summary + code_summary.
    Used for: (1) semantic search, (2) cosine-similarity matching to planner_tags.
    planner_tags.embedding = summary + action_items → same space, enabling cross-table match.
    """
    try:
        from memory.memory_embedding import _embed
        text = f"{ai_name} {ai_desc} {requirements} {summary} {code_summary}".strip()
        vec = await _embed(text)
        if vec and db.is_available():
            vec_str = f"[{','.join(str(x) for x in vec)}]"
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mem_ai_work_items SET embedding = %s::vector WHERE id = %s::uuid AND project_id=%s",
                        (vec_str, item_id, project_id),
                    )
    except Exception as e:
        log.debug(f"_embed_work_item error: {e}")


async def _run_matching(project: str, work_item_id: str) -> None:
    """Background task: match a work item to planner tags; persist best match as ai_tag_id."""
    try:
        from memory.memory_tagging import MemoryTagging
        matches = await MemoryTagging().match_work_item_to_tags(project, work_item_id)
        if matches:
            best = matches[0]
            if best.get("confidence", 0) > 0.70 and best.get("tag_id"):
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE mem_ai_work_items SET ai_tag_id=%s::uuid WHERE id=%s::uuid",
                            (best["tag_id"], work_item_id),
                        )
    except Exception:
        pass  # non-critical background task


# ── Models ────────────────────────────────────────────────────────────────────

class WorkItemCreate(BaseModel):
    ai_category:         str
    ai_name:             str
    ai_desc:             str = ""
    project:             Optional[str] = None
    status_user:         str = "active"
    status_ai:           str = "active"
    requirements:        str = ""
    acceptance_criteria: str = ""
    action_items:        str = ""
    code_summary:        str = ""
    summary:             str = ""
    tags:                dict = {}


class WorkItemMerge(BaseModel):
    merge_with: str   # UUID of the other work item to merge with


class WorkItemPatch(BaseModel):
    ai_name:             Optional[str] = None
    ai_desc:             Optional[str] = None
    status_user:         Optional[str] = None   # set by user: active / paused / done
    status_ai:           Optional[str] = None   # set by AI: active / in_progress / done
    requirements:        Optional[str] = None
    acceptance_criteria: Optional[str] = None
    action_items:        Optional[str] = None
    code_summary:        Optional[str] = None
    summary:             Optional[str] = None
    tags:                Optional[dict] = None
    ai_tags:             Optional[dict] = None
    tag_id:              Optional[str] = None
    ai_tag_id:           Optional[str] = None
    merged_into:         Optional[str] = None
    start_date:          Optional[str] = None


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/unlinked")
async def get_unlinked_work_items(project: str | None = Query(None)):
    """Work items not yet linked to a planner tag (tag_id IS NULL).
    Returns ai_tag_name via JOIN on ai_tag_id for hint badge display."""
    if not db.is_available():
        return {"items": [], "project": _project(project), "fallback": True}
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id,))
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                for dt_field in ("created_at", "start_date"):
                    if row.get(dt_field):
                        row[dt_field] = row[dt_field].isoformat()
                rows.append(row)
    return {"items": rows, "project": p, "total": len(rows)}


@router.get("")
async def list_work_items(
    project:  str | None = Query(None),
    category: str | None = Query(None),
    status:   str | None = Query(None),
    name:     str | None = Query(None),
    limit:    int        = Query(100),
):
    """List work items, optionally filtered by category, status, or exact name."""
    if not db.is_available():
        return {"items": [], "project": _project(project), "fallback": True}
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    where = ["w.project_id=%s"]
    params: list = [p_id]
    if category:
        where.append("w.ai_category=%s"); params.append(category)
    if status:
        where.append("w.status_user=%s"); params.append(status)
    where.append("w.merged_into IS NULL")   # exclude items absorbed into a merge
    if name:
        where.append("w.ai_name=%s"); params.append(name)

    sql = _SQL_LIST_WORK_ITEMS_BASE.format(where=" AND ".join(where))
    with db.conn() as conn:
        with conn.cursor() as cur:
            # 3 extra p_id params for the ev_count/cm_count/mcount CTEs
            cur.execute(sql, [p_id, p_id, p_id] + params + [limit])
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                for dt_field in ("created_at", "updated_at", "start_date"):
                    if row.get(dt_field):
                        row[dt_field] = row[dt_field].isoformat()
                row["id"] = str(row["id"])
                if row.get("tag_id"):
                    row["tag_id"] = str(row["tag_id"])
                if row.get("ai_tag_id"):
                    row["ai_tag_id"] = str(row["ai_tag_id"])
                if row.get("tags") is None:
                    row["tags"] = {}
                if row.get("ai_tags") is None:
                    row["ai_tags"] = {}
                rows.append(row)
    return {"work_items": rows, "project": p, "total": len(rows)}


@router.post("", status_code=201)
async def create_work_item(
    body: WorkItemCreate,
    background_tasks: BackgroundTasks,
    project: str | None = Query(None),
):
    """Create a new work item."""
    _require_db()
    p = _project(project or body.project)
    p_id = db.get_or_create_project_id(p)

    import json as _json
    with db.conn() as conn:
        with conn.cursor() as cur:
            seq = next_seq(cur, p_id, body.ai_category)
            cur.execute(
                _SQL_INSERT_WORK_ITEM,
                (p_id, body.ai_category, body.ai_name, body.ai_desc,
                 body.requirements, body.acceptance_criteria, body.action_items,
                 body.code_summary, body.summary,
                 _json.dumps(body.tags), body.status_user, body.status_ai, seq),
            )
            r = cur.fetchone()
    if not r:
        raise HTTPException(409, f"Work item '{body.ai_name}' already exists in category '{body.ai_category}'")
    item_id = str(r[0])
    asyncio.create_task(_embed_work_item(p_id, item_id, body.ai_name, body.ai_desc, body.requirements, body.summary))
    asyncio.create_task(_trigger_memory_regen(p))
    background_tasks.add_task(_run_matching, p, item_id)
    return {
        "id": item_id, "ai_name": r[1], "ai_category": r[2],
        "created_at": r[3].isoformat(), "project": p, "seq_num": r[4],
    }


@router.patch("/{item_id}")
async def patch_work_item(
    item_id: str,
    body: WorkItemPatch,
    project: str | None = Query(None),
    background: BackgroundTasks = BackgroundTasks(),
):
    """Update work item fields."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    fields, params = [], []
    if body.ai_name             is not None: fields.append("ai_name=%s");             params.append(body.ai_name)
    if body.ai_desc             is not None: fields.append("ai_desc=%s");             params.append(body.ai_desc)
    if body.status_user         is not None: fields.append("status_user=%s");         params.append(body.status_user)
    if body.status_ai           is not None: fields.append("status_ai=%s");           params.append(body.status_ai)
    if body.requirements        is not None: fields.append("requirements=%s");        params.append(body.requirements)
    if body.acceptance_criteria is not None: fields.append("acceptance_criteria=%s"); params.append(body.acceptance_criteria)
    if body.action_items        is not None: fields.append("action_items=%s");        params.append(body.action_items)
    if body.code_summary        is not None: fields.append("code_summary=%s");        params.append(body.code_summary)
    if body.summary             is not None: fields.append("summary=%s");             params.append(body.summary)
    if body.tags                is not None:
        import json as _json
        fields.append("tags=%s"); params.append(_json.dumps(body.tags))
    if body.ai_tags             is not None:
        import json as _json
        fields.append("ai_tags = ai_tags || %s::jsonb"); params.append(_json.dumps(body.ai_tags))
    if body.tag_id              is not None:
        fields.append("tag_id=%s")
        params.append(body.tag_id if body.tag_id else None)
    if body.ai_tag_id           is not None:
        fields.append("ai_tag_id=%s")
        params.append(body.ai_tag_id if body.ai_tag_id else None)
    if body.merged_into         is not None:
        fields.append("merged_into=%s")
        params.append(body.merged_into if body.merged_into else None)
    if body.start_date is not None:
        fields.append("start_date=%s")
        params.append(body.start_date if body.start_date else None)
    if body.status_user == 'in_progress':
        fields.append("start_date=COALESCE(start_date, NOW())")

    if not fields:
        raise HTTPException(400, "Nothing to update")

    fields.append("updated_at=NOW()")
    params.append(item_id)
    params.append(p_id)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE mem_ai_work_items SET {','.join(fields)} WHERE id=%s::uuid AND project_id=%s RETURNING id, status_user",
                params,
            )
            result = cur.fetchone()
            if not result:
                raise HTTPException(404, "Work item not found")

    body_dict = body.model_dump(exclude_none=True)
    content_fields = {"ai_name", "ai_desc", "requirements", "summary", "code_summary"}
    if any(f in body_dict for f in content_fields):
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT ai_name, ai_desc, requirements, summary FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s",
                    (item_id, p_id),
                )
                row = cur.fetchone()
        if row:
            asyncio.create_task(_embed_work_item(p_id, item_id, row[0], row[1] or "", row[2] or "", row[3] or ""))
        background.add_task(_run_matching, p, item_id)

    asyncio.create_task(_trigger_memory_regen(p))
    return {"ok": True, "id": item_id, "status_user": result[1]}


@router.delete("/{item_id}")
async def delete_work_item(item_id: str, project: str | None = Query(None)):
    """Delete a work item."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_WORK_ITEM, (item_id, p_id))
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")
    return {"ok": True}


@router.post("/{item_id}/extract")
async def extract_work_item_code(item_id: str, project: str | None = Query(None)):
    """Aggregate commits linked to this work item + LLM extraction → populate ai_tags."""
    _require_db()
    p = _project(project)
    from memory.memory_extraction import MemoryExtraction
    result = await MemoryExtraction().extract_work_item_code_summary(p, item_id)
    return result



# ── Lookup by sequential number ───────────────────────────────────────────────

@router.get("/number/{seq_num}")
async def get_work_item_by_number(seq_num: int, project: str | None = Query(None)):
    """Resolve a short sequential number (e.g. #10005) to the full work item."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_WORK_ITEM_BY_SEQ, (p_id, seq_num))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, f"Work item #{seq_num} not found in project {p!r}")
            cols = [d[0] for d in cur.description]
            row = dict(zip(cols, r))
            row["id"] = str(row["id"])
            for dt_field in ("created_at", "updated_at"):
                if row.get(dt_field):
                    row[dt_field] = row[dt_field].isoformat()
            if row.get("tag_id"):
                row["tag_id"] = str(row["tag_id"])
            if row.get("ai_tag_id"):
                row["ai_tag_id"] = str(row["ai_tag_id"])
            return row


# ── Interactions for a work item ──────────────────────────────────────────────

@router.get("/{item_id}/interactions")
async def get_work_item_interactions(
    item_id: str,
    project: str | None = Query(None),
    limit:   int        = Query(20),
):
    """Return recent interactions tagged to this work item."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_INTERACTIONS, (item_id, p_id, limit))
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)
    return {"interactions": rows, "work_item_id": item_id, "project": p}


# ── Merge two work items ─────────────────────────────────────────────────────


@router.post("/{item_id}/merge", status_code=201)
async def merge_work_item_into(
    item_id: str,
    body: WorkItemMerge,
    background_tasks: BackgroundTasks,
    project: str | None = Query(None),
):
    """Merge item_id and body.merge_with into a new combined work item.
    Both originals are marked merged_into=<new_id>, status_user='done'.
    """
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, ai_category, ai_name, ai_desc, requirements, action_items, "
                "acceptance_criteria, summary, tag_id, seq_num "
                "FROM mem_ai_work_items WHERE project_id=%s AND id=ANY(%s::uuid[])",
                (p_id, [item_id, body.merge_with]),
            )
            rows = cur.fetchall()

    if len(rows) < 2:
        raise HTTPException(404, "One or both work items not found")

    a = dict(zip(["id","ai_category","ai_name","ai_desc","requirements","action_items",
                  "acceptance_criteria","summary","tag_id","seq_num"], rows[0]))
    b = dict(zip(["id","ai_category","ai_name","ai_desc","requirements","action_items",
                  "acceptance_criteria","summary","tag_id","seq_num"], rows[1]))

    # Build merged item — combine fields, prefer non-empty values
    import json as _json
    new_name        = f"{a['ai_name']} + {b['ai_name']}"
    new_desc        = f"{a['ai_desc'] or ''}\n{b['ai_desc'] or ''}".strip()
    new_req         = f"{a['requirements'] or ''}\n{b['requirements'] or ''}".strip()
    new_actions     = f"{a['action_items'] or ''}\n{b['action_items'] or ''}".strip()
    new_criteria    = f"{a['acceptance_criteria'] or ''}\n{b['acceptance_criteria'] or ''}".strip()
    new_category    = a['ai_category']  # use first item's category
    linked_tag_id   = a['tag_id'] or b['tag_id']  # keep any linked tag

    with db.conn() as conn:
        with conn.cursor() as cur:
            seq = next_seq(cur, p_id, new_category)
            cur.execute(
                """INSERT INTO mem_ai_work_items
                       (project_id, ai_category, ai_name, ai_desc, requirements,
                        action_items, acceptance_criteria, tag_id, status_user, status_ai, seq_num)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'active','active',%s)
                   ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
                   RETURNING id""",
                (p_id, new_category, new_name, new_desc, new_req,
                 new_actions, new_criteria,
                 str(linked_tag_id) if linked_tag_id else None, seq),
            )
            new_row = cur.fetchone()
            if not new_row:
                raise HTTPException(409, f"Merged item '{new_name}' already exists")
            new_id = str(new_row[0])

            # Mark both originals as merged
            cur.execute(
                "UPDATE mem_ai_work_items SET merged_into=%s::uuid, status_user='done', updated_at=NOW() "
                "WHERE id=ANY(%s::uuid[]) AND project_id=%s",
                (new_id, [item_id, body.merge_with], p_id),
            )

    asyncio.create_task(_embed_work_item(p_id, new_id, new_name, new_desc, new_req, ""))
    asyncio.create_task(_trigger_memory_regen(p))
    background_tasks.add_task(_run_matching, p, new_id)

    return {"id": new_id, "ai_name": new_name, "ai_category": new_category,
            "merged_from": [item_id, body.merge_with], "project": p}


@router.post("/{item_id}/dismerge", status_code=200)
async def dismerge_work_item(item_id: str, project: str | None = Query(None)):
    """Roll back a merge: restore original work items, delete the merged result.
    Sets merged_into=NULL, status_user='active' on all originals; deletes the merged item.
    """
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Restore originals
            cur.execute(
                "UPDATE mem_ai_work_items "
                "SET merged_into=NULL, status_user='active', updated_at=NOW() "
                "WHERE merged_into=%s::uuid AND project_id=%s RETURNING id",
                (item_id, p_id),
            )
            restored = [str(r[0]) for r in cur.fetchall()]
            if not restored:
                raise HTTPException(404, "No merged source items found for this work item")
            # Delete the merged result
            cur.execute(
                "DELETE FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s",
                (item_id, p_id),
            )
    asyncio.create_task(_trigger_memory_regen(p))
    return {"ok": True, "restored": restored, "deleted": item_id, "project": p}


# ── Commits linked to a work item ────────────────────────────────────────────

@router.get("/{item_id}/commits")
async def get_work_item_commits(
    item_id: str,
    project: str | None = Query(None),
    limit:   int        = Query(20),
):
    """Return commits tagged to this work item (via mem_mrr_commits.tags['work-item']=id)."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_COMMITS, (p_id, item_id, limit))
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("committed_at"):
                    row["committed_at"] = row["committed_at"].isoformat()
                rows.append(row)
    return {"commits": rows, "work_item_id": item_id, "project": p}


# ── Per-work-item statistics ──────────────────────────────────────────────────

@router.get("/{item_id}/stats")
async def get_work_item_stats(
    item_id: str,
    project: str | None = Query(None),
):
    """Return aggregated stats for a work item: prompt count, commit count,
    files/rows changed, symbols touched, and languages breakdown.

    All stats are derived from mem_mrr_commits and mem_mrr_commits_code rows
    tagged with 'work-item': item_id.
    """
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    # Each placeholder pair (project_id, item_id) repeated 7 times for 7 subqueries
    params = (p_id, item_id) * 7
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_WORK_ITEM_STATS, params)
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
    if not row:
        return {"work_item_id": item_id, "project": p, "stats": {}}
    stats = dict(zip(cols, row))
    return {"work_item_id": item_id, "project": p, "stats": stats}


# ── Semantic search ───────────────────────────────────────────────────────────

@router.get("/search")
async def search_work_items(
    query:    str            = Query(..., description="Natural language query"),
    project:  str | None     = Query(None),
    category: str | None     = Query(None, description="Filter by category: feature, bug, task"),
    limit:    int            = Query(10, ge=1, le=50),
):
    """Semantic search over work items using pgvector cosine similarity."""
    _require_db()
    from memory.memory_embedding import _embed
    p = _project(project)
    vec = await _embed(query)
    if not vec:
        raise HTTPException(503, "Embedding unavailable — check OpenAI API key")
    vec_str = f"[{','.join(str(x) for x in vec)}]"
    p_id = db.get_or_create_project_id(p)
    where = "project_id=%s AND embedding IS NOT NULL"
    where_params: list = [p_id]
    if category:
        where += " AND ai_category=%s"
        where_params.append(category)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, ai_name, ai_category, ai_desc, status_user,
                           acceptance_criteria, seq_num,
                           1 - (embedding <=> %s::vector) AS score
                    FROM mem_ai_work_items
                    WHERE {where}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s""",
                [vec_str] + where_params + [vec_str, limit],
            )
            rows = cur.fetchall()
    return {
        "results": [
            {
                "id": str(r[0]), "ai_name": r[1], "category": r[2],
                "ai_desc": (r[3] or "")[:300],
                "status_user": r[4],
                "criteria_preview": (r[5] or "")[:200],
                "seq_num": r[6], "score": round(float(r[7]), 4),
            }
            for r in rows
        ],
        "query": query, "project": p, "total": len(rows),
    }


@router.get("/facts/search")
async def search_project_facts(
    query:   str        = Query(..., description="Natural language query"),
    project: str | None = Query(None),
    limit:   int        = Query(10, ge=1, le=50),
):
    """Semantic search over current project facts using pgvector cosine similarity."""
    _require_db()
    from memory.memory_embedding import _embed
    p = _project(project)
    vec = await _embed(query)
    if not vec:
        raise HTTPException(503, "Embedding unavailable — check OpenAI API key")
    vec_str = f"[{','.join(str(x) for x in vec)}]"
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, fact_key, fact_value, category, valid_from,
                          1 - (embedding <=> %s::vector) AS score
                   FROM mem_ai_project_facts
                   WHERE project_id=%s AND valid_until IS NULL AND embedding IS NOT NULL
                   ORDER BY embedding <=> %s::vector
                   LIMIT %s""",
                (vec_str, p_id, vec_str, limit),
            )
            rows = cur.fetchall()
    return {
        "results": [
            {
                "id": str(r[0]), "fact_key": r[1], "fact_value": r[2],
                "category": r[3],
                "valid_from": r[4].isoformat() if r[4] else None,
                "score": round(float(r[5]), 4),
            }
            for r in rows
        ],
        "query": query, "project": p, "total": len(rows),
    }


# ── Project facts ─────────────────────────────────────────────────────────────

@router.get("/facts")
async def get_project_facts(project: str | None = Query(None)):
    """Return current (valid_until IS NULL) project facts."""
    if not db.is_available():
        return {"facts": [], "project": _project(project), "total": 0, "fallback": True}
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_FACTS, (p_id,))
            cols = [d[0] for d in cur.description]
            facts = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("valid_from"):
                    row["valid_from"] = row["valid_from"].isoformat()
                facts.append(row)
    return {"facts": facts, "project": p, "total": len(facts)}


# ── Memory items ──────────────────────────────────────────────────────────────

@router.get("/memory-items")
async def get_memory_items(
    project: str | None = Query(None),
    scope:   str | None = Query(None),   # "session" | "feature"
    limit:   int        = Query(20),
):
    """Return recent memory events (distilled session/feature summaries)."""
    _require_db()
    p = _project(project)
    p_id = db.get_or_create_project_id(p)
    where_parts = ["project_id=%s"]
    params: list = [p_id]
    if scope:
        where_parts.append("event_type=%s"); params.append(scope)

    sql = _SQL_GET_MEMORY_ITEMS.format(where=" AND ".join(where_parts))
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params + [limit])
            cols = [d[0] for d in cur.description]
            items = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                items.append(row)
    return {"memory_items": items, "project": p, "total": len(items)}
