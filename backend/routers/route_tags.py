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
           t.status, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.short_desc, t.due_date, t.priority,
           t.source, t.creator, t.full_desc, t.requirements,
           t.acceptance_criteria, t.is_reusable, t.summary, t.action_items,
           t.requester, t.extra,
           t.embedding IS NOT NULL AS has_embedding,
           0 AS source_count
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.client_id = 1 AND t.project = %s
      AND t.merged_into IS NULL
    ORDER BY t.created_at
"""

_SQL_GET_TAG = """
    SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
           t.status, t.seq_num, t.created_at,
           tc.name AS category_name, tc.color, tc.icon,
           t.short_desc, t.due_date, t.priority, t.requirements, t.requester, t.extra,
           t.source, t.creator, t.full_desc, t.acceptance_criteria,
           t.is_reusable, t.summary, t.action_items,
           t.embedding IS NOT NULL AS has_embedding
    FROM planner_tags t
    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.client_id = 1 AND t.project = %s AND t.id = %s::uuid
"""

_SQL_INSERT_TAG = """
    INSERT INTO planner_tags (client_id, project, name, category_id, parent_id, status)
    VALUES (1, %s, %s, %s, %s, %s)
    ON CONFLICT (client_id, project, name, category_id) DO NOTHING
    RETURNING id, name, created_at
"""

_SQL_DELETE_TAG = """
    DELETE FROM planner_tags WHERE id = %s::uuid AND client_id = 1 AND project = %s
    RETURNING id
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
    status: str = "open"


class TagUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    parent_id: Optional[str] = None
    merged_into: Optional[str] = None
    status: Optional[str] = None
    seq_num: Optional[int] = None
    source: Optional[str] = None
    creator: Optional[str] = None
    short_desc: Optional[str] = None
    full_desc: Optional[str] = None
    requirements: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    requester: Optional[str] = None
    extra: Optional[dict] = None
    is_reusable: Optional[bool] = None
    summary: Optional[str] = None
    action_items: Optional[str] = None


class TagMerge(BaseModel):
    project: str
    from_name: str
    into_name: str


class SourceTagCreate(BaseModel):
    tag_id: str
    related_type: str  # 'prompt' | 'commit' | 'item' | 'message' | 'work_item' | 'session'
    related_id: str
    related_layer: str = "mirror"  # 'mirror' | 'ai'


class RelationUpdate(BaseModel):
    related_approved: Optional[str] = None  # 'approved' | 'rejected' | None (reset to pending)


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
    # Column order matches _SQL_LIST_TAGS (26 columns + source_count = index 25):
    #  0  id
    #  1  name
    #  2  category_id
    #  3  parent_id
    #  4  merged_into
    #  5  status
    #  6  seq_num
    #  7  created_at
    #  8  category_name
    #  9  color
    # 10  icon
    # 11  short_desc
    # 12  due_date
    # 13  priority
    # 14  source
    # 15  creator
    # 16  full_desc
    # 17  requirements
    # 18  acceptance_criteria
    # 19  is_reusable
    # 20  summary
    # 21  action_items
    # 22  requester
    # 23  extra
    # 24  has_embedding
    # 25  source_count  (only in _SQL_LIST_TAGS)
    return {
        "id":                  str(row[0]),
        "name":                row[1],
        "category_id":         row[2],
        "parent_id":           str(row[3]) if row[3] else None,
        "merged_into":         str(row[4]) if row[4] else None,
        "status":              row[5],
        "seq_num":             row[6],
        "created_at":          row[7].isoformat() if row[7] else None,
        "category_name":       row[8],
        "color":               row[9] or "#4a90e2",
        "icon":                row[10] or "⬡",
        "short_desc":          row[11] or "",
        "due_date":            row[12].isoformat() if row[12] else None,
        "priority":            row[13] if row[13] is not None else 3,
        "source":              row[14] or "user",
        "creator":             row[15],
        "full_desc":           row[16] or "",
        "requirements":        row[17] or "",
        "acceptance_criteria": row[18] or "",
        "is_reusable":         bool(row[19]) if row[19] is not None else False,
        "summary":             row[20] or "",
        "action_items":        row[21] or "",
        "requester":           row[22] or "",
        "extra":               row[23] if row[23] is not None else {},
        "has_embedding":       bool(row[24]) if row[24] is not None else False,
        "source_count":        row[25] if len(row) > 25 else 0,
        "children":            [],
    }


def _row_to_tag_detail(row: tuple) -> dict:
    # Column order matches _SQL_GET_TAG (25 columns):
    #  0  id
    #  1  name
    #  2  category_id
    #  3  parent_id
    #  4  merged_into
    #  5  status
    #  6  seq_num
    #  7  created_at
    #  8  category_name
    #  9  color
    # 10  icon
    # 11  short_desc
    # 12  due_date
    # 13  priority
    # 14  requirements
    # 15  requester
    # 16  extra
    # 17  source
    # 18  creator
    # 19  full_desc
    # 20  acceptance_criteria
    # 21  is_reusable
    # 22  summary
    # 23  action_items
    # 24  has_embedding
    return {
        "id":                  str(row[0]),
        "name":                row[1],
        "category_id":         row[2],
        "parent_id":           str(row[3]) if row[3] else None,
        "merged_into":         str(row[4]) if row[4] else None,
        "status":              row[5],
        "seq_num":             row[6],
        "created_at":          row[7].isoformat() if row[7] else None,
        "category_name":       row[8],
        "color":               row[9] or "#4a90e2",
        "icon":                row[10] or "⬡",
        "short_desc":          row[11] or "",
        "due_date":            row[12].isoformat() if row[12] else None,
        "priority":            row[13] if row[13] is not None else 3,
        "requirements":        row[14] or "",
        "requester":           row[15] or "",
        "extra":               row[16] if row[16] is not None else {},
        "source":              row[17] or "user",
        "creator":             row[18],
        "full_desc":           row[19] or "",
        "acceptance_criteria": row[20] or "",
        "is_reusable":         bool(row[21]) if row[21] is not None else False,
        "summary":             row[22] or "",
        "action_items":        row[23] or "",
        "has_embedding":       bool(row[24]) if row[24] is not None else False,
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
                 body.parent_id, body.status),
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
    if body.parent_id is not None:
        fields["parent_id"] = body.parent_id
    if body.merged_into is not None:
        fields["merged_into"] = body.merged_into
    if body.status is not None:
        fields["status"] = body.status
    if body.seq_num is not None:
        fields["seq_num"] = body.seq_num
    if body.source is not None:
        fields["source"] = body.source
    if body.creator is not None:
        fields["creator"] = body.creator
    if body.short_desc is not None:
        fields["short_desc"] = body.short_desc
    if body.full_desc is not None:
        fields["full_desc"] = body.full_desc
    if body.requirements is not None:
        fields["requirements"] = body.requirements
    if body.acceptance_criteria is not None:
        fields["acceptance_criteria"] = body.acceptance_criteria
    if body.priority is not None:
        fields["priority"] = body.priority
    if body.due_date is not None:
        fields["due_date"] = body.due_date
    if body.requester is not None:
        fields["requester"] = body.requester
    if body.extra is not None:
        fields["extra"] = json.dumps(body.extra)
    if body.is_reusable is not None:
        fields["is_reusable"] = body.is_reusable
    if body.summary is not None:
        fields["summary"] = body.summary
    if body.action_items is not None:
        fields["action_items"] = body.action_items

    if not fields:
        return {"ok": True}

    with db.conn() as conn:
        with conn.cursor() as cur:
            set_clause, vals = build_update(fields)
            cur.execute(
                f"UPDATE planner_tags SET {set_clause}, updated_at = NOW() "
                f"WHERE id = %s::uuid AND client_id = 1",
                vals + [tag_id],
            )
    return {"ok": True}


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str, project: str = Query(...), force: bool = Query(False)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_TAG, (tag_id, project))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"ok": True, "id": str(row[0])}


@router.post("/merge")
async def merge_tags(body: TagMerge):
    """Mark from_name as merged into into_name; re-link all mem_tags_relations rows."""
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
                "UPDATE planner_tags SET merged_into = %s, status = 'archived' WHERE id = %s",
                (into_id, from_id),
            )
    return {"ok": True, "merged_into": str(into_id)}


# ── Source endpoints ──────────────────────────────────────────────────────────

@router.get("/{tag_id}/sources")
async def get_tag_sources(tag_id: str, project: str = Query(...)):
    """Return prompts and commits tagged with this tag via their tags[] array.

    Builds the tag string as "category:name" from the planner_tags row,
    then queries mem_mrr_prompts and mem_mrr_commits WHERE tag_str = ANY(tags).
    """
    _require_db()

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

    results = []
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_id, LEFT(prompt,300), session_id, created_at "
                "FROM mem_mrr_prompts WHERE client_id=1 AND project=%s AND %s = ANY(tags) "
                "ORDER BY created_at DESC LIMIT 100",
                (project, tag_str),
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
                "SELECT commit_hash, LEFT(commit_msg,300), session_id, committed_at "
                "FROM mem_mrr_commits WHERE client_id=1 AND project=%s AND %s = ANY(tags) "
                "ORDER BY committed_at DESC LIMIT 100",
                (project, tag_str),
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


@router.post("/source")
async def add_source_tag(body: SourceTagCreate):
    """Deprecated: use POST /entities/events/tag-by-source-id with a tag string instead."""
    raise HTTPException(410, "mem_tags_relations removed — use tag-by-source-id with tag string")


@router.delete("/source/{source_tag_id}")
async def remove_source_tag(source_tag_id: str):
    """Deprecated: use DELETE /entities/events/tag-by-source-id with a tag string instead."""
    raise HTTPException(410, "mem_tags_relations removed — use tag-by-source-id with tag string")


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


# ── AI tag suggestion endpoints ───────────────────────────────────────────────

class SuggestionApplyBody(BaseModel):
    source_type: str
    source_id: str
    tag_name: str
    session_id: Optional[str] = None
    session_src_desc: Optional[str] = None
    layer: str = "mrr"  # 'mrr' = mem_mrr_* row, 'ai' = mem_ai_events row


class SuggestionIgnoreBody(BaseModel):
    source_type: str
    source_id: str
    layer: str = "mrr"


@router.post("/suggestions/generate")
async def generate_tag_suggestions(project: str = Query(...)):
    """AI tag suggestions for MRR rows dropped — tags are now set explicitly via hooks.

    Returns empty suggestions list for backward compatibility.
    AI suggestions for work items (mem_ai_work_items) are handled via the pipeline.
    """
    return {
        "suggestions":        [],
        "total_untagged_mrr": 0,
        "total_untagged_ai":  0,
        "total_untagged":     0,
    }


@router.post("/suggestions/apply")
async def apply_tag_suggestion(project: str = Query(...), body: SuggestionApplyBody = ...):
    """Deprecated: AI tag suggestions for MRR rows removed. Use tag-by-source-id instead."""
    raise HTTPException(410, "AI tag suggestion pipeline for MRR removed — use POST /entities/events/tag-by-source-id")


@router.post("/suggestions/ignore")
async def ignore_tag_suggestion(project: str = Query(...), body: SuggestionIgnoreBody = ...):
    """Deprecated: AI tag suggestions for MRR rows removed."""
    raise HTTPException(410, "AI tag suggestion pipeline for MRR removed")


# ── Relations endpoints ───────────────────────────────────────────────────────

@router.get("/relations")
async def get_tag_relations(
    project: str = Query(...),
    tag_id: Optional[str] = Query(None),
    work_item_id: Optional[str] = Query(None),
):
    """Deprecated: mem_tags_relations table removed. Returns empty list."""
    return []


@router.patch("/relations/{relation_id}")
async def update_relation(relation_id: str, body: RelationUpdate):
    """Deprecated: mem_tags_relations table removed."""
    raise HTTPException(410, "mem_tags_relations removed")


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
    with db.conn() as conn:
        with conn.cursor() as cur:
            # ── Tag properties ──────────────────────────────────────────────
            cur.execute(
                """SELECT t.id, t.name, t.category_id, t.parent_id,
                          c.name AS category_name, c.color, c.icon,
                          t.short_desc, t.status, t.priority, t.summary
                   FROM planner_tags t
                   LEFT JOIN mng_tags_categories c ON c.id = t.category_id
                   WHERE t.client_id=1 AND t.project=%s AND t.name=%s
                   LIMIT 1""",
                (project, tag_name),
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
                "short_desc":  tag_row[7] or "",
                "status":      tag_row[8],
                "priority":    tag_row[9] if tag_row[9] is not None else 3,
                "summary":     tag_row[10] or "",
                "parent_id":   str(tag_row[3]) if tag_row[3] else None,
            }

            # ── Recent AI events for this project ──────────────────────────
            cur.execute(
                """SELECT e.id, e.event_type, e.source_id, LEFT(e.content, 400) AS preview,
                          e.summary, e.created_at
                   FROM mem_ai_events e
                   WHERE e.client_id=1 AND e.project=%s
                   ORDER BY e.created_at DESC
                   LIMIT %s""",
                (project, limit),
            )
            ai_events = [
                {
                    "id":         str(r[0]),
                    "event_type": r[1],
                    "source_id":  r[2],
                    "preview":    r[3],
                    "summary":    r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in cur.fetchall()
            ]

            # ── Recent sources (prompts + commits via tags[]) ─────────────
            tag_str_full = tag_info.get("category", "") + ":" + tag_info.get("name", "")
            cur.execute(
                """SELECT source_id, 'prompt', created_at FROM mem_mrr_prompts
                   WHERE client_id=1 AND project=%s AND %s = ANY(tags)
                   ORDER BY created_at DESC LIMIT %s""",
                (project, tag_str_full, limit),
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
                """SELECT commit_hash, 'commit', committed_at FROM mem_mrr_commits
                   WHERE client_id=1 AND project=%s AND %s = ANY(tags)
                   ORDER BY committed_at DESC LIMIT %s""",
                (project, tag_str_full, limit),
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

            # ── Work items linked to this tag (via mem_tags_relations for AI layer) ─
            work_items = []
            try:
                cur.execute(
                    """SELECT wi.id, wi.name, wi.category_name, wi.status
                       FROM mem_ai_work_items wi
                       WHERE wi.client_id=1 AND wi.project=%s
                         AND (wi.name ILIKE %s OR wi.category_name || ':' || wi.name = %s)
                       ORDER BY wi.created_at DESC
                       LIMIT 20""",
                    (project, f"%{tag_info.get('name', '')}%", tag_str_full),
                )
                work_items = [
                    {"id": str(r[0]), "name": r[1], "category": r[2], "status": r[3]}
                    for r in cur.fetchall()
                ]
            except Exception:
                pass

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
                # Set short_desc if not already set
                cur.execute(
                    """UPDATE planner_tags
                          SET short_desc = COALESCE(NULLIF(short_desc, ''), %s),
                              category_id = %s
                        WHERE id = %s AND (short_desc IS NULL OR short_desc = '')""",
                    (f"[suggested: {cat_name.lower()}] (auto-migrated)", ai_cat_id, tag_id),
                )
                if cur.rowcount == 0:
                    # short_desc already set, just update category
                    cur.execute(
                        "UPDATE planner_tags SET category_id = %s WHERE id = %s",
                        (ai_cat_id, tag_id),
                    )
                moved += 1
    return {"moved": moved}
