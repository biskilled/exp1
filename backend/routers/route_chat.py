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
from memory.mem_sessions import SessionStore

# ── SQL ─────────────────────────────────────────────────────────────────────────

# Removed: _SQL_INSERT_PROMPT_EVENT wrote to pr_events (dropped in memory infra migration).
# Prompt logging now uses _SQL_INSERT_INTERACTION (pr_prompts) only.

_SQL_INSERT_INTERACTION = """
    INSERT INTO pr_prompts
           (client_id, project, session_id, llm_source, event_type, source_id,
            prompt, response, phase, metadata, created_at)
       VALUES (1, %s, %s, %s, 'prompt', %s, %s, %s, %s, %s::jsonb, %s::timestamptz)
       ON CONFLICT (client_id, project, source_id) WHERE source_id IS NOT NULL DO NOTHING
"""

_SQL_INSERT_TRANSACTION = """
    INSERT INTO mng_transactions
       (user_id, type, amount_usd, base_cost_usd, description, ref)
       VALUES (%s, %s, %s, %s, %s, %s)
"""

_SQL_GET_PROMPT_BY_SOURCE = """
    SELECT id::text FROM pr_prompts
    WHERE client_id=1 AND project=%s AND event_type='prompt' AND source_id=%s
    LIMIT 1
"""

_SQL_GET_SESSION_FEATURE = """
    SELECT feature FROM mng_session_tags WHERE client_id=1 AND project=%s
"""

_SQL_GET_ACTIVE_FEATURES = """
    SELECT t.name FROM pr_tags t
       JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
       WHERE t.client_id=1 AND t.project=%s AND tc.name='feature' AND t.status='active'
       ORDER BY t.name
"""

_SQL_UPSERT_SESSION_FEATURE = """
    INSERT INTO mng_session_tags (client_id, project, feature)
       VALUES (1, %s, %s)
       ON CONFLICT (client_id, project) DO UPDATE SET feature=%s, updated_at=NOW()
"""

_SQL_GET_WORKFLOW_BY_NAME = """
    SELECT id, name FROM pr_graph_workflows WHERE client_id=1 AND project=%s AND name=%s
"""

_SQL_GET_WORKFLOW_FUZZY = """
    SELECT id, name FROM pr_graph_workflows
    WHERE client_id=1 AND project=%s AND lower(name) LIKE %s
    LIMIT 1
"""

_SQL_INSERT_GRAPH_RUN = """
    INSERT INTO pr_graph_runs (id, client_id, project, workflow_id, status, user_input)
    VALUES (%s, 1, %s, %s, 'running', %s)
"""

_SQL_UPDATE_COMMIT_PHASE = """
    UPDATE pr_commits SET phase=%s
    WHERE client_id=1 AND project=%s AND session_id=%s
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
    """Write a completed exchange to the DB (pr_prompts + pr_events).

    DB is the primary store. JSONL files are no longer written here.
    Returns the ts string so callers can correlate the event.
    """
    if ts is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not db.is_available():
        return ts

    phase = (tags or {}).get("phase") or None
    meta  = json.dumps({"user": user_email or user_id, "source": "ui"})

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # pr_prompts — feeds memory distillation pipeline
                cur.execute(
                    _SQL_INSERT_INTERACTION,
                    (project, session_id, provider, ts,
                     (user_msg or "")[:4000], (response or "")[:8000],
                     phase, meta, ts),
                )
                # pr_events was removed — pr_prompts is the only log now.
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

        # Fire-and-forget: embed + auto-tag suggestions + proactive feature detection
        try:
            from memory.mem_embeddings import embed_and_store as _embed
            asyncio.create_task(_embed(
                project, "history", _ts, f"Q: {message}\nA: {content}",
                chunk_index=0, chunk_type="full",
                metadata={"provider": provider, "source": "ui"},
            ))
            # Auto-tag suggestions for the event we just created
            if db.is_available():
                from routers.route_entities import _auto_suggest_tags
                asyncio.create_task(_auto_suggest_tags_for_event(_ts, project, message))
                # Proactive feature auto-detection (first prompt in new session only)
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


async def _auto_suggest_tags_for_event(ts: str, project: str, user_msg: str) -> None:
    """Look up the prompt by source_id then apply session tags. Silent on error."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_PROMPT_BY_SOURCE, (project, ts))
                row = cur.fetchone()
        if row:
            from routers.route_entities import _auto_suggest_tags
            await _auto_suggest_tags(row[0], project, user_msg)
    except Exception:
        pass


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

        # Guard: skip if session already has a feature tag
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_SESSION_FEATURE, (project,))
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
                cur.execute(_SQL_GET_ACTIVE_FEATURES, (project,))
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
                cur.execute(_SQL_UPSERT_SESSION_FEATURE, (project, feature_name, feature_name))

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
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORKFLOW_BY_NAME, (project, pipeline_name))
                row = cur.fetchone()
        if not row:
            # Try partial/case-insensitive match
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WORKFLOW_FUZZY, (project, f"%{pipeline_name.lower()}%"))
                    row = cur.fetchone()
        if not row:
            return f"⚠ No pipeline named **{pipeline_name}** found. Check the Pipelines tab for available flows."

        workflow_id, workflow_name = str(row[0]), row[1]
        run_id = str(_uuid.uuid4())

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_GRAPH_RUN,
                    (run_id, project, workflow_id, f"/run {pipeline_name}"),
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
    phase: str | None = None
    feature: str | None = None
    context_tags: dict = {}   # {stage: "discovery", feature: "auth", ...} from .agent-context


class HookResponseRequest(BaseModel):
    ts: str                    # matches the ts from HookLogRequest
    session_id: str
    response: str
    stop_reason: str = "end_turn"


def _count_session_prompts(project: str, session_id: str) -> int:
    """Count how many prompts exist for this session (used for batch trigger)."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM pr_prompts "
                    "WHERE client_id=1 AND project=%s AND session_id=%s",
                    (project, session_id),
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
    """Generate a digest for the last N prompts in the session → pr_memory_events."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, prompt, response FROM pr_prompts
                       WHERE client_id=1 AND project=%s AND session_id=%s
                         AND response != ''
                       ORDER BY created_at DESC LIMIT %s""",
                    (project, session_id, n),
                )
                prompts = list(reversed(cur.fetchall()))
        if not prompts:
            return

        # Build prompt for Haiku
        pairs = "\n\n".join(
            f"Q: {(p[1] or '')[:500]}\nA: {(p[2] or '')[:800]}"
            for p in prompts
        )
        # Load system role
        sys_prompt = "Given N sequential prompt/response pairs, extract a 1-2 sentence digest capturing what was decided, built, or discovered. Return plain text only, no preamble."
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT content FROM mng_system_roles "
                        "WHERE client_id=1 AND name='memory_batch_digest' AND is_active=TRUE LIMIT 1"
                    )
                    row = cur.fetchone()
                    if row:
                        sys_prompt = row[0]
        except Exception:
            pass

        from data.dl_api_keys import get_key
        import anthropic
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=200,
            system=sys_prompt,
            messages=[{"role": "user", "content": pairs}],
        )
        content = (resp.content[0].text if resp.content else "").strip()
        if not content:
            return

        last_prompt_id = str(prompts[-1][0])
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO pr_memory_events
                           (client_id, project, source_type, source_id, session_id, content, importance)
                       VALUES (1, %s, 'prompt_batch', %s::uuid, %s, %s, 1)
                       ON CONFLICT (client_id, project, source_type, source_id) DO NOTHING
                       RETURNING id""",
                    (project, last_prompt_id, session_id, content),
                )
        log.debug(f"Memory batch digest generated for {project}/{session_id}")
    except Exception as e:
        log.debug(f"_generate_memory_batch error: {e}")


async def _tag_prompt_from_context(project: str, prompt_id: str, context_tags: dict) -> None:
    """Create pr_source_tags rows for each key:value in context_tags (auto_tagged=True)."""
    if not context_tags or not db.is_available():
        return
    try:
        from datetime import datetime as _dt, timezone as _tz
        with db.conn() as conn:
            with conn.cursor() as cur:
                for key, value in context_tags.items():
                    tag_name = f"{key}:{value}" if key not in ("feature", "bug_ref") else str(value)
                    # get_or_create tag
                    cur.execute(
                        "SELECT id FROM pr_tags WHERE client_id=1 AND project=%s AND name=%s",
                        (project, tag_name),
                    )
                    row = cur.fetchone()
                    if row:
                        tag_id = row[0]
                    else:
                        cur.execute(
                            "INSERT INTO pr_tags (client_id, project, name, status) "
                            "VALUES (1, %s, %s, 'active') "
                            "ON CONFLICT (client_id, project, name) DO NOTHING RETURNING id",
                            (project, tag_name),
                        )
                        ins = cur.fetchone()
                        if not ins:
                            cur.execute(
                                "SELECT id FROM pr_tags WHERE client_id=1 AND project=%s AND name=%s",
                                (project, tag_name),
                            )
                            ins = cur.fetchone()
                        if ins:
                            tag_id = ins[0]
                        else:
                            continue
                    # Insert source-tag link
                    cur.execute(
                        """INSERT INTO pr_source_tags (tag_id, prompt_id, auto_tagged)
                           VALUES (%s::uuid, %s::uuid, TRUE)
                           ON CONFLICT DO NOTHING""",
                        (tag_id, prompt_id),
                    )
    except Exception as e:
        log.debug(f"_tag_prompt_from_context error: {e}")


@router.post("/{project}/hook-log")
async def hook_log_prompt(project: str, body: HookLogRequest):
    """Unauthenticated endpoint — CLI hooks write prompts directly to pr_prompts.

    Called by log_user_prompt.sh after every Claude Code prompt.
    No auth required: runs on localhost, hook scripts have no JWT.
    Also triggers memory batch digest every N prompts.
    """
    ts = body.ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not db.is_available():
        return {"ok": False, "reason": "db_unavailable"}
    try:
        prompt_id = None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_INTERACTION,
                    (project, body.session_id, body.source, ts,
                     (body.prompt or "")[:4000], "",
                     body.phase,
                     json.dumps({"source": body.source, "provider": body.provider,
                                 "feature": body.feature,
                                 "context_tags": body.context_tags}),
                     ts),
                )
                # Fetch the inserted prompt id
                cur.execute(
                    "SELECT id FROM pr_prompts WHERE client_id=1 AND project=%s AND source_id=%s",
                    (project, ts),
                )
                row = cur.fetchone()
                if row:
                    prompt_id = str(row[0])

        # Fire memory batch digest every N prompts (fire-and-forget)
        count = _count_session_prompts(project, body.session_id)
        batch_size = _get_batch_size(project)
        if count > 0 and count % batch_size == 0:
            asyncio.create_task(_generate_memory_batch(project, body.session_id, batch_size))

        # Tag prompt with context_tags if provided
        if body.context_tags and prompt_id:
            asyncio.create_task(_tag_prompt_from_context(project, prompt_id, body.context_tags))

        return {"ok": True, "ts": ts}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


@router.post("/{project}/hook-response")
async def hook_update_response(project: str, body: HookResponseRequest):
    """Unauthenticated endpoint — CLI hooks update response text in pr_prompts.

    Called by log_session_stop.sh after Claude Code finishes responding.
    When ts is empty, finds the most recent empty-response row for the session.
    """
    if not db.is_available():
        return {"ok": False, "reason": "db_unavailable"}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                if body.ts:
                    cur.execute(
                        """UPDATE pr_prompts SET response = %s
                           WHERE client_id=1 AND project=%s
                             AND source_id = %s AND session_id = %s
                             AND (response IS NULL OR response = '')""",
                        ((body.response or "")[:8000], project, body.ts, body.session_id),
                    )
                else:
                    # Find latest empty-response row for this session
                    cur.execute(
                        """UPDATE pr_prompts SET response = %s
                           WHERE id = (
                               SELECT id FROM pr_prompts
                               WHERE client_id=1 AND project=%s
                                 AND session_id = %s
                                 AND (response IS NULL OR response = '')
                               ORDER BY created_at DESC LIMIT 1
                           )""",
                        ((body.response or "")[:8000], project, body.session_id),
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
        if db.is_available():
            asyncio.create_task(_auto_suggest_tags_for_event(_ts, project, req.message))

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


def _backfill_session_phase(project: str, session_id: str, phase: Optional[str]) -> None:
    """Retroactively set phase on all history.jsonl entries + DB rows for a session.

    Called whenever a session's phase tag is changed so that all prompts and commits
    linked to that session become filterable by the new phase.
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
                        entry["phase"] = phase
                    updated.append(json.dumps(entry, ensure_ascii=False))
                except Exception:
                    updated.append(line)
            hist_path.write_text("\n".join(updated) + "\n")
        except Exception:
            pass  # read-only filesystem or concurrent write — best-effort

    # 2. Update commits table phase (events table has no session_id column;
    #    history.jsonl is the source of truth for the History chat filter)
    if db.is_available():
        import logging as _log
        _logger = _log.getLogger(__name__)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_UPDATE_COMMIT_PHASE, (phase, project, session_id))
                    c_rows = cur.rowcount
            _logger.info(
                f"backfill_session_phase: project={project} session={session_id[:8]} "
                f"phase={phase!r} → commits={c_rows}"
            )
        except Exception as exc:
            _logger.warning(f"backfill_session_phase DB failed: {exc}")


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
        if body.phase is not None:
            _backfill_session_phase(p, session_id, body.phase or None)
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
    if body.phase is not None:
        _backfill_session_phase(p, session_id, body.phase or None)
    return {"ok": True, "tags": entry}
