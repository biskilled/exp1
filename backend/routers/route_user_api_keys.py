"""
Per-user API key management.

Users can store their own provider keys; these take priority over server keys.
Keys are Fernet-encrypted in mng_user_api_keys — never stored in plain text.

GET    /user/api-keys              → list user's saved providers (masked)
PUT    /user/api-keys/{provider}   → save or update a key
DELETE /user/api-keys/{provider}   → remove a key
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user
from data.dl_api_keys import list_user_keys, save_user_key, delete_user_key

router = APIRouter()

_PROVIDERS = ("claude", "openai", "deepseek", "gemini", "grok")


class KeyBody(BaseModel):
    key: str


@router.get("")
async def get_user_api_keys(current_user: dict = Depends(get_current_user)):
    """Return masked key status for all providers the user has saved."""
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id == "dev-admin":
        return {"keys": []}
    return {"keys": list_user_keys(user_id)}


@router.put("/{provider}")
async def put_user_api_key(
    provider: str,
    body: KeyBody,
    current_user: dict = Depends(get_current_user),
):
    """Save or update the user's API key for a provider."""
    if provider not in _PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'")
    if not body.key.strip():
        raise HTTPException(status_code=400, detail="Key must not be empty")

    user_id = current_user.get("sub") or current_user.get("id")
    if user_id == "dev-admin":
        return {"ok": True, "message": "Dev admin — key not saved"}

    save_user_key(user_id, provider, body.key)
    return {"ok": True, "provider": provider, "message": f"{provider} key saved"}


@router.delete("/{provider}")
async def delete_user_api_key(
    provider: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove the user's saved key for a provider (falls back to server key)."""
    user_id = current_user.get("sub") or current_user.get("id")
    deleted = delete_user_key(user_id, provider)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No saved key for '{provider}'")
    return {"ok": True, "provider": provider}
