"""
route_tags.py — Unified tag management router.

Manages the per-project tag registry (planner_tags), global categories (mng_tags_categories),
source-tag links (mem_mrr_tags), and session context persistence.

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
    SELECT 'commit' AS source_type, c.commit_hash AS source_id, c.commit_msg AS content, c.created_at,
           c.session_id, c.commit_hash
    FROM mem_mrr_tags st
    JOIN mem_mrr_commits c ON c.commit_hash = st.commit_id
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
    commit_id: Optional[str] = None
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
            # Also remap AI-layer event tags
            cur.execute(
                "UPDATE mem_ai_tags SET tag_id = %s WHERE tag_id = %s",
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
    layer: str = "mrr"  # 'mrr' = mem_mrr_* row, 'ai' = mem_ai_events row


class SuggestionIgnoreBody(BaseModel):
    source_type: str
    source_id: str
    layer: str = "mrr"


@router.post("/suggestions/generate")
async def generate_tag_suggestions(project: str = Query(...)):
    """Suggest planner_tags for untagged rows in mem_mrr_* and mem_ai_events.

    Returns: {suggestions: [...], total_untagged_mrr: N, total_untagged_ai: N}
    """
    _require_db()
    from memory.memory_tagging import MemoryTagging
    from memory.memory_mirroring import MemoryMirroring
    from core.database import db

    tagging  = MemoryTagging()
    mirroring = MemoryMirroring()

    total_untagged_mrr = sum(
        len(mirroring.get_untagged(project, stype, limit=1000))
        for stype in ("prompt", "commit", "item")
    )

    # Count untagged AI events
    total_untagged_ai = 0
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT COUNT(*) FROM mem_ai_events e
                       WHERE e.client_id=1 AND e.project=%s
                         AND NOT EXISTS (
                             SELECT 1 FROM mem_ai_tags t WHERE t.event_id = e.id
                         )""",
                    (project,),
                )
                row = cur.fetchone()
                total_untagged_ai = row[0] if row else 0
    except Exception:
        pass

    suggestions = await tagging.suggest_tags_for_untagged(project, batch_size=20)
    return {
        "suggestions":        suggestions,
        "total_untagged_mrr": total_untagged_mrr,
        "total_untagged_ai":  total_untagged_ai,
        # backward-compat alias
        "total_untagged":     total_untagged_mrr + total_untagged_ai,
    }


@router.post("/suggestions/apply")
async def apply_tag_suggestion(project: str = Query(...), body: SuggestionApplyBody = ...):
    """Apply an AI tag suggestion.

    For layer='mrr': links to mem_mrr_tags and marks ai_tags='approved'.
    For layer='ai':  links to mem_ai_tags with ai_suggested=True.
    """
    _require_db()
    from memory.memory_tagging import MemoryTagging
    tagging = MemoryTagging()
    ok = await tagging.apply_suggestion(
        project, body.source_type, body.source_id, body.tag_name,
        session_id=body.session_id, session_src_desc=body.session_src_desc,
        layer=body.layer,
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


class RelationCreateByName(BaseModel):
    """Create a relation using tag names — tags are created if they don't exist."""
    project: str
    from_name: str
    relation: str
    to_name: str
    note: Optional[str] = None
    source: str = "manual"


@router.get("/relations")
async def list_tag_relations(project: str = Query(...)):
    """List mem_ai_tags_relations for a project (both directions) with tag names."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    return MemoryTagging().get_relations(project)


@router.post("/relations")
async def create_tag_relation(body: RelationCreate, project: str | None = Query(None)):
    """Add a relationship between two planner_tags (by UUID)."""
    _require_db()
    from memory.memory_tagging import MemoryTagging
    MemoryTagging().add_relation(
        body.from_tag_id, body.relation, body.to_tag_id,
        note=body.note, source=body.source,
    )
    if project:
        asyncio.create_task(_trigger_memory_regen(project))
    return {"ok": True}


@router.post("/relations/by-name")
async def create_tag_relation_by_name(body: RelationCreateByName):
    """Add a relationship using tag names — tags are created if missing.

    Example: {"project": "aicli", "from_name": "retry-dashboard",
               "relation": "depends_on", "to_name": "retry-backend",
               "note": "Dashboard cannot ship without backend retry API"}
    """
    _require_db()
    from memory.memory_tagging import MemoryTagging
    ok = MemoryTagging().add_relation_by_name(
        body.project, body.from_name, body.relation, body.to_name,
        note=body.note, source=body.source,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Could not resolve or create tags")
    asyncio.create_task(_trigger_memory_regen(body.project))
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


@router.get("/context")
async def get_tag_context(
    tag_name: str = Query(..., description="Tag name to retrieve full context for"),
    project:  str = Query(...),
    limit:    int = Query(20, ge=1, le=100),
):
    """Return comprehensive context for a tag: properties, AI events, mirroring rows, relations.

    Used by the pipeline's first agent (PM) to orient on a feature/bug before planning.
    """
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            # ── Tag properties ──────────────────────────────────────────────
            cur.execute(
                """SELECT t.id, t.name, t.category_id, t.parent_id,
                          c.name AS category_name, c.color, c.icon,
                          tm.description
                   FROM planner_tags t
                   LEFT JOIN mng_tags_categories c ON c.id = t.category_id
                   LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
                   WHERE t.client_id=1 AND t.project=%s AND t.name=%s
                   LIMIT 1""",
                (project, tag_name),
            )
            tag_row = cur.fetchone()
            if not tag_row:
                raise HTTPException(404, f"Tag '{tag_name}' not found in project '{project}'")
            tag_id = str(tag_row[0])
            tag_info = {
                "id": tag_id, "name": tag_row[1],
                "category": tag_row[4], "color": tag_row[5], "icon": tag_row[6],
                "description": tag_row[7] or "",
                "parent_id": str(tag_row[3]) if tag_row[3] else None,
            }

            # ── Recent AI events tagged with this tag ───────────────────────
            cur.execute(
                """SELECT e.id, e.event_type, e.source_id, LEFT(e.content, 400) AS preview,
                          e.summary, e.created_at
                   FROM mem_ai_events e
                   JOIN mem_ai_tags at ON at.event_id = e.id
                   WHERE at.tag_id = %s::uuid
                   ORDER BY e.created_at DESC
                   LIMIT %s""",
                (tag_id, limit),
            )
            ai_events = [
                {
                    "id": str(r[0]), "event_type": r[1], "source_id": r[2],
                    "preview": r[3], "summary": r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in cur.fetchall()
            ]

            # ── Recent mirroring sources tagged with this tag ───────────────
            cur.execute(
                """SELECT prompt_id, commit_id, item_id, message_id, created_at
                   FROM mem_mrr_tags
                   WHERE tag_id = %s::uuid
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (tag_id, limit),
            )
            mrr_sources = [
                {
                    "prompt_id": str(r[0]) if r[0] else None,
                    "commit_id": r[1],
                    "item_id": str(r[2]) if r[2] else None,
                    "message_id": str(r[3]) if r[3] else None,
                    "created_at": r[4].isoformat() if r[4] else None,
                }
                for r in cur.fetchall()
            ]

            # ── Relations involving this tag ────────────────────────────────
            cur.execute(
                """SELECT r.id, r.relation, r.note, r.source,
                          tf.name AS from_name, tt.name AS to_name
                   FROM mng_ai_tags_relations r
                   JOIN planner_tags tf ON tf.id = r.from_tag_id
                   JOIN planner_tags tt ON tt.id = r.to_tag_id
                   WHERE r.from_tag_id = %s::uuid OR r.to_tag_id = %s::uuid""",
                (tag_id, tag_id),
            )
            relations = [
                {
                    "id": str(r[0]), "relation": r[1], "note": r[2], "source": r[3],
                    "from": r[4], "to": r[5],
                }
                for r in cur.fetchall()
            ]

            # ── Work items referencing this tag ─────────────────────────────
            cur.execute(
                """SELECT id, name, category_name, lifecycle_status, status, description
                   FROM mem_ai_work_items
                   WHERE client_id=1 AND project=%s AND tag_id = %s::uuid
                   ORDER BY created_at DESC
                   LIMIT 10""",
                (project, tag_id),
            )
            work_items = [
                {
                    "id": str(r[0]), "name": r[1], "category": r[2],
                    "lifecycle": r[3], "status": r[4],
                    "description": (r[5] or "")[:200],
                }
                for r in cur.fetchall()
            ]

    return {
        "tag": tag_info,
        "ai_events": ai_events,
        "mrr_sources": mrr_sources,
        "relations": relations,
        "work_items": work_items,
        "project": project,
    }


@router.post("/migrate-to-ai-suggestions")
async def migrate_tags_to_ai_suggestions(project: str = Query(...)):
    """Move planner_tags that were auto-created under bug/feature/task into the ai_suggestion
    category.  Safe: only moves tags with zero linked event rows in mem_mrr_tags."""
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

            # Find tags in work-item categories with zero linked events
            cur.execute(
                """SELECT t.id, c.name AS cat_name, t.name
                     FROM planner_tags t
                     JOIN mng_tags_categories c ON c.id = t.category_id
                    WHERE t.client_id=1 AND t.project=%s
                      AND LOWER(c.name) IN ('bug','feature','task')
                      AND NOT EXISTS (
                            SELECT 1 FROM mem_mrr_tags st WHERE st.tag_id = t.id
                          )""",
                (project,),
            )
            candidates = cur.fetchall()
            for tag_id, cat_name, tag_name in candidates:
                # Add suggested-type prefix to description (if not already set)
                cur.execute(
                    """INSERT INTO planner_tags_meta (tag_id, description)
                            VALUES (%s, %s)
                       ON CONFLICT (tag_id) DO UPDATE
                            SET description = EXCLUDED.description
                       WHERE planner_tags_meta.description IS NULL
                          OR planner_tags_meta.description = ''""",
                    (tag_id, f"[suggested: {cat_name.lower()}] (auto-migrated)"),
                )
                cur.execute(
                    "UPDATE planner_tags SET category_id=%s WHERE id=%s",
                    (ai_cat_id, tag_id),
                )
                moved += 1
    return {"moved": moved}
