"""
route_tags.py — Unified tag management router.

Manages the per-project tag registry (planner_tags), global categories (mng_tags_categories),
source-tag links (mem_tags_relations), and session context persistence.

Endpoints:
    Tags:
        GET    /tags                  list tags as tree (children[] nested)
        POST   /tags                  create tag
        PATCH  /tags/{id}             update tag
        DELETE /tags/{id}             delete tag (block if has sources)
        POST   /tags/merge            merge two tags

    Sources:
        GET    /tags/{id}/sources     all prompts/commits/items linked via mem_tags_relations
        POST   /tags/source           add source-tag link (mem_tags_relations)
        DELETE /tags/source/{id}      remove source-tag link

    Relations:
        GET    /tags/relations        get mem_tags_relations rows filtered by tag_id or work_item_id
        PATCH  /tags/relations/{id}   approve or reject a relation

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
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.database import db, build_update

log = logging.getLogger(__name__)

router = APIRouter()


async def _trigger_memory_regen(project: str, tag_name: str | None = None) -> None:
    """Background task: regenerate root + optional feature context files."""
    try:
        from memory.memory_files import MemoryFiles
        mf = MemoryFiles()
        await asyncio.get_event_loop().run_in_executor(
            None, mf.write_root_files, project
        )
        if tag_name:
            await asyncio.get_event_loop().run_in_executor(
                None, mf.write_feature_files, project, tag_name
            )
    except Exception as e:
        log.debug(f"_trigger_memory_regen error: {e}")

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_TAGS = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.description, t.due_date, t.priority,
           t.creator, t.requirements, t.acceptance_criteria,
           t.action_items, t.deliveries, t.requester,
           0 AS source_count,
           t.updater, t.updated_at
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.project_id = %s
      AND t.merged_into IS NULL
    ORDER BY t.created_at
"""
# column indices for _row_to_tag (LIST — has source_count):
#  0 id  1 name  2 category_id  3 parent_id  4 merged_into
#  5 status  6 created_at  7 category_name  8 color  9 icon
# 10 description  11 due_date  12 priority  13 creator
# 14 requirements  15 acceptance_criteria  16 action_items  17 deliveries
# 18 requester  19 source_count  20 updater  21 updated_at

_SQL_GET_TAG = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.description, t.due_date, t.priority,
           t.creator, t.requirements, t.acceptance_criteria,
           t.action_items, t.deliveries, t.requester,
           t.updater, t.updated_at
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.project_id = %s AND t.id = %s::uuid
"""
# column indices for _row_to_tag_detail (GET — no source_count):
#  0 id  1 name  2 category_id  3 parent_id  4 merged_into
#  5 status  6 created_at  7 category_name  8 color  9 icon
# 10 description  11 due_date  12 priority  13 creator
# 14 requirements  15 acceptance_criteria  16 action_items  17 deliveries
# 18 requester  19 updater  20 updated_at

_SQL_LIST_DELIVERIES = """
    SELECT id, category, type, label, sort_order
    FROM mng_deliveries
    ORDER BY category, sort_order, label
"""

_SQL_INSERT_DELIVERY = """
    INSERT INTO mng_deliveries (category, type, label, sort_order)
    VALUES (%s, %s, %s, %s)
    RETURNING id, category, type, label, sort_order
"""

_SQL_DELETE_DELIVERY = "DELETE FROM mng_deliveries WHERE id = %s RETURNING id"

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (project_id, name, category_id, parent_id, status, creator, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (project_id, name, category_id) DO NOTHING
    RETURNING id, name, created_at
"""

_SQL_DELETE_TAG = """
    DELETE FROM planner_tags WHERE id = %s::uuid AND project_id = %s
    RETURNING id
"""









_SQL_GET_SESSION_CONTEXT = """
    SELECT extra FROM mng_session_tags
    WHERE project_id = %s
"""

_SQL_UPSERT_SESSION_CONTEXT = """
    INSERT INTO mng_session_tags (project_id, extra, updated_at)
    VALUES (%s, %s::jsonb, NOW())
    ON CONFLICT (project_id) DO UPDATE
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
    status: str = "open"
    creator: str = "user"


class TagUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    parent_id: Optional[str] = None
    merged_into: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    action_items: Optional[str] = None
    deliveries: Optional[list] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    requester: Optional[str] = None
    creator: Optional[str] = None
    updater: Optional[str] = None


class DeliveryCreate(BaseModel):
    category: str
    type: str
    label: str
    sort_order: int = 0


class TagMerge(BaseModel):
    project: str
    from_name: str
    into_name: str


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
    # Column order matches _SQL_LIST_TAGS (LIST — has source_count):
    #  0 id  1 name  2 category_id  3 parent_id  4 merged_into
    #  5 status  6 created_at  7 category_name  8 color  9 icon
    # 10 description  11 due_date  12 priority  13 creator
    # 14 requirements  15 acceptance_criteria  16 action_items  17 deliveries
    # 18 requester  19 source_count  20 updater  21 updated_at
    return {
        "id":                  str(row[0]),
        "name":                row[1],
        "category_id":         row[2],
        "parent_id":           str(row[3]) if row[3] else None,
        "merged_into":         str(row[4]) if row[4] else None,
        "status":              row[5],
        "created_at":          row[6].isoformat() if row[6] else None,
        "category_name":       row[7],
        "color":               row[8] or "#4a90e2",
        "icon":                row[9] or "⬡",
        "description":         row[10] or "",
        "due_date":            row[11].isoformat() if row[11] else None,
        "priority":            row[12] if row[12] is not None else 3,
        "creator":             row[13] or "user",
        "requirements":        row[14] or "",
        "acceptance_criteria": row[15] or "",
        "action_items":        row[16] or "",
        "deliveries":          row[17] or [],
        "requester":           row[18] or "",
        "source_count":        row[19] if len(row) > 19 else 0,
        "updater":             row[20] or "user",
        "updated_at":          row[21].isoformat() if len(row) > 21 and row[21] else None,
        "children":            [],
    }


def _row_to_tag_detail(row: tuple) -> dict:
    # Column order matches _SQL_GET_TAG (GET — no source_count):
    #  0 id  1 name  2 category_id  3 parent_id  4 merged_into
    #  5 status  6 created_at  7 category_name  8 color  9 icon
    # 10 description  11 due_date  12 priority  13 creator
    # 14 requirements  15 acceptance_criteria  16 action_items  17 deliveries
    # 18 requester  19 updater  20 updated_at
    return {
        "id":                  str(row[0]),
        "name":                row[1],
        "category_id":         row[2],
        "parent_id":           str(row[3]) if row[3] else None,
        "merged_into":         str(row[4]) if row[4] else None,
        "status":              row[5],
        "created_at":          row[6].isoformat() if row[6] else None,
        "category_name":       row[7],
        "color":               row[8] or "#4a90e2",
        "icon":                row[9] or "⬡",
        "description":         row[10] or "",
        "due_date":            row[11].isoformat() if row[11] else None,
        "priority":            row[12] if row[12] is not None else 3,
        "creator":             row[13] or "user",
        "requirements":        row[14] or "",
        "acceptance_criteria": row[15] or "",
        "action_items":        row[16] or "",
        "deliveries":          row[17] or [],
        "requester":           row[18] or "",
        "updater":             row[19] or "user",
        "updated_at":          row[20].isoformat() if row[20] else None,
        "children":            [],
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
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_TAGS, (project_id,))
            rows = cur.fetchall()
    tags = [_row_to_tag(r) for r in rows]
    return _build_tree(tags)


@router.post("")
async def create_tag(body: TagCreate):
    _require_db()
    from core.auth import ADMIN_USER_ID
    project_id = db.get_or_create_project_id(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_TAG,
                (project_id, body.name, body.category_id,
                 body.parent_id, body.status, body.creator, ADMIN_USER_ID),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=409, detail=f"Tag '{body.name}' already exists in project '{body.project}'")
    return {"id": str(row[0]), "name": row[1], "created_at": row[2].isoformat() if row[2] else None}


@router.patch("/{tag_id}")
async def update_tag(tag_id: str, body: TagUpdate):
    _require_db()
    fields: dict = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.category_id is not None:
        fields["category_id"] = body.category_id
    # parent_id can be explicitly set to None (clear parent) — check model_fields_set
    # When set to a value, put in fields dict; when explicitly null, handle separately below
    parent_id_clear = False
    if "parent_id" in body.model_fields_set:
        if body.parent_id is not None:
            fields["parent_id"] = body.parent_id
        else:
            parent_id_clear = True  # will emit "parent_id = NULL" in raw SQL
    if body.merged_into is not None:
        fields["merged_into"] = body.merged_into
    if body.status is not None:
        fields["status"] = body.status
    if body.description is not None:
        fields["description"] = body.description
    if body.requirements is not None:
        fields["requirements"] = body.requirements
    if body.acceptance_criteria is not None:
        fields["acceptance_criteria"] = body.acceptance_criteria
    if body.action_items is not None:
        fields["action_items"] = body.action_items
    if body.priority is not None:
        fields["priority"] = body.priority
    if body.due_date is not None:
        fields["due_date"] = body.due_date
    if body.requester is not None:
        fields["requester"] = body.requester
    if body.creator is not None:
        fields["creator"] = body.creator
    # updater: explicit override or default to 'user'
    fields["updater"] = body.updater or "user"

    # deliveries is JSONB — handled separately from build_update
    deliveries_sql = ""
    deliveries_val = None
    if body.deliveries is not None:
        deliveries_sql = ", deliveries = %s::jsonb"
        deliveries_val = json.dumps(body.deliveries)

    parent_null_sql = ", parent_id = NULL" if parent_id_clear else ""

    has_normal_fields = len(fields) > 1  # more than just updater
    if not has_normal_fields and deliveries_val is None and not parent_id_clear:
        return {"ok": True}

    with db.conn() as conn:
        with conn.cursor() as cur:
            set_clause, vals = build_update(fields)
            if deliveries_val is not None:
                vals = vals + [deliveries_val]
            cur.execute(
                f"UPDATE planner_tags SET {set_clause}{deliveries_sql}{parent_null_sql}, updated_at = NOW() "
                f"WHERE id = %s::uuid AND client_id = 1",
                vals + [tag_id],
            )
    return {"ok": True}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, project: str = Query(...), force: bool = Query(False)):
    _require_db()
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_TAG, (tag_id, project_id))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"ok": True, "id": str(row[0])}


@router.post("/merge")
async def merge_tags(body: TagMerge):
    """Mark from_name as merged into into_name; re-link all mem_tags_relations rows."""
    _require_db()
    project_id = db.get_or_create_project_id(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM planner_tags WHERE project_id=%s AND name=%s",
                (project_id, body.from_name),
            )
            from_row = cur.fetchone()
            cur.execute(
                "SELECT id FROM planner_tags WHERE project_id=%s AND name=%s",
                (project_id, body.into_name),
            )
            into_row = cur.fetchone()
            if not from_row:
                raise HTTPException(status_code=404, detail=f"Tag '{body.from_name}' not found")
            if not into_row:
                raise HTTPException(status_code=404, detail=f"Tag '{body.into_name}' not found")
            from_id, into_id = from_row[0], into_row[0]
            cur.execute(
                "UPDATE planner_tags SET merged_into = %s, status = 'archived' WHERE id = %s",
                (into_id, from_id),
            )
    return {"ok": True, "merged_into": str(into_id)}



@router.get("/{tag_id}/sources")
async def get_tag_sources(tag_id: str, project: str = Query(...)):
    """Return prompts and commits tagged with this tag via their tags[] array.

    Builds the tag string as "category:name" from the planner_tags row,
    then queries mem_mrr_prompts and mem_mrr_commits WHERE tag_str = ANY(tags).
    """
    _require_db()
    project_id = db.get_or_create_project_id(project)

    # Resolve tag string from UUID
    tag_str = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT tc.name || ':' || t.name FROM planner_tags t
                   JOIN mng_tags_categories tc ON tc.id = t.category_id
                   WHERE t.id=%s::uuid AND t.client_id=1 LIMIT 1""",
                (tag_id,),
            )
            row = cur.fetchone()
            if row:
                tag_str = row[0]

    if not tag_str:
        return []

    from core.tags import parse_tag as _parse_tag
    import json as _json
    _k, _v = _parse_tag(tag_str)
    tag_jsonb = _json.dumps({_k: _v})

    results = []
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_id, LEFT(prompt,300), session_id, created_at "
                "FROM mem_mrr_prompts WHERE project_id=%s AND tags @> %s::jsonb "
                "ORDER BY created_at DESC LIMIT 100",
                (project_id, tag_jsonb),
            )
            for row in cur.fetchall():
                results.append({
                    "related_type":  "prompt",
                    "related_id":    row[0],
                    "related_layer": "mirror",
                    "content":       row[1],
                    "session_id":    row[2],
                    "created_at":    row[3].isoformat() if row[3] else None,
                })
            cur.execute(
                "SELECT commit_hash, LEFT(commit_msg,300), session_id, created_at "
                "FROM mem_mrr_commits WHERE project_id=%s AND tags @> %s::jsonb "
                "ORDER BY created_at DESC LIMIT 100",
                (project_id, tag_jsonb),
            )
            for row in cur.fetchall():
                results.append({
                    "related_type":  "commit",
                    "related_id":    row[0],
                    "related_layer": "mirror",
                    "content":       row[1],
                    "session_id":    row[2],
                    "created_at":    row[3].isoformat() if row[3] else None,
                })
    return results


# ── Session context endpoints ─────────────────────────────────────────────────

@router.get("/session-context")
async def get_session_context(project: str = Query(...)):
    _require_db()
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SESSION_CONTEXT, (project_id,))
            row = cur.fetchone()
    if not row or not row[0]:
        return {"tags": {"stage": "discovery"}}
    extra = row[0] if isinstance(row[0], dict) else {}
    return {"tags": extra.get("tags", extra)}


@router.post("/session-context")
async def save_session_context(project: str = Query(...), body: dict = {}):
    _require_db()
    project_id = db.get_or_create_project_id(project)
    tags = body.get("tags", body)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPSERT_SESSION_CONTEXT,
                (project_id, json.dumps({"tags": tags})),
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
            set_clause, vals = build_update(fields)
            cur.execute(
                f"UPDATE mng_tags_categories SET {set_clause}, updated_at = NOW() "
                f"WHERE id = %s AND client_id = 1",
                vals + [cat_id],
            )
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


# ── Delivery endpoints ────────────────────────────────────────────────────────

@router.get("/deliveries")
async def list_deliveries():
    """Return all delivery types grouped by category.

    Response shape:
        {"code": [{"id":1,"type":"python","label":"Python","sort_order":10},...], ...}
    """
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_DELIVERIES)
            rows = cur.fetchall()
    result: dict = {}
    for row in rows:
        cat = row[1]
        if cat not in result:
            result[cat] = []
        result[cat].append({
            "id":         row[0],
            "type":       row[2],
            "label":      row[3],
            "sort_order": row[4],
        })
    return result


@router.post("/deliveries")
async def create_delivery(body: DeliveryCreate):
    """Admin: add a new delivery type to mng_deliveries."""
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_DELIVERY,
                (body.category, body.type, body.label, body.sort_order),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=409, detail=f"Delivery type '{body.type}' already exists in category '{body.category}'")
    return {"id": row[0], "category": row[1], "type": row[2], "label": row[3], "sort_order": row[4]}


@router.delete("/deliveries/{delivery_id}")
async def delete_delivery(delivery_id: int):
    """Admin: remove a delivery type from mng_deliveries."""
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_DELIVERY, (delivery_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Delivery type not found")
    return {"ok": True, "id": row[0]}


# ── AI tag suggestion endpoints ───────────────────────────────────────────────

@router.post("/suggestions/generate")
async def generate_tag_suggestions(project: str = Query(...)):
    """AI tag suggestions for MRR rows dropped — tags are now set explicitly via hooks.

    Returns empty suggestions list for backward compatibility.
    """
    return {
        "suggestions":        [],
        "total_untagged_mrr": 0,
        "total_untagged_ai":  0,
        "total_untagged":     0,
    }


# ── Tag context endpoint ───────────────────────────────────────────────────────

@router.get("/context")
async def get_tag_context(
    tag_name: str = Query(..., description="Tag name to retrieve full context for"),
    project:  str = Query(...),
    limit:    int = Query(20, ge=1, le=100),
):
    """Return comprehensive context for a tag: properties, AI events, source relations, work items.

    Used by the pipeline's first agent (PM) to orient on a feature/bug before planning.
    """
    _require_db()
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            # ── Tag properties ──────────────────────────────────────────────
            cur.execute(
                """SELECT t.id, t.name, t.category_id, t.parent_id,
                          c.name AS category_name, c.color, c.icon,
                          t.description, t.status, t.priority
                   FROM planner_tags t
                   LEFT JOIN mng_tags_categories c ON c.id = t.category_id
                   WHERE t.project_id=%s AND t.name=%s
                   LIMIT 1""",
                (project_id, tag_name),
            )
            tag_row = cur.fetchone()
            if not tag_row:
                raise HTTPException(404, f"Tag '{tag_name}' not found in project '{project}'")
            tag_id = str(tag_row[0])
            tag_info = {
                "id":          tag_id,
                "name":        tag_row[1],
                "category":    tag_row[4],
                "color":       tag_row[5],
                "icon":        tag_row[6],
                "description": tag_row[7] or "",
                "status":      tag_row[8],
                "priority":    tag_row[9] if tag_row[9] is not None else 3,
                "parent_id":   str(tag_row[3]) if tag_row[3] else None,
            }

            # ── Recent AI events removed (mem_ai_events table dropped) ────
            ai_events: list[dict] = []

            # ── Recent sources (prompts + commits via tags JSONB) ─────────────
            from core.tags import parse_tag as _parse_tag
            import json as _json
            tag_str_full = tag_info.get("category", "") + ":" + tag_info.get("name", "")
            _tk, _tv = _parse_tag(tag_str_full)
            tag_ctx_jsonb = _json.dumps({_tk: _tv})
            cur.execute(
                """SELECT source_id, 'prompt', created_at FROM mem_mrr_prompts
                   WHERE project_id=%s AND tags @> %s::jsonb
                   ORDER BY created_at DESC LIMIT %s""",
                (project_id, tag_ctx_jsonb, limit),
            )
            sources = [
                {
                    "related_type": "prompt",
                    "related_id":   r[0],
                    "related_layer": "mirror",
                    "created_at":   r[2].isoformat() if r[2] else None,
                }
                for r in cur.fetchall()
            ]
            cur.execute(
                """SELECT commit_hash, 'commit', created_at FROM mem_mrr_commits
                   WHERE project_id=%s AND tags @> %s::jsonb
                   ORDER BY created_at DESC LIMIT %s""",
                (project_id, tag_ctx_jsonb, limit),
            )
            sources += [
                {
                    "related_type": "commit",
                    "related_id":   r[0],
                    "related_layer": "mirror",
                    "created_at":   r[2].isoformat() if r[2] else None,
                }
                for r in cur.fetchall()
            ]

            # ── Work items removed (mem_ai_work_items table dropped) ───────
            work_items: list[dict] = []

    return {
        "tag":        tag_info,
        "ai_events":  ai_events,
        "sources":    sources,
        "work_items": work_items,
        "project":    project,
    }


@router.post("/migrate-to-ai-suggestions")
async def migrate_tags_to_ai_suggestions(project: str = Query(...)):
    """Move planner_tags that were auto-created under bug/feature/task into the ai_suggestion
    category. Safe: only moves tags with zero linked relation rows in mem_tags_relations."""
    _require_db()
    project_id = db.get_or_create_project_id(project)
    moved = 0
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Find ai_suggestion category id
            cur.execute(
                "SELECT id FROM mng_tags_categories WHERE name='ai_suggestion' LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(400, "ai_suggestion category not found")
            ai_cat_id = row[0]

            # Find tags in work-item categories with zero linked relations
            cur.execute(
                """SELECT t.id, c.name AS cat_name, t.name
                     FROM planner_tags t
                     JOIN mng_tags_categories c ON c.id = t.category_id
                    WHERE t.client_id=1 AND t.project=%s
                      AND LOWER(c.name) IN ('bug','feature','task')""",
                (project,),
            )
            candidates = cur.fetchall()
            for tag_id, cat_name, tag_name in candidates:
                # Set description if not already set
                cur.execute(
                    """UPDATE planner_tags
                          SET description = COALESCE(NULLIF(description, ''), %s),
                              category_id = %s
                        WHERE id = %s AND (description IS NULL OR description = '')""",
                    (f"[suggested: {cat_name.lower()}] (auto-migrated)", ai_cat_id, tag_id),
                )
                if cur.rowcount == 0:
                    # description already set, just update category
                    cur.execute(
                        "UPDATE planner_tags SET category_id = %s WHERE id = %s",
                        (ai_cat_id, tag_id),
                    )
                moved += 1
    return {"moved": moved}


# ── Project facts ─────────────────────────────────────────────────────────────

_SQL_GET_FACTS = (
    """SELECT id, fact_key, fact_value, category, valid_from
       FROM mem_ai_project_facts
       WHERE project_id=%s AND valid_until IS NULL
       ORDER BY fact_key"""
)


@router.get("/{project}/facts")
async def get_project_facts(project: str):
    """Return current project facts (valid_until IS NULL)."""
    if not db.is_available():
        return {"facts": [], "project": project, "total": 0, "fallback": True}
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_FACTS, (project_id,))
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    for r in rows:
        if r.get("valid_from"):
            r["valid_from"] = r["valid_from"].isoformat()
        if r.get("id"):
            r["id"] = str(r["id"])
    return {"facts": rows, "project": project, "total": len(rows)}


@router.delete("/{project}/facts/{fact_id}")
async def delete_fact(project: str, fact_id: str):
    """Expire a single project fact by ID (sets valid_until=NOW())."""
    if not db.is_available():
        return {"error": "db not available"}
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mem_ai_project_facts SET valid_until=NOW() "
                "WHERE id=%s::uuid AND project_id=%s AND valid_until IS NULL",
                (fact_id, project_id),
            )
            affected = cur.rowcount
        conn.commit()
    if not affected:
        return {"error": "fact not found or already expired"}
    return {"expired": True, "id": fact_id}


@router.delete("/{project}/facts")
async def clear_all_facts(project: str):
    """Expire ALL project facts (sets valid_until=NOW() on all active rows)."""
    if not db.is_available():
        return {"error": "db not available"}
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mem_ai_project_facts SET valid_until=NOW() "
                "WHERE project_id=%s AND valid_until IS NULL",
                (project_id,),
            )
            affected = cur.rowcount
        conn.commit()
    return {"expired": affected, "project": project}
