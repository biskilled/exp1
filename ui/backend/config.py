"""
Backend configuration — loaded from environment variables.

Key env vars:
  WORKSPACE_DIR   root of all project workspaces
  ACTIVE_PROJECT  currently active project name
  CODE_DIR        default code directory for file browsing
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).parent.resolve()
_UI_DIR = _BACKEND_DIR.parent
_ENGINE_ROOT = _UI_DIR.parent


class Settings(BaseSettings):
    # LLM API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""

    # Models
    claude_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4.1"
    deepseek_model: str = "deepseek-chat"
    deepseek_reasoner_model: str = "deepseek-reasoner"
    gemini_model: str = "gemini-2.0-flash"
    grok_model: str = "grok-3"

    # Workspace
    workspace_dir: str = str(_ENGINE_ROOT / "workspace")
    active_project: str = "aicli"
    code_dir: str = str(_ENGINE_ROOT)

    # Auth
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    require_auth: bool = False          # set True in Railway env vars
    access_token_expire_minutes: int = 60 * 24 * 7   # 7 days

    # Data storage (user accounts, usage logs)
    data_dir: str = str(_ENGINE_ROOT / ".aicli" / "server_data")

    # PostgreSQL (optional — falls back to JSON file store when empty)
    database_url: str = ""   # set DATABASE_URL=postgresql://... in .env

    # App
    cors_origins: str = "*"

    class Config:
        env_file = str(_ENGINE_ROOT / ".env")
        extra = "ignore"


settings = Settings()
