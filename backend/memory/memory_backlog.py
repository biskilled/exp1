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

# SQL SIMILAR TO pattern for system/generated file paths (no real code symbols)
_SYSTEM_FILE_PATTERN = (
    r"%(CLAUDE|MEMORY|\.cursorrules|\.claude|copilot-instructions"
    r"|backlog_config|project\.yaml|package-lock\.json|yarn\.lock"
    r"|__pycache__|\.pyc|\.min\.js)%"
)


def _is_system_stat(diff_stat: str) -> bool:
    """Return True if ALL changed files in a git --stat output look like system files."""
    lines = [l.strip() for l in diff_stat.splitlines() if "|" in l]
    if not lines:
        return True
    _SYS = ("CLAUDE", "MEMORY", ".cursorrules", ".claude", "copilot", "backlog_config",
            "project.yaml", "package-lock.json", "yarn.lock", ".pyc", ".min.js")
    return all(any(s in line for s in _SYS) for line in lines)

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
                       VALUES (%s, 'claude', %s, %s, %s, %s, 0, 'memory')""",
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
        from pipelines.pipeline_git import get_project_code_dir
        cd = get_project_code_dir(project)
        return Path(cd) if cd else None
    except Exception:
        return None


# ── Entry format helpers ───────────────────────────────────────────────────────
# Header format:  SOURCE YY/MM/DD-HH:MM REF_ID [APPROVE] [slug] [classify] (user) — summary
# APPROVE values: [ ] = pending | [+] or [x] = approved | [-] = rejected

_ENTRY_HEADER_RE = re.compile(
    r"^(PROMPTS|COMMITS|ITEMS|MESSAGES)\s+"
    r"(\d{2}/\d{2}/\d{2}(?:-\d{2}:\d{2})?)\s+"
    r"([PCMI]\d+)\s+"
    r"\[([+ x\-]*)\]\s+"
    r"\[([^\]]*)\]\s+"
    r"\[([^\]]*)\]\s+"
    r"\([^)]*\)\s+"
    r"—\s+(.+)$"
)

_SOURCE_LABEL: dict[str, str] = {
    "prompts":  "PROMPTS",
    "commits":  "COMMITS",
    "messages": "MESSAGES",
    "items":    "ITEMS",
}
_PREFIX_TO_LABEL: dict[str, str] = {
    "P": "PROMPTS", "C": "COMMITS", "M": "MESSAGES", "I": "ITEMS",
}


def _fmt_date(dt_val) -> str:
    """Return YY/MM/DD-HH:MM from a date, datetime, or ISO/YYYY-MM-DD string."""
    if isinstance(dt_val, datetime):
        return dt_val.strftime("%y/%m/%d-%H:%M")
    if isinstance(dt_val, date):
        return dt_val.strftime("%y/%m/%d-00:00")
    if isinstance(dt_val, str) and dt_val:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(dt_val[:len(fmt)], fmt).strftime("%y/%m/%d-00:00")
            except Exception:
                pass
    return date.today().strftime("%y/%m/%d-00:00")


def _fmt_entry(item: dict) -> str:
    """Render a single-row digest dict into the new backlog.md header format.

    Commit entries (ref_id starts 'C') are auto-approved.
    """
    ref_id   = item.get("ref_id", "")
    prefix   = ref_id[0] if ref_id else "P"
    src      = _PREFIX_TO_LABEL.get(prefix, "PROMPTS")
    dt       = _fmt_date(item.get("date", date.today()))
    summary  = item.get("summary", "")
    classify = item.get("classify", "task")
    ai_match = item.get("ai_match", {})
    slug     = ai_match.get("slug", "") or "general"
    approve  = "x" if prefix == "C" else " "

    lines = [
        f"{src} {dt} {ref_id} [{approve}] [{slug}] [{classify}] (auto) — {summary}",
        "",
    ]

    reqs = item.get("requirements", [])
    if reqs:
        lines.append("  Requirements:")
        for r in reqs:
            lines.append(f"  - {r}")
        lines.append("")

    deliveries = item.get("deliveries", [])
    if deliveries:
        lines.append("  Completed:")
        for dv in deliveries:
            lines.append(f"  - {dv.get('desc','')} ({dv.get('type','')})")
        lines.append("")

    action_items = item.get("action_items", [])
    if action_items:
        lines.append("  Action items:")
        for a in action_items:
            acc = a.get("acceptance", "")
            lines.append(f"  - {a.get('desc','')}" + (f" (acceptance: {acc})" if acc else ""))
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
                    if source_type == "commits":
                        # Only count unlinked commits (no prompt_id) — those are the ones
                        # the standalone commit pipeline processes
                        cur.execute(
                            "SELECT COUNT(*) FROM mem_mrr_commits "
                            "WHERE project_id=%s AND backlog_ref IS NULL AND prompt_id IS NULL",
                            (project_id,),
                        )
                    else:
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
            system_prompt = self._build_system_prompt(p_desc, uc_context, source_type)
            user_prompt   = self._build_user_prompt(source_type, formatted, ref_ids)

            # Call Haiku
            raw = await _call_haiku(system_prompt, user_prompt, model, max_tokens=3000)

            # Parse JSON response
            items = self._parse_haiku_response(raw, ref_ids, source_type)

            # Append to backlog.md
            self._append_to_backlog(items)
            appended += len(items)

            # Mark rows as processed (for prompts: also stamps linked commits)
            self._mark_processed(
                source_type, project_id,
                [r["id"] for r in batch],
                [item["ref_id"] for item in items],
                rows=batch,
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
        """Fetch pending (backlog_ref IS NULL) rows for the given source type.

        prompts: enriched with linked commits + commit_code context.
        commits: ONLY commits with prompt_id IS NULL (standalone, no user session).
        messages/items: plain fetch.
        """
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if source_type == "prompts":
                        return self._fetch_prompts_with_commit_context(cur, project_id)
                    elif source_type == "commits":
                        return self._fetch_standalone_commits(cur, project_id)
                    elif source_type == "messages":
                        cur.execute(
                            """SELECT id::text, platform, channel, messages, created_at
                               FROM mem_mrr_messages
                               WHERE project_id=%s AND backlog_ref IS NULL
                               ORDER BY created_at LIMIT 500""",
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
                               ORDER BY created_at LIMIT 500""",
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

    def _fetch_prompts_with_commit_context(self, cur, project_id: int) -> list[dict]:
        """Fetch pending prompts and enrich each with linked commits + code symbols."""
        cur.execute(
            """SELECT id::text, prompt, response, created_at
               FROM mem_mrr_prompts
               WHERE project_id=%s AND backlog_ref IS NULL
               ORDER BY created_at LIMIT 500""",
            (project_id,),
        )
        rows = cur.fetchall()
        result: list[dict] = []
        for r in rows:
            prompt_id, prompt, response, created_at = r[0], r[1], r[2], r[3]
            # Fetch commits linked to this prompt
            cur.execute(
                """SELECT commit_hash, commit_msg, diff_summary
                   FROM mem_mrr_commits
                   WHERE project_id=%s AND prompt_id=%s::uuid AND backlog_ref IS NULL
                   ORDER BY created_at""",
                (project_id, prompt_id),
            )
            commits = cur.fetchall()
            # For each commit, fetch code symbols (skip generated/system files)
            commit_contexts: list[dict] = []
            for c_hash, c_msg, c_stat in commits:
                cur.execute(
                    """SELECT file_path, file_change, symbol_type, class_name,
                              method_name, rows_added, rows_removed
                       FROM mem_mrr_commits_code
                       WHERE project_id=%s AND commit_hash=%s
                         AND file_path NOT SIMILAR TO %s
                       ORDER BY file_path, symbol_type LIMIT 30""",
                    (project_id, c_hash, _SYSTEM_FILE_PATTERN),
                )
                symbols = [
                    {"file": s[0], "change": s[1], "type": s[2],
                     "class": s[3], "method": s[4], "+": s[5], "-": s[6]}
                    for s in cur.fetchall()
                ]
                if symbols or c_msg:
                    commit_contexts.append({
                        "hash": c_hash[:8], "msg": c_msg, "symbols": symbols,
                    })
            result.append({
                "id": prompt_id, "prompt": prompt, "response": response,
                "created_at": created_at, "commits": commit_contexts,
            })
        return result

    def _fetch_standalone_commits(self, cur, project_id: int) -> list[dict]:
        """Fetch commits with NO linked prompt (CI/CD, merges, direct pushes).

        Enriched with commit_code symbols for action-item extraction.
        Commits where ALL code rows are system/generated files are skipped.
        """
        cur.execute(
            """SELECT commit_hash, commit_msg, diff_summary, created_at
               FROM mem_mrr_commits
               WHERE project_id=%s AND backlog_ref IS NULL AND prompt_id IS NULL
               ORDER BY created_at LIMIT 500""",
            (project_id,),
        )
        commits = cur.fetchall()
        result: list[dict] = []
        for c_hash, c_msg, c_stat, c_at in commits:
            cur.execute(
                """SELECT file_path, file_change, symbol_type, class_name,
                          method_name, rows_added, rows_removed
                   FROM mem_mrr_commits_code
                   WHERE project_id=%s AND commit_hash=%s
                     AND file_path NOT SIMILAR TO %s
                   ORDER BY file_path, symbol_type LIMIT 30""",
                (project_id, c_hash, _SYSTEM_FILE_PATTERN),
            )
            symbols = [
                {"file": s[0], "change": s[1], "type": s[2],
                 "class": s[3], "method": s[4], "+": s[5], "-": s[6]}
                for s in cur.fetchall()
            ]
            # Skip commits that only touched system/generated files
            if not symbols and _is_system_stat(c_stat or ""):
                log.debug(f"backlog: skipping system-only commit {c_hash[:8]}")
                # Stamp with a sentinel so it's not re-evaluated every time
                cur.execute(
                    "UPDATE mem_mrr_commits SET backlog_ref='SKIP' "
                    "WHERE commit_hash=%s",
                    (c_hash,),
                )
                continue
            result.append({
                "id": c_hash, "commit_msg": c_msg, "diff_summary": c_stat,
                "created_at": c_at, "symbols": symbols,
            })
        return result

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
                p    = (r.get("prompt")   or "")[:500]
                resp = (r.get("response") or "")[:300]
                block = f"[{i}] PROMPT: {p}\nRESPONSE: {resp}"
                # Append linked commit code context
                for ctx in r.get("commits", []):
                    block += f"\n  LINKED COMMIT {ctx['hash']}: {ctx['msg'][:120]}"
                    for sym in ctx.get("symbols", [])[:15]:
                        cls = f"{sym['class']}." if sym.get("class") else ""
                        mth = sym.get("method") or ""
                        sym_name = f"{cls}{mth}" if (cls or mth) else sym["file"]
                        block += (
                            f"\n    {sym['file']} [{sym['change']}]"
                            f" {sym['type']}: {sym_name}"
                            f" (+{sym['+'] or 0}/-{sym['-'] or 0})"
                        )
                parts.append(block)
            elif source_type == "commits":
                msg  = r.get("commit_msg", "")
                block = f"[{i}] COMMIT: {msg}"
                for sym in r.get("symbols", [])[:20]:
                    cls = f"{sym['class']}." if sym.get("class") else ""
                    mth = sym.get("method") or ""
                    sym_name = f"{cls}{mth}" if (cls or mth) else sym["file"]
                    block += (
                        f"\n  {sym['file']} [{sym['change']}]"
                        f" {sym['type']}: {sym_name}"
                        f" (+{sym['+'] or 0}/-{sym['-'] or 0})"
                    )
                parts.append(block)
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

    def _build_system_prompt(self, p_desc: str, uc_context: str, source_type: str = "prompts") -> str:
        if source_type == "commits":
            extra = (
                "These are standalone commits (no user session) — CI/CD, merges, direct pushes.\n"
                "Use the CODE CHANGES (file/class/method names) to infer action items.\n"
                "Deliveries are already done (the commit is the delivery).\n"
                "Set APPROVE to 'x' automatically — commit entries do not require user review.\n"
            )
        else:
            extra = (
                "LINKED COMMIT sections show code changes made during this session.\n"
                "Include those as 'code' deliveries and reference method/class names where relevant.\n"
                "If LINKED COMMIT sections are absent, the session produced no code changes.\n"
            )

        return f"""{p_desc}

{extra}
Active use cases for matching:
{uc_context}

MANDATORY TAGGING RULES (both tags required on every entry):
1. ai_match (use case tag): MUST be set to an existing slug, a new slug, or 'none' only if
   the entry is purely internal/chore with no user value.
   - type: "existing" if it matches one of the active use cases above
   - type: "new" if it represents a new capability not yet in the list
   - type: "none" only for pure chore/system work (rare)
2. classify (work type tag): MUST be exactly one of: bug | feature | task
   - bug: fixes broken behaviour
   - feature: adds new user-facing capability
   - task: infrastructure, refactor, docs, chore

Return a JSON array. Each element must have these exact keys:
{{
  "ref_id": "<placeholder, will be filled>",
  "date": "YYYY/MM/DD",
  "summary": "one-line description (max 120 chars)",
  "requirements": ["requirement 1", "..."],
  "deliveries": [{{"type": "code|docs|design", "desc": "what was produced/changed"}}],
  "action_items": [{{"desc": "what still needs to be done", "acceptance": "done when..."}}],
  "classify": "bug|feature|task",
  "ai_match": {{"type": "existing|new|none", "slug": "slug-name-or-empty"}}
}}

Return ONLY the JSON array. No markdown fences. No extra text."""

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
        rows: Optional[list[dict]] = None,
    ) -> None:
        """SET backlog_ref = ref_id on each source row.

        For prompts: also stamps backlog_ref on all commits linked to those prompts
        (so they are not re-processed as standalone commit entries).
        """
        if not row_ids or not ref_ids:
            return
        table = _TABLE[source_type]
        pk = "commit_hash" if source_type == "commits" else "id"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for row_id, ref_id in zip(row_ids, ref_ids):
                        cur.execute(
                            f"UPDATE {table} SET backlog_ref=%s WHERE {pk}=%s AND project_id=%s",
                            (ref_id, row_id, project_id),
                        )
                    # For prompts: stamp linked commits with the same ref so they're not
                    # picked up by the standalone-commit pipeline
                    if source_type == "prompts" and rows:
                        for row, ref_id in zip(rows, ref_ids):
                            prompt_id = row.get("id")
                            if not prompt_id:
                                continue
                            cur.execute(
                                """UPDATE mem_mrr_commits
                                   SET backlog_ref=%s
                                   WHERE project_id=%s AND prompt_id=%s::uuid
                                     AND backlog_ref IS NULL""",
                                (ref_id, project_id, prompt_id),
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

        src_type = header.group(1)   # PROMPTS | COMMITS | ...
        dt       = header.group(2)   # YY/MM/DD-HH:MM
        ref_id   = header.group(3)   # P100042
        approve_raw = header.group(4).strip()  # +, x, -, or empty
        slug     = header.group(5).strip()
        classify = header.group(6).strip()
        summary  = header.group(7).strip()

        # Normalise: both + and x mean approved
        if approve_raw in ("+", "x"):
            approve = "x"
        elif approve_raw == "-":
            approve = "-"
        else:
            approve = " "

        return {
            "ref_id":   ref_id,
            "source":   src_type,
            "date":     dt,
            "summary":  summary,
            "approve":  approve,   # ' '=pending, 'x'=approved, '-'=rejected
            "slug":     slug,
            "classify": classify,
            "raw":      chunk,
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


# ── Full-digest pipeline ──────────────────────────────────────────────────────

def _fmt_full_digest_entry(entry: dict) -> str:
    """Render a full-digest group entry into the new backlog.md format.

    Header: SOURCE YY/MM/DD-HH:MM REF_ID [APPROVE] [slug] [classify] (auto) — topic
    Commits are auto-approved [x]; prompt/item/message groups start pending [ ].
    """
    ref_id   = entry.get("ref_id", "?")
    prefix   = ref_id[0] if ref_id else "P"
    src      = _PREFIX_TO_LABEL.get(prefix, "PROMPTS")
    dt       = _fmt_date(entry.get("date", date.today()))
    slug     = entry.get("slug", "general")
    classify = entry.get("classify", "task")
    # Strip auto-prefix from summary if present (e.g. "auth-refactor: topic" → "topic")
    raw_summary = entry.get("summary", "")
    if raw_summary.startswith(f"{slug}: "):
        summary = raw_summary[len(slug) + 2:]
    else:
        summary = raw_summary

    # Commits auto-approved; others pending
    approve = "x" if prefix == "C" else " "

    completed     = entry.get("completed", [])
    open_features = entry.get("open_features", [])
    open_bugs     = entry.get("open_bugs", [])
    action_items  = entry.get("action_items", [])   # standalone commit items
    event_ids     = entry.get("event_ids", [])

    lines = [
        f"{src} {dt} {ref_id} [{approve}] [{slug}] [{classify}] (auto) — {summary}",
        "",
    ]

    if completed:
        lines.append("  Completed:")
        for item in completed:
            lines.append(f"  - {item}")
        lines.append("")

    if open_features:
        lines.append("  Action items:")
        for item in open_features:
            desc = item.get("desc", item) if isinstance(item, dict) else item
            acc  = item.get("acceptance", "") if isinstance(item, dict) else ""
            lines.append(f"  - {desc}" + (f" (acceptance: {acc})" if acc else ""))
        lines.append("")

    if open_bugs:
        lines.append("  Open bugs:")
        for item in open_bugs:
            desc = item.get("desc", item) if isinstance(item, dict) else item
            acc  = item.get("acceptance", "") if isinstance(item, dict) else ""
            lines.append(f"  - {desc}" + (f" (acceptance: {acc})" if acc else ""))
        lines.append("")

    if action_items:
        lines.append("  Action items:")
        for item in action_items:
            desc = item.get("desc", item) if isinstance(item, dict) else item
            acc  = item.get("acceptance", "") if isinstance(item, dict) else ""
            lines.append(f"  - {desc}" + (f" (acceptance: {acc})" if acc else ""))
        lines.append("")

    n = len(event_ids)
    if n:
        lines.append(f"  Events: {n} source row(s) processed")
        lines.append("")

    return "\n".join(lines)


class _FullDigest:
    """Full-pass digest: groups ALL pending prompts by use case (one entry per group).

    Standalone commits (no linked prompt) produce a single action-items summary entry.
    Unlike process_pending() which works per cnt-threshold, this sees all data at once.
    """

    def __init__(self, bl: "MemoryBacklog") -> None:
        self.bl = bl
        cfg_root = bl._config().get("full_digest", {})
        self.max_groups    = int(cfg_root.get("max_groups", 7))
        self.max_open_bugs  = int(cfg_root.get("max_open_bugs", 3))
        self.max_open_items = int(cfg_root.get("max_open_items", 3))
        self.grouping_cfg   = cfg_root.get("grouping_prompt", {})
        self.summary_cfg    = cfg_root.get("summary_prompt", {})
        self.commits_cfg    = cfg_root.get("commits_summary_prompt", {})

    async def run(self) -> dict:
        bl         = self.bl
        project_id = bl._get_project_id()
        if not project_id:
            return {"error": "project not found"}

        uc_context = bl._load_use_case_context()

        # 1. Load all pending rows
        prompt_rows: list[dict] = []
        standalone_commits: list[dict] = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    prompt_rows       = bl._fetch_prompts_with_commit_context(cur, project_id)
                    standalone_commits = bl._fetch_standalone_commits(cur, project_id)
        except Exception as e:
            log.warning(f"full_digest: fetch error: {e}")

        if not prompt_rows and not standalone_commits:
            log.info("full_digest: nothing pending")
            return {"appended": 0, "groups": 0, "commits_entry": None,
                    "total_prompts": 0, "total_standalone_commits": 0}

        log.info(
            f"full_digest: {len(prompt_rows)} prompts, "
            f"{len(standalone_commits)} standalone commits"
        )

        # 2. Group prompts
        groups: list[dict] = []
        if prompt_rows:
            groups = await self._group_prompts(prompt_rows, uc_context)

        # 3. Summarize each group
        entries: list[dict] = []
        all_prompt_ids: list[str] = []
        for group in groups:
            idx_list   = group.get("event_indices", [])
            slug       = group.get("slug", "general")
            classify   = group.get("classify", "task")
            slug_type  = group.get("slug_type", "existing")
            topic      = group.get("topic", slug)
            group_rows = [prompt_rows[i] for i in idx_list if i < len(prompt_rows)]
            if not group_rows:
                continue

            ref_ids = bl._allocate_refs(project_id, "P", 1)
            if not ref_ids:
                continue
            ref_id = ref_ids[0]

            summary_data = await self._summarize_group(group_rows, slug, classify)

            entries.append({
                "ref_id":       ref_id,
                "date":         date.today().strftime("%Y/%m/%d"),
                "summary":      f"{slug}: {topic}",
                "slug":         slug,
                "slug_type":    slug_type,
                "classify":     classify,
                "completed":    summary_data.get("completed", []),
                "open_features": summary_data.get("open_features", [])[:self.max_open_items],
                "open_bugs":    summary_data.get("open_bugs", [])[:self.max_open_bugs],
                "event_ids":    [r["id"] for r in group_rows],
            })
            all_prompt_ids.extend(r["id"] for r in group_rows)

        # 4. Standalone commits → ONE entry
        commits_entry: Optional[dict] = None
        if standalone_commits:
            c_ref_ids = bl._allocate_refs(project_id, "C", 1)
            if c_ref_ids:
                c_summary = await self._summarize_standalone_commits(
                    standalone_commits, uc_context
                )
                commits_entry = {
                    "ref_id":      c_ref_ids[0],
                    "date":        date.today().strftime("%Y/%m/%d"),
                    "summary":     f"standalone commits summary ({len(standalone_commits)} commits)",
                    "slug":        c_summary.get("slug", "discovery"),
                    "slug_type":   "existing",
                    "classify":    "task",
                    "action_items": c_summary.get("action_items", []),
                    "event_ids":   [],
                }

        # 5. Write backlog.md (overwrite pending section, keep archive)
        all_entries = entries + ([commits_entry] if commits_entry else [])
        self._write_entries(all_entries)

        # 6. Mark all source rows as processed
        self._mark_processed(
            project_id, entries, commits_entry, all_prompt_ids, standalone_commits
        )

        return {
            "appended":               len(all_entries),
            "groups":                 len(entries),
            "commits_entry":          commits_entry["ref_id"] if commits_entry else None,
            "total_prompts":          len(prompt_rows),
            "total_standalone_commits": len(standalone_commits),
        }

    # ── LLM helpers ─────────────────────────────────────────────────────────

    async def _group_prompts(self, rows: list[dict], uc_context: str) -> list[dict]:
        """Group all prompts into max max_groups clusters using LLM."""
        model = self.grouping_cfg.get("llm", settings.haiku_model)
        desc  = self.grouping_cfg.get("desc", "")

        # Compress each prompt to a short preview for the grouping call
        compressed: list[str] = []
        for i, r in enumerate(rows):
            p    = (r.get("prompt") or "")[:150].replace("\n", " ")
            dt   = r.get("created_at", "")
            dt_s = str(dt)[:10] if dt else ""
            c_ct = len(r.get("commits", []))
            suffix = f" [{c_ct} commits]" if c_ct else ""
            compressed.append(f"[{i}] {dt_s} {p}{suffix}")

        system_p = f"""{desc}

Active use cases:
{uc_context}

Rules:
- Group into AT MOST {self.max_groups} groups.
- Each event index must appear in exactly one group.
- Prefer existing slugs. Create new slug only if truly new capability.
- New slugs must be lowercase-hyphenated (e.g. "stripe-billing").
- slug_type: "existing" or "new"
- classify: "bug" | "feature" | "task"

Return JSON array only. No markdown. No extra text.
[{{"event_indices":[0,1],"slug":"auth-refactor","slug_type":"existing",
   "classify":"feature","topic":"JWT auth and session management"}}]"""

        user_p = f"Total prompts: {len(rows)}\n\n" + "\n".join(compressed)

        raw = await _call_haiku(system_p, user_p, model, max_tokens=4000)
        if not raw:
            # Fallback: put all in one group
            return [{"event_indices": list(range(len(rows))), "slug": "discovery",
                     "slug_type": "existing", "classify": "task",
                     "topic": "all development work"}]

        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            groups = json.loads(cleaned)
            if not isinstance(groups, list):
                raise ValueError("not a list")
            # Validate and filter SKIP groups
            groups = [g for g in groups if g.get("slug", "").upper() != "SKIP" and g.get("event_indices")]
            # Limit to max_groups
            groups = groups[:self.max_groups]
            # Ensure every index is covered (add leftover to last group or new group)
            covered = {i for g in groups for i in g.get("event_indices", [])}
            leftover = [i for i in range(len(rows)) if i not in covered]
            if leftover:
                if groups:
                    groups[-1]["event_indices"].extend(leftover)
                else:
                    groups.append({"event_indices": leftover, "slug": "discovery",
                                   "slug_type": "existing", "classify": "task",
                                   "topic": "general work"})
            return groups
        except Exception as e:
            log.warning(f"full_digest: grouping parse error: {e}\nraw={raw[:200]}")
            return [{"event_indices": list(range(len(rows))), "slug": "discovery",
                     "slug_type": "existing", "classify": "task",
                     "topic": "all development work"}]

    async def _summarize_group(
        self, rows: list[dict], slug: str, classify: str
    ) -> dict:
        """Summarize one group of prompts into completed/open_features/open_bugs."""
        model = self.summary_cfg.get("llm", settings.haiku_model)
        desc  = self.summary_cfg.get("desc", "")

        max_f = self.max_open_items
        max_b = self.max_open_bugs

        # Build context for this group
        parts: list[str] = []
        for i, r in enumerate(rows, 1):
            p    = (r.get("prompt")   or "")[:400]
            resp = (r.get("response") or "")[:200]
            block = f"[{i}] PROMPT: {p}\nRESPONSE: {resp}"
            for ctx in r.get("commits", []):
                block += f"\n  COMMIT {ctx['hash'][:7]}: {ctx['msg'][:100]}"
                for sym in ctx.get("symbols", [])[:8]:
                    cls = f"{sym['class']}." if sym.get("class") else ""
                    mth = sym.get("method") or ""
                    nm  = f"{cls}{mth}" if (cls or mth) else sym["file"]
                    block += f"\n    {sym['file']} {sym['type']}: {nm} (+{sym.get('+',0)}/-{sym.get('-',0)})"
            parts.append(block)

        system_p = f"""{desc}

Use case: {slug}  |  classify: {classify}

Return JSON (no markdown, no extra text):
{{
  "completed":     ["done item referencing file/class where known"],
  "open_features": [{{"desc": "...", "acceptance": "done when ..."}}],
  "open_bugs":     [{{"desc": "...", "acceptance": "done when ..."}}]
}}

Limits: completed = any number.  open_features ≤ {max_f}.  open_bugs ≤ {max_b}.
Be specific; reference file/class/method names. One sentence per item."""

        user_p = "\n\n".join(parts)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=2500)

        if not raw:
            return {"completed": [], "open_features": [], "open_bugs": []}
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            m = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
        return {"completed": [], "open_features": [], "open_bugs": []}

    async def _summarize_standalone_commits(
        self, commits: list[dict], uc_context: str
    ) -> dict:
        """Summarize all standalone commits into ONE entry with action_items + slug."""
        model = self.commits_cfg.get("llm", settings.haiku_model)
        desc  = self.commits_cfg.get("desc", "")

        parts: list[str] = []
        for i, c in enumerate(commits, 1):
            msg = c.get("commit_msg", "")
            block = f"[{i}] COMMIT: {msg}"
            for sym in c.get("symbols", [])[:12]:
                cls = f"{sym['class']}." if sym.get("class") else ""
                mth = sym.get("method") or ""
                nm  = f"{cls}{mth}" if (cls or mth) else sym["file"]
                block += f"\n  {sym['file']} {sym['type']}: {nm} (+{sym.get('+',0)}/-{sym.get('-',0)})"
            parts.append(block)

        system_p = f"""{desc}

Active use cases:
{uc_context}

These commits have no linked user session (CI/CD, merges, direct pushes).
The work is already done. Identify any action items the commits suggest are still needed.
Also suggest the best matching slug from the active use cases (or "discovery" if unclear).

Return JSON only:
{{
  "slug":         "best-matching-slug",
  "action_items": [{{"desc": "...", "acceptance": "..."}}]
}}"""

        user_p = "\n\n".join(parts)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=1500)

        if not raw:
            return {"slug": "discovery", "action_items": []}
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            m = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:
                    pass
        return {"slug": "discovery", "action_items": []}

    # ── File I/O ────────────────────────────────────────────────────────────

    def _write_entries(self, entries: list[dict]) -> None:
        """Overwrite the pending section of backlog.md with new full-digest entries.

        Preserves any existing ## Processed archive section.
        """
        path = self.bl._backlog_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        separator = "\n---\n\n"
        content   = separator.join(_fmt_full_digest_entry(e) for e in entries)

        # Preserve archive section if it exists
        archive_block = ""
        if path.exists():
            existing = path.read_text(errors="ignore")
            idx = existing.find("\n## Processed ")
            if idx != -1:
                archive_block = existing[idx:]

        header = (
            "# Backlog\n\n"
            "> Full-digest run — all entries auto-approved (APPROVE: x).\n"
            "> Run `POST /memory/{project}/work-items` to merge into use cases.\n\n"
        )
        path.write_text(header + content + "\n" + archive_block)
        log.info(f"full_digest: wrote {len(entries)} entries → {path}")

    # ── DB marking ──────────────────────────────────────────────────────────

    def _mark_processed(
        self,
        project_id: int,
        entries: list[dict],
        commits_entry: Optional[dict],
        all_prompt_ids: list[str],
        standalone_commits: list[dict],
    ) -> None:
        """Stamp backlog_ref on all source rows that were processed."""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Stamp each prompt with its group's ref_id
                    for entry in entries:
                        ref_id = entry["ref_id"]
                        for pid in entry.get("event_ids", []):
                            cur.execute(
                                "UPDATE mem_mrr_prompts SET backlog_ref=%s "
                                "WHERE id=%s::uuid AND project_id=%s",
                                (ref_id, pid, project_id),
                            )
                            # Stamp commits linked to this prompt
                            cur.execute(
                                "UPDATE mem_mrr_commits SET backlog_ref=%s "
                                "WHERE project_id=%s AND prompt_id=%s::uuid "
                                "  AND (backlog_ref IS NULL OR backlog_ref <> 'SKIP')",
                                (ref_id, project_id, pid),
                            )

                    # Stamp standalone commits
                    if commits_entry and standalone_commits:
                        ref_id = commits_entry["ref_id"]
                        for c in standalone_commits:
                            cur.execute(
                                "UPDATE mem_mrr_commits SET backlog_ref=%s "
                                "WHERE commit_hash=%s AND project_id=%s",
                                (ref_id, c["id"], project_id),
                            )
                conn.commit()
        except Exception as e:
            log.warning(f"full_digest: _mark_processed error: {e}")


async def process_full_digest(project: str) -> dict:
    """Module-level convenience: run the full-digest pipeline for a project."""
    bl = MemoryBacklog(project)
    fd = _FullDigest(bl)
    return await fd.run()


# ── Use-case file helpers ──────────────────────────────────────────────────────

_USE_CASE_STUB = """\
# {slug}
status: 1
created_at: {created_at}
updated_at: {created_at}
total_events: 0

## Summary
{summary}

## Delivery
_Code stack, commits count, and storage paths — updated on refresh._

## Completed Action Items
<!-- Entries moved here when done -->

## Completed Bugs
<!-- Entries moved here when done -->

## Open Items
<!-- AI-appended from approved backlog entries -->

## Open Bugs
<!-- AI-appended from approved backlog entries -->

## Events
<!-- system-managed: rebuilt from mem_backlog_links — do not edit -->
| ID | Source | Date | Summary |
|----|--------|------|---------|
"""


def _slug_path(uc_dir: Path, slug: str) -> Path:
    return uc_dir / f"{slug}.md"


def _create_use_case(uc_dir: Path, slug: str, entry: dict) -> None:
    """Create a new use case file from stub template, then merge entry."""
    uc_dir.mkdir(parents=True, exist_ok=True)
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        today = date.today().strftime("%Y/%m/%d")
        stub = _USE_CASE_STUB.format(
            slug=slug,
            summary=entry.get("summary", ""),
            created_at=today,
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

    # Determine section: bugs → Open Bugs, everything else → Open Items
    section_tag = "## Open Bugs" if classify == "bug" else "## Open Items"

    action_items = entry.get("action_items", [])
    acceptance = ""
    if action_items:
        first = action_items[0]
        acceptance = first.get("acceptance", "") if isinstance(first, dict) else ""

    new_item = (
        f"- [ ] {summary}\n"
        + (f"  Acceptance: {acceptance}\n" if acceptance else "")
        + (f"  Linked: {ref_id}\n" if ref_id else "")
    )

    # Insert after the section heading (before next ## heading)
    if section_tag in text:
        idx = text.index(section_tag) + len(section_tag)
        # Skip past any comment line immediately after the heading
        rest = text[idx:]
        comment_m = re.match(r"\n<!--[^>]*-->", rest)
        skip = len(comment_m.group()) if comment_m else 0
        text = text[:idx + skip] + "\n" + new_item + text[idx + skip:]
    else:
        text = text.rstrip() + f"\n\n{section_tag}\n{new_item}"

    # Append to Events table
    src_type = ref_id[0] if ref_id else "?"
    type_label = {"P": "prompt", "C": "commit", "M": "message", "I": "item"}.get(src_type, "?")
    row = f"| {ref_id} | {type_label} | {dt} | {summary[:60]} |"
    if "## Events" in text:
        lines = text.splitlines()
        insert_at = None
        for i, line in enumerate(lines):
            if line.startswith("| ID") or line.startswith("| id"):
                insert_at = i + 2  # after header + separator
                break
        if insert_at is not None:
            lines.insert(insert_at, row)
            text = "\n".join(lines) + "\n"
        else:
            text = text.rstrip() + f"\n{row}\n"
    else:
        text = (
            text.rstrip()
            + "\n\n## Events\n"
            "<!-- system-managed: rebuilt from mem_backlog_links — do not edit -->\n"
            "| ID | Source | Date | Summary |\n"
            "|----|--------|------|---------|\n"
            + row + "\n"
        )

    path.write_text(text)
    log.info(f"use_case: merged {ref_id} → {slug}")


# ── mem_backlog_links helpers ─────────────────────────────────────────────────

def _insert_backlog_link(
    project_id: int,
    ref_id: str,
    tag_id: Optional[str],
    use_case_slug: str,
    classify: str,
    summary: str,
) -> None:
    """Insert or update a mem_backlog_links row for an approved backlog entry.

    This is the stable DB record that survives .md file edits/deletion.
    UNIQUE(project_id, ref_id) — one backlog entry can only belong to one use case.
    """
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mem_backlog_links
                       (project_id, ref_id, tag_id, use_case_slug, classify, summary)
                       VALUES (%s, %s, %s::uuid, %s, %s, %s)
                       ON CONFLICT (project_id, ref_id) DO UPDATE SET
                           tag_id        = COALESCE(EXCLUDED.tag_id, mem_backlog_links.tag_id),
                           use_case_slug = EXCLUDED.use_case_slug,
                           classify      = EXCLUDED.classify,
                           summary       = EXCLUDED.summary,
                           approved_at   = NOW()""",
                    (project_id, ref_id, tag_id, use_case_slug, classify, summary or ""),
                )
            conn.commit()
    except Exception as e:
        log.warning(f"_insert_backlog_link({ref_id}→{use_case_slug}) error: {e}")


def _regenerate_internal_usage(uc_dir: Path, slug: str, project_id: int) -> None:
    """Rebuild the ## Internal Usage table in a use case file from mem_backlog_links.

    Called when the section is missing or when run_work_items() finishes.
    Safe to call multiple times — always rebuilds from DB truth.
    """
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        return
    if not db.is_available():
        return

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT ref_id, classify, summary, approved_at
                       FROM mem_backlog_links
                       WHERE project_id=%s AND use_case_slug=%s
                       ORDER BY approved_at""",
                    (project_id, slug),
                )
                rows = cur.fetchall()
    except Exception as e:
        log.debug(f"_regenerate_internal_usage query error: {e}")
        return

    if not rows:
        return

    # Build the Events table rows
    type_label = {"P": "prompt", "C": "commit", "M": "message", "I": "item"}
    table_lines = [
        "## Events",
        "<!-- system-managed: rebuilt from mem_backlog_links — do not edit -->",
        "| ID | Source | Date | Summary |",
        "|----|--------|------|---------|",
    ]
    for ref_id, classify, summary, approved_at in rows:
        src = ref_id[0] if ref_id else "?"
        t = type_label.get(src, "?")
        dt = approved_at.strftime("%Y-%m-%d") if approved_at else ""
        table_lines.append(f"| {ref_id} | {t} | {dt} | {(summary or '')[:60]} |")

    new_section = "\n".join(table_lines) + "\n"

    text = path.read_text(errors="ignore")

    # Replace ## Events section (or ## Internal Usage for legacy files) to end-of-file
    for marker in ("## Events", "## Internal Usage"):
        if marker in text:
            idx = text.index(marker)
            text = text[:idx].rstrip() + "\n\n" + new_section
            break
    else:
        text = text.rstrip() + "\n\n" + new_section

    path.write_text(text)
    log.info(f"_regenerate_internal_usage: rebuilt {len(rows)} rows → {slug}.md")


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
            classify = entry.get("classify", "use_case")
            if classify not in _CLASSIFY_TO_TAG:
                classify = "use_case"

            # Slug comes directly from entry (set in header by user or LLM)
            slug = entry.get("slug", "").strip() or "general"
            slug = re.sub(r"[^a-z0-9\-]", "-", slug.lower()).strip("-") or "general"

            try:
                if not _slug_path(uc_dir, slug).exists():
                    _create_use_case(uc_dir, slug, entry)
                else:
                    _merge_into_use_case(uc_dir, slug, entry)
                use_cases_updated.add(slug)
            except Exception as e:
                log.warning(f"run_work_items: file merge error for {entry['ref_id']}: {e}")

            # Step 3b: upsert planner_tag with seq_num + file_ref
            tag_uuid: Optional[str] = None
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
                    tag_uuid, seq_num = tag_result
                    display_id = _tag_display_id(classify, seq_num)
                    tags_created.append({
                        "slug":       slug,
                        "tag_id":     tag_uuid,
                        "seq_num":    seq_num,
                        "display_id": display_id,
                        "classify":   classify,
                        "ref_id":     entry["ref_id"],
                    })
                    log.info(
                        f"backlog: planner_tag {display_id} ({slug}) "
                        f"linked to {entry['ref_id']}"
                    )

                # Step 3c: insert stable DB linkage record
                _insert_backlog_link(
                    project_id=project_id,
                    ref_id=entry["ref_id"],
                    tag_id=tag_uuid,
                    use_case_slug=slug,
                    classify=classify,
                    summary=entry.get("summary", ""),
                )

            approved_ids.append(entry["ref_id"])

        elif ap == "-":
            rejected_ids.append(entry["ref_id"])
        else:
            pending.append(entry)

    # Step 5: rewrite backlog
    if approved_ids or rejected_ids:
        bl.rewrite(keep=pending, processed=approved_ids, rejected=rejected_ids)

    # Step 6: regenerate ## Internal Usage in all touched use case files
    # (rebuilds from mem_backlog_links — survives manual edits/deletion)
    if project_id:
        for slug in use_cases_updated:
            try:
                _regenerate_internal_usage(uc_dir, slug, project_id)
            except Exception as e:
                log.debug(f"run_work_items: regenerate_internal_usage({slug}) error: {e}")

    return {
        "flushed":           total_flushed,
        "flushed_by_source": flushed,
        "approved":          len(approved_ids),
        "rejected":          len(rejected_ids),
        "pending":           len(pending),
        "use_cases_updated": sorted(use_cases_updated),
        "tags_created":      tags_created,
    }
