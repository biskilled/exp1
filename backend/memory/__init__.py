# memory — 5-layer memory management for aicli
#
# Modules:
#   sessions.py          — JSON-file session store (message lists for LLM context continuity)
#   mem_embeddings.py    — Layer 4 semantic upgrade: pgvector chunking + similarity search (legacy)
#   memory_mirroring.py  — Layer 1 mirroring: store raw source data (prompts, commits, items, messages)
#   memory_tagging.py    — Layer 2 tagging: tag hierarchy, AI suggestions, event linkage
#   memory_embedding.py  — Layer 3 AI events: digest + embed into mem_ai_events
#   memory_promotion.py  — Layer 4 promotion: work item summaries, 4-layer snapshots, fact conflicts

from memory.memory_mirroring import MemoryMirroring
from memory.memory_tagging import MemoryTagging
from memory.memory_embedding import MemoryEmbedding
from memory.memory_promotion import MemoryPromotion, compute_relevance

__all__ = ["MemoryMirroring", "MemoryTagging", "MemoryEmbedding", "MemoryPromotion", "compute_relevance"]
