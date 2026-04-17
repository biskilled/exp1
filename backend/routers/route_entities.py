"""entities.py — Entity/relationship model for the aicli knowledge layer.

Manages the tag taxonomy and source-tag links connecting every prompt, commit,
document, and message to named features, bugs, and tasks.

Underlying tables:
  mng_tags_categories  — global category vocabulary
  planner_tags         — per-project tag registry, UUID PK; inline metadata columns
                         (short_desc, requirements, due_date, priority, status, etc.)
  mem_tags_relations   — unified junction: tag ↔ prompt | commit | item | message
                         related_layer='mirror' replaces mem_mrr_tags
                         related_layer='ai'     replaces mem_ai_tags
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
from core.tags import parse_tag, tags_to_list

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
    LEFT JOIN planner_tags t ON t.category_id = tc.id AND t.project_id=%s
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

# planner_tags (UUID PK) — inline metadata
# {where} is injected at call site; caller always provides at least "t.project_id=X"
_SQL_LIST_VALUES = """
    SELECT t.id::text, t.category_id, t.name,
           COALESCE(t.description,'') AS description, t.status,
           t.created_at, t.updated_at, t.due_date, t.parent_id::text,
           tc.name AS category_name, tc.color, tc.icon,
           COALESCE(t.priority, 3) AS priority,
           COALESCE(t.file_ref, '') AS file_ref
    FROM planner_tags t
    JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
    WHERE {where}
    ORDER BY t.parent_id NULLS FIRST, t.status, t.name
"""

# Used by entity_summary endpoint and /memory synthesis
_SQL_LIST_VALUES_SUMMARY = """
    SELECT tc.id AS cat_id, tc.name AS category, tc.color, tc.icon,
           t.id::text, t.name,
           COALESCE(t.description,'') AS description, t.status,
           t.due_date, t.parent_id::text, t.status AS lifecycle_status,
           0 AS event_count,
           0 AS commit_count
    FROM mng_tags_categories tc
    JOIN planner_tags t ON t.category_id = tc.id AND t.project_id=%s
    WHERE tc.client_id=1 AND t.status != 'archived'
    ORDER BY tc.name, t.status, t.name
"""

_SQL_INSERT_VALUE = """
    INSERT INTO planner_tags (project_id, name, category_id, parent_id, status)
    VALUES (%s, %s, %s, %s::uuid, %s)
    RETURNING id::text
"""

_SQL_GET_VALUE_BY_SEQ = None  # seq_num dropped from planner_tags in m026; endpoint returns 404

_SQL_DELETE_VALUE = """
    DELETE FROM planner_tags WHERE id=%s::uuid RETURNING id
"""

# Sources (prompts + commits) tagged with a given tag via tags JSONB column
# tag_jsonb is a JSONB string like '{"feature":"auth"}' built at call site
_SQL_GET_EVENTS_FOR_VALUE = """
    SELECT pr.source_id, 'prompt' AS event_type, pr.source_id AS source_id,
           left(pr.prompt, 120) AS title, pr.created_at
    FROM mem_mrr_prompts pr
    WHERE pr.project_id=%s AND pr.tags @> %s::jsonb
    UNION ALL
    SELECT c.commit_hash, 'commit', c.commit_hash,
           left(c.commit_msg, 120), c.created_at
    FROM mem_mrr_commits c
    WHERE c.project_id=%s AND c.tags @> %s::jsonb
    ORDER BY 5 DESC LIMIT %s
"""

# Session tags: distinct tag strings from prompts + commits in this session
# Expands JSONB dict {"phase":"discovery","feature":"auth"} → "phase:discovery", "feature:auth"
_SQL_GET_SESSION_TAGS_FROM_MRR = """
    SELECT DISTINCT (key || ':' || value) AS tag_str
    FROM mem_mrr_prompts, jsonb_each_text(tags - 'source' - 'llm')
    WHERE project_id=%s AND session_id=%s
      AND (tags - 'source' - 'llm') != '{}'::jsonb
    UNION
    SELECT DISTINCT (key || ':' || value)
    FROM mem_mrr_commits, jsonb_each_text(tags - 'source' - 'llm')
    WHERE project_id=%s AND session_id=%s
      AND (tags - 'source' - 'llm') != '{}'::jsonb
"""

# GitHub sync: upsert tag by name+project including description inline
_SQL_UPSERT_TAG_GITHUB = """
    INSERT INTO planner_tags (project_id, name, category_id, description, source, updated_at)
    VALUES (%s, %s, %s, %s, 'github', NOW())
    ON CONFLICT (project_id, name, category_id) DO UPDATE SET
        description = EXCLUDED.description,
        source = EXCLUDED.source,
        updated_at = NOW()
    RETURNING (xmax = 0) AS was_inserted, id::text
"""

# Validate category id exists (global lookup)
_SQL_GET_CATEGORY_BY_ID = """
    SELECT id FROM mng_tags_categories WHERE client_id=1 AND id=%s
"""

# Get category name by id (global lookup)
_SQL_GET_CATEGORY_NAME_BY_ID = """
    SELECT name FROM mng_tags_categories WHERE client_id=1 AND id=%s
"""

# Resolve tag string "category:name" for a planner_tags UUID — used for tagging/events
_SQL_GET_TAG_STRING_BY_ID = """
    SELECT tc.name || ':' || t.name
    FROM planner_tags t
    JOIN mng_tags_categories tc ON tc.id = t.category_id
    WHERE t.id=%s::uuid AND t.client_id=1
    LIMIT 1
"""

# List commits for events endpoint
_SQL_LIST_COMMIT_EVENTS = """
    SELECT commit_hash, 'commit', commit_hash, left(commit_msg,120), created_at
    FROM mem_mrr_commits WHERE project_id=%s
    ORDER BY created_at DESC NULLS LAST LIMIT %s
"""

# List prompts for events endpoint
_SQL_LIST_PROMPT_EVENTS = """
    SELECT source_id, 'prompt', source_id, left(prompt,120), created_at
    FROM mem_mrr_prompts WHERE project_id=%s AND event_type='prompt'
    ORDER BY created_at DESC LIMIT %s
"""

# Find existing planner_tag by project + name
_SQL_GET_TAG_BY_NAME = """
    SELECT id::text FROM planner_tags WHERE project_id=%s AND name=%s
"""

# Insert session tag with description
_SQL_INSERT_SESSION_TAG_WITH_DESC = """
    INSERT INTO planner_tags (project_id, name, category_id, description)
    VALUES (%s, %s, %s, %s) RETURNING id::text
"""

# Apply a JSONB tag to all prompts in a session
_SQL_TAG_PROMPTS_BY_SESSION = """
    UPDATE mem_mrr_prompts SET tags = tags || %s::jsonb
    WHERE project_id=%s AND session_id=%s
"""

# Apply a JSONB tag to all commits in a session
_SQL_TAG_COMMITS_BY_SESSION = """
    UPDATE mem_mrr_commits SET tags = tags || %s::jsonb
    WHERE project_id=%s AND session_id=%s
"""

# Apply a JSONB tag to a single commit by hash
_SQL_TAG_COMMIT_BY_HASH = """
    UPDATE mem_mrr_commits SET tags = tags || %s::jsonb
    WHERE project_id=%s AND commit_hash=%s
"""

# Propagate tag from commit → its linked prompt
_SQL_TAG_PROMPT_FROM_COMMIT = """
    UPDATE mem_mrr_prompts pr
       SET tags = pr.tags || %s::jsonb
      FROM mem_mrr_commits c
     WHERE c.project_id=%s AND c.commit_hash=%s
       AND pr.id = c.prompt_id
    RETURNING pr.source_id
"""

# Apply a JSONB tag to a single prompt by source_id
_SQL_TAG_PROMPT_BY_SOURCE = """
    UPDATE mem_mrr_prompts SET tags = tags || %s::jsonb
    WHERE project_id=%s AND source_id=%s
"""

# Propagate tag from prompt → its linked commit
_SQL_TAG_COMMIT_FROM_PROMPT = """
    UPDATE mem_mrr_commits c
       SET tags = c.tags || %s::jsonb
      FROM mem_mrr_prompts p
     WHERE p.project_id=%s AND p.source_id=%s
       AND c.prompt_id = p.id
    RETURNING c.commit_hash
"""

# Remove a tag key from a commit by hash
_SQL_UNTAG_COMMIT_BY_HASH = """
    UPDATE mem_mrr_commits SET tags = tags - %s
    WHERE project_id=%s AND commit_hash=%s
"""

# Propagate tag removal from commit → its linked prompt
_SQL_UNTAG_PROMPT_FROM_COMMIT = """
    UPDATE mem_mrr_prompts pr
       SET tags = pr.tags - %s
      FROM mem_mrr_commits c
     WHERE c.project_id=%s AND c.commit_hash=%s
       AND pr.id = c.prompt_id
    RETURNING pr.source_id
"""

# Remove a tag key from a prompt by source_id
_SQL_UNTAG_PROMPT_BY_SOURCE = """
    UPDATE mem_mrr_prompts SET tags = tags - %s
    WHERE project_id=%s AND source_id=%s
"""

# Propagate tag removal from prompt → its linked commit
_SQL_UNTAG_COMMIT_FROM_PROMPT = """
    UPDATE mem_mrr_commits c
       SET tags = c.tags - %s
      FROM mem_mrr_prompts p
     WHERE p.project_id=%s AND p.source_id=%s
       AND c.prompt_id = p.id
    RETURNING c.commit_hash
"""

# Remove a tag key from all prompts in a session
_SQL_UNTAG_PROMPTS_BY_SESSION = """
    UPDATE mem_mrr_prompts SET tags = tags - %s
    WHERE project_id=%s AND session_id=%s
"""

# Remove a tag key from all commits in a session
_SQL_UNTAG_COMMITS_BY_SESSION = """
    UPDATE mem_mrr_commits SET tags = tags - %s
    WHERE project_id=%s AND session_id=%s
"""

# All tagged prompts for source-tags endpoint (exclude internal-only tags)
_SQL_GET_TAGGED_PROMPTS = """
    SELECT source_id, tags FROM mem_mrr_prompts
    WHERE project_id=%s AND (tags - 'source' - 'llm') != '{}'::jsonb
"""

# All tagged commits for source-tags endpoint (exclude internal-only tags)
_SQL_GET_TAGGED_COMMITS = """
    SELECT commit_hash, tags FROM mem_mrr_commits
    WHERE project_id=%s AND (tags - 'source' - 'llm') != '{}'::jsonb
"""

# Set due_date on a planner_tag by id
_SQL_SET_TAG_DUE_DATE = """
    UPDATE planner_tags SET due_date=%s WHERE id=%s::uuid
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
    project_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_CATEGORIES, (project_id,))
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
    category_id:          int = 0
    name:                 str
    description:          str = ""       # mapped to short_desc
    project:              Optional[str] = None
    due_date:             Optional[str] = None
    parent_id:            Optional[str] = None   # UUID string
    category_name:        Optional[str] = None   # alternative to category_id
    lifecycle_status:     Optional[str] = None
    requirements:         Optional[str] = None
    acceptance_criteria:  Optional[str] = None
    priority:             Optional[int] = None
    requester:            Optional[str] = None
    source:               Optional[str] = None
    creator:              Optional[str] = None
    is_reusable:          Optional[bool] = None
    extra:                Optional[dict] = None

class ValuePatch(BaseModel):
    name:                 Optional[str] = None
    description:          Optional[str] = None   # mapped to short_desc
    status:               Optional[str] = None
    due_date:             Optional[str] = None
    parent_id:            Optional[str] = None   # UUID string
    lifecycle_status:     Optional[str] = None
    requirements:         Optional[str] = None
    acceptance_criteria:  Optional[str] = None
    priority:             Optional[int] = None
    requester:            Optional[str] = None
    source:               Optional[str] = None
    creator:              Optional[str] = None
    is_reusable:          Optional[bool] = None
    extra:                Optional[dict] = None


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

            project_id = db.get_or_create_project_id(p)
            where_parts = ["t.project_id=%s"]
            params: list = [project_id]
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
                for ts_col in ("created_at", "updated_at", "due_date"):
                    if row.get(ts_col):
                        row[ts_col] = row[ts_col].isoformat()
                rows.append(row)
            return {"values": rows, "project": p}


@router.get("/all-values")
async def list_all_values(project: str | None = Query(None)):
    """Return all planner_tag values for ALL categories in a single query.

    Replaces N parallel /entities/values calls in loadTagCache() with one
    round-trip. Response groups values by category_id for direct cache hydration.

    Returns:
        {by_category: {"<cat_id>": [value, ...]}, categories: [{id,name,...}], project}
    """
    if not db.is_available():
        return {"by_category": {}, "categories": [], "project": _project(project), "fallback": True}

    p = _project(project)
    _seed_defaults(p)
    project_id = db.get_or_create_project_id(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Load categories with value counts
            cur.execute(_SQL_LIST_CATEGORIES, (project_id,))
            cat_cols = [d[0] for d in cur.description]
            categories = [dict(zip(cat_cols, r)) for r in cur.fetchall()]

            # Load ALL values in one query (no category filter)
            cur.execute(
                _SQL_LIST_VALUES.format(where="t.project_id=%s"),
                (project_id,),
            )
            val_cols = [d[0] for d in cur.description]
            by_category: dict[str, list] = {}
            for r in cur.fetchall():
                row = dict(zip(val_cols, r))
                for ts_col in ("created_at", "updated_at", "due_date"):
                    if row.get(ts_col):
                        row[ts_col] = row[ts_col].isoformat()
                key = str(row["category_id"])
                by_category.setdefault(key, []).append(row)

    return {"by_category": by_category, "categories": categories, "project": p}


@router.get("/summary")
async def entity_summary(project: str | None = Query(None)):
    """Structured project management view: all active tags grouped by category.

    Returns features/bugs/tasks with descriptions, due dates, source counts and
    linked commit counts. Used by /memory synthesis and MCP get_project_state.
    """
    _require_db()
    p = _project(project)
    _seed_defaults(p)
    project_id = db.get_or_create_project_id(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_VALUES_SUMMARY, (project_id,))
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
            "lifecycle_status": lc_status or "open",
            "event_count": event_count,
            "commit_count": commit_count,
        })

    return {"summary": list(cats.values()), "project": p}


@router.post("/values", status_code=201)
async def create_value(body: ValueCreate):
    _require_db()
    p = _project(body.project)
    project_id = db.get_or_create_project_id(p)
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
                cur.execute(_SQL_GET_CATEGORY_BY_ID, (cat_id,))
                if not cur.fetchone():
                    raise HTTPException(404, "Category not found")

            lc = body.lifecycle_status or "open"

            # Build inline fields for planner_tags INSERT
            inline_fields: dict[str, object] = {}
            if body.description:
                inline_fields["description"] = body.description
            if body.requirements is not None:
                inline_fields["requirements"] = body.requirements
            if body.acceptance_criteria is not None:
                inline_fields["acceptance_criteria"] = body.acceptance_criteria
            if body.due_date is not None:
                inline_fields["due_date"] = body.due_date or None
            if body.requester is not None:
                inline_fields["requester"] = body.requester
            if body.priority is not None:
                inline_fields["priority"] = body.priority
            if body.creator is not None:
                inline_fields["creator"] = body.creator

            if inline_fields:
                extra_cols = ", ".join(inline_fields.keys())
                extra_placeholders = ", ".join(["%s"] * len(inline_fields))
                cur.execute(
                    f"INSERT INTO planner_tags (project_id, name, category_id, parent_id, status, {extra_cols}) "
                    f"VALUES (%s, %s, %s, %s::uuid, %s, {extra_placeholders}) "
                    f"RETURNING id::text",
                    [project_id, body.name, cat_id, body.parent_id or None, lc] + list(inline_fields.values()),
                )
            else:
                cur.execute(
                    _SQL_INSERT_VALUE,
                    (project_id, body.name, cat_id, body.parent_id or None, lc),
                )
            new_id = cur.fetchone()[0]

            return {"id": new_id, "name": body.name, "project": p, "category_id": cat_id}


@router.get("/values/number/{seq_num}")
async def get_value_by_number(seq_num: int, project: str | None = Query(None)):
    """Resolve a short sequential number to the full tag/value.
    Note: seq_num was removed from planner_tags in m026 — always returns 404."""
    raise HTTPException(404, f"Tag #{seq_num} not found — seq_num lookup is deprecated for planner_tags")


@router.patch("/values/{val_id}")
async def patch_value(val_id: str, body: ValuePatch):
    """Update a tag (val_id is a UUID string). All metadata is inline on planner_tags."""
    _require_db()
    tag_updates: dict[str, object] = {}
    if body.name             is not None: tag_updates["name"] = body.name
    if body.status           is not None: tag_updates["status"] = body.status
    if body.lifecycle_status is not None: tag_updates["status"] = body.lifecycle_status
    # parent_id can be explicitly set to null (clear parent) — check model_fields_set
    if "parent_id" in body.model_fields_set: tag_updates["parent_id"] = body.parent_id or None
    if body.description      is not None: tag_updates["description"] = body.description
    if body.due_date         is not None: tag_updates["due_date"] = body.due_date or None
    if body.requirements     is not None: tag_updates["requirements"] = body.requirements
    if body.acceptance_criteria is not None: tag_updates["acceptance_criteria"] = body.acceptance_criteria
    if body.priority         is not None: tag_updates["priority"] = body.priority
    if body.requester        is not None: tag_updates["requester"] = body.requester
    if body.source           is not None: tag_updates["source"] = body.source
    if body.creator          is not None: tag_updates["creator"] = body.creator
    if body.is_reusable      is not None: tag_updates["is_reusable"] = body.is_reusable
    if body.extra            is not None: tag_updates["extra"] = json.dumps(body.extra)

    if not tag_updates:
        raise HTTPException(400, "Nothing to update")

    with db.conn() as conn:
        with conn.cursor() as cur:
            # parent_id is a UUID — cast it; everything else is plain
            set_parts, set_vals = [], []
            for k, v in tag_updates.items():
                if k == "parent_id":
                    set_parts.append("parent_id=%s::uuid")
                else:
                    set_parts.append(f"{k}=%s")
                set_vals.append(v)
            set_vals.append(val_id)
            cur.execute(
                f"UPDATE planner_tags SET {','.join(set_parts)}, updated_at=NOW() "
                f"WHERE id=%s::uuid AND client_id=1 RETURNING id",
                set_vals,
            )
            if not cur.fetchone():
                raise HTTPException(404, "Tag not found")
    return {"ok": True}


@router.delete("/values/{val_id}")
async def delete_value(val_id: str):
    """Delete a tag (val_id is a UUID string). CASCADE deletes mem_tags_relations rows."""
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
    project_id = db.get_or_create_project_id(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if value_id:
                # Build tag string from planner_tags UUID
                tag_str = None
                try:
                    cur.execute(_SQL_GET_TAG_STRING_BY_ID, (value_id,))
                    ts_row = cur.fetchone()
                    if ts_row:
                        tag_str = ts_row[0]
                except Exception:
                    pass
                if not tag_str:
                    return {"events": [], "project": p, "total": 0}
                _k, _v = parse_tag(tag_str)
                tag_jsonb = json.dumps({_k: _v})
                cur.execute(
                    _SQL_GET_EVENTS_FOR_VALUE,
                    (project_id, tag_jsonb, project_id, tag_jsonb, limit),
                )
                rows_raw = cur.fetchall()
                rows = [
                    {"event_type": r[1], "source_id": r[2], "title": r[3],
                     "created_at": r[4].isoformat() if r[4] else None, "tags": []}
                    for r in rows_raw
                ]
            elif event_type == "commit":
                cur.execute(_SQL_LIST_COMMIT_EVENTS, (project_id, limit))
                rows = [
                    {"event_type": "commit", "source_id": r[0], "title": r[3],
                     "created_at": r[4].isoformat() if r[4] else None, "tags": []}
                    for r in cur.fetchall()
                ]
            else:
                cur.execute(_SQL_LIST_PROMPT_EVENTS, (project_id, limit))
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
    Tagging now uses tags TEXT[] inline on MRR rows.
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
    """No-op stub — event sync is now handled via mem_mrr_prompts + mem_mrr_commits + mem_tags_relations."""
    p = _project(project)
    return {"imported": {"prompt": 0, "commit": 0}, "project": p, "phase5": "noop"}




@router.get("/values/{val_id}/events")
async def value_events(val_id: str, project: str | None = Query(None), limit: int = Query(50)):
    return await list_events(project=project, value_id=val_id, limit=limit)


# ── Auto-tag suggestions ────────────────────────────────────────────────────────




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
    project_id = db.get_or_create_project_id(p)

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
                cur.execute(_SQL_GET_TAG_BY_NAME, (project_id, body.value_name))
                val_row = cur.fetchone()
                if val_row:
                    tag_id = val_row[0]
                else:
                    if body.description:
                        cur.execute(
                            _SQL_INSERT_SESSION_TAG_WITH_DESC,
                            (project_id, body.value_name, cat_id, body.description),
                        )
                    else:
                        cur.execute(
                            _SQL_INSERT_VALUE,
                            (project_id, body.value_name, cat_id, None, "open"),
                        )
                    tag_id = cur.fetchone()[0]

            # Tag all prompts and commits in this session via tags[] array
            # Build tag string from category + value name
            tag_str = body.value_name or tag_id  # fallback to UUID if no name
            if body.category_name and body.value_name:
                tag_str = f"{body.category_name}:{body.value_name}"
            elif tag_id:
                # Try to look up the tag string from planner_tags
                cur.execute(_SQL_GET_TAG_STRING_BY_ID, (tag_id,))
                lookup = cur.fetchone()
                if lookup:
                    tag_str = lookup[0]

            _sk, _sv = parse_tag(tag_str)
            _tag_jsonb = json.dumps({_sk: _sv})
            cur.execute(_SQL_TAG_PROMPTS_BY_SESSION, (_tag_jsonb, p, body.session_id))
            prompt_tagged = cur.rowcount
            cur.execute(_SQL_TAG_COMMITS_BY_SESSION, (_tag_jsonb, p, body.session_id))
            commit_tagged = cur.rowcount

    return {
        "ok": True,
        "tag": tag_str if 'tag_str' in dir() else tag_id,
        "session_id": body.session_id,
        "events_tagged": prompt_tagged + commit_tagged,
        "project": p,
    }


# ── Per-entry tagging (History tab) ───────────────────────────────────────────

class TagBySourceIdBody(BaseModel):
    source_id: str           # prompt source_id (timestamp) or commit hash
    tag:       str           # tag string e.g. "phase:discovery", "feature:auth"
    project:   Optional[str] = None
    # Legacy fields kept for backward compat — ignored when tag is provided
    tag_id:          Optional[str] = None
    entity_value_id: Optional[int] = None





@router.post("/events/tag-by-source-id")
async def tag_event_by_source_id(body: TagBySourceIdBody, background: BackgroundTasks):
    """Tag a single prompt or commit by its source_id / commit hash.

    source_id is either:
      - a timestamp string (prompt) → looked up in mem_mrr_prompts.source_id
      - a 7-40 char hex string (commit hash) → looked up in mem_mrr_commits.commit_hash
    tag must be a string like "phase:discovery" or "feature:auth".
    """
    _require_db()
    p = _project(body.project)
    project_id = db.get_or_create_project_id(p)
    tag = body.tag

    if not tag:
        raise HTTPException(400, "tag must be a non-empty string like 'phase:discovery'")

    from core.tags import parse_tag
    import json as _json
    k, v = parse_tag(tag)
    tag_jsonb = _json.dumps({k: v})

    is_commit = bool(re.match(r'^[0-9a-f]{7,40}$', body.source_id.lower()))

    propagated_to: str | None = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            if is_commit:
                cur.execute(_SQL_TAG_COMMIT_BY_HASH, (tag_jsonb, project_id, body.source_id))
                if cur.rowcount == 0:
                    raise HTTPException(404, f"Commit {body.source_id!r} not found")
                cur.execute(_SQL_TAG_PROMPT_FROM_COMMIT, (tag_jsonb, project_id, body.source_id))
                row = cur.fetchone()
                if row:
                    propagated_to = row[0]
            else:
                cur.execute(_SQL_TAG_PROMPT_BY_SOURCE, (tag_jsonb, project_id, body.source_id))
                if cur.rowcount == 0:
                    raise HTTPException(404, f"Prompt with source_id={body.source_id!r} not found")
                cur.execute(_SQL_TAG_COMMIT_FROM_PROMPT, (tag_jsonb, project_id, body.source_id))
                row = cur.fetchone()
                if row:
                    propagated_to = row[0]

    return {"ok": True, "source_id": body.source_id, "tag": tag, "project": p,
            "propagated_to": propagated_to}


@router.delete("/events/tag-by-source-id")
async def untag_event_by_source_id(
    source_id: str = Query(...),
    tag:       str = Query(...),   # tag string e.g. "phase:discovery"
    project:   str | None = Query(None),
    value_id:  str | None = Query(None),   # legacy alias — ignored when tag is provided
):
    """Remove a tag from a prompt or commit identified by its source_id / commit hash."""
    _require_db()
    project_id = db.get_or_create_project_id(p)
    p = _project(project)
    from core.tags import parse_tag
    key, _ = parse_tag(tag)
    is_commit = bool(re.match(r'^[0-9a-f]{7,40}$', source_id.lower()))
    propagated_to: str | None = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            if is_commit:
                cur.execute(_SQL_UNTAG_COMMIT_BY_HASH, (key, project_id, source_id))
                cur.execute(_SQL_UNTAG_PROMPT_FROM_COMMIT, (key, project_id, source_id))
                row = cur.fetchone()
                if row:
                    propagated_to = row[0]
            else:
                cur.execute(_SQL_UNTAG_PROMPT_BY_SOURCE, (key, project_id, source_id))
                cur.execute(_SQL_UNTAG_COMMIT_FROM_PROMPT, (key, project_id, source_id))
                row = cur.fetchone()
                if row:
                    propagated_to = row[0]
    return {"ok": True, "source_id": source_id, "tag": tag, "propagated_to": propagated_to}


@router.delete("/session-tag")
async def remove_session_tag(
    session_id: str = Query(...),
    tag:        str = Query(...),   # tag string e.g. "phase:discovery"
    project:    str | None = Query(None),
    value_id:   str | None = Query(None),   # legacy alias — ignored when tag is provided
):
    """Remove a tag from all prompts and commits in a session."""
    _require_db()
    project_id = db.get_or_create_project_id(p)
    p = _project(project)
    _rk, _ = parse_tag(tag)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_UNTAG_PROMPTS_BY_SESSION, (_rk, project_id, session_id))
            deleted_p = cur.rowcount
            cur.execute(_SQL_UNTAG_COMMITS_BY_SESSION, (_rk, project_id, session_id))
            deleted_c = cur.rowcount
    return {"ok": True, "session_id": session_id, "tag": tag,
            "deleted": deleted_p + deleted_c}


@router.get("/events/source-tags")
async def get_events_source_tags(project: str | None = Query(None)):
    """Return a map of source_id → tags[] for all tagged prompts and commits.

    Used by the History tab to display persisted tags on each history entry.
    Returns {} (not 503) when DB is unavailable.
    Tags are plain strings like ["phase:discovery", "feature:auth"].
    """
    if not db.is_available():
        return {}
    p = _project(project)
    project_id = db.get_or_create_project_id(p)

    result: dict = {}
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Prompts — only rows with user-facing tags (exclude source/llm-only rows)
            cur.execute(_SQL_GET_TAGGED_PROMPTS, (project_id,))
            for source_id, tags in cur.fetchall():
                if source_id and tags:
                    result[source_id] = tags_to_list(tags)
            # Commits — only rows with user-facing tags
            cur.execute(_SQL_GET_TAGGED_COMMITS, (project_id,))
            for commit_hash, tags in cur.fetchall():
                if commit_hash and tags:
                    result[commit_hash] = tags_to_list(tags)
    return result




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
    Idempotent: re-running updates short_desc without duplicating tags.
    """
    _require_db()
    import httpx

    p = _project(project)
    _seed_defaults(p)
    project_id = db.get_or_create_project_id(p)

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

                # Upsert tag with short_desc inline
                cur.execute(_SQL_UPSERT_TAG_GITHUB, (project_id, name, cat_id, desc or None))
                row = cur.fetchone()
                if row and row[0]:
                    created += 1
                    # Set due_date if present (not covered by the upsert above)
                    if due:
                        cur.execute(_SQL_SET_TAG_DUE_DATE, (due, row[1]))
                else:
                    updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(issues),
        "project": p,
    }


@router.get("/session-tags")
async def get_session_entity_tags(session_id: str, project: str | None = Query(None)):
    """Return all distinct tags from prompts/commits in a session.

    Returns tag strings like ["phase:discovery", "feature:auth"].
    """
    _require_db()
    p = _project(project)
    project_id = db.get_or_create_project_id(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SESSION_TAGS_FROM_MRR, (project_id, session_id, project_id, session_id))
            tags = [row[0] for row in cur.fetchall() if row[0]]

    return {"tags": tags, "session_id": session_id, "project": p}
