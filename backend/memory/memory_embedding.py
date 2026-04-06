"""
memory_embedding.py — Layer 3 of the three-layer memory architecture.

Embeds content via OpenAI text-embedding-3-small (1536 dims) and stores in mem_ai_events.
Smart chunking splits large content into semantic units.

Public API::

    embedding = MemoryEmbedding()

    # Batch-digest N prompts in a session → mem_ai_events
    event_id = await embedding.process_prompt_batch(project, session_id, n)

    # Embed a commit diff → mem_ai_events (multi-chunk for large diffs)
    event_id = await embedding.process_commit(project, commit_id)

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

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from core.config import settings
from core.database import db
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

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_UPSERT_EVENT = """
    INSERT INTO mem_ai_events
           (project_id, event_type, source_id, session_id,
            chunk, chunk_type, content, embedding, summary, action_items, tags, importance)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s::jsonb, %s)
       ON CONFLICT (project_id, event_type, source_id, chunk)
       DO UPDATE SET
           content      = EXCLUDED.content,
           embedding    = EXCLUDED.embedding,
           summary      = EXCLUDED.summary,
           action_items = EXCLUDED.action_items,
           tags         = EXCLUDED.tags
    RETURNING id
"""

_SQL_GET_COMMIT = """
    SELECT commit_hash, commit_msg, summary, tags, session_id
    FROM mem_mrr_commits
    WHERE project_id=%s AND commit_hash=%s
"""

_SQL_UPDATE_COMMIT_TAGS = """
    UPDATE mem_mrr_commits
    SET tags = tags || %s::jsonb
    WHERE commit_hash = %s
"""

_SQL_UPDATE_COMMIT_SUMMARY = """
    UPDATE mem_mrr_commits
    SET summary = %s
    WHERE commit_hash = %s AND (summary IS NULL OR summary = '')
"""

_SQL_GET_ITEM = """
    SELECT id, item_type, title, raw_text, summary
    FROM mem_mrr_items
    WHERE project_id=%s AND id=%s::uuid
"""

_SQL_LOAD_PROMPT = """
    SELECT content FROM mng_system_roles
    WHERE client_id=1 AND name=%s AND is_active=TRUE
    LIMIT 1
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


async def _embed(text: str) -> Optional[list[float]]:
    """Call OpenAI embeddings API. Returns None on failure."""
    key = _openai_key()
    if not key:
        return None
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=key)
        resp = await client.embeddings.create(model=_EMBEDDING_MODEL, input=text[:8000])
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
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_haiku error: {e}")
        return ""


async def _load_system_role(name: str) -> Optional[str]:
    """Load a mng_system_roles prompt by name."""
    if not db.is_available():
        return None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_LOAD_PROMPT, (name,))
                row = cur.fetchone()
        return row[0] if row else None
    except Exception:
        return None


def _parse_haiku_json(raw: str, fallback: str) -> tuple[str, str]:
    """Return (summary, action_items). Handles plain-text fallback gracefully."""
    try:
        parsed = json.loads(raw)
        return parsed.get("summary", fallback), parsed.get("action_items", "")
    except (json.JSONDecodeError, AttributeError):
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
    # backward-compat: callers may still pass these; merged into tags
    metadata: dict | None = None,
    doc_type: Optional[str] = None,
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    importance: int = 1,
    # ignored legacy params
    llm_source: Optional[str] = None,  # deprecated — put in tags["llm"] instead
    session_desc: Optional[str] = None,
    cnt_prompts: Optional[int] = None,
) -> Optional[str]:
    """Insert or update a row in mem_ai_events. Returns UUID string.

    tags: unified dict — use tags["source"] for originating platform,
          tags["llm"] for the model that produced digest content.
    doc_type / language / file_path are accepted for backward-compat and merged into tags.
    llm_source is accepted for backward-compat and merged into tags["llm"] if not already set.
    """
    if not db.is_available():
        return None
    # Accept legacy `metadata` kwarg — merge into tags
    merged = {**(metadata or {}), **(tags or {})}
    # Merge legacy individual column params into tags
    if doc_type:
        merged.setdefault("doc_type", doc_type)
    if language:
        merged.setdefault("language", language)
    if file_path:
        merged.setdefault("file", file_path)
    # Backward-compat: if caller passed llm_source kwarg, fold into tags["llm"]
    if llm_source:
        merged.setdefault("llm", llm_source)
    # Auto-add system classifiers so all events are consistently tagged
    enriched: dict = {"event": source_type, "chunk_type": chunk_type}
    enriched.update(merged)  # caller tags override system keys
    vec_str = f"[{','.join(str(x) for x in embedding)}]" if embedding else None
    project_id = db.get_or_create_project_id(project)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_EVENT,
                    (project_id, source_type, source_id, session_id,
                     chunk, chunk_type, content, vec_str, summary,
                     action_items, json.dumps(enriched), importance),
                )
                row = cur.fetchone()
        return str(row[0]) if row else None
    except Exception as e:
        log.debug(f"_upsert_event error: {e}")
        return None


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
        """Digest and embed the last N prompts of a session.

        1. Load last N prompts from mem_mrr_prompts
        2. Load prompt_batch_digest system role → Haiku digest
        3. Embed digest → VECTOR(1536)
        4. INSERT mem_ai_events (event_type='prompt_batch', cnt_prompts=n)
        Returns the mem_ai_events UUID.
        """
        prompts = self._mirroring.get_last_n_prompts(project, session_id, n)
        if not prompts:
            return None

        pairs = "\n\n".join(
            f"Q: {(p['prompt'] or '')[:500]}\nA: {(p['response'] or '')[:800]}"
            for p in prompts
        )

        sys_prompt = await _load_system_role("prompt_batch_digest") or (
            "Given N sequential prompt/response pairs, extract a digest. "
            'Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet or empty string"}'
        )
        raw = await _haiku(sys_prompt, pairs, max_tokens=250)
        if not raw:
            return None
        summary_text, action_items = _parse_haiku_json(raw, pairs[:200])

        embedding = await _embed(summary_text)
        last_id   = prompts[-1]["id"]

        # Fetch MRR tags from the most recent prompt in this session
        mrr_tags: dict = {}
        _pb_project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tags FROM mem_mrr_prompts "
                        "WHERE project_id=%s AND session_id=%s "
                        "ORDER BY created_at DESC LIMIT 1",
                        (_pb_project_id, session_id),
                    )
                    tr = cur.fetchone()
                    if tr:
                        mrr_tags = tr[0] or {}
        except Exception:
            pass

        event_tags = {**mrr_tags, "llm": settings.haiku_model}
        event_id = _upsert_event(
            project, "prompt_batch", last_id, 0, "full", summary_text, embedding,
            session_id=session_id,
            summary=summary_text, action_items=action_items, tags=event_tags, importance=1,
        )

        # Chunk long responses (raw embed, no LLM)
        chunk_idx = 1
        for p in prompts:
            resp = p.get("response", "")
            if len(resp.split()) > 400:
                resp_chunks = MemoryEmbedding.smart_chunk_text(resp)
                if len(resp_chunks) > 1:
                    for rc in resp_chunks:
                        rc_emb = await _embed(rc["content"])
                        _upsert_event(
                            project, "prompt_batch", last_id, chunk_idx,
                            rc.get("chunk_type", "section"), rc["content"], rc_emb,
                            session_id=session_id, tags=mrr_tags, importance=1,
                        )
                        chunk_idx += 1

        return event_id

    async def process_commit(
        self,
        project: str,
        commit_hash: str,
    ) -> Optional[str]:
        """Digest and embed a commit from mem_mrr_commits.

        Uses commit_hash (the natural PK) as the identifier.
        Returns the mem_ai_events UUID.
        """
        if not db.is_available():
            return None
        _c_project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_COMMIT, (_c_project_id, commit_hash))
                    row = cur.fetchone()
            if not row:
                return None

            commit_hash_val, commit_msg, existing_summary, mrr_tags, session_id = row
            mrr_tags = mrr_tags or {}
        except Exception as e:
            log.debug(f"process_commit DB error: {e}")
            return None

        sys_prompt = await _load_system_role("commit_digest") or (
            "Given a git commit message, produce a digest. "
            'Return JSON only: {"summary": "1-2 sentence digest of what changed and why", "action_items": ""}'
        )
        user_content = f"Commit: {commit_hash_val[:8]}\n{commit_msg}"
        if existing_summary:
            user_content += f"\nSummary: {existing_summary}"

        raw = await _haiku(sys_prompt, user_content, max_tokens=200)
        summary_text, action_items = _parse_haiku_json(raw, commit_msg[:300]) if raw else (commit_msg[:300], "")

        embedding = await _embed(summary_text)

        # Merge MRR classification tags + commit-specific metadata
        base_tags: dict = {**mrr_tags, "commit_hash": commit_hash_val}

        # chunk=0: Haiku digest — carries tags["llm"]
        digest_tags = {**base_tags, "llm": settings.haiku_model}
        event_id = _upsert_event(
            project, "commit", commit_hash_val, 0, "full", summary_text, embedding,
            session_id=session_id,
            summary=summary_text, action_items=action_items, tags=digest_tags,
        )

        # Back-propagate summary + llm tag to mem_mrr_commits (visible in history UI)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_UPDATE_COMMIT_SUMMARY, (summary_text, commit_hash_val))
                    cur.execute(_SQL_UPDATE_COMMIT_TAGS,
                                (json.dumps({"llm": settings.haiku_model}), commit_hash_val))
        except Exception as e:
            log.debug(f"process_commit tag update error: {e}")

        # Per-file diff chunks (raw embed, no llm tag) + back-propagate file stats to mrr
        try:
            code_dir = settings.code_dir
            if code_dir:
                result = subprocess.run(
                    ["git", "show", "--format=%B%n---DIFF---", commit_hash_val],
                    cwd=code_dir, capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    parts = result.stdout.split("\n---DIFF---\n", 1)
                    diff_text = parts[1] if len(parts) > 1 else ""
                    if diff_text.strip():
                        diff_chunks = MemoryEmbedding.smart_chunk_diff(
                            diff_text, commit_hash_val, {"commit_msg": commit_msg}
                        )
                        # Back-propagate file/language stats from summary chunk to mrr
                        summary_chunk_tags = diff_chunks[0].get("tags", {}) if diff_chunks else {}
                        mrr_stat_update: dict = {}
                        if summary_chunk_tags.get("files"):
                            mrr_stat_update["files"] = summary_chunk_tags["files"]
                        if summary_chunk_tags.get("languages"):
                            mrr_stat_update["languages"] = summary_chunk_tags["languages"]
                        if mrr_stat_update:
                            with db.conn() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(_SQL_UPDATE_COMMIT_TAGS,
                                                (json.dumps(mrr_stat_update), commit_hash_val))
                        # Skip chunk[0] (summary) — Haiku digest is already chunk=0
                        for i, dc in enumerate(diff_chunks[1:], start=1):
                            dc_content = dc.get("content", "")
                            dc_tags = {**base_tags, **dc.get("tags", {})}
                            dc_emb = await _embed(dc_content)
                            _upsert_event(
                                project, "commit", commit_hash_val, i, "diff_file",
                                dc_content, dc_emb,
                                session_id=session_id, tags=dc_tags,
                            )
        except Exception as e:
            log.debug(f"process_commit diff chunks error: {e}")

        return event_id

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
            sys_prompt = await _load_system_role("meeting_sections") or (
                "Split this text into named sections (key topics). "
                'Return JSON: [{"title": str, "content": str}]'
            )
            sections_raw = await _haiku(sys_prompt, raw_text[:6000], max_tokens=1000)
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
            sys_prompt = await _load_system_role("item_digest") or (
                "Summarise this document. "
                'Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet or empty string"}'
            )
            raw = await _haiku(sys_prompt, raw_text[:3000], max_tokens=200)
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
        rel_prompt = await _load_system_role("relation_extraction") or (
            "Given a text snippet, identify explicit relationships between features/bugs/tasks. "
            'Return ONLY JSON: {"relations": [{"from": "slug", "relation": "part_of|depends_on|blocks|relates_to|replaces|extracted_from", "to": "slug", "note": "..."}]} '
            "If none found, return {\"relations\": []}"
        )
        rel_raw = await _haiku(rel_prompt, raw_text[:3000], max_tokens=400)
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

        sys_prompt = await _load_system_role("message_chunk_digest") or (
            "Summarise this message thread chunk. "
            'Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet or empty string"}'
        )
        raw = await _haiku(sys_prompt, text, max_tokens=200)
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

    @staticmethod
    def smart_chunk_diff(diff_text: str, commit_hash: str, meta: Optional[dict] = None) -> list[dict]:
        """Parse a git unified diff into summary + per-file chunks."""
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
        if changed_files:
            files_list = "\n".join(f"  - {f}" for f in changed_files[:20])
            summary_parts.append(f"Files changed ({len(changed_files)}):\n{files_list}")

        # Accumulate per-file stats for summary tags
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
            file_stats.append({"name": filepath, "language": lang, "added": added, "removed": removed})

        # Summary chunk tags: files dict (name→rows_changed) + languages list
        files_tag = {s["name"]: s["added"] + s["removed"] for s in file_stats}
        languages_list = sorted({s["language"] for s in file_stats if s["language"]})
        summary_tags: dict = {**meta, "commit_hash": commit_hash, "changed_files": changed_files}
        if files_tag:
            summary_tags["files"] = files_tag
        if languages_list:
            summary_tags["languages"] = languages_list

        chunks.append({
            "content": "\n".join(summary_parts), "chunk_type": "summary",
            "chunk_index": 0,
            "tags": summary_tags,
        })

        for stat in file_stats:
            filepath = stat["name"]
            # Find the matching section text
            for section in file_sections:
                m = re.match(r'diff --git a/(.*?) b/', section)
                if m and m.group(1) == filepath:
                    chunks.append({
                        "content": section[:6000], "chunk_type": "diff_file",
                        "chunk_index": len(chunks),
                        "tags": {**meta, "commit_hash": commit_hash, "file": stat},
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
