"""
agents/agent.py — Unified Agent class combining DB role + provider + tools + agentic loop.

Two run modes:
  run()          — general-purpose loop (used by pipeline graph nodes, work-item pipeline, etc.)
  run_pipeline() — ReAct-enforced loop for orchestrated pipelines:
                    • Hallucination guard: requires Thought text before every tool call
                    • Loop detection: aborts if the same tool is called 3× in a row
                    • Structured handoff: extracts JSON output and passes it to the next agent
                    • Memory save: persists every handoff to mem_mrr_prompts

Usage:
    # General use
    agent = await Agent.from_role("Product Manager")
    result = await agent.run("Write acceptance criteria for: ...")

    # Pipeline / orchestrated use
    agent = await Agent.from_role("Web Developer")
    result = await agent.run_pipeline(task="Implement X", handoff=pm_output, project="myproject")
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from core.logger import get_logger
from core.prompt_loader import prompts

log = get_logger(__name__)

_CTX_CAP = 3000   # chars per prior-node output injected into user message
_OBS_CAP = 4000   # max chars of a single tool observation sent back to the LLM


def _calc_cost(provider: str, model: str | None, input_tok: int, output_tok: int) -> float:
    """Return estimated USD cost; never raises."""
    try:
        from agents.providers.pr_costs import estimate_cost
        return estimate_cost(provider, model or provider, input_tok, output_tok)
    except Exception:
        return 0.0

# ── ReAct base injected into EVERY pipeline agent system prompt ────────────────
# Role-specific content (job, must-nots, output format) lives in each YAML.
# This base is prepended by run_pipeline() automatically.
_REACT_SYSTEM_BASE: str = prompts.content("react_pipeline_base") or """\
You are an AgentDesk AI agent. You operate in a strict ReAct loop.

## ReAct Rules
- ALWAYS write Thought: before any action
- ONE action per step — never batch multiple tool calls
- ALWAYS wait for the Observation before the next Thought
- NEVER assume a tool result — wait for the actual observation
- NEVER fabricate file contents, test results, or memory
- If unsure, call a tool. Never guess.

## Anti-Hallucination Rules
- If you don't know something, say "I need to check this" and call a tool
- Never describe code you haven't read this session
- Never claim tests pass without running them or reading diff output
- Never reference a past decision unless memory confirms it exists
- If memory returns empty, say "no relevant memory found" — don't invent context
- If a tool fails, reason about why before retrying

## Handoff Rules
- Your final output MUST be a structured JSON object (no markdown fences)
- Never pass raw conversation — only structured, verified facts
- Include "confidence" (0.0–1.0) reflecting how certain you are
- Include "memory_references" citing exactly what memory returned
- Include your "role" field so the next agent knows who produced this
"""

# ── Simpler suffix used for run() (non-pipeline) ──────────────────────────────
_REACT_SUFFIX: str = prompts.content("react_suffix") or """\
## Reasoning Format

When using tools, follow this pattern:

Thought: [what you need to find out or do, and why]
Action: [call the tool]
Observation: [result — filled in automatically]

Repeat Thought/Action/Observation as needed. When you have sufficient
information, write your final output directly."""

# Tools allowed in planning phase (read-only research)
_PLANNING_TOOLS = frozenset({
    "search_memory", "get_project_facts", "get_tag_context",
    "search_features", "read_file", "list_dir", "git_diff",
})

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_LOAD_ROLE = """SELECT ar.system_prompt, ar.provider, ar.model,
                          COALESCE(
                            string_agg(sr.content, E'\\n\\n' ORDER BY rl.order_index),
                            ''
                          ) AS sys_content,
                          COALESCE(ar.tools, '[]'::jsonb),
                          COALESCE(ar.react, TRUE),
                          COALESCE(ar.max_iterations, 10),
                          ar.temperature
                   FROM   mng_agent_roles ar
                   LEFT JOIN mng_role_system_links rl ON rl.role_id = ar.id
                   LEFT JOIN mng_system_roles sr ON sr.id = rl.system_role_id
                   WHERE  ar.name = %s AND ar.client_id = 1
                   GROUP  BY ar.id, ar.system_prompt, ar.provider, ar.model,
                             ar.tools, ar.react, ar.max_iterations, ar.temperature
                   LIMIT 1"""

_SQL_SAVE_INTERACTION = """INSERT INTO mem_mrr_prompts
    (project_id, source, session_id, content, metadata, created_at)
    VALUES (%s, %s, %s, %s, %s::jsonb, NOW())"""


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ReactStep:
    """One Thought → Action → Observation cycle in the ReAct loop."""
    step_num: int
    thought: str                   # text the model wrote before the tool call
    action_name: str               # tool name
    action_args: dict              # tool input
    observation: str               # tool result
    hallucination_guard_fired: bool = False


@dataclass
class AgentResult:
    output: str                                    # raw text output
    structured_output: dict | None = None          # parsed JSON handoff (pipeline mode)
    steps: list[ReactStep] = field(default_factory=list)  # ReAct trace
    tool_calls_made: list = field(default_factory=list)
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    status: str = "done"   # "done" | "loop_detected" | "max_steps_reached" | "error"
    error: str | None = None


class Agent:
    """LLM agent combining a DB role, a provider, optional tools, and an agentic loop."""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        provider: str,
        model: str,
        tools: list[dict] | None = None,
        react: bool = False,
        max_iterations: int = 10,
        temperature: float | None = None,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.provider = provider
        self.model = model
        self.tools = tools or []
        self.react = react
        self.max_iterations = max_iterations
        self.temperature = temperature

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    async def from_role(
        cls,
        role_name: str,
        with_tools: bool = False,
    ) -> "Agent":
        """Load from mng_agent_roles + mng_system_roles JOIN.

        Falls back to a sensible default when DB is unavailable or role is not found.
        Respects tools/react/max_iterations from the DB.
        """
        from core.database import db
        from core.config import settings

        system_prompt  = f"You are a {role_name}."
        provider       = "claude"
        model          = settings.haiku_model
        role_tool_names: list[str] = []
        react          = True
        max_iterations = 10
        temperature: float | None = None

        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(_SQL_LOAD_ROLE, (role_name,))
                        row = cur.fetchone()
                        if row:
                            base            = row[0] or ""
                            provider        = row[1] or "claude"
                            model           = row[2] or settings.haiku_model
                            sys_content     = row[3] or ""
                            role_tool_names = row[4] or []
                            react           = bool(row[5])
                            max_iterations  = int(row[6] or 10)
                            temperature     = float(row[7]) if row[7] is not None else None
                            system_prompt   = (
                                f"{base}\n\n{sys_content}".strip() if sys_content else base
                            )
            except Exception as e:
                log.debug("Agent.from_role DB error for '%s': %s", role_name, e)

        # YAML fallback: if DB has no tools configured, scan template YAMLs by name field
        if not role_tool_names:
            try:
                import yaml as _yaml
                from pathlib import Path as _Path
                _roles_dir = (
                    _Path(__file__).parent.parent.parent
                    / "workspace" / "_templates" / "pipelines" / "roles"
                )
                for _yp in _roles_dir.glob("role_*.yaml"):
                    try:
                        _yd = _yaml.safe_load(_yp.read_text())
                        if _yd and _yd.get("name", "").strip() == role_name.strip():
                            role_tool_names = _yd.get("tools") or []
                            if role_tool_names:
                                log.info(
                                    "Agent.from_role '%s': YAML tools fallback (%s) → %s",
                                    role_name, _yp.name, role_tool_names,
                                )
                            break
                    except Exception:
                        continue
            except Exception as _ye:
                log.debug("Agent.from_role YAML fallback failed for '%s': %s", role_name, _ye)

        log.info("Agent.from_role '%s': provider=%s model=%s tools=%s",
                 role_name, provider, model, role_tool_names or [])

        # Build tool definitions filtered to this role's allowed tool list
        tools: list[dict] = []
        if with_tools or role_tool_names:
            from agents.tools import AGENT_TOOLS, ALL_TOOL_DEFS
            if role_tool_names:
                tools = [
                    AGENT_TOOLS[t]["definition"]
                    for t in role_tool_names
                    if t in AGENT_TOOLS
                ]
            elif with_tools:
                tools = ALL_TOOL_DEFS

        return cls(
            name=role_name,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            tools=tools,
            react=react,
            max_iterations=max_iterations,
            temperature=temperature,
        )

    # ── Prompt construction ───────────────────────────────────────────────────

    def build_prompt(
        self,
        task: str,
        handoff: dict | None = None,
    ) -> tuple[str, list[dict]]:
        """Build (system_prompt, messages) for pipeline mode.

        System = _REACT_SYSTEM_BASE + role-specific system_prompt.
        Handoff from previous agent is injected as structured JSON in the user message.
        """
        system = f"{_REACT_SYSTEM_BASE}\n\n{self.system_prompt}".strip()

        user_parts = [f"## Task\n{task}"]
        if handoff:
            user_parts.append(
                f"## Input from previous agent\n```json\n{json.dumps(handoff, indent=2)}\n```"
            )

        messages = [{"role": "user", "content": "\n\n".join(user_parts)}]
        return system, messages

    # ── Response parsing helpers ───────────────────────────────────────────────

    @staticmethod
    def _extract_thought(content: str) -> str:
        """Return the text portion of a response (before/between tool calls)."""
        return (content or "").strip()

    @staticmethod
    def _parse_structured_output(content: str) -> dict | None:
        """Try to extract a JSON handoff object from the final response text.

        Handles both raw JSON and JSON wrapped in markdown fences.
        Returns the dict only if it looks like a structured handoff
        (has 'role' or 'confidence' or 'verdict' or 'work_items').
        """
        if not content:
            return None
        # Strip markdown fences
        text = content.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if fence:
            text = fence.group(1).strip()
        # Find first { ... } block
        start = text.find("{")
        if start == -1:
            return None
        try:
            data = json.loads(text[start:])
            if isinstance(data, dict) and (
                "role" in data or "confidence" in data
                or "verdict" in data or "work_items" in data
            ):
                return data
        except (json.JSONDecodeError, ValueError):
            pass
        return None

    @staticmethod
    def _detect_loop(steps: list[ReactStep]) -> bool:
        """Return True if the EXACT same tool call (tool + args) was made 3× in a row.

        Calling the same tool with different arguments is valid (e.g., searching memory
        once per work item).  Only identical tool+args repeated 3 times is a loop.
        """
        if len(steps) < 3:
            return False
        last = steps[-3:]
        tools = [s.action_name for s in last]
        if len(set(tools)) != 1:
            return False
        # Same tool — also require identical args to confirm it's truly stuck
        import json as _json
        def _sig(s: "ReactStep") -> str:
            try:
                return _json.dumps(s.action_args or {}, sort_keys=True)
            except Exception:
                return ""
        sigs = [_sig(s) for s in last]
        return len(set(sigs)) == 1

    # ── Memory save ───────────────────────────────────────────────────────────

    async def _save_to_memory(
        self,
        task: str,
        output: dict,
        project: str,
    ) -> None:
        """Persist the agent's structured handoff to mem_mrr_prompts."""
        from core.database import db
        import uuid
        if not db.is_available():
            return
        try:
            content = json.dumps(output)
            metadata = json.dumps({
                "task": task[:500],
                "role": self.name,
                "agent_handoff": True,
                "tags": [self.name.lower().replace(" ", "_"), "handoff", "react-output"],
            })
            session_id = str(uuid.uuid4())
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_SAVE_INTERACTION,
                        (project_id, f"agent:{self.name}", session_id, content, metadata),
                    )
                conn.commit()
            log.debug("Agent '%s' saved handoff to mem_mrr_prompts (project=%s)", self.name, project)
        except Exception as e:
            log.warning("Agent '%s' failed to save to memory: %s", self.name, e)

    # ── LLM dispatch ──────────────────────────────────────────────────────────

    async def _call_provider(
        self,
        messages: list[dict],
        max_tokens: int,
        api_key: str | None,
        system_override: str | None = None,
    ) -> dict:
        """Dispatch to the correct provider and return a standard response dict."""
        system = system_override if system_override is not None else self.system_prompt

        t = self.temperature  # None = use provider default

        if self.provider in ("claude", "anthropic", ""):
            from agents.providers.pr_claude import call_claude
            return await call_claude(
                messages, system=system,
                model=self.model, tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key, temperature=t,
            )
        elif self.provider == "openai":
            from agents.providers.pr_openai import call_openai
            return await call_openai(
                messages, system=system,
                model=self.model, tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key, temperature=t,
            )
        elif self.provider == "deepseek":
            from agents.providers.pr_deepseek import call_deepseek
            return await call_deepseek(
                messages, system=system,
                tools=self.tools or None,
                max_tokens=max_tokens, api_key=api_key, temperature=t,
            )
        elif self.provider == "gemini":
            from agents.providers.pr_gemini import call_gemini
            user_text = " ".join(
                m["content"] for m in messages if m.get("role") == "user"
                and isinstance(m.get("content"), str)
            )
            return await call_gemini(
                user_text, system=system,
                model=self.model, api_key=api_key, temperature=t,
            )
        elif self.provider == "grok":
            from agents.providers.pr_grok import call_grok
            return await call_grok(
                messages, system=system,
                model=self.model, max_tokens=max_tokens, api_key=api_key, temperature=t,
            )
        else:
            raise ValueError(f"Unknown provider: {self.provider!r} for agent '{self.name}'")

    # ── Standard agentic loop (used by graph nodes, work-item pipeline) ───────

    async def run(
        self,
        user_msg: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> AgentResult:
        """Run the agent with an optional context dict.

        Standard loop: context injection → provider call → tool dispatch → repeat.
        Uses simple _REACT_SUFFIX (not the full _REACT_SYSTEM_BASE).
        """
        from data.dl_api_keys import get_key
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

        # Inject ReAct reasoning suffix if configured
        effective_system = self.system_prompt
        if self.react and self.tools:
            effective_system = self.system_prompt + "\n\n" + _REACT_SUFFIX

        for _ in range(self.max_iterations + 1):
            resp = await self._call_provider(messages, max_tokens, api_key,
                                             system_override=effective_system)
            total_input  += resp.get("input_tokens", 0)
            total_output += resp.get("output_tokens", 0)

            tool_calls  = resp.get("tool_calls", [])
            stop_reason = resp.get("stop_reason", "end_turn")

            if stop_reason != "tool_use" or not tool_calls:
                cost = _calc_cost(self.provider, self.model, total_input, total_output)
                return AgentResult(
                    output=resp.get("content", ""),
                    tool_calls_made=tool_calls_made,
                    cost_usd=cost,
                    input_tokens=total_input,
                    output_tokens=total_output,
                )

            from agents.tools import invoke_tool
            _raw = resp.get("raw")
            messages.append({"role": "assistant", "content": _raw.content if hasattr(_raw, "content") else resp.get("content", "")})
            tool_results: list[dict] = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    tool_name  = tc.get("name", "")
                    tool_input = tc.get("input", {})
                    tool_id    = tc.get("id", "")
                else:
                    tool_name  = getattr(tc, "name",  "") or ""
                    tool_input = getattr(tc, "input", None)
                    if tool_input is None: tool_input = {}
                    tool_id    = getattr(tc, "id",    "") or ""
                result_text = invoke_tool(tool_name, tool_input)
                if len(result_text) > _OBS_CAP:
                    result_text = result_text[:_OBS_CAP] + f"\n[...truncated {len(result_text)-_OBS_CAP} chars]"
                tool_calls_made.append({"name": tool_name, "input": tool_input})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result_text,
                })
            messages.append({"role": "user", "content": tool_results})

        cost = _calc_cost(self.provider, self.model, total_input, total_output)
        return AgentResult(
            output=resp.get("content", ""),
            tool_calls_made=tool_calls_made,
            cost_usd=cost,
            input_tokens=total_input,
            output_tokens=total_output,
            status="max_steps_reached",
        )

    # ── Pipeline ReAct loop ────────────────────────────────────────────────────

    async def run_pipeline(
        self,
        task: str,
        handoff: dict | None = None,
        project: str = "agentdesk",
        max_tokens: int = 4096,
        api_key: str | None = None,
        planning_mode: bool = False,
        system_suffix: str | None = None,
    ) -> AgentResult:
        """ReAct-enforced pipeline run with structured handoff.

        Differences from run():
        - Uses _REACT_SYSTEM_BASE + role prompt as system (full anti-hallucination rules)
        - Tracks Thought/Action/Observation as ReactSteps
        - Hallucination guard: injects a warning if model calls a tool without a Thought
        - Loop detection: aborts if same tool called 3× in a row
        - Parses final response as structured JSON handoff
        - Saves structured output to mem_mrr_prompts (memory)

        planning_mode: restrict tools to read-only set and inject planning instructions
        system_suffix: additional text appended to system prompt (e.g. execution phase context)
        """
        from data.dl_api_keys import get_key
        from agents.tools import invoke_tool

        if api_key is None:
            api_key = get_key(self.provider) or get_key("claude")

        # Planning mode: filter tools to read-only + inject planning suffix
        original_tools = self.tools
        if planning_mode:
            self.tools = [t for t in self.tools if t.get("name") in _PLANNING_TOOLS]
            planning_suffix = (
                "\n\n## PLANNING PHASE\n"
                "Do NOT call write_file, git_commit, or git_push. "
                "Research the codebase and produce a detailed code plan. "
                "Include 'phase': 'planning' in your JSON output."
            )
            system_suffix = (system_suffix or "") + planning_suffix

        system, messages = self.build_prompt(task, handoff)

        # Inject system_suffix (planning phase or execution phase context)
        if system_suffix:
            system = system + "\n" + system_suffix

        steps: list[ReactStep] = []
        tool_calls_made: list[dict] = []
        total_input = total_output = 0
        hallucination_guard_count = 0
        _MAX_GUARD_RETRIES = 3
        resp: dict = {}

        log.info(
            "Agent '%s' starting pipeline run (project=%s, max_iter=%d, planning_mode=%s)",
            self.name, project, self.max_iterations, planning_mode,
        )

        for iteration in range(self.max_iterations + 1):
            resp = await self._call_provider(messages, max_tokens, api_key,
                                             system_override=system)
            total_input  += resp.get("input_tokens", 0)
            total_output += resp.get("output_tokens", 0)

            tool_calls  = resp.get("tool_calls", [])
            stop_reason = resp.get("stop_reason", "end_turn")
            content     = resp.get("content", "")  # text portion of response

            # ── Terminal turn ──────────────────────────────────────────────────
            if stop_reason != "tool_use" or not tool_calls:
                structured = self._parse_structured_output(content)

                # ── Force-JSON step ────────────────────────────────────────────
                # If the model ended on a "Thought:" continuation without emitting
                # JSON, inject one more user turn demanding the output JSON now.
                if not structured and steps:
                    _raw = resp.get("raw")
                    _assistant_content = _raw.content if (
                        _raw and hasattr(_raw, "content")
                    ) else content
                    messages.append({"role": "assistant", "content": _assistant_content})
                    messages.append({
                        "role": "user",
                        "content": (
                            "You have finished your research. "
                            "Do NOT call any more tools. "
                            "Output ONLY the required JSON object right now based on "
                            "everything you found. No Thought: prefix, no markdown fences — "
                            "just the raw JSON."
                        ),
                    })
                    resp2 = await self._call_provider(
                        messages, max_tokens, api_key, system_override=system
                    )
                    total_input  += resp2.get("input_tokens", 0)
                    total_output += resp2.get("output_tokens", 0)
                    content2 = resp2.get("content", "")
                    structured = self._parse_structured_output(content2)
                    if structured:
                        content = content2
                        log.info(
                            "Agent '%s' force-JSON succeeded on extra turn",
                            self.name,
                        )
                    else:
                        log.warning(
                            "Agent '%s' force-JSON failed — structured_out will be None",
                            self.name,
                        )

                log.info(
                    "Agent '%s' finished: %d steps, structured=%s, tokens=%d/%d",
                    self.name, len(steps), bool(structured), total_input, total_output,
                )
                if structured:
                    await self._save_to_memory(task, structured, project)

                cost = _calc_cost(self.provider, self.model, total_input, total_output)
                return AgentResult(
                    output=content,
                    structured_output=structured,
                    steps=steps,
                    tool_calls_made=tool_calls_made,
                    cost_usd=cost,
                    input_tokens=total_input,
                    output_tokens=total_output,
                    status="done",
                )

            # ── Hallucination guard ────────────────────────────────────────────
            # The model called a tool but wrote no reasoning text first.
            if not content.strip() and hallucination_guard_count < _MAX_GUARD_RETRIES:
                hallucination_guard_count += 1
                log.warning(
                    "Agent '%s' step %d: tool call without Thought — firing hallucination guard (%d/%d)",
                    self.name, iteration, hallucination_guard_count, _MAX_GUARD_RETRIES,
                )
                # Anthropic requires every tool_use to be followed by tool_result blocks.
                # Satisfy each tool_use with a tool_result error, so the message
                # history remains valid, then continue so the model retries with a Thought.
                _raw = resp.get("raw")
                messages.append({"role": "assistant", "content": _raw.content if hasattr(_raw, "content") else []})
                guard_results = []
                for tc in tool_calls:
                    tid = getattr(tc, "id", "") if not isinstance(tc, dict) else tc.get("id", "")
                    guard_results.append({
                        "type": "tool_result",
                        "tool_use_id": tid,
                        "content": (
                            "Tool call skipped — you must write 'Thought: [your reasoning]' "
                            "before every tool call. Please restart your response with a Thought."
                        ),
                    })
                messages.append({"role": "user", "content": guard_results})
                continue  # re-call LLM — don't execute the tool yet

            # ── Loop detection ─────────────────────────────────────────────────
            if self._detect_loop(steps):
                log.error(
                    "Agent '%s' loop detected at step %d — requesting JSON output",
                    self.name, iteration,
                )
                # Satisfy pending tool calls so messages history is valid, then
                # inject a JSON-demand turn before giving up.
                _raw_loop = resp.get("raw")
                messages.append({
                    "role": "assistant",
                    "content": _raw_loop.content if (
                        _raw_loop and hasattr(_raw_loop, "content")
                    ) else content,
                })
                _loop_tool_results = []
                for tc in tool_calls:
                    tid = getattr(tc, "id", "") if not isinstance(tc, dict) else tc.get("id", "")
                    _loop_tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tid,
                        "content": "Loop detected — tool call skipped.",
                    })
                messages.append({"role": "user", "content": _loop_tool_results})
                messages.append({
                    "role": "assistant",
                    "content": "Understood — I will stop calling tools and produce the final output.",
                })
                messages.append({
                    "role": "user",
                    "content": (
                        "You have been calling the same tool repeatedly. Stop now. "
                        "Based on everything you have found so far, output ONLY the "
                        "required JSON object. No Thought:, no markdown fences."
                    ),
                })
                resp_loop = await self._call_provider(
                    messages, max_tokens, api_key, system_override=system
                )
                total_input  += resp_loop.get("input_tokens", 0)
                total_output += resp_loop.get("output_tokens", 0)
                loop_content  = resp_loop.get("content", "")
                loop_struct   = self._parse_structured_output(loop_content)
                if loop_struct:
                    await self._save_to_memory(task, loop_struct, project)
                    log.info("Agent '%s' recovered from loop — got structured output", self.name)
                else:
                    log.warning("Agent '%s' loop recovery failed — no structured output", self.name)
                cost = _calc_cost(self.provider, self.model, total_input, total_output)
                return AgentResult(
                    output=loop_content if loop_struct else content,
                    structured_output=loop_struct,
                    steps=steps,
                    tool_calls_made=tool_calls_made,
                    cost_usd=cost,
                    input_tokens=total_input,
                    output_tokens=total_output,
                    status="done" if loop_struct else "loop_detected",
                    error=None if loop_struct else f"Loop at step {iteration}",
                )

            # ── Execute tools ──────────────────────────────────────────────────
            thought = self._extract_thought(content)
            _raw = resp.get("raw")
            messages.append({"role": "assistant", "content": _raw.content if hasattr(_raw, "content") else resp.get("content", "")})
            tool_results: list[dict] = []

            for tc in tool_calls:
                if isinstance(tc, dict):
                    tool_name  = tc.get("name", "")
                    tool_input = tc.get("input", {})
                    tool_id    = tc.get("id", "")
                else:
                    tool_name  = getattr(tc, "name",  "") or ""
                    tool_input = getattr(tc, "input", None)
                    if tool_input is None: tool_input = {}
                    tool_id    = getattr(tc, "id",    "") or ""

                log.debug("Agent '%s' step %d — tool: %s, args: %s",
                          self.name, iteration, tool_name, json.dumps(tool_input)[:200])

                observation = invoke_tool(tool_name, tool_input)
                obs_for_llm = (
                    observation if len(observation) <= _OBS_CAP
                    else observation[:_OBS_CAP] + f"\n[...truncated {len(observation)-_OBS_CAP} chars]"
                )
                tool_calls_made.append({"name": tool_name, "input": tool_input})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": obs_for_llm,
                })

                steps.append(ReactStep(
                    step_num=len(steps) + 1,
                    thought=thought,
                    action_name=tool_name,
                    action_args=tool_input,
                    observation=observation[:2000],  # cap for storage
                    hallucination_guard_fired=(hallucination_guard_count > 0),
                ))
                thought = ""  # only first tool in batch gets the thought

            messages.append({"role": "user", "content": tool_results})

        # Max iterations exceeded
        log.warning("Agent '%s' exceeded max_iterations=%d", self.name, self.max_iterations)
        self.tools = original_tools  # restore before returning
        cost = _calc_cost(self.provider, self.model, total_input, total_output)
        return AgentResult(
            output=resp.get("content", ""),
            steps=steps,
            tool_calls_made=tool_calls_made,
            cost_usd=cost,
            input_tokens=total_input,
            output_tokens=total_output,
            status="max_steps_reached",
            error=f"Exceeded {self.max_iterations} iterations",
        )
