"""
search.py — Semantic search over the 5-layer memory system.

Requires PostgreSQL + pgvector + OpenAI API key (for embeddings).
Returns 503 when pgvector or OpenAI key is unavailable.
"""
from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.auth import get_optional_user
from core.database import db

# ── SQL ──────────────────────────────────────────────────────────────────────

# Base template for tagged-context queries over mem_mrr_prompts (replaces pr_events).
# mem_mrr_prompts has no title/feature column; left(prompt,120) serves as title.
# {where} is injected at call site.
_SQL_SEARCH_PROMPTS_BASE = (
    """SELECT p.id, 'prompt' AS event_type, p.source_id,
              left(p.prompt, 120) AS title,
              p.phase, p.session_id,
              p.created_at, p.metadata
         FROM mem_mrr_prompts p
         {where}
        ORDER BY p.created_at DESC
        LIMIT %s"""
)

_SQL_COUNT_INTERACTIONS_TOTAL = (
    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE client_id=1 AND project=%s AND event_type='prompt'"
)

_SQL_COUNT_INTERACTIONS_SINCE = (
    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE client_id=1 AND project=%s AND event_type='prompt' AND created_at > %s::timestamptz"
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    project: Optional[str] = None
    limit: int = 10
    source_types: Optional[list[str]] = None
    # Metadata filters for smart-chunk retrieval
    language: Optional[str] = None
    doc_type: Optional[str] = None
    file_path: Optional[str] = None
    chunk_types: Optional[list[str]] = None
    # Tag-aware filters — restrict results to events with this phase/feature
    phase: Optional[str] = None
    feature: Optional[str] = None
    # Entity-tag filters — restrict to embeddings tagged with a specific entity value or category
    entity_name: Optional[str] = None       # e.g. "auth", "UI dropbox"
    entity_category: Optional[str] = None  # e.g. "bug", "feature", "task"


@router.post("/semantic")
async def semantic_search(body: SearchRequest, user=Depends(get_optional_user)):
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL + pgvector required for semantic search")

    from memory.mem_embeddings import semantic_search as _search
    project = body.project or settings.active_project or "default"
    results = await _search(
        project=project,
        query=body.query,
        limit=max(1, min(body.limit, 50)),
        source_types=body.source_types or None,
        language=body.language,
        doc_type=body.doc_type,
        file_path=body.file_path,
        chunk_types=body.chunk_types or None,
        phase=body.phase,
        feature=body.feature,
        entity_name=body.entity_name,
        entity_category=body.entity_category,
    )
    return {"results": results, "query": body.query, "total": len(results)}


@router.get("/tagged")
async def get_tagged_context(
    project: str = Query(""),
    phase: Optional[str] = Query(None),
    feature: Optional[str] = Query(None),
    tag_id: Optional[str] = Query(None),        # planner_tags UUID — replaces entity_value_id
    entity_value_id: Optional[int] = Query(None),  # deprecated alias; ignored if tag_id given
    limit: int = Query(20),
    user=Depends(get_optional_user),
):
    """Return prompts filtered by phase, feature, or tag.

    Used by MCP get_tagged_context tool to retrieve structured context for a feature/phase.
    Queries mem_mrr_prompts and mem_mrr_tags.
    """
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required")

    p = project or settings.active_project or "default"

    filters: list[str] = ["p.client_id=1", "p.project=%s"]
    params: list = [p]

    effective_tag_id = tag_id
    if not effective_tag_id and entity_value_id:
        # Legacy: try to resolve entity_value_id → planner_tags UUID by seq_num / int PK
        # (mng_entity_values was merged into planner_tags; seq_num may match)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id::text FROM planner_tags WHERE client_id=1 AND project=%s AND seq_num=%s LIMIT 1",
                        (p, entity_value_id),
                    )
                    row = cur.fetchone()
                    if row:
                        effective_tag_id = row[0]
        except Exception:
            pass

    if effective_tag_id:
        # Filter by applied source tag — join through mem_mrr_tags
        filters.append(
            "p.id IN (SELECT prompt_id FROM mem_mrr_tags WHERE tag_id=%s::uuid AND prompt_id IS NOT NULL)"
        )
        params.append(effective_tag_id)
    else:
        # Filter by phase / feature columns (fast indexed lookup)
        if phase:
            filters.append("p.phase = %s")
            params.append(phase)
        if feature:
            # feature is stored in metadata JSONB or mng_session_tags (not a direct column)
            filters.append(
                "p.metadata->>'feature' = %s"
            )
            params.append(feature)

    where = "WHERE " + " AND ".join(filters)
    params.append(limit)

    sql = _SQL_SEARCH_PROMPTS_BASE.format(where=where)

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        events = [
            {
                "id": str(r[0]), "event_type": r[1], "source_id": r[2],
                "title": r[3], "phase": r[4],
                "session_id": r[5],
                "created_at": r[6].isoformat() if r[6] else None,
                "metadata": r[7] or {},
            }
            for r in rows
        ]
        return {"events": events, "total": len(events), "phase": phase, "feature": feature}
    except Exception as exc:
        raise HTTPException(500, str(exc))


@router.get("/ingest")
async def ingest(project: str = Query(""), user=Depends(get_optional_user)):
    """Trigger bulk embedding ingest for history + roles (background task)."""
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL + pgvector required for embeddings")

    p = project or settings.active_project or "default"

    async def _do_ingest():
        from memory.mem_embeddings import ingest_history, ingest_roles
        h = await ingest_history(p)
        r = await ingest_roles(p)
        import logging
        logging.getLogger(__name__).info(f"Ingest {p}: history={h}, roles={r}")

    asyncio.create_task(_do_ingest())
    return {"status": "started", "project": p}
