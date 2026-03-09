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

from config import settings
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


@router.post("/semantic")
async def semantic_search(body: SearchRequest, user=Depends(get_optional_user)):
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL + pgvector required for semantic search")

    from core.embeddings import semantic_search as _search
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
    )
    return {"results": results, "query": body.query, "total": len(results)}


@router.get("/ingest")
async def ingest(project: str = Query(""), user=Depends(get_optional_user)):
    """Trigger bulk embedding ingest for history + roles (background task)."""
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL + pgvector required for embeddings")

    p = project or settings.active_project or "default"

    async def _do_ingest():
        from core.embeddings import ingest_history, ingest_roles
        h = await ingest_history(p)
        r = await ingest_roles(p)
        import logging
        logging.getLogger(__name__).info(f"Ingest {p}: history={h}, roles={r}")

    asyncio.create_task(_do_ingest())
    return {"status": "started", "project": p}
