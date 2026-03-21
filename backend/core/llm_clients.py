"""
llm_clients.py — Backward-compat shim.

Re-exports all provider functions from agents/providers/ so existing
routers importing `from core.llm_clients import call_claude` continue to work.
"""
from agents.providers.claude import call_claude, _client as _async_anthropic_client, _sync_client as _anthropic_client  # noqa: F401
from agents.providers.openai import call_openai, _async_client as _async_openai_client, _sync_client as _openai_client  # noqa: F401
from agents.providers.deepseek import call_deepseek  # noqa: F401
from agents.providers.gemini import call_gemini  # noqa: F401
from agents.providers.grok import call_grok  # noqa: F401
