"""
memory_planner.py — Planner document synthesis for planner_tags.

For a given tag (feature/bug/task), aggregates all linked work items,
their commit history, and interaction stats, then calls Haiku to produce
a concise Markdown document saved under
  {workspace_path}/{project}/documents/{category}/{tag_name}.md

Also syncs acceptance_criteria and action_items back to planner_tags
and each linked mem_ai_work_items row.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

from core.database import db
from core.prompt_loader import prompts as _prompts

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_TAG = """
    SELECT pt.id, pt.name, tc.name AS category_name,
           pt.requirements, pt.action_items, pt.acceptance_criteria, pt.summary
    FROM planner_tags pt
    JOIN mng_tags_categories tc ON tc.id = pt.category_id
    WHERE pt.id = %s::uuid AND pt.project_id = %s
    LIMIT 1
"""

_SQL_GET_WORK_ITEMS = """
    SELECT wi.id, wi.name_ai, wi.desc_ai, wi.status_user, wi.status_ai,
           wi.acceptance_criteria_ai, wi.action_items_ai, wi.summary_ai,
           wi.seq_num, wi.start_date
    FROM mem_ai_work_items wi
    WHERE wi.tag_id_user = %s::uuid AND wi.project_id = %s
      AND wi.merged_into IS NULL
    ORDER BY wi.created_at
"""

_SQL_GET_WI_COMMITS = """
    SELECT commit_hash, commit_msg, summary, tags
    FROM mem_mrr_commits
    WHERE project_id = %s AND tags @> jsonb_build_object('work-item', %s::text)
    ORDER BY committed_at DESC LIMIT 10
"""

_SQL_GET_WI_INTERACTION_STATS = """
    SELECT COUNT(*) AS n_prompts,
           COALESCE(SUM(CHAR_LENGTH(COALESCE(prompt,''))+CHAR_LENGTH(COALESCE(response,''))), 0) AS total_chars
    FROM mem_mrr_prompts
    WHERE project_id = %s AND tags @> jsonb_build_object('work-item', %s::text)
"""

_SQL_UPDATE_TAG = """
    UPDATE planner_tags
    SET summary = %s, action_items = %s, acceptance_criteria = %s,
        updater = 'ai', updated_at = NOW()
    WHERE id = %s::uuid AND project_id = %s
"""

_SQL_UPDATE_WORK_ITEM = """
    UPDATE mem_ai_work_items
    SET action_items_ai = %s, acceptance_criteria_ai = %s, summary_ai = %s, updated_at = NOW()
    WHERE id = %s::uuid AND project_id = %s
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_diff_stat(text: str) -> dict:
    """Extract files changed, lines added/removed from a git diff summary string."""
    files: list[str] = []
    added = 0
    removed = 0
    for line in (text or "").split("\n"):
        fm = re.match(r"^\s*(.+?)\s*\|\s*\d+", line)
        if fm:
            files.append(fm.group(1).strip())
        sm = re.search(r"(\d+) insertions?\(\+\)", line)
        if sm:
            added += int(sm.group(1))
        dm = re.search(r"(\d+) deletions?\(-\)", line)
        if dm:
            removed += int(dm.group(1))
    return {"files": files, "added": added, "removed": removed}


def _get_workspace_path(project: str) -> Path:
    """Return the workspace_path for a project from mng_projects, fallback to settings."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT workspace_path FROM mng_projects WHERE name=%s", (project,)
                )
                row = cur.fetchone()
        if row and row[0]:
            return Path(row[0])
    except Exception as e:
        log.debug(f"_get_workspace_path error: {e}")
    from core.config import settings
    return Path(settings.workspace_dir)


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


async def _call_llm(system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return ""
        import anthropic
        from core.config import settings
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=getattr(settings, "claude_haiku_model", "claude-haiku-4-5-20251001"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_llm error: {e}")
        return ""


_FALLBACK_SYSTEM_PROMPT = """
You are a technical project planner. Given a tag with linked work items and their commit
history, produce a concise planner document.

Return ONLY valid JSON with keys:
- use_case_summary: short paragraph (2-4 sentences) describing purpose and current state
- done_items: list of completed action items (1-2 lines each)
- remaining_items: list of what still needs to be done (1-2 lines each)
- acceptance_criteria: list of testable QA criteria (1 line each)
- work_item_updates: [{id, remaining_action_items, acceptance_criteria, summary (3-4 sentences)}]

Be concise. Per-work-item summary: max 3-4 sentences.
""".strip()


# ── MemoryPlanner ─────────────────────────────────────────────────────────────

class MemoryPlanner:
    """
    Synthesises planner_tags + linked work items into a Markdown document
    and syncs acceptance_criteria / action_items back to the DB.
    """

    async def run_planner(self, project: str, tag_id: str) -> dict:
        """
        Main entry point.  Returns a summary dict including the doc_path and counts.
        """
        if not db.is_available():
            raise RuntimeError("PostgreSQL not available")

        p_id = db.get_or_create_project_id(project)

        # 1. Load tag
        tag = self._load_tag(p_id, tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found in project {project}")

        # 2. Load linked work items
        work_items = self._load_work_items(p_id, tag_id)

        # 3. For each work item load commit stats + interaction stats
        wi_data: list[dict] = []
        for wi in work_items:
            wi_id = str(wi["id"])
            commits = self._load_wi_commits(p_id, wi_id)
            stats = self._load_wi_interaction_stats(p_id, wi_id)

            # Aggregate diff stats across all commits from tags["files"] dict (name→rows_changed)
            all_files: dict[str, bool] = {}
            total_added = 0
            total_removed = 0
            for c in commits:
                ctags = c.get("tags") or {}
                files_tag = ctags.get("files") or {}
                if isinstance(files_tag, dict):
                    for fname in files_tag:
                        all_files[fname] = True

            wi_data.append({
                **wi,
                "id": wi_id,
                "commits": commits,
                "n_commits": len(commits),
                "files": list(all_files.keys()),
                "total_added": total_added,
                "total_removed": total_removed,
                "n_prompts": stats["n_prompts"],
                "words": stats["words"],
            })

        # 4. Build LLM user message
        user_msg = self._build_user_message(tag, wi_data)

        # 5. Call Haiku
        system_prompt = _prompts.content("planner_summary") or _FALLBACK_SYSTEM_PROMPT
        raw = await _call_llm(system_prompt, user_msg, max_tokens=2000)
        parsed = _parse_json(raw)

        if not parsed:
            log.warning(f"MemoryPlanner: LLM returned no parseable JSON for tag {tag_id}")
            parsed = {
                "use_case_summary": "",
                "done_items": [],
                "remaining_items": [],
                "acceptance_criteria": [],
                "work_item_updates": [],
            }

        # 6. Write back to DB
        self._write_tag(p_id, tag_id, parsed)
        wi_updates = parsed.get("work_item_updates") or []
        self._write_work_items(p_id, wi_updates)

        # 7. Write Markdown document
        doc_path = self._write_document(project, tag, wi_data, parsed)

        return {
            "tag_id": tag_id,
            "tag_name": tag["name"],
            "project": project,
            "doc_path": str(doc_path),
            "done_count": len(parsed.get("done_items") or []),
            "remaining_count": len(parsed.get("remaining_items") or []),
            "work_items_updated": len(wi_updates),
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_tag(self, p_id: int, tag_id: str) -> Optional[dict]:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_TAG, (tag_id, p_id))
                row = cur.fetchone()
                if not row:
                    return None
                cols = [d[0] for d in cur.description]
                return dict(zip(cols, row))

    def _load_work_items(self, p_id: int, tag_id: str) -> list[dict]:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORK_ITEMS, (tag_id, p_id))
                cols = [d[0] for d in cur.description]
                rows = []
                for r in cur.fetchall():
                    row = dict(zip(cols, r))
                    row["id"] = str(row["id"])
                    if row.get("start_date"):
                        row["start_date"] = row["start_date"].isoformat()
                    rows.append(row)
                return rows

    def _load_wi_commits(self, p_id: int, wi_id: str) -> list[dict]:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WI_COMMITS, (p_id, wi_id))
                    cols = [d[0] for d in cur.description]
                    return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception:
            return []

    def _load_wi_interaction_stats(self, p_id: int, wi_id: str) -> dict:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WI_INTERACTION_STATS, (p_id, wi_id))
                    row = cur.fetchone()
                    if row:
                        n_prompts = int(row[0] or 0)
                        total_chars = int(row[1] or 0)
                        return {"n_prompts": n_prompts, "words": total_chars // 5}
        except Exception:
            pass
        return {"n_prompts": 0, "words": 0}

    def _build_user_message(self, tag: dict, wi_data: list[dict]) -> str:
        lines = [
            f"TAG: {tag['category_name'].upper()} / {tag['name']}",
            f"Requirements: {tag.get('requirements') or '—'}",
            f"Existing summary: {tag.get('summary') or '—'}",
            f"Existing action_items: {tag.get('action_items') or '—'}",
            f"Existing acceptance_criteria: {tag.get('acceptance_criteria') or '—'}",
            "",
            f"WORK ITEMS ({len(wi_data)} total):",
        ]
        for wi in wi_data:
            lines.append(f"\n--- Work Item #{wi.get('seq_num', '?')}: {wi['name_ai']} ---")
            lines.append(f"ID: {wi['id']}")
            lines.append(f"Status: {wi.get('status_user', 'active')}")
            lines.append(f"Description: {wi.get('desc_ai') or '—'}")
            lines.append(f"Requirements: —")
            lines.append(f"Action items: {wi.get('action_items_ai') or '—'}")
            lines.append(f"Acceptance criteria: {wi.get('acceptance_criteria_ai') or '—'}")
            lines.append(f"Summary: {wi.get('summary_ai') or '—'}")
            lines.append(f"Prompts: {wi['n_prompts']} · ~{wi['words']} words · {wi['n_commits']} commits")
            if wi["files"]:
                lines.append(f"Files changed: {', '.join(wi['files'][:10])}")
            if wi["commits"]:
                lines.append("Recent commits:")
                for c in wi["commits"][:3]:
                    lines.append(f"  - {(c.get('commit_msg') or '')[:80]}")
        return "\n".join(lines)

    def _write_tag(self, p_id: int, tag_id: str, parsed: dict) -> None:
        summary = parsed.get("use_case_summary") or ""
        action_items = "\n".join(parsed.get("remaining_items") or [])
        acceptance_criteria = "\n".join(
            f"- [ ] {c}" for c in (parsed.get("acceptance_criteria") or [])
        )
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPDATE_TAG, (summary, action_items, acceptance_criteria, tag_id, p_id))

    def _write_work_items(self, p_id: int, updates: list[dict]) -> None:
        if not updates:
            return
        with db.conn() as conn:
            with conn.cursor() as cur:
                for u in updates:
                    wi_id = u.get("id")
                    if not wi_id:
                        continue
                    action_items = u.get("remaining_action_items") or ""
                    if isinstance(action_items, list):
                        action_items = "\n".join(action_items)
                    ac = u.get("acceptance_criteria") or ""
                    if isinstance(ac, list):
                        ac = "\n".join(f"- [ ] {c}" for c in ac)
                    summary = u.get("summary") or ""
                    cur.execute(_SQL_UPDATE_WORK_ITEM, (action_items, ac, summary, wi_id, p_id))

    def _write_document(
        self, project: str, tag: dict, wi_data: list[dict], parsed: dict
    ) -> Path:
        ws = _get_workspace_path(project)
        cat_slug = _slugify(tag["category_name"])
        tag_slug = _slugify(tag["name"])
        doc_dir = ws / project / "documents" / cat_slug
        doc_dir.mkdir(parents=True, exist_ok=True)
        doc_path = doc_dir / f"{tag_slug}.md"

        today = date.today().isoformat()
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        # Build files-changed table from all work items
        all_files: dict[str, tuple[int, int]] = {}
        for wi in wi_data:
            for f in wi.get("files") or []:
                prev = all_files.get(f, (0, 0))
                all_files[f] = (
                    prev[0] + wi.get("total_added", 0),
                    prev[1] + wi.get("total_removed", 0),
                )

        # Work items section
        wi_sections: list[str] = []
        for wi in wi_data:
            sd = wi.get("start_date")
            start_str = sd[:10] if sd else "—"
            wi_sections.append(
                f"### #{wi.get('seq_num', '?')} {wi['name_ai']} · {wi.get('status_user', 'active')}\n"
                f"_Prompts: {wi['n_prompts']} · ~{wi['words']:,} words · "
                f"{wi['n_commits']} commits · Started: {start_str}_\n\n"
                f"{wi.get('summary_ai') or wi.get('desc_ai') or ''}\n\n"
                + (
                    f"**Remaining:** {wi.get('action_items_ai') or '—'}\n"
                    if wi.get("action_items_ai")
                    else ""
                )
            )

        done_md = "\n".join(
            f"- {item}" for item in (parsed.get("done_items") or [])
        ) or "— none recorded"
        remaining_md = "\n".join(
            f"- {item}" for item in (parsed.get("remaining_items") or [])
        ) or "— none"
        ac_md = "\n".join(
            f"- [ ] {c}" for c in (parsed.get("acceptance_criteria") or [])
        ) or "— none"

        files_table = "| File | +Added | -Removed |\n|------|--------|------|\n"
        if all_files:
            for fname, (a, r) in list(all_files.items())[:30]:
                files_table += f"| {fname} | +{a} | -{r} |\n"
        else:
            files_table += "| — | — | — |\n"

        content = (
            f"# {tag['category_name']}: {tag['name']}\n"
            f"_Last updated: {today} · Project: {project}_\n\n"
            f"## Use Case Summary\n{parsed.get('use_case_summary') or '—'}\n\n"
            f"## Work Items ({len(wi_data)})\n\n"
            + "\n---\n\n".join(wi_sections)
            + f"\n\n---\n\n## What Was Done\n{done_md}\n\n"
            f"## What Remains\n{remaining_md}\n\n"
            f"## Acceptance Criteria\n{ac_md}\n\n"
            f"## Files Changed\n{files_table}\n"
            f"---\n_Auto-generated by aicli Planner · {ts}_\n"
        )

        doc_path.write_text(content, encoding="utf-8")
        log.info(f"MemoryPlanner: wrote {doc_path}")
        return doc_path
