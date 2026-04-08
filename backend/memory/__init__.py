# memory — 5-layer memory management for aicli
#
# Modules:
#   memory_sessions.py   — Layer 2 working memory: JSON-file session store (LLM message context)
#   memory_mirroring.py  — Layer 1 mirroring: store raw source data (prompts, commits, items, messages)
#   memory_tagging.py    — planner_tags CRUD + AI tag suggestions + work-item matching
#   memory_embedding.py  — Layer 3 AI events: Haiku digest + OpenAI embed → mem_ai_events
#   memory_promotion.py  — Layer 4 promotion: work item summaries, feature snapshots, fact conflicts
#   memory_extraction.py — work item code intelligence: aggregate commits + LLM extraction
#   memory_code_parser.py — tree-sitter AST → mem_mrr_commits_code (per-symbol diff stats)
#   memory_files.py      — deterministic template render → CLAUDE.md / .cursorrules / llm_prompts
#   memory_planner.py    — planner doc generation → documents/{cat}/{slug}.md

from memory.memory_mirroring import MemoryMirroring
from memory.memory_tagging import MemoryTagging
from memory.memory_embedding import MemoryEmbedding
from memory.memory_promotion import MemoryPromotion, compute_relevance
from memory.memory_files import MemoryFiles

__all__ = ["MemoryMirroring", "MemoryTagging", "MemoryEmbedding", "MemoryPromotion", "compute_relevance", "MemoryFiles"]
