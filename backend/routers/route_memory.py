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
    POST /memory/{project}/quality-check        — re-run quality gate on staging work items
    POST /memory/{project}/prune-tags           — delete planner_tags except keep_ids list
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

@router.post("/{project}/rebuild")
async def rebuild_work_items(
    project: str,
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(True, description="If true, only preview what would be deleted"),
):
    """Rebuild all open+unlinked work items and their events from scratch.

    Deletes open work items (status != 'done') that have no user tag link
    (tag_id_user IS NULL), then nullifies event_id on all mirror rows and
    queues embed-prompts + embed-commits to reprocess everything.
    Pass ?dry_run=false to execute. Default is preview only.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    project_id = db.get_or_create_project_id(project)

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Count what would be deleted
                cur.execute(
                    """SELECT COUNT(*) FROM mem_ai_work_items
                       WHERE project_id = %s
                         AND COALESCE(status_user,'active') NOT IN ('done','archived')
                         AND tag_id_user IS NULL""",
                    (project_id,),
                )
                wi_count = cur.fetchone()[0]

                cur.execute(
                    """SELECT COUNT(*) FROM mem_ai_events
                       WHERE project_id = %s
                         AND event_type IN ('prompt_batch','commit','session_summary')""",
                    (project_id,),
                )
                ev_count = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND event_id IS NOT NULL",
                    (project_id,),
                )
                p_backprop = cur.fetchone()[0]

                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND event_id IS NOT NULL",
                    (project_id,),
                )
                c_backprop = cur.fetchone()[0]

                if dry_run:
                    return {
                        "dry_run": True,
                        "project": project,
                        "would_delete": {
                            "work_items": wi_count,
                            "events": ev_count,
                        },
                        "would_reset": {
                            "prompt_event_ids": p_backprop,
                            "commit_event_ids": c_backprop,
                        },
                        "note": "Pass ?dry_run=false to execute",
                    }

                # --- EXECUTE ---
                # 1. NULL work_item_id on events before deleting work items (FK)
                cur.execute(
                    """UPDATE mem_ai_events SET work_item_id = NULL
                       WHERE project_id = %s AND work_item_id IN (
                           SELECT id FROM mem_ai_work_items
                           WHERE project_id = %s
                             AND COALESCE(status_user,'active') NOT IN ('done','archived')
                             AND tag_id_user IS NULL
                       )""",
                    (project_id, project_id),
                )

                # 2. Delete open+unlinked work items
                cur.execute(
                    """DELETE FROM mem_ai_work_items
                       WHERE project_id = %s
                         AND COALESCE(status_user,'active') NOT IN ('done','archived')
                         AND tag_id_user IS NULL""",
                    (project_id,),
                )
                deleted_wi = cur.rowcount

                # 3. Delete auto-generated events (not linked to kept work items)
                cur.execute(
                    """DELETE FROM mem_ai_events
                       WHERE project_id = %s
                         AND event_type IN ('prompt_batch','commit','session_summary')
                         AND work_item_id IS NULL""",
                    (project_id,),
                )
                deleted_ev = cur.rowcount

                # 4. Reset back-propagated event_ids on mirror tables
                cur.execute(
                    "UPDATE mem_mrr_prompts SET event_id = NULL WHERE project_id = %s",
                    (project_id,),
                )
                reset_prompts = cur.rowcount

                cur.execute(
                    "UPDATE mem_mrr_commits SET event_id = NULL WHERE project_id = %s",
                    (project_id,),
                )
                reset_commits = cur.rowcount

            conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Queue reprocessing in background
    async def _reprocess():
        from memory.memory_embedding import MemoryEmbedding
        emb = MemoryEmbedding()
        # Embed all pending prompts
        try:
            with db.conn() as conn2:
                with conn2.cursor() as cur2:
                    cur2.execute(
                        """SELECT session_id, COUNT(*) FROM mem_mrr_prompts
                           WHERE project_id=%s AND event_id IS NULL
                           GROUP BY session_id ORDER BY COUNT(*) DESC""",
                        (project_id,),
                    )
                    sessions = cur2.fetchall()
            for sid, cnt in sessions:
                try:
                    await emb.process_prompt_batch(project, str(sid), cnt)
                except Exception as _e:
                    log.debug(f"rebuild reprocess prompt session {str(sid)[:8]}: {_e}")
        except Exception as _e:
            log.warning(f"rebuild reprocess prompts error: {_e}")

        # Embed all pending commits
        try:
            await emb.process_commit_batch(project, min_commits=1)
        except Exception as _e:
            log.warning(f"rebuild reprocess commits error: {_e}")

    background_tasks.add_task(_reprocess)

    return {
        "dry_run": False,
        "project": project,
        "deleted": {
            "work_items": deleted_wi,
            "events": deleted_ev,
        },
        "reset": {
            "prompt_event_ids": reset_prompts,
            "commit_event_ids": reset_commits,
        },
        "reprocess": "queued in background (embed-prompts + embed-commits)",
    }


class PruneTagsBody(BaseModel):
    keep_ids: list[str]  # UUIDs to keep; all others will be deleted


@router.post("/{project}/quality-check")
async def run_quality_check(project: str, background_tasks: BackgroundTasks):
    """Re-run quality gate on all staging work items.

    Checks name specificity and evidence count for every item with
    quality_stage='staging', upgrading to 'approved' or 'rejected'.
    Returns {checked, approved, rejected, still_staging}.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    project_id = db.get_or_create_project_id(project)

    # Load all staging items
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM mem_ai_work_items WHERE project_id=%s AND quality_stage='staging'",
                    (project_id,),
                )
                staging_ids = [str(r[0]) for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    from memory.memory_promotion import MemoryPromotion
    mp = MemoryPromotion()
    checked = approved = rejected = still_staging = 0

    for wi_id in staging_ids:
        try:
            stage = await mp.run_quality_gate(project_id, wi_id)
            checked += 1
            if stage == "approved":
                approved += 1
            elif stage == "rejected":
                rejected += 1
            else:
                still_staging += 1
        except Exception as e:
            log.debug(f"quality_check error for {wi_id}: {e}")
            still_staging += 1

    return {
        "project": project,
        "checked": checked,
        "approved": approved,
        "rejected": rejected,
        "still_staging": still_staging,
    }


@router.post("/{project}/prune-tags")
async def prune_tags(project: str, body: PruneTagsBody):
    """Delete all planner_tags for this project EXCEPT those in keep_ids.

    Use this to reset the tag taxonomy to a curated set before a full rebuild.
    Returns {deleted, kept}.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    if not body.keep_ids:
        raise HTTPException(status_code=400, detail="keep_ids must not be empty — pass the UUIDs to keep")

    project_id = db.get_or_create_project_id(project)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Count total before deletion
                cur.execute("SELECT COUNT(*) FROM planner_tags WHERE project_id=%s", (project_id,))
                total_before = cur.fetchone()[0] or 0

                # Delete all except keep_ids
                import psycopg2.extras
                cur.execute(
                    "DELETE FROM planner_tags WHERE project_id=%s AND id != ALL(%s::uuid[])",
                    (project_id, body.keep_ids),
                )
                deleted = cur.rowcount
        kept = total_before - deleted
        log.info(f"prune_tags: deleted={deleted} kept={kept} for '{project}'")
        return {"project": project, "deleted": deleted, "kept": kept}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
                 "session_summary", "tag_match", "work_item_embed", "work_item_promote"]
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
    health: dict = {}
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
                                  COUNT(*) FILTER (WHERE tag_id_user IS NOT NULL),
                                  COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '24 hours'),
                                  MAX(updated_at),
                                  COUNT(*) FILTER (WHERE tag_id_user IS NULL AND tag_id_ai IS NULL),
                                  COUNT(*) FILTER (WHERE tag_id_user IS NULL AND tag_id_ai IS NOT NULL),
                                  COUNT(*) FILTER (WHERE score_ai = 0),
                                  COUNT(*) FILTER (WHERE score_ai = 1),
                                  COUNT(*) FILTER (WHERE score_ai = 2),
                                  COUNT(*) FILTER (WHERE score_ai = 3),
                                  COUNT(*) FILTER (WHERE score_ai = 4),
                                  COUNT(*) FILTER (WHERE score_ai = 5),
                                  COUNT(*) FILTER (WHERE quality_stage = 'staging'),
                                  COUNT(*) FILTER (WHERE quality_stage = 'rejected'),
                                  COUNT(*) FILTER (WHERE category_ai = 'feature'),
                                  COUNT(*) FILTER (WHERE category_ai = 'bug'),
                                  COUNT(*) FILTER (WHERE category_ai = 'task')
                           FROM mem_ai_work_items WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    total_wi = r[0] or 0
                    unlinked_ai_only = r[8] or 0
                    ai["work_items"] = {
                        "total":           total_wi,
                        "last_24h":        r[1] or 0,
                        "last_at":         r[2].isoformat() if r[2] else None,
                        "active":          r[3] or 0,
                        "done":            r[4] or 0,
                        "linked":          r[5] or 0,
                        "promoted_24h":    r[6] or 0,
                        "last_promoted_at": r[7].isoformat() if r[7] else None,
                        "unlinked_ai_only": unlinked_ai_only,
                        "ai_suggested":    r[9] or 0,
                        "by_score": {
                            "0": r[10] or 0, "1": r[11] or 0, "2": r[12] or 0,
                            "3": r[13] or 0, "4": r[14] or 0, "5": r[15] or 0,
                        },
                        "staging":         r[16] or 0,
                        "rejected":        r[17] or 0,
                        "by_category": {
                            "feature": r[18] or 0,
                            "bug":     r[19] or 0,
                            "task":    r[20] or 0,
                        },
                    }
                except Exception:
                    conn.rollback()
                    total_wi = 0
                    unlinked_ai_only = 0
                    ai["work_items"] = {"total": 0, "last_24h": 0, "last_at": None,
                                        "active": 0, "done": 0, "linked": 0,
                                        "promoted_24h": 0, "last_promoted_at": None,
                                        "unlinked_ai_only": 0, "ai_suggested": 0,
                                        "by_score": {"0":0,"1":0,"2":0,"3":0,"4":0,"5":0},
                                        "staging": 0, "rejected": 0,
                                        "by_category": {"feature": 0, "bug": 0, "task": 0}}

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
                           "session_summary", "tag_match", "work_item_embed",
                           "work_item_promote"]
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

                # ── Health KPIs ───────────────────────────────────────────
                health: dict = {}
                try:
                    # Count features (category_id matching 'feature' category)
                    cur.execute(
                        """SELECT COUNT(DISTINCT pt.id)
                           FROM planner_tags pt
                           JOIN mng_tags_categories tc ON tc.id=pt.category_id AND tc.name='feature'
                           WHERE pt.project_id=%s AND pt.status NOT IN ('archived', 'done')""",
                        (project_id,),
                    )
                    total_features = cur.fetchone()[0] or 0

                    # Features with at least 1 linked work item
                    cur.execute(
                        """SELECT COUNT(DISTINCT pt.id)
                           FROM planner_tags pt
                           JOIN mng_tags_categories tc ON tc.id=pt.category_id AND tc.name='feature'
                           WHERE pt.project_id=%s AND pt.status NOT IN ('archived', 'done')
                             AND EXISTS (
                               SELECT 1 FROM mem_ai_work_items wi
                               WHERE (wi.tag_id_user=pt.id OR wi.tag_id_ai=pt.id)
                                 AND wi.project_id=%s
                             )""",
                        (project_id, project_id),
                    )
                    features_with_wi = cur.fetchone()[0] or 0

                    # Total active planner tags
                    cur.execute(
                        "SELECT COUNT(*) FROM planner_tags WHERE project_id=%s AND status NOT IN ('archived','done')",
                        (project_id,),
                    )
                    total_tags = cur.fetchone()[0] or 0

                    # Re-use earlier values (may be 0 if query failed)
                    _wi = ai.get("work_items", {})
                    staging = _wi.get("staging", 0)
                    rejected = _wi.get("rejected", 0)
                    _total_wi = _wi.get("total", 0)
                    _unlinked = _wi.get("unlinked_ai_only", 0)

                    health = {
                        "orphan_rate":        round(_unlinked / max(_total_wi, 1), 3),
                        "coverage_rate":      round(features_with_wi / max(total_features, 1), 3),
                        "staging_count":      staging,
                        "rejected_count":     rejected,
                        "scope_breakdown":    _wi.get("by_category", {}),
                        "total_planner_tags": total_tags,
                        "max_recommended_wi": max(5, int(total_tags * 1.5)),
                    }
                except Exception:
                    conn.rollback()
                    health = {
                        "orphan_rate": 0, "coverage_rate": 0,
                        "staging_count": 0, "rejected_count": 0,
                        "scope_breakdown": {}, "total_planner_tags": 0,
                        "max_recommended_wi": 5,
                    }

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
                "pending": pending, "health": health, "recent_errors": recent_errors, "error": str(e)}

    return {
        "mirror":        mirror,
        "ai":            ai,
        "pipeline":      pipeline,
        "pending":       pending,
        "recent_errors": recent_errors,
        "health":        health,
    }


@router.get("/{project}/llm-costs")
async def llm_costs(project: str):
    """Return LLM cost breakdown for memory pipeline calls (last 24h + all time).

    Queries mng_usage_logs WHERE source='memory', grouped by provider and model.
    Does NOT filter by project — pipeline costs are system-wide.
    """
    if not db.is_available():
        return {"last_24h": {"total_calls": 0, "total_cost_usd": 0, "by_model": []},
                "all_time":  {"total_calls": 0, "total_cost_usd": 0, "by_model": []}}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        provider, model,
                        COUNT(*) AS calls,
                        SUM(cost_usd) AS cost_usd,
                        SUM(input_tokens) AS input_tokens,
                        SUM(output_tokens) AS output_tokens,
                        (created_at > NOW() - INTERVAL '24 hours') AS is_24h
                    FROM mng_usage_logs
                    WHERE source = 'memory'
                    GROUP BY provider, model, (created_at > NOW() - INTERVAL '24 hours')
                    ORDER BY cost_usd DESC
                """)
                rows = cur.fetchall()

        def _build(is_24h_flag: bool) -> dict:
            models = [
                {
                    "provider": r[0], "model": r[1],
                    "calls": r[2], "cost_usd": float(r[3] or 0),
                    "input_tokens": r[4] or 0, "output_tokens": r[5] or 0,
                }
                for r in rows if r[6] == is_24h_flag
            ]
            return {
                "total_calls":    sum(m["calls"] for m in models),
                "total_cost_usd": round(sum(m["cost_usd"] for m in models), 6),
                "by_model":       models,
            }

        return {"last_24h": _build(True), "all_time": _build(False), "project": project}
    except Exception as e:
        log.warning(f"llm_costs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
