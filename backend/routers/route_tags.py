"""
route_tags.py — Unified tag management router.

Manages the per-project tag registry (planner_tags), global categories (mng_tags_categories),
source-tag links (mem_mrr_tags), and session context persistence.

Replaces mng_entity_categories + mng_entity_values with a cleaner hierarchy.

Endpoints:
    Tags:
        GET    /tags                  list tags as tree (children[] nested)
        POST   /tags                  create tag
        PATCH  /tags/{id}             update tag
        DELETE /tags/{id}             delete tag (block if has sources)
        POST   /tags/merge            merge two tags

    Sources:
        GET    /tags/{id}/sources     all prompts/commits/items tagged with this tag
        POST   /tags/source           add source-tag link
        DELETE /tags/source/{id}      remove source-tag link

    Session context:
        GET    /tags/session-context  last used tags for project
        POST   /tags/session-context  save tags for project

    Categories (global):
        GET    /tags/categories       list mng_tags_categories
        POST   /tags/categories       create category
        PATCH  /tags/categories/{id}  update category
        DELETE /tags/categories/{id}  delete category (only if no tags reference it)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.database import db, build_update

log = logging.getLogger(__name__)

router = APIRouter()

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.lifecycle, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           tm.description, tm.due_date, tm.priority,
           (SELECT COUNT(*) FROM mem_mrr_tags st WHERE st.tag_id = t.id) AS source_count
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    WHERE t.client_id = 1 AND t.project = %s
      AND t.merged_into IS NULL
    ORDER BY t.created_at
"""

_SQL_GET_TAG = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.lifecycle, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           tm.description, tm.due_date, tm.priority, tm.requirements, tm.requester, tm.extra
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    WHERE t.client_id = 1 AND t.project = %s AND t.id = %s::uuid
"""

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (client_id, project, name, category_id, parent_id, status, lifecycle)
    VALUES (1, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (client_id, project, name) DO NOTHING
    RETURNING id, name, created_at
"""

_SQL_DELETE_TAG = """
    DELETE FROM planner_tags WHERE id = %s::uuid AND client_id = 1 AND project = %s
    RETURNING id
"""

_SQL_CHECK_TAG_SOURCES = """
    SELECT COUNT(*) FROM mem_mrr_tags WHERE tag_id = %s::uuid
"""

_SQL_GET_TAG_SOURCES = """
    SELECT 'prompt' AS source_type, p.id::text AS source_id, p.prompt AS content, p.created_at,
           p.session_id, NULL::text AS commit_hash
    FROM mem_mrr_tags st
    JOIN mem_mrr_prompts p ON p.id = st.prompt_id
    WHERE st.tag_id = %s::uuid AND st.prompt_id IS NOT NULL
    UNION ALL
    SELECT 'commit' AS source_type, c.id::text AS source_id, c.commit_msg AS content, c.created_at,
           c.session_id, c.commit_hash
    FROM mem_mrr_tags st
    JOIN mem_mrr_commits c ON c.id = st.commit_id
    WHERE st.tag_id = %s::uuid AND st.commit_id IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 100
"""

_SQL_INSERT_SOURCE_TAG = """
    INSERT INTO mem_mrr_tags
           (tag_id, session_id, session_src_id, session_src_desc,
            prompt_id, commit_id, item_id, message_id, auto_tagged)
    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
"""

_SQL_DELETE_SOURCE_TAG = """
    DELETE FROM mem_mrr_tags WHERE id = %s::uuid RETURNING id
"""

_SQL_GET_SESSION_CONTEXT = """
    SELECT extra FROM mng_session_tags
    WHERE client_id = 1 AND project = %s
"""

_SQL_UPSERT_SESSION_CONTEXT = """
    INSERT INTO mng_session_tags (client_id, project, extra, updated_at)
    VALUES (1, %s, %s::jsonb, NOW())
    ON CONFLICT (client_id, project) DO UPDATE
    SET extra = mng_session_tags.extra || EXCLUDED.extra, updated_at = NOW()
"""

_SQL_LIST_CATEGORIES = """
    SELECT id, name, color, icon, description, created_at
    FROM mng_tags_categories
    WHERE client_id = 1
    ORDER BY name
"""

_SQL_INSERT_CATEGORY = """
    INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
    VALUES (1, %s, %s, %s, %s)
    ON CONFLICT (client_id, name) DO NOTHING
    RETURNING id, name
"""

_SQL_DELETE_CATEGORY = """
    DELETE FROM mng_tags_categories WHERE id = %s AND client_id = 1
    RETURNING id
"""

_SQL_CHECK_CATEGORY_IN_USE = """
    SELECT COUNT(*) FROM planner_tags WHERE category_id = %s AND client_id = 1
"""

# ── Pydantic models ───────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    project: str
    name: str
    category_id: Optional[int] = None
    parent_id: Optional[str] = None
    status: str = "active"
    lifecycle: str = "idea"


class TagUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    lifecycle: Optional[str] = None
    seq_num: Optional[int] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[int] = None
    requester: Optional[str] = None


class TagMerge(BaseModel):
    project: str
    from_name: str
    into_name: str


class SourceTagCreate(BaseModel):
    tag_id: str
    session_id: Optional[str] = None
    session_src_id: Optional[str] = None
    session_src_desc: Optional[str] = None
    prompt_id: Optional[str] = None
    commit_id: Optional[int] = None
    item_id: Optional[str] = None
    message_id: Optional[str] = None
    auto_tagged: bool = False


class CategoryCreate(BaseModel):
    name: str
    color: str = "#4a90e2"
    icon: str = "⬡"
    description: str = ""


class CategoryUpdate(BaseModel):
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")


def _row_to_tag(row: tuple) -> dict:
    return {
        "id":            str(row[0]),
        "name":          row[1],
        "category_id":   row[2],
        "parent_id":     str(row[3]) if row[3] else None,
        "merged_into":   str(row[4]) if row[4] else None,
        "status":        row[5],
        "lifecycle":     row[6],
        "seq_num":       row[7],
        "created_at":    row[8].isoformat() if row[8] else None,
        "category_name": row[9],
        "color":         row[10] or "#4a90e2",
        "icon":          row[11] or "⬡",
        "description":   row[12] or "",
        "due_date":      row[13].isoformat() if row[13] else None,
        "priority":      row[14] or 3,
        "source_count":  row[15] if len(row) > 15 else 0,
        "children":      [],
    }


def _build_tree(tags: list[dict]) -> list[dict]:
    """Build a parent→children tree from a flat list."""
    by_id = {t["id"]: t for t in tags}
    roots = []
    for tag in tags:
        pid = tag.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(tag)
        else:
            roots.append(tag)
    return roots


# ── Tag endpoints ─────────────────────────────────────────────────────────────

@router.get("")
async def list_tags(project: str = Query(...)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_TAGS, (project,))
            rows = cur.fetchall()
    tags = [_row_to_tag(r) for r in rows]
    return _build_tree(tags)


@router.post("")
async def create_tag(body: TagCreate):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_TAG,
                (body.project, body.name, body.category_id,
                 body.parent_id, body.status, body.lifecycle),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=409, detail=f"Tag '{body.name}' already exists in project '{body.project}'")
    return {"id": str(row[0]), "name": row[1], "created_at": row[2].isoformat() if row[2] else None}


@router.patch("/{tag_id}")
async def update_tag(tag_id: str, body: TagUpdate):
    _require_db()
    tag_fields: dict = {}
    meta_fields: dict = {}
    if body.name is not None:
        tag_fields["name"] = body.name
    if body.category_id is not None:
        tag_fields["category_id"] = body.category_id
    if body.parent_id is not None:
        tag_fields["parent_id"] = body.parent_id
    if body.status is not None:
        tag_fields["status"] = body.status
    if body.lifecycle is not None:
        tag_fields["lifecycle"] = body.lifecycle
    if body.seq_num is not None:
        tag_fields["seq_num"] = body.seq_num
    if body.description is not None:
        meta_fields["description"] = body.description
    if body.requirements is not None:
        meta_fields["requirements"] = body.requirements
    if body.due_date is not None:
        meta_fields["due_date"] = body.due_date
    if body.priority is not None:
        meta_fields["priority"] = body.priority
    if body.requester is not None:
        meta_fields["requester"] = body.requester

    with db.conn() as conn:
        with conn.cursor() as cur:
            if tag_fields:
                sql, vals = build_update("planner_tags", tag_fields, "id = %s::uuid AND client_id = 1")
                cur.execute(sql, (*vals, tag_id))
            if meta_fields:
                cur.execute(
                    "SELECT project FROM planner_tags WHERE id = %s::uuid AND client_id = 1",
                    (tag_id,),
                )
                proj_row = cur.fetchone()
                if proj_row:
                    now = datetime.now(timezone.utc)
                    col_names = ", ".join(meta_fields.keys())
                    placeholders = ", ".join(["%s"] * len(meta_fields))
                    updates = ", ".join(f"{k} = EXCLUDED.{k}" for k in meta_fields)
                    cur.execute(
                        f"""INSERT INTO planner_tags_meta (tag_id, client_id, project, {col_names}, updated_at)
                            VALUES (%s::uuid, 1, %s, {placeholders}, %s)
                            ON CONFLICT (tag_id) DO UPDATE SET
                            {updates},
                            updated_at = NOW()""",
                        (tag_id, proj_row[0], *meta_fields.values(), now),
                    )
    return {"ok": True}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, project: str = Query(...), force: bool = Query(False)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            if not force:
                cur.execute(_SQL_CHECK_TAG_SOURCES, (tag_id,))
                count = cur.fetchone()[0]
                if count > 0:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Tag has {count} source links. Use force=true to delete anyway.",
                    )
            cur.execute(_SQL_DELETE_TAG, (tag_id, project))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"ok": True, "id": str(row[0])}


@router.post("/merge")
async def merge_tags(body: TagMerge):
    """Mark from_name as merged into into_name; re-link all source_tags."""
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s",
                (body.project, body.from_name),
            )
            from_row = cur.fetchone()
            cur.execute(
                "SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s",
                (body.project, body.into_name),
            )
            into_row = cur.fetchone()
            if not from_row:
                raise HTTPException(status_code=404, detail=f"Tag '{body.from_name}' not found")
            if not into_row:
                raise HTTPException(status_code=404, detail=f"Tag '{body.into_name}' not found")
            from_id, into_id = from_row[0], into_row[0]
            cur.execute(
                "UPDATE mem_mrr_tags SET tag_id = %s WHERE tag_id = %s",
                (into_id, from_id),
            )
            cur.execute(
                "UPDATE planner_tags SET merged_into = %s, status = 'archived' WHERE id = %s",
                (into_id, from_id),
            )
    return {"ok": True, "merged_into": str(into_id)}


# ── Source endpoints ──────────────────────────────────────────────────────────

@router.get("/{tag_id}/sources")
async def get_tag_sources(tag_id: str, project: str = Query(...)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_TAG_SOURCES, (tag_id, tag_id))
            rows = cur.fetchall()
    return [
        {
            "source_type": row[0],
            "source_id":   row[1],
            "content":     (row[2] or "")[:300],
            "created_at":  row[3].isoformat() if row[3] else None,
            "session_id":  row[4],
            "commit_hash": row[5],
        }
        for row in rows
    ]


@router.post("/source")
async def add_source_tag(body: SourceTagCreate):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_SOURCE_TAG,
                (body.tag_id, body.session_id, body.session_src_id, body.session_src_desc,
                 body.prompt_id, body.commit_id, body.item_id, body.message_id, body.auto_tagged),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=409, detail="Source-tag link already exists")
    return {"id": str(row[0])}


@router.delete("/source/{source_tag_id}")
async def remove_source_tag(source_tag_id: str):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_SOURCE_TAG, (source_tag_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Source-tag link not found")
    return {"ok": True}


# ── Session context endpoints ─────────────────────────────────────────────────

@router.get("/session-context")
async def get_session_context(project: str = Query(...)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SESSION_CONTEXT, (project,))
            row = cur.fetchone()
    if not row or not row[0]:
        return {"tags": {"stage": "discovery"}}
    extra = row[0] if isinstance(row[0], dict) else {}
    return {"tags": extra.get("tags", extra)}


@router.post("/session-context")
async def save_session_context(project: str = Query(...), body: dict = {}):
    _require_db()
    tags = body.get("tags", body)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPSERT_SESSION_CONTEXT,
                (project, json.dumps({"tags": tags})),
            )
    return {"ok": True}


# ── Category endpoints ────────────────────────────────────────────────────────

@router.get("/categories")
async def list_categories():
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_CATEGORIES)
            rows = cur.fetchall()
    return [
        {
            "id":          row[0],
            "name":        row[1],
            "color":       row[2],
            "icon":        row[3],
            "description": row[4] or "",
            "created_at":  row[5].isoformat() if row[5] else None,
        }
        for row in rows
    ]


@router.post("/categories")
async def create_category(body: CategoryCreate):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_CATEGORY,
                (body.name, body.color, body.icon, body.description),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=409, detail=f"Category '{body.name}' already exists")
    return {"id": row[0], "name": row[1]}


@router.patch("/categories/{cat_id}")
async def update_category(cat_id: int, body: CategoryUpdate):
    _require_db()
    fields: dict = {}
    if body.color is not None:
        fields["color"] = body.color
    if body.icon is not None:
        fields["icon"] = body.icon
    if body.description is not None:
        fields["description"] = body.description
    if not fields:
        return {"ok": True}
    with db.conn() as conn:
        with conn.cursor() as cur:
            sql, vals = build_update("mng_tags_categories", fields, "id = %s AND client_id = 1")
            cur.execute(sql, (*vals, cat_id))
    return {"ok": True}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_CHECK_CATEGORY_IN_USE, (cat_id,))
            count = cur.fetchone()[0]
            if count > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Category is referenced by {count} tag(s). Remove tags first.",
                )
            cur.execute(_SQL_DELETE_CATEGORY, (cat_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"ok": True}


# ── AI tag suggestion endpoints ───────────────────────────────────────────────

class SuggestionApplyBody(BaseModel):
    source_type: str
    source_id: str
    tag_name: str
    session_id: Optional[str] = None
    session_src_desc: Optional[str] = None


class SuggestionIgnoreBody(BaseModel):
    source_type: str
    source_id: str


@router.post("/suggestions/generate")
async def generate_tag_suggestions(project: str = Query(...)):
    """Suggest planner_tags for all untagged mirroring rows (ai_tags IS NULL).

    Calls Haiku once per row with the ai_tag_suggestion prompt.
    Returns: {suggestions: [...], total_untagged: N}
    """
    _require_db()
    from memory.memory_tagging import MemoryTagging
    from memory.memory_mirroring import MemoryMirroring

    tagging = MemoryTagging()
    mirroring = MemoryMirroring()

    total_untagged = sum(
        len(mirroring.get_untagged(project, stype, limit=1000))
        for stype in ("prompt", "commit", "item")
    )

    suggestions = await tagging.suggest_tags_for_untagged(project, batch_size=20)
    return {"suggestions": suggestions, "total_untagged": total_untagged}


@router.post("/suggestions/apply")
async def apply_tag_suggestion(project: str = Query(...), body: SuggestionApplyBody = ...):
    """Apply an AI tag suggestion: create/get tag, link to source, mark 'approved'."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    tagging = MemoryTagging()
    ok = await tagging.apply_suggestion(
        project, body.source_type, body.source_id, body.tag_name,
        session_id=body.session_id, session_src_desc=body.session_src_desc,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to apply suggestion")
    return {"ok": True}


@router.post("/suggestions/ignore")
async def ignore_tag_suggestion(project: str = Query(...), body: SuggestionIgnoreBody = ...):
    """Mark a source row's AI tagging as 'ignored'."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    MemoryTagging().ignore_suggestion(body.source_type, body.source_id)
    return {"ok": True}


# ── Tag relation endpoints ────────────────────────────────────────────────────

class RelationCreate(BaseModel):
    from_tag_id: str
    relation: str
    to_tag_id: str
    note: Optional[str] = None
    source: str = "manual"


@router.get("/relations")
async def list_tag_relations(project: str = Query(...)):
    """List mng_ai_tags_relations for tags belonging to a project."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    return MemoryTagging().get_relations(project)


@router.post("/relations")
async def create_tag_relation(body: RelationCreate):
    """Add a relationship between two planner_tags."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    MemoryTagging().add_relation(
        body.from_tag_id, body.relation, body.to_tag_id,
        note=body.note, source=body.source,
    )
    return {"ok": True}


@router.delete("/relations/{relation_id}")
async def delete_tag_relation(relation_id: str):
    """Remove a tag relation by UUID."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    deleted = MemoryTagging().delete_relation(relation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relation not found")
    return {"ok": True}
