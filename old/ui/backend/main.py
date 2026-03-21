"""
aicli Desktop — FastAPI backend.

Serves the API for the Electron frontend.
No SQLite, no ChromaDB — JSONL/JSON/CSV file storage only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from pathlib import Path

from config import settings


def _migrate_server_data():
    """One-time migration: copy files from old .aicli/server_data/ to ui/backend/data/."""
    engine_root = Path(__file__).parent.parent.parent.resolve()
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
        print(f"✅ Migrated server_data to ui/backend/data/: {', '.join(migrated)}")
from core.database import db
from routers import auth, chat, history, usage, workflows, prompts, files, projects, config_sync, admin, git, billing, search, entities, graph_workflows, work_items, agent_roles, system_roles, documents
from pwa_router import router as pwa_router


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
app.include_router(auth.router,        prefix="/auth",        tags=["auth"])
app.include_router(usage.router,       prefix="/usage",       tags=["usage"])
app.include_router(chat.router,        prefix="/chat",        tags=["chat"])
app.include_router(history.router,     prefix="/history",     tags=["history"])
app.include_router(workflows.router,   prefix="/workflows",   tags=["workflows"])
app.include_router(prompts.router,     prefix="/prompts",     tags=["prompts"])
app.include_router(files.router,       prefix="/files",       tags=["files"])
app.include_router(projects.router,    prefix="/projects",    tags=["projects"])
app.include_router(config_sync.router, prefix="/config",      tags=["config"])
app.include_router(admin.router,       prefix="/admin",        tags=["admin"])
app.include_router(git.router,         prefix="/git",           tags=["git"])
app.include_router(billing.router,         prefix="/billing",          tags=["billing"])
app.include_router(search.router,          prefix="/search",    tags=["search"])
app.include_router(entities.router,        prefix="/entities",  tags=["entities"])
app.include_router(graph_workflows.router, prefix="/graph",      tags=["graph_workflows"])
app.include_router(work_items.router,     prefix="/work-items",   tags=["work_items"])
app.include_router(agent_roles.router,    prefix="/agent-roles",   tags=["agent_roles"])
app.include_router(system_roles.router,   prefix="/system-roles",  tags=["system_roles"])
app.include_router(documents.router,      prefix="/documents",     tags=["documents"])

# Static files
STATIC_DIR = Path(__file__).parent.parent / "static"
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
    }


@app.on_event("startup")
async def startup():
    db.init()   # connect to PostgreSQL if DATABASE_URL is set; no-op otherwise

    # Migrate server_data from old .aicli/server_data/ path to ui/backend/data/
    _migrate_server_data()

    # Ensure monetization data files exist on first start
    from core.pricing import load_pricing
    from core.api_keys import load_keys, save_keys, _env_key, _PROVIDERS
    from routers.admin import _load_coupons
    load_pricing(); _load_coupons()
    # Seed api_keys.json from env vars for any provider slot that is still empty
    keys = load_keys()
    updated = False
    for p in _PROVIDERS:
        if not keys.get(p, "").strip():
            env_val = _env_key(p)
            if env_val:
                keys[p] = env_val
                updated = True
    if updated:
        save_keys(keys)
    print(f"✅ aicli backend ready — {settings.backend_url}")
    print(f"   workspace: {settings.workspace_dir}")
    print(f"   project:   {settings.active_project}")
    print(f"   db:        {'PostgreSQL' if db.is_available() else 'file-based'}")
    if settings.dev_mode:
        print(f"   ⚠️  DEV_MODE=true — all requests authenticated as admin")
