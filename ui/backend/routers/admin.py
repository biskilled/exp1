"""
Admin router — user management (admin only).

GET    /admin/users              → list all users + usage summary
PATCH  /admin/users/{id}         → update is_admin / is_active
DELETE /admin/users/{id}         → soft-delete (sets is_active=False)
"""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from config import settings
from core.auth import get_current_user
from models.user import find_by_id, list_users, update_user, delete_user

router = APIRouter()


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    user = find_by_id(current_user["sub"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def _usage_summary(user_id: str) -> dict:
    """Read usage JSONL and aggregate — fast enough for < 100k lines."""
    path = Path(settings.data_dir) / "usage" / f"{user_id}.jsonl"
    if not path.exists():
        return {"total_calls": 0, "total_tokens": 0, "total_cost_usd": 0.0}
    total_calls = 0
    total_tokens = 0
    total_cost = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            total_calls += 1
            total_tokens += r.get("input_tokens", 0) + r.get("output_tokens", 0)
            total_cost += r.get("cost_usd", 0.0)
        except json.JSONDecodeError:
            pass
    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
    }


@router.get("/users")
async def list_all_users(_: dict = Depends(_require_admin)):
    """List all users with usage summary."""
    users = list_users()
    result = []
    for u in users:
        result.append({
            **u,
            "usage": _usage_summary(u["id"]),
        })
    return {"users": result, "total": len(result)}


class UserPatch(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None


@router.patch("/users/{user_id}")
async def patch_user(user_id: str, body: UserPatch, admin: dict = Depends(_require_admin)):
    """Update is_admin or is_active for a user."""
    fields = {}
    if body.is_admin is not None:
        fields["is_admin"] = body.is_admin
    if body.is_active is not None:
        fields["is_active"] = body.is_active
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = update_user(user_id, **fields)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, admin: dict = Depends(_require_admin)):
    """Soft-delete a user (sets is_active=False). Cannot delete yourself."""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    ok = delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": user_id}
