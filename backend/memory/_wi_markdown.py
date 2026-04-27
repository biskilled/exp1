"""_wi_markdown.py — Markdown file management mixin for MemoryWorkItems.

Contains all methods related to reading/writing use-case MD files,
parsing MD content, and the use-case completion lifecycle.

Mixed into MemoryWorkItems via class inheritance.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from core.config import settings
from core.database import db
from memory._wi_helpers import _use_case_slug, _embed_work_item

log = logging.getLogger(__name__)


class _MarkdownMixin:
    """Markdown file management methods — read, write, parse, complete, reopen."""

    def _status_label(self, score_status: int) -> str:
        if not score_status or score_status == 0:
            return "requirement"
        if score_status >= 5:
            return "done"
        return "in_progress"

    def get_md(self, item_id: str, pid: int) -> str:
        """Render a use_case work item as clean Markdown (no HTML comment tags).

        Uses a recursive CTE to capture all descendants (not just direct children).
        Format is designed to be human-editable — save_md() parses it back to DB.
        """
        if not db.is_available():
            return ""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT wi_id, name, summary, score_status, created_at, updated_at
                           FROM mem_work_items
                           WHERE id=%s::uuid AND project_id=%s""",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return ""
                    wi_id, name, summary, score_status, created_at, updated_at = row
                    created_str = created_at.strftime("%Y-%m-%d") if created_at else ""
                    updated_str = updated_at.strftime("%Y-%m-%d") if updated_at else ""

                    # Recursive CTE — all descendants, excluding deleted/rejected
                    cur.execute(
                        """WITH RECURSIVE descendants AS (
                             SELECT id, wi_id, wi_type, name, summary,
                                    COALESCE(user_status, score_status, 0) AS eff_status,
                                    0 AS depth
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.wi_type, w.name, w.summary,
                                    COALESCE(w.user_status, w.score_status, 0),
                                    d.depth + 1
                             FROM mem_work_items w
                             JOIN descendants d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                               AND d.depth < 20
                           )
                           SELECT wi_id, wi_type, name, summary, eff_status
                           FROM descendants
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'
                           ORDER BY wi_id""",
                        (item_id, pid, pid),
                    )
                    cols = [d[0] for d in cur.description]
                    all_items = [dict(zip(cols, r)) for r in cur.fetchall()]

            _TYPE_LABEL = {
                "bug": "bug", "feature": "feature", "task": "task",
                "policy": "policy", "requirement": "requirement", "use_case": "use case",
            }
            _TYPE_ORDER = ["bug", "feature", "task", "requirement", "policy"]

            req_items  = [c for c in all_items if c["wi_type"] == "requirement"]
            work_items = [c for c in all_items if c["wi_type"] != "requirement"]

            done_items = [c for c in work_items if (c["eff_status"] or 0) >= 5]
            open_items = [c for c in work_items if (c["eff_status"] or 0) < 5]

            type_counts: dict[str, int] = {}
            for c in all_items:
                type_counts[c["wi_type"]] = type_counts.get(c["wi_type"], 0) + 1
            stat_parts = [
                f"{type_counts[t]} {_TYPE_LABEL.get(t, t)}{'s' if type_counts[t] != 1 else ''}"
                for t in _TYPE_ORDER if t in type_counts
            ]
            stats_str = " · ".join(stat_parts) if stat_parts else "no items"

            def _item_block(ch: dict) -> list[str]:
                wid   = ch["wi_id"] or "pending"
                lines = [f"#### {wid} — {ch['name']}"]
                if ch.get("summary"):
                    lines += ["", ch["summary"]]
                return lines

            def _group_section(items: list) -> list[str]:
                _ORDER = ["bug", "feature", "task", "policy"]
                _SKIP  = {"requirement", "use_case"}
                by_type: dict = {}
                for c in items:
                    if c["wi_type"] not in _SKIP:
                        by_type.setdefault(c["wi_type"], []).append(c)
                lines: list[str] = []
                for t in _ORDER + [k for k in by_type if k not in _ORDER]:
                    grp = by_type.get(t, [])
                    if not grp:
                        continue
                    t_plural = _TYPE_LABEL.get(t, t).capitalize() + "s"
                    if lines:
                        lines.append("")
                    lines += [f"### {t_plural} ({len(grp)})", ""]
                    for i, ch in enumerate(grp):
                        lines += _item_block(ch)
                        if i < len(grp) - 1:
                            lines.append("")
                return lines

            req_lines: list[str] = []
            if req_items:
                for r in req_items:
                    req_lines += _item_block(r)
                    req_lines.append("")
            else:
                req_lines += ["_Add requirements here_", ""]

            L: list[str] = [
                f"# {wi_id or 'pending'} — {name}",
                "",
                f"created: {created_str} | updated: {updated_str} | {stats_str}",
                "",
                "## Summary",
                "",
                summary or "_No summary yet. Click ⟳ Summarise in the Use Cases tab to generate._",
                "",
                "## Requirements",
                "",
            ]
            L += req_lines

            L += ["---", "", f"## Completed ({len(done_items)})", ""]
            if done_items:
                L += _group_section(done_items)
                L.append("")
            else:
                L += ["_No completed items yet._", ""]

            L += ["---", "", f"## Open Items ({len(open_items)})", ""]
            if open_items:
                L += _group_section(open_items)
            else:
                L += ["_No open items._"]

            return "\n".join(L)
        except Exception as e:
            log.warning(f"get_md({item_id}) error: {e}")
            return ""

    @staticmethod
    def _parse_md_items(content: str) -> dict[str, dict]:
        """Parse #### WKID — title blocks from MD content.

        Returns {wi_id: {'name': str, 'summary': str}}.
        """
        items: dict[str, dict] = {}
        current_id: Optional[str] = None
        current_name: str = ""
        current_lines: list[str] = []
        skip_type_line: bool = False

        for line in content.splitlines():
            if line.startswith("## ") or line.startswith("---"):
                if current_id:
                    items[current_id] = {
                        "name": current_name,
                        "summary": "\n".join(current_lines).strip(),
                    }
                current_id = None
                current_lines = []
                skip_type_line = False
                continue
            m = re.match(r'^#### (\S+) — (.+)$', line)
            if m:
                if current_id:
                    items[current_id] = {
                        "name": current_name,
                        "summary": "\n".join(current_lines).strip(),
                    }
                current_id   = m.group(1)
                current_name = m.group(2).strip()
                current_lines = []
                skip_type_line = True
                continue
            if skip_type_line:
                if re.match(r'^\*\w+\*$', line.strip()):
                    skip_type_line = False
                    continue
                if line.strip() == "":
                    skip_type_line = False
            if current_id:
                current_lines.append(line)

        if current_id:
            items[current_id] = {
                "name": current_name,
                "summary": "\n".join(current_lines).strip(),
            }
        return items

    def save_md(self, item_id: str, pid: int, content: str) -> dict:
        """Parse MD content and persist changes to DB + file.

        Syncs:
          - ## Summary section → UC summary field
          - #### WKID — title blocks → child name + summary
          - Items removed from MD → marked deleted_at=NOW() (approved) or deleted (pending)
        """
        if not db.is_available():
            return {"error": "db not available"}

        updated = 0
        deleted_count = 0
        embedded = 0
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # 1. UC summary
                    summary_match = re.search(
                        r'## Summary\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL
                    )
                    if summary_match:
                        new_summary = summary_match.group(1).strip()
                        if new_summary.startswith("_No summary"):
                            new_summary = ""
                        cur.execute(
                            "UPDATE mem_work_items SET summary=%s, updated_at=NOW() "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (new_summary, item_id, pid),
                        )
                        if cur.rowcount:
                            updated += 1

                    # 2. Parse all #### WKID blocks from the file
                    md_items = self._parse_md_items(content)

                    # 3. Load all DB children (non-deleted, non-rejected)
                    cur.execute(
                        """WITH RECURSIVE tree AS (
                             SELECT id, wi_id, wi_type, name, summary, 0 AS depth
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.wi_type, w.name, w.summary,
                                    d.depth + 1
                             FROM mem_work_items w JOIN tree d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                               AND d.depth < 20
                           )
                           SELECT id::text, wi_id, wi_type, name, summary
                           FROM tree
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%'""",
                        (item_id, pid, pid),
                    )
                    db_children = {
                        r[1]: {"id": r[0], "wi_type": r[2], "name": r[3], "summary": r[4]}
                        for r in cur.fetchall()
                    }

                    # 4. Update items present in MD, mark missing ones as deleted
                    for wi_id_key, db_child in db_children.items():
                        if wi_id_key in md_items:
                            md = md_items[wi_id_key]
                            new_name    = md["name"]
                            new_summary = md["summary"]
                            if new_name != db_child["name"] or new_summary != (db_child["summary"] or ""):
                                cur.execute(
                                    """UPDATE mem_work_items
                                       SET name=%s, summary=%s, updated_at=NOW()
                                       WHERE wi_id=%s AND project_id=%s""",
                                    (new_name, new_summary, wi_id_key, pid),
                                )
                                if cur.rowcount:
                                    updated += 1
                        else:
                            if wi_id_key.startswith("AI"):
                                cur.execute(
                                    "DELETE FROM mem_work_items WHERE wi_id=%s AND project_id=%s",
                                    (wi_id_key, pid),
                                )
                            else:
                                cur.execute(
                                    "UPDATE mem_work_items SET deleted_at=NOW(), updated_at=NOW() "
                                    "WHERE wi_id=%s AND project_id=%s",
                                    (wi_id_key, pid),
                                )
                            deleted_count += 1

                conn.commit()

            # Re-embed UC (summary may have changed)
            try:
                with db.conn() as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute(
                            "SELECT name, wi_type, summary FROM mem_work_items "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (item_id, pid),
                        )
                        uc_row = cur2.fetchone()
                if uc_row:
                    _embed_work_item(item_id, {
                        "name": uc_row[0], "wi_type": uc_row[1], "summary": uc_row[2] or ""
                    })
                    embedded += 1
            except Exception:
                pass

            self._write_md_file(item_id, pid, content)

            return {"updated": updated, "deleted": deleted_count, "embedded": embedded}
        except Exception as e:
            log.warning(f"save_md({item_id}) error: {e}")
            return {"error": str(e)}

    def refresh_md(self, item_id: str, pid: int) -> str:
        """Ensure the MD file exists. Generates from DB only if file not yet created."""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if row:
                slug    = _use_case_slug(row[0])
                uc_path = Path(settings.workspace_dir) / self.project / "documents" / "use_cases" / f"{slug}.md"  # type: ignore[attr-defined]
                if uc_path.exists():
                    return uc_path.read_text(encoding="utf-8")
        except Exception:
            pass
        content = self.get_md(item_id, pid)
        if content:
            self._write_md_file(item_id, pid, content)
        return content

    def _write_md_file(self, item_id: str, pid: int, content: str) -> None:
        """Write MD content to workspace/{project}/documents/use_cases/{slug}.md."""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
            if not row:
                return
            slug   = _use_case_slug(row[0])
            uc_dir = Path(settings.workspace_dir) / self.project / "documents" / "use_cases"  # type: ignore[attr-defined]
            uc_dir.mkdir(parents=True, exist_ok=True)
            (uc_dir / f"{slug}.md").write_text(content, encoding="utf-8")
            log.debug(f"_write_md_file({item_id}): wrote {slug}.md → {uc_dir}")
        except Exception as e:
            log.debug(f"_write_md_file({item_id}) error: {e}")

    def _move_md_file(self, name: str, from_folder: str, to_folder: str) -> None:
        """Move a use-case MD file between documents sub-folders."""
        try:
            slug    = _use_case_slug(name)
            base    = Path(settings.workspace_dir) / self.project / "documents"  # type: ignore[attr-defined]
            src     = base / from_folder / f"{slug}.md"
            dst_dir = base / to_folder
            dst_dir.mkdir(parents=True, exist_ok=True)
            if src.exists():
                src.rename(dst_dir / f"{slug}.md")
        except Exception as e:
            log.debug(f"_move_md_file({name}) error: {e}")

    def complete_use_case(self, item_id: str, pid: int) -> dict:
        """Mark a use case as completed.

        Validates all recursive descendants have eff_status >= 5, then sets
        completed_at = NOW() and moves the MD file to documents/completed/.
        """
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT wi_id, name FROM mem_work_items "
                        "WHERE id=%s::uuid AND project_id=%s AND wi_type='use_case'",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "use case not found"}
                    wi_id, name = row

                    cur.execute(
                        """WITH RECURSIVE tree AS (
                             SELECT id, wi_id, name,
                                    COALESCE(user_status, score_status, 0) AS eff,
                                    0 AS depth
                             FROM mem_work_items
                             WHERE wi_parent_id=%s::uuid AND project_id=%s
                               AND deleted_at IS NULL
                           UNION ALL
                             SELECT w.id, w.wi_id, w.name,
                                    COALESCE(w.user_status, w.score_status, 0),
                                    d.depth + 1
                             FROM mem_work_items w JOIN tree d ON w.wi_parent_id = d.id
                             WHERE w.project_id=%s AND w.deleted_at IS NULL
                               AND d.depth < 20
                           )
                           SELECT name FROM tree
                           WHERE wi_id IS NOT NULL AND wi_id NOT LIKE 'REJ%%' AND eff < 5
                           LIMIT 10""",
                        (item_id, pid, pid),
                    )
                    incomplete = [r[0] for r in cur.fetchall()]
                    if incomplete:
                        return {
                            "error": "not all items completed",
                            "incomplete": incomplete,
                        }

                    cur.execute(
                        "UPDATE mem_work_items SET completed_at=NOW(), updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                conn.commit()

            self._move_md_file(name, "use_cases", "completed")
            return {"completed": True, "wi_id": wi_id}
        except Exception as e:
            log.warning(f"complete_use_case({item_id}) error: {e}")
            return {"error": str(e)}

    def reopen_use_case(self, item_id: str, pid: int) -> dict:
        """Reopen a completed use case — clears completed_at, moves MD back."""
        if not db.is_available():
            return {"error": "db not available"}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT name FROM mem_work_items WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                    row = cur.fetchone()
                    if not row:
                        return {"error": "use case not found"}
                    name = row[0]
                    cur.execute(
                        "UPDATE mem_work_items SET completed_at=NULL, updated_at=NOW() "
                        "WHERE id=%s::uuid AND project_id=%s",
                        (item_id, pid),
                    )
                conn.commit()
            self._move_md_file(name, "completed", "use_cases")
            return {"reopened": True}
        except Exception as e:
            log.warning(f"reopen_use_case({item_id}) error: {e}")
            return {"error": str(e)}

    def get_completed_use_cases(self, pid: int) -> list[dict]:
        """Return all completed use cases with summary, dates, total_days."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT id::text, wi_id, name, summary,
                                  start_date, completed_at,
                                  CASE WHEN start_date IS NOT NULL
                                       THEN (completed_at::date - start_date)
                                       ELSE NULL END AS total_days
                           FROM mem_work_items
                           WHERE project_id=%s AND wi_type='use_case'
                             AND completed_at IS NOT NULL
                           ORDER BY completed_at DESC""",
                        (pid,),
                    )
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            result = []
            for r in rows:
                d = dict(zip(cols, r))
                for k in ("start_date", "completed_at"):
                    if d.get(k):
                        d[k] = d[k].isoformat() if hasattr(d[k], 'isoformat') else str(d[k])
                if d.get("total_days") is not None:
                    d["total_days"] = int(d["total_days"])
                slug = _use_case_slug(d["name"])
                d["md_path"] = f"completed/{slug}.md"
                result.append(d)
            return result
        except Exception as e:
            log.warning(f"get_completed_use_cases error: {e}")
            return []
