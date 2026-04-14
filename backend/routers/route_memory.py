"""
route_memory.py — Memory file generation and session summary endpoints.

Session summaries are stored directly in mem_ai_events (event_type='session_summary')
with the structured field action_items (merged threads + next steps).

Endpoints:
    GET  /memory/{project}/top-events           — top-N events by relevance_score
    POST /memory/{project}/session-summary      — generate + store session summary
    GET  /memory/{project}/session-summaries    — list recent session summaries
    POST /memory/{project}/regenerate           — regenerate context files from DB
    GET  /memory/{project}/llm-prompt           — get rendered system prompt (compact|full|gemini)
    POST /memory/{project}/embed-commits        — run Haiku digest + embedding for all unprocessed commits
    POST /memory/{project}/embed-prompts        — process all pending prompts across all sessions
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.database import db
from core.pipeline_log import _insert_run, _finish_run
from core.prompt_loader import prompts as _prompts

log = logging.getLogger(__name__)
router = APIRouter()

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_SESSION_PROMPTS = """
    SELECT prompt, response, created_at
    FROM mem_mrr_prompts
    WHERE project_id=%s AND session_id=%s
      AND prompt IS NOT NULL AND prompt != ''
    ORDER BY created_at
"""

_SQL_UPSERT_SESSION_SUMMARY = """
    INSERT INTO mem_ai_events
        (project_id, event_type, source_id, session_id,
         chunk, chunk_type, content, summary, action_items, tags, created_at)
    VALUES (%s, 'session_summary', %s, %s,
            0, 'full', %s, %s, %s, %s::jsonb, NOW())
    ON CONFLICT (project_id, event_type, source_id, chunk)
    DO UPDATE SET
        content      = EXCLUDED.content,
        summary      = EXCLUDED.summary,
        action_items = EXCLUDED.action_items,
        tags         = EXCLUDED.tags
    RETURNING id
"""

_SQL_LIST_SESSION_SUMMARIES = """
    SELECT e.id, e.session_id, e.summary, e.action_items, e.tags, e.created_at
    FROM mem_ai_events e
    WHERE e.project_id=%s AND e.event_type='session_summary'
    ORDER BY e.created_at DESC
    LIMIT %s
"""

_SQL_GET_EXISTING_SUMMARY = """
    SELECT id FROM mem_ai_events
    WHERE project_id=%s AND event_type='session_summary'
      AND source_id=%s
    LIMIT 1
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")


async def _call_haiku(system_prompt: str, user_message: str, max_tokens: int = 600) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return ""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=getattr(settings, "claude_haiku_model", "claude-haiku-4-5-20251001"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_haiku error: {e}")
        return ""


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


async def _generate_session_summary(
    project: str, session_id: str
) -> Optional[dict]:
    """
    Read session prompts, call Haiku with session_end_synthesis prompt,
    return {summary, action_items}.
    """
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SESSION_PROMPTS, (project_id, session_id))
            pairs = cur.fetchall()

    if not pairs:
        return None

    # Build conversation text for synthesis
    conv_lines = []
    for prompt, response, created_at in pairs[-20:]:  # last 20 pairs
        if prompt:
            conv_lines.append(f"User: {prompt[:300]}")
        if response:
            conv_lines.append(f"Assistant: {response[:300]}")
    conv_text = "\n".join(conv_lines)

    system_prompt = _prompts.content("session_end_synthesis") or (
        "Analyse this development session and produce a structured summary.\n"
        "Return JSON only:\n"
        "{\n"
        "  \"summary\": \"3-6 bullet points of what was decided/built/fixed\",\n"
        "  \"action_items\": \"bullet list merging unresolved threads AND next steps (empty string if none)\"\n"
        "}\n"
        "No preamble, no markdown fences."
    )

    raw = await _call_haiku(system_prompt, conv_text, max_tokens=600)
    if not raw:
        return None
    parsed = _parse_json(raw)
    if not parsed:
        return None

    return {
        "summary":      parsed.get("summary", ""),
        "action_items": parsed.get("action_items", ""),
    }


async def _trigger_root_regen(project: str) -> None:
    """Background task: regenerate root context files."""
    try:
        from memory.memory_files import MemoryFiles
        await asyncio.get_event_loop().run_in_executor(
            None, MemoryFiles().write_root_files, project
        )
        log.debug(f"Root files regenerated for '{project}'")
    except Exception as e:
        log.debug(f"_trigger_root_regen error: {e}")


async def _trigger_feature_regen(project: str, tag_name: str) -> None:
    """Background task: regenerate a feature CLAUDE.md."""
    try:
        from memory.memory_files import MemoryFiles
        await asyncio.get_event_loop().run_in_executor(
            None, MemoryFiles().write_feature_files, project, tag_name
        )
        log.debug(f"Feature files regenerated for '{project}/{tag_name}'")
    except Exception as e:
        log.debug(f"_trigger_feature_regen error: {e}")


# ── Models ────────────────────────────────────────────────────────────────────

class SessionSummaryRequest(BaseModel):
    session_id: str
    force:      bool = False   # re-generate even if summary already exists


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{project}/top-events")
async def get_top_events(
    project: str,
    limit:      int         = Query(5, ge=1, le=20),
    session_id: str | None  = Query(None),
):
    """Return top-N memory events ranked by time-decayed relevance score."""
    _require_db()
    from memory.memory_files import MemoryFiles
    events = MemoryFiles().get_top_events(project, limit)
    return {"events": events, "project": project, "total": len(events)}


@router.post("/{project}/session-summary")
async def create_session_summary(
    project: str,
    body: SessionSummaryRequest,
    background: BackgroundTasks = BackgroundTasks(),
):
    """
    Generate a structured session summary from session prompts.
    Stores directly in mem_ai_events (event_type='session_summary').
    Triggers root files regeneration as a background task.
    """
    _require_db()
    project_id = db.get_or_create_project_id(project)
    session_id = body.session_id
    import time as _time
    _pl_t0 = _time.monotonic()
    _pl_run_id = _insert_run(project_id, "session_summary", session_id)

    # Skip if already exists (unless force=True)
    if not body.force:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_EXISTING_SUMMARY, (project_id, session_id))
                if cur.fetchone():
                    _finish_run(_pl_run_id, "skipped", 1, 0, _pl_t0)
                    return {"status": "already_exists", "session_id": session_id}

    result = await _generate_session_summary(project, session_id)
    if not result:
        _finish_run(_pl_run_id, "skipped", 1, 0, _pl_t0)
        return {"status": "no_data", "session_id": session_id}

    summary_text = result["summary"]
    action_items = result["action_items"]
    combined_content = "\n\n".join(filter(None, [
        f"Summary:\n{summary_text}",
        f"Action Items:\n{action_items}" if action_items else "",
    ]))

    import json as _json
    # Only user-intent tags belong in mem_ai_events.tags (phase/feature/bug/source)
    # event, chunk_type, llm are system metadata — stripped by _user_tags filter
    auto_tags = _json.dumps({})
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPSERT_SESSION_SUMMARY,
                (project_id, session_id, session_id,
                 combined_content, summary_text,
                 action_items, auto_tags),
            )
            row = cur.fetchone()
            event_id = str(row[0]) if row else None

    # Regenerate root files in background
    background.add_task(_trigger_root_regen, project)

    _finish_run(_pl_run_id, "created", 1, 1, _pl_t0)
    log.info(f"Session summary stored in mem_ai_events for '{project}' session={session_id}")
    return {
        "status":       "created",
        "id":           event_id,
        "session_id":   session_id,
        "summary":      summary_text,
        "action_items": action_items,
    }


@router.get("/{project}/session-summaries")
async def list_session_summaries(
    project: str,
    limit: int = Query(10, ge=1, le=50),
):
    """Return recent session summaries (from mem_ai_events where event_type='session_summary')."""
    _require_db()
    project_id = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_SESSION_SUMMARIES, (project_id, limit))
            rows = cur.fetchall()
    return {
        "summaries": [
            {
                "id":           str(r[0]),
                "session_id":   r[1],
                "summary":      r[2],
                "action_items": r[3],
                "tags":         r[4] or {},
                "created_at":   r[5].isoformat() if r[5] else None,
            }
            for r in rows
        ],
        "project": project,
        "total": len(rows),
    }


@router.post("/{project}/regenerate")
async def regenerate_memory_files(
    project: str,
    scope:    str        = Query("root", pattern="^(root|feature|all)$"),
    tag_name: str | None = Query(None),
):
    """
    Regenerate context files from DB tables.

    scope=root    → CLAUDE.md, .cursorrules, system prompts, top_events.md
    scope=feature → features/{tag_name}/CLAUDE.md  (tag_name required)
    scope=all     → root + all active feature files
    """
    from memory.memory_files import MemoryFiles
    mf = MemoryFiles()
    written: list[str] = []

    if scope == "root":
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_root_files, project
        )
    elif scope == "feature":
        if not tag_name:
            raise HTTPException(400, "tag_name is required for scope=feature")
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_feature_files, project, tag_name
        )
    elif scope == "all":
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_all_files, project
        )

    return {
        "status":  "ok",
        "project": project,
        "scope":   scope,
        "written": [p.split("/workspace/")[-1] if "/workspace/" in p else p for p in written],
        "count":   len(written),
    }


@router.get("/{project}/llm-prompt")
async def get_llm_prompt(
    project: str,
    variant: str = Query("compact", pattern="^(compact|full|gemini)$"),
):
    """Return a rendered LLM system prompt. Useful for copy-paste into claude.ai, ChatGPT, etc."""
    from memory.memory_files import MemoryFiles
    mf = MemoryFiles()
    ctx = mf._load_context(project)

    if variant == "compact":
        content = mf.render_system_compact(ctx)
    elif variant == "full":
        content = mf.render_system_full(ctx)
    else:
        content = mf.render_gemini_context(ctx)

    return {"variant": variant, "project": project, "content": content}


@router.post("/{project}/embed-commits")
async def embed_commits(
    project: str,
    limit: int = Query(50),
):
    """Process all pending commits as tag-grouped batch events.

    Groups commits with identical phase/feature/bug tags into a single
    mem_ai_events row per group. Processes all pending commits regardless
    of the limit parameter (limit kept for API compatibility).
    Returns count of batch events created.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    from memory.memory_embedding import MemoryEmbedding
    emb = MemoryEmbedding()
    n = await emb.process_commit_batch(project, min_commits=1)
    return {"events_created": n, "project": project}


@router.post("/{project}/embed-prompts")
async def embed_prompts(project: str):
    """Process all pending prompts across every session for this project.

    For each session that has prompts with event_id IS NULL, runs
    process_prompt_batch() to create mem_ai_events rows and back-propagate
    event_id. Useful as a backfill after a session ends without triggering
    the periodic batch digest.
    Returns count of events created and sessions processed.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    project_id = db.get_or_create_project_id(project)
    # Find all sessions with unprocessed prompts
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT session_id, COUNT(*) as cnt
                       FROM mem_mrr_prompts
                       WHERE project_id=%s AND event_id IS NULL
                       GROUP BY session_id
                       ORDER BY cnt DESC""",
                    (project_id,),
                )
                sessions = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    from memory.memory_embedding import MemoryEmbedding
    emb = MemoryEmbedding()
    total_events = 0
    sessions_done = 0
    for session_id, prompt_cnt in sessions:
        try:
            event_id = await emb.process_prompt_batch(project, str(session_id), prompt_cnt)
            if event_id:
                sessions_done += 1
                total_events += 1  # at least 1 event per session
        except Exception as _e:
            log.debug(f"embed_prompts: session {str(session_id)[:8]} error: {_e}")

    return {
        "project": project,
        "sessions_processed": sessions_done,
        "sessions_found": len(sessions),
        "events_created": total_events,
    }

@router.post("/{project}/dedup-work-items")
async def dedup_work_items(project: str):
    """Merge duplicate work items that share the same feature or bug tag.

    For each tag value that maps to multiple work items, keeps one canonical
    item (named after the tag value) and merges all others into it.
    Re-links mem_ai_events.work_item_id to the canonical item.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    from memory.memory_promotion import MemoryPromotion
    result = await MemoryPromotion().dedup_work_items(project)
    return {"project": project, **result}


@router.get("/{project}/pipeline-status")
async def get_pipeline_status(project: str):
    """Return pipeline health dashboard: last-24h stats per pipeline, pending counts, recent errors."""
    if not db.is_available():
        return {"last_24h": {}, "pending": {}, "recent_errors": []}

    project_id = db.get_or_create_project_id(project)

    pipelines = ["commit_embed", "commit_store", "commit_code_extract",
                 "session_summary", "tag_match", "work_item_embed"]
    last_24h: dict = {}

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Per-pipeline counts in last 24h
                cur.execute(
                    """SELECT pipeline, status, COUNT(*) AS cnt,
                              MAX(started_at) AS last_run
                       FROM mem_pipeline_runs
                       WHERE project_id = %s
                         AND started_at > NOW() - INTERVAL '24 hours'
                       GROUP BY pipeline, status""",
                    (project_id,),
                )
                rows = cur.fetchall()
                # Aggregate
                agg: dict = {}
                for pl, st, cnt, last_run in rows:
                    if pl not in agg:
                        agg[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}
                    key = st if st in ("ok", "error", "skipped") else "error"
                    agg[pl][key] += cnt
                    if last_run:
                        existing = agg[pl]["last_run"]
                        if not existing or last_run.isoformat() > existing:
                            agg[pl]["last_run"] = last_run.isoformat()

                for pl in pipelines:
                    last_24h[pl] = agg.get(pl, {"ok": 0, "error": 0, "skipped": 0, "last_run": None})

                # Pending commits (not embedded — event_id set by process_commit on completion)
                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND event_id IS NULL",
                    (project_id,),
                )
                commits_not_embedded = cur.fetchone()[0] or 0

                # Pending work items (unmatched)
                cur.execute(
                    """SELECT COUNT(*) FROM mem_ai_work_items
                       WHERE project_id=%s AND tag_id_ai IS NULL AND tag_id_user IS NULL
                         AND status_user != 'done'""",
                    (project_id,),
                )
                work_items_unmatched = cur.fetchone()[0] or 0

                # Recent errors (last 10)
                cur.execute(
                    """SELECT pipeline, source_id, error_msg, started_at
                       FROM mem_pipeline_runs
                       WHERE project_id=%s AND status='error'
                       ORDER BY started_at DESC LIMIT 10""",
                    (project_id,),
                )
                recent_errors = [
                    {
                        "pipeline": r[0],
                        "source_id": r[1] or "",
                        "error_msg": r[2] or "",
                        "at": r[3].isoformat() if r[3] else None,
                    }
                    for r in cur.fetchall()
                ]

    except Exception as e:
        log.warning(f"get_pipeline_status error: {e}")
        return {"last_24h": {pl: {"ok": 0, "error": 0, "skipped": 0, "last_run": None} for pl in pipelines},
                "pending": {}, "recent_errors": []}

    return {
        "last_24h": last_24h,
        "pending": {
            "commits_not_embedded": commits_not_embedded,
            "work_items_unmatched": work_items_unmatched,
        },
        "recent_errors": recent_errors,
    }


@router.get("/{project}/data-dashboard")
async def get_data_dashboard(project: str):
    """Data Dashboard: mirror layer counts, AI layer counts, pipeline health, pending."""
    if not db.is_available():
        return {"mirror": {}, "ai": {}, "pipeline": {}, "pending": {}, "recent_errors": [], "fallback": True}

    project_id = db.get_or_create_project_id(project)
    mirror: dict = {}
    ai: dict = {}
    pipeline: dict = {}
    pending: dict = {}
    recent_errors: list = []

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:

                # ── Mirror layer ──────────────────────────────────────────
                for table, key in [
                    ("mem_mrr_commits",  "commits"),
                    ("mem_mrr_prompts",  "prompts"),
                    ("mem_mrr_items",    "items"),
                    ("mem_mrr_messages", "messages"),
                ]:
                    try:
                        cur.execute(
                            f"""SELECT COUNT(*),
                                       COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
                                       MAX(created_at)
                                FROM {table} WHERE project_id = %s""",
                            (project_id,),
                        )
                        r = cur.fetchone()
                        mirror[key] = {
                            "total": r[0] or 0,
                            "last_24h": r[1] or 0,
                            "last_at": r[2].isoformat() if r[2] else None,
                        }
                    except Exception:
                        conn.rollback()
                        mirror[key] = {"total": 0, "last_24h": 0, "last_at": None}

                # Commits: pending embed
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND event_id IS NULL",
                        (project_id,),
                    )
                    mirror["commits"]["pending_embed"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    mirror["commits"]["pending_embed"] = 0

                # Prompts: pending embed
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND event_id IS NULL",
                        (project_id,),
                    )
                    mirror["prompts"]["pending_embed"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    mirror["prompts"]["pending_embed"] = 0

                # ── AI layer ──────────────────────────────────────────────
                # Events
                try:
                    cur.execute(
                        """SELECT COUNT(*),
                                  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
                                  MAX(created_at)
                           FROM mem_ai_events WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["events"] = {
                        "total": r[0] or 0,
                        "last_24h": r[1] or 0,
                        "last_at": r[2].isoformat() if r[2] else None,
                        "by_type": {},
                    }
                    cur.execute(
                        "SELECT event_type, COUNT(*) FROM mem_ai_events WHERE project_id=%s GROUP BY event_type ORDER BY 2 DESC",
                        (project_id,),
                    )
                    ai["events"]["by_type"] = {row[0]: row[1] for row in cur.fetchall()}
                except Exception:
                    conn.rollback()
                    ai["events"] = {"total": 0, "last_24h": 0, "last_at": None, "by_type": {}}

                # Work items
                try:
                    cur.execute(
                        """SELECT COUNT(*),
                                  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
                                  MAX(created_at),
                                  COUNT(*) FILTER (WHERE status_user NOT IN ('done','archived')),
                                  COUNT(*) FILTER (WHERE status_user = 'done'),
                                  COUNT(*) FILTER (WHERE tag_id_user IS NOT NULL)
                           FROM mem_ai_work_items WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["work_items"] = {
                        "total": r[0] or 0,
                        "last_24h": r[1] or 0,
                        "last_at": r[2].isoformat() if r[2] else None,
                        "active": r[3] or 0,
                        "done": r[4] or 0,
                        "linked": r[5] or 0,
                    }
                except Exception:
                    conn.rollback()
                    ai["work_items"] = {"total": 0, "last_24h": 0, "last_at": None,
                                        "active": 0, "done": 0, "linked": 0}

                # Feature snapshots (planner_tags with AI content)
                try:
                    cur.execute(
                        """SELECT COUNT(*),
                                  COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '24 hours'),
                                  MAX(updated_at)
                           FROM planner_tags
                           WHERE project_id = %s
                             AND (description IS NOT NULL OR acceptance_criteria IS NOT NULL)""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["feature_snapshots"] = {
                        "total": r[0] or 0,
                        "last_24h": r[1] or 0,
                        "last_at": r[2].isoformat() if r[2] else None,
                    }
                except Exception:
                    conn.rollback()
                    ai["feature_snapshots"] = {"total": 0, "last_24h": 0, "last_at": None}

                # ── Pipeline runs (last 24h) ───────────────────────────────
                pl_keys = ["commit_embed", "commit_store", "commit_code_extract",
                           "session_summary", "tag_match", "work_item_embed"]
                try:
                    cur.execute(
                        """SELECT pipeline, status, COUNT(*), MAX(started_at)
                           FROM mem_pipeline_runs
                           WHERE project_id = %s AND started_at > NOW() - INTERVAL '24 hours'
                           GROUP BY pipeline, status""",
                        (project_id,),
                    )
                    agg: dict = {}
                    for pl, st, cnt, last_run in cur.fetchall():
                        if pl not in agg:
                            agg[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}
                        key = st if st in ("ok", "error", "skipped") else "error"
                        agg[pl][key] += cnt
                        if last_run:
                            ex = agg[pl]["last_run"]
                            if not ex or last_run.isoformat() > ex:
                                agg[pl]["last_run"] = last_run.isoformat()
                    for pl in pl_keys:
                        pipeline[pl] = agg.get(pl, {"ok": 0, "error": 0, "skipped": 0, "last_run": None})
                except Exception:
                    conn.rollback()
                    for pl in pl_keys:
                        pipeline[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}

                # ── Pending ───────────────────────────────────────────────
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND event_id IS NULL",
                        (project_id,),
                    )
                    pending["commits_not_embedded"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    pending["commits_not_embedded"] = 0

                try:
                    cur.execute(
                        """SELECT COUNT(*) FROM mem_ai_work_items
                           WHERE project_id=%s AND tag_id_ai IS NULL AND tag_id_user IS NULL
                             AND status_user != 'done'""",
                        (project_id,),
                    )
                    pending["work_items_unmatched"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    pending["work_items_unmatched"] = 0

                # ── Recent errors ─────────────────────────────────────────
                try:
                    cur.execute(
                        """SELECT pipeline, source_id, error_msg, started_at
                           FROM mem_pipeline_runs
                           WHERE project_id=%s AND status='error'
                           ORDER BY started_at DESC LIMIT 5""",
                        (project_id,),
                    )
                    recent_errors = [
                        {"pipeline": r[0], "source_id": r[1] or "",
                         "error_msg": r[2] or "", "at": r[3].isoformat() if r[3] else None}
                        for r in cur.fetchall()
                    ]
                except Exception:
                    conn.rollback()

    except Exception as e:
        log.warning(f"get_data_dashboard error: {e}")
        return {"mirror": mirror, "ai": ai, "pipeline": pipeline,
                "pending": pending, "recent_errors": recent_errors, "error": str(e)}

    return {
        "mirror": mirror,
        "ai": ai,
        "pipeline": pipeline,
        "pending": pending,
        "recent_errors": recent_errors,
    }


@router.get("/{project}/workflow-templates")
async def get_workflow_templates(project: str):
    """Return delivery-type → workflow mapping + available workflows for this project."""
    from pathlib import Path
    import yaml as _yaml

    templates_path = Path(__file__).parent.parent.parent / "workspace" / "_templates" / "workflows" / "templates.yaml"
    templates: dict = {}
    if templates_path.exists():
        try:
            data = _yaml.safe_load(templates_path.read_text()) or {}
            templates = data.get("templates", {})
        except Exception:
            pass

    workflows: list = []
    if db.is_available():
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT w.id::text, w.name,
                                  COUNT(n.id) AS node_count
                           FROM pr_graph_workflows w
                           LEFT JOIN pr_graph_nodes n ON n.workflow_id = w.id
                           WHERE w.project_id = %s
                           GROUP BY w.id, w.name
                           ORDER BY w.name""",
                        (project_id,),
                    )
                    for r in cur.fetchall():
                        workflows.append({"id": r[0], "name": r[1], "node_count": r[2] or 0})
        except Exception as e:
            log.debug(f"get_workflow_templates workflows query error: {e}")

    return {"templates": templates, "workflows": workflows}
