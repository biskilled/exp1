"""
Loads environment variables from a .env file.
Accepts both str and Path objects.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_environment(env_path: str | Path = ".env") -> dict:
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=False)
        print(f"[env] Loaded {env_file}")
    else:
        print("[env] No .env file found — using system environment.")
    return dict(os.environ)
