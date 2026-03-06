"""
aicli Desktop — FastAPI backend.

Serves the API for the Electron frontend.
No SQLite, no ChromaDB — JSONL/JSON/CSV file storage only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from config import settings
from core.database import db
from routers import auth, chat, history, usage, workflows, prompts, files, projects, config_sync, admin, git
from pwa_router import router as pwa_router


app = FastAPI(
    title="aicli Desktop API",
    description="AI-powered development CLI — desktop backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    print(f"✅ aicli backend ready — http://localhost:8000")
    print(f"   workspace: {settings.workspace_dir}")
    print(f"   project:   {settings.active_project}")
    print(f"   db:        {'PostgreSQL' if db.is_available() else 'file-based'}")
