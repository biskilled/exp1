"""
prompt_loader.py — File-based system prompt loader.

Each prompt is a self-contained YAML file under backend/prompts/ with fields:
  name         — human-readable label
  description  — what the prompt does
  model        — haiku | sonnet  (resolved to full model ID at load time)
  max_tokens   — int
  system       — the system prompt text (multiline YAML literal block)
  tools        — (optional) list of tool definitions
  mcp_server   — (optional) MCP server config

Prompts are NOT stored in the DB and NOT exposed to users.
The loader walks the directory recursively and uses the stem filename as the key
(e.g. commits/commit_digest.yaml → key "commit_digest").

Usage::

    from core.prompt_loader import prompts

    # Get prompt config (content + model + max_tokens)
    cfg = prompts.get("commit_digest")   # PromptConfig | None

    # Call the configured model directly
    result = await prompts.call("commit_digest", user_message)   # → str

    # Just get the system text (for callers that manage their own LLM calls)
    text = prompts.content("commit_digest")   # str | None
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


@dataclass
class PromptConfig:
    name: str
    description: str
    content: str          # the system prompt text
    model: str            # resolved model ID (e.g. "claude-haiku-4-5-20251001")
    max_tokens: int
    tools: list[dict[str, Any]] = field(default_factory=list)
    mcp_server: Optional[dict[str, Any]] = None
    file_path: Optional[Path] = None


class PromptLoader:
    """
    Walks backend/prompts/ recursively for *.yaml files on first access.
    Each YAML file is one prompt; its stem filename is the lookup key.
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
        """Return just the system prompt text, or None if not found."""
        cfg = self.get(name)
        return cfg.content if cfg else None

    async def call(self, name: str, user_message: str, *,
                   max_tokens: Optional[int] = None) -> str:
        """Load the prompt, call the configured model, return the response text.

        Falls back gracefully to '' if the prompt is missing or the API call fails.
        """
        cfg = self.get(name)
        if not cfg or not cfg.content:
            log.debug(f"prompt_loader.call: prompt '{name}' not found or empty")
            return ""
        tokens = max_tokens or cfg.max_tokens
        return await _call_model(cfg.model, cfg.content, user_message, tokens)

    def list_names(self) -> list[str]:
        """Return all loaded prompt keys."""
        self._ensure_loaded()
        return list(self._configs.keys())

    # ── Internal ────────────────────────────────────────────────────────────

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        self._load()

    def _load(self) -> None:
        if not _PROMPTS_DIR.exists():
            log.warning(f"prompt_loader: prompts directory not found: {_PROMPTS_DIR}")
            return

        try:
            import yaml as _yaml
        except ImportError:
            log.warning("prompt_loader: PyYAML not installed — no prompts loaded")
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
        for yaml_file in sorted(_PROMPTS_DIR.rglob("*.yaml")):
            # Skip the legacy prompts.yaml index file if still present
            if yaml_file.name == "prompts.yaml":
                continue
            try:
                data = _yaml.safe_load(yaml_file.read_text()) or {}
            except Exception as e:
                log.warning(f"prompt_loader: failed to parse {yaml_file}: {e}")
                continue

            key        = yaml_file.stem                          # filename without .yaml
            model_key  = data.get("model", "haiku")
            model_id   = model_map.get(model_key, model_key)    # fallback: use key as-is
            max_tokens = int(data.get("max_tokens", 300))
            system     = (data.get("system") or "").strip()
            tools      = data.get("tools") or []
            mcp_server = data.get("mcp_server") or None

            if not system:
                log.warning(f"prompt_loader: {yaml_file.name} has no 'system' field — skipped")
                continue

            self._configs[key] = PromptConfig(
                name=data.get("name", key),
                description=data.get("description", ""),
                content=system,
                model=model_id,
                max_tokens=max_tokens,
                tools=tools,
                mcp_server=mcp_server,
                file_path=yaml_file,
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
