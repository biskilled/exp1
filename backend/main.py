"""
aicli Desktop — FastAPI backend.

Serves the API for the Electron frontend.
No SQLite, no ChromaDB — JSONL/JSON/CSV file storage only.
"""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings

# ── Logging — must be set up before any other import that calls get_logger ──────
from core.logger import AppLogger, get_logger

AppLogger.setup(
    log_dir=Path(settings.log_dir),
    level=settings.log_level,
    retention_days=settings.log_retention_days,
    debug_backup_count=settings.log_debug_backup_count,
)
log = get_logger(__name__)
# ────────────────────────────────────────────────────────────────────────────────

from core.database import db
from routers import (
    route_auth, route_chat, route_history, route_usage, route_workflows,
    route_prompts, route_files, route_projects, route_config_sync, route_admin,
    route_git, route_billing, route_search, route_entities, route_graph_workflows,
    route_agent_roles, route_system_roles, route_documents,
    route_user_api_keys, route_logs, route_agents, route_tags,
)
from routers import route_memory
from routers.route_work_items import router as work_items_router
from routers.route_system import router as system_router
from pwa_router import router as pwa_router


def _migrate_server_data():
    """One-time migration: copy files from old .aicli/server_data/ to ui/backend/data/."""
    engine_root = Path(__file__).parent.parent.resolve()
    old_path = engine_root / ".aicli" / "server_data"
    new_path = Path(settings.data_dir)
    if not old_path.exists():
        return
    new_path.mkdir(parents=True, exist_ok=True)
    migrated = []
    for item in old_path.iterdir():
        dest = new_path / item.name
        if not dest.exists():
            if item.is_dir():
                shutil.copytree(str(item), str(dest))
            else:
                shutil.copy2(str(item), str(dest))
            migrated.append(item.name)
    if migrated:
        log.info("Migrated server_data → data/: %s", ", ".join(migrated))


app = FastAPI(
    title="aicli Desktop API",
    description="AI-powered development CLI — desktop backend",
    version="2.0.0",
)

_cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PWA routes (before static mount)
app.include_router(pwa_router, tags=["pwa"])

# API routes
app.include_router(route_auth.router,           prefix="/auth",           tags=["auth"])
app.include_router(route_usage.router,          prefix="/usage",          tags=["usage"])
app.include_router(route_chat.router,           prefix="/chat",           tags=["chat"])
app.include_router(route_history.router,        prefix="/history",        tags=["history"])
app.include_router(route_workflows.router,      prefix="/workflows",      tags=["workflows"])
app.include_router(route_prompts.router,        prefix="/prompts",        tags=["prompts"])
app.include_router(route_files.router,          prefix="/files",          tags=["files"])
app.include_router(route_projects.router,       prefix="/projects",       tags=["projects"])
app.include_router(route_config_sync.router,    prefix="/config",         tags=["config"])
app.include_router(route_admin.router,          prefix="/admin",          tags=["admin"])
app.include_router(route_git.router,            prefix="/git",            tags=["git"])
app.include_router(route_billing.router,        prefix="/billing",        tags=["billing"])
app.include_router(route_search.router,         prefix="/search",         tags=["search"])
app.include_router(route_entities.router,       prefix="/entities",       tags=["entities"])
app.include_router(route_graph_workflows.router,prefix="/graph",          tags=["graph_workflows"])
app.include_router(route_agent_roles.router,    prefix="/agent-roles",    tags=["agent_roles"])
app.include_router(route_system_roles.router,   prefix="/system-roles",   tags=["system_roles"])
app.include_router(route_documents.router,      prefix="/documents",      tags=["documents"])
app.include_router(route_user_api_keys.router,  prefix="/user/api-keys",  tags=["user_api_keys"])
app.include_router(route_logs.router,           prefix="/logs",           tags=["logs"])
app.include_router(route_agents.router,         prefix="/agents",         tags=["agents"])
app.include_router(route_tags.router,           prefix="/tags",           tags=["tags"])
app.include_router(route_memory.router,         prefix="/memory",         tags=["memory"])
app.include_router(work_items_router,           prefix="/wi",             tags=["work_items"])
app.include_router(system_router,                                          tags=["system"])

# Static files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "require_auth": settings.require_auth,
        "workspace_dir": settings.workspace_dir,
        "active_project": settings.active_project,
        "db_connected": db.is_available(),
    }


async def _warmup_statistics():
    """Wait for DB to connect then pre-compute today's pr_statistics row.

    Runs as a background task after startup so the dashboard has cached counts
    available immediately on first open without the user having to trigger
    a full data-dashboard reload.
    """
    import asyncio
    for _ in range(30):           # wait up to 60 s (Railway cold-start)
        if db.is_available():
            break
        await asyncio.sleep(2)
    if not db.is_available():
        log.debug("warmup_statistics: DB not ready after 60s, skipping")
        return
    try:
        from routers.route_memory import _refresh_stats
        pid = db.get_or_create_project_id(settings.active_project)
        _refresh_stats(pid)
        log.info("warmup_statistics: pr_statistics populated for '%s'", settings.active_project)
    except Exception as e:
        log.debug("warmup_statistics error: %s", e)


@app.on_event("startup")
async def startup():
    import asyncio
    # Fire-and-forget: DB init runs in a thread so the server starts immediately.
    # Routes check db.is_available() and fall back to file storage until DB connects.
    asyncio.get_event_loop().run_in_executor(None, db.init)

    # Pre-compute statistics once DB is ready (background, non-blocking)
    asyncio.ensure_future(_warmup_statistics())

    # Migrate server_data from old .aicli/server_data/ path to ui/backend/data/
    _migrate_server_data()

    # Warm up DB-backed config (seeds defaults if not yet stored)
    from agents.providers.pr_pricing import load_pricing
    from routers.route_admin import _load_coupons
    load_pricing(); _load_coupons()

    log.info("aicli backend ready — %s", settings.backend_url)
    log.info("  workspace : %s", settings.workspace_dir)
    log.info("  project   : %s", settings.active_project)
    log.info("  db        : %s", "PostgreSQL" if db.is_available() else "file-based")
    log.info("  logs      : %s", settings.log_dir)
    if settings.dev_mode:
        log.warning("DEV_MODE=true — all requests authenticated as admin")
