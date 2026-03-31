"""
embeddings.py — Layer 4 semantic upgrade for the 5-layer memory system.

Embeds content via OpenAI text-embedding-3-small (1536 dims) and stores in pgvector.
Smart chunking splits large content into semantic units (class/function/section/file-diff)
so queries can retrieve precise, relevant context rather than large monolithic blobs.

Degrades silently if PostgreSQL or OpenAI key unavailable — callers never see errors.
All public async functions are fire-and-forget safe.

Public API:
    embed_and_store(project, source_type, source_id, content, **chunk_meta) -> None
    embed_chunks(project, source_type, source_id, chunks) -> int
    semantic_search(project, query, limit, source_types, **filters) -> list[dict]
    ingest_history(project) -> int
    ingest_roles(project) -> int
    ingest_commit(project, commit_hash, code_dir) -> int
    ingest_document(project, doc_path, content, doc_type) -> int
    embed_node_outputs(run_id, project) -> None
    smart_chunk_code(content, filename) -> list[dict]
    smart_chunk_markdown(content, doc_type=None) -> list[dict]
    smart_chunk_diff(diff_text, commit_hash, meta) -> list[dict]
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

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_UPSERT_EMBEDDING = """INSERT INTO pr_embeddings
                           (client_id, project, source_type, source_id, chunk_index, content,
                            embedding, chunk_type, doc_type, language, file_path, metadata)
                       VALUES (1, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s, %s, %s::jsonb)
                       ON CONFLICT (client_id, project, source_type, source_id, chunk_index)
                       DO UPDATE SET
                           content=EXCLUDED.content,
                           embedding=EXCLUDED.embedding,
                           chunk_type=EXCLUDED.chunk_type,
                           doc_type=EXCLUDED.doc_type,
                           language=EXCLUDED.language,
                           file_path=EXCLUDED.file_path,
                           metadata=EXCLUDED.metadata,
                           created_at=NOW()"""

# Base search template — client_id=1 and project=%s are listed first to match
# the (client_id, project, source_type) index. Dynamic WHERE filters are appended
# at runtime; %s placeholders for query_vec and limit are appended by the caller.
_SQL_SEARCH_EMBEDDINGS_TPL = """SELECT source_type, source_id, chunk_index, chunk_type,
                               content, language, file_path, doc_type, metadata,
                               1 - (embedding <=> %s::vector) AS score
                        FROM pr_embeddings
                        WHERE {where}
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s"""

_SQL_GET_COMMIT_META = (
    "SELECT phase, feature, bug_ref "
    "FROM pr_commits WHERE client_id=1 AND project=%s AND commit_hash=%s"
)

_SQL_GET_NODE_OUTPUTS = (
    "SELECT node_id, node_name, output FROM pr_graph_node_results WHERE run_id=%s AND status='done'"
)

# Propagate entity value tags from pr_event_tags into pr_embeddings.metadata.
# The bridge is ev.source_id == e.source_id (timestamp for history, commit_hash for commit).
# Uses || merge so existing metadata keys are preserved.
_SQL_BACKFILL_ENTITY_TAGS = """
    UPDATE pr_embeddings e
    SET metadata = e.metadata || jsonb_build_object('entity_tags',
        (SELECT jsonb_agg(jsonb_build_object('id', t.id::text, 'name', t.name, 'category', tc.name))
         FROM pr_prompts pr
         JOIN pr_source_tags st ON st.prompt_id = pr.id
         JOIN pr_tags t  ON t.id  = st.tag_id AND t.client_id=1
         JOIN mng_tags_categories tc ON tc.id = t.category_id AND tc.client_id=1
         WHERE pr.client_id=1 AND pr.project=%s AND pr.source_id = e.source_id)
    )
    WHERE e.client_id=1 AND e.project=%s
      AND EXISTS (
          SELECT 1 FROM pr_prompts pr
          JOIN pr_source_tags st ON st.prompt_id = pr.id
          WHERE pr.client_id=1 AND pr.project=%s AND pr.source_id = e.source_id
      )
"""


def _openai_key() -> str | None:
    try:
        from data.dl_api_keys import get_key
        return get_key("openai") or None
    except Exception:
        return None


def _detect_language(filename: str) -> str | None:
    """Return language label from file extension, or None."""
    return _EXT_LANG.get(Path(filename).suffix.lower())


# ── Smart chunking ───────────────────────────────────────────────────────────


def smart_chunk_code(content: str, filename: str) -> list[dict]:
    """Split code into summary + per-class/function chunks.

    Returns list of chunk dicts:
        {content, chunk_type, chunk_index, language, file_path, metadata}
    chunk_type: "summary" | "class" | "function" | "full"
    """
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
        # No smart splitting for other languages — one full chunk
        return [{
            "content": content[:8000],
            "chunk_type": "full",
            "chunk_index": 0,
            "language": language,
            "file_path": filename,
            "metadata": {},
        }]

    # Collect top-level symbol names for the summary chunk
    top_names: list[str] = []
    for m in top_pattern.finditer(content):
        nm = re.match(r'(?:class|def|function|const|export\s+\S+\s+(?:class|function|async function|const))\s+(\w+)', m.group())
        if nm:
            top_names.append(nm.group(1))

    # Summary chunk: first 15 lines + symbol list
    first_lines = "\n".join(content.splitlines()[:15])
    summary = first_lines[:600]
    if top_names:
        summary += f"\n\n# Symbols: {', '.join(top_names[:25])}"
    chunks.append({
        "content": summary,
        "chunk_type": "summary",
        "chunk_index": 0,
        "language": language,
        "file_path": filename,
        "metadata": {"symbols": top_names[:25]},
    })

    # Per-symbol chunks
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
            "content": block[:6000],
            "chunk_type": chunk_type,
            "chunk_index": i + 1,
            "language": language,
            "file_path": filename,
            "metadata": {"symbol": symbol},
        })

    return chunks


def smart_chunk_markdown(content: str, doc_type: str | None = None) -> list[dict]:
    """Split markdown by H2/H3 sections into individual chunks.

    Returns list of chunk dicts with chunk_type="summary" (intro) or "section".
    Large H2 sections are further split at H3 boundaries.
    """
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
            # Sub-split at H3
            sub_sections = re.split(r'\n(?=### )', section)
            for sub in sub_sections:
                if not sub.strip():
                    continue
                sub_heading = sub.split('\n')[0].lstrip('#').strip() if sub.startswith('#') else heading
                meta = {**base_meta, "heading": sub_heading} if sub_heading else base_meta
                chunks.append({
                    "content": sub[:6000],
                    "chunk_type": "section",
                    "chunk_index": len(chunks),
                    "language": "markdown",
                    "file_path": None,
                    "metadata": meta,
                })
        else:
            chunk_type = "summary" if not chunks else "section"
            chunks.append({
                "content": section[:6000],
                "chunk_type": chunk_type,
                "chunk_index": len(chunks),
                "language": "markdown",
                "file_path": None,
                "metadata": base_meta,
            })

    if not chunks:
        return [{
            "content": content[:6000],
            "chunk_type": "full",
            "chunk_index": 0,
            "language": "markdown",
            "file_path": None,
            "metadata": {"doc_type": doc_type} if doc_type else {},
        }]

    # Ensure sequential chunk_index
    for idx, chunk in enumerate(chunks):
        chunk["chunk_index"] = idx
    return chunks


def smart_chunk_diff(diff_text: str, commit_hash: str, meta: dict | None = None) -> list[dict]:
    """Parse a git unified diff into summary + per-file chunks.

    meta: optional extra metadata — commit_msg, phase, feature, bug_ref.
    Returns list of chunk dicts with file_path and language for each file section.
    """
    chunks: list[dict] = []
    meta = meta or {}

    # Find all file sections
    file_sections = re.split(r'(?=^diff --git )', diff_text, flags=re.MULTILINE)

    # Summary chunk: commit message + changed-files list
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
        "content": "\n".join(summary_parts),
        "chunk_type": "summary",
        "chunk_index": 0,
        "language": None,
        "file_path": None,
        "metadata": {**meta, "commit_hash": commit_hash, "files_changed": len(changed_files)},
    })

    # Per-file diff chunks
    for section in file_sections:
        m = re.match(r'diff --git a/.*? b/(.*?)\n', section)
        if not m:
            continue
        file_path = m.group(1)
        if "Binary files" in section[:300]:
            continue
        language = _detect_language(file_path)
        chunks.append({
            "content": section[:6000],
            "chunk_type": "file_diff",
            "chunk_index": len(chunks),
            "language": language,
            "file_path": file_path,
            "metadata": {**meta, "commit_hash": commit_hash},
        })

    return chunks


# ── Core embed/store ─────────────────────────────────────────────────────────


async def embed_and_store(
    project: str,
    source_type: str,
    source_id: str,
    content: str,
    chunk_index: int = 0,
    chunk_type: str = "full",
    doc_type: str | None = None,
    language: str | None = None,
    file_path: str | None = None,
    metadata: dict | None = None,
) -> None:
    """Embed content and upsert into pgvector. Silent on any error."""
    if not db.is_available():
        return
    key = _openai_key()
    if not key:
        return
    if not content or not content.strip():
        return

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=key)
        response = await client.embeddings.create(
            model=_EMBEDDING_MODEL,
            input=content[:8000],
        )
        vector = response.data[0].embedding
        meta_json = json.dumps(metadata or {})

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_EMBEDDING,
                    (
                        project, source_type, source_id, chunk_index,
                        content[:4000], str(vector), chunk_type,
                        doc_type, language, file_path, meta_json,
                    ),
                )
    except Exception as e:
        log.debug(f"embed_and_store failed ({source_type}/{source_id}:{chunk_index}): {e}")


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


# ── Semantic search ──────────────────────────────────────────────────────────


async def semantic_search(
    project: str,
    query: str,
    limit: int = 10,
    source_types: list[str] | None = None,
    language: str | None = None,
    doc_type: str | None = None,
    file_path: str | None = None,
    chunk_types: list[str] | None = None,
    phase: str | None = None,
    feature: str | None = None,
    entity_name: str | None = None,
    entity_category: str | None = None,
) -> list[dict]:
    """Search embeddings by cosine similarity. Returns empty list on any error.

    Optional metadata filters: language, doc_type, file_path, chunk_types, phase, feature.
    entity_name: restrict to embeddings tagged with this entity value name (e.g. 'auth').
    entity_category: restrict to embeddings tagged with this category (e.g. 'bug', 'feature').
    Entity filters use JSONB containment on metadata->entity_tags populated by backfill_entity_tags().
    """
    if not db.is_available():
        return []
    key = _openai_key()
    if not key:
        return []

    try:
        import openai
        client = openai.AsyncOpenAI(api_key=key)
        response = await client.embeddings.create(model=_EMBEDDING_MODEL, input=query[:2000])
        query_vec = response.data[0].embedding

        # client_id=1 and project=%s are first to leverage the composite index
        filters: list[str] = ["client_id=1", "project=%s", "embedding IS NOT NULL"]
        params: list = [project, str(query_vec)]

        if source_types:
            filters.append("source_type = ANY(%s)")
            params.append(source_types)
        if language:
            filters.append("language=%s")
            params.append(language)
        if doc_type:
            filters.append("doc_type=%s")
            params.append(doc_type)
        if file_path:
            filters.append("file_path ILIKE %s")
            params.append(f"%{file_path}%")
        if chunk_types:
            filters.append("chunk_type = ANY(%s)")
            params.append(chunk_types)
        if phase:
            filters.append("metadata->>'phase' = %s")
            params.append(phase)
        if feature:
            filters.append("metadata->>'feature' = %s")
            params.append(feature)
        if entity_name:
            # JSONB containment: metadata @> '{"entity_tags":[{"name":"auth"}]}'
            filters.append("metadata @> %s::jsonb")
            params.append(json.dumps({"entity_tags": [{"name": entity_name}]}))
        if entity_category:
            filters.append("metadata @> %s::jsonb")
            params.append(json.dumps({"entity_tags": [{"category": entity_category}]}))

        where = " AND ".join(filters)
        params += [str(query_vec), limit]

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_SEARCH_EMBEDDINGS_TPL.format(where=where),
                    params,
                )
                rows = cur.fetchall()

        return [
            {
                "source_type": r[0], "source_id": r[1],
                "chunk_index": r[2], "chunk_type": r[3],
                "content": r[4], "language": r[5],
                "file_path": r[6], "doc_type": r[7],
                "metadata": r[8] or {},
                "score": float(r[9]),
            }
            for r in rows
        ]
    except Exception as e:
        log.debug(f"semantic_search failed: {e}")
        return []


# ── Bulk ingest ──────────────────────────────────────────────────────────────


async def ingest_history(project: str, since: str | None = None) -> int:
    """Embed history.jsonl entries. If since (ISO ts) is given, only embed newer entries.

    Returns count of newly embedded entries.
    """
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
            # Skip entries at or before the since threshold
            if since and ts and ts <= since:
                continue
            user_input = entry.get("user_input", "")
            output = entry.get("output", "")
            source_id = ts or f"hist_{embedded}"
            content = f"Q: {user_input}\nA: {output}"
            if content.strip() == "Q: \nA: ":
                continue
            meta: dict = {}
            for k in ("provider", "source", "phase", "feature"):
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
            chunks = smart_chunk_markdown(content, doc_type="role")
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
        # Get commit message + diff in one call
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

        # Look up commit metadata from DB (phase/feature/bug_ref)
        meta: dict = {"commit_msg": commit_msg}
        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(_SQL_GET_COMMIT_META, (project, commit_hash))
                        row = cur.fetchone()
                        if row:
                            if row[0]: meta["phase"] = row[0]
                            if row[1]: meta["feature"] = row[1]
                            if row[2]: meta["bug_ref"] = row[2]
            except Exception:
                pass

        if not diff_text.strip():
            await embed_and_store(
                project, "commit", commit_hash, commit_msg,
                chunk_index=0, chunk_type="summary", metadata=meta,
            )
            return 1

        chunks = smart_chunk_diff(diff_text, commit_hash, meta)
        return await embed_chunks(project, "commit", commit_hash, chunks)

    except Exception as e:
        log.debug(f"ingest_commit failed ({commit_hash}): {e}")
        return 0


async def ingest_document(
    project: str,
    doc_path: str,
    content: str,
    doc_type: str = "doc",
    metadata: dict | None = None,
) -> int:
    """Chunk and embed a document (markdown or code file). Returns chunks embedded."""
    extra_meta = metadata or {}
    language = _detect_language(doc_path)
    source_id = doc_path.replace("/", "_").replace(" ", "_").replace("\\", "_")

    if language == "markdown":
        chunks = smart_chunk_markdown(content, doc_type=doc_type)
    elif language in ("python", "javascript", "typescript", "go", "rust", "java"):
        chunks = smart_chunk_code(content, doc_path)
    else:
        chunks = [{
            "content": content[:8000],
            "chunk_type": "full",
            "chunk_index": 0,
            "language": language,
            "file_path": doc_path,
            "metadata": {},
        }]

    for chunk in chunks:
        chunk.setdefault("metadata", {}).update(extra_meta)
        if not chunk.get("file_path"):
            chunk["file_path"] = doc_path
        if not chunk.get("doc_type"):
            chunk["doc_type"] = doc_type

    return await embed_chunks(project, "doc", source_id, chunks)


async def backfill_entity_tags(project: str) -> int:
    """Propagate entity value tags from pr_event_tags into pr_embeddings.metadata.

    Runs after any tagging operation so embeddings become searchable by entity.
    Finds all embeddings whose source_id matches a tagged pr_events.source_id and
    merges an 'entity_tags' list into the metadata JSONB:
        {"entity_tags": [{"id": 5, "name": "auth", "category": "feature"}, ...]}

    The || merge operator preserves existing metadata keys (phase, feature, etc.).
    Safe to call repeatedly — idempotent. Silent on error.
    Returns count of updated embedding rows.
    """
    if not db.is_available():
        return 0
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_BACKFILL_ENTITY_TAGS, (project, project, project))
                return cur.rowcount
    except Exception as e:
        log.debug(f"backfill_entity_tags failed ({project}): {e}")
        return 0


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
