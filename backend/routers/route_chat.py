"""
Chat router with SSE streaming support.

Server mode: API keys stored encrypted in DB (mng_clients.server_api_keys / mng_user_api_keys).
Balance is checked before every LLM call and debited after.
When REQUIRE_AUTH=True (or DEV_MODE=True), a valid Bearer token is required.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.config import settings
from core.auth import get_optional_user
from data.dl_api_keys import get_key
from core.database import db
from agents.providers.pr_pricing import load_pricing, calculate_cost, can_user_access
from agents.providers import call_claude, call_deepseek, call_gemini, call_grok
from routers.route_usage import log_usage
from memory.memory_sessions import SessionStore

# ── SQL ─────────────────────────────────────────────────────────────────────────


_SQL_INSERT_INTERACTION = """
    INSERT INTO mem_mrr_prompts
           (project_id, session_id, source_id,
            prompt, response, tags, created_at)
       VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz)
       ON CONFLICT (project_id, source_id) WHERE source_id IS NOT NULL DO NOTHING
"""

_SQL_INSERT_TRANSACTION = """
    INSERT INTO mng_transactions
       (user_id, type, amount_usd, base_cost_usd, description, ref)
       VALUES (%s, %s, %s, %s, %s, %s)
"""

_SQL_GET_SESSION_FEATURE = """
    SELECT feature FROM mng_session_tags WHERE project_id=%s
"""

_SQL_GET_ACTIVE_FEATURES = """
    SELECT t.name FROM planner_tags t
       JOIN mng_tags_categories tc ON tc.id = t.category_id
       WHERE t.project_id=%s AND tc.name='feature' AND t.status='active'
       ORDER BY t.name
"""

_SQL_UPSERT_SESSION_FEATURE = """
    INSERT INTO mng_session_tags (project_id, feature)
       VALUES (%s, %s)
       ON CONFLICT (project_id) DO UPDATE SET feature=%s, updated_at=NOW()
"""

_SQL_GET_WORKFLOW_BY_NAME = """
    SELECT id, name FROM pr_graph_workflows WHERE project_id=%s AND name=%s
"""

_SQL_GET_WORKFLOW_FUZZY = """
    SELECT id, name FROM pr_graph_workflows
    WHERE project_id=%s AND lower(name) LIKE %s
    LIMIT 1
"""

_SQL_INSERT_GRAPH_RUN = """
    INSERT INTO pr_graph_runs (id, project_id, workflow_id, status, user_input)
    VALUES (%s, %s, %s, 'running', %s)
"""

_SQL_UPDATE_COMMIT_TAGS = """
    UPDATE mem_mrr_commits
    SET tags = (tags - 'phase' - 'feature' - 'bug')
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('phase',   %s::text) ELSE '{}'::jsonb END
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('feature', %s::text) ELSE '{}'::jsonb END
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('bug',     %s::text) ELSE '{}'::jsonb END
    WHERE project_id=%s AND session_id=%s
"""

_SQL_UPDATE_PROMPT_TAGS = """
    UPDATE mem_mrr_prompts
    SET tags = (tags - 'phase' - 'feature' - 'bug')
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('phase',   %s::text) ELSE '{}'::jsonb END
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('feature', %s::text) ELSE '{}'::jsonb END
        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('bug',     %s::text) ELSE '{}'::jsonb END
    WHERE project_id=%s AND session_id=%s
"""

# ────────────────────────────────────────────────────────────────────────────────

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: str = "claude"
    system: str = ""
    stream: bool = True
    tags: dict = {}  # {"phase": "discovery", "feature": "...", "bug_ref": "..."}


def _get_store() -> SessionStore:
    return SessionStore(
        workspace_dir=Path(settings.workspace_dir),
        project=settings.active_project or "default",
    )


def _append_history(
    project: str, provider: str, user_msg: str, response: str,
    session_id: str, user_id: Optional[str] = None,
    user_email: Optional[str] = None, ts: Optional[str] = None,
    tags: Optional[dict] = None,
) -> str:
    """Write a completed exchange to the DB (mem_mrr_prompts).

    DB is the primary store. JSONL files are no longer written here.
    Returns the ts string so callers can correlate the event.
    """
    if ts is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not db.is_available():
        return ts

    import json as _json
    from core.tags import tags_to_dict as _tags_to_dict
    # Convert tags dict → JSONB-ready dict (handles bug_ref → bug prefix)
    tags_dict: dict = {}
    for k, v in (tags or {}).items():
        if v:
            prefix = "bug" if k == "bug_ref" else k
            tags_dict[prefix] = v

    tags_dict["source"] = provider or "aicli"
    project_id = db.get_or_create_project_id(project)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # mem_mrr_prompts — feeds memory distillation pipeline
                cur.execute(
                    _SQL_INSERT_INTERACTION,
                    (project_id, session_id, ts,
                     (user_msg or "")[:4000], (response or "")[:8000],
                     _json.dumps(tags_dict), ts),
                )
    except Exception:
        pass  # never break chat because of logging

    return ts


def _update_runtime_state(project: str, provider: str, prompt_preview: str, session_id: str, user_id: Optional[str] = None) -> None:
    """Update _system/dev_runtime_state.json with the latest exchange metadata."""
    try:
        sys_dir = Path(settings.workspace_dir) / project / "_system"
        sys_dir.mkdir(parents=True, exist_ok=True)
        state_path = sys_dir / "dev_runtime_state.json"

        existing: dict = {}
        if state_path.exists():
            try:
                existing = json.loads(state_path.read_text())
            except Exception:
                pass

        session_count = existing.get("session_count", 0)
        if existing.get("last_session_id") != session_id:
            session_count += 1

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        state = {
            "last_updated": now,
            "last_session_id": session_id,
            "last_session_ts": now,
            "session_count": session_count,
            "last_provider": provider,
            "last_prompt_preview": prompt_preview[:200],
        }
        state_path.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _append_transaction(
    user_id: str, tx_type: str, amount_usd: float,
    description: str, ref: str = "", base_cost_usd: Optional[float] = None,
) -> None:
    """Append a transaction record to PostgreSQL (when available) and JSONL file."""
    try:
        # Primary: PostgreSQL
        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            _SQL_INSERT_TRANSACTION,
                            (user_id, tx_type, amount_usd, base_cost_usd, description, ref or ""),
                        )
            except Exception:
                pass
        # Always write to file (fallback / portability)
        tx_dir = Path(settings.data_dir) / "transactions"
        tx_dir.mkdir(parents=True, exist_ok=True)
        record: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": tx_type,
            "amount_usd": amount_usd,
            "description": description,
            "ref": ref,
        }
        if base_cost_usd is not None:
            record["base_cost_usd"] = base_cost_usd
        with open(tx_dir / f"{user_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


async def _call_provider(provider: str, messages: list[dict], system: str) -> dict:
    """Dispatch to the right LLM client using server-side keys. Passes full conversation history."""
    api_key = get_key(provider)
    if provider == "claude":
        return await call_claude(messages, system=system, api_key=api_key or None)
    elif provider == "deepseek":
        return await call_deepseek(messages, system=system, api_key=api_key or None)
    elif provider == "gemini":
        # Gemini takes a single prompt — flatten history into context prefix
        if len(messages) > 1:
            history_txt = "\n".join(f"[{m['role']}]: {m['content']}" for m in messages[:-1])
            prompt = f"Previous conversation:\n{history_txt}\n\n[user]: {messages[-1]['content']}"
        else:
            prompt = messages[-1]["content"] if messages else ""
        return await call_gemini(prompt, system=system, api_key=api_key or None)
    elif provider == "grok":
        return await call_grok(messages, system=system, api_key=api_key or None)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


def _debit_user(user_id: str, provider: str, model: str, input_tokens: int, output_tokens: int) -> None:
    """Log usage, deduct cost from user balance, append transaction."""
    try:
        from data.dl_user import find_by_id, update_user
        pricing      = load_pricing()
        markup       = pricing.get("providers", {}).get(provider, {}).get("markup_percent", 0)
        real_cost    = calculate_cost(provider, model, input_tokens, output_tokens, 0)
        charged_cost = calculate_cost(provider, model, input_tokens, output_tokens, markup)

        # Write usage row with both real and charged cost
        log_usage(user_id=user_id, provider=provider, model=model,
                  input_tokens=input_tokens, output_tokens=output_tokens,
                  charged_usd=charged_cost)

        if charged_cost <= 0:
            return
        user = find_by_id(user_id)
        if not user:
            return
        new_used = round(user.get("balance_used_usd", 0.0) + charged_cost, 8)
        update_user(user_id, balance_used_usd=new_used)
        _append_transaction(
            user_id, "usage_debit", charged_cost,
            f"{provider} {model} {input_tokens}+{output_tokens} tokens",
            base_cost_usd=real_cost,
        )
    except Exception:
        pass  # never block chat because of billing


async def _stream_response(
    message: str, provider: str, system: str,
    user_id: Optional[str], user: Optional[dict], model_used: Optional[str],
    store: SessionStore, session_id: str, tags: Optional[dict] = None,
):
    """Generate SSE events from LLM response, save assistant reply, log usage."""
    try:
        # Build full conversation history so LLM has context from prior turns.
        # store.append_message(session_id, "user", ...) was already called before this generator.
        sess = store.get(session_id)
        messages = [{"role": m["role"], "content": m["content"]}
                    for m in (sess.get("messages", []) if sess else [])]
        if not messages:
            messages = [{"role": "user", "content": message}]
        result = await _call_provider(provider, messages, system)
        content = result.get("content", "")
        actual_model = result.get("model", provider)

        # Pre-compute ts so we can emit it before [DONE] for client-side polling
        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Stream in chunks
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            yield f"data: {content[i:i + chunk_size]}\n\n"
            await asyncio.sleep(0.01)

        # Emit event ts BEFORE [DONE] so frontend can poll for tag suggestions
        yield f"data: [EVENT:{_ts}]\n\n"
        yield "data: [DONE]\n\n"

        # Persist assistant reply
        store.append_message(session_id, "assistant", content)

        # Append to shared project history + create event row in DB
        project = settings.active_project or "default"
        user_email = user.get("email") if user else None
        _append_history(project, provider, message, content, session_id, user_id, user_email, ts=_ts, tags=tags)
        _update_runtime_state(project, provider, message, session_id, user_id)

        # Fire-and-forget: embed + proactive feature detection
        try:
            from memory.memory_embedding import embed_and_store as _embed
            asyncio.create_task(_embed(
                project, "history", _ts, f"Q: {message}\nA: {content}",
                chunk_index=0, chunk_type="full",
                metadata={"provider": provider, "source": "ui"},
            ))
            # Proactive feature auto-detection (first prompt in new session only)
            if db.is_available():
                asyncio.create_task(
                    _auto_detect_session_feature(session_id, project, message, messages)
                )
        except Exception:
            pass

        # Log usage + debit balance
        input_t = result.get("input_tokens", 0)
        output_t = result.get("output_tokens", 0)
        if user_id and user_id != "dev-admin":
            _debit_user(user_id, provider, actual_model, input_t, output_t)

    except Exception as e:
        yield f"data: [ERROR] {e}\n\n"



async def _auto_detect_session_feature(
    session_id: str, project: str, user_msg: str, messages: list[dict]
) -> None:
    """Auto-detect and apply the most relevant feature tag for a new session's first prompt.

    Guards:
    - Only runs on the first user message in a session.
    - Skips if the session already has a feature tag in session_tags.
    - Calls Haiku with the prompt + list of existing feature names.
    - Applies the matched feature to session_tags and session JSON if confident.
    Silent on any error.
    """
    if not db.is_available():
        return
    try:
        # Guard: only on first user message
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if len(user_msgs) != 1:
            return

        project_id = db.get_or_create_project_id(project)
        # Guard: skip if session already has a feature tag
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_SESSION_FEATURE, (project_id,))
                row = cur.fetchone()
        if row and row[0]:
            return

        from data.dl_api_keys import get_key
        key = get_key("claude") or get_key("anthropic")
        if not key:
            return

        # Load existing feature names
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_ACTIVE_FEATURES, (project_id,))
                features = [r[0] for r in cur.fetchall()]

        if not features:
            return

        import anthropic
        feat_list = ", ".join(f'"{f}"' for f in features[:30])
        prompt = (
            f"Existing features: [{feat_list}]\n\n"
            f"New developer prompt:\n{user_msg[:400]}\n\n"
            'Does this prompt clearly relate to one of the existing features? '
            'If yes, return {"feature": "exact-feature-name"}. '
            'If not a confident match, return {"feature": null}. '
            'Return ONLY valid JSON, nothing else.'
        )
        client = anthropic.AsyncAnthropic(api_key=key)
        resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (resp.content[0].text if resp.content else "").strip()
        import re as _re
        m = _re.search(r'\{.*?\}', text, _re.DOTALL)
        if not m:
            return
        parsed = json.loads(m.group())
        feature_name = parsed.get("feature")
        if not feature_name or feature_name not in features:
            return

        # Apply feature to session_tags
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPSERT_SESSION_FEATURE, (project_id, feature_name, feature_name))

        # Also update the session JSON file's feature field
        store = SessionStore(
            workspace_dir=Path(settings.workspace_dir),
            project=project,
        )
        sess = store.get(session_id)
        if sess is not None:
            sess.setdefault("metadata", {}).setdefault("tags", {})["feature"] = feature_name
            store._save(sess)

    except Exception:
        pass


async def _handle_run_command(pipeline_name: str, project: str, session_id: str) -> str:
    """Handle /run <pipeline-name> chat command.

    Looks up the workflow by name in the DB and starts a background run.
    Returns a user-facing status message.
    """
    if not db.is_available():
        return "⚠ Database not available — cannot run pipelines from chat."

    import uuid as _uuid
    try:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORKFLOW_BY_NAME, (project_id, pipeline_name))
                row = cur.fetchone()
        if not row:
            # Try partial/case-insensitive match
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WORKFLOW_FUZZY, (project_id, f"%{pipeline_name.lower()}%"))
                    row = cur.fetchone()
        if not row:
            return f"⚠ No pipeline named **{pipeline_name}** found. Check the Pipelines tab for available flows."

        workflow_id, workflow_name = str(row[0]), row[1]
        run_id = str(_uuid.uuid4())

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_GRAPH_RUN,
                    (run_id, project_id, workflow_id, f"/run {pipeline_name}"),
                )

        from pipelines.pipeline_graph_runner import run_graph_workflow

        async def _bg():
            try:
                await run_graph_workflow(workflow_id, f"/run {pipeline_name}", run_id, project)
            except Exception as _e:
                import logging
                logging.getLogger(__name__).error(f"Chat /run failed: {_e}")

        asyncio.create_task(_bg())
        return f"▶ Started pipeline **{workflow_name}** (run ID: `{run_id[:8]}…`). Check the **Pipelines** tab → run log for live status."

    except Exception as e:
        return f"⚠ Failed to start pipeline: {e}"


# ── Hook endpoints (unauthenticated — called by CLI hook scripts) ─────────────

class HookLogRequest(BaseModel):
    ts: str | None = None
    session_id: str
    prompt: str
    source: str = "claude_cli"
    provider: str = "claude"
    tags: list[str] = []              # ["phase:discovery", "feature:auth"] — preferred
    phase: str | None = None          # legacy alias → "phase:{phase}" added to tags
    feature: str | None = None        # legacy alias → "feature:{feature}" added to tags
    session_src_id: str | None = None
    context_tags: dict = {}           # legacy — ignored when tags[] is provided


class HookResponseRequest(BaseModel):
    ts: str                    # matches the ts from HookLogRequest
    session_id: str
    response: str
    stop_reason: str = "end_turn"


def _count_session_prompts(project: str, session_id: str) -> int:
    """Count how many prompts exist for this session (used for batch trigger)."""
    try:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_prompts "
                    "WHERE project_id=%s AND session_id=%s",
                    (project_id, session_id),
                )
                return cur.fetchone()[0]
    except Exception:
        return 0


def _get_batch_size(project: str) -> int:
    """Read memory.batch_size from aicli.yaml (default 3)."""
    try:
        from pathlib import Path as _Path
        import yaml as _yaml
        cfg = _Path(settings.workspace_dir).parent / "aicli.yaml"
        if cfg.exists():
            d = _yaml.safe_load(cfg.read_text()) or {}
            return int((d.get("memory") or {}).get("batch_size", 3))
    except Exception:
        pass
    return 3


async def _generate_memory_batch(project: str, session_id: str, n: int) -> None:
    """Generate a Haiku digest + embedding for the last N prompts → mem_ai_events."""
    try:
        from memory.memory_embedding import MemoryEmbedding
        event_id = await MemoryEmbedding().process_prompt_batch(project, session_id, n)
        if event_id:
            log.debug(f"Memory batch digest generated for {project}/{session_id}: {event_id}")
    except Exception as e:
        log.debug(f"_generate_memory_batch error: {e}")


async def _check_backlog_threshold(project: str, source_type: str) -> None:
    """Trigger backlog digest if pending row count meets the configured threshold."""
    try:
        from memory.memory_backlog import MemoryBacklog
        await MemoryBacklog(project).check_and_trigger(source_type)
    except Exception as e:
        log.debug(f"_check_backlog_threshold({source_type}) error: {e}")



@router.post("/{project}/hook-log")
async def hook_log_prompt(project: str, body: HookLogRequest):
    """Unauthenticated endpoint — CLI hooks write prompts directly to mem_mrr_prompts.

    Called by log_user_prompt.sh after every Claude Code prompt.
    No auth required: runs on localhost, hook scripts have no JWT.
    Also triggers memory batch digest every N prompts.
    """
    ts = body.ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not db.is_available():
        return {"ok": False, "reason": "db_unavailable"}
    try:
        # Build tags list: prefer body.tags; fall back to legacy phase/feature fields
        tags_list = list(body.tags) if body.tags else []
        if not tags_list:
            if body.phase:
                tags_list.append(f"phase:{body.phase}")
            if body.feature:
                tags_list.append(f"feature:{body.feature}")
        # Also merge any context_tags dict (legacy fallback)
        if not tags_list and body.context_tags:
            for k, v in body.context_tags.items():
                if v:
                    prefix = "bug" if k == "bug_ref" else k
                    tags_list.append(f"{prefix}:{v}")

        import json as _json
        from core.tags import tags_to_dict as _tags_to_dict
        hook_tags = _tags_to_dict(tags_list)
        hook_tags["source"] = body.source or "claude_cli"
        project_id = db.get_or_create_project_id(project)

        # Fallback: if hook sent no phase/feature/bug, read from active mng_session_tags
        if "phase" not in hook_tags or "feature" not in hook_tags:
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT phase, feature, bug_ref FROM mng_session_tags WHERE project_id=%s",
                            (project_id,),
                        )
                        st = cur.fetchone()
                        if st:
                            if st[0] and "phase"   not in hook_tags: hook_tags["phase"]   = st[0]
                            if st[1] and "feature" not in hook_tags: hook_tags["feature"] = st[1]
                            if st[2] and "bug"     not in hook_tags: hook_tags["bug"]     = st[2]
            except Exception:
                pass
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_INTERACTION,
                    (project_id, body.session_id, ts,
                     (body.prompt or "")[:4000], "",
                     _json.dumps(hook_tags), ts),
                )

        # Fire memory batch digest every N prompts (fire-and-forget)
        count = _count_session_prompts(project, body.session_id)
        batch_size = _get_batch_size(project)
        if count > 0 and count % batch_size == 0:
            asyncio.create_task(_generate_memory_batch(project, body.session_id, batch_size))

        # Backlog threshold check — fire-and-forget after each prompt stored
        asyncio.create_task(_check_backlog_threshold(project, "prompts"))

        return {"ok": True, "ts": ts}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


@router.post("/{project}/hook-response")
async def hook_update_response(project: str, body: HookResponseRequest):
    """Unauthenticated endpoint — CLI hooks update response text in mem_mrr_prompts.

    Called by log_session_stop.sh after Claude Code finishes responding.
    When ts is empty, finds the most recent empty-response row for the session.
    """
    if not db.is_available():
        return {"ok": False, "reason": "db_unavailable"}
    try:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                if body.ts:
                    cur.execute(
                        """UPDATE mem_mrr_prompts SET response = %s
                           WHERE project_id=%s
                             AND source_id = %s AND session_id = %s
                             AND (response IS NULL OR response = '')""",
                        ((body.response or "")[:8000], project_id, body.ts, body.session_id),
                    )
                else:
                    # Find latest empty-response row for this session
                    cur.execute(
                        """UPDATE mem_mrr_prompts SET response = %s
                           WHERE id = (
                               SELECT id FROM mem_mrr_prompts
                               WHERE project_id=%s
                                 AND session_id = %s
                                 AND (response IS NULL OR response = '')
                               ORDER BY created_at DESC LIMIT 1
                           )""",
                        ((body.response or "")[:8000], project_id, body.session_id),
                    )
                updated = cur.rowcount
        return {"ok": True, "updated": updated}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """SSE streaming chat endpoint."""
    # Balance / access check
    if current_user and current_user.get("id") != "dev-admin":
        from data.dl_user import find_by_id
        full_user = find_by_id(current_user["sub"]) if "sub" in current_user else current_user
        model = settings.claude_model  # default; real model resolved in _call_provider
        ok, reason = can_user_access(full_user or current_user, req.provider, model)
        if not ok:
            raise HTTPException(status_code=402, detail=reason)
    else:
        full_user = current_user

    store = _get_store()
    session_id = req.session_id or str(uuid.uuid4())

    session = store.get(session_id)
    if session is None:
        metadata = {"tags": req.tags} if req.tags else {}
        session = store.create(metadata=metadata)
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    # Detect /run <pipeline-name> command
    if req.message.strip().startswith("/run "):
        pipeline_name = req.message.strip()[5:].strip()
        project = settings.active_project or "default"
        run_resp = await _handle_run_command(pipeline_name, project, req.session_id or session_id)

        async def _run_sse():
            yield f"data: {run_resp}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            _run_sse(), media_type="text/event-stream",
            headers={"X-Session-Id": session_id},
        )

    user_id = current_user.get("sub") or current_user.get("id") if current_user else None

    return StreamingResponse(
        _stream_response(req.message, req.provider, req.system, user_id, full_user, None, store, session_id, tags=req.tags or {}),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/")
async def chat(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Non-streaming chat endpoint."""
    # Balance / access check
    if current_user and current_user.get("id") != "dev-admin":
        from data.dl_user import find_by_id
        full_user = find_by_id(current_user.get("sub") or current_user.get("id")) or current_user
        model = settings.claude_model
        ok, reason = can_user_access(full_user, req.provider, model)
        if not ok:
            raise HTTPException(status_code=402, detail=reason)
    else:
        full_user = current_user

    store = _get_store()
    session_id = req.session_id or str(uuid.uuid4())

    session = store.get(session_id)
    if session is None:
        metadata = {"tags": req.tags} if req.tags else {}
        session = store.create(metadata=metadata)
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    # Detect /run <pipeline-name> command
    if req.message.strip().startswith("/run "):
        pipeline_name = req.message.strip()[5:].strip()
        project = settings.active_project or "default"
        run_msg = await _handle_run_command(pipeline_name, project, session_id)
        return {"content": run_msg, "session_id": session_id}

    try:
        # Build full conversation history for multi-turn context
        sess = store.get(session_id)
        messages_hist = [{"role": m["role"], "content": m["content"]}
                         for m in (sess.get("messages", []) if sess else [])]
        if not messages_hist:
            messages_hist = [{"role": "user", "content": req.message}]

        result = await _call_provider(req.provider, messages_hist, req.system)
        content = result.get("content", "")
        actual_model = result.get("model", req.provider)
        store.append_message(session_id, "assistant", content)

        user_id = current_user.get("sub") or current_user.get("id") if current_user else None

        # Append to shared project history
        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        project = settings.active_project or "default"
        user_email = full_user.get("email") if full_user else None
        _append_history(project, req.provider, req.message, content, session_id, user_id, user_email, ts=_ts, tags=req.tags or {})
        _update_runtime_state(project, req.provider, req.message, session_id, user_id)
        # Log usage + debit balance
        input_t = result.get("input_tokens", 0)
        output_t = result.get("output_tokens", 0)
        if user_id and user_id != "dev-admin":
            log_usage(user_id=user_id, provider=req.provider, model=actual_model,
                      input_tokens=input_t, output_tokens=output_t)
            _debit_user(user_id, req.provider, actual_model, input_t, output_t)

        return {
            "response": content,
            "provider": req.provider,
            "session_id": session_id,
            "input_tokens": input_t,
            "output_tokens": output_t,
        }

    except Exception as e:
        return {"error": str(e), "session_id": session_id}


@router.get("/sessions")
async def list_sessions():
    store = _get_store()
    return store.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    store = _get_store()
    session = store.get(session_id)
    if session is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return session


class SessionTagsPatch(BaseModel):
    phase:   Optional[str] = None
    feature: Optional[str] = None
    bug_ref: Optional[str] = None


def _backfill_session_tags(
    project: str, session_id: str,
    phase: Optional[str] = None,
    feature: Optional[str] = None,
    bug_ref: Optional[str] = None,
) -> None:
    """Retroactively set phase/feature/bug tags on all history.jsonl entries + DB commits.

    Called whenever any session tag is changed via PATCH /sessions/{id}/tags so that
    all prompts and commits linked to that session become filterable by the new tags.
    Only keys explicitly passed (not None) are updated; None-valued keys are removed.
    """
    # 1. Rewrite matching entries in history.jsonl
    hist_path = Path(settings.workspace_dir) / project / "_system" / "history.jsonl"
    if hist_path.exists():
        try:
            lines = hist_path.read_text().splitlines()
            updated = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("session_id") == session_id:
                        if phase   is not None: entry["phase"]   = phase   or None
                        if feature is not None: entry["feature"] = feature or None
                        if bug_ref is not None: entry["bug_ref"] = bug_ref or None
                    updated.append(json.dumps(entry, ensure_ascii=False))
                except Exception:
                    updated.append(line)
            hist_path.write_text("\n".join(updated) + "\n")
        except Exception:
            pass  # read-only filesystem or concurrent write — best-effort

    # 2. Update mem_mrr_commits.tags + mem_mrr_prompts.tags for all rows in this session
    if db.is_available():
        import logging as _log
        _logger = _log.getLogger(__name__)
        try:
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_UPDATE_COMMIT_TAGS,
                        (phase, phase, feature, feature, bug_ref, bug_ref, project_id, session_id),
                    )
                    c_rows = cur.rowcount
                    cur.execute(
                        _SQL_UPDATE_PROMPT_TAGS,
                        (phase, phase, feature, feature, bug_ref, bug_ref, project_id, session_id),
                    )
                    p_rows = cur.rowcount
            _logger.info(
                f"backfill_session_tags: project={project} session={session_id[:8]} "
                f"phase={phase!r} feature={feature!r} bug={bug_ref!r} "
                f"→ commits={c_rows} prompts={p_rows}"
            )
        except Exception as exc:
            _logger.warning(f"backfill_session_tags DB failed: {exc}")


@router.patch("/sessions/{session_id}/tags")
async def patch_session_tags(
    session_id: str,
    body: SessionTagsPatch,
    project: str | None = None,
):
    """Update the phase/feature/bug_ref tags stored in a session's metadata.

    For UI sessions: writes to the session JSON file.
    For CLI/workflow sessions: writes to _system/session_phases.json as a fallback.
    In both cases, retroactively backfills phase onto all history.jsonl entries
    and DB rows (events, commits) for this session.
    """
    p = project or settings.active_project or "default"
    store = _get_store()
    session = store.get(session_id)
    if session is not None:
        # UI session — update metadata in the session file
        meta = session.setdefault("metadata", {})
        tags = meta.setdefault("tags", {})
        if body.phase   is not None: tags["phase"]   = body.phase or None
        if body.feature is not None: tags["feature"] = body.feature or None
        if body.bug_ref is not None: tags["bug_ref"] = body.bug_ref or None
        # Do NOT update updated_at — tag edits shouldn't change session sort order
        store._save(session)
        if body.phase is not None or body.feature is not None or body.bug_ref is not None:
            _backfill_session_tags(p, session_id,
                                   phase=body.phase, feature=body.feature, bug_ref=body.bug_ref)
        return {"ok": True, "tags": tags}

    # CLI / workflow session — persist in session_phases.json
    phases_path = Path(settings.workspace_dir) / p / "_system" / "session_phases.json"
    phases_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing: dict = json.loads(phases_path.read_text()) if phases_path.exists() else {}
    except Exception:
        existing = {}
    entry = existing.setdefault(session_id, {})
    if body.phase   is not None: entry["phase"]   = body.phase or None
    if body.feature is not None: entry["feature"] = body.feature or None
    if body.bug_ref is not None: entry["bug_ref"] = body.bug_ref or None
    phases_path.write_text(json.dumps(existing, indent=2))
    if body.phase is not None or body.feature is not None or body.bug_ref is not None:
        _backfill_session_tags(p, session_id,
                               phase=body.phase, feature=body.feature, bug_ref=body.bug_ref)
    return {"ok": True, "tags": entry}
