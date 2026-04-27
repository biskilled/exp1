"""
search.py — Tagged context search + semantic (embedding) search.

/search/tagged   — tag-filtered prompts from mem_mrr_prompts
/search/semantic — cosine similarity over mem_work_items (pgvector, embedding VECTOR(1536))

Note: mem_ai_events was dropped (migration m078+). Semantic search now only covers
mem_work_items rows that have been embedded via POST /memory/{project}/embed-prompts.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.auth import get_optional_user
from core.database import db

# ── SQL ──────────────────────────────────────────────────────────────────────

# Base template for tagged-context queries over mem_mrr_prompts.
# mem_mrr_prompts has no title/feature column; left(prompt,120) serves as title.
# {where} is injected at call site.
_SQL_SEARCH_PROMPTS_BASE = (
    """SELECT p.id, 'prompt' AS event_type, p.source_id,
              left(p.prompt, 120) AS title,
              p.tags, p.session_id,
              p.created_at
         FROM mem_mrr_prompts p
         {where}
        ORDER BY p.created_at DESC
        LIMIT %s"""
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()


@router.get("/tagged")
async def get_tagged_context(
    project: str = Query(""),
    phase: Optional[str] = Query(None),
    feature: Optional[str] = Query(None),
    entity_value_id: Optional[int] = Query(None),  # deprecated alias; ignored
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

    project_id = db.get_or_create_project_id(p)
    filters: list[str] = ["p.project_id=%s"]
    params: list = [project_id]

    # Filter by tags[] array (phase/feature are now inline tags)
    if phase:
        filters.append("('phase:' || %s) = ANY(p.tags)")
        params.append(phase)
    if feature:
        filters.append("('feature:' || %s) = ANY(p.tags)")
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
                "title": r[3], "tags": r[4] or [],
                "session_id": r[5],
                "created_at": r[6].isoformat() if r[6] else None,
            }
            for r in rows
        ]
        return {"events": events, "total": len(events), "phase": phase, "feature": feature}
    except Exception as exc:
        raise HTTPException(500, str(exc))


# ── Semantic (embedding) search ───────────────────────────────────────────────

class SemanticSearchRequest(BaseModel):
    query: str
    project: str = ""
    limit: int = 10
    # Optional filters
    source_types: Optional[list[str]] = None   # ["commit","prompt_batch","work_item",...]
    phase: Optional[str] = None
    feature: Optional[str] = None


@router.post("/semantic")
async def semantic_search(body: SemanticSearchRequest, user=Depends(get_optional_user)):
    """Cosine-similarity search over mem_work_items (pgvector).

    Embeds the query with text-embedding-3-small, then queries mem_work_items
    using the pgvector <=> operator.

    Only items that have been embedded appear in results (run
    POST /memory/{project}/embed-prompts to populate embeddings).

    source_types: "work_item" (default and only supported value)
    """
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for semantic search")

    project = body.project or settings.active_project or "default"
    limit = min(body.limit, 50)

    # ── Embed the query (async to avoid blocking the event loop) ──────────────
    try:
        from agents.tools.tool_memory import _embed_async, _vec_str
        vec = await _embed_async(body.query)
    except Exception:
        vec = None

    if not vec:
        raise HTTPException(400, "Embedding unavailable — check OpenAI API key in settings")

    vs = _vec_str(vec)
    project_id = db.get_or_create_project_id(project)
    results: list[dict] = []

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:

                # ── mem_work_items (only table with embeddings now) ────────────
                phase_filter = ""
                params: list = [vs, project_id, vs]

                if body.phase:
                    phase_filter = "AND w.tags->>'phase' = %s"
                    params.insert(-1, body.phase)  # before the trailing vs
                    params = [vs, project_id]
                    if body.phase:
                        params.append(body.phase)
                    params.append(vs)

                # Rebuild params cleanly
                params = [vs, project_id]
                extra_filters = ""
                if body.phase:
                    extra_filters += " AND w.tags->>'phase' = %s"
                    params.append(body.phase)
                if body.feature:
                    extra_filters += " AND w.tags->>'feature' = %s"
                    params.append(body.feature)
                params.append(vs)
                params.append(limit)

                cur.execute(
                    f"""SELECT w.id::text,
                               w.wi_type AS source_type,
                               w.name AS title,
                               left(COALESCE(w.summary, ''), 300) AS snippet,
                               w.created_at,
                               w.tags,
                               1 - (w.embedding <=> %s::vector) AS score
                        FROM mem_work_items w
                        WHERE w.project_id = %s
                          AND w.embedding IS NOT NULL
                          AND w.deleted_at IS NULL
                          AND (w.completed_at IS NULL OR w.completed_at > NOW() - INTERVAL '30 days')
                          {extra_filters}
                        ORDER BY w.embedding <=> %s::vector
                        LIMIT %s""",
                    params,
                )
                for row in cur.fetchall():
                    results.append({
                        "id":          row[0],
                        "source_type": row[1] or "work_item",
                        "title":       row[2] or "",
                        "snippet":     row[3] or "",
                        "created_at":  row[4].isoformat() if row[4] else None,
                        "tags":        row[5] or {},
                        "session_id":  None,
                        "score":       round(float(row[6] or 0), 4),
                    })

    except Exception as exc:
        raise HTTPException(500, str(exc))

    # Merge and re-rank by score
    results.sort(key=lambda r: r["score"], reverse=True)
    results = results[:limit]

    return {
        "query":   body.query,
        "project": project,
        "total":   len(results),
        "results": results,
    }


# ── Project-facts semantic search ─────────────────────────────────────────────

@router.get("/facts")
async def search_facts(
    query: str = Query(..., description="Natural language search query"),
    project: str = Query("", description="Project name"),
    limit: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None, description="Filter by category: stack|pattern|convention|constraint|general|code"),
    user=Depends(get_optional_user),
):
    """Cosine-similarity search over mem_ai_project_facts (pgvector).

    Searches embeddings of project facts, including the code_structure document
    embedded from code.md. Returns fact_key + fact_value + category.
    """
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for semantic search")

    project = project or settings.active_project or "default"
    limit = min(limit, 50)

    try:
        from agents.tools.tool_memory import _embed_async, _vec_str
        vec = await _embed_async(query)
    except Exception:
        vec = None

    if not vec:
        raise HTTPException(400, "Embedding unavailable — check OpenAI API key in settings")

    vs = _vec_str(vec)
    project_id = db.get_or_create_project_id(project)

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                extra = ""
                params: list = [vs, project_id]
                if category:
                    extra = "AND f.category = %s"
                    params.append(category)
                params += [vs, limit]
                cur.execute(
                    f"""SELECT f.id::text, f.fact_key, LEFT(f.fact_value, 500),
                               f.category, f.created_at,
                               1 - (f.embedding <=> %s::vector) AS score
                        FROM mem_ai_project_facts f
                        WHERE f.project_id = %s
                          AND f.embedding IS NOT NULL
                          AND f.valid_until IS NULL
                          AND f.conflict_status IS DISTINCT FROM 'pending_review'
                          {extra}
                        ORDER BY f.embedding <=> %s::vector
                        LIMIT %s""",
                    params,
                )
                results = [
                    {
                        "id":         r[0],
                        "fact_key":   r[1],
                        "fact_value": r[2],
                        "category":   r[3] or "general",
                        "created_at": r[4].isoformat() if r[4] else None,
                        "score":      round(float(r[5] or 0), 4),
                    }
                    for r in cur.fetchall()
                ]
    except Exception as exc:
        raise HTTPException(500, str(exc))

    return {
        "query":   query,
        "project": project,
        "total":   len(results),
        "results": results,
    }

