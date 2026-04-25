"""
search.py — Tagged context search + semantic (embedding) search.

/search/tagged  — tag-filtered prompts from mem_mrr_prompts
/search/semantic — cosine similarity over mem_ai_events + mem_ai_work_items (pgvector)
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
    if tag_id:
        # tag_id is a planner_tags UUID — look up the tag name and filter by "cat:name"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT tc.name || ':' || t.name FROM planner_tags t
                           JOIN mng_tags_categories tc ON tc.id = t.category_id
                           WHERE t.id=%s::uuid LIMIT 1""",
                        (tag_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        filters.append("%s = ANY(p.tags)")
                        params.append(row[0])
        except Exception:
            pass

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
    """Cosine-similarity search over mem_ai_events + mem_ai_work_items.

    Embeds the query with text-embedding-3-small, then queries both tables
    using pgvector <=> operator.  Results from both tables are merged and
    re-ranked by score before returning.

    source_types filter values:
      mem_ai_events  → "commit" | "prompt_batch" | "session_summary" | "item" | "message"
      mem_ai_work_items → "work_item"
    """
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for semantic search")

    project = body.project or settings.active_project or "default"
    limit = min(body.limit, 50)

    # ── Embed the query ────────────────────────────────────────────────────────
    try:
        from agents.tools.tool_memory import _embed_sync, _vec_str
        vec = _embed_sync(body.query)
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

                # ── mem_ai_events ──────────────────────────────────────────────
                want_events = (
                    not body.source_types
                    or any(s != "work_item" for s in body.source_types)
                )
                if want_events:
                    event_types_filter = ""
                    params_ev: list = [vs, project_id, vs]

                    allowed_event_types = [
                        s for s in (body.source_types or [])
                        if s != "work_item"
                    ] if body.source_types else []

                    if allowed_event_types:
                        placeholders = ",".join("%s" for _ in allowed_event_types)
                        event_types_filter = f"AND e.event_type IN ({placeholders})"
                        params_ev.extend(allowed_event_types)

                    phase_filter = ""
                    if body.phase:
                        phase_filter = "AND e.tags->>'phase' = %s"
                        params_ev.append(body.phase)

                    feature_filter = ""
                    if body.feature:
                        feature_filter = "AND e.tags->>'feature' = %s"
                        params_ev.append(body.feature)

                    params_ev.append(limit * 2)

                    cur.execute(
                        f"""SELECT e.id::text,
                                   e.event_type AS source_type,
                                   left(COALESCE(e.content, e.summary, ''), 150) AS title,
                                   COALESCE(e.summary, left(e.content, 300)) AS snippet,
                                   e.created_at,
                                   e.tags,
                                   e.session_id::text,
                                   1 - (e.embedding <=> %s::vector) AS score
                            FROM mem_ai_events e
                            WHERE e.project_id = %s
                              AND e.embedding IS NOT NULL
                              {event_types_filter}
                              {phase_filter}
                              {feature_filter}
                            ORDER BY e.embedding <=> %s::vector
                            LIMIT %s""",
                        params_ev,
                    )
                    for row in cur.fetchall():
                        results.append({
                            "id":          row[0],
                            "source_type": row[1],
                            "title":       row[2] or "",
                            "snippet":     row[3] or "",
                            "created_at":  row[4].isoformat() if row[4] else None,
                            "tags":        row[5] or {},
                            "session_id":  row[6],
                            "score":       round(float(row[7] or 0), 4),
                        })

                # ── mem_ai_work_items ──────────────────────────────────────────
                want_wi = (
                    not body.source_types
                    or "work_item" in body.source_types
                )
                if want_wi:
                    cur.execute(
                        """SELECT w.id::text,
                                  'work_item' AS source_type,
                                  w.name_ai AS title,
                                  COALESCE(w.summary_ai, left(w.desc_ai, 300)) AS snippet,
                                  w.created_at,
                                  w.tags,
                                  NULL AS session_id,
                                  1 - (w.embedding <=> %s::vector) AS score
                           FROM mem_ai_work_items w
                           WHERE w.project_id = %s
                             AND w.embedding IS NOT NULL
                             AND (w.deleted_at IS NULL)
                           ORDER BY w.embedding <=> %s::vector
                           LIMIT %s""",
                        (vs, project_id, vs, limit * 2),
                    )
                    for row in cur.fetchall():
                        results.append({
                            "id":          row[0],
                            "source_type": "work_item",
                            "title":       row[2] or "",
                            "snippet":     row[3] or "",
                            "created_at":  row[4].isoformat() if row[4] else None,
                            "tags":        row[5] or {},
                            "session_id":  None,
                            "score":       round(float(row[7] or 0), 4),
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

