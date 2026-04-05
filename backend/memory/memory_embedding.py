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
           (client_id, project, event_type, source_id, session_id,
            llm_source, chunk, chunk_type, content, embedding, summary,
            doc_type, language, file_path, tags, importance)
       VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s,
               %s, %s, %s, %s::jsonb, %s)
       ON CONFLICT (client_id, project, event_type, source_id, chunk)
       DO UPDATE SET
           content    = EXCLUDED.content,
           embedding  = EXCLUDED.embedding,
           summary    = EXCLUDED.summary,
           llm_source = EXCLUDED.llm_source,
           tags       = EXCLUDED.tags
    RETURNING id
"""

_SQL_GET_COMMIT = """
    SELECT commit_hash, commit_msg, summary, tags, session_id
    FROM mem_mrr_commits
    WHERE client_id=1 AND project=%s AND commit_hash=%s
"""

_SQL_GET_ITEM = """
    SELECT id, item_type, title, raw_text, summary
    FROM mem_mrr_items
    WHERE client_id=1 AND project=%s AND id=%s::uuid
"""

_SQL_LOAD_PROMPT = """
    SELECT content FROM mng_system_roles
    WHERE client_id=1 AND name=%s AND is_active=TRUE
    LIMIT 1
"""

_SQL_SEARCH_TPL = """
    SELECT event_type, source_id, chunk, chunk_type, content,
           language, file_path, doc_type, tags, session_id,
           1 - (embedding <=> %s::vector) AS score
    FROM mem_ai_events
    WHERE {where}
    ORDER BY embedding <=> %s::vector
    LIMIT %s
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
    llm_source: Optional[str] = None,
    summary: Optional[str] = None,
    doc_type: Optional[str] = None,
    language: Optional[str] = None,
    file_path: Optional[str] = None,
    tags: dict | None = None,
    # backward-compat aliases
    metadata: dict | None = None,
    importance: int = 1,
    session_desc: Optional[str] = None,
    cnt_prompts: Optional[int] = None,
) -> Optional[str]:
    """Insert or update a row in mem_ai_events. Returns UUID string.

    tags: unified dict merging MRR classification tags + source-specific metadata,
          e.g. {"phase": "discovery", "commit_hash": "abc123", "platform": "slack"}.
    """
    if not db.is_available():
        return None
    # Accept legacy `metadata` kwarg — merge into tags
    merged = {**(metadata or {}), **(tags or {})}
    # Auto-add system classifiers so all events are consistently tagged
    enriched: dict = {"event": source_type, "chunk_type": chunk_type}
    enriched.update(merged)  # caller tags override system keys
    vec_str = f"[{','.join(str(x) for x in embedding)}]" if embedding else None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_EVENT,
                    (project, source_type, source_id, session_id,
                     llm_source, chunk, chunk_type, content, vec_str, summary,
                     doc_type, language, file_path,
                     json.dumps(enriched), importance),
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
            "Given N sequential prompt/response pairs, extract a 1-2 sentence digest "
            "capturing what was decided, built, or discovered. Return plain text only."
        )
        digest = await _haiku(sys_prompt, pairs, max_tokens=200)
        if not digest:
            return None

        embedding = await _embed(digest)
        last_id   = prompts[-1]["id"]

        # Fetch MRR tags from the most recent prompt in this session
        mrr_tags: dict = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tags FROM mem_mrr_prompts "
                        "WHERE client_id=1 AND project=%s AND session_id=%s "
                        "ORDER BY created_at DESC LIMIT 1",
                        (project, session_id),
                    )
                    tr = cur.fetchone()
                    if tr:
                        mrr_tags = tr[0] or {}
        except Exception:
            pass

        event_id = _upsert_event(
            project, "prompt_batch", last_id, 0, "full", digest, embedding,
            session_id=session_id, llm_source=settings.haiku_model,
            summary=digest, tags=mrr_tags, importance=1,
        )
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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_COMMIT, (project, commit_hash))
                    row = cur.fetchone()
            if not row:
                return None

            commit_hash_val, commit_msg, summary, mrr_tags, session_id = row
            # mrr_tags is already a dict from JSONB column
            mrr_tags = mrr_tags or {}
        except Exception as e:
            log.debug(f"process_commit DB error: {e}")
            return None

        sys_prompt = await _load_system_role("commit_digest") or (
            "Given a git commit message, produce a 1-2 sentence digest of what changed and why. "
            "Return plain text only."
        )
        content = f"Commit: {commit_hash_val[:8]}\n{commit_msg}"
        if summary:
            content += f"\nSummary: {summary}"

        digest = await _haiku(sys_prompt, content, max_tokens=150)
        if not digest:
            digest = commit_msg[:300]

        embedding = await _embed(digest)

        # Merge MRR classification tags + commit-specific metadata
        event_tags = {**mrr_tags, "commit_hash": commit_hash_val}
        event_id = _upsert_event(
            project, "commit", commit_hash_val, 0, "full", digest, embedding,
            session_id=session_id, llm_source=settings.haiku_model,
            summary=digest, tags=event_tags,
        )
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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_ITEM, (project, item_id))
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
                        "SELECT tags FROM mem_mrr_items WHERE client_id=1 AND project=%s AND id=%s::uuid",
                        (project, item_id),
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
                    doc_type=item_type,
                    tags={**item_mrr_tags, "title": sec.get("title", ""), "section_index": str(i)},
                )
                if i == 0:
                    first_id = event_id
            result_id = first_id
        else:
            sys_prompt = await _load_system_role("item_digest") or (
                "Summarise this document in 1-2 sentences. Return plain text only."
            )
            digest = await _haiku(sys_prompt, raw_text[:3000], max_tokens=150)
            if not digest:
                digest = (summary or raw_text)[:300]
            emb = await _embed(digest)
            result_id = _upsert_event(
                project, "item", item_id, 0, "full", digest, emb,
                doc_type=item_type, summary=digest, tags=item_mrr_tags,
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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, platform, channel, messages FROM mem_mrr_messages "
                        "WHERE client_id=1 AND project=%s AND id=%s::uuid",
                        (project, message_id),
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
            "Summarise this message thread chunk in 1-2 sentences. Return plain text only."
        )
        digest = await _haiku(sys_prompt, text, max_tokens=150)
        if not digest:
            digest = text[:300]

        # Fetch MRR tags for this message to merge into event
        mrr_tags: dict = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT tags FROM mem_mrr_messages WHERE client_id=1 AND project=%s AND id=%s::uuid",
                        (project, message_id),
                    )
                    tr = cur.fetchone()
                    if tr:
                        mrr_tags = tr[0] or {}
        except Exception:
            pass

        emb = await _embed(digest)
        event_id = _upsert_event(
            project, "message", message_id, 0, "full", digest, emb,
            summary=digest,
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
        conditions = ["client_id=1", "project=%s", "embedding IS NOT NULL"]
        params: list = [project]

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
            return [
                {
                    "event_type": r[0],
                    "source_id":   r[1],
                    "chunk":       r[2],
                    "chunk_type":  r[3],
                    "content":     r[4],
                    "language":    r[5],
                    "file_path":   r[6],
                    "doc_type":    r[7],
                    "tags":        r[8] or {},
                    "session_id":  r[9],
                    "score":       float(r[10]),
                }
                for r in rows
            ]
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

        chunks.append({
            "content": "\n".join(summary_parts), "chunk_type": "summary",
            "chunk_index": 0, "language": None, "file_path": None,
            "metadata": {**meta, "changed_files": changed_files},
        })

        for section in file_sections:
            if not section.strip() or not section.startswith("diff --git"):
                continue
            file_match = re.match(r'diff --git a/(.*?) b/', section)
            filepath = file_match.group(1) if file_match else None
            language = _detect_language(filepath) if filepath else None
            chunks.append({
                "content": section[:6000], "chunk_type": "diff_file",
                "chunk_index": len(chunks), "language": language,
                "file_path": filepath,
                "metadata": {**meta, "file": filepath},
            })

        return chunks


# ── Backward-compat wrapper (delegates to the old mem_embeddings.py public API) ─

async def embed_and_store(
    project: str,
    source_type: str,
    source_id: str,
    content: str,
    **chunk_meta,
) -> None:
    """Backward-compatible wrapper: embed content and store in mem_ai_events."""
    vec = await _embed(content)
    chunk = chunk_meta.get("chunk_index", 0)
    chunk_type = chunk_meta.get("chunk_type", "full")
    _upsert_event(
        project, source_type, source_id, chunk, chunk_type, content, vec,
        doc_type=chunk_meta.get("doc_type"),
        language=chunk_meta.get("language"),
        file_path=chunk_meta.get("file_path"),
        metadata=chunk_meta.get("metadata"),
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


# Module-level smart chunking (backward compat)
smart_chunk_code     = MemoryEmbedding.smart_chunk_code
smart_chunk_markdown = MemoryEmbedding.smart_chunk_markdown
smart_chunk_diff     = MemoryEmbedding.smart_chunk_diff
