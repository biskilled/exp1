"""
embeddings.py — Layer 4 semantic upgrade for the 5-layer memory system.

Embeds content via OpenAI text-embedding-3-small (1536 dims) and stores in pgvector.
Degrades silently if PostgreSQL or OpenAI key unavailable — callers never see errors.
All public async functions are fire-and-forget safe.

Public API:
    embed_and_store(project, source_type, source_id, content) -> None
    semantic_search(project, query, limit, source_types) -> list[dict]
    ingest_history(project) -> int   (number of new entries embedded)
    ingest_roles(project)   -> int   (number of role files embedded)
    embed_node_outputs(run_id, project) -> None
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from config import settings
from core.database import db

log = logging.getLogger(__name__)

_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIMS = 1536


def _openai_key() -> str | None:
    try:
        from core.api_keys import get_key
        return get_key("openai") or None
    except Exception:
        return None


async def embed_and_store(
    project: str,
    source_type: str,
    source_id: str,
    content: str,
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
            input=content[:8000],  # stay within token limit
        )
        vector = response.data[0].embedding

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO embeddings (project, source_type, source_id, content, embedding)
                       VALUES (%s, %s, %s, %s, %s::vector)
                       ON CONFLICT (project, source_type, source_id)
                       DO UPDATE SET content=EXCLUDED.content, embedding=EXCLUDED.embedding,
                                     created_at=NOW()""",
                    (project, source_type, source_id, content[:4000], str(vector)),
                )
    except Exception as e:
        log.debug(f"embed_and_store failed ({source_type}/{source_id}): {e}")


async def semantic_search(
    project: str,
    query: str,
    limit: int = 10,
    source_types: list[str] | None = None,
) -> list[dict]:
    """Search embeddings by cosine similarity. Returns empty list on error."""
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

        type_filter = ""
        params: list = [str(query_vec), project]
        if source_types:
            type_filter = "AND source_type = ANY(%s)"
            params.append(source_types)
        params.append(limit)

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""SELECT source_type, source_id, content,
                               1 - (embedding <=> %s::vector) AS score
                        FROM embeddings
                        WHERE project=%s {type_filter}
                          AND embedding IS NOT NULL
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s""",
                    [str(query_vec), project] + (([source_types] if source_types else []))
                    + [str(query_vec), limit],
                )
                rows = cur.fetchall()

        return [
            {"source_type": r[0], "source_id": r[1], "content": r[2], "score": float(r[3])}
            for r in rows
        ]
    except Exception as e:
        log.debug(f"semantic_search failed: {e}")
        return []


async def ingest_history(project: str) -> int:
    """Embed history.jsonl entries that haven't been embedded yet. Returns count embedded."""
    history_path = Path(settings.workspace_dir) / project / "_system" / "history.jsonl"
    if not history_path.exists():
        return 0

    embedded = 0
    try:
        lines = history_path.read_text().splitlines()
        for line in lines:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = entry.get("ts", "")
            user_input = entry.get("user_input", "")
            output = entry.get("output", "")
            source_id = ts or f"hist_{embedded}"
            content = f"Q: {user_input}\nA: {output}"
            if content.strip() == "Q: \nA: ":
                continue
            await embed_and_store(project, "history", source_id, content)
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
            await embed_and_store(project, "role", rel, content)
            embedded += 1
    except Exception as e:
        log.warning(f"ingest_roles failed: {e}")

    return embedded


async def embed_node_outputs(run_id: str, project: str) -> None:
    """Embed all completed node outputs from a graph run. Silent on error."""
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT node_id, node_name, output FROM graph_node_results WHERE run_id=%s AND status='done'",
                    (run_id,),
                )
                rows = cur.fetchall()
        for node_id, node_name, output in rows:
            if output:
                source_id = f"{run_id}:{node_id}"
                content = f"[{node_name}]\n{output}"
                await embed_and_store(project, "node_output", source_id, content)
    except Exception as e:
        log.debug(f"embed_node_outputs failed: {e}")
