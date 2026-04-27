"""
prompt_loader.py — File-based system prompt loader.

Each YAML file under backend/prompts/ is one of two formats:

  Single-prompt (dict):
    name, description, model, max_tokens, system, tools?, mcp_server?
    Key = filename stem (e.g. conflict_detection.yaml → "conflict_detection")

  Multi-prompt (list):
    Each item has the same fields plus a required `key` field.
    Key = item["key"] (e.g. commit.yaml with key=commit_analysis → "commit_analysis")

Prompts are NOT stored in the DB and NOT exposed to users.

Usage::

    from core.prompt_loader import prompts

    cfg = prompts.get("commit_analysis")   # PromptConfig | None
    result = await prompts.call("commit_symbol", user_message)   # → str
    text = prompts.content("conflict_detection")   # str | None
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
            # These files use custom nested formats loaded directly by their callers
            if yaml_file.name in ("prompts.yaml", "command_work_items.yaml"):
                continue
            try:
                data = _yaml.safe_load(yaml_file.read_text())
            except Exception as e:
                log.warning(f"prompt_loader: failed to parse {yaml_file}: {e}")
                continue

            # Support both single-prompt (dict) and multi-prompt (list) formats
            items: list[tuple[str, dict]]
            if isinstance(data, list):
                items = [(item["key"], item) for item in data if isinstance(item, dict) and item.get("key")]
            elif isinstance(data, dict):
                items = [(yaml_file.stem, data)]
            else:
                continue

            for key, item in items:
                system = (item.get("system") or "").strip()
                if not system:
                    log.warning(f"prompt_loader: {yaml_file.name}[{key}] has no 'system' field — skipped")
                    continue
                model_key = item.get("model", "haiku")
                self._configs[key] = PromptConfig(
                    name=item.get("name", key),
                    description=item.get("description", ""),
                    content=system,
                    model=model_map.get(model_key, model_key),
                    max_tokens=int(item.get("max_tokens", 300)),
                    tools=item.get("tools") or [],
                    mcp_server=item.get("mcp_server") or None,
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
        _log_usage(model, getattr(resp.usage, "input_tokens", 0), getattr(resp.usage, "output_tokens", 0))
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_call_model({model}): {e}")
        return ""


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    """Write a memory-source usage record to mng_usage_logs (best-effort)."""
    try:
        from core.database import db
        from core.auth import ADMIN_USER_ID
        from agents.providers.pr_pricing import calculate_cost
        cost = calculate_cost("claude", model, input_tokens, output_tokens, markup_pct=0)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_usage_logs
                       (user_id, provider, model, input_tokens, output_tokens, cost_usd, charged_usd, source)
                       VALUES (%s, 'claude', %s, %s, %s, %s, 0, 'memory')""",
                    (ADMIN_USER_ID, model, input_tokens, output_tokens, cost),
                )
    except Exception as _e:
        log.debug(f"prompt_loader._log_usage: {_e}")


# ── Module-level singleton ────────────────────────────────────────────────────
prompts = PromptLoader()
