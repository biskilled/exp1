"""
memory_feature_snapshot.py — Per-tag, per-use-case feature snapshot pipeline.

Merges planner_tags requirements + deliveries + linked work items + recent AI events
into structured mem_ai_feature_snapshot rows (one per use case per version).

Triggered via POST /tags/{id}/snapshot.  AI version ('ai') is overwritten on each run;
user version ('user') is promoted from AI via POST /tags/{id}/snapshot/promote and is
never overwritten by AI.

Output files:
    {code_dir}/features/{tag_name}/feature_ai.md
    {code_dir}/features/{tag_name}/feature_final.md
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.database import db
from core.prompt_loader import prompts as _prompts

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_TAG = """
    SELECT pt.id, pt.name, tc.name AS category_name,
           pt.status, pt.priority, pt.due_date,
           pt.requirements, pt.acceptance_criteria, pt.deliveries
    FROM planner_tags pt
    JOIN mng_tags_categories tc ON tc.id = pt.category_id
    WHERE pt.id = %s::uuid AND pt.project_id = %s
    LIMIT 1
"""

_SQL_GET_WORK_ITEMS = """
    SELECT wi.id, wi.name_ai, wi.desc_ai, wi.status_user,
           wi.action_items_ai, wi.acceptance_criteria_ai, wi.summary_ai
    FROM mem_ai_work_items wi
    WHERE wi.tag_id_user = %s::uuid AND wi.project_id = %s
      AND wi.merged_into IS NULL
    ORDER BY wi.created_at
"""

_SQL_GET_RECENT_EVENTS = """
    SELECT id, event_type, summary, action_items, created_at
    FROM mem_ai_events
    WHERE project_id = %s
      AND event_type IN ('session_summary', 'prompt_batch')
    ORDER BY created_at DESC
    LIMIT 20
"""

_SQL_GET_CODE_DIR = """
    SELECT code_dir FROM mng_projects WHERE name = %s LIMIT 1
"""

_SQL_DELETE_AI_ROWS = """
    DELETE FROM mem_ai_feature_snapshot
    WHERE project_id = %s AND tag_id = %s::uuid AND version = 'ai'
"""

_SQL_DELETE_USER_ROWS = """
    DELETE FROM mem_ai_feature_snapshot
    WHERE project_id = %s AND tag_id = %s::uuid AND version = 'user'
"""

_SQL_INSERT_ROW = """
    INSERT INTO mem_ai_feature_snapshot (
        id, client_id, project_id, tag_id, use_case_num,
        name, category, status, priority, due_date, summary,
        use_case_summary, use_case_type,
        use_case_delivery_category, use_case_delivery_type,
        related_work_items, requirements, action_items, version
    ) VALUES (
        %s, 1, %s, %s::uuid, %s,
        %s, %s, %s, %s, %s, %s,
        %s, %s,
        %s, %s,
        %s::jsonb, %s::jsonb, %s::jsonb, %s
    )
"""

_SQL_GET_AI_ROWS = """
    SELECT id, use_case_num, name, category, status, priority, due_date, summary,
           use_case_summary, use_case_type,
           use_case_delivery_category, use_case_delivery_type,
           related_work_items, requirements, action_items, version, created_at
    FROM mem_ai_feature_snapshot
    WHERE tag_id = %s::uuid AND version = %s
    ORDER BY use_case_num
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

_FALLBACK_SYSTEM = """
You are a technical project analyst. Given a feature tag with work items and events,
return ONLY valid JSON matching this schema:
{
  "summary": "2-4 sentence global feature summary",
  "use_cases": [
    {
      "use_case_num": 1,
      "use_case_summary": "purpose and current state",
      "use_case_type": "feature",
      "use_case_delivery_category": "code",
      "use_case_delivery_type": "python",
      "related_work_item_ids": [],
      "requirements": [{"text": "...", "source": "ai", "score": 0}],
      "action_items": [{"action_item": "...", "acceptance": "...", "score": 0}]
    }
  ]
}
""".strip()


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def _call_llm(system_prompt: str, user_message: str, max_tokens: int = 3000) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            log.warning("_call_llm: no claude/anthropic API key found")
            return ""
        import anthropic
        from core.config import settings
        model = getattr(settings, "claude_haiku_model", "claude-haiku-4-5-20251001")
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_llm error: {e}")
        return ""


# ── MemoryFeatureSnapshot ──────────────────────────────────────────────────────

class MemoryFeatureSnapshot:
    """
    Generates and persists per-use-case feature snapshots for a planner_tag.

    AI rows are overwritten on each run; user rows are promoted once and never
    touched by AI.
    """

    # ── Public entry points ───────────────────────────────────────────────────

    async def run_snapshot(self, project: str, tag_id: str) -> dict:
        """Run AI snapshot for tag_id, write feature_ai.md, return summary dict."""
        if not db.is_available():
            raise RuntimeError("PostgreSQL not available")

        p_id = db.get_or_create_project_id(project)
        code_dir = self._get_code_dir(project)

        # 1. Load tag
        tag = self._load_tag(p_id, tag_id)
        if not tag:
            raise ValueError(f"Tag {tag_id} not found in project {project}")

        # 2. Load work items
        work_items = self._load_work_items(p_id, tag_id)
        wi_by_id = {str(wi["id"]): wi for wi in work_items}

        # 3. Load recent AI events
        events = self._load_recent_events(p_id)

        # 4. Load user baseline (feature_final.md) if exists
        baseline = self._load_baseline(code_dir, tag["name"])

        # 5. Build LLM user message
        user_msg = self._build_user_message(tag, work_items, events, baseline)

        # 6. Call Haiku
        system_prompt = _prompts.content("feature_snapshot_v2") or _FALLBACK_SYSTEM
        raw = await _call_llm(system_prompt, user_msg, max_tokens=3000)
        parsed = _parse_json(raw)

        if not parsed or "use_cases" not in parsed:
            log.warning(f"MemoryFeatureSnapshot: no parseable JSON for tag {tag_id}")
            parsed = {"summary": "", "use_cases": []}

        global_summary = parsed.get("summary", "")
        use_cases: list[dict] = parsed.get("use_cases", [])

        # 7. Resolve related_work_item_ids → full JSONB objects
        rows = self._build_rows(
            p_id, tag, global_summary, use_cases, wi_by_id, version="ai"
        )

        # 8. Persist: delete old ai rows + insert new ones
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_DELETE_AI_ROWS, (p_id, tag_id))
                for row in rows:
                    cur.execute(_SQL_INSERT_ROW, row)

        # 9. Write feature_ai.md
        doc_path = self._write_snapshot_md(code_dir, tag, global_summary, rows, "ai")

        return {
            "tag_id": tag_id,
            "tag_name": tag["name"],
            "use_case_count": len(rows),
            "doc_path": str(doc_path),
            "project": project,
        }

    async def promote_to_user(self, project: str, tag_id: str) -> dict:
        """Copy ai rows to user rows, write feature_final.md, return summary dict."""
        if not db.is_available():
            raise RuntimeError("PostgreSQL not available")

        p_id = db.get_or_create_project_id(project)
        code_dir = self._get_code_dir(project)

        # 1. Fetch ai rows
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_AI_ROWS, (tag_id, "ai"))
                ai_rows = cur.fetchall()

        if not ai_rows:
            raise ValueError(f"No AI snapshot found for tag {tag_id} — run snapshot first")

        # Reconstruct tag metadata from first row
        first = ai_rows[0]
        tag_stub = {
            "id": tag_id,
            "name": first[2],
            "category": first[3],
            "status": first[4],
            "priority": first[5],
            "due_date": first[6],
        }
        global_summary = first[7]

        # 2. Build user insert rows (copy ai rows, change version + ids)
        user_rows = []
        for r in ai_rows:
            (row_id, uc_num, name, category, status, priority, due_date, summary,
             uc_summary, uc_type, uc_del_cat, uc_del_type,
             rel_wi, reqs, actions, _version, _created_at) = r
            user_rows.append((
                str(uuid.uuid4()), p_id, tag_id, uc_num,
                name, category, status, priority, due_date, summary,
                uc_summary, uc_type, uc_del_cat, uc_del_type,
                json.dumps(rel_wi if rel_wi else []),
                json.dumps(reqs if reqs else []),
                json.dumps(actions if actions else []),
                "user",
            ))

        # 3. Delete old user rows + insert new ones
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_DELETE_USER_ROWS, (p_id, tag_id))
                for row in user_rows:
                    cur.execute(_SQL_INSERT_ROW, row)

        # 4. Write feature_final.md
        doc_path = self._write_snapshot_md(code_dir, tag_stub, global_summary, user_rows, "user")

        return {
            "tag_id": tag_id,
            "tag_name": tag_stub["name"],
            "use_case_count": len(user_rows),
            "doc_path": str(doc_path),
        }

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _load_tag(self, p_id: int, tag_id: str) -> dict | None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_TAG, (tag_id, p_id))
                row = cur.fetchone()
        if not row:
            return None
        return {
            "id":               str(row[0]),
            "name":             row[1],
            "category":         row[2],
            "status":           row[3] or "open",
            "priority":         row[4] or 3,
            "due_date":         row[5],
            "requirements":     row[6] or "",
            "acceptance_criteria": row[7] or "",
            "deliveries":       row[8] if row[8] else [],
        }

    def _load_work_items(self, p_id: int, tag_id: str) -> list[dict]:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_WORK_ITEMS, (tag_id, p_id))
                rows = cur.fetchall()
        return [
            {
                "id":                    str(r[0]),
                "name_ai":               r[1] or "",
                "desc_ai":               r[2] or "",
                "status_user":           r[3] or "active",
                "action_items_ai":       r[4] or "",
                "acceptance_criteria_ai": r[5] or "",
                "summary_ai":            r[6] or "",
            }
            for r in rows
        ]

    def _load_recent_events(self, p_id: int) -> list[dict]:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_RECENT_EVENTS, (p_id,))
                rows = cur.fetchall()
        return [
            {
                "id":          str(r[0]),
                "event_type":  r[1],
                "summary":     r[2] or "",
                "action_items": r[3] or "",
                "created_at":  r[4].isoformat() if r[4] else "",
            }
            for r in rows
        ]

    def _get_code_dir(self, project: str) -> Path:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_CODE_DIR, (project,))
                    row = cur.fetchone()
            if row and row[0]:
                return Path(row[0])
        except Exception as e:
            log.debug(f"_get_code_dir error: {e}")
        from core.config import settings
        return Path(getattr(settings, "workspace_dir", "/tmp"))

    # ── Message builder ───────────────────────────────────────────────────────

    def _load_baseline(self, code_dir: Path, tag_name: str) -> str:
        slug = _slugify(tag_name)
        path = code_dir / "features" / slug / "feature_final.md"
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception:
                pass
        return ""

    def _build_user_message(
        self,
        tag: dict,
        work_items: list[dict],
        events: list[dict],
        baseline: str,
    ) -> str:
        parts: list[str] = []

        # Tag section
        deliveries_str = ""
        if tag["deliveries"]:
            deliveries_str = "\n".join(
                f"  - [{d.get('category','')}] {d.get('type','')} — {d.get('label','')}"
                for d in tag["deliveries"]
            )
        parts.append(
            f"## Tag\n"
            f"Name: {tag['name']}\n"
            f"Category: {tag['category']}\n"
            f"Status: {tag['status']}\n"
            f"Priority: {tag['priority']}\n"
            f"Due: {tag['due_date'] or 'not set'}\n\n"
            f"### Requirements\n{tag['requirements'] or '(none)'}\n\n"
            f"### Acceptance Criteria\n{tag['acceptance_criteria'] or '(none)'}\n\n"
            f"### Deliveries\n{deliveries_str or '(none)'}"
        )

        # Work items
        if work_items:
            wi_parts = []
            for wi in work_items:
                wi_parts.append(
                    f"- ID: {wi['id']}\n"
                    f"  Name: {wi['name_ai']}\n"
                    f"  Status: {wi['status_user']}\n"
                    f"  Desc: {wi['desc_ai'][:300]}\n"
                    f"  Summary: {wi['summary_ai'][:300]}\n"
                    f"  Actions: {wi['action_items_ai'][:200]}\n"
                    f"  Acceptance: {wi['acceptance_criteria_ai'][:200]}"
                )
            parts.append("## Work Items\n" + "\n\n".join(wi_parts))
        else:
            parts.append("## Work Items\n(none)")

        # Recent events
        if events:
            ev_parts = []
            for ev in events[:10]:
                ev_parts.append(
                    f"[{ev['created_at'][:10]}] {ev['event_type']}: {ev['summary'][:200]}"
                )
            parts.append("## Recent AI Events\n" + "\n".join(ev_parts))

        # User baseline
        if baseline:
            parts.append(f"## User-confirmed baseline\n{baseline[:3000]}")

        return "\n\n---\n\n".join(parts)

    # ── Row builder ───────────────────────────────────────────────────────────

    def _build_rows(
        self,
        p_id: int,
        tag: dict,
        global_summary: str,
        use_cases: list[dict],
        wi_by_id: dict[str, dict],
        version: str,
    ) -> list[tuple]:
        """Convert LLM use_cases into INSERT tuples."""
        rows = []
        for uc in use_cases:
            uc_num = int(uc.get("use_case_num", len(rows) + 1))

            # Resolve work items
            rel_ids: list[str] = uc.get("related_work_item_ids", [])
            rel_wi_objs = []
            for wid in rel_ids:
                wi = wi_by_id.get(str(wid))
                if wi:
                    rel_wi_objs.append({
                        "id":          wi["id"],
                        "name":        wi["name_ai"],
                        "status_user": wi["status_user"],
                        "summary_ai":  wi["summary_ai"][:200],
                        "score":       0,
                    })

            rows.append((
                str(uuid.uuid4()),          # id
                p_id,                       # project_id
                tag["id"],                  # tag_id
                uc_num,                     # use_case_num
                tag["name"],                # name
                tag["category"],            # category
                tag["status"],              # status
                tag["priority"],            # priority
                tag["due_date"],            # due_date
                global_summary,             # summary
                uc.get("use_case_summary", ""),
                uc.get("use_case_type", "feature"),
                uc.get("use_case_delivery_category", ""),
                uc.get("use_case_delivery_type", ""),
                json.dumps(rel_wi_objs),
                json.dumps(uc.get("requirements", [])),
                json.dumps(uc.get("action_items", [])),
                version,
            ))
        return rows

    # ── Markdown writer ───────────────────────────────────────────────────────

    def _write_snapshot_md(
        self,
        code_dir: Path,
        tag: dict,
        global_summary: str,
        rows: list[tuple],
        version: str,
    ) -> Path:
        slug = _slugify(tag["name"])
        out_dir = code_dir / "features" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = "feature_ai.md" if version == "ai" else "feature_final.md"
        path = out_dir / filename

        version_label = "AI Generated" if version == "ai" else "User Confirmed"
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        due = tag.get("due_date") or "not set"
        if hasattr(due, "isoformat"):
            due = due.isoformat()

        lines = [
            f"# Feature Snapshot: {tag['name']}",
            f"> {tag['category']} | Status: {tag['status']} | Priority: {tag['priority']} | Due: {due}",
            f"> Generated: {ts} | Version: {version_label}",
            "",
            f"## {'(AI) ' if version == 'ai' else '(USER) '}Summary",
            global_summary or "_No summary generated._",
            "",
            "---",
        ]

        for row in rows:
            # row tuple indices from _build_rows / promote_to_user:
            # promote_to_user passes: (new_uuid, p_id, tag_id, uc_num, name, category,
            #   status, priority, due_date, summary, uc_summary, uc_type,
            #   uc_del_cat, uc_del_type, rel_wi_json, reqs_json, actions_json, version)
            # _build_rows passes the same shape
            if len(row) == 18:
                (row_id, r_pid, r_tag_id, uc_num,
                 r_name, r_cat, r_status, r_priority, r_due, r_summary,
                 uc_summary, uc_type, del_cat, del_type,
                 rel_wi_raw, reqs_raw, actions_raw, r_version) = row
            else:
                continue

            # Parse JSONB (may be str or already list)
            rel_wi = json.loads(rel_wi_raw) if isinstance(rel_wi_raw, str) else (rel_wi_raw or [])
            reqs = json.loads(reqs_raw) if isinstance(reqs_raw, str) else (reqs_raw or [])
            actions = json.loads(actions_raw) if isinstance(actions_raw, str) else (actions_raw or [])

            src_label = "(AI)" if version == "ai" else "(USER)"
            del_label = f"{del_type} [{del_cat}]" if del_cat else del_type or "—"

            lines += [
                "",
                f"## Use Case {uc_num}: {uc_type} — {del_label}",
                "",
                f"### {src_label} Use Case Summary",
                uc_summary or "_No summary._",
                "",
            ]

            # Requirements table
            if reqs:
                lines += [
                    "### Requirements",
                    "| # | Requirement | Source | Score |",
                    "|---|-------------|--------|-------|",
                ]
                for i, req in enumerate(reqs, 1):
                    src = "(AI)" if req.get("source") == "ai" else "(USER)"
                    lines.append(
                        f"| {i} | {req.get('text','').replace('|','/')} | {src} | {req.get('score',0)}/10 |"
                    )
                lines.append("")

            # Related work items table
            if rel_wi:
                lines += [
                    "### Related Work Items",
                    "| Name | Status | Summary |",
                    "|------|--------|---------|",
                ]
                for wi in rel_wi:
                    lines.append(
                        f"| {wi.get('name','').replace('|','/')} | {wi.get('status_user','')} "
                        f"| {wi.get('summary_ai','')[:100].replace('|','/')} |"
                    )
                lines.append("")

            # Action items table
            if actions:
                lines += [
                    "### Action Items & Acceptance Criteria",
                    "| # | Action Item | Acceptance Criteria | Score |",
                    "|---|-------------|---------------------|-------|",
                ]
                for i, act in enumerate(actions, 1):
                    lines.append(
                        f"| {i} | {act.get('action_item','').replace('|','/')} "
                        f"| {act.get('acceptance','').replace('|','/')} "
                        f"| {act.get('score',0)}/10 |"
                    )
                lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        log.info(f"_write_snapshot_md: wrote {path}")
        return path
