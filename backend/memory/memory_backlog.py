"""
memory_backlog.py — File-based backlog pipeline for the aicli memory system.

Replaces the mem_ai_events → mem_ai_work_items DB pipeline with a simpler
file-based system.  The pipeline reads raw mem_mrr_* rows, calls Claude Haiku
to produce structured digest entries, and appends them to documents/backlog.md.

Public API::

    bl = MemoryBacklog(project)

    # called after each new row insert (threshold-based trigger)
    await bl.check_and_trigger("commits")

    # flush all unprocessed rows for a source type
    await bl.process_pending("prompts")

    # flush all source types (called by /memory and /work_items)
    await bl.process_all_pending()

    # parse current backlog.md into structured entries
    entries = bl.parse_backlog()

    # rewrite backlog.md keeping/archiving entries
    bl.rewrite(keep=[...], processed=[...], rejected=[...])

    # full pipeline: flush → approve → create/merge use cases
    result = await run_work_items(project)
"""
from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from core.config import settings
from core.database import db

log = logging.getLogger(__name__)

# ── Source-type → prefix mapping ──────────────────────────────────────────────

_PREFIX: dict[str, str] = {
    "prompts":  "P",
    "commits":  "C",
    "messages": "M",
    "items":    "I",
}

_TABLE: dict[str, str] = {
    "prompts":  "mem_mrr_prompts",
    "commits":  "mem_mrr_commits",
    "messages": "mem_mrr_messages",
    "items":    "mem_mrr_items",
}

# Template location (relative to project root)
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "workspace" / "_templates" / "backlog_config.yaml"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _claude_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("claude") or get_key("anthropic") or None
    except Exception:
        return None


def _log_usage(model: str, input_tokens: int, output_tokens: int) -> None:
    try:
        from core.auth import ADMIN_USER_ID
        _RATES = {
            "claude-haiku-4-5-20251001": (0.00025, 0.00125),
            "claude-haiku-4-5":          (0.00025, 0.00125),
        }
        in_r, out_r = _RATES.get(model, (0.00025, 0.00125))
        cost = (input_tokens * in_r + output_tokens * out_r) / 1000.0
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_usage_logs
                       (user_id, provider, model, input_tokens, output_tokens,
                        cost_usd, charged_usd, source)
                       VALUES (%s, 'claude', %s, %s, %s, %s, 0, 'backlog')""",
                    (ADMIN_USER_ID, model, input_tokens, output_tokens, cost),
                )
    except Exception as _e:
        log.debug(f"_log_usage error: {_e}")


async def _call_haiku(system: str, user: str, model: str, max_tokens: int = 2000) -> str:
    """Call Claude Haiku and return raw text.  Returns '' on failure."""
    key = _claude_key()
    if not key:
        return ""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
        resp = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if hasattr(resp, "usage"):
            _log_usage(
                model,
                getattr(resp.usage, "input_tokens", 0),
                getattr(resp.usage, "output_tokens", 0),
            )
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_call_haiku error: {e}")
        return ""


def _get_code_dir(project: str) -> Optional[Path]:
    try:
        from gitops.git import get_project_code_dir
        cd = get_project_code_dir(project)
        return Path(cd) if cd else None
    except Exception:
        return None


# ── Entry format helpers ───────────────────────────────────────────────────────

_ENTRY_HEADER_RE = re.compile(
    r"^###\s+([PCMI]\d+)\s+(\d{4}/\d{2}/\d{2})\s+—\s+(.+)$"
)
_APPROVE_RE  = re.compile(r"<!--\s*APPROVE:\s*\[([ x\-])\]\s*-->")
_TAG_RE      = re.compile(r"<!--\s*TAG:\s*(.*?)\s*-->")
_MATCH_RE    = re.compile(r"<!--\s*AI_MATCH:\s*(existing|new|none):(\S*)\s*-->")


def _fmt_entry(item: dict) -> str:
    """Render a digest dict into the backlog.md markdown block."""
    ref_id   = item.get("ref_id", "")
    d        = item.get("date", date.today().strftime("%Y/%m/%d"))
    summary  = item.get("summary", "")
    classify = item.get("classify", "task")
    ai_match = item.get("ai_match", {})
    match_type = ai_match.get("type", "none")
    match_slug = ai_match.get("slug", "")

    reqs = item.get("requirements", [])
    reqs_txt = "; ".join(str(r) for r in reqs) if reqs else ""

    deliveries = item.get("deliveries", [])
    del_lines = "\n".join(
        f"  `{d.get('desc','')}` ({d.get('type','')})" for d in deliveries
    )

    action_items = item.get("action_items", [])
    ai_lines = "\n".join(
        f"- [ ] {a.get('desc','')} (acceptance: {a.get('acceptance','')})"
        for a in action_items
    )

    lines = [
        f"### {ref_id} {d} — {summary}",
        "",
        "<!-- APPROVE: [ ] -->",
        "<!-- TAG: -->",
        f"<!-- AI_MATCH: {match_type}:{match_slug} -->",
        f"<!-- AI_CLASSIFY: {classify} -->",
        "",
    ]
    if reqs_txt:
        lines.append(f"**Requirements:** {reqs_txt}")
    if del_lines:
        lines.append(f"**Deliveries:**\n{del_lines}")
    if ai_lines:
        lines.append(f"**Action items:**\n{ai_lines}")
    lines.append("")
    return "\n".join(lines)


# ── Main class ────────────────────────────────────────────────────────────────

class MemoryBacklog:
    """File-based backlog pipeline: mem_mrr_* → backlog.md → use_cases/*.md."""

    def __init__(self, project: str) -> None:
        self.project   = project
        self.project_id: Optional[int] = None
        self._cfg: Optional[dict] = None

    # ── Config ─────────────────────────────────────────────────────────────────

    def _config(self) -> dict:
        if self._cfg is not None:
            return self._cfg
        code_dir = _get_code_dir(self.project)
        if code_dir:
            cfg_path = code_dir / ".ai" / "backlog_config.yaml"
        else:
            cfg_path = Path(settings.workspace_dir) / self.project / ".ai" / "backlog_config.yaml"

        if not cfg_path.exists():
            # Auto-copy template on first run
            try:
                cfg_path.parent.mkdir(parents=True, exist_ok=True)
                if _TEMPLATE_PATH.exists():
                    shutil.copy2(_TEMPLATE_PATH, cfg_path)
                    log.info(f"backlog_config: copied template → {cfg_path}")
            except Exception as e:
                log.debug(f"backlog_config template copy error: {e}")

        try:
            self._cfg = yaml.safe_load(cfg_path.read_text()) or {} if cfg_path.exists() else {}
        except Exception as e:
            log.debug(f"backlog_config read error: {e}")
            self._cfg = {}

        return self._cfg

    def _source_cfg(self, source_type: str) -> dict:
        return self._config().get("mirroring_event_summary", {}).get(source_type, {})

    def _cnt(self, source_type: str) -> int:
        return int(self._source_cfg(source_type).get("cnt", 99999))

    def _backlog_path(self) -> Path:
        code_dir = _get_code_dir(self.project)
        cfg = self._config()
        fname = cfg.get("file_name", "backlog.md")
        if cfg.get("rotation"):
            today = date.today().strftime("%Y-%m-%d")
            fname = f"backlog_{today}.md"
        base = code_dir if code_dir else Path(settings.workspace_dir) / self.project
        return base / "documents" / fname

    def _use_cases_dir(self) -> Path:
        code_dir = _get_code_dir(self.project)
        base = code_dir if code_dir else Path(settings.workspace_dir) / self.project
        return base / "documents" / "use_cases"

    def _get_project_id(self) -> Optional[int]:
        if self.project_id:
            return self.project_id
        if not db.is_available():
            return None
        try:
            self.project_id = db.get_or_create_project_id(self.project)
            return self.project_id
        except Exception:
            return None

    # ── Pending count ──────────────────────────────────────────────────────────

    def _pending_count(self, source_type: str) -> int:
        project_id = self._get_project_id()
        if not project_id:
            return 0
        table = _TABLE.get(source_type)
        if not table:
            return 0
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    return cur.fetchone()[0] or 0
        except Exception as e:
            log.debug(f"_pending_count({source_type}) error: {e}")
            return 0

    # ── Threshold check ────────────────────────────────────────────────────────

    async def check_and_trigger(self, source_type: str) -> None:
        """Called after each new row insert.  Process when pending >= cnt threshold."""
        cnt = self._cnt(source_type)
        pending = self._pending_count(source_type)
        if pending >= cnt:
            log.info(
                f"backlog: {pending} pending {source_type} >= threshold {cnt}, processing"
            )
            await self.process_pending(source_type)

    # ── Core digest loop ───────────────────────────────────────────────────────

    async def process_pending(self, source_type: str) -> int:
        """Load pending rows, call Haiku, append to backlog.md, mark rows processed.

        Returns number of entries appended.
        """
        project_id = self._get_project_id()
        if not project_id:
            return 0

        table  = _TABLE.get(source_type)
        prefix = _PREFIX.get(source_type)
        if not table or not prefix:
            log.warning(f"backlog: unknown source_type '{source_type}'")
            return 0

        # Load all pending rows
        rows = self._fetch_pending_rows(source_type, project_id)
        if not rows:
            return 0

        # Load active use case summaries for matching context
        uc_context = self._load_use_case_context()

        # Prompt config
        src_cfg  = self._source_cfg(source_type)
        p_cfg    = src_cfg.get("prompt", {})
        model    = p_cfg.get("llm", settings.haiku_model)
        p_desc   = p_cfg.get("desc", "Summarize and classify each item.")
        cnt      = self._cnt(source_type)

        appended = 0
        # Process in batches of cnt
        for batch_start in range(0, len(rows), max(cnt, 1)):
            batch = rows[batch_start : batch_start + cnt]

            # Allocate ref IDs
            ref_ids = self._allocate_refs(project_id, prefix, len(batch))
            if not ref_ids:
                log.warning(f"backlog: failed to allocate {len(batch)} ref IDs for {prefix}")
                break

            # Format input for Haiku
            formatted = self._format_rows(source_type, batch)

            # Build prompt
            system_prompt = self._build_system_prompt(p_desc, uc_context)
            user_prompt   = self._build_user_prompt(source_type, formatted, ref_ids)

            # Call Haiku
            raw = await _call_haiku(system_prompt, user_prompt, model, max_tokens=3000)

            # Parse JSON response
            items = self._parse_haiku_response(raw, ref_ids, source_type)

            # Append to backlog.md
            self._append_to_backlog(items)
            appended += len(items)

            # Mark rows as processed
            self._mark_processed(
                source_type, project_id,
                [r["id"] for r in batch],
                [item["ref_id"] for item in items],
            )

        return appended

    async def process_all_pending(self) -> dict[str, int]:
        """Flush all source types.  Called by /memory and /work_items."""
        results: dict[str, int] = {}
        for src in ["commits", "prompts", "messages", "items"]:
            try:
                n = await self.process_pending(src)
                results[src] = n
            except Exception as e:
                log.warning(f"backlog: process_all_pending({src}) error: {e}")
                results[src] = 0
        return results

    # ── Row fetching ───────────────────────────────────────────────────────────

    def _fetch_pending_rows(self, source_type: str, project_id: int) -> list[dict]:
        table = _TABLE[source_type]
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if source_type == "prompts":
                        cur.execute(
                            """SELECT id::text, prompt, response, created_at
                               FROM mem_mrr_prompts
                               WHERE project_id=%s AND backlog_ref IS NULL
                               ORDER BY created_at
                               LIMIT 500""",
                            (project_id,),
                        )
                        return [
                            {"id": r[0], "prompt": r[1], "response": r[2], "created_at": r[3]}
                            for r in cur.fetchall()
                        ]
                    elif source_type == "commits":
                        cur.execute(
                            """SELECT commit_hash as id, commit_msg, diff_summary, created_at
                               FROM mem_mrr_commits
                               WHERE project_id=%s AND backlog_ref IS NULL
                               ORDER BY created_at
                               LIMIT 500""",
                            (project_id,),
                        )
                        return [
                            {"id": r[0], "commit_msg": r[1], "diff_summary": r[2], "created_at": r[3]}
                            for r in cur.fetchall()
                        ]
                    elif source_type == "messages":
                        cur.execute(
                            """SELECT id::text, platform, channel, messages, created_at
                               FROM mem_mrr_messages
                               WHERE project_id=%s AND backlog_ref IS NULL
                               ORDER BY created_at
                               LIMIT 500""",
                            (project_id,),
                        )
                        return [
                            {"id": r[0], "platform": r[1], "channel": r[2],
                             "messages": r[3], "created_at": r[4]}
                            for r in cur.fetchall()
                        ]
                    elif source_type == "items":
                        cur.execute(
                            """SELECT id::text, item_type, title, raw_text, created_at
                               FROM mem_mrr_items
                               WHERE project_id=%s AND backlog_ref IS NULL
                               ORDER BY created_at
                               LIMIT 500""",
                            (project_id,),
                        )
                        return [
                            {"id": r[0], "item_type": r[1], "title": r[2],
                             "raw_text": r[3], "created_at": r[4]}
                            for r in cur.fetchall()
                        ]
        except Exception as e:
            log.debug(f"_fetch_pending_rows({source_type}) error: {e}")
        return []

    # ── Ref ID allocation ──────────────────────────────────────────────────────

    def _allocate_refs(self, project_id: int, prefix: str, n: int) -> list[str]:
        refs: list[str] = []
        try:
            from data.dl_seq import next_seq
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for _ in range(n):
                        seq = next_seq(cur, project_id, prefix)
                        refs.append(f"{prefix}{seq}")
                conn.commit()
        except Exception as e:
            log.debug(f"_allocate_refs error: {e}")
        return refs

    # ── Input formatting ───────────────────────────────────────────────────────

    def _format_rows(self, source_type: str, rows: list[dict]) -> str:
        parts: list[str] = []
        for i, r in enumerate(rows, 1):
            if source_type == "prompts":
                p = (r.get("prompt") or "")[:500]
                resp = (r.get("response") or "")[:300]
                parts.append(f"[{i}] PROMPT: {p}\nRESPONSE: {resp}")
            elif source_type == "commits":
                msg  = r.get("commit_msg", "")
                diff = (r.get("diff_summary") or "")[:400]
                parts.append(f"[{i}] COMMIT: {msg}\nSTAT: {diff}")
            elif source_type == "messages":
                msgs = r.get("messages", [])
                txt  = json.dumps(msgs)[:400] if msgs else ""
                ch   = r.get("channel", "")
                parts.append(f"[{i}] CHANNEL: {ch}\nMESSAGES: {txt}")
            elif source_type == "items":
                title = r.get("title", "")
                raw   = (r.get("raw_text") or "")[:500]
                parts.append(f"[{i}] ITEM ({r.get('item_type','')}): {title}\n{raw}")
        return "\n\n".join(parts)

    # ── Prompt builders ────────────────────────────────────────────────────────

    def _load_use_case_context(self) -> str:
        uc_dir = self._use_cases_dir()
        if not uc_dir.exists():
            return "No existing use cases."
        lines: list[str] = []
        for md in sorted(uc_dir.glob("*.md"))[:20]:
            slug = md.stem
            first_lines = md.read_text(errors="ignore").splitlines()[:25]
            overview = "\n".join(first_lines[:3])
            lines.append(f"- {slug}: {overview}")
        return "\n".join(lines) if lines else "No existing use cases."

    def _build_system_prompt(self, p_desc: str, uc_context: str) -> str:
        return f"""{p_desc}

Active use cases for matching:
{uc_context}

Return a JSON array.  Each element must have these exact keys:
{{
  "ref_id": "<placeholder, will be filled>",
  "date": "YYYY/MM/DD",
  "summary": "one-line description",
  "requirements": ["..."],
  "deliveries": [{{"type": "code|docs|design", "desc": "..."}}],
  "action_items": [{{"desc": "...", "acceptance": "user accepts"}}],
  "classify": "bug|feature|task",
  "ai_match": {{"type": "existing|new|none", "slug": "slug-name"}}
}}

Return ONLY the JSON array. No markdown fences."""

    def _build_user_prompt(
        self, source_type: str, formatted: str, ref_ids: list[str]
    ) -> str:
        ref_list = ", ".join(ref_ids)
        return (
            f"Source type: {source_type}\n"
            f"Ref IDs to assign (in order): {ref_list}\n\n"
            f"{formatted}"
        )

    # ── Response parsing ───────────────────────────────────────────────────────

    def _parse_haiku_response(
        self, raw: str, ref_ids: list[str], source_type: str
    ) -> list[dict]:
        if not raw:
            return self._fallback_items(ref_ids, source_type)

        # Strip markdown fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            items = json.loads(cleaned)
            if not isinstance(items, list):
                items = [items]
        except json.JSONDecodeError:
            # Try extracting first JSON array
            m = re.search(r"\[.*\]", cleaned, re.DOTALL)
            if m:
                try:
                    items = json.loads(m.group())
                except Exception:
                    return self._fallback_items(ref_ids, source_type)
            else:
                return self._fallback_items(ref_ids, source_type)

        today = date.today().strftime("%Y/%m/%d")
        # Assign ref_ids in order (Haiku may use placeholders or wrong values)
        result: list[dict] = []
        for idx, item in enumerate(items[:len(ref_ids)]):
            ref_id = ref_ids[idx]
            result.append({
                "ref_id":       ref_id,
                "date":         item.get("date", today),
                "summary":      item.get("summary", f"{source_type} entry {ref_id}"),
                "requirements": item.get("requirements", []),
                "deliveries":   item.get("deliveries", []),
                "action_items": item.get("action_items", []),
                "classify":     item.get("classify", "task"),
                "ai_match":     item.get("ai_match", {"type": "none", "slug": ""}),
            })
        # Fill any remaining ref_ids that Haiku didn't produce entries for
        for idx in range(len(result), len(ref_ids)):
            result.append(self._fallback_item(ref_ids[idx], source_type))
        return result

    def _fallback_items(self, ref_ids: list[str], source_type: str) -> list[dict]:
        return [self._fallback_item(r, source_type) for r in ref_ids]

    def _fallback_item(self, ref_id: str, source_type: str) -> dict:
        return {
            "ref_id":       ref_id,
            "date":         date.today().strftime("%Y/%m/%d"),
            "summary":      f"{source_type} entry",
            "requirements": [],
            "deliveries":   [],
            "action_items": [],
            "classify":     "task",
            "ai_match":     {"type": "none", "slug": ""},
        }

    # ── Backlog file I/O ───────────────────────────────────────────────────────

    def _append_to_backlog(self, items: list[dict]) -> None:
        path = self._backlog_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        separator = "\n---\n\n"
        content = separator.join(_fmt_entry(item) for item in items)
        if not content:
            return
        if path.exists() and path.stat().st_size > 0:
            existing = path.read_text(errors="ignore")
            # Insert before any "## Processed" archive section
            archive_idx = existing.find("\n## Processed ")
            if archive_idx != -1:
                path.write_text(
                    existing[:archive_idx] + separator + content + "\n"
                    + existing[archive_idx:]
                )
            else:
                path.write_text(existing.rstrip() + "\n" + separator + content + "\n")
        else:
            path.write_text(
                "# Backlog\n\n"
                "> Approve entries with `x`, reject with `-`, tag with TAG comment.\n"
                "> Run `POST /memory/{project}/work-items` to process approved entries.\n\n"
                + content + "\n"
            )
        log.info(f"backlog: appended {len(items)} entries → {path}")

    def _mark_processed(
        self,
        source_type: str,
        project_id: int,
        row_ids: list[str],
        ref_ids: list[str],
    ) -> None:
        """SET backlog_ref = ref_id on each source row."""
        if not row_ids or not ref_ids:
            return
        table = _TABLE[source_type]
        # Primary key column name differs per table
        pk = "commit_hash" if source_type == "commits" else "id"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for row_id, ref_id in zip(row_ids, ref_ids):
                        cur.execute(
                            f"UPDATE {table} SET backlog_ref=%s WHERE {pk}=%s AND project_id=%s",
                            (ref_id, row_id, project_id),
                        )
                conn.commit()
        except Exception as e:
            log.debug(f"_mark_processed error: {e}")

    # ── Backlog parsing ────────────────────────────────────────────────────────

    def parse_backlog(self) -> list[dict]:
        """Split backlog.md on `---` separator and parse each entry."""
        path = self._backlog_path()
        if not path.exists():
            return []
        text = path.read_text(errors="ignore")

        # Only parse the pending section (before any archive)
        archive_idx = text.find("\n## Processed ")
        pending_text = text[:archive_idx] if archive_idx != -1 else text

        entries: list[dict] = []
        for chunk in re.split(r"\n---\n", pending_text):
            chunk = chunk.strip()
            if not chunk:
                continue
            entry = self._parse_entry(chunk)
            if entry:
                entries.append(entry)
        return entries

    def _parse_entry(self, chunk: str) -> Optional[dict]:
        lines = chunk.splitlines()
        header = None
        for line in lines:
            m = _ENTRY_HEADER_RE.match(line.strip())
            if m:
                header = m
                break
        if not header:
            return None

        ref_id  = header.group(1)
        dt      = header.group(2)
        summary = header.group(3)

        approve = " "
        tag     = ""
        match_type, match_slug = "none", ""

        for line in lines:
            m = _APPROVE_RE.search(line)
            if m:
                approve = m.group(1)
            m = _TAG_RE.search(line)
            if m:
                tag = m.group(1).strip()
            m = _MATCH_RE.search(line)
            if m:
                match_type = m.group(1)
                match_slug = m.group(2)

        return {
            "ref_id":     ref_id,
            "date":       dt,
            "summary":    summary,
            "approve":    approve,   # ' '=pending, 'x'=approved, '-'=rejected
            "tag":        tag,
            "match_type": match_type,
            "match_slug": match_slug,
            "raw":        chunk,
        }

    # ── Backlog rewrite ────────────────────────────────────────────────────────

    def rewrite(
        self,
        keep: list[dict],
        processed: list[str],
        rejected: list[str],
    ) -> None:
        """Rewrite backlog.md: keep pending entries at top, archive the rest."""
        path = self._backlog_path()
        text = path.read_text(errors="ignore") if path.exists() else ""

        # Build set of handled ref_ids
        handled = set(processed) | set(rejected)

        # Keep entries not yet handled
        keep_chunks = [e["raw"] for e in keep if e["ref_id"] not in handled]

        # Existing archive section
        archive_idx = text.find("\n## Processed ")
        existing_archive = text[archive_idx:] if archive_idx != -1 else ""

        today = date.today().strftime("%Y-%m-%d")
        new_archive_header = f"\n## Processed {today}\n"

        # Archive lines
        archive_refs = (
            [f"- {r} (approved)" for r in processed]
            + [f"- {r} (rejected)" for r in rejected]
        )
        archive_block = (
            (existing_archive + "\n" + "\n".join(archive_refs))
            if existing_archive
            else (new_archive_header + "\n".join(archive_refs))
        )

        header = (
            "# Backlog\n\n"
            "> Approve entries with `x`, reject with `-`, tag with TAG comment.\n"
            "> Run `POST /memory/{project}/work-items` to process approved entries.\n\n"
        )
        new_text = header + "\n---\n\n".join(keep_chunks)
        if keep_chunks:
            new_text += "\n"
        new_text += archive_block + "\n"

        path.write_text(new_text)
        log.info(
            f"backlog: rewrite — {len(keep_chunks)} pending, "
            f"{len(processed)} processed, {len(rejected)} rejected"
        )


# ── Use-case file helpers ──────────────────────────────────────────────────────

_USE_CASE_STUB = """\
# {slug}

## Overview
{summary}

## Requirements

### Closed
<!-- Entries moved here when done -->

### Open Features
<!-- AI-appended: [ref_id] entries from backlog -->

### Open Bugs
<!-- AI-appended: [ref_id] entries from backlog -->

## Internal Usage
| ID | Type | Date | Summary |
|----|------|------|---------|
"""


def _slug_path(uc_dir: Path, slug: str) -> Path:
    return uc_dir / f"{slug}.md"


def _create_use_case(uc_dir: Path, slug: str, entry: dict) -> None:
    """Create a new use case file from stub template, then merge entry."""
    uc_dir.mkdir(parents=True, exist_ok=True)
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        stub = _USE_CASE_STUB.format(
            slug=slug,
            summary=entry.get("summary", ""),
        )
        path.write_text(stub)
        log.info(f"use_case: created {path}")
    _merge_into_use_case(uc_dir, slug, entry)


def _merge_into_use_case(uc_dir: Path, slug: str, entry: dict) -> None:
    """Append entry into the appropriate section of an existing use case file."""
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        _create_use_case(uc_dir, slug, entry)
        return

    text = path.read_text(errors="ignore")
    ref_id  = entry.get("ref_id", "")
    summary = entry.get("summary", "")
    classify = entry.get("classify", "task")
    dt      = entry.get("date", date.today().strftime("%Y/%m/%d"))

    # Deduplication guard
    if ref_id and ref_id in text:
        log.debug(f"use_case: {ref_id} already in {slug}, skipping")
        return

    # Determine section
    section_tag = "### Open Bugs" if classify == "bug" else "### Open Features"

    action_items = entry.get("action_items", [])
    acceptance = ""
    if action_items:
        acceptance = action_items[0].get("acceptance", "")

    new_item = (
        f"- [ ] {summary}\n"
        + (f"  Acceptance: {acceptance}\n" if acceptance else "")
        + (f"  Linked: {ref_id}\n" if ref_id else "")
    )

    # Insert before next section after the target section
    if section_tag in text:
        idx = text.index(section_tag) + len(section_tag)
        text = text[:idx] + "\n" + new_item + text[idx:]
    else:
        text = text.rstrip() + f"\n\n{section_tag}\n{new_item}"

    # Append to Internal Usage table
    src_type = ref_id[0] if ref_id else "?"
    type_label = {"P": "prompt", "C": "commit", "M": "message", "I": "item"}.get(src_type, "?")
    row = f"| {ref_id} | {type_label} | {dt} | {summary[:50]} |"
    if "## Internal Usage" in text:
        # Insert row after the header row
        table_idx = text.index("## Internal Usage")
        lines = text.splitlines()
        insert_at = None
        for i, line in enumerate(lines):
            if line.startswith("| ID"):
                insert_at = i + 2  # after header + separator
                break
            if line.startswith("| ") and "|---" in lines[i + 1] if i + 1 < len(lines) else False:
                insert_at = i + 2
                break
        if insert_at is not None:
            lines.insert(insert_at, row)
            text = "\n".join(lines) + "\n"
        else:
            text = text.rstrip() + f"\n{row}\n"
    else:
        text = text.rstrip() + "\n\n## Internal Usage\n| ID | Type | Date | Summary |\n|----|------|------|------|\n" + row + "\n"

    path.write_text(text)
    log.info(f"use_case: merged {ref_id} → {slug}")


# ── Planner-tag helpers ───────────────────────────────────────────────────────

# Map classify value → (mng_tags_categories.name, pr_seq_counters.category, display prefix)
_CLASSIFY_TO_TAG: dict[str, tuple[str, str, str]] = {
    "use_case": ("use_case", "uc",   "UC"),
    "feature":  ("feature",  "feat", "F"),
    "bug":      ("bug",      "bug",  "B"),
    "task":     ("task",     "feat", "F"),   # tasks fall into feature range
}

_DEFAULT_TAG_CFG = ("use_case", "uc", "UC")


def _upsert_planner_tag(
    project: str,
    project_id: int,
    name: str,
    classify: str,
    file_ref: str,
    description: str = "",
) -> Optional[tuple[str, int]]:
    """Find or create a planner_tag row for this use-case / feature / bug.

    Assigns a seq_num on creation (never changes it later).
    Sets file_ref to point at the use-case .md file.
    Returns (tag_id: str, seq_num: int) or None on failure.
    """
    if not db.is_available():
        return None

    cat_name, seq_cat, _ = _CLASSIFY_TO_TAG.get(classify, _DEFAULT_TAG_CFG)

    try:
        from data.dl_seq import next_seq

        with db.conn() as conn:
            with conn.cursor() as cur:
                # Resolve category_id
                cur.execute(
                    "SELECT id FROM mng_tags_categories WHERE client_id=1 AND name=%s",
                    (cat_name,),
                )
                row = cur.fetchone()
                cat_id = row[0] if row else None

                # Check if a tag already exists for this name + category in this project
                cur.execute(
                    """SELECT id::text, seq_num FROM planner_tags
                       WHERE project_id=%s AND name=%s
                         AND (category_id=%s OR category_id IS NULL)
                       LIMIT 1""",
                    (project_id, name, cat_id),
                )
                existing = cur.fetchone()

                if existing:
                    tag_id, seq_num = existing
                    # Update file_ref if provided
                    if file_ref:
                        cur.execute(
                            "UPDATE planner_tags SET file_ref=%s, updated_at=NOW() WHERE id=%s::uuid",
                            (file_ref, tag_id),
                        )
                    conn.commit()
                    return (tag_id, seq_num)

                # Allocate seq_num
                seq_num = next_seq(cur, project_id, seq_cat)

                cur.execute(
                    """INSERT INTO planner_tags
                       (project_id, name, category_id, description, status,
                        creator, seq_num, file_ref)
                       VALUES (%s, %s, %s, %s, 'open', 'ai', %s, %s)
                       ON CONFLICT (project_id, name, category_id) DO UPDATE SET
                           file_ref    = COALESCE(EXCLUDED.file_ref, planner_tags.file_ref),
                           seq_num     = COALESCE(planner_tags.seq_num, EXCLUDED.seq_num),
                           updated_at  = NOW()
                       RETURNING id::text, seq_num""",
                    (project_id, name, cat_id, description or name, seq_num, file_ref),
                )
                result = cur.fetchone()
                conn.commit()

                if result:
                    return (result[0], result[1])
    except Exception as e:
        log.warning(f"_upsert_planner_tag({name}, {classify}) error: {e}")
    return None


def _tag_display_id(classify: str, seq_num: int) -> str:
    """Return human-readable tag ID: UC10001, F20001, B30001."""
    _, _, prefix = _CLASSIFY_TO_TAG.get(classify, _DEFAULT_TAG_CFG)
    return f"{prefix}{seq_num}"


# ── run_work_items ────────────────────────────────────────────────────────────

async def run_work_items(project: str) -> dict:
    """Full pipeline: flush pending → approve → create/merge use cases + planner_tags.

    1. Flush all unprocessed mirror rows into backlog.md
    2. Parse backlog.md
    3. For approved (APPROVE: x) entries:
       a. Create/merge into use_cases/{slug}.md
       b. Upsert planner_tag with seq_num, file_ref pointing to .md file
    4. For rejected (APPROVE: -) entries: archive them
    5. Rewrite backlog.md
    6. Return summary stats
    """
    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()

    # Step 1: flush
    flushed = await bl.process_all_pending()
    total_flushed = sum(flushed.values())

    # Step 2: parse
    entries = bl.parse_backlog()

    approved_ids: list[str] = []
    rejected_ids: list[str] = []
    pending: list[dict] = []
    use_cases_updated: set[str] = set()
    tags_created: list[dict] = []

    uc_dir = bl._use_cases_dir()

    for entry in entries:
        ap = entry.get("approve", " ")
        if ap == "x":
            # Step 3a: create/merge use-case file
            tag_override = entry.get("tag", "").strip()
            match_type   = entry.get("match_type", "none")
            match_slug   = entry.get("match_slug", "").strip()
            classify     = entry.get("classify", "use_case")
            # Normalise classify: "task" → treat as feature in the file, but
            # keep classify for the seq range
            if classify not in _CLASSIFY_TO_TAG:
                classify = "use_case"

            slug = tag_override or match_slug or "general"
            slug = re.sub(r"[^a-z0-9\-]", "-", slug.lower()).strip("-") or "general"

            try:
                if match_type == "new" and not tag_override:
                    _create_use_case(uc_dir, slug, entry)
                else:
                    if not _slug_path(uc_dir, slug).exists():
                        _create_use_case(uc_dir, slug, entry)
                    else:
                        _merge_into_use_case(uc_dir, slug, entry)
                use_cases_updated.add(slug)
            except Exception as e:
                log.warning(f"run_work_items: file merge error for {entry['ref_id']}: {e}")

            # Step 3b: upsert planner_tag with seq_num + file_ref
            if project_id:
                uc_path = _slug_path(uc_dir, slug)
                # file_ref relative to code_dir (or absolute fallback)
                code_dir = _get_code_dir(project)
                if code_dir and uc_path.is_relative_to(code_dir):
                    file_ref = str(uc_path.relative_to(code_dir))
                else:
                    file_ref = f"documents/use_cases/{slug}.md"

                tag_result = _upsert_planner_tag(
                    project=project,
                    project_id=project_id,
                    name=slug,
                    classify=classify,
                    file_ref=file_ref,
                    description=entry.get("summary", ""),
                )
                if tag_result:
                    tag_id, seq_num = tag_result
                    display_id = _tag_display_id(classify, seq_num)
                    tags_created.append({
                        "slug":       slug,
                        "tag_id":     tag_id,
                        "seq_num":    seq_num,
                        "display_id": display_id,
                        "classify":   classify,
                        "ref_id":     entry["ref_id"],
                    })
                    log.info(
                        f"backlog: planner_tag {display_id} ({slug}) "
                        f"linked to {entry['ref_id']}"
                    )

            approved_ids.append(entry["ref_id"])

        elif ap == "-":
            rejected_ids.append(entry["ref_id"])
        else:
            pending.append(entry)

    # Step 5: rewrite backlog
    if approved_ids or rejected_ids:
        bl.rewrite(keep=pending, processed=approved_ids, rejected=rejected_ids)

    return {
        "flushed":           total_flushed,
        "flushed_by_source": flushed,
        "approved":          len(approved_ids),
        "rejected":          len(rejected_ids),
        "pending":           len(pending),
        "use_cases_updated": sorted(use_cases_updated),
        "tags_created":      tags_created,
    }
