"""
Config sync router — stub for future remote workspace upload.

Future: client POSTs workspace files to hosted backend.
Currently: returns local config info only.
"""

from fastapi import APIRouter

from core.config import settings

router = APIRouter()


@router.get("/")
async def get_config():
    """Return current backend configuration (non-sensitive fields)."""
    return {
        "workspace_dir": settings.workspace_dir,
        "active_project": settings.active_project,
        "code_dir": settings.code_dir,
        "providers_available": {
            "claude": bool(settings.anthropic_api_key),
            "openai": bool(settings.openai_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "gemini": bool(settings.gemini_api_key),
            "grok": bool(settings.grok_api_key),
        },
    }


@router.post("/sync")
async def sync_workspace():
    """
    Stub: upload workspace files to remote backend.
    Not implemented — local only for now.
    """
    return {
        "status": "stub",
        "message": "Remote sync not yet implemented. Files are local only.",
    }
