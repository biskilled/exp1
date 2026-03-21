# Backward-compatibility shim — implementation moved to memory/embeddings.py
from memory.embeddings import *  # noqa: F401, F403
from memory.embeddings import (  # noqa: F401
    embed_and_store,
    embed_chunks,
    semantic_search,
    ingest_history,
    ingest_roles,
    ingest_commit,
    ingest_document,
    embed_node_outputs,
    smart_chunk_code,
    smart_chunk_markdown,
    smart_chunk_diff,
)
