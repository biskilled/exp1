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

_SQL_GET_SYSTEM_ROLE = """
    SELECT content FROM mng_system_roles
    WHERE client_id=1 AND name=%s AND is_active=TRUE
    LIMIT 1
"""

_SQL_UPSERT_SESSION_SUMMARY = """
    INSERT INTO mem_ai_events
        (project_id, event_type, source_id, session_id,
         chunk, chunk_type, content, summary, action_items,
         importance, tags, created_at)
    VALUES (%s, 'session_summary', %s, %s,
            0, 'full', %s, %s, %s, 2, %s::jsonb, NOW())
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

    # Load synthesis prompt from DB
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SYSTEM_ROLE, ("session_end_synthesis",))
            row = cur.fetchone()
    system_prompt = row[0] if row else (
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

    # Skip if already exists (unless force=True)
    if not body.force:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_EXISTING_SUMMARY, (project_id, session_id))
                if cur.fetchone():
                    return {"status": "already_exists", "session_id": session_id}

    result = await _generate_session_summary(project, session_id)
    if not result:
        return {"status": "no_data", "session_id": session_id}

    summary_text = result["summary"]
    action_items = result["action_items"]
    combined_content = "\n\n".join(filter(None, [
        f"Summary:\n{summary_text}",
        f"Action Items:\n{action_items}" if action_items else "",
    ]))

    haiku_model = getattr(settings, "haiku_model", "claude-haiku-4-5-20251001")
    import json as _json
    auto_tags = _json.dumps({
        "event": "session_summary", "chunk_type": "full",
        "llm": haiku_model,
    })
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
    limit: int = Query(50, description="Max commits to process in one call"),
):
    """Run process_commit() for commits that have no Haiku digest yet.

    Selects commits where tags->>'llm' IS NULL (never processed), runs Haiku
    digest + embedding for each, back-propagates summary and llm tag to
    mem_mrr_commits. Returns count processed.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT commit_hash FROM mem_mrr_commits
                       WHERE project_id=%s
                         AND (tags->>'llm') IS NULL
                       ORDER BY committed_at DESC NULLS LAST
                       LIMIT %s""",
                    (project, limit),
                )
                hashes = [r[0] for r in cur.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not hashes:
        return {"processed": 0, "project": project, "note": "all commits already processed"}

    from memory.memory_embedding import MemoryEmbedding
    emb = MemoryEmbedding()
    processed = 0
    errors = 0
    for h in hashes:
        try:
            result = await emb.process_commit(project, h)
            if result:
                processed += 1
        except Exception as e:
            log.debug(f"embed_commits {h}: {e}")
            errors += 1

    return {"processed": processed, "errors": errors, "project": project}
