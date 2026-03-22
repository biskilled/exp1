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
    )
    return {"results": results, "query": body.query, "total": len(results)}


@router.get("/tagged")
async def get_tagged_context(
    project: str = Query(""),
    phase: Optional[str] = Query(None),
    feature: Optional[str] = Query(None),
    entity_value_id: Optional[int] = Query(None),
    limit: int = Query(20),
    user=Depends(get_optional_user),
):
    """Return events (prompts + commits) filtered by phase, feature, or entity tag.

    Used by MCP get_tagged_context tool to retrieve structured context for a feature/phase.
    """
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required")

    p = project or settings.active_project or "default"

    filters: list[str] = ["ev.client_id=1", "ev.project=%s"]
    params: list = [p]

    if entity_value_id:
        # Filter by applied entity tag — join through event_tags
        filters.append(
            "ev.id IN (SELECT event_id FROM pr_event_tags WHERE entity_value_id = %s)"
        )
        params.append(entity_value_id)
    else:
        # Filter by phase / feature columns (fast indexed lookup)
        if phase:
            filters.append(
                "COALESCE(ev.phase, ev.metadata->>'phase') = %s"
            )
            params.append(phase)
        if feature:
            filters.append(
                "COALESCE(ev.feature, ev.metadata->>'feature') = %s"
            )
            params.append(feature)

    where = "WHERE " + " AND ".join(filters)
    params.append(limit)

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""SELECT ev.id, ev.event_type, ev.source_id, ev.title,
                               ev.phase, ev.feature, ev.session_id,
                               ev.created_at, ev.metadata
                          FROM pr_events ev
                          {where}
                         ORDER BY ev.created_at DESC
                         LIMIT %s""",
                    params,
                )
                rows = cur.fetchall()
        events = [
            {
                "id": r[0], "event_type": r[1], "source_id": r[2],
                "title": r[3], "phase": r[4], "feature": r[5],
                "session_id": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "metadata": r[8] or {},
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
