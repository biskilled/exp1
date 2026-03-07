"""
Admin router — user management, pricing, coupons, API keys (admin only).

GET    /admin/users              → list all users + usage + balance summary
PATCH  /admin/users/{id}         → update role, is_active, balance_added_usd (credit)
DELETE /admin/users/{id}         → soft-delete (sets is_active=False)

GET    /admin/pricing            → load pricing.json
PUT    /admin/pricing            → save pricing.json

GET    /admin/coupons            → list all coupons
POST   /admin/coupons            → create coupon
DELETE /admin/coupons/{code}     → delete coupon

GET    /admin/api-keys           → masked keys (last 4 chars)
PUT    /admin/api-keys           → save full keys
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from config import settings
from core.auth import get_current_user
from core.pricing import load_pricing, save_pricing
from core.api_keys import load_keys, save_keys, masked_keys
from models.user import find_by_id, list_users, update_user, delete_user

router = APIRouter()


# ── Admin guard ────────────────────────────────────────────────────────────────

def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    # dev_mode synthetic admin has id "dev-admin"
    if current_user.get("id") == "dev-admin" or current_user.get("sub") == "dev-admin":
        return current_user
    user_id = current_user.get("sub") or current_user.get("id", "")
    user = find_by_id(user_id)
    if not user or not (user.get("is_admin") or user.get("role") == "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


# ── Usage helpers ──────────────────────────────────────────────────────────────

def _usage_summary(user_id: str) -> dict:
    path = Path(settings.data_dir) / "usage" / f"{user_id}.jsonl"
    if not path.exists():
        return {"total_calls": 0, "total_tokens": 0, "total_cost_usd": 0.0}
    total_calls = total_tokens = 0
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
    return {"total_calls": total_calls, "total_tokens": total_tokens, "total_cost_usd": round(total_cost, 6)}


# ── Coupon helpers ─────────────────────────────────────────────────────────────

_AICLI_COUPON = {
    "code": "AICLI",
    "amount_usd": 10.0,
    "max_uses": 999,
    "used_count": 0,
    "used_by": [],
    "description": "Test coupon — $10 credit",
    "expires_at": None,
    "created_by": "system",
    "created_at": "2026-03-07T00:00:00Z",
}


def _coupons_path() -> Path:
    p = Path(settings.data_dir) / "coupons.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_coupons() -> list[dict]:
    path = _coupons_path()
    if not path.exists():
        coupons = [_AICLI_COUPON]
        _save_coupons(coupons)
        return coupons
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [_AICLI_COUPON]


def _save_coupons(coupons: list[dict]) -> None:
    _coupons_path().write_text(json.dumps(coupons, indent=2), encoding="utf-8")


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(_: dict = Depends(_require_admin)):
    """Aggregate totals across all users: balance, charged cost, real cost, margin."""
    users = list_users()
    total_added  = sum(u.get("balance_added_usd",  0.0) for u in users)
    total_charged = sum(u.get("balance_used_usd",  0.0) for u in users)

    # Scan all transaction files for usage_debit records.
    # Accumulate total real cost and per-provider breakdowns.
    total_real_cost = 0.0
    by_provider: dict[str, dict] = {}
    tx_dir = Path(settings.data_dir) / "transactions"
    if tx_dir.exists():
        for txf in tx_dir.glob("*.jsonl"):
            try:
                for line in txf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    if r.get("type") != "usage_debit":
                        continue
                    charged   = r.get("amount_usd", 0.0)
                    real_cost = r.get("base_cost_usd", charged)
                    total_real_cost += real_cost
                    # First word of description is the provider name
                    provider = (r.get("description") or "").split(" ")[0] or "unknown"
                    p = by_provider.setdefault(provider, {"charged_usd": 0.0, "real_cost_usd": 0.0, "calls": 0})
                    p["charged_usd"]   = round(p["charged_usd"]   + charged,   8)
                    p["real_cost_usd"] = round(p["real_cost_usd"] + real_cost, 8)
                    p["calls"]        += 1
            except Exception:
                pass

    return {
        "user_count":          len(users),
        "active_users":        sum(1 for u in users if u.get("is_active", True)),
        "total_balance_usd":   round(total_added - total_charged, 4),
        "total_added_usd":     round(total_added, 4),
        "total_charged_usd":   round(total_charged, 4),
        "total_real_cost_usd": round(total_real_cost, 4),
        "total_margin_usd":    round(total_charged - total_real_cost, 4),
        "by_provider":         by_provider,
    }


# ── Users ──────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_all_users(_: dict = Depends(_require_admin)):
    users = list_users()
    result = []
    for u in users:
        balance = round(u.get("balance_added_usd", 0.0) - u.get("balance_used_usd", 0.0), 6)
        result.append({
            **u,
            "balance_usd": balance,
            "usage": _usage_summary(u["id"]),
        })
    return {"users": result, "total": len(result)}


class UserPatch(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    credit_usd: float | None = None   # positive → adds to balance_added_usd


@router.patch("/users/{user_id}")
async def patch_user(user_id: str, body: UserPatch, admin: dict = Depends(_require_admin)):
    fields: dict = {}
    if body.role is not None:
        if body.role not in ("admin", "paid", "free"):
            raise HTTPException(status_code=400, detail="role must be admin, paid, or free")
        fields["role"] = body.role
        fields["is_admin"] = body.role == "admin"
    if body.is_active is not None:
        fields["is_active"] = body.is_active
    if body.credit_usd is not None:
        user = find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # Append transaction record
        from routers.chat import _append_transaction
        _append_transaction(user_id, "admin_credit", body.credit_usd,
                            f"Manual credit by admin", "admin")
        fields["balance_added_usd"] = round(user.get("balance_added_usd", 0.0) + body.credit_usd, 6)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    updated = update_user(user_id, **fields)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/users/{user_id}")
async def deactivate_user(user_id: str, admin: dict = Depends(_require_admin)):
    admin_id = admin.get("id") or admin.get("sub")
    if user_id == admin_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    ok = delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": user_id}


# ── Pricing ────────────────────────────────────────────────────────────────────

@router.get("/pricing")
async def get_pricing(_: dict = Depends(_require_admin)):
    return load_pricing()


@router.put("/pricing")
async def put_pricing(body: dict, _: dict = Depends(_require_admin)):
    save_pricing(body)
    return {"ok": True}


# ── Coupons ────────────────────────────────────────────────────────────────────

@router.get("/coupons")
async def list_coupons(_: dict = Depends(_require_admin)):
    return {"coupons": _load_coupons()}


class CouponCreate(BaseModel):
    code: str
    amount_usd: float
    max_uses: int = 1
    description: str = ""
    expires_at: str | None = None


@router.post("/coupons")
async def create_coupon(body: CouponCreate, admin: dict = Depends(_require_admin)):
    coupons = _load_coupons()
    code = body.code.upper().strip()
    if any(c["code"] == code for c in coupons):
        raise HTTPException(status_code=400, detail=f"Coupon code '{code}' already exists")
    admin_email = admin.get("email", "admin")
    coupon = {
        "code": code,
        "amount_usd": body.amount_usd,
        "max_uses": body.max_uses,
        "used_count": 0,
        "used_by": [],
        "description": body.description,
        "expires_at": body.expires_at,
        "created_by": admin_email,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    coupons.append(coupon)
    _save_coupons(coupons)
    return coupon


@router.delete("/coupons/{code}")
async def delete_coupon(code: str, _: dict = Depends(_require_admin)):
    coupons = _load_coupons()
    code = code.upper().strip()
    new_list = [c for c in coupons if c["code"] != code]
    if len(new_list) == len(coupons):
        raise HTTPException(status_code=404, detail=f"Coupon '{code}' not found")
    _save_coupons(new_list)
    return {"deleted": code}


# ── API Keys ───────────────────────────────────────────────────────────────────

@router.get("/api-keys")
async def get_api_keys(_: dict = Depends(_require_admin)):
    """Return masked keys (last 4 chars visible)."""
    return masked_keys()


@router.put("/api-keys")
async def put_api_keys(body: dict, _: dict = Depends(_require_admin)):
    """Save full API keys (only non-empty values are written)."""
    current = load_keys()
    for provider, key in body.items():
        if key is not None:
            current[provider] = str(key).strip()
    save_keys(current)
    return {"ok": True, "keys": masked_keys()}


# ── Live API Balances ───────────────────────────────────────────────────────────

@router.get("/api-balances")
async def get_api_balances(_: dict = Depends(_require_admin)):
    """Return live balance from each provider's API (where supported)."""
    from core.api_balances import get_all_balances
    return await get_all_balances()


# ── Usage Table (daily aggregated) ─────────────────────────────────────────────

@router.get("/usage-table")
async def get_usage_table(_: dict = Depends(_require_admin)):
    """
    Daily aggregated usage table — grain: (date, user_id, provider).

    Aggregates usage/{user_id}.jsonl (tokens/cost) and
    transactions/{user_id}.jsonl (revenue, topups) into one table.
    Also returns 'system_rows' with live API balances per provider.
    """
    from core.api_balances import get_all_balances

    users     = list_users()
    user_map  = {u["id"]: u for u in users}

    # (date, user_id, provider) → running totals
    rows: dict[tuple, dict] = {}

    def _row(date: str, user_id: str, provider: str) -> dict:
        key = (date, user_id, provider)
        if key not in rows:
            rows[key] = {
                "date":           date,
                "user_id":        user_id,
                "provider":       provider,
                "tokens_input":   0,
                "tokens_output":  0,
                "cost":           0.0,    # real LLM cost (no markup)
                "revenue":        0.0,    # charged to user (with markup)
            }
        return rows[key]

    # (date, user_id) → topup buckets (shared across all provider rows that day)
    topups: dict[tuple, dict] = {}

    def _topup(date: str, user_id: str) -> dict:
        key = (date, user_id)
        if key not in topups:
            topups[key] = {"cash": 0.0, "cash_cnt": 0, "coupon": 0.0, "coupon_cnt": 0}
        return topups[key]

    usage_dir = Path(settings.data_dir) / "usage"
    tx_dir    = Path(settings.data_dir) / "transactions"

    # Pass 1 — usage files: tokens + real cost
    if usage_dir.exists():
        for uf in usage_dir.glob("*.jsonl"):
            uid = uf.stem
            for line in uf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    r        = json.loads(line)
                    date     = r["ts"][:10]
                    provider = r.get("provider", "unknown")
                    row      = _row(date, uid, provider)
                    row["tokens_input"]  += r.get("input_tokens", 0)
                    row["tokens_output"] += r.get("output_tokens", 0)
                    row["cost"]           = round(row["cost"] + r.get("cost_usd", 0.0), 8)
                except Exception:
                    pass

    # Pass 2 — transaction files: revenue + topups
    if tx_dir.exists():
        for tf in tx_dir.glob("*.jsonl"):
            uid = tf.stem
            for line in tf.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    r        = json.loads(line)
                    date     = r["ts"][:10]
                    tx_type  = r.get("type", "")
                    amount   = r.get("amount_usd", 0.0)

                    if tx_type == "usage_debit":
                        # First word of description = provider
                        desc     = r.get("description", "")
                        provider = desc.split(" ")[0] if desc else "unknown"
                        real     = r.get("base_cost_usd", amount)
                        row      = _row(date, uid, provider)
                        row["revenue"] = round(row["revenue"] + amount, 8)
                        # Back-fill cost from tx if usage file had nothing
                        if row["cost"] == 0.0:
                            row["cost"] = round(row["cost"] + real, 8)

                    elif tx_type == "coupon_credit":
                        t = _topup(date, uid)
                        t["coupon"]     = round(t["coupon"] + amount, 6)
                        t["coupon_cnt"] += 1

                    elif tx_type in ("admin_credit", "stripe_payment"):
                        t = _topup(date, uid)
                        t["cash"]     = round(t["cash"] + amount, 6)
                        t["cash_cnt"] += 1

                except Exception:
                    pass

    # Build sorted result rows
    mk = masked_keys()
    result = []
    for (date, uid, provider), row in sorted(rows.items()):
        user    = user_map.get(uid, {})
        balance = round(
            user.get("balance_added_usd", 0.0) - user.get("balance_used_usd", 0.0), 4
        )
        tp      = topups.get((date, uid), {})
        ki      = mk.get(provider, {})
        result.append({
            "date":             date,
            "user_id":          uid,
            "email":            user.get("email", uid),
            "llm":              provider,
            "api_key_masked":   ki.get("masked", ""),
            "tokens":           row["tokens_input"] + row["tokens_output"],
            "tokens_input":     row["tokens_input"],
            "tokens_output":    row["tokens_output"],
            "cost":             round(row["cost"], 6),
            "revenue":          round(row["revenue"], 6),
            "margin":           round(row["revenue"] - row["cost"], 6),
            "balance":          balance,
            "topup_cash":       tp.get("cash", 0.0),
            "topup_cash_cnt":   tp.get("cash_cnt", 0),
            "topup_coupon":     tp.get("coupon", 0.0),
            "topup_coupon_cnt": tp.get("coupon_cnt", 0),
        })

    # System rows — one per provider with live API balance
    api_balances = await get_all_balances()
    system_rows  = []
    for provider, bal in api_balances.items():
        ki = mk.get(provider, {})
        system_rows.append({
            "provider":       provider,
            "api_key_masked": ki.get("masked", ""),
            "api_balance":    bal,
        })

    return {"rows": result, "system_rows": system_rows}
