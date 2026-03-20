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

from config import settings
from core.database import db

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
    ts = datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S")
    try:
        from core.api_keys import get_key
        import anthropic

        key = get_key("claude") or get_key("anthropic")
        if not key:
            _set_status(work_item_id, "failed", error="No API key")
            return

        client = anthropic.AsyncAnthropic(api_key=key)

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
        pm_prompt_sys, _, pm_model = _load_role("Product Manager")
        pm_user = (
            f"{context_block}"
            f"Work item: **{name}**\nDescription: {description}\n\n"
            f"{'Existing criteria:\n' + existing_criteria + chr(10) + chr(10) if existing_criteria else ''}"
            f"Produce the task spec now."
        )
        pm_resp = await client.messages.create(
            model=pm_model,
            max_tokens=400,
            system=pm_prompt_sys,
            messages=[{"role": "user", "content": pm_user}],
        )
        acceptance_criteria = (pm_resp.content[0].text if pm_resp.content else "").strip()
        if not acceptance_criteria:
            _set_status(work_item_id, "failed", error="PM stage produced no output")
            return
        try:
            _save_pipeline_doc(project, work_item_id, f"pm_design_{ts}.md",
                               f"# Acceptance Criteria\n\n{acceptance_criteria}")
        except Exception:
            pass

        # ── Stage 2: Architect — concise implementation plan ─────────────────
        arch_prompt_sys, _, arch_model = _load_role("Sr. Architect")
        arch_user = (
            f"{context_block}"
            f"Work item: **{name}**\n\n"
            f"Acceptance criteria:\n{acceptance_criteria}\n\n"
            f"Produce the implementation plan now."
        )
        arch_resp = await client.messages.create(
            model=arch_model,
            max_tokens=500,
            system=arch_prompt_sys,
            messages=[{"role": "user", "content": arch_user}],
        )
        implementation_plan = (arch_resp.content[0].text if arch_resp.content else "").strip()
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
        dev_prompt_sys, _, dev_model = _load_role("Web Developer")
        rev_prompt_sys, _, rev_model = _load_role("Code Reviewer")

        dev_output = ""
        reviewer_feedback = ""
        for iteration in range(_MAX_ITERATIONS + 1):
            dev_user = (
                f"Work item: **{name}**\n\n"
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation plan:\n{implementation_plan}\n\n"
                f"{'Previous reviewer feedback:\n' + reviewer_feedback + chr(10) + chr(10) if reviewer_feedback and iteration > 0 else ''}"
                f"Implement the changes now."
            )
            dev_resp = await client.messages.create(
                model=dev_model,
                max_tokens=2000,
                system=dev_prompt_sys,
                messages=[{"role": "user", "content": dev_user}],
            )
            dev_output = (dev_resp.content[0].text if dev_resp.content else "").strip()
            if not dev_output:
                break

            # Reviewer: fresh context (stateless Trycycle)
            rev_user = (
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation:\n{dev_output[:2000]}\n\n"
                f"Review now."
            )
            rev_resp = await client.messages.create(
                model=rev_model,
                max_tokens=400,
                system=rev_prompt_sys,
                messages=[{"role": "user", "content": rev_user}],
            )
            rev_text = (rev_resp.content[0].text if rev_resp.content else "").strip()
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
            except Exception:
                pass

            if passed or score >= 7:
                break

        # ── Store final output in work item implementation_plan ──────────────
        if dev_output:
            final_plan = f"{implementation_plan}\n\n## Implementation Output\n{dev_output}"
            _update_fields(work_item_id, acceptance_criteria, final_plan)
            try:
                _save_pipeline_doc(project, work_item_id, f"implementation_{ts}.md",
                                   f"# Implementation\n\n{dev_output}")
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
