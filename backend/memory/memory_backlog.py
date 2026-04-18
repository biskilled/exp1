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

# Primary prompt config: backend/prompts/backlog.yaml
# Fallback / legacy template kept for project-level override copies
_BACKLOG_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "backlog.yaml"
_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "workspace" / "_templates" / "backlog_config.yaml"
# Use case prompts: backend/prompts/use_case.yaml
_USE_CASE_PROMPTS_PATH = Path(__file__).parent.parent / "prompts" / "use_case.yaml"

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

# New GROUP header: ## **slug** · YY/MM/DD-HH:MM [APPROVE] (source)
_GROUP_HEADER_RE = re.compile(
    r"^## \*\*([^*]+)\*\*"                          # group 1: slug (bold)
    r"\s+·\s+"
    r"(\d{2}/\d{2}/\d{2}(?:-\d{2}:\d{2})?)"        # group 2: date
    r"\s+\[([+ x\-]*)\]"                            # group 3: approve
    r"\s+\(([^)]*)\)"                               # group 4: source
)

# New ITEM header: SOURCE REF_ID [APPROVE] [CLASSIFY] [STATUS] [AI_SCORE] — summary
_ITEM_HEADER_RE = re.compile(
    r"^\s*(PROMPTS|COMMITS|ITEMS|MESSAGES)\s+"
    r"([PCMI]\d+)\s+"
    r"\[([+ x\-]*)\]\s+"
    r"\[([^\]]*)\]\s+"   # classify: feature|bug|task
    r"\[([^\]]*)\]\s+"   # status: in-progress|completed
    r"\[(\d)\]\s+"       # ai_score: 0-5
    r"—\s+(.+)$"
)

# Keep old regex for backward-compat parsing of old-format entries
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
        """Load pipeline config.

        Priority order (later overrides earlier):
          1. backend/prompts/backlog.yaml  — system prompt definitions
          2. {code_dir}/.ai/backlog_config.yaml — project-level overrides (optional)
        """
        if self._cfg is not None:
            return self._cfg

        # 1. Base: backend/prompts/backlog.yaml
        base_cfg: dict = {}
        if _BACKLOG_PROMPTS_PATH.exists():
            try:
                base_cfg = yaml.safe_load(_BACKLOG_PROMPTS_PATH.read_text()) or {}
            except Exception as e:
                log.debug(f"backlog.yaml load error: {e}")

        # 2. Project-level overrides
        code_dir = _get_code_dir(self.project)
        if code_dir:
            cfg_path = code_dir / ".ai" / "backlog_config.yaml"
        else:
            cfg_path = Path(settings.workspace_dir) / self.project / ".ai" / "backlog_config.yaml"

        if cfg_path.exists():
            try:
                project_cfg = yaml.safe_load(cfg_path.read_text()) or {}
                # Deep-merge: for dict values, merge recursively one level
                merged = dict(base_cfg)
                for k, v in project_cfg.items():
                    if isinstance(v, dict) and isinstance(merged.get(k), dict):
                        merged[k] = {**merged[k], **v}
                    else:
                        merged[k] = v
                self._cfg = merged
            except Exception as e:
                log.debug(f"project backlog_config read error: {e}")
                self._cfg = base_cfg
        else:
            self._cfg = base_cfg

        return self._cfg

    def _use_case_cfg(self) -> dict:
        """Load use_case.yaml prompts."""
        if _USE_CASE_PROMPTS_PATH.exists():
            try:
                return yaml.safe_load(_USE_CASE_PROMPTS_PATH.read_text()) or {}
            except Exception as e:
                log.debug(f"use_case.yaml load error: {e}")
        return {}

    def _source_cfg(self, source_type: str) -> dict:
        return self._config().get("mirroring_event_summary", {}).get(source_type, {})

    def _cnt(self, source_type: str) -> int:
        return int(self._source_cfg(source_type).get("cnt", 99999))

    def _backlog_path(self) -> Path:
        cfg = self._config()
        fname = cfg.get("file_name", "backlog.md")
        if cfg.get("rotation"):
            today = date.today().strftime("%Y-%m-%d")
            fname = f"backlog_{today}.md"
        base = Path(settings.workspace_dir) / self.project
        return base / "documents" / fname

    def _rejected_path(self) -> Path:
        return self._backlog_path().parent / "rejected.md"

    def _use_cases_dir(self) -> Path:
        base = Path(settings.workspace_dir) / self.project
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
            """SELECT id::text, prompt, response, created_at,
                      COALESCE(tags->>'source', 'user') as source,
                      tags as tags_json
               FROM mem_mrr_prompts
               WHERE project_id=%s AND backlog_ref IS NULL
               ORDER BY created_at LIMIT 500""",
            (project_id,),
        )
        rows = cur.fetchall()
        result: list[dict] = []
        for r in rows:
            prompt_id, prompt, response, created_at, source = r[0], r[1], r[2], r[3], r[4]
            tags_raw  = r[5]
            tags_json = tags_raw if isinstance(tags_raw, dict) else {}
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
                "created_at": created_at, "source": source,
                "tags_json": tags_json, "commits": commit_contexts,
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
            # Skip commits with no code symbols (system/infra commits with no
            # tracked source changes — nothing useful to show in the backlog)
            if not symbols:
                log.debug(f"backlog: skipping no-symbol commit {c_hash[:8]}")
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
        sp      = self._cfg.get("system_prompt", {})
        extra   = sp.get("commits_context", "") if source_type == "commits" else sp.get("prompts_context", "")
        tagging = sp.get("tagging_rules", "")
        schema  = sp.get("json_schema", "")
        return (
            f"{p_desc}\n\n{extra}\n"
            f"Active use cases for matching:\n{uc_context}\n\n"
            f"{tagging}\n{schema}"
        ).strip()

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
        """Parse backlog.md and return list of groups, each with nested items.

        Supports both new GROUP format and old flat entry format (backward compat).
        Returns list of group dicts:
          {date, approve, source, slug, slug_type, user_tags, ai_existing_tags,
           ai_new_tags, items: [{ref_id, src_label, approve, classify, status,
           ai_score, summary, requirements, deliveries, raw}]}
        """
        path = self._backlog_path()
        if not path.exists():
            return []
        text = path.read_text(errors="ignore")

        # Only parse the pending section (before archive)
        archive_idx = text.find("\n## Processed ")
        pending_text = text[:archive_idx] if archive_idx != -1 else text

        groups: list[dict] = []

        for chunk in re.split(r"\n\n?---\n\n?", pending_text):
            chunk = chunk.strip()
            if not chunk:
                continue

            lines = chunk.splitlines()

            # ── Try new GROUP format ──────────────────────────────────────
            group_m = None
            for ln in lines:  # scan all lines (first chunk includes file header)
                group_m = _GROUP_HEADER_RE.match(ln.strip())
                if group_m:
                    break

            if group_m:
                slug      = group_m.group(1).strip()
                dt        = group_m.group(2)
                ap_raw    = group_m.group(3).strip()
                source    = group_m.group(4).strip()

                approve = "x" if ap_raw in ("+", "x") else ("-" if ap_raw == "-" else " ")

                # Parse metadata lines (new "> Key: ..." format + old "<!-- G_TYPE -->" compat)
                slug_type   = "existing"
                user_tags: list[str] = []
                ai_existing: list[dict] = []
                ai_new:      list[dict] = []
                group_summary: str = ""
                group_completed: list[str] = []    # requirement strings
                group_action_items: list[dict] = [] # delivery dicts

                for ln in lines:
                    ls = ln.strip()
                    # Only parse group-level metadata lines: "> Key: value" or "<!-- G_... -->"
                    # Item sub-lines ("    Requirements:" / "    Deliveries:") are indented
                    # and must NOT be processed as group metadata.
                    if ls.startswith("> "):
                        ls = ls[2:]
                    elif ls.startswith("<!-- G_"):
                        pass  # handled below as HTML comment compat
                    else:
                        continue  # skip item headers, sub-lines, blank lines
                    # Old HTML comment compat
                    if ls.startswith("<!-- G_TYPE:"):
                        slug_type = ls.split(":", 1)[1].strip(" -->").strip()
                    elif ls.startswith("Type:"):
                        slug_type = ls[len("Type:"):].strip()
                    elif ls.startswith("User tags:"):
                        raw_tags = ls[len("User tags:"):].strip()
                        # Support both "; " and "," separators
                        sep = ";" if ";" in raw_tags else ","
                        user_tags = [t.strip() for t in raw_tags.split(sep) if t.strip()]
                    elif ls.startswith("AI existing:"):
                        raw = ls[len("AI existing:"):].strip()
                        for chip in re.findall(r"\[([^\]]+)\]", raw):
                            parts = chip.split(":", 1)
                            if len(parts) == 2:
                                ai_existing.append({"category": parts[0], "name": parts[1]})
                    elif ls.startswith("AI new:"):
                        raw = ls[len("AI new:"):].strip()
                        for chip in re.findall(r"\[([^\]]+)\]", raw):
                            parts = chip.split(":", 1)
                            if len(parts) == 2:
                                ai_new.append({"category": parts[0], "name": parts[1]})
                    elif ls.startswith("Summary:"):
                        group_summary = ls[len("Summary:"):].strip()
                    elif ls.startswith("Requirements:"):
                        raw = ls[len("Requirements:"):].strip()
                        group_completed = [c.strip() for c in raw.split(";") if c.strip()]
                    elif ls.startswith("Deliveries:"):
                        raw = ls[len("Deliveries:"):].strip()
                        # Format: [classify|status|ai_score|event_count|name|tag_id] summary; ...
                        for part in raw.split("; "):
                            part = part.strip()
                            # New 6-field format (backward-compatible): [classify|status|score|N|name|tag_id] summary
                            m2 = re.match(
                                r"\[([^\]]+)\|([^\]]+)\|(\d+)\|(\d+)(?:\|([^\]]*)\|([^\]]*))?\]\s*(.*)",
                                part
                            )
                            if m2:
                                group_action_items.append({
                                    "classify":    m2.group(1),
                                    "status":      m2.group(2),
                                    "ai_score":    int(m2.group(3)),
                                    "event_count": int(m2.group(4)),
                                    "name":        m2.group(5) or "",
                                    "tag_id":      m2.group(6) or "",
                                    "desc":        m2.group(7).strip(),
                                })
                                continue
                            # Old format without event_count: [classify|status|score] summary
                            m2 = re.match(r"\[([^\]]+)\|([^\]]+)\|(\d+)\]\s*(.*)", part)
                            if m2:
                                group_action_items.append({
                                    "classify":    m2.group(1),
                                    "status":      m2.group(2),
                                    "ai_score":    int(m2.group(3)),
                                    "event_count": 1,
                                    "name":        "",
                                    "tag_id":      "",
                                    "desc":        m2.group(4).strip(),
                                })
                            elif part:
                                group_action_items.append({
                                    "classify": "task", "status": "in-progress",
                                    "ai_score": 0, "name": "", "tag_id": "", "desc": part,
                                })
                    # Backward compat: old "Completed:" and "Action items:" lines
                    elif ls.startswith("Completed:"):
                        raw = ls[len("Completed:"):].strip()
                        group_completed = [c.strip() for c in raw.split(";") if c.strip()]
                    elif ls.startswith("Action items:"):
                        raw = ls[len("Action items:"):].strip()
                        for part in raw.split(";"):
                            part = part.strip()
                            m2 = re.match(r"\[([^\]]+)\]\s+(.+)", part)
                            if m2:
                                group_action_items.append({
                                    "classify": m2.group(1), "status": "in-progress",
                                    "ai_score": 0, "name": "", "tag_id": "", "desc": m2.group(2),
                                })
                            elif part:
                                group_action_items.append({
                                    "classify": "task", "status": "in-progress",
                                    "ai_score": 0, "name": "", "tag_id": "", "desc": part,
                                })

                # Parse items
                items: list[dict] = []
                current_item: Optional[dict] = None

                for ln in lines:
                    item_m = _ITEM_HEADER_RE.match(ln)
                    if item_m:
                        if current_item:
                            items.append(current_item)
                        src_label  = item_m.group(1)
                        ref_id     = item_m.group(2)
                        iap_raw    = item_m.group(3).strip()
                        classify   = item_m.group(4).strip()
                        status     = item_m.group(5).strip()
                        ai_score   = int(item_m.group(6))
                        summary    = item_m.group(7).strip()

                        i_approve = "x" if iap_raw in ("+", "x") else ("-" if iap_raw == "-" else " ")
                        current_item = {
                            "ref_id":    ref_id,
                            "src_label": src_label,
                            "approve":   i_approve,
                            "classify":  classify,
                            "status":    status,
                            "ai_score":  ai_score,
                            "summary":   summary,
                            "requirements": "",
                            "deliveries":   "",
                            "group_slug":   slug,
                            "raw":          ln,
                        }
                    elif current_item:
                        ls = ln.strip()
                        if ls.startswith("Requirements:"):
                            val = ls[len("Requirements:"):].strip()
                            # Skip char-corrupted values like "H; i; s; t; o"
                            parts = val.split("; ")
                            if not (len(parts) >= 2 and all(len(p) <= 2 for p in parts)):
                                current_item["requirements"] = val
                        elif ls.startswith("Deliveries:"):
                            val = ls[len("Deliveries:"):].strip()
                            parts = val.split("; ")
                            if not (len(parts) >= 2 and all(len(p) <= 2 for p in parts)):
                                current_item["deliveries"] = val
                        elif ls and not ls.startswith("<!--") and not ls.startswith("> ") \
                             and not ls.startswith("Total:") \
                             and not ls.startswith("User tags") and not ls.startswith("AI "):
                            current_item["raw"] += "\n" + ln

                if current_item:
                    items.append(current_item)

                groups.append({
                    "date":             dt,
                    "approve":          approve,
                    "source":           source,
                    "slug":             slug,
                    "slug_type":        slug_type,
                    "user_tags":        user_tags,
                    "ai_existing_tags": ai_existing,
                    "ai_new_tags":      ai_new,
                    "summary":          group_summary,
                    "requirements":     group_completed,   # list of requirement strings
                    "deliveries":       group_action_items, # list of {classify,status,ai_score,desc}
                    "items":            items,
                })
                continue

            # ── Fallback: old flat format (may have multiple entry headers) ──
            entry_starts = [
                i for i, ln in enumerate(lines)
                if _ENTRY_HEADER_RE.match(ln.strip())
            ]
            if not entry_starts:
                # Also try _ITEM_HEADER_RE at top level (bare items without group header)
                item_group: list[dict] = []
                for ln in lines:
                    item_m = _ITEM_HEADER_RE.match(ln)
                    if item_m:
                        item_group.append({
                            "ref_id":    item_m.group(2),
                            "src_label": item_m.group(1),
                            "approve":   "x" if item_m.group(3).strip() in ("+","x") else (" " if item_m.group(3).strip() == "" else "-"),
                            "classify":  item_m.group(4).strip(),
                            "status":    item_m.group(5).strip(),
                            "ai_score":  int(item_m.group(6)),
                            "summary":   item_m.group(7).strip(),
                            "requirements": "", "deliveries": "",
                            "group_slug": "discovery", "raw": ln,
                        })
                if item_group:
                    groups.append({
                        "date": "", "approve": " ", "source": "auto",
                        "slug": "discovery", "slug_type": "existing",
                        "user_tags": [], "ai_existing_tags": [], "ai_new_tags": [],
                        "items": item_group,
                    })
                continue

            # Old format: wrap each entry as a synthetic group
            for j, start_i in enumerate(entry_starts):
                end_i = entry_starts[j + 1] if j + 1 < len(entry_starts) else len(lines)
                entry_chunk = "\n".join(lines[start_i:end_i]).strip()
                if not entry_chunk:
                    continue
                entry = self._parse_entry(entry_chunk)
                if entry:
                    groups.append({
                        "date": entry.get("date", ""),
                        "approve": entry.get("approve", " "),
                        "source": "auto",
                        "slug": entry.get("slug", "discovery"),
                        "slug_type": "existing",
                        "user_tags": [], "ai_existing_tags": [], "ai_new_tags": [],
                        "items": [{
                            "ref_id":    entry["ref_id"],
                            "src_label": entry.get("source", "PROMPTS"),
                            "approve":   entry.get("approve", " "),
                            "classify":  entry.get("classify", "task"),
                            "status":    "in-progress",
                            "ai_score":  0,
                            "summary":   entry.get("summary", ""),
                            "requirements": "", "deliveries": "",
                            "group_slug": entry.get("slug", "discovery"),
                            "raw": entry.get("raw", ""),
                        }],
                    })

        return groups

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
        groups: list[dict],
        processed: list[str],
        rejected_items: list[dict],
    ) -> None:
        """Rewrite backlog.md after run_work_items.

        - Approved items (processed) are removed entirely (moved to use case files).
        - Rejected items move to the >>>>>>> REJECTED <<<<<< section at the bottom.
        - Groups that still have pending items stay at the top, re-rendered.
        """
        path = self._backlog_path()
        today = date.today().strftime("%Y-%m-%d")

        handled = set(processed) | {e.get("ref_id", "") for e in rejected_items}

        # Re-render groups keeping only pending items
        pending_blocks: list[str] = []
        for grp in groups:
            pending_items = [
                it for it in grp.get("items", [])
                if it.get("ref_id", "") not in handled
            ]
            if pending_items:
                pending_group = {**grp, "items": pending_items}
                pending_blocks.append(_fmt_group_block(pending_group))

        header = (
            "# Backlog\n\n"
            "> Review each use case group. Approve `[+]` items, reject `[-]`.\n"
            "> Run `POST /memory/{project}/work-items/sync` to merge approved items into use cases.\n\n"
        )

        new_text = header
        if pending_blocks:
            new_text += "\n\n---\n\n".join(pending_blocks) + "\n"

        # ── Write rejected items to rejected.md (separate file) ─────────────
        if rejected_items:
            rej_path = self._rejected_path()
            existing_rej = rej_path.read_text(errors="ignore") if rej_path.exists() else ""

            new_rej_blocks: list[str] = []
            for item in rejected_items:
                block = _fmt_item_entry(item, item.get("src_label", "PROMPTS")).strip()
                new_rej_blocks.append(block + f"\n  <!-- Rejected: {today} -->")

            if new_rej_blocks:
                if not existing_rej.strip():
                    existing_rej = (
                        "# Rejected\n\n"
                        "> Items moved here when rejected during backlog review.\n\n"
                    )
                rej_path.write_text(
                    existing_rej.rstrip() + "\n\n"
                    + "\n\n".join(new_rej_blocks) + "\n"
                )

        path.write_text(new_text)
        log.info(
            f"backlog: rewrite — {len(pending_blocks)} pending groups, "
            f"{len(processed)} processed, {len(rejected_items)} rejected"
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


def _fmt_event_entry(e: dict, src_label: str, slug: str) -> str:
    """Format a single source event (prompt or commit) as one backlog entry line.

    All entries default to [+] (approved) — user changes to [-] to reject.
    """
    ref_id   = e.get("ref_id", "?")
    dt       = _fmt_date(e.get("date"))
    classify = e.get("classify", "task")
    summary  = (e.get("summary") or "")[:100]
    user     = e.get("user", "auto")

    lines = [
        f"{src_label} {dt} {ref_id} [+] [{slug}] [{classify}] ({user}) — {summary}",
        "",
    ]

    reqs = e.get("requirements", "")
    if reqs:
        if isinstance(reqs, list):
            lines.append(f"  Requirements: {'; '.join(str(r) for r in reqs[:5])}")
        else:
            lines.append(f"  Requirements: {str(reqs)[:300]}")

    completed = e.get("completed", [])
    if completed:
        if isinstance(completed, list):
            lines.append(f"  Completed: {'; '.join(str(c) for c in completed[:5])}")
        else:
            lines.append(f"  Completed: {str(completed)[:300]}")

    ais = e.get("action_items", [])
    if ais:
        ai_strs: list[str] = []
        for ai in ais[:3]:
            if isinstance(ai, dict):
                desc = ai.get("desc", "")
                acc  = ai.get("acceptance", "")
                ai_strs.append(desc + (f" (acceptance: {acc})" if acc else ""))
            else:
                ai_strs.append(str(ai))
        if ai_strs:
            lines.append(f"  Action items: {'; '.join(ai_strs)}")

    return "\n".join(lines)


class _FullDigest:
    """Full-pass digest: groups ALL pending events by use case.

    Produces one backlog entry PER SOURCE EVENT (one per prompt, one per standalone
    commit), organized under GROUP section headers in backlog.md.
    """

    def __init__(self, bl: "MemoryBacklog") -> None:
        self.bl = bl
        cfg_root = bl._config().get("full_digest", {})
        self.max_groups       = int(cfg_root.get("max_groups", 7))
        self.grouping_cfg     = cfg_root.get("grouping_prompt", {})
        self.summary_cfg      = cfg_root.get("summary_prompt", {})
        self.commits_batch_cfg = cfg_root.get("commits_batch_summary_prompt",
                                              cfg_root.get("commits_summary_prompt", {}))

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
                    prompt_rows        = bl._fetch_prompts_with_commit_context(cur, project_id)
                    standalone_commits = bl._fetch_standalone_commits(cur, project_id)
        except Exception as e:
            log.warning(f"full_digest: fetch error: {e}")

        if not prompt_rows and not standalone_commits:
            log.info("full_digest: nothing pending")
            return {"appended": 0, "groups": 0,
                    "total_prompts": 0, "total_standalone_commits": 0}

        log.info(
            f"full_digest: {len(prompt_rows)} prompts, "
            f"{len(standalone_commits)} standalone commits"
        )

        # 2. Allocate all ref IDs upfront (one P per prompt, one C per commit)
        p_refs = bl._allocate_refs(project_id, "P", len(prompt_rows))
        c_refs = bl._allocate_refs(project_id, "C", len(standalone_commits))

        # 3. Group prompts into use case buckets (commits handled separately)
        groups = await self._group_all_events(prompt_rows, uc_context)

        # 4. For each group, batch-summarize prompts → per-event entries
        group_sections: list[dict] = []
        total_entries = 0
        # Maps: source_id → ref_id (for DB stamping)
        prompt_stamp: dict[str, str] = {}
        commit_stamp: dict[str, str] = {}

        for group in groups:
            slug      = group.get("slug", "general")
            slug_type = group.get("slug_type", "existing")
            classify  = group.get("classify", "task")
            topic     = group.get("topic", slug)
            p_indices = [i for i in group.get("prompt_indices", []) if i < len(prompt_rows)]

            grp_prompt_rows = [prompt_rows[i] for i in p_indices]
            if not grp_prompt_rows:
                continue

            entries: list[dict] = []
            summaries = await self._summarize_prompts_batch(grp_prompt_rows, slug, classify)
            for j, row in enumerate(grp_prompt_rows):
                global_i = p_indices[j]
                ref_id   = p_refs[global_i] if global_i < len(p_refs) else f"P?{global_i}"
                sv       = summaries[j] if j < len(summaries) else {}
                entries.append({
                    "ref_id":       ref_id,
                    "date":         row["created_at"],
                    "src_label":    "PROMPTS",
                    "approve":      " ",
                    "summary":      sv.get("summary", (row.get("prompt") or "")[:80].replace("\n", " ")),
                    "classify":     sv.get("classify", classify),
                    "status":       sv.get("status", "in-progress"),
                    "ai_score":     int(sv.get("ai_score", 0)),
                    "user":         row.get("source", "user"),
                    "requirements": sv.get("requirements", []),
                    "deliveries":   sv.get("deliveries", sv.get("completed", [])),
                    "action_items": sv.get("action_items", []),
                })
                prompt_stamp[row["id"]] = ref_id

            # Collect user tags from all prompts in this group
            user_tags_set: set[str] = set()
            for row in grp_prompt_rows:
                tags_json = row.get("tags_json") or {}
                for k, v in (tags_json.items() if isinstance(tags_json, dict) else []):
                    if k not in ("source",) and v:
                        user_tags_set.add(f"{k}:{v}")
            dates = [r["created_at"] for r in grp_prompt_rows if r.get("created_at")]
            earliest = min(dates) if dates else date.today()

            group_sections.append({
                "slug":             slug,
                "slug_type":        slug_type,
                "topic":            topic,
                "date":             _fmt_date(earliest),
                "source":           grp_prompt_rows[0].get("source", "auto"),
                "approve":          " ",
                "user_tags":        sorted(user_tags_set),
                "ai_existing_tags": group.get("ai_existing_tags", []),
                "ai_new_tags":      group.get("ai_new_tags", []),
                "items":            entries,
                # group_deliveries filled after synthesis call below
                "group_deliveries": [],
            })
            total_entries += len(entries)

        # 5. Group-level synthesis: cluster events into 3-5 thematic deliveries
        for gs in group_sections:
            if gs.get("items"):
                gs["group_deliveries"] = await self._synthesize_group_deliveries(
                    gs["items"], gs["slug"], gs.get("topic", gs["slug"])
                )

        # 6. All standalone commits → one "general-commits" group
        if standalone_commits:
            commits_section = await self._build_commits_group(
                standalone_commits, c_refs, commit_stamp
            )
            if commits_section:
                group_sections.append(commits_section)
                total_entries += len(commits_section.get("items", []))

        # 7. Write backlog.md with GROUP sections
        self._write_group_sections(group_sections)

        # 6. Stamp all source rows
        self._mark_processed_v2(project_id, prompt_stamp, commit_stamp,
                                prompt_rows, standalone_commits)

        return {
            "appended":                 total_entries,
            "groups":                   len(group_sections),
            "total_prompts":            len(prompt_rows),
            "total_standalone_commits": len(standalone_commits),
        }

    # ── LLM helpers ─────────────────────────────────────────────────────────

    async def _group_all_events(
        self,
        prompt_rows: list[dict],
        uc_context: str,
    ) -> list[dict]:
        """Group prompts into max_groups use case buckets.

        Standalone commits are handled separately in _build_commits_group().
        """
        if not prompt_rows:
            return []

        model = self.grouping_cfg.get("llm", settings.haiku_model)
        desc  = self.grouping_cfg.get("desc", "")

        items: list[str] = []
        for i, r in enumerate(prompt_rows):
            p    = (r.get("prompt") or "")[:120].replace("\n", " ")
            dt   = str(r.get("created_at", ""))[:10]
            c_ct = len(r.get("commits", []))
            suffix = f" [{c_ct} commits]" if c_ct else ""
            items.append(f"[P{i}] {dt} {p}{suffix}")

        system_p = f"""{desc}

Active use cases:
{uc_context}

Rules:
- Group into AT MOST {self.max_groups} groups.
- Each event key (P0, P1, ...) must appear in exactly one group.
- Prefer existing slugs. Create new slug only if truly new topic.
- New slugs must be lowercase-hyphenated (e.g. "stripe-billing").
- slug_type: "existing" or "new"
- classify: "bug" | "feature" | "task" — dominant intent of the group
- Merge minor topics (1-3 events) into the closest related group.

Return JSON array only. No markdown. No extra text.
[{{"slug":"discovery","slug_type":"existing","classify":"task",
   "topic":"Discovery and architecture work",
   "prompt_indices":[0,1,2]}}]"""

        user_p = f"Total prompts: {len(items)}\n\n" + "\n".join(items)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=4000)

        fallback = [{
            "slug": "discovery", "slug_type": "existing", "classify": "task",
            "topic": "all development work",
            "prompt_indices": list(range(len(prompt_rows))),
        }]

        if not raw:
            return fallback

        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            groups = json.loads(cleaned)
            if not isinstance(groups, list):
                raise ValueError("not a list")

            groups = [g for g in groups if g.get("slug", "").upper() != "SKIP"]
            groups = groups[:self.max_groups]

            covered_p = {i for g in groups for i in g.get("prompt_indices", [])}
            leftover_p = [i for i in range(len(prompt_rows)) if i not in covered_p]
            if leftover_p:
                if groups:
                    groups[-1].setdefault("prompt_indices", []).extend(leftover_p)
                else:
                    groups = [{
                        "slug": "discovery", "slug_type": "existing", "classify": "task",
                        "topic": "general work", "prompt_indices": leftover_p,
                    }]
            return groups

        except Exception as e:
            log.warning(f"full_digest: _group_all_events parse error: {e}\nraw={raw[:200]}")
            return fallback

    async def _build_commits_group(
        self,
        standalone_commits: list[dict],
        c_refs: list[str],
        commit_stamp: dict[str, str],
    ) -> Optional[dict]:
        """Build the 'general-commits' group from all standalone commits.

        Generates an aggregated summary from symbol data (files/classes/methods).
        Each commit becomes one item — pre-approved, no user interaction needed.
        """
        if not standalone_commits:
            return None

        # Summarize commits via LLM (one batch call for all commits)
        classify = "task"
        c_summaries = await self._summarize_commits_batch(standalone_commits, "general-commits", classify)

        entries: list[dict] = []
        for j, row in enumerate(standalone_commits):
            ref_id = c_refs[j] if j < len(c_refs) else f"C?{j}"
            sv     = c_summaries[j] if j < len(c_summaries) else {}

            # Build deliveries from code symbols for this commit
            sym_deliveries: list[str] = []
            seen_sym: set[str] = set()
            for s in row.get("symbols", [])[:10]:
                cls = f"{s['class']}." if s.get("class") else ""
                mth = s.get("method") or ""
                nm  = f"{cls}{mth}" if (cls or mth) else s.get("file", "")
                label = f"{s.get('file','?')}: {nm} (+{s.get('+',0)}/-{s.get('-',0)})"
                if label not in seen_sym:
                    seen_sym.add(label)
                    sym_deliveries.append(label)

            entries.append({
                "ref_id":     ref_id,
                "date":       row.get("created_at"),
                "src_label":  "COMMITS",
                "approve":    "+",   # commits are always auto-approved
                "summary":    sv.get("summary", (row.get("commit_msg") or "")[:80]),
                "classify":   sv.get("classify", classify),
                "status":     "completed",
                "ai_score":   int(sv.get("ai_score", 5)),
                "user":       "auto",
                "deliveries": sym_deliveries,
                "requirements": "",
            })
            commit_stamp[row["id"]] = ref_id

        # Build group-level topic summary: aggregate unique files/classes
        all_files: list[str] = []
        all_classes: set[str] = set()
        seen_files: set[str] = set()
        for row in standalone_commits:
            for s in row.get("symbols", []):
                f = s.get("file", "")
                if f and f not in seen_files:
                    seen_files.add(f)
                    all_files.append(f)
                if s.get("class"):
                    all_classes.add(s["class"])

        n = len(standalone_commits)
        file_sample = ", ".join(all_files[:6]) + ("…" if len(all_files) > 6 else "")
        class_sample = (", ".join(sorted(all_classes)[:4]) + ("…" if len(all_classes) > 4 else "")) if all_classes else ""
        topic = (
            f"{n} commit{'s' if n != 1 else ''} updating: {file_sample}"
            + (f" | classes: {class_sample}" if class_sample else "")
        )

        earliest = min(
            (r["created_at"] for r in standalone_commits if r.get("created_at")),
            default=date.today(),
        )
        return {
            "slug":             "general-commits",
            "slug_type":        "existing",
            "topic":            topic,
            "date":             _fmt_date(earliest),
            "source":           "auto",
            "approve":          "+",
            "user_tags":        [],
            "ai_existing_tags": [],
            "ai_new_tags":      [],
            "items":            entries,
        }

    def _build_event_block(self, i: int, r: dict, global_offset: int = 0) -> str:
        """Format one prompt row into a text block for the summarization prompt."""
        p    = (r.get("prompt")   or "")[:600].replace("\n", " ").strip()
        resp = (r.get("response") or "")[:500].replace("\n", " ").strip()
        tags_json = r.get("tags_json") or {}
        tag_parts = [f"{k}:{v}" for k, v in tags_json.items() if k not in ("source",) and v]
        tags_line = f"\nTAGS: {' | '.join(tag_parts)}" if tag_parts else ""
        block = f"[{i + global_offset}]\nPROMPT: {p}{tags_line}\nRESPONSE: {resp}"
        for ctx in r.get("commits", []):
            block += f"\nCOMMIT {ctx['hash'][:8]}: {ctx['msg'][:120]}"
            for sym in ctx.get("symbols", [])[:10]:
                cls = f"{sym['class']}." if sym.get("class") else ""
                mth = sym.get("method") or ""
                nm  = f"{cls}{mth}" if (cls or mth) else sym.get("file", "")
                block += f"\n  {sym.get('file','?')}: {nm} (+{sym.get('+',0)}/-{sym.get('-',0)})"
        return block

    async def _summarize_chunk(
        self,
        rows: list[dict],
        global_offset: int,
        slug: str,
        classify: str,
        model: str,
        desc: str,
        max_tokens: int,
    ) -> list[dict]:
        """Summarize a single chunk (≤10 events). Returns list aligned with input."""
        def _fallback(i: int, r: dict) -> dict:
            return {
                "summary": (r.get("prompt") or "")[:80].replace("\n", " "),
                "classify": classify, "requirements": [], "deliveries": [],
                "action_items": [], "status": "in-progress", "ai_score": 0,
            }

        # Always use local 0-based indices so LLM output aligns regardless of chunk offset
        parts = [self._build_event_block(i, r, 0) for i, r in enumerate(rows)]
        system_p = (
            f"{desc}\n\nUse case: {slug}  |  default classify: {classify}\n\n"
            f"IMPORTANT: Return a valid JSON ARRAY — one element per event, same count "
            f"and order as input. Array length MUST equal {len(rows)}. "
            f"event_index values: {list(range(len(rows)))} (0-based within this chunk)."
        )
        user_p = f"Events ({len(rows)}):\n\n" + "\n\n---\n\n".join(parts)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=max_tokens)

        if not raw:
            return [_fallback(i, r) for i, r in enumerate(rows)]

        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                # event_index is local (0-based); map directly
                result_map = {item.get("event_index", j): item for j, item in enumerate(result)}
                return [result_map.get(i, _fallback(i, r)) for i, r in enumerate(rows)]
        except Exception as e:
            log.warning(f"full_digest: _summarize_chunk (offset={global_offset}) parse error: {e}")
        return [_fallback(i, r) for i, r in enumerate(rows)]

    async def _summarize_prompts_batch(
        self, rows: list[dict], slug: str, classify: str
    ) -> list[dict]:
        """Batch-summarize prompts → one dict per event.

        Processes in chunks of chunk_size (default 10) to avoid token-limit
        truncation on large groups. Returns list aligned with input rows.
        """
        model      = self.summary_cfg.get("llm", settings.haiku_model)
        desc       = self.summary_cfg.get("desc", "")
        max_tokens = int(self.summary_cfg.get("max_tokens", 4000))
        chunk_size = int(self.summary_cfg.get("chunk_size", 10))

        results: list[dict] = []
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            chunk_results = await self._summarize_chunk(
                chunk, start, slug, classify, model, desc, max_tokens
            )
            results.extend(chunk_results)

        return results

    async def _synthesize_group_deliveries(
        self, event_summaries: list[dict], slug: str, topic: str
    ) -> list[dict]:
        """Post-process: cluster event summaries into 3-5 thematic group deliveries.

        Returns list of {summary, classify, status, ai_score, event_count} dicts,
        sorted completed-first by ai_score desc.
        """
        cfg        = self.bl._config().get("full_digest", {}).get("group_synthesis_prompt", {})
        model      = cfg.get("llm", settings.haiku_model)
        desc       = cfg.get("desc", "")
        max_tokens = int(cfg.get("max_tokens", 1000))

        if not desc or not event_summaries:
            return []

        lines: list[str] = []
        for i, sv in enumerate(event_summaries):
            reqs = sv.get("requirements", [])
            reqs_str = "; ".join(reqs[:2]) if isinstance(reqs, list) else str(reqs)[:100]
            lines.append(
                f"[{i}] [{sv.get('classify','task')}|{sv.get('status','in-progress')}|"
                f"{sv.get('ai_score',0)}] {sv.get('summary','')[:100]} | req: {reqs_str}"
            )

        system_p = f"{desc}\n\nUse case slug: {slug}\nGroup topic: {topic}"
        user_p   = f"Events ({len(event_summaries)}):\n" + "\n".join(lines)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=max_tokens)

        if not raw:
            return []
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                done = sorted(
                    [r for r in result if r.get("status") == "completed"],
                    key=lambda x: -int(x.get("ai_score", 0)),
                )
                prog = sorted(
                    [r for r in result if r.get("status") != "completed"],
                    key=lambda x: -int(x.get("ai_score", 0)),
                )
                return done + prog
        except Exception as e:
            log.warning(f"full_digest: _synthesize_group_deliveries parse error: {e}")
        return []

    async def _summarize_commits_batch(
        self, commits: list[dict], slug: str, classify: str
    ) -> list[dict]:
        """Batch-summarize standalone commits → one dict per commit.

        Data source: commit message + all symbols from mem_mrr_commits_code.
        classify is inferred from commit message keywords + symbol changes.
        """
        model      = self.commits_batch_cfg.get("llm", settings.haiku_model)
        desc       = self.commits_batch_cfg.get("desc", "")
        max_tokens = int(self.commits_batch_cfg.get("max_tokens", 6000))

        parts: list[str] = []
        for i, c in enumerate(commits):
            msg   = (c.get("commit_msg") or "")[:200]
            block = f"[{i}] COMMIT: {msg}"
            symbols = c.get("symbols", [])
            for sym in symbols[:15]:
                cls = f"{sym['class']}." if sym.get("class") else ""
                mth = sym.get("method") or ""
                nm  = f"{cls}{mth}" if (cls or mth) else sym.get("file", "")
                chg = sym.get("change", "")
                block += (
                    f"\n  [{chg}] {sym.get('file','?')}: {nm}"
                    f" (+{sym.get('+',0)}/-{sym.get('-',0)})"
                )
            parts.append(block)

        system_p = f"""{desc}

Use case: {slug}

IMPORTANT: Return a valid JSON ARRAY — one element per commit, same count and order.
Array length MUST equal {len(commits)}."""

        user_p = f"Commits ({len(commits)}):\n\n" + "\n\n---\n\n".join(parts)
        raw = await _call_haiku(system_p, user_p, model, max_tokens=max_tokens)

        def _fallback(i: int, c: dict) -> dict:
            return {
                "summary": (c.get("commit_msg") or "")[:80],
                "classify": "task", "deliveries": [], "status": "completed", "ai_score": 5,
            }

        if not raw:
            return [_fallback(i, c) for i, c in enumerate(commits)]

        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                result_map = {item.get("event_index", j): item for j, item in enumerate(result)}
                return [result_map.get(i, _fallback(i, c)) for i, c in enumerate(commits)]
        except Exception as e:
            log.warning(f"full_digest: _summarize_commits_batch parse error: {e}")
        return [_fallback(i, c) for i, c in enumerate(commits)]

    # ── File I/O ────────────────────────────────────────────────────────────

    def _write_group_sections(self, groups: list[dict]) -> None:
        """Write GROUP sections to backlog.md using the new group format."""
        path = self.bl._backlog_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        section_blocks = [_fmt_group_block(g) for g in groups]
        content = "\n\n---\n\n".join(section_blocks)

        # Preserve archive
        archive_block = ""
        if path.exists():
            existing = path.read_text(errors="ignore")
            idx = existing.find("\n## Processed ")
            if idx != -1:
                archive_block = existing[idx:]

        header = (
            "# Backlog\n\n"
            "> Review each use case group. Approve `[+]` items, reject `[-]`.\n"
            "> Run `POST /memory/{project}/work-items` to merge approved items into use cases.\n\n"
        )
        path.write_text(header + content + "\n" + archive_block)
        log.info(
            f"full_digest: wrote {sum(len(g.get('items',[])) for g in groups)} items "
            f"across {len(groups)} groups → {path}"
        )

    # ── DB marking ──────────────────────────────────────────────────────────

    def _mark_processed_v2(
        self,
        project_id: int,
        prompt_stamp: dict[str, str],
        commit_stamp: dict[str, str],
        prompt_rows: list[dict],
        standalone_commits: list[dict],
    ) -> None:
        """Stamp each source row with its individual ref_id."""
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    for row in prompt_rows:
                        pid = row["id"]
                        ref = prompt_stamp.get(pid)
                        if not ref:
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_prompts SET backlog_ref=%s "
                            "WHERE id=%s::uuid AND project_id=%s",
                            (ref, pid, project_id),
                        )
                        # Stamp commits linked to this prompt with the same ref
                        cur.execute(
                            "UPDATE mem_mrr_commits SET backlog_ref=%s "
                            "WHERE project_id=%s AND prompt_id=%s::uuid "
                            "  AND (backlog_ref IS NULL OR backlog_ref <> 'SKIP')",
                            (ref, project_id, pid),
                        )
                    for row in standalone_commits:
                        cid = row["id"]
                        ref = commit_stamp.get(cid)
                        if not ref:
                            continue
                        cur.execute(
                            "UPDATE mem_mrr_commits SET backlog_ref=%s "
                            "WHERE commit_hash=%s AND project_id=%s",
                            (ref, cid, project_id),
                        )
                conn.commit()
        except Exception as e:
            log.warning(f"full_digest: _mark_processed_v2 error: {e}")


def _fmt_item_entry(e: dict, src_label: str) -> str:
    """Format a single event item in the new GROUP format.

    Format: SOURCE REF_ID [APPROVE] [CLASSIFY] [STATUS] [AI_SCORE] — summary
    """
    ref_id   = e.get("ref_id", "?")
    approve  = e.get("approve", " ")
    classify = e.get("classify", "task")
    status   = e.get("status", "in-progress")
    ai_score = e.get("ai_score", 0)
    summary  = (e.get("summary") or "")[:100]

    lines = [
        f"  {src_label} {ref_id} [{approve}] [{classify}] [{status}] [{ai_score}] — {summary}",
    ]

    reqs = e.get("requirements", "")
    if reqs:
        if isinstance(reqs, list):
            req_str = "; ".join(str(r) for r in reqs[:5])
        else:
            req_str = str(reqs)[:300]
        lines.append(f"    Requirements: {req_str}")

    deliveries = e.get("deliveries", "") or e.get("completed", "")
    if deliveries:
        if isinstance(deliveries, list):
            del_str = "; ".join(str(d) for d in deliveries[:5])
        else:
            del_str = str(deliveries)[:300]
        lines.append(f"    Deliveries: {del_str}")

    return "\n".join(lines)


def _fmt_group_block(group: dict) -> str:
    """Format a full GROUP section for backlog.md."""
    slug      = group.get("slug", "general")
    slug_type = group.get("slug_type", "existing")
    date_str  = group.get("date", "")
    source    = group.get("source", "auto")
    approve   = group.get("approve", " ")
    items     = group.get("items", [])

    # Count by source type
    cnt = {"PROMPTS": 0, "COMMITS": 0, "MESSAGES": 0, "ITEMS": 0}
    for it in items:
        cnt[it.get("src_label", "PROMPTS")] += 1

    total_line = " · ".join(
        f"{v} {k.lower()}" for k, v in cnt.items() if v > 0
    ) or "0 events"

    user_tags     = group.get("user_tags", [])
    ai_existing   = group.get("ai_existing_tags", [])
    ai_new        = group.get("ai_new_tags", [])

    lines = [
        f"## **{slug}** · {date_str} [{approve}] ({source})",
        f"> Type: {slug_type}",
        f"> Total: {total_line}",
    ]

    if user_tags:
        lines.append(f"> User tags: {'; '.join(str(t) for t in user_tags)}")
    else:
        lines.append("> User tags:")

    if ai_existing:
        chips = " ".join(
            f"[{t.get('category','?')}:{t.get('name','?')}]"
            for t in ai_existing
        )
        lines.append(f"> AI existing: {chips}")
    else:
        lines.append("> AI existing:")

    if ai_new:
        chips = " ".join(
            f"[{t.get('category','?')}:{t.get('name','?')}]"
            for t in ai_new
        )
        lines.append(f"> AI new: {chips}")
    else:
        lines.append("> AI new:")

    # Aggregate requirements text from all items
    seen_reqs: set[str] = set()
    all_reqs: list[str] = []
    for it in items:
        reqs = it.get("requirements", "")
        if isinstance(reqs, str):
            for r in reqs.split(";"):
                r = r.strip()
                if r and r not in seen_reqs:
                    seen_reqs.add(r)
                    all_reqs.append(r)
        elif isinstance(reqs, list):
            for r in reqs:
                r = str(r).strip()
                if r and r not in seen_reqs:
                    seen_reqs.add(r)
                    all_reqs.append(r)

    topic = group.get("topic", "")
    if topic:
        lines.append(f"> Summary: {topic}")
    if all_reqs[:5]:
        lines.append(f"> Requirements: {'; '.join(all_reqs[:5])}")

    # Synthesised group deliveries (3-5 thematic items from LLM synthesis call)
    group_deliveries: list[dict] = group.get("group_deliveries", [])
    if group_deliveries:
        delivery_strs: list[str] = []
        for d in group_deliveries[:5]:
            name   = d.get("name", "")
            tag_id = d.get("tag_id", "")
            delivery_strs.append(
                f"[{d.get('classify','task')}|{d.get('status','in-progress')}|"
                f"{d.get('ai_score',0)}|{d.get('event_count',1)}|{name}|{tag_id}]"
                f" {d.get('summary','')}"
            )
        lines.append(f"> Deliveries: {'; '.join(delivery_strs)}")

    lines.append("")

    # Group items by source type, then by classify
    type_order    = ["PROMPTS", "COMMITS", "MESSAGES", "ITEMS"]
    classify_order = ["feature", "bug", "task"]

    for src_type in type_order:
        type_items = [it for it in items if it.get("src_label") == src_type]
        if not type_items:
            continue
        # Sort by classify order
        type_items.sort(
            key=lambda x: classify_order.index(x.get("classify", "task"))
            if x.get("classify", "task") in classify_order else 99
        )
        for it in type_items:
            lines.append(_fmt_item_entry(it, src_type))
            lines.append("")

    return "\n".join(lines).rstrip()


async def process_full_digest(project: str) -> dict:
    """Module-level convenience: run the full-digest pipeline for a project."""
    bl = MemoryBacklog(project)
    fd = _FullDigest(bl)
    return await fd.run()


# ── Use-case file helpers ──────────────────────────────────────────────────────

_USE_CASE_STUB = """\
# {slug}
<!-- STATUS: 1 -->
<!-- STATUS_VALUES: 1=not started | 2=in progress | 3=done -->
<!-- CREATED: {created_at} -->
<!-- UPDATED: {created_at} -->
<!-- EVENTS: 0 -->
<!-- PROMPTS: 0 -->
<!-- COMMITS: 0 -->
<!-- MESSAGES: 0 -->
<!-- ITEMS: 0 -->
<!-- NOTE: counters updated automatically on each work-items/sync run -->

## Summary

{summary}

## Requirements

- {requirement}

## Delivery

### Code

| Stack | Location | Commits |
|-------|----------|---------|
| —     | —        | 0       |

### Documents

| Name | Type | Path | Summary |
|------|------|------|---------|
| —    | —    | —    | —       |

---

## Completed

### Action Items

| Done | Events | Summary |
|------|--------|---------|
| —    | —      | —       |

### Bugs Fixed

| Fixed | Events | Summary |
|-------|--------|---------|
| —     | —      | —       |

---

## Open Items
<!-- AI-appended from approved backlog entries -->

## Open Bugs
<!-- AI-appended from approved backlog entries -->

---

## Events

<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- SYSTEM-MANAGED — items appended here on each work-items/sync run.     -->
<!-- Rebuild from DB: POST /memory/{{p}}/regenerate-use-case?slug={slug}   -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->

<!-- EVENTS_START -->

<!-- EVENTS_END -->
"""


def _slug_path(uc_dir: Path, slug: str) -> Path:
    return uc_dir / f"{slug}.md"


def _create_use_case(uc_dir: Path, slug: str, entry: dict) -> None:
    """Create a new use case file from template, then merge entry."""
    uc_dir.mkdir(parents=True, exist_ok=True)
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        today_iso  = date.today().isoformat()
        today_disp = date.today().strftime("%Y/%m/%d")
        # Try loading the use_case_template.md from the workspace templates directory
        tpl_path = (
            Path(__file__).parent.parent.parent
            / "workspace" / "_templates" / "use_cases" / "use_case_template.md"
        )
        if tpl_path.exists():
            stub = (
                tpl_path.read_text()
                .replace("{use-case-name}", slug)
                .replace("{YYYY-MM-DD}", today_iso)
                .replace("- {requirement 1}", f"- {entry.get('summary', slug)}")
                .replace("- {requirement 2}", "")
                .replace("{One-paragraph description of what this use case covers and its current state.\nUpdated by LLM summary. Edit freely — will be overwritten on llm-summary run.}", entry.get("summary", ""))
            )
        else:
            stub = _USE_CASE_STUB.format(
                slug=slug,
                summary=entry.get("summary", ""),
                requirement=entry.get("summary", ""),
                created_at=today_disp,
            )
        path.write_text(stub)
        log.info(f"use_case: created {path}")
    _merge_into_use_case(uc_dir, slug, entry)


def _fmt_event_block(entry: dict) -> str:
    """Format a backlog item as a full event block for the ## Events section."""
    ref_id    = entry.get("ref_id", "?")
    src_label = entry.get("src_label", "PROMPTS")
    classify  = entry.get("classify", "task")
    status    = entry.get("status", "in-progress")
    ai_score  = entry.get("ai_score", 0)
    dt        = _fmt_date(entry.get("date"))
    summary   = entry.get("summary", "")

    lines = [
        f"### {ref_id} · {dt} · {src_label} · {classify} · {status} · AI:{ai_score}",
        "",
        summary,
        "",
    ]

    reqs = entry.get("requirements", [])
    if isinstance(reqs, str):
        reqs = [r.strip() for r in reqs.split(";") if r.strip()]
    if reqs:
        lines.append(f"**Requirements:** {'; '.join(str(r) for r in reqs[:5])}")

    deliveries = entry.get("deliveries", []) or entry.get("completed", [])
    if isinstance(deliveries, str):
        deliveries = [d.strip() for d in deliveries.split(";") if d.strip()]
    if deliveries:
        if isinstance(deliveries[0], dict):
            d_strs = [d.get("desc", str(d)) for d in deliveries[:5]]
        else:
            d_strs = [str(d) for d in deliveries[:5]]
        lines.append(f"**Deliveries:** {'; '.join(d_strs)}")

    action_items = entry.get("action_items", [])
    if isinstance(action_items, str):
        action_items = [action_items]
    if action_items:
        lines.append("**Action items:**")
        for ai in action_items[:5]:
            if isinstance(ai, dict):
                desc = ai.get("desc", "")
                acc  = ai.get("acceptance", "")
                lines.append(f"- {desc}" + (f" (acceptance: {acc})" if acc else ""))
            else:
                lines.append(f"- {ai}")

    lines.append("")
    return "\n".join(lines)


def _merge_into_use_case(uc_dir: Path, slug: str, entry: dict) -> None:
    """Append entry into the use case file.

    1. Adds item to ## Open Items or ## Open Bugs (with AI score + acceptance).
    2. Appends full event block inside <!-- EVENTS_START --> … <!-- EVENTS_END --> markers.
    3. Increments all relevant counters in the file header metadata.
    4. Updates <!-- UPDATED: … --> date.
    """
    path = _slug_path(uc_dir, slug)
    if not path.exists():
        _create_use_case(uc_dir, slug, entry)
        return

    text = path.read_text(errors="ignore")
    ref_id   = entry.get("ref_id", "")
    summary  = entry.get("summary", "")
    classify = entry.get("classify", "task")
    dt       = entry.get("date", date.today().strftime("%Y/%m/%d"))
    src_label = entry.get("src_label", "PROMPTS")
    prefix   = ref_id[0] if ref_id else "P"

    # Deduplication guard
    if ref_id and ref_id in text:
        log.debug(f"use_case: {ref_id} already in {slug}, skipping")
        return

    # ── 1. Add to Open Items / Open Bugs ─────────────────────────────────────
    section_tag = "## Open Bugs" if classify == "bug" else "## Open Items"

    action_items = entry.get("action_items", [])
    acceptance = ""
    if action_items:
        first = action_items[0] if isinstance(action_items, list) else action_items
        if isinstance(first, dict):
            acceptance = first.get("acceptance", "")

    ai_score = entry.get("ai_score", 0)
    new_item = (
        f"- [ ] AI:{ai_score}  {summary}\n"
        + (f"  Acceptance: {acceptance}\n" if acceptance else "")
        + (f"  Linked: {ref_id}\n" if ref_id else "")
    )

    if section_tag in text:
        idx = text.index(section_tag) + len(section_tag)
        rest = text[idx:]
        comment_m = re.match(r"\n<!--[^>]*-->", rest)
        skip = len(comment_m.group()) if comment_m else 0
        text = text[:idx + skip] + "\n" + new_item + text[idx + skip:]
    else:
        text = text.rstrip() + f"\n\n{section_tag}\n{new_item}"

    # ── 2. Append full event block inside EVENTS_START … EVENTS_END ──────────
    event_block = _fmt_event_block(entry)
    divider = "---\n\n"

    if "<!-- EVENTS_START -->" in text and "<!-- EVENTS_END -->" in text:
        idx = text.index("<!-- EVENTS_END -->")
        text = text[:idx] + event_block + divider + text[idx:]
    elif "## Events" in text:
        events_idx = text.index("## Events")
        # Convert legacy table-based Events section to block format
        end_m = re.search(r"\n##\s", text[events_idx + 9:])
        if end_m:
            section_end = events_idx + 9 + end_m.start()
        else:
            section_end = len(text)
        new_events_section = (
            "## Events\n\n"
            "<!-- ═══════════════════════════════════════════════════════════════════════ -->\n"
            "<!-- SYSTEM-MANAGED — items appended here on each work-items/sync run.     -->\n"
            "<!-- ═══════════════════════════════════════════════════════════════════════ -->\n\n"
            "<!-- EVENTS_START -->\n\n"
            + event_block + divider +
            "<!-- EVENTS_END -->\n"
        )
        text = text[:events_idx] + new_events_section + text[section_end:]
    else:
        text = (
            text.rstrip()
            + "\n\n## Events\n\n"
            "<!-- EVENTS_START -->\n\n"
            + event_block + divider +
            "<!-- EVENTS_END -->\n"
        )

    # ── 3. Increment counters ─────────────────────────────────────────────────
    type_counter = {"P": "PROMPTS", "C": "COMMITS", "M": "MESSAGES", "I": "ITEMS"}.get(prefix, "PROMPTS")

    def _inc(t: str, key: str) -> str:
        pat = re.compile(rf"<!-- {key}: (\d+) -->")
        m = pat.search(t)
        if m:
            return pat.sub(f"<!-- {key}: {int(m.group(1)) + 1} -->", t, count=1)
        # Key not found — add after <!-- EVENTS: … -->
        ep = re.compile(r"<!-- EVENTS: \d+ -->")
        em = ep.search(t)
        if em:
            return t[:em.end()] + f"\n<!-- {key}: 1 -->" + t[em.end():]
        return t

    text = _inc(text, "EVENTS")
    text = _inc(text, type_counter)

    # ── 4. Update UPDATED date ────────────────────────────────────────────────
    today_iso = date.today().isoformat()
    text = re.sub(r"<!-- UPDATED: [^>]+ -->", f"<!-- UPDATED: {today_iso} -->", text)

    path.write_text(text)
    log.info(f"use_case: merged {ref_id} → {slug}")


# ── mem_backlog_links helpers ─────────────────────────────────────────────────

def _get_client_id(project_id: int) -> Optional[int]:
    """Return the client_id for a given project_id."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT client_id FROM mng_projects WHERE id=%s", (project_id,))
                row = cur.fetchone()
                return row[0] if row else None
    except Exception:
        return None


def _insert_backlog_link(
    project_id: int,
    ref_id: str,
    tag_id: Optional[str],
    use_case_slug: str,
    classify: str,
    summary: str,
    tag_name: str = "",
    use_case_id: Optional[str] = None,
    is_llm: bool = False,
    client_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> None:
    """Insert or update a mem_backlog_links row for an approved backlog entry.

    This is the stable DB record that survives .md file edits/deletion.
    UNIQUE(project_id, ref_id) — one backlog entry can only belong to one use case.

    is_llm=False  → mirror-table event (ref_id like 'P100042', 'C200001')
                    tag_id points to the use-case planner_tag
    is_llm=True   → AI-generated delivery item (ref_id = child planner_tag UUID)
                    tag_id = child planner_tag, use_case_id = parent use-case tag
    """
    if not db.is_available():
        return
    if client_id is None:
        client_id = _get_client_id(project_id)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mem_backlog_links
                       (client_id, project_id, user_id, ref_id, tag_id, tag_name,
                        use_case_id, use_case_slug, classify, is_llm, summary)
                       VALUES (%s, %s, %s, %s, %s::uuid, %s, %s::uuid, %s, %s, %s, %s)
                       ON CONFLICT (project_id, ref_id) DO UPDATE SET
                           tag_id        = COALESCE(EXCLUDED.tag_id, mem_backlog_links.tag_id),
                           tag_name      = COALESCE(EXCLUDED.tag_name, mem_backlog_links.tag_name),
                           use_case_id   = COALESCE(EXCLUDED.use_case_id, mem_backlog_links.use_case_id),
                           use_case_slug = EXCLUDED.use_case_slug,
                           classify      = EXCLUDED.classify,
                           is_llm        = EXCLUDED.is_llm,
                           summary       = EXCLUDED.summary,
                           updated_at    = NOW()""",
                    (client_id, project_id, user_id, ref_id, tag_id, tag_name or "",
                     use_case_id, use_case_slug, classify, is_llm, summary or ""),
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

    # Build the Events section with full blocks (each row is a compact block)
    type_label = {"P": "PROMPTS", "C": "COMMITS", "M": "MESSAGES", "I": "ITEMS"}
    event_blocks: list[str] = []
    for ref_id, classify, summary, approved_at in rows:
        src = ref_id[0] if ref_id else "?"
        src_label = type_label.get(src, "PROMPTS")
        dt = approved_at.strftime("%y/%m/%d-%H:%M") if approved_at else ""
        # Minimal block (DB only stores summary; full content lives in the file)
        block = (
            f"### {ref_id} · {dt} · {src_label} · {classify}\n\n"
            f"{(summary or '')}\n"
        )
        event_blocks.append(block)

    events_body = "\n---\n\n".join(event_blocks) if event_blocks else ""

    new_section = (
        "## Events\n\n"
        "<!-- ═══════════════════════════════════════════════════════════════════════ -->\n"
        "<!-- SYSTEM-MANAGED — items appended here on each work-items/sync run.     -->\n"
        "<!-- Rebuild from DB: POST /memory/{p}/regenerate-use-case?slug={slug}     -->\n"
        "<!-- ═══════════════════════════════════════════════════════════════════════ -->\n\n"
        "<!-- EVENTS_START -->\n\n"
        + events_body + ("\n\n" if events_body else "") +
        "<!-- EVENTS_END -->\n"
    )

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
    parent_id: Optional[str] = None,
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
                        creator, seq_num, file_ref, parent_id)
                       VALUES (%s, %s, %s, %s, 'open', 'ai', %s, %s, %s::uuid)
                       ON CONFLICT (project_id, name, category_id) DO UPDATE SET
                           file_ref    = COALESCE(EXCLUDED.file_ref, planner_tags.file_ref),
                           seq_num     = COALESCE(planner_tags.seq_num, EXCLUDED.seq_num),
                           parent_id   = COALESCE(planner_tags.parent_id, EXCLUDED.parent_id),
                           updated_at  = NOW()
                       RETURNING id::text, seq_num""",
                    (project_id, name, cat_id, description or name, seq_num, file_ref,
                     parent_id if parent_id else None),
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

async def run_work_items_for_group(project: str, slug: str, approve: str) -> dict:
    """Process only one named group immediately (approve all or reject all).

    approve="x" → merge all items into use case file + planner_tags
    approve="-"  → reject all items (moved to REJECTED section)
    """
    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()
    groups = bl.parse_backlog()
    target = next((g for g in groups if g.get("slug") == slug), None)
    if not target:
        return {"error": f"group '{slug}' not found"}

    approved_ids: list[str] = []
    rejected: list[dict] = []
    uc_dir = bl._use_cases_dir()
    group_tag_uuid: Optional[str] = None   # the parent planner_tag for this group's use case

    if approve == "x":
        for item in target.get("items", []):
            item["approve"] = "x"
            item_slug = (item.get("group_slug") or slug)
            item_slug = re.sub(r"[^a-z0-9\-]", "-", item_slug.lower()).strip("-") or "general"
            classify = item.get("classify", "task")
            if classify not in _CLASSIFY_TO_TAG:
                classify = "use_case"
            try:
                if not _slug_path(uc_dir, item_slug).exists():
                    _create_use_case(uc_dir, item_slug, item)
                else:
                    _merge_into_use_case(uc_dir, item_slug, item)
            except Exception as e:
                log.warning(f"run_work_items_for_group: {e}")
            if project_id:
                file_ref = f"documents/use_cases/{item_slug}.md"
                tag_result = _upsert_planner_tag(
                    project=project,
                    project_id=project_id,
                    name=item_slug,
                    classify=classify,
                    file_ref=file_ref,
                    description=item.get("summary", ""),
                )
                tag_uuid = tag_result[0] if tag_result else None
                # Track the group-level use-case tag (first item sets it; all items in a
                # group share the same slug so the tag_uuid should be consistent)
                if tag_uuid and not group_tag_uuid:
                    group_tag_uuid = tag_uuid
                # Mirror-table event → is_llm=False; tag_name = use-case slug
                _insert_backlog_link(
                    project_id=project_id,
                    ref_id=item["ref_id"],
                    tag_id=tag_uuid,
                    tag_name=item_slug,
                    use_case_id=tag_uuid,
                    use_case_slug=item_slug,
                    classify=classify,
                    is_llm=False,
                    summary=item.get("summary", ""),
                )
            approved_ids.append(item["ref_id"])

        # Create child planner_tags for each group-level delivery theme
        # and insert them as AI-generated links (is_llm=True)
        if project_id and group_tag_uuid:
            for delivery in target.get("deliveries", []):
                d_linked_id = (delivery.get("tag_id") or "").strip()
                if d_linked_id:
                    # User linked to an existing tag — just insert backlog link pointing there
                    _insert_backlog_link(
                        project_id=project_id,
                        ref_id=d_linked_id,
                        tag_id=d_linked_id,
                        tag_name=(delivery.get("name") or "").strip() or delivery.get("desc", "")[:80],
                        use_case_id=group_tag_uuid,
                        use_case_slug=slug,
                        classify=delivery.get("classify", "task"),
                        is_llm=True,
                        summary=delivery.get("desc", ""),
                    )
                    continue
                d_name = (delivery.get("name") or "").strip() or delivery.get("desc", "")[:80]
                if not d_name:
                    continue
                d_classify = delivery.get("classify", "task")
                try:
                    child_result = _upsert_planner_tag(
                        project=project,
                        project_id=project_id,
                        name=d_name,
                        classify=d_classify,
                        file_ref=f"documents/use_cases/{slug}.md",
                        description=delivery.get("desc", ""),
                        parent_id=group_tag_uuid,
                    )
                    child_uuid = child_result[0] if child_result else None
                    if child_uuid:
                        # AI-generated delivery → is_llm=True, ref_id = child tag UUID
                        _insert_backlog_link(
                            project_id=project_id,
                            ref_id=child_uuid,
                            tag_id=child_uuid,
                            tag_name=d_name,
                            use_case_id=group_tag_uuid,
                            use_case_slug=slug,
                            classify=d_classify,
                            is_llm=True,
                            summary=delivery.get("desc", ""),
                        )
                except Exception as e:
                    log.debug(f"run_work_items_for_group: child tag ({d_name}) error: {e}")

        if project_id:
            try:
                _regenerate_internal_usage(uc_dir, slug, project_id)
            except Exception as e:
                log.debug(f"run_work_items_for_group: regenerate_internal_usage({slug}) error: {e}")
    elif approve == "-":
        for item in target.get("items", []):
            item["approve"] = "-"
        rejected = list(target.get("items", []))

    bl.rewrite(groups=groups, processed=approved_ids, rejected_items=rejected)
    return {"slug": slug, "processed": len(approved_ids), "rejected": len(rejected)}


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
    groups = bl.parse_backlog()
    # Flatten all items across all groups
    approved: list[dict] = []
    rejected: list[dict] = []
    pending:  list[dict] = []
    for grp in groups:
        for item in grp.get("items", []):
            ap = item.get("approve", " ")
            if ap == "x":
                approved.append(item)
            elif ap == "-":
                rejected.append(item)
            else:
                pending.append(item)

    approved_ids: list[str] = []
    rejected_ids: list[str] = []
    use_cases_updated: set[str] = set()
    tags_created: list[dict] = []

    uc_dir = bl._use_cases_dir()

    for entry in approved:
        # Step 3a: create/merge use-case file
        classify = entry.get("classify", "use_case")
        if classify not in _CLASSIFY_TO_TAG:
            classify = "use_case"

        # Slug comes from group_slug (new format) or slug field (old format)
        slug = (entry.get("group_slug") or entry.get("slug", "")).strip() or "general"
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
                tag_name=slug,
                use_case_id=tag_uuid,
                use_case_slug=slug,
                classify=classify,
                is_llm=False,
                summary=entry.get("summary", ""),
            )

        approved_ids.append(entry["ref_id"])

    for entry in rejected:
        rejected_ids.append(entry["ref_id"])

    # Step 5: rewrite backlog (approved removed; rejected moved to REJECTED section)
    if approved_ids or rejected:
        bl.rewrite(groups=groups, processed=approved_ids, rejected_items=rejected)

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
