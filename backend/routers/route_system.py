"""route_system.py — System info and self-hosted update manifest.

Exposes /system/version (current UI + backend versions) and
/system/update-manifest (admin-hosted JSON describing the latest release).
Clients poll the manifest to discover updates without requiring an external
update service — the manifest lives in workspace/_system/update.json.
"""

import json
from pathlib import Path

from fastapi import APIRouter

from core.config import settings

router = APIRouter(prefix="/system", tags=["system"])

_UI_VERSION_FILE = Path(__file__).parent.parent.parent / "ui" / "VERSION"
_MANIFEST_FILE   = Path(settings.workspace_dir) / "_system" / "update.json"
BACKEND_VERSION  = "2.0.0"


@router.get("/version")
def get_version():
    """Return the current UI and backend versions."""
    ui_version = _UI_VERSION_FILE.read_text().strip() if _UI_VERSION_FILE.exists() else "unknown"
    return {"ui_version": ui_version, "backend_version": BACKEND_VERSION}


@router.get("/update-manifest")
def get_update_manifest():
    """Return the update manifest.  Returns {version: null} if no manifest exists."""
    if not _MANIFEST_FILE.exists():
        return {"version": None}
    try:
        return json.loads(_MANIFEST_FILE.read_text())
    except Exception:
        return {"version": None}


@router.put("/update-manifest")
def save_update_manifest(body: dict):
    """Admin-only: write a new update manifest to workspace/_system/update.json."""
    _MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    _MANIFEST_FILE.write_text(json.dumps(body, indent=2))
    return {"saved": True}
