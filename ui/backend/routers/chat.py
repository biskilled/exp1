"""
Chat router with SSE streaming support.

Cloud mode: clients send their own API keys in request headers:
  X-Anthropic-Key, X-OpenAI-Key, X-DeepSeek-Key, X-Gemini-Key, X-Grok-Key

When REQUIRE_AUTH=True, a valid Bearer token is also required.
Usage (token counts + cost) is logged per user after each call.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from core.auth import get_optional_user
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


def _extract_keys(
    x_anthropic_key: Optional[str] = Header(None),
    x_openai_key: Optional[str] = Header(None),
    x_deepseek_key: Optional[str] = Header(None),
    x_gemini_key: Optional[str] = Header(None),
    x_grok_key: Optional[str] = Header(None),
) -> dict[str, Optional[str]]:
    return {
        "claude":   x_anthropic_key,
        "openai":   x_openai_key,
        "deepseek": x_deepseek_key,
        "gemini":   x_gemini_key,
        "grok":     x_grok_key,
    }


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


async def _call_provider(provider: str, message: str, system: str, api_keys: dict) -> dict:
    """Dispatch to the right LLM client and return the result dict."""
    key = api_keys.get(provider)
    if provider == "claude":
        return await call_claude([{"role": "user", "content": message}], system=system, api_key=key)
    elif provider == "deepseek":
        return await call_deepseek([{"role": "user", "content": message}], system=system, api_key=key)
    elif provider == "gemini":
        return await call_gemini(message, system=system, api_key=key)
    elif provider == "grok":
        return await call_grok([{"role": "user", "content": message}], system=system, api_key=key)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


async def _stream_response(
    message: str, provider: str, system: str, api_keys: dict,
    user_id: Optional[str], store: SessionStore, session_id: str,
):
    """Generate SSE events from LLM response, save assistant reply, log usage."""
    try:
        result = await _call_provider(provider, message, system, api_keys)
        content = result.get("content", "")

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
        _append_history(project, provider, message, content, session_id, user_id)
        _update_runtime_state(project, provider, message, session_id, user_id)

        # Log usage
        if user_id:
            log_usage(
                user_id=user_id,
                provider=provider,
                model=result.get("model", provider),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
            )

    except Exception as e:
        yield f"data: [ERROR] {e}\n\n"


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    api_keys: dict = Depends(_extract_keys),
):
    """SSE streaming chat endpoint."""
    store = _get_store()
    session_id = req.session_id or str(uuid.uuid4())

    session = store.get(session_id)
    if session is None:
        session = store.create()
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    user_id = current_user["sub"] if current_user else None

    return StreamingResponse(
        _stream_response(req.message, req.provider, req.system, api_keys, user_id, store, session_id),
        media_type="text/event-stream",
        headers={"X-Session-Id": session_id},
    )


@router.post("/")
async def chat(
    req: ChatRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
    api_keys: dict = Depends(_extract_keys),
):
    """Non-streaming chat endpoint."""
    store = _get_store()
    session_id = req.session_id or str(uuid.uuid4())

    session = store.get(session_id)
    if session is None:
        session = store.create()
        session_id = session["id"]

    store.append_message(session_id, "user", req.message)

    try:
        result = await _call_provider(req.provider, req.message, req.system, api_keys)
        content = result.get("content", "")
        store.append_message(session_id, "assistant", content)

        user_id = current_user["sub"] if current_user else None

        # Append to shared project history
        project = settings.active_project or "default"
        _append_history(project, req.provider, req.message, content, session_id, user_id)
        _update_runtime_state(project, req.provider, req.message, session_id, user_id)

        # Log usage
        if user_id:
            log_usage(
                user_id=user_id,
                provider=req.provider,
                model=result.get("model", req.provider),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
            )

        return {
            "response": content,
            "provider": req.provider,
            "session_id": session_id,
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
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
