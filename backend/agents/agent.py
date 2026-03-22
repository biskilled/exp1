"""
agents/agent.py — Unified Agent class combining DB role + provider + tools + agentic loop.

Replaces the scattered _execute_node + _load_role + _call patterns across
graph_runner.py and work_item_pipeline.py with a single, composable abstraction.

Usage:
    agent = await Agent.from_role("Product Manager")
    result = await agent.run("Write acceptance criteria for: ...")

    # With tools enabled:
    agent = await Agent.from_role("Web Developer", with_tools=True)
    result = await agent.run("Implement the feature", context={"plan": "..."})
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

_MAX_TOOL_CALLS = 10
_CTX_CAP = 3000  # chars per prior-node output injected into user message


@dataclass
class AgentResult:
    output: str
    tool_calls_made: list = field(default_factory=list)
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "done"  # "done" | "error"


class Agent:
    """LLM agent combining a DB role, a provider, optional tools, and an agentic loop."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        provider: str,
        model: str,
        tools: list[dict] | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.provider = provider
        self.model = model
        self.tools = tools or []

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    async def from_role(
        cls,
        role_name: str,
        with_tools: bool = False,
    ) -> "Agent":
        """Load from mng_agent_roles + mng_system_roles JOIN.

        Falls back to a sensible default when the DB is unavailable or the
        role is not found.
        """
        from core.database import db
        from core.config import settings

        system_prompt = f"You are a {role_name}."
        provider = "claude"
        model = settings.haiku_model

        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """SELECT ar.system_prompt, ar.provider, ar.model,
                                      COALESCE(
                                        string_agg(sr.content, E'\\n\\n' ORDER BY rl.order_index),
                                        ''
                                      ) AS sys_content
                               FROM   mng_agent_roles ar
                               LEFT JOIN mng_role_system_links rl ON rl.role_id = ar.id
                               LEFT JOIN mng_system_roles sr ON sr.id = rl.system_role_id
                               WHERE  ar.name = %s AND ar.client_id = 1
                               GROUP  BY ar.id, ar.system_prompt, ar.provider, ar.model""",
                            (role_name,),
                        )
                        row = cur.fetchone()
                        if row:
                            base = row[0] or ""
                            provider = row[1] or "claude"
                            model = row[2] or settings.haiku_model
                            sys_content = row[3] or ""
                            system_prompt = (
                                f"{base}\n\n{sys_content}".strip() if sys_content else base
                            )
            except Exception as e:
                log.debug(f"Agent.from_role DB error for '{role_name}': {e}")

        tools: list[dict] = []
        if with_tools:
            from agents.tools import ALL_TOOL_DEFS
            tools = ALL_TOOL_DEFS

        return cls(name=role_name, system_prompt=system_prompt,
                   provider=provider, model=model, tools=tools)

    # ── LLM dispatch ──────────────────────────────────────────────────────────

    async def _call_provider(
        self,
        messages: list[dict],
        max_tokens: int,
        api_key: str | None,
    ) -> dict:
        """Dispatch to the correct provider and return a standard response dict."""
        if self.provider in ("claude", "anthropic", ""):
            from agents.providers.pr_claude import call_claude
            return await call_claude(
                messages, system=self.system_prompt,
                model=self.model, tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key,
            )
        elif self.provider == "openai":
            from agents.providers.pr_openai import call_openai
            return await call_openai(
                messages, system=self.system_prompt,
                model=self.model, tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key,
            )
        elif self.provider == "deepseek":
            from agents.providers.pr_deepseek import call_deepseek
            return await call_deepseek(
                messages, system=self.system_prompt,
                tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key,
            )
        elif self.provider == "gemini":
            from agents.providers.pr_gemini import call_gemini
            user_text = " ".join(
                m["content"] for m in messages if m.get("role") == "user"
            )
            return await call_gemini(
                user_text, system=self.system_prompt,
                model=self.model, api_key=api_key,
            )
        elif self.provider == "grok":
            from agents.providers.pr_grok import call_grok
            return await call_grok(
                messages, system=self.system_prompt,
                model=self.model, max_tokens=max_tokens, api_key=api_key,
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider!r} for agent '{self.name}'")

    # ── Agentic loop ──────────────────────────────────────────────────────────

    async def run(
        self,
        user_msg: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> AgentResult:
        """Run the agent with an optional context dict.

        Agentic loop:
        1. Inject context into user message (each prior output capped at _CTX_CAP chars)
        2. Call provider (with tools if configured)
        3. If stop_reason == "tool_use": invoke tool handler → append result → re-call
        4. Repeat until "end_turn" or max tool calls exceeded
        """
        from core.api_keys import get_key
        from agents.providers.pr_costs import estimate_cost

        if api_key is None:
            api_key = get_key(self.provider) or get_key("claude")

        # Build user message with context injection
        parts: list[str] = []
        if context:
            ctx_str = "\n\n".join(
                f"=== {k} output ===\n"
                + (
                    v[:_CTX_CAP] + "\n[...truncated]"
                    if isinstance(v, str) and len(v) > _CTX_CAP
                    else (v if isinstance(v, str) else json.dumps(v)[:_CTX_CAP])
                )
                for k, v in context.items()
                if not k.startswith("_")
            )
            if ctx_str:
                parts.append(f"<context>\n{ctx_str}\n</context>")
        parts.append(user_msg)
        full_user_msg = "\n".join(parts)

        messages: list[dict] = [{"role": "user", "content": full_user_msg}]

        tool_calls_made: list[dict] = []
        total_input = total_output = 0

        for _ in range(_MAX_TOOL_CALLS + 1):
            resp = await self._call_provider(messages, max_tokens, api_key)
            total_input += resp.get("input_tokens", 0)
            total_output += resp.get("output_tokens", 0)

            tool_calls = resp.get("tool_calls", [])
            stop_reason = resp.get("stop_reason", "end_turn")

            if stop_reason != "tool_use" or not tool_calls:
                # Terminal turn — return content
                cost = 0.0
                try:
                    cost = estimate_cost(
                        self.provider, self.model or self.provider,
                        total_input, total_output,
                    )
                except Exception:
                    pass
                return AgentResult(
                    output=resp.get("content", ""),
                    tool_calls_made=tool_calls_made,
                    cost_usd=cost,
                    input_tokens=total_input,
                    output_tokens=total_output,
                    status="done",
                )

            # Tool use turn — invoke each tool and append results
            from agents.tools import invoke_tool

            # Append assistant turn with tool calls
            messages.append({"role": "assistant", "content": resp.get("raw", resp)})

            tool_results: list[dict] = []
            for tc in tool_calls:
                tool_name = getattr(tc, "name", None) or tc.get("name", "")
                tool_input = getattr(tc, "input", None) or tc.get("input", {})
                tool_id = getattr(tc, "id", None) or tc.get("id", "")
                result_text = invoke_tool(tool_name, tool_input)
                tool_calls_made.append({"name": tool_name, "input": tool_input})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result_text,
                })

            messages.append({"role": "user", "content": tool_results})

        # Exceeded max tool calls — return last content
        return AgentResult(
            output=resp.get("content", ""),
            tool_calls_made=tool_calls_made,
            cost_usd=0.0,
            input_tokens=total_input,
            output_tokens=total_output,
            status="done",
        )
