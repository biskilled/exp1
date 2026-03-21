"""
Billing router — per-user balance, coupons, transaction history.

GET  /billing/balance        → current balance + tier info
POST /billing/apply-coupon   → apply a coupon code to user account
GET  /billing/history        → last 50 transactions
POST /billing/add-payment    → placeholder (Stripe not yet integrated)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import settings
from core.auth import get_current_user
from core.pricing import load_pricing
from models.user import find_by_id, update_user

router = APIRouter()


# ── Transaction helpers ────────────────────────────────────────────────────────

def _tx_path(user_id: str) -> Path:
    p = Path(settings.data_dir) / "transactions" / f"{user_id}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_transactions(user_id: str) -> list[dict]:
    path = _tx_path(user_id)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _append_transaction(user_id: str, tx_type: str, amount_usd: float, description: str, ref: str = "") -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": tx_type,
        "amount_usd": amount_usd,
        "description": description,
        "ref": ref,
    }
    with open(_tx_path(user_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# ── Coupon helpers ─────────────────────────────────────────────────────────────

def _coupons_path() -> Path:
    return Path(settings.data_dir) / "coupons.json"


def _load_coupons() -> list[dict]:
    path = _coupons_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_coupons(coupons: list[dict]) -> None:
    _coupons_path().write_text(json.dumps(coupons, indent=2), encoding="utf-8")


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub") or current_user.get("id")
    # dev admin — synthetic response
    if user_id == "dev-admin":
        return {
            "role": "admin",
            "balance_added_usd": 999.0,
            "balance_used_usd": 0.0,
            "balance_usd": 999.0,
            "free_tier_limit_usd": None,
            "free_tier_used_usd": None,
        }
    user = find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pricing = load_pricing()
    role = user.get("role", "free")
    balance_added = user.get("balance_added_usd", 0.0)
    balance_used = user.get("balance_used_usd", 0.0)
    balance = round(balance_added - balance_used, 6)

    result: dict = {
        "role": role,
        "balance_added_usd": balance_added,
        "balance_used_usd": balance_used,
        "balance_usd": balance,
        "free_tier_limit_usd": None,
        "free_tier_used_usd": None,
    }

    if role == "free":
        result["free_tier_limit_usd"] = pricing.get("free_tier_limit_usd", 5.0)
        result["free_tier_used_usd"] = balance_used
        result["free_tier_models"] = pricing.get("free_tier_models", [])

    return result


class CouponBody(BaseModel):
    code: str


@router.post("/apply-coupon")
async def apply_coupon(body: CouponBody, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id == "dev-admin":
        return {"ok": True, "message": "Dev admin — coupon not applied to synthetic account"}

    user = find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    code = body.code.upper().strip()
    coupons = _load_coupons()
    coupon = next((c for c in coupons if c["code"] == code), None)
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon code '{code}' not found")

    # Already used by this user?
    if user_id in (coupon.get("used_by") or []):
        raise HTTPException(status_code=400, detail="You have already used this coupon")

    # Max uses reached?
    if coupon.get("max_uses") and coupon.get("used_count", 0) >= coupon["max_uses"]:
        raise HTTPException(status_code=400, detail="Coupon has reached its maximum uses")

    # Expired?
    expires_at = coupon.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                raise HTTPException(status_code=400, detail="Coupon has expired")
        except (ValueError, AttributeError):
            pass

    amount = coupon["amount_usd"]

    # Credit user
    new_added = round(user.get("balance_added_usd", 0.0) + amount, 6)
    coupons_used = user.get("coupons_used") or []
    coupons_used = list(coupons_used) + [code]
    update_user(user_id, balance_added_usd=new_added, coupons_used=coupons_used)

    # Update coupon usage
    coupon["used_count"] = coupon.get("used_count", 0) + 1
    used_by = list(coupon.get("used_by") or [])
    used_by.append(user_id)
    coupon["used_by"] = used_by
    _save_coupons(coupons)

    # Append transaction
    _append_transaction(user_id, "coupon_credit", amount, f"Coupon {code}", code)

    return {
        "ok": True,
        "amount_usd": amount,
        "new_balance_usd": round(new_added - user.get("balance_used_usd", 0.0), 6),
        "message": f"${amount:.2f} credit applied successfully",
    }


@router.get("/history")
async def billing_history(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub") or current_user.get("id")
    if user_id == "dev-admin":
        return {"transactions": [], "total": 0}
    records = _load_transactions(user_id)
    return {"transactions": records[-50:], "total": len(records)}


@router.post("/add-payment")
async def add_payment(_: dict = Depends(get_current_user)):
    return {
        "status": "coming_soon",
        "message": "Stripe integration coming soon. Contact admin to add credit.",
    }
