"""
memory_embedding.py — Layer 3 of the three-layer memory architecture.

Embeds content via OpenAI text-embedding-3-small (1536 dims) and stores in mem_ai_events.
Smart chunking splits large content into semantic units.

Public API::

    embedding = MemoryEmbedding()

    # Batch-digest N prompts in a session → mem_ai_events
    event_id = await embedding.process_prompt_batch(project, session_id, n)

    # Batch-digest all pending commits (grouped by tag context) → mem_ai_events
    n = await embedding.process_commit_batch(project)

    # Embed a document item or meeting → mem_ai_events
    event_id = await embedding.process_item(project, item_id)

    # Semantic search across mem_ai_events
    results = await embedding.semantic_search(project, query, limit=10)

    # Smart chunking helpers (static)
    chunks = MemoryEmbedding.smart_chunk_code(content, filename)
    chunks = MemoryEmbedding.smart_chunk_markdown(content)
    chunks = MemoryEmbedding.smart_chunk_diff(diff_text, commit_hash)

Degrades silently if PostgreSQL or embedding key unavailable.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from core.config import settings
from core.database import db
from core.prompt_loader import prompts as _prompts
from memory.memory_mirroring import MemoryMirroring
from memory.memory_tagging import MemoryTagging

log = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIMS = 1536

# Map file extensions to language labels
_EXT_LANG: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".go": "go",
    ".rs": "rust", ".java": "java", ".rb": "ruby", ".php": "php",
    ".cs": "csharp", ".cpp": "cpp", ".c": "c", ".sh": "shell",
    ".sql": "sql", ".yaml": "yaml", ".yml": "yaml", ".json": "json",
    ".md": "markdown", ".html": "html", ".css": "css",
}

# ── Tag fingerprint helper ─────────────────────────────────────────────────────

_USER_TAG_KEYS = frozenset({"phase", "feature", "bug", "source"})
"""Keys allowed in mem_ai_events.tags. Only user-intent context; no system metadata."""

# Files/patterns that indicate an auto-generated system commit (not real dev work)
_SYSTEM_FILE_PATTERNS = (
    "CLAUDE.md", "MEMORY.md", "PROJECT.md", ".cursorrules",
    ".ai/", ".github/copilot", "_system/", "commit_log.jsonl",
    "history.jsonl", "session_state.json",
)

def _is_system_commit(commit_msgs: list[str], diff_summaries: list[str]) -> bool:
    """Return True if the commit group looks like auto-generated system file updates."""
    # Check commit messages for system-file-only patterns
    _sys_msg_patterns = (
        "update project.md", "update claude.md", "update memory.md",
        "sync memory", "auto-commit", "update cursorrules",
        "update copilot", "update .ai/", "update _system",
    )
    all_msgs = " ".join((m or "").lower() for m in commit_msgs)
    all_diffs = " ".join((d or "").lower() for d in diff_summaries)
    combined = all_msgs + " " + all_diffs

    # If any system file appears AND no real source files, it's a system commit
    has_system_file = any(p.lower() in combined for p in _SYSTEM_FILE_PATTERNS)
    has_real_code = any(
        ext in combined for ext in (".py ", ".ts ", ".js ", ".sql ", ".yaml ")
    )
    if has_system_file and not has_real_code:
        return True
    # Explicit system message patterns with no feature/bug tag
    if any(p in all_msgs for p in _sys_msg_patterns) and not has_real_code:
        return True
    return False


def _tag_fingerprint(tags: dict) -> str:
    """Return a stable string key for grouping by user-intent tags (phase/feature/bug)."""
    relevant = {k: tags[k] for k in ("phase", "feature", "bug") if k in tags and tags[k]}
    return json.dumps(sorted(relevant.items()))


def _user_tags(tags: dict) -> dict:
    """Filter a tags dict to only user-intent keys (phase, feature, bug, source).

    Strips system metadata (llm, chunk_type, event, file, languages, symbols,
    commit_hash, commit_count, prompt_count, rows_changed, etc.) that should
    never appear in the tags column of mem_ai_events.
    """
    return {k: v for k, v in tags.items() if k in _USER_TAG_KEYS and v}


# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_UPSERT_EVENT = """
    INSERT INTO mem_ai_events
           (project_id, event_type, event_cnt, source_id, session_id,
            chunk, chunk_type, content, embedding, summary, action_items, tags, event_system)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s::jsonb, %s)
       ON CONFLICT (project_id, event_type, source_id, chunk)
       DO UPDATE SET
           event_cnt    = EXCLUDED.event_cnt,
           content      = EXCLUDED.content,
           embedding    = EXCLUDED.embedding,
           summary      = EXCLUDED.summary,
           action_items = EXCLUDED.action_items,
           tags         = EXCLUDED.tags,
           event_system = EXCLUDED.event_system
    RETURNING id
"""

_SQL_UPDATE_COMMIT_TAGS = """
    UPDATE mem_mrr_commits
    SET tags = tags || %s::jsonb
    WHERE commit_hash = %s
"""

_SQL_GET_ITEM = """
    SELECT id, item_type, title, raw_text, summary
    FROM mem_mrr_items
    WHERE project_id=%s AND id=%s::uuid
"""

_SQL_SEARCH_TPL = """
    SELECT event_type, source_id, chunk, chunk_type, content,
           tags, session_id,
           1 - (embedding <=> %s::vector) AS score
    FROM mem_ai_events
    WHERE {where}
    ORDER BY embedding <=> %s::vector
    LIMIT %s
"""

_SQL_GET_NODE_OUTPUTS = (
    "SELECT node_id, node_name, output FROM pr_graph_node_results WHERE run_id=%s AND status='done'"
)

_SQL_GET_PENDING_COMMITS_WITH_SYMBOLS = """
    SELECT c.commit_hash, c.commit_msg, c.summary, c.tags, c.session_id, c.diff_summary,
           COALESCE(array_agg(DISTINCT cc.full_symbol)
                    FILTER (WHERE cc.full_symbol IS NOT NULL), '{}') AS symbols
    FROM mem_mrr_commits c
    LEFT JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash
    WHERE c.project_id = %s AND c.event_id IS NULL
    GROUP BY c.commit_hash, c.commit_msg, c.summary, c.tags, c.session_id, c.diff_summary
    ORDER BY c.committed_at ASC NULLS LAST
"""

_SQL_GET_PENDING_PROMPTS = """
    SELECT id, prompt, response, tags
    FROM mem_mrr_prompts
    WHERE project_id = %s AND session_id = %s AND event_id IS NULL
    ORDER BY created_at ASC
"""

_SQL_BACKPROP_COMMIT_EVENT = """
    UPDATE mem_mrr_commits SET event_id=%s::uuid, summary=%s, llm=%s
    WHERE commit_hash = ANY(%s)
"""

_SQL_BACKPROP_PROMPT_EVENT = """
    UPDATE mem_mrr_prompts SET event_id=%s::uuid WHERE id = ANY(%s::uuid[])
"""


def _openai_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("openai") or None
    except Exception:
        return None


def _claude_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("claude") or get_key("anthropic") or None
    except Exception:
        return None


def _detect_language(filename: str) -> Optional[str]:
    return _EXT_LANG.get(Path(filename).suffix.lower())


def _log_pipeline_usage(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Fire-and-forget: log memory pipeline LLM/embedding costs to mng_usage_logs."""
    try:
        from core.auth import ADMIN_USER_ID
        from core.database import db as _db
        if not _db.is_available():
            return
        # Inline pricing (avoid circular import with agents/providers)
        _COST_PER_1K: dict[tuple[str, str], tuple[float, float]] = {
            ("claude", "claude-haiku-4-5-20251001"):     (0.00025, 0.00125),
            ("claude", "claude-haiku-4-5"):              (0.00025, 0.00125),
            ("openai", "text-embedding-3-small"):        (0.00002, 0.0),
            ("openai", "text-embedding-3-large"):        (0.00013, 0.0),
        }
        key = (provider, model)
        in_rate, out_rate = _COST_PER_1K.get(key, (0.001, 0.003))
        cost_usd = (input_tokens * in_rate + output_tokens * out_rate) / 1000.0
        with _db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_usage_logs
                       (user_id, provider, model, input_tokens, output_tokens,
                        cost_usd, charged_usd, source)
                       VALUES (%s, %s, %s, %s, %s, %s, 0, 'memory')""",
                    (ADMIN_USER_ID, provider, model,
                     input_tokens, output_tokens, cost_usd),
                )
    except Exception as _e:
        log.debug(f"_log_pipeline_usage error: {_e}")


async def _embed(text: str) -> Optional[list[float]]:
    """Call OpenAI embeddings API. Returns None on failure."""
    key = _openai_key()
    if not key:
        return None
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=key)
        resp = await client.embeddings.create(model=_EMBEDDING_MODEL, input=text[:8000])
        tok = getattr(resp.usage, "total_tokens", len(text) // 4)
        _log_pipeline_usage("openai", _EMBEDDING_MODEL, tok, 0)
        return resp.data[0].embedding
    except Exception as e:
        log.debug(f"_embed error: {e}")
        return None


async def _haiku(system: str, user: str, max_tokens: int = 200) -> str:
    """Call Claude Haiku for a digest or classification. Returns '' on failure."""
    key = _claude_key()
    if not key:
        return ""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
        resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if hasattr(resp, "usage"):
            _log_pipeline_usage(
                "claude", settings.haiku_model,
                getattr(resp.usage, "input_tokens", 0),
                getattr(resp.usage, "output_tokens", 0),
            )
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_haiku error: {e}")
        return ""


def _parse_haiku_json(raw: str, fallback: str) -> tuple[str, str]:
    """Return (summary, action_items). Handles plain-text fallback gracefully."""
    try:
        # Strip markdown fences if present
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
        parsed = json.loads(clean)
        return parsed.get("summary", fallback), parsed.get("action_items", "")
    except (json.JSONDecodeError, AttributeError, ValueError):
        return raw or fallback, ""


def _upsert_event(
    project: str,
    source_type: str,
    source_id: str,
    chunk: int,
    chunk_type: str,
    content: str,
    embedding: Optional[list[float]],
    *,
    session_id: Optional[str] = None,
    summary: Optional[str] = None,
    action_items: str = "",
    tags: dict | None = None,
    event_cnt: int = 1,
    is_system: bool = False,
    # backward-compat kwargs — accepted but ignored for tags (system metadata, not stored)
    metadata: dict | None = None,
    doc_type: Optional[str] = None,
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    llm_source: Optional[str] = None,
    session_desc: Optional[str] = None,
    cnt_prompts: Optional[int] = None,
    importance: int = 1,  # accepted but ignored — column dropped (m037)
) -> Optional[str]:
    """Insert or update a row in mem_ai_events. Returns UUID string.

    tags: only user-intent context keys are stored — phase, feature, bug, source.
          All system metadata (llm, chunk_type, event, file, symbols, etc.) is stripped
          before insert so the column stays clean for filtering and work-item matching.
    event_cnt: number of mirror rows this event aggregates (e.g. 5 prompts, 3 commits).
    """
    if not db.is_available():
        return None
    # Keep only user-intent tags; strip all system/technical metadata
    clean_tags = _user_tags({**(tags or {}), **(metadata or {})})
    vec_str = f"[{','.join(str(x) for x in embedding)}]" if embedding else None
    project_id = db.get_or_create_project_id(project)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_EVENT,
                    (project_id, source_type, event_cnt, source_id, session_id,
                     chunk, chunk_type, content, vec_str, summary,
                     action_items, json.dumps(clean_tags), is_system),
                )
                row = cur.fetchone()
        return str(row[0]) if row else None
    except Exception as e:
        log.debug(f"_upsert_event error: {e}")
        return None


def _read_commit_min_diff_lines(project: str) -> int:
    """Read commit_code_extraction.min_diff_lines from project.yaml (default 5)."""
    try:
        import yaml as _yaml
        from pathlib import Path as _Path
        proj_yaml = _Path(settings.workspace_dir) / project / "project.yaml"
        if proj_yaml.exists():
            cfg = _yaml.safe_load(proj_yaml.read_text()) or {}
            return int(cfg.get("commit_code_extraction", {}).get("min_diff_lines", 5))
    except Exception:
        pass
    return 5


def _count_diff_stat_lines(diff_summary: str) -> int:
    """Parse total changed lines from git --stat output.

    e.g. '3 files changed, 10 insertions(+), 5 deletions(-)' → 15
    Returns 0 if summary is missing/unparseable.
    """
    import re as _re
    total = 0
    for count, _ in _re.findall(r"(\d+) (insertion|deletion)", diff_summary):
        total += int(count)
    return total


class MemoryEmbedding:
    """Embeds and stores content in mem_ai_events; provides semantic search."""

    def __init__(self) -> None:
        self._mirroring = MemoryMirroring()
        self._tagging   = MemoryTagging()

    # ── Process functions ──────────────────────────────────────────────────

    async def process_prompt_batch(
        self,
        project: str,
        session_id: str,
        n: int,
        session_desc: Optional[str] = None,
    ) -> Optional[str]:
        """Digest pending prompts in a session, grouped by tag context.

        Queries all prompts with event_id IS NULL (unprocessed) for the session,
        groups them by phase/feature/bug tag fingerprint, creates one mem_ai_events
        row per group, and back-propagates event_id to mem_mrr_prompts.

        The `n` parameter is kept for API compatibility but is no longer used as
        a limit — all pending prompts are processed.

        Returns the last event_id created (or None if nothing to process).
        """
        if not db.is_available():
            return None
        project_id = db.get_or_create_project_id(project)

        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_PENDING_PROMPTS, (project_id, session_id))
                    rows = cur.fetchall()
        except Exception as e:
            log.debug(f"process_prompt_batch DB query error: {e}")
            return None

        if not rows:
            return None

        # Group by tag fingerprint (phase/feature/bug) preserving insertion order
        groups: dict[str, list] = {}
        group_order: list[str] = []
        for pid, prompt, response, tags in rows:
            tags = tags or {}
            fp = _tag_fingerprint(tags)
            if fp not in groups:
                groups[fp] = []
                group_order.append(fp)
            groups[fp].append({
                "id": str(pid),
                "prompt": prompt,
                "response": response,
                "tags": tags,
            })

        last_event_id: Optional[str] = None

        for fp in group_order:
            group = groups[fp]

            pairs = "\n\n".join(
                f"Q: {(p['prompt'] or '')[:500]}\nA: {(p['response'] or '')[:800]}"
                for p in group
            )

            raw = await _prompts.call("prompt_batch_digest", pairs)
            if not raw:
                continue
            summary_text, action_items = _parse_haiku_json(raw, pairs[:200])

            embedding = await _embed(summary_text)

            # source_id = last prompt UUID in this tag group
            source_id = group[-1]["id"]

            # Merged tags = union of user-intent tags from all prompts in group
            # prompt_count and llm are system metadata → stored in event_cnt, not tags
            merged_tags: dict = {}
            for p in group:
                for k, v in (p["tags"] or {}).items():
                    if k not in merged_tags:
                        merged_tags[k] = v

            event_id = _upsert_event(
                project, "prompt_batch", source_id, 0, "full", summary_text, embedding,
                session_id=session_id,
                summary=summary_text, action_items=action_items,
                tags=merged_tags, event_cnt=len(group),
            )

            if event_id:
                last_event_id = event_id
                # Back-propagate event_id to all prompts in this group
                prompt_ids = [p["id"] for p in group]
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(_SQL_BACKPROP_PROMPT_EVENT, (event_id, prompt_ids))
                except Exception as _e:
                    log.debug(f"process_prompt_batch back-propagation error: {_e}")

                # Chunk long responses (raw embed, no LLM)
                chunk_idx = 1
                for p in group:
                    resp = p.get("response", "")
                    if len(resp.split()) > 400:
                        resp_chunks = MemoryEmbedding.smart_chunk_text(resp)
                        if len(resp_chunks) > 1:
                            for rc in resp_chunks:
                                rc_emb = await _embed(rc["content"])
                                _upsert_event(
                                    project, "prompt_batch", source_id, chunk_idx,
                                    rc.get("chunk_type", "section"), rc["content"], rc_emb,
                                    session_id=session_id, tags=merged_tags,
                                )
                                chunk_idx += 1

        if not last_event_id:
            return None

        # Process pending commits as tag-grouped batch events.
        # Runs after prompt digests so prompt events exist before work item extraction.
        try:
            await self.process_commit_batch(project)
        except Exception as _e:
            log.debug(f"process_prompt_batch: commit batch error: {_e}")

        # Auto-trigger work item extraction in background (fire-and-forget).
        try:
            import asyncio
            from memory.memory_promotion import MemoryPromotion
            asyncio.ensure_future(MemoryPromotion().extract_work_items_from_events(project, batch_size=5))
        except Exception as _e:
            log.debug(f"process_prompt_batch: auto-extract skipped: {_e}")

        return last_event_id

    async def process_commit_batch(
        self,
        project: str,
        min_commits: int = 1,
    ) -> int:
        """Digest all pending commits as tag-grouped batch events.

        Groups commits with identical phase/feature/bug tags into a single
        mem_ai_events row per group. Back-propagates event_id + summary + llm
        to all commits in each group.

        Returns count of events created. Defers if fewer than min_commits pending.
        """
        if not db.is_available():
            return 0
        project_id = db.get_or_create_project_id(project)

        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_PENDING_COMMITS_WITH_SYMBOLS, (project_id,))
                    rows = cur.fetchall()
        except Exception as e:
            log.debug(f"process_commit_batch DB query error: {e}")
            return 0

        if len(rows) < min_commits:
            return 0

        # Group by tag fingerprint (phase/feature/bug) preserving order
        groups: dict[str, list] = {}
        group_order: list[str] = []
        for commit_hash, commit_msg, summary, tags, session_id, diff_summary, symbols in rows:
            tags = tags or {}
            fp = _tag_fingerprint(tags)
            if fp not in groups:
                groups[fp] = []
                group_order.append(fp)
            groups[fp].append({
                "commit_hash": commit_hash,
                "commit_msg": commit_msg,
                "summary": summary,
                "tags": tags,
                "session_id": session_id,
                "diff_summary": diff_summary,
                "symbols": list(symbols) if symbols else [],
            })

        events_created = 0
        for fp in group_order:
            group = groups[fp]

            # Build content: commit messages + changed symbols + diff stats
            msg_parts = " | ".join(
                (g["commit_msg"] or g["commit_hash"][:8]) for g in group[:10]
            )
            all_symbols = list({s for g in group for s in (g["symbols"] or [])})[:20]
            diff_sum = next((g["diff_summary"] for g in group if g["diff_summary"]), "")

            content = f"Commits: {msg_parts}"
            if all_symbols:
                content += f"\nChanged: {', '.join(all_symbols)}"
            if diff_sum:
                content += f"\nStats: {diff_sum[:200]}"

            raw = await _prompts.call("commit_digest", content)
            summary_text, action_items = (
                _parse_haiku_json(raw, msg_parts[:300]) if raw else (msg_parts[:300], "")
            )

            embedding = await _embed(summary_text)

            # source_id: batch_{first_hash8}_{tag_fingerprint_md5_8}
            tag_fp8 = hashlib.md5(fp.encode()).hexdigest()[:8]
            first_hash8 = group[0]["commit_hash"][:8]
            source_id = f"batch_{first_hash8}_{tag_fp8}"

            # Merged tags = union of user-intent tags from all commits in group
            # commit_count and llm are system metadata → stored in event_cnt, not tags
            merged_tags: dict = {}
            for g in group:
                for k, v in (g["tags"] or {}).items():
                    if k not in merged_tags:
                        merged_tags[k] = v

            # Use session_id from first commit (group may span sessions)
            session_id = group[0].get("session_id")

            # Detect system-only commits (PROJECT.md / CLAUDE.md / MEMORY.md updates)
            sys_flag = _is_system_commit(
                [g["commit_msg"] for g in group],
                [g["diff_summary"] for g in group],
            )

            event_id = _upsert_event(
                project, "commit", source_id, 0, "full", content, embedding,
                session_id=session_id,
                summary=summary_text, action_items=action_items,
                tags=merged_tags, event_cnt=len(group),
                is_system=sys_flag,
            )

            if event_id:
                events_created += 1
                # Back-propagate event_id + summary to all commits in group
                hashes = [g["commit_hash"] for g in group]
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                _SQL_BACKPROP_COMMIT_EVENT,
                                (event_id, summary_text, settings.haiku_model, hashes),
                            )
                except Exception as _e:
                    log.debug(f"process_commit_batch back-propagation error: {_e}")

        log.info(
            f"process_commit_batch: {events_created} events from "
            f"{len(rows)} commits ({len(group_order)} tag groups) for {project}"
        )
        return events_created

    async def process_item(
        self,
        project: str,
        item_id: str,
    ) -> Optional[str]:
        """Digest and embed a mem_mrr_items document.

        Short items (<200 words): single digest chunk.
        Long/meeting items: split into sections via meeting_sections prompt.
        Returns first chunk UUID.
        """
        if not db.is_available():
            return None
        _i_project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_ITEM, (_i_project_id, item_id))
                    row = cur.fetchone()
            if not row:
                return None
            _, item_type, title, raw_text, summary = row
        except Exception as e:
            log.debug(f"process_item DB error: {e}")
            return None

        # Fetch MRR tags for this item to merge into events
        item_mrr_tags: dict = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tags FROM mem_mrr_items WHERE project_id=%s AND id=%s::uuid",
                        (_i_project_id, item_id),
                    )
                    tr = cur.fetchone()
                    if tr:
                        item_mrr_tags = tr[0] or {}
        except Exception:
            pass

        word_count = len(raw_text.split())

        if item_type == "meeting" or word_count > 200:
            # Split into sections
            sections_raw = await _prompts.call("meeting_sections", raw_text[:6000])
            try:
                sections = json.loads(sections_raw)
            except Exception:
                sections = [{"title": title or item_type, "content": raw_text[:3000]}]

            first_id = None
            for i, sec in enumerate(sections):
                content = f"{sec.get('title', '')}\n{sec.get('content', '')}"
                emb = await _embed(content)
                event_id = _upsert_event(
                    project, "item", item_id, i, "section", content[:6000], emb,
                    tags={**item_mrr_tags, "doc_type": item_type,
                          "title": sec.get("title", ""), "section_index": str(i)},
                )
                if i == 0:
                    first_id = event_id
            result_id = first_id
        else:
            raw = await _prompts.call("item_digest", raw_text[:3000])
            item_summary, item_action_items = _parse_haiku_json(raw, (summary or raw_text)[:300]) if raw else ((summary or raw_text)[:300], "")
            emb = await _embed(item_summary)
            result_id = _upsert_event(
                project, "item", item_id, 0, "full", item_summary, emb,
                summary=item_summary, action_items=item_action_items,
                tags={**item_mrr_tags, "doc_type": item_type},
            )

        if not result_id:
            return None

        # Relation extraction — lightweight Haiku call to detect tag relationships
        rel_raw = await _prompts.call("relation_extraction", raw_text[:3000])
        if rel_raw:
            try:
                rel_parsed = json.loads(rel_raw)
                relations = rel_parsed.get("relations", [])
                if relations:
                    from memory.memory_tagging import MemoryTagging
                    MemoryTagging().upsert_relations_from_list(
                        project, relations, source="item_extraction"
                    )
            except Exception:
                pass

        return result_id

    async def process_messages(
        self,
        project: str,
        message_id: str,
    ) -> Optional[str]:
        """Embed a mem_mrr_messages chunk. Returns UUID or None."""
        if not db.is_available():
            return None
        _m_project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, platform, channel, messages FROM mem_mrr_messages "
                        "WHERE project_id=%s AND id=%s::uuid",
                        (_m_project_id, message_id),
                    )
                    row = cur.fetchone()
            if not row:
                return None
            _, platform, channel, messages_json = row
        except Exception as e:
            log.debug(f"process_messages DB error: {e}")
            return None

        if isinstance(messages_json, str):
            try:
                messages = json.loads(messages_json)
            except Exception:
                messages = []
        else:
            messages = messages_json or []

        text = " ".join(
            f"{m.get('user', '')}: {m.get('text', '')}"
            for m in (messages if isinstance(messages, list) else [])
        )[:6000]

        raw = await _prompts.call("message_chunk_digest", text)
        msg_summary, msg_action_items = _parse_haiku_json(raw, text[:300]) if raw else (text[:300], "")

        # Fetch MRR tags for this message to merge into event
        mrr_tags: dict = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tags FROM mem_mrr_messages WHERE project_id=%s AND id=%s::uuid",
                        (_m_project_id, message_id),
                    )
                    tr = cur.fetchone()
                    if tr:
                        mrr_tags = tr[0] or {}
        except Exception:
            pass

        emb = await _embed(msg_summary)
        event_id = _upsert_event(
            project, "message", message_id, 0, "full", msg_summary, emb,
            summary=msg_summary, action_items=msg_action_items,
            tags={**mrr_tags, "platform": platform, "channel": channel or ""},
        )
        return event_id

    async def semantic_search(
        self,
        project: str,
        query: str,
        limit: int = 10,
        source_types: Optional[list[str]] = None,
    ) -> list[dict]:
        """Cosine similarity search over mem_ai_events.embedding."""
        if not db.is_available():
            return []

        vec = await _embed(query)
        if not vec:
            return []

        vec_str = f"[{','.join(str(x) for x in vec)}]"

        # Build WHERE clause
        _s_project_id = db.get_or_create_project_id(project)
        conditions = ["project_id=%s", "embedding IS NOT NULL"]
        params: list = [_s_project_id]

        if source_types:
            placeholders = ",".join(["%s"] * len(source_types))
            conditions.append(f"event_type IN ({placeholders})")
            params.extend(source_types)

        where_clause = " AND ".join(conditions)
        sql = _SQL_SEARCH_TPL.format(where=where_clause)

        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, [vec_str] + params + [vec_str, limit])
                    rows = cur.fetchall()
            results = []
            for r in rows:
                tags = r[5] or {}
                file_info = tags.get("file")
                results.append({
                    "event_type": r[0],
                    "source_id":   r[1],
                    "chunk":       r[2],
                    "chunk_type":  r[3],
                    "content":     r[4],
                    # backward-compat: reconstruct from tags
                    "language":    tags.get("language"),
                    "file_path":   file_info.get("name") if isinstance(file_info, dict) else file_info,
                    "doc_type":    tags.get("doc_type"),
                    "tags":        tags,
                    "session_id":  r[6],
                    "score":       float(r[7]),
                })
            return results
        except Exception as e:
            log.debug(f"MemoryEmbedding.semantic_search error: {e}")
            return []

    # ── Smart chunking (static helpers) ────────────────────────────────────

    @staticmethod
    def smart_chunk_code(content: str, filename: str) -> list[dict]:
        """Split code into summary + per-class/function chunks."""
        language = _detect_language(filename)
        chunks: list[dict] = []

        if language == "python":
            top_pattern = re.compile(r'^(?:class|def)\s+\w+', re.MULTILINE)
        elif language in ("javascript", "typescript"):
            top_pattern = re.compile(
                r'^(?:class\s+\w+|function\s+\w+|const\s+\w+\s*=|'
                r'export\s+(?:default\s+)?(?:class|function|async function|const)\s+\w+)',
                re.MULTILINE,
            )
        else:
            return [{
                "content": content[:8000], "chunk_type": "full", "chunk_index": 0,
                "language": language, "file_path": filename, "metadata": {},
            }]

        top_names: list[str] = []
        for m in top_pattern.finditer(content):
            nm = re.match(
                r'(?:class|def|function|const|export\s+\S+\s+(?:class|function|async function|const))\s+(\w+)',
                m.group(),
            )
            if nm:
                top_names.append(nm.group(1))

        first_lines = "\n".join(content.splitlines()[:15])
        summary = first_lines[:600]
        if top_names:
            summary += f"\n\n# Symbols: {', '.join(top_names[:25])}"
        chunks.append({
            "content": summary, "chunk_type": "summary", "chunk_index": 0,
            "language": language, "file_path": filename,
            "metadata": {"symbols": top_names[:25]},
        })

        block_starts = [(m.start(), m.group()) for m in top_pattern.finditer(content)]
        for i, (start, _) in enumerate(block_starts):
            end = block_starts[i + 1][0] if i + 1 < len(block_starts) else len(content)
            block = content[start:end].strip()
            if len(block) < 30:
                continue
            first_line = block.split('\n')[0]
            chunk_type = "class" if "class " in first_line else "function"
            nm = re.match(
                r'(?:class|def|function|const|export\s+\S+\s+(?:class|function|async function|const))\s+(\w+)',
                first_line,
            )
            symbol = nm.group(1) if nm else f"block_{i}"
            chunks.append({
                "content": block[:6000], "chunk_type": chunk_type, "chunk_index": i + 1,
                "language": language, "file_path": filename, "metadata": {"symbol": symbol},
            })
        return chunks

    @staticmethod
    def smart_chunk_markdown(content: str, doc_type: Optional[str] = None) -> list[dict]:
        """Split markdown by H2/H3 sections."""
        chunks: list[dict] = []
        sections = re.split(r'\n(?=## )', content)
        for section in sections:
            if not section.strip():
                continue
            heading = section.split('\n')[0].lstrip('#').strip() if section.startswith('#') else ""
            base_meta: dict = {}
            if heading:
                base_meta["heading"] = heading
            if doc_type:
                base_meta["doc_type"] = doc_type

            if len(section) > 3000:
                sub_sections = re.split(r'\n(?=### )', section)
                for sub in sub_sections:
                    if not sub.strip():
                        continue
                    sub_heading = sub.split('\n')[0].lstrip('#').strip() if sub.startswith('#') else heading
                    meta = {**base_meta, "heading": sub_heading} if sub_heading else base_meta
                    chunks.append({
                        "content": sub[:6000], "chunk_type": "section",
                        "chunk_index": len(chunks), "language": "markdown",
                        "file_path": None, "metadata": meta,
                    })
            else:
                chunk_type = "summary" if not chunks else "section"
                chunks.append({
                    "content": section[:6000], "chunk_type": chunk_type,
                    "chunk_index": len(chunks), "language": "markdown",
                    "file_path": None, "metadata": base_meta,
                })

        if not chunks:
            return [{
                "content": content[:6000], "chunk_type": "full", "chunk_index": 0,
                "language": "markdown", "file_path": None,
                "metadata": {"doc_type": doc_type} if doc_type else {},
            }]
        for idx, chunk in enumerate(chunks):
            chunk["chunk_index"] = idx
        return chunks

    # Generated/internal files that add noise — excluded from per-file diff chunks
    _GENERATED_FILE_PATTERNS = re.compile(
        r'^(CLAUDE\.md|\.cursorrules|MEMORY\.md|\.claude/|'
        r'workspace/.*/_system/|history\.jsonl|'
        r'.*\.pyc$|__pycache__/)',
        re.IGNORECASE,
    )

    @staticmethod
    def _extract_code_symbols(section_text: str, language: Optional[str]) -> list[str]:
        """Extract class/function/method names from a unified diff section."""
        symbols: list[str] = []
        if language == "python":
            pattern = re.compile(r'^[+-]?\s*(?:class|def)\s+(\w+)', re.MULTILINE)
        elif language in ("javascript", "typescript"):
            pattern = re.compile(
                r'^[+-]?\s*(?:class\s+(\w+)|function\s+(\w+)|'
                r'(?:export\s+)?(?:async\s+)?function\s+(\w+)|'
                r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()',
                re.MULTILINE,
            )
        else:
            return symbols
        seen: set[str] = set()
        for m in pattern.finditer(section_text):
            name = next((g for g in m.groups() if g), None)
            if name and name not in seen:
                symbols.append(name)
                seen.add(name)
        return symbols[:20]

    @staticmethod
    def smart_chunk_diff(diff_text: str, commit_hash: str, meta: Optional[dict] = None) -> list[dict]:
        """Parse a git unified diff into summary + per-file chunks.

        Generated/internal files (CLAUDE.md, .cursorrules, etc.) are excluded
        from per-file chunks but still counted in the summary stats.
        Code symbols (class/function names) are extracted and stored in chunk tags.
        """
        chunks: list[dict] = []
        meta = meta or {}
        file_sections = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)

        changed_files: list[str] = []
        for section in file_sections:
            m = re.match(r'diff --git a/(.*?) b/', section)
            if m:
                changed_files.append(m.group(1))

        summary_parts: list[str] = []
        if meta.get("commit_msg"):
            summary_parts.append(f"Commit: {meta['commit_msg']}")
        summary_parts.append(f"Hash: {commit_hash[:8]}")
        if meta.get("phase"):
            summary_parts.append(f"Phase: {meta['phase']}")
        if meta.get("feature"):
            summary_parts.append(f"Feature: {meta['feature']}")

        # Separate code files from generated/internal files
        code_files = [f for f in changed_files
                      if not MemoryEmbedding._GENERATED_FILE_PATTERNS.match(f)]
        gen_files  = [f for f in changed_files
                      if MemoryEmbedding._GENERATED_FILE_PATTERNS.match(f)]

        if code_files:
            files_list = "\n".join(f"  - {f}" for f in code_files[:20])
            summary_parts.append(f"Code files ({len(code_files)}):\n{files_list}")
        if gen_files:
            summary_parts.append(f"Generated/internal files: {', '.join(gen_files[:5])}")

        # Accumulate per-file stats (all files for stats, only code files for chunks)
        file_stats: list[dict] = []
        for section in file_sections:
            if not section.strip() or not section.startswith("diff --git"):
                continue
            file_match = re.match(r'diff --git a/(.*?) b/', section)
            filepath = file_match.group(1) if file_match else None
            if not filepath:
                continue
            lang = _detect_language(filepath)
            section_lines = section.splitlines()
            added   = sum(1 for ln in section_lines if ln.startswith('+') and not ln.startswith('+++'))
            removed = sum(1 for ln in section_lines if ln.startswith('-') and not ln.startswith('---'))
            symbols = MemoryEmbedding._extract_code_symbols(section, lang)
            is_generated = bool(MemoryEmbedding._GENERATED_FILE_PATTERNS.match(filepath))
            file_stats.append({
                "name": filepath, "language": lang,
                "added": added, "removed": removed,
                "symbols": symbols, "generated": is_generated,
            })

        # Summary chunk tags: code files only for "files" dict; all languages
        code_stats = [s for s in file_stats if not s["generated"]]
        files_tag = {s["name"]: s["added"] + s["removed"] for s in code_stats}
        languages_list = sorted({s["language"] for s in code_stats if s["language"]})
        all_symbols = list({sym for s in code_stats for sym in s.get("symbols", [])})
        total_added   = sum(s["added"]   for s in code_stats)
        total_removed = sum(s["removed"] for s in code_stats)

        summary_tags: dict = {**meta, "commit_hash": commit_hash, "changed_files": code_files}
        if files_tag:
            summary_tags["files"] = files_tag
        if languages_list:
            summary_tags["languages"] = languages_list
        if all_symbols:
            summary_tags["symbols"] = all_symbols[:30]
        if total_added or total_removed:
            summary_tags["rows_changed"] = {"added": total_added, "removed": total_removed}

        if all_symbols:
            summary_parts.append(f"Symbols changed: {', '.join(all_symbols[:15])}")

        chunks.append({
            "content": "\n".join(summary_parts), "chunk_type": "summary",
            "chunk_index": 0,
            "tags": summary_tags,
        })

        # Per-file chunks — only non-generated code files
        for stat in code_stats:
            filepath = stat["name"]
            for section in file_sections:
                m = re.match(r'diff --git a/(.*?) b/', section)
                if m and m.group(1) == filepath:
                    file_tag = {k: v for k, v in stat.items() if k != "generated"}
                    chunks.append({
                        "content": section[:6000], "chunk_type": "diff_file",
                        "chunk_index": len(chunks),
                        "tags": {**meta, "commit_hash": commit_hash, "file": file_tag},
                    })
                    break

        return chunks

    @staticmethod
    def smart_chunk_text(text: str, max_words: int = 400) -> list[dict]:
        """Split plain text (prompts, responses, raw items) on paragraph breaks.

        Targets ~max_words per chunk. Returns list of chunk dicts with
        chunk_type='full' (single chunk) or 'section' (multi-chunk).
        """
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
        chunks: list[str] = []
        current: list[str] = []
        word_count = 0
        for para in paragraphs:
            wc = len(para.split())
            if word_count + wc > max_words and current:
                chunks.append('\n\n'.join(current))
                current, word_count = [para], wc
            else:
                current.append(para)
                word_count += wc
        if current:
            chunks.append('\n\n'.join(current))
        if not chunks:
            return [{"content": text[:6000], "chunk_type": "full", "chunk_index": 0, "tags": {}}]
        chunk_type = "full" if len(chunks) == 1 else "section"
        return [
            {"content": c[:6000], "chunk_type": chunk_type, "chunk_index": i, "tags": {}}
            for i, c in enumerate(chunks)
        ]


# ── Backward-compat wrapper (delegates to the old mem_embeddings.py public API) ─

async def embed_and_store(
    project: str,
    source_type: str,
    source_id: str,
    content: str,
    chunk_index: int = 0,
    chunk_type: str = "full",
    doc_type: Optional[str] = None,
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    metadata: Optional[dict] = None,
    tags: Optional[dict] = None,
    **_extra,  # absorb any extra legacy kwargs silently
) -> None:
    """Embed content and store in mem_ai_events. Silently no-ops on error."""
    vec = await _embed(content)
    _upsert_event(
        project, source_type, source_id, chunk_index, chunk_type, content, vec,
        doc_type=doc_type,
        language=language,
        file_path=file_path,
        metadata=metadata,
        tags=tags,
    )


async def semantic_search(
    project: str,
    query: str,
    limit: int = 10,
    source_types: Optional[list[str]] = None,
    **_filters,
) -> list[dict]:
    """Backward-compatible semantic search wrapper."""
    emb = MemoryEmbedding()
    return await emb.semantic_search(project, query, limit, source_types=source_types)


async def embed_chunks(
    project: str,
    source_type: str,
    source_id: str,
    chunks: list[dict],
) -> int:
    """Embed a list of pre-computed chunk dicts. Returns number embedded."""
    count = 0
    for chunk in chunks:
        await embed_and_store(
            project=project,
            source_type=source_type,
            source_id=source_id,
            content=chunk.get("content", ""),
            chunk_index=chunk.get("chunk_index", 0),
            chunk_type=chunk.get("chunk_type", "full"),
            doc_type=chunk.get("doc_type"),
            language=chunk.get("language"),
            file_path=chunk.get("file_path"),
            metadata=chunk.get("metadata", {}),
        )
        count += 1
    return count


async def ingest_history(project: str, since: Optional[str] = None) -> int:
    """Embed history.jsonl entries. Returns count of newly embedded entries."""
    history_path = Path(settings.workspace_dir) / project / "_system" / "history.jsonl"
    if not history_path.exists():
        return 0
    embedded = 0
    try:
        for line in history_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = entry.get("ts", "")
            if since and ts and ts <= since:
                continue
            user_input = entry.get("user_input", "")
            output = entry.get("output", "")
            source_id = ts or f"hist_{embedded}"
            content = f"Q: {user_input}\nA: {output}"
            if content.strip() == "Q: \nA: ":
                continue
            meta: dict = {}
            for k in ("provider", "source"):
                if entry.get(k):
                    meta[k] = entry[k]
            await embed_and_store(
                project, "history", source_id, content,
                chunk_index=0, chunk_type="full", metadata=meta,
            )
            embedded += 1
    except Exception as e:
        log.warning(f"ingest_history failed: {e}")
    return embedded


async def ingest_roles(project: str) -> int:
    """Embed all role .md files in workspace/{project}/prompts/roles/. Returns count."""
    roles_dir = Path(settings.workspace_dir) / project / "prompts" / "roles"
    if not roles_dir.exists():
        return 0
    embedded = 0
    try:
        for md_file in sorted(roles_dir.rglob("*.md")):
            rel = str(md_file.relative_to(roles_dir))
            content = md_file.read_text()
            chunks = MemoryEmbedding.smart_chunk_markdown(content, doc_type="role")
            for chunk in chunks:
                await embed_and_store(
                    project, "role", rel, chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    chunk_type=chunk["chunk_type"],
                    doc_type="role",
                    language="markdown",
                    metadata=chunk.get("metadata", {}),
                )
            embedded += 1
    except Exception as e:
        log.warning(f"ingest_roles failed: {e}")
    return embedded


async def ingest_commit(project: str, commit_hash: str, code_dir: str) -> int:
    """Fetch git diff for a commit, chunk it, and embed. Returns chunks embedded."""
    if not code_dir:
        return 0
    try:
        result = subprocess.run(
            ["git", "show", "--format=%B%n---DIFF---", commit_hash],
            cwd=code_dir, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return 0
        output = result.stdout
        parts = output.split("\n---DIFF---\n", 1)
        commit_msg = parts[0].strip()
        diff_text = parts[1] if len(parts) > 1 else ""
        meta: dict = {"commit_msg": commit_msg}
        if db.is_available():
            try:
                _ic_project_id = db.get_or_create_project_id(project)
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT tags FROM mem_mrr_commits "
                            "WHERE project_id=%s AND commit_hash=%s",
                            (_ic_project_id, commit_hash),
                        )
                        row = cur.fetchone()
                        if row and row[0]:
                            meta["tags"] = row[0]
            except Exception:
                pass
        if not diff_text.strip():
            await embed_and_store(
                project, "commit", commit_hash, commit_msg,
                chunk_index=0, chunk_type="summary", metadata=meta,
            )
            return 1
        chunks = MemoryEmbedding.smart_chunk_diff(diff_text, commit_hash, meta)
        return await embed_chunks(project, "commit", commit_hash, chunks)
    except Exception as e:
        log.debug(f"ingest_commit failed ({commit_hash}): {e}")
        return 0


async def ingest_document(
    project: str,
    doc_path: str,
    content: str,
    doc_type: str = "doc",
    metadata: Optional[dict] = None,
) -> int:
    """Chunk and embed a document (markdown or code file). Returns chunks embedded."""
    extra_meta = metadata or {}
    language = _detect_language(doc_path)
    source_id = doc_path.replace("/", "_").replace(" ", "_").replace("\\", "_")
    if language == "markdown":
        chunks = MemoryEmbedding.smart_chunk_markdown(content, doc_type=doc_type)
    elif language in ("python", "javascript", "typescript", "go", "rust", "java"):
        chunks = MemoryEmbedding.smart_chunk_code(content, doc_path)
    else:
        chunks = [{
            "content": content[:8000], "chunk_type": "full", "chunk_index": 0,
            "language": language, "file_path": doc_path, "metadata": {},
        }]
    for chunk in chunks:
        chunk.setdefault("metadata", {}).update(extra_meta)
        if not chunk.get("file_path"):
            chunk["file_path"] = doc_path
        if not chunk.get("doc_type"):
            chunk["doc_type"] = doc_type
    return await embed_chunks(project, "doc", source_id, chunks)


async def embed_node_outputs(run_id: str, project: str) -> None:
    """Embed all completed node outputs from a graph run. Silent on error."""
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_NODE_OUTPUTS, (run_id,))
                rows = cur.fetchall()
        for node_id, node_name, output in rows:
            if output:
                source_id = f"{run_id}:{node_id}"
                content = f"[{node_name}]\n{output}"
                await embed_and_store(
                    project, "node_output", source_id, content,
                    chunk_index=0, chunk_type="full",
                )
    except Exception as e:
        log.debug(f"embed_node_outputs failed: {e}")


async def backfill_entity_tags(project: str) -> None:
    """Stub — entity tag backfill not implemented."""
    pass


# Module-level smart chunking (backward compat)
smart_chunk_code     = MemoryEmbedding.smart_chunk_code
smart_chunk_markdown = MemoryEmbedding.smart_chunk_markdown
smart_chunk_diff     = MemoryEmbedding.smart_chunk_diff
smart_chunk_text     = MemoryEmbedding.smart_chunk_text
get_embedding        = _embed  # trivial alias
