"""
Backend configuration — loaded from environment variables.

Key env vars:
  WORKSPACE_DIR   root of all project workspaces
  ACTIVE_PROJECT  currently active project name
  CODE_DIR        default code directory for file browsing
"""

import json
import os
from pathlib import Path
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).parent.parent.resolve()

_ENGINE_ROOT = _BACKEND_DIR.parent

# Bootstrap WORKSPACE_DIR from ~/.agentdesk/config.json when not already set via env
_agentdesk_config_path = Path.home() / ".agentdesk" / "config.json"
if _agentdesk_config_path.exists() and not os.environ.get("WORKSPACE_DIR"):
    try:
        _c = json.loads(_agentdesk_config_path.read_text())
        _agentdesk_dir = _c.get("agentdesk_dir", "")
        if _agentdesk_dir:
            os.environ.setdefault("WORKSPACE_DIR", str(Path(_agentdesk_dir) / "workspace"))
    except Exception:
        pass


class Settings(BaseSettings):
    # LLM API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""

    # Models
    claude_model: str = "claude-sonnet-4-6"
    haiku_model: str = "claude-haiku-4-5-20251001"
    openai_model: str = "gpt-4.1"
    deepseek_model: str = "deepseek-chat"
    deepseek_reasoner_model: str = "deepseek-reasoner"
    gemini_model: str = "gemini-2.0-flash"
    grok_model: str = "grok-3"

    # Workspace
    workspace_dir: str = str(_ENGINE_ROOT / "workspace")
    active_project: str = "agentdesk"
    code_dir: str = str(_ENGINE_ROOT)

    # Auth
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    require_auth: bool = False          # set True in Railway env vars
    access_token_expire_minutes: int = 60 * 24 * 7   # 7 days


    # Runtime data dir — outside backend/ (JSON fallbacks when DB unavailable)
    data_dir: str = str(_ENGINE_ROOT / "data")

    # PostgreSQL (optional — falls back to JSON file store when empty)
    database_url: str = ""   # set DATABASE_URL=postgresql://... in .env

    # Developer / deployment mode
    dev_mode: bool = False              # DEV_MODE=true → all requests treated as admin, no login

    # Stripe (placeholder — real charging deferred)
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""

    # App
    cors_origins: str = "*"
    backend_url: str = "http://localhost:8000"
    db_pool_max: int = 10

    # Logging — files written to log_dir (external to backend/)
    # Override via env: LOG_DIR, LOG_LEVEL, LOG_RETENTION_DAYS, LOG_DEBUG_BACKUP_COUNT
    log_dir: str = str(Path.home() / ".agentdesk" / "logs")
    log_level: str = "info"            # console level: debug|info|warning|error
    log_retention_days: int = 30       # days to keep app.log + error.log backups
    log_debug_backup_count: int = 7    # days to keep debug.log backups

    class Config:
        env_file = str(_ENGINE_ROOT / ".env")
        extra = "ignore"


settings = Settings()
