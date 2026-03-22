"""
Admin router — user management, pricing, coupons, API keys, billing (admin only).

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

GET    /admin/provider-costs              → load provider_costs.json
PUT    /admin/provider-costs              → save provider_costs.json
POST   /admin/fetch-provider-usage        → fetch real usage from provider API
GET    /admin/provider-usage-history      → last N fetch results
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.auth import get_current_user
from core.database import db
from agents.providers.pr_pricing import load_pricing, save_pricing
from data.dl_api_keys import masked_keys, save_server_key
from data.dl_user import find_by_id, list_users, update_user, delete_user

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_USAGE_SUMMARY_PER_USER = """
    SELECT COUNT(*), COALESCE(SUM(input_tokens+output_tokens),0),
           COALESCE(SUM(cost_usd),0)
    FROM mng_usage_logs WHERE user_id=%s AND source='request'
"""

_SQL_LIST_COUPONS = (
    "SELECT code,amount_usd,max_uses,used_count,used_by,description,"
    "expires_at,created_by,created_at FROM mng_coupons WHERE client_id=1"
)

_SQL_INSERT_COUPON_SEED = """
    INSERT INTO mng_coupons
       (client_id,code,amount_usd,max_uses,description,created_by,created_at)
       VALUES (1,'AICLI',10.0,999,'Test coupon — $10 credit','system',NOW())
       ON CONFLICT DO NOTHING
"""

_SQL_INSERT_COUPON = """
    INSERT INTO mng_coupons
       (client_id,code,amount_usd,max_uses,description,expires_at,created_by)
       VALUES (1,%s,%s,%s,%s,%s,%s)
       RETURNING code,amount_usd,max_uses,used_count,used_by,
                 description,expires_at,created_by,created_at
"""

_SQL_DELETE_COUPON = "DELETE FROM mng_coupons WHERE client_id=1 AND code=%s"

_SQL_PROVIDER_MARGINS = """
    SELECT
        SPLIT_PART(description, ' ', 1) AS provider,
        SUM(amount_usd)::float           AS charged,
        SUM(COALESCE(base_cost_usd, amount_usd))::float AS real_cost,
        COUNT(*)::int                    AS calls
    FROM mng_transactions
    WHERE type = 'usage_debit'
    GROUP BY SPLIT_PART(description, ' ', 1)
"""

# Grain: (date, user_id, provider) — source filter omitted intentionally here
# because this query backs the usage-table endpoint which shows all records.
_SQL_USAGE_BY_DATE = """
    SELECT
        DATE(created_at)::text        AS date,
        user_id,
        COALESCE(provider, 'unknown') AS provider,
        SUM(input_tokens)::int        AS tokens_input,
        SUM(output_tokens)::int       AS tokens_output,
        SUM(cost_usd)::float          AS cost,
        SUM(charged_usd)::float       AS revenue
    FROM mng_usage_logs
    WHERE user_id IS NOT NULL
      AND source='request'
    GROUP BY DATE(created_at), user_id, provider
    ORDER BY DATE(created_at) DESC, user_id, provider
"""

_SQL_TRANSACTIONS_BY_DATE = """
    SELECT
        DATE(created_at)::text AS date,
        user_id,
        type,
        SUM(amount_usd)::float AS total_amount,
        COUNT(*)::int          AS cnt
    FROM mng_transactions
    WHERE type IN ('coupon_credit', 'admin_credit', 'stripe_payment')
      AND user_id IS NOT NULL
    GROUP BY DATE(created_at), user_id, type
"""

_SQL_MIGRATE_CHECK_TABLE = (
    "SELECT 1 FROM information_schema.tables "
    "WHERE table_schema='public' AND table_name=%s"
)

_SQL_INSERT_CATEGORY = """
    INSERT INTO mng_entity_categories (client_id, name, color, icon)
    VALUES (1, %s, %s, %s)
    ON CONFLICT (client_id, name) DO NOTHING
    RETURNING id
"""

_SQL_UPSERT_ENTITY_VALUE = """
    INSERT INTO mng_entity_values
        (client_id, category_id, name, description, lifecycle_status, created_at)
    VALUES (1, %s, %s, %s, 'active', NOW())
    ON CONFLICT (client_id, category_id, name) DO UPDATE
        SET description = EXCLUDED.description
    RETURNING id
"""

# ── Router definition ─────────────────────────────────────────────────────────

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
    """Aggregate usage stats for a user from mng_usage_logs."""
    if not db.is_available():
        return {"total_calls": 0, "total_tokens": 0, "total_cost_usd": 0.0}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_USAGE_SUMMARY_PER_USER, (user_id,))
                row = cur.fetchone()
                return {
                    "total_calls":    int(row[0]) if row else 0,
                    "total_tokens":   int(row[1]) if row else 0,
                    "total_cost_usd": round(float(row[2]), 6) if row else 0.0,
                }
    except Exception:
        return {"total_calls": 0, "total_tokens": 0, "total_cost_usd": 0.0}


# ── Coupon helpers ─────────────────────────────────────────────────────────────

def _load_coupons() -> list[dict]:
    """Load all coupons from mng_coupons, seeding the default AICLI coupon if empty."""
    if not db.is_available():
        return []
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_LIST_COUPONS)
                rows = cur.fetchall()
                if not rows:
                    # Seed default coupon
                    cur.execute(_SQL_INSERT_COUPON_SEED)
                    return _load_coupons()
                return [
                    {
                        "code":        r[0],
                        "amount_usd":  float(r[1]),
                        "max_uses":    r[2],
                        "used_count":  r[3],
                        "used_by":     r[4] or [],
                        "description": r[5],
                        "expires_at":  r[6].isoformat() if r[6] else None,
                        "created_by":  r[7],
                        "created_at":  r[8].isoformat() if r[8] else None,
                    }
                    for r in rows
                ]
    except Exception:
        return []


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(_: dict = Depends(_require_admin)):
    """Aggregate totals across all users: balance, charged cost, real cost, margin."""
    users         = list_users()
    total_added   = sum(u.get("balance_added_usd", 0.0) for u in users)
    total_charged = sum(u.get("balance_used_usd",  0.0) for u in users)

    total_real_cost = 0.0
    by_provider: dict[str, dict] = {}

    if db.is_available():
        # Read from PostgreSQL transactions table
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_PROVIDER_MARGINS)
                    for row in cur.fetchall():
                        prov, charged, real_cost, calls = row
                        prov = prov or "unknown"
                        total_real_cost += real_cost or 0.0
                        by_provider[prov] = {
                            "charged_usd":   round(float(charged   or 0), 8),
                            "real_cost_usd": round(float(real_cost or 0), 8),
                            "calls":         calls,
                        }
        except Exception:
            pass
    else:
        # Scan JSONL transaction files
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
        from routers.route_chat import _append_transaction
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
    code = body.code.upper().strip()
    admin_email = admin.get("email", "admin")
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_INSERT_COUPON,
                    (code, body.amount_usd, body.max_uses, body.description,
                     body.expires_at, admin_email),
                )
                r = cur.fetchone()
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Coupon code '{code}' already exists")
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "code": r[0], "amount_usd": float(r[1]), "max_uses": r[2],
        "used_count": r[3], "used_by": r[4] or [], "description": r[5],
        "expires_at": r[6].isoformat() if r[6] else None,
        "created_by": r[7], "created_at": r[8].isoformat() if r[8] else None,
    }


@router.delete("/coupons/{code}")
async def delete_coupon(code: str, _: dict = Depends(_require_admin)):
    code = code.upper().strip()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_COUPON, (code,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"Coupon '{code}' not found")
    return {"deleted": code}


# ── API Keys ───────────────────────────────────────────────────────────────────

@router.get("/api-keys")
async def get_api_keys(_: dict = Depends(_require_admin)):
    """Return masked keys (last 4 chars visible)."""
    return masked_keys()


@router.put("/api-keys")
async def put_api_keys(body: dict, _: dict = Depends(_require_admin)):
    """Save server-level API keys (encrypted in DB). Only non-empty values are written."""
    for provider, key in body.items():
        if key is not None:
            save_server_key(provider, str(key))
    return {"ok": True, "keys": masked_keys()}


# ── Live API Balances ───────────────────────────────────────────────────────────

@router.get("/api-balances")
async def get_api_balances(_: dict = Depends(_require_admin)):
    """Return live balance from each provider's API (where supported)."""
    from agents.providers.pr_api_balances import get_all_balances
    return await get_all_balances()


# ── Usage Table (daily aggregated) ─────────────────────────────────────────────

@router.get("/usage-table")
async def get_usage_table(_: dict = Depends(_require_admin)):
    """
    Daily aggregated usage table — grain: (date, user_id, provider).

    Reads from PostgreSQL when DATABASE_URL is set; falls back to JSONL files.
    Also returns 'system_rows' with live API balances per provider.
    """
    from agents.providers.pr_api_balances import get_all_balances

    users    = list_users()
    user_map = {u["id"]: u for u in users}
    mk       = masked_keys()
    result: list[dict] = []

    def _build_row(date: str, uid: str, provider: str, tin: int, tout: int,
                   cost: float, revenue: float, tp: dict) -> dict:
        user    = user_map.get(uid, {})
        balance = round(float(user.get("balance_added_usd", 0.0))
                        - float(user.get("balance_used_usd", 0.0)), 4)
        ki = mk.get(provider, {})
        return {
            "date":             date or "",
            "user_id":          uid or "",
            "email":            user.get("email", uid or ""),
            "llm":              provider,
            "api_key_masked":   ki.get("masked", ""),
            "tokens":           tin + tout,
            "tokens_input":     tin,
            "tokens_output":    tout,
            "cost":             round(float(cost    or 0), 6),
            "revenue":          round(float(revenue or 0), 6),
            "margin":           round(float(revenue or 0) - float(cost or 0), 6),
            "balance":          balance,
            "topup_cash":       tp.get("cash",        0.0),
            "topup_cash_cnt":   tp.get("cash_cnt",    0),
            "topup_coupon":     tp.get("coupon",      0.0),
            "topup_coupon_cnt": tp.get("coupon_cnt",  0),
        }

    if db.is_available():
        # ── PostgreSQL path ────────────────────────────────────────────────────
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_USAGE_BY_DATE)
                    usage_rows = cur.fetchall()

                    cur.execute(_SQL_TRANSACTIONS_BY_DATE)
                    tx_rows = cur.fetchall()

            # Build topups lookup: (date, user_id) → bucket
            pg_topups: dict[tuple, dict] = {}
            for date, uid, tx_type, amount, cnt in tx_rows:
                key = (date, uid)
                if key not in pg_topups:
                    pg_topups[key] = {"cash": 0.0, "cash_cnt": 0, "coupon": 0.0, "coupon_cnt": 0}
                if tx_type == "coupon_credit":
                    pg_topups[key]["coupon"]     = round(pg_topups[key]["coupon"] + float(amount or 0), 6)
                    pg_topups[key]["coupon_cnt"] += cnt
                else:
                    pg_topups[key]["cash"]     = round(pg_topups[key]["cash"] + float(amount or 0), 6)
                    pg_topups[key]["cash_cnt"] += cnt

            for date, uid, provider, tin, tout, cost, revenue in usage_rows:
                tp = pg_topups.get((date, uid), {})
                result.append(_build_row(date, uid, provider, tin or 0, tout or 0, cost or 0, revenue or 0, tp))

        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    else:
        # ── JSONL file path (when no DATABASE_URL) ─────────────────────────────
        file_rows: dict[tuple, dict] = {}
        file_topups: dict[tuple, dict] = {}

        def _frow(date: str, uid: str, provider: str) -> dict:
            key = (date, uid, provider)
            if key not in file_rows:
                file_rows[key] = {"tokens_input": 0, "tokens_output": 0, "cost": 0.0, "revenue": 0.0}
            return file_rows[key]

        def _ftopup(date: str, uid: str) -> dict:
            key = (date, uid)
            if key not in file_topups:
                file_topups[key] = {"cash": 0.0, "cash_cnt": 0, "coupon": 0.0, "coupon_cnt": 0}
            return file_topups[key]

        usage_dir = Path(settings.data_dir) / "usage"
        tx_dir    = Path(settings.data_dir) / "transactions"

        if usage_dir.exists():
            for uf in usage_dir.glob("*.jsonl"):
                uid = uf.stem
                for line in uf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        row = _frow(r["ts"][:10], uid, r.get("provider", "unknown"))
                        row["tokens_input"]  += r.get("input_tokens", 0)
                        row["tokens_output"] += r.get("output_tokens", 0)
                        row["cost"]           = round(row["cost"] + r.get("cost_usd", 0.0), 8)
                    except Exception:
                        pass

        if tx_dir.exists():
            for tf in tx_dir.glob("*.jsonl"):
                uid = tf.stem
                for line in tf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r       = json.loads(line)
                        date    = r["ts"][:10]
                        tx_type = r.get("type", "")
                        amount  = r.get("amount_usd", 0.0)
                        if tx_type == "usage_debit":
                            desc     = r.get("description", "")
                            provider = desc.split(" ")[0] if desc else "unknown"
                            row      = _frow(date, uid, provider)
                            row["revenue"] = round(row["revenue"] + amount, 8)
                            if row["cost"] == 0.0:
                                row["cost"] = round(row["cost"] + r.get("base_cost_usd", amount), 8)
                        elif tx_type == "coupon_credit":
                            t = _ftopup(date, uid)
                            t["coupon"] = round(t["coupon"] + amount, 6); t["coupon_cnt"] += 1
                        elif tx_type in ("admin_credit", "stripe_payment"):
                            t = _ftopup(date, uid)
                            t["cash"] = round(t["cash"] + amount, 6); t["cash_cnt"] += 1
                    except Exception:
                        pass

        for (date, uid, provider), row in sorted(file_rows.items()):
            tp = file_topups.get((date, uid), {})
            result.append(_build_row(date, uid, provider,
                                     row["tokens_input"], row["tokens_output"],
                                     row["cost"], row["revenue"], tp))

    # ── System rows: live API balance per provider ─────────────────────────────
    api_balances = await get_all_balances()
    system_rows  = [
        {
            "provider":       provider,
            "api_key_masked": mk.get(provider, {}).get("masked", ""),
            "api_balance":    bal,
        }
        for provider, bal in api_balances.items()
    ]

    return {"rows": result, "system_rows": system_rows}


# ── Provider Costs (per-token pricing config) ───────────────────────────────────

@router.get("/provider-costs")
async def get_provider_costs(_: dict = Depends(_require_admin)):
    """Return provider_costs.json — per-token pricing used for cost estimation."""
    from agents.providers.pr_costs import load_costs, get_model_list
    cfg = load_costs()
    return {**cfg, "model_list": get_model_list()}


@router.put("/provider-costs")
async def put_provider_costs(body: dict, admin: dict = Depends(_require_admin)):
    """Save updated provider_costs.json."""
    from agents.providers.pr_costs import save_costs
    admin_email = admin.get("email", "admin")
    save_costs(body, updated_by=admin_email)
    return {"ok": True}


# ── Fetch Provider Usage (actual costs from provider APIs) ──────────────────────

class FetchUsageRequest(BaseModel):
    provider: str                  # "openai" | "anthropic" / "claude"
    start_date: str                # YYYY-MM-DD
    end_date: str                  # YYYY-MM-DD
    org_id: str | None = None      # Required for Anthropic
    api_key: str | None = None     # Override server key (optional)


@router.post("/fetch-provider-usage")
async def fetch_provider_usage_endpoint(
    body: FetchUsageRequest,
    _: dict = Depends(_require_admin),
):
    """
    Fetch actual usage data from the provider's billing API.
    Results are stored and returned immediately.
    """
    from agents.providers.pr_usage_api import fetch_provider_usage
    result = await fetch_provider_usage(
        provider=body.provider,
        start_date=body.start_date,
        end_date=body.end_date,
        org_id=body.org_id,
        api_key=body.api_key or None,
    )
    return result


@router.get("/provider-usage-history")
async def get_provider_usage_history(
    provider: str | None = None,
    limit: int = 50,
    _: dict = Depends(_require_admin),
):
    """Return last N provider usage fetch results (from JSONL history)."""
    from agents.providers.pr_usage_api import load_usage_history
    return {"records": load_usage_history(provider=provider, limit=limit)}


@router.delete("/provider-usage-history")
async def delete_provider_usage_history(
    provider: str,
    fetched_at: str | None = None,
    _: dict = Depends(_require_admin),
):
    """Delete a single record (by fetched_at) or all records for a provider."""
    from agents.providers.pr_usage_api import delete_history_record, clear_history
    if fetched_at:
        ok = delete_history_record(provider, fetched_at)
        return {"ok": ok, "deleted": 1 if ok else 0}
    deleted = clear_history(provider)
    return {"ok": True, "deleted": deleted}


# ── Manual Provider Balances ────────────────────────────────────────────────────

@router.get("/provider-balances")
async def get_provider_balances(_: dict = Depends(_require_admin)):
    """Return manually-entered provider balances (from provider_balances.json)."""
    from agents.providers.pr_balances import load_balances
    return load_balances()


@router.put("/provider-balances")
async def put_provider_balances(body: dict, admin: dict = Depends(_require_admin)):
    """Save manually-entered provider balances."""
    from agents.providers.pr_balances import save_balances
    admin_email = admin.get("email", "admin")
    data = save_balances(body, updated_by=admin_email)
    return {"ok": True, "balances": data}


# ── DB Schema Migration ──────────────────────────────────────────────────────────

@router.post("/migrate-project-tables")
async def migrate_project_tables(_: dict = Depends(_require_admin)):
    """Migrate data from old shared tables to per-project tables.

    Reads from legacy shared tables (commits, events, embeddings, event_tags, event_links)
    and copies rows into the new per-project tables. Idempotent — safe to run multiple times.
    Returns migrated row counts per project.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    migrated: dict[str, dict[str, int]] = {}

    def _table_exists(cur, table: str) -> bool:
        cur.execute(_SQL_MIGRATE_CHECK_TABLE, (table,))
        return cur.fetchone() is not None

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Collect distinct projects from each old shared table
            projects: set[str] = set()
            for old_table in ("commits", "events", "embeddings"):
                if _table_exists(cur, old_table):
                    cur.execute(f"SELECT DISTINCT project FROM {old_table}")
                    for row in cur.fetchall():
                        if row[0]:
                            projects.add(row[0])

            for project in sorted(projects):
                counts: dict[str, int] = {}

                # Migrate commits
                if _table_exists(cur, "commits"):
                    cur.execute(
                        """INSERT INTO pr_commits
                               (client_id, project, commit_hash, commit_msg, summary, phase, feature,
                                bug_ref, source, session_id, tags, committed_at, created_at)
                            SELECT 1, %s, commit_hash, commit_msg, summary, phase, feature,
                                   bug_ref, source, session_id, tags, committed_at, created_at
                            FROM commits WHERE project=%s
                            ON CONFLICT (commit_hash) DO NOTHING""",
                        (project, project),
                    )
                    counts["commits"] = cur.rowcount

                # Migrate events (build a mapping old_id → new_id for FK resolution)
                old_to_new_event: dict[int, int] = {}
                if _table_exists(cur, "events"):
                    cur.execute(
                        "SELECT id, event_type, source_id, title, content, metadata, created_at "
                        "FROM events WHERE project=%s",
                        (project,),
                    )
                    event_rows = cur.fetchall()
                    inserted_events = 0
                    for old_id, et, sid, title, content, meta, created_at in event_rows:
                        cur.execute(
                            """INSERT INTO pr_events
                                   (client_id, project, event_type, source_id, title, content, metadata, created_at)
                                VALUES (1,%s,%s,%s,%s,%s,%s,%s)
                                ON CONFLICT (client_id, project, event_type, source_id) DO NOTHING
                                RETURNING id""",
                            (project, et, sid, title, content, meta, created_at),
                        )
                        row = cur.fetchone()
                        if row:
                            old_to_new_event[old_id] = row[0]
                            inserted_events += 1
                        else:
                            # Already existed — look up new id
                            cur.execute(
                                "SELECT id FROM pr_events WHERE client_id=1 AND project=%s AND event_type=%s AND source_id=%s",
                                (project, et, sid),
                            )
                            r2 = cur.fetchone()
                            if r2:
                                old_to_new_event[old_id] = r2[0]
                    counts["events"] = inserted_events

                # Migrate event_tags
                if _table_exists(cur, "event_tags") and old_to_new_event:
                    cur.execute(
                        "SELECT et.event_id, et.entity_value_id, et.auto_tagged "
                        "FROM event_tags et "
                        "JOIN events e ON e.id = et.event_id "
                        "WHERE e.project=%s",
                        (project,),
                    )
                    et_rows = cur.fetchall()
                    inserted_tags = 0
                    for old_eid, val_id, auto in et_rows:
                        new_eid = old_to_new_event.get(old_eid)
                        if new_eid:
                            cur.execute(
                                "INSERT INTO pr_event_tags (event_id, entity_value_id, auto_tagged) "
                                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                                (new_eid, val_id, auto),
                            )
                            inserted_tags += cur.rowcount
                    counts["event_tags"] = inserted_tags

                # Migrate event_links
                if _table_exists(cur, "event_links") and old_to_new_event:
                    cur.execute(
                        "SELECT el.from_event_id, el.to_event_id, el.link_type "
                        "FROM event_links el "
                        "JOIN events e ON e.id = el.from_event_id "
                        "WHERE e.project=%s",
                        (project,),
                    )
                    el_rows = cur.fetchall()
                    inserted_links = 0
                    for old_from, old_to, ltype in el_rows:
                        new_from = old_to_new_event.get(old_from)
                        new_to   = old_to_new_event.get(old_to)
                        if new_from and new_to:
                            cur.execute(
                                "INSERT INTO pr_event_links (from_event_id, to_event_id, link_type) "
                                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                                (new_from, new_to, ltype),
                            )
                            inserted_links += cur.rowcount
                    counts["event_links"] = inserted_links

                # Migrate embeddings
                if _table_exists(cur, "embeddings"):
                    cur.execute(
                        """INSERT INTO pr_embeddings
                               (client_id, project, source_type, source_id, chunk_index, content, embedding,
                                chunk_type, doc_type, language, file_path, metadata, created_at)
                            SELECT 1, %s, source_type, source_id, chunk_index, content, embedding,
                                   chunk_type, doc_type, language, file_path, metadata, created_at
                            FROM embeddings WHERE project=%s
                            ON CONFLICT (client_id, project, source_type, source_id, chunk_index) DO NOTHING""",
                        (project, project),
                    )
                    counts["embeddings"] = cur.rowcount

                migrated[project] = counts

    return {"migrated": migrated, "projects": list(migrated.keys())}


# ── Memory Layer Migration ────────────────────────────────────────────────────

@router.post("/migrate-to-memory-layers")
async def migrate_to_memory_layers(project: str, _: dict = Depends(_require_admin)):
    """Migrate per-project event/tag tables to shared interactions/work_items tables.

    Runs in the background — returns immediately with status.
    Safe to call multiple times (idempotent).
    """
    import asyncio
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    from core.migrations.migrate_to_memory_layers import run_migration
    asyncio.create_task(run_migration(project))
    return {"status": "migration started", "project": project}
