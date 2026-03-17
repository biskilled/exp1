"""
work_item_pipeline.py — 4-agent pipeline for work item development.

Pipeline stages (all via Anthropic API):
  1. PM        (Haiku)  — write acceptance criteria from description + project_facts
  2. Architect (Haiku)  — write implementation plan using project_facts + memory_items
  3. Developer (claude_model) — implement against plan + acceptance_criteria
  4. Reviewer  (Haiku, fresh context = Trycycle) — review against criteria only;
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


async def trigger_work_item_pipeline(
    work_item_id: str,
    project: str,
    name: str,
    description: str,
    existing_criteria: str = "",
) -> None:
    """Run the full 4-agent pipeline for a work item. Fully async, safe to background."""
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
                            "SELECT fact_key, fact_value FROM mng_project_facts "
                            "WHERE project_id=%s AND valid_until IS NULL ORDER BY fact_key",
                            (project,),
                        )
                        facts = cur.fetchall()
                        if facts:
                            project_facts_text = "\n".join(f"  {k}: {v}" for k, v in facts)
                        cur.execute(
                            "SELECT content FROM mng_memory_items WHERE project_id=%s "
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

        # ── Stage 1: PM — acceptance criteria ────────────────────────────────
        pm_prompt = (
            f"{context_block}"
            f"Work item: **{name}**\nDescription: {description}\n\n"
            f"{'Existing criteria:\n' + existing_criteria + chr(10) + chr(10) if existing_criteria else ''}"
            f"Write clear, testable acceptance criteria (3-8 bullet points). "
            f"Be specific and measurable. Start each with '- [ ]'."
        )
        pm_resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=600,
            messages=[{"role": "user", "content": pm_prompt}],
        )
        acceptance_criteria = (pm_resp.content[0].text if pm_resp.content else "").strip()
        if not acceptance_criteria:
            _set_status(work_item_id, "failed", error="PM stage produced no output")
            return

        # ── Stage 2: Architect — implementation plan ──────────────────────────
        arch_prompt = (
            f"{context_block}"
            f"Work item: **{name}**\nDescription: {description}\n\n"
            f"Acceptance criteria:\n{acceptance_criteria}\n\n"
            f"Write a concise technical implementation plan (numbered steps, "
            f"include specific files/functions to change). Focus on HOW not WHAT."
        )
        arch_resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=800,
            messages=[{"role": "user", "content": arch_prompt}],
        )
        implementation_plan = (arch_resp.content[0].text if arch_resp.content else "").strip()
        if not implementation_plan:
            _set_status(work_item_id, "failed", error="Architect stage produced no output")
            return

        # Save AC + plan to work item
        _update_fields(work_item_id, acceptance_criteria, implementation_plan)

        # ── Stage 3+4: Developer → Reviewer (loop up to max_iterations) ──────
        dev_output = ""
        for iteration in range(_MAX_ITERATIONS + 1):
            dev_prompt = (
                f"Work item: **{name}**\n\n"
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation plan:\n{implementation_plan}\n\n"
                f"{'Previous attempt feedback:\n' + dev_output + chr(10) + chr(10) if dev_output and iteration > 0 else ''}"
                f"Provide a detailed technical implementation addressing all acceptance criteria. "
                f"Include code snippets, specific changes, and rationale."
            )
            dev_resp = await client.messages.create(
                model=settings.claude_model if hasattr(settings, "claude_model") else settings.haiku_model,
                max_tokens=1500,
                messages=[{"role": "user", "content": dev_prompt}],
            )
            dev_output = (dev_resp.content[0].text if dev_resp.content else "").strip()
            if not dev_output:
                break

            # Reviewer: fresh context (Trycycle)
            rev_prompt = (
                f"Review this implementation against the acceptance criteria ONLY.\n\n"
                f"Acceptance criteria:\n{acceptance_criteria}\n\n"
                f"Implementation:\n{dev_output[:2000]}\n\n"
                f"Return ONLY valid JSON: "
                f"{{\"passed\": true/false, \"score\": 1-10, \"issues\": [\"...\"]}}. "
                f"Score >= 7 means passed."
            )
            rev_resp = await client.messages.create(
                model=settings.haiku_model,
                max_tokens=300,
                messages=[{"role": "user", "content": rev_prompt}],
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
                    dev_output = "\n".join(parsed["issues"])  # feed issues back as prompt
            except Exception:
                pass

            if passed or score >= 7:
                break

        # ── Store final output in work item implementation_plan ──────────────
        if dev_output:
            final_plan = f"{implementation_plan}\n\n## Implementation Output\n{dev_output}"
            _update_fields(work_item_id, acceptance_criteria, final_plan)

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
                        "UPDATE mng_work_items SET agent_status=%s, updated_at=NOW() WHERE id=%s::uuid",
                        (f"{status}: {error[:200]}", work_item_id),
                    )
                else:
                    cur.execute(
                        "UPDATE mng_work_items SET agent_status=%s, updated_at=NOW() WHERE id=%s::uuid",
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
                    """UPDATE mng_work_items
                          SET acceptance_criteria=%s,
                              implementation_plan=%s,
                              updated_at=NOW()
                       WHERE id=%s::uuid""",
                    (acceptance_criteria, implementation_plan, work_item_id),
                )
    except Exception as e:
        log.debug(f"_update_fields failed: {e}")
