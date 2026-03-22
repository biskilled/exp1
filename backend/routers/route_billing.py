"""
Billing router — per-user balance, coupons, transaction history.

GET  /billing/balance        → current balance + tier info
POST /billing/apply-coupon   → apply a coupon code to user account
GET  /billing/history        → last 50 transactions
POST /billing/add-payment    → placeholder (Stripe not yet integrated)
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user
from core.database import db
from agents.providers.pr_pricing import load_pricing
from data.dl_user import find_by_id, update_user

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_INSERT_TRANSACTION = """
    INSERT INTO mng_transactions (user_id, type, amount_usd, description, ref)
    VALUES (%s, %s, %s, %s, %s)
"""

# LIMIT 50 is intentional for the UI history view.
# TODO: parameterise LIMIT if server-side pagination is needed in future.
_SQL_LIST_TRANSACTIONS = """
    SELECT type, amount_usd, description, ref, created_at
    FROM mng_transactions WHERE user_id=%s
    ORDER BY created_at DESC LIMIT 50
"""

_SQL_GET_COUPON = """
    SELECT code,amount_usd,max_uses,used_count,used_by,expires_at
    FROM mng_coupons WHERE client_id=1 AND code=%s
"""

_SQL_UPDATE_COUPON_USED = """
    UPDATE mng_coupons
    SET used_count = used_count + 1,
        used_by    = used_by || %s::jsonb
    WHERE client_id=1 AND code=%s
"""

# ── Router definition ─────────────────────────────────────────────────────────

router = APIRouter()


# ── Transaction helpers ────────────────────────────────────────────────────────

def _append_transaction(user_id: str, tx_type: str, amount_usd: float, description: str, ref: str = "") -> None:
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_TRANSACTION,
                    (user_id, tx_type, amount_usd, description, ref),
                )
    except Exception:
        pass


def _load_transactions(user_id: str) -> list[dict]:
    if not db.is_available():
        return []
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_LIST_TRANSACTIONS, (user_id,))
                return [
                    {
                        "type":        r[0],
                        "amount_usd":  float(r[1]),
                        "description": r[2],
                        "ref":         r[3],
                        "ts":          r[4].isoformat() if r[4] else None,
                    }
                    for r in cur.fetchall()
                ]
    except Exception:
        return []


# ── Coupon helpers ─────────────────────────────────────────────────────────────

def _get_coupon(code: str) -> dict | None:
    if not db.is_available():
        return None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_COUPON, (code,))
                r = cur.fetchone()
                if not r:
                    return None
                return {
                    "code":       r[0],
                    "amount_usd": float(r[1]),
                    "max_uses":   r[2],
                    "used_count": r[3],
                    "used_by":    r[4] or [],
                    "expires_at": r[5].isoformat() if r[5] else None,
                }
    except Exception:
        return None


def _mark_coupon_used(code: str, user_id: str) -> None:
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPDATE_COUPON_USED,
                    (f'["{user_id}"]', code),
                )
    except Exception:
        pass


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/balance")
async def get_balance(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("sub") or current_user.get("id")
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
    coupon = _get_coupon(code)
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon code '{code}' not found")

    if user_id in (coupon.get("used_by") or []):
        raise HTTPException(status_code=400, detail="You have already used this coupon")

    if coupon.get("max_uses") and coupon.get("used_count", 0) >= coupon["max_uses"]:
        raise HTTPException(status_code=400, detail="Coupon has reached its maximum uses")

    expires_at = coupon.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                raise HTTPException(status_code=400, detail="Coupon has expired")
        except (ValueError, AttributeError):
            pass

    amount = coupon["amount_usd"]
    new_added = round(user.get("balance_added_usd", 0.0) + amount, 6)
    coupons_used = list(user.get("coupons_used") or []) + [code]
    update_user(user_id, balance_added_usd=new_added, coupons_used=coupons_used)
    _mark_coupon_used(code, user_id)
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
    return {"transactions": records, "total": len(records)}


@router.post("/add-payment")
async def add_payment(_: dict = Depends(get_current_user)):
    return {
        "status": "coming_soon",
        "message": "Stripe integration coming soon. Contact admin to add credit.",
    }
