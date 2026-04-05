"""mem_embeddings.py — all logic moved to memory_embedding.py. Re-exported for compat.

All callers (route_search, route_projects, route_chat, route_snapshots,
memory_promotion, pipeline_graph_runner) keep working without changes.
"""
from memory.memory_embedding import (
    embed_and_store,
    embed_chunks,
    semantic_search,
    ingest_history,
    ingest_roles,
    ingest_commit,
    ingest_document,
    embed_node_outputs,
    get_embedding,
    backfill_entity_tags,
    smart_chunk_code,
    smart_chunk_markdown,
    smart_chunk_diff,
    smart_chunk_text,
    MemoryEmbedding,
)

__all__ = [
    "embed_and_store",
    "embed_chunks",
    "semantic_search",
    "ingest_history",
    "ingest_roles",
    "ingest_commit",
    "ingest_document",
    "embed_node_outputs",
    "get_embedding",
    "backfill_entity_tags",
    "smart_chunk_code",
    "smart_chunk_markdown",
    "smart_chunk_diff",
    "smart_chunk_text",
    "MemoryEmbedding",
]
