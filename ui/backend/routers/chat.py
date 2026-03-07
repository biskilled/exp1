"""
Chat router with SSE streaming support.

Server mode: API keys are stored server-side (api_keys.json) — no client X-*-Key headers.
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

from config import settings
from core.auth import get_optional_user
from core.api_keys import get_key
from core.pricing import load_pricing, calculate_cost, can_user_access
from core.llm_clients import call_claude, call_deepseek, call_gemini, call_grok
from routers.usage import log_usage
from storage.sessions import SessionStore

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    provider: str = "claude"
    system: str = ""
    stream: bool = True


def _get_store() -> SessionStore:
    return SessionStore(
        workspace_dir=Path(settings.workspace_dir),
        project=settings.active_project or "default",
    )


def _append_history(project: str, provider: str, user_msg: str, response: str, session_id: str, user_id: Optional[str] = None, user_email: Optional[str] = None) -> None:
    """Append a completed exchange to workspace/{project}/_system/history.jsonl."""
    try:
        sys_dir = Path(settings.workspace_dir) / project / "_system"
        sys_dir.mkdir(parents=True, exist_ok=True)
        path = sys_dir / "history.jsonl"
        entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "ui",
            "session_id": session_id,
            "provider": provider,
            "user_input": user_msg,
            "output": response,
            "user": user_email or user_id or None,
            "feature": None,
            "tags": [],
        }
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never break chat because of logging


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


def _append_transaction(user_id: str, tx_type: str, amount_usd: float, description: str, ref: str = "") -> None:
    """Append a transaction record to transactions/{user_id}.jsonl."""
    try:
        tx_dir = Path(settings.data_dir) / "transactions"
        tx_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": tx_type,
            "amount_usd": amount_usd,
            "description": description,
            "ref": ref,
        }
        with open(tx_dir / f"{user_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


async def _call_provider(provider: str, message: str, system: str) -> dict:
    """Dispatch to the right LLM client using server-side keys."""
    api_key = get_key(provider)
    if provider == "claude":
        return await call_claude([{"role": "user", "content": message}], system=system, api_key=api_key or None)
    elif provider == "deepseek":
        return await call_deepseek([{"role": "user", "content": message}], system=system, api_key=api_key or None)
    elif provider == "gemini":
        return await call_gemini(message, system=system, api_key=api_key or None)
    elif provider == "grok":
        return await call_grok([{"role": "user", "content": message}], system=system, api_key=api_key or None)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


def _debit_user(user_id: str, provider: str, model: str, input_tokens: int, output_tokens: int) -> None:
    """Deduct usage cost from user balance and append transaction."""
    try:
        from models.user import find_by_id, update_user
        pricing = load_pricing()
        markup = pricing.get("providers", {}).get(provider, {}).get("markup_percent", 0)
        cost = calculate_cost(provider, model, input_tokens, output_tokens, markup)
        if cost <= 0:
            return
        user = find_by_id(user_id)
        if not user:
            return
        new_used = round(user.get("balance_used_usd", 0.0) + cost, 8)
        update_user(user_id, balance_used_usd=new_used)
        _append_transaction(user_id, "usage_debit", cost, f"{provider} {model} {input_tokens}+{output_tokens} tokens")
    except Exception:
        pass  # never block chat because of billing


async def _stream_response(
    message: str, provider: str, system: str,
    user_id: Optional[str], user: Optional[dict], model_used: Optional[str],
    store: SessionStore, session_id: str,
):
    """Generate SSE events from LLM response, save assistant reply, log usage."""
    try:
        result = await _call_provider(provider, message, system)
        content = result.get("content", "")
        actual_model = result.get("model", provider)

        # Stream in chunks
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            yield f"data: {content[i:i + chunk_size]}\n\n"
            await asyncio.sleep(0.01)
        yield "data: [DONE]\n\n"

        # Persist assistant reply
        store.append_message(session_id, "assistant", content)

        # Append to shared project history
        project = settings.active_project or "default"
        user_email = user.get("email") if user else None
        _append_history(project, provider, message, content, session_id, user_id, user_email)
        _update_runtime_state(project, provider, message, session_id, user_id)

        # Log usage + debit balance
        input_t = result.get("input_tokens", 0)
        output_t = result.get("output_tokens", 0)
        if user_id and user_id != "dev-admin":
            log_usage(user_id=user_id, provider=provider, model=actual_model,
                      input_tokens=input_t, output_tokens=output_t)
            _debit_user(user_id, provider, actual_model, input_t, output_t)

    except Exception as e:
        yield f"data: [ERROR] {e}\n\n"


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """SSE streaming chat endpoint."""
    # Balance / access check
    if current_user and current_user.get("id") != "dev-admin":
        from models.user import find_by_id
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
        session = store.create()
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    user_id = current_user.get("sub") or current_user.get("id") if current_user else None

    return StreamingResponse(
        _stream_response(req.message, req.provider, req.system, user_id, full_user, None, store, session_id),
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
        from models.user import find_by_id
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
        session = store.create()
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    try:
        result = await _call_provider(req.provider, req.message, req.system)
        content = result.get("content", "")
        actual_model = result.get("model", req.provider)
        store.append_message(session_id, "assistant", content)

        user_id = current_user.get("sub") or current_user.get("id") if current_user else None

        # Append to shared project history
        project = settings.active_project or "default"
        user_email = full_user.get("email") if full_user else None
        _append_history(project, req.provider, req.message, content, session_id, user_id, user_email)
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
