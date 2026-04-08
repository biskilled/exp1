"""
prompt_loader.py — File-based system prompt loader.

Loads internal system prompts from backend/prompts/.
Configuration in backend/prompts/prompts.yaml specifies model + max_tokens per prompt.
Prompts are NOT stored in the DB and NOT exposed to users.

Usage::

    from core.prompt_loader import prompts

    # Get prompt config (content + model + max_tokens)
    cfg = prompts.get("commit_digest")   # PromptConfig | None

    # Call the configured model directly
    result = await prompts.call("commit_digest", user_message)   # → str

    # Just get the text (for callers that manage their own LLM calls)
    text = prompts.content("commit_digest")   # str | None
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Resolved at import time — same directory as this file's parent / prompts
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class PromptConfig:
    name: str
    content: str
    model: str        # resolved model ID (e.g. "claude-haiku-4-5-20251001")
    max_tokens: int
    file_path: Path


class PromptLoader:
    """
    Reads backend/prompts/prompts.yaml and the referenced .md files once on first access.
    Thread-safe for reads (writes never happen at runtime).
    """

    def __init__(self) -> None:
        self._configs: dict[str, PromptConfig] = {}
        self._loaded = False

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[PromptConfig]:
        """Return the PromptConfig for the given name, or None if not found."""
        self._ensure_loaded()
        return self._configs.get(name)

    def content(self, name: str) -> Optional[str]:
        """Return just the prompt text, or None if not found."""
        cfg = self.get(name)
        return cfg.content if cfg else None

    async def call(self, name: str, user_message: str, *,
                   max_tokens: Optional[int] = None) -> str:
        """Load the prompt, call the configured model, return the response text.

        Falls back gracefully to '' if the prompt file is missing or the API call fails.
        """
        cfg = self.get(name)
        if not cfg or not cfg.content:
            log.debug(f"prompt_loader.call: prompt '{name}' not found or empty")
            return ""
        tokens = max_tokens or cfg.max_tokens
        return await _call_model(cfg.model, cfg.content, user_message, tokens)

    # ── Internal ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True  # set early to avoid re-entrant loading
        self._load()

    def _load(self) -> None:
        yaml_path = _PROMPTS_DIR / "prompts.yaml"
        if not yaml_path.exists():
            log.warning(f"prompt_loader: {yaml_path} not found — no prompts loaded")
            return
        try:
            import yaml
            data = yaml.safe_load(yaml_path.read_text()) or {}
        except Exception as e:
            log.warning(f"prompt_loader: failed to parse prompts.yaml: {e}")
            return

        try:
            from core.config import settings
            model_map: dict[str, str] = {
                "haiku":  getattr(settings, "haiku_model",  "claude-haiku-4-5-20251001"),
                "sonnet": getattr(settings, "model",        "claude-sonnet-4-6"),
            }
        except Exception:
            model_map = {
                "haiku":  "claude-haiku-4-5-20251001",
                "sonnet": "claude-sonnet-4-6",
            }

        loaded = 0
        for name, cfg in (data.get("prompts") or {}).items():
            rel_path   = cfg.get("file", "")
            model_key  = cfg.get("model", "haiku")
            max_tokens = int(cfg.get("max_tokens", 300))
            model_id   = model_map.get(model_key, model_key)  # fallback: use key as-is

            file_path = _PROMPTS_DIR / rel_path
            if not file_path.exists():
                log.warning(f"prompt_loader: prompt file not found: {file_path}")
                content = ""
            else:
                content = file_path.read_text().strip()

            self._configs[name] = PromptConfig(
                name=name,
                content=content,
                model=model_id,
                max_tokens=max_tokens,
                file_path=file_path,
            )
            loaded += 1

        log.debug(f"prompt_loader: loaded {loaded} prompts from {_PROMPTS_DIR}")


async def _call_model(model: str, system: str, user: str, max_tokens: int) -> str:
    """Call Claude with the given model/system/user. Returns '' on any failure."""
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return ""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_call_model({model}): {e}")
        return ""


# ── Module-level singleton ────────────────────────────────────────────────────
prompts = PromptLoader()
