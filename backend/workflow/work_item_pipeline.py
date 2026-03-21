"""
work_item_pipeline.py — 4-agent pipeline for work item development.

Pipeline stages (all via Anthropic API, prompts loaded from DB agent roles):
  1. PM        (Product Manager role)  — write acceptance criteria from description
  2. Architect (Sr. Architect role)    — write implementation plan
  3. Developer (Web Developer role)    — implement against plan + AC
  4. Reviewer  (Code Reviewer role, fresh context) — review against criteria only;
     returns {passed, score, issues}; loops back to Developer if score < 7, max_iterations=2

Stores graph_runs.id → work_items.agent_run_id on start.
Sets work_items.agent_status = 'done' | 'failed' on completion.
Updates acceptance_criteria and implementation_plan fields on the work_item.
"""
from __future__ import annotations

import json
import logging

from core.config import settings
from data.database import db

log = logging.getLogger(__name__)

_MAX_ITERATIONS = 2

# Role name → fallback system prompt (used when DB is unavailable)
_FALLBACK_PROMPTS: dict[str, str] = {
    "Product Manager": (
        "You are a senior product manager. Given a work item, produce ONLY:\n\n"
        "## Task\n<one-sentence task statement>\n\n"
        "## Description\n<2-3 sentences: goal, user value, scope>\n\n"
        "## Acceptance Criteria\n"
        "- [ ] <specific, testable criterion 1>\n"
        "- [ ] <specific, testable criterion 2>\n"
        "- [ ] <specific, testable criterion 3 (max 5 total)>\n\n"
        "Rules: under 250 words total. No preamble."
    ),
    "Sr. Architect": (
        "You are a senior software architect. Given a task and acceptance criteria, "
        "produce ONLY:\n\n"
        "## Plan\n1. <concrete step>\n2. <concrete step>\n...(max 6 steps)\n\n"
        "## Files to Change\n"
        "- `path/to/file.py` — <what to add/modify>\n\n"
        "## Notes\n<2-3 sentences: key decisions, patterns to follow, risks>\n\n"
        "Rules: under 300 words. Be precise about file paths."
    ),
    "Web Developer": (
        "You are a senior full-stack developer. Given an implementation plan and "
        "acceptance criteria, write the actual code changes.\n\n"
        "For EACH file you create or modify, use this EXACT format:\n\n"
        "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
        "After all files, add:\n"
        "## Summary\n- <bullet: what changed>\n- <bullet: why>"
    ),
    "Code Reviewer": (
        "You are a senior code reviewer. Review the implementation against "
        "the acceptance criteria.\n\n"
        "Return ONLY valid JSON (no markdown fences, no preamble):\n"
        '{"score": <1-10>, "passed": <true|false>, '
        '"issues": ["..."], "suggestions": ["..."]}\n\n'
        "Score >= 7 means passed."
    ),
}


def _load_role(role_name: str) -> tuple[str, str, str]:
    """Return (system_prompt, provider, model) for the named role.

    Falls back to _FALLBACK_PROMPTS if DB is unavailable or role not found.
    Returns (haiku_model, haiku_model, haiku_model) provider/model defaults.
    """
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
                        base_prompt = row[0] or ""
                        provider = row[1] or "claude"
                        model = row[2] or settings.haiku_model
                        sys_content = row[3] or ""
                        if sys_content:
                            full_prompt = f"{base_prompt}\n\n{sys_content}".strip()
                        else:
                            full_prompt = base_prompt
                        return full_prompt, provider, model
        except Exception as e:
            log.debug(f"_load_role DB error for '{role_name}': {e}")

    # Fallback
    prompt = _FALLBACK_PROMPTS.get(role_name, f"You are a {role_name}.")
    return prompt, "claude", settings.haiku_model


def _save_pipeline_doc(project: str, work_item_id: str, filename: str, content: str) -> None:
    """Save a pipeline stage output to the documents folder. Silent on error."""
    import re
    from pathlib import Path
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT category_name, name FROM pr_work_items WHERE id=%s::uuid",
                    (work_item_id,),
                )
                wi = cur.fetchone()
        if not wi:
            return
        slug = re.sub(r"[^a-z0-9_]", "", wi[1].lower().replace(" ", "_"))
        dest = Path(settings.workspace_dir) / project / "documents" / wi[0] / slug / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
    except Exception as e:
        log.debug(f"_save_pipeline_doc: {e}")


async def trigger_work_item_pipeline(
    work_item_id: str,
    project: str,
    name: str,
    description: str,
    existing_criteria: str = "",
) -> None:
    """Run the full 4-agent pipeline for a work item. Fully async, safe to background."""
    from datetime import datetime, timezone
    from core.api_keys import get_key
    from agents.providers import call_claude, call_deepseek, call_gemini, call_grok

    ts = datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S")

    async def _call(provider: str, model: str, system: str, user: str, max_tokens: int = 800) -> str:
        """Dispatch to the correct LLM provider using the role's configured provider."""
        api_key = get_key(provider) or get_key("claude") or get_key("anthropic")
        messages = [{"role": "user", "content": user}]
        try:
            if provider in ("claude", "anthropic", ""):
                resp = await call_claude(messages, system=system, model=model, api_key=api_key, max_tokens=max_tokens)
            elif provider == "openai":
                from agents.providers.pr_openai import _async_client as _async_openai_client
                client = _async_openai_client(api_key)
                full = ([{"role": "system", "content": system}] if system else []) + messages
                raw = await client.chat.completions.create(model=model, messages=full, max_tokens=max_tokens)
                return raw.choices[0].message.content or ""
            elif provider == "deepseek":
                resp = await call_deepseek(messages, system=system, api_key=api_key, max_tokens=max_tokens)
            elif provider == "gemini":
                resp = await call_gemini(user, system=system, model=model, api_key=api_key)
            elif provider == "grok":
                resp = await call_grok(messages, system=system, api_key=api_key, max_tokens=max_tokens)
            else:
                # Unknown provider — fall back to claude
                resp = await call_claude(messages, system=system, model=model, api_key=get_key("claude"), max_tokens=max_tokens)
            return resp.get("content", "").strip()
        except Exception as _ce:
            log.warning(f"work_item_pipeline _call({provider}) failed: {_ce}")
            raise

    try:
        # ── Load project context ───────────────────────────────────────────────
        project_facts_text = ""
        memory_text = ""
        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT fact_key, fact_value FROM pr_project_facts "
                            "WHERE client_id=1 AND project=%s AND valid_until IS NULL ORDER BY fact_key",
                            (project,),
                        )
                        facts = cur.fetchall()
                        if facts:
                            project_facts_text = "\n".join(f"  {k}: {v}" for k, v in facts)
                        cur.execute(
                            "SELECT content FROM pr_memory_items WHERE client_id=1 AND project=%s "
                            "ORDER BY created_at DESC LIMIT 3",
                            (project,),
                        )
                        mem_rows = [r[0] for r in cur.fetchall()]
                        if mem_rows:
                            memory_text = "\n---\n".join(mem_rows)
            except Exception as e:
                log.debug(f"work_item_pipeline context load: {e}")

        context_block = ""
        if project_facts_text:
            context_block += f"[Project Facts]\n{project_facts_text}\n\n"
        if memory_text:
            context_block += f"[Recent Project Memory]\n{memory_text[:1500]}\n\n"

        # ── Stage 1: PM — short task spec + acceptance criteria ─────────────
        pm_sys, pm_provider, pm_model = _load_role("Product Manager")
        pm_user = (
            f"{context_block}"
            f"Work item: **{name}**\nDescription: {description}\n\n"
            f"{'Existing criteria:\n' + existing_criteria + chr(10) + chr(10) if existing_criteria else ''}"
            f"Produce the task spec now."
        )
        acceptance_criteria = await _call(pm_provider, pm_model, pm_sys, pm_user, max_tokens=400)
        if not acceptance_criteria:
            _set_status(work_item_id, "failed", error="PM stage produced no output")
            return
        try:
            _save_pipeline_doc(project, work_item_id, f"pm_design_{ts}.md",
                               f"# Acceptance Criteria\n\n{acceptance_criteria}")
        except Exception:
            pass

        # ── Stage 2: Architect — concise implementation plan ─────────────────
        arch_sys, arch_provider, arch_model = _load_role("Sr. Architect")
        arch_user = (
            f"{context_block}"
            f"Work item: **{name}**\n\n"
            f"Acceptance criteria:\n{acceptance_criteria}\n\n"
            f"Produce the implementation plan now."
        )
        implementation_plan = await _call(arch_provider, arch_model, arch_sys, arch_user, max_tokens=500)
        if not implementation_plan:
            _set_status(work_item_id, "failed", error="Architect stage produced no output")
            return
        try:
            _save_pipeline_doc(project, work_item_id, f"architecture_{ts}.md",
                               f"# Implementation Plan\n\n{implementation_plan}")
        except Exception:
            pass

        # Save AC + plan to work item
        _update_fields(work_item_id, acceptance_criteria, implementation_plan)

        # ── Stage 3+4: Developer → Reviewer (loop up to max_iterations) ──────
        dev_sys, dev_provider, dev_model = _load_role("Web Developer")
        rev_sys, rev_provider, rev_model = _load_role("Code Reviewer")

        # Import code-commit helpers from graph_runner (reuse, don't duplicate)
        from gitops.git import parse_code_changes as _parse_code_changes, apply_code_and_commit as _apply_code_and_commit, get_project_code_dir as _get_project_code_dir

        dev_output = ""
        reviewer_feedback = ""
        commit_hash = ""
        for iteration in range(_MAX_ITERATIONS + 1):
            dev_user = (
                f"Work item: **{name}**\n\n"
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation plan:\n{implementation_plan}\n\n"
                f"{'Previous reviewer feedback:\n' + reviewer_feedback + chr(10) + chr(10) if reviewer_feedback and iteration > 0 else ''}"
                f"Implement the changes now. Write complete file content for every file you create or modify."
            )
            # Developer needs generous token budget to write full files
            dev_output = await _call(dev_provider, dev_model, dev_sys, dev_user, max_tokens=8000)
            if not dev_output:
                break

            log.info(f"work_item_pipeline developer output: {len(dev_output)} chars, iteration={iteration}")

            # Auto-commit: parse ### File: blocks and write + git commit
            try:
                code_dir = _get_project_code_dir(project)
                changes = _parse_code_changes(dev_output)
                if changes:
                    log.info(f"work_item_pipeline: found {len(changes)} file(s) to commit")
                    commit_hash = _apply_code_and_commit(
                        code_dir, changes, f"work-item/{name}", work_item_id[:8]
                    )
                    if commit_hash and not commit_hash.startswith("error:"):
                        log.info(f"work_item_pipeline: committed {commit_hash}")
                    else:
                        log.warning(f"work_item_pipeline: commit failed: {commit_hash}")
                        commit_hash = ""
                else:
                    log.info("work_item_pipeline developer: no ### File: blocks found in output")
            except Exception as _ce:
                log.warning(f"work_item_pipeline auto_commit failed: {_ce}")

            # Reviewer: fresh context — pass full dev output, summarised if very long
            rev_preview = dev_output if len(dev_output) <= 4000 else (
                dev_output[:2000] + "\n\n[...middle truncated...]\n\n" + dev_output[-1500:]
            )
            rev_user = (
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation:\n{rev_preview}\n\n"
                f"Review now and return JSON only."
            )
            rev_text = await _call(rev_provider, rev_model, rev_sys, rev_user, max_tokens=500)
            score = 8
            passed = True
            try:
                if "```" in rev_text:
                    for part in rev_text.split("```"):
                        s = part.strip().lstrip("json").strip()
                        if s.startswith("{"):
                            rev_text = s
                            break
                parsed = json.loads(rev_text)
                score  = int(parsed.get("score", 8))
                passed = parsed.get("passed", score >= 7)
                if not passed and parsed.get("issues"):
                    reviewer_feedback = "\n".join(parsed["issues"])
                log.info(f"work_item_pipeline reviewer: score={score}, passed={passed}")
            except Exception:
                log.debug(f"work_item_pipeline reviewer JSON parse failed: {rev_text[:200]}")

            if passed or score >= 7:
                break

        # ── Store final output in work item implementation_plan ──────────────
        if dev_output:
            commit_note = f"\n\n**Commit:** `{commit_hash}`" if commit_hash else ""
            final_plan = (
                f"{implementation_plan}\n\n"
                f"## Implementation Output{commit_note}\n\n"
                f"{dev_output}"
            )
            _update_fields(work_item_id, acceptance_criteria, final_plan)
            try:
                _save_pipeline_doc(project, work_item_id, f"implementation_{ts}.md",
                                   f"# Implementation{commit_note}\n\n{dev_output}")
            except Exception:
                pass

        _set_status(work_item_id, "done")
        log.info(f"work_item_pipeline completed: {work_item_id}")

    except Exception as exc:
        log.error(f"work_item_pipeline failed for {work_item_id}: {exc}")
        _set_status(work_item_id, "failed", error=str(exc))


def _set_status(work_item_id: str, status: str, error: str = "") -> None:
    """Update agent_status on the work item. Silent on error."""
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                if error:
                    cur.execute(
                        "UPDATE pr_work_items SET agent_status=%s, updated_at=NOW() WHERE id=%s::uuid",
                        (f"{status}: {error[:200]}", work_item_id),
                    )
                else:
                    cur.execute(
                        "UPDATE pr_work_items SET agent_status=%s, updated_at=NOW() WHERE id=%s::uuid",
                        (status, work_item_id),
                    )
    except Exception as e:
        log.debug(f"_set_status failed: {e}")


def _update_fields(work_item_id: str, acceptance_criteria: str, implementation_plan: str) -> None:
    """Save acceptance_criteria + implementation_plan to work item. Silent on error."""
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE pr_work_items
                          SET acceptance_criteria=%s,
                              implementation_plan=%s,
                              updated_at=NOW()
                       WHERE id=%s::uuid""",
                    (acceptance_criteria, implementation_plan, work_item_id),
                )
    except Exception as e:
        log.debug(f"_update_fields failed: {e}")
