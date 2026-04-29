<!-- Last updated: 2026-04-29 20:14 UTC -->
# Code Map: aicli
_Comprehensive code structure — single source for all LLMs. Refresh: `/memory`_

## Project Structure

```
aicli/
├── backend/
│   ├── agents/
│   │   ├── mcp/
│   │   ├── providers/
│   │   ├── tools/
│   │   ├── yaml_config/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── orchestrator.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── db_migrations.py
│   │   ├── db_schema.sql
│   │   ├── logger.py
│   │   ├── pipeline_log.py
│   │   ├── project_paths.py
│   │   ├── prompt_loader.py
│   │   └── tags.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── clean_pg_db.py
│   │   ├── dl_api_keys.py
│   │   ├── dl_seq.py
│   │   └── dl_user.py
│   ├── memory/
│   │   ├── templates/
│   │   ├── yaml_config/
│   │   ├── __init__.py
│   │   ├── _wi_classify.py
│   │   ├── _wi_helpers.py
│   │   ├── _wi_markdown.py
│   │   ├── memory_code_parser.py
│   │   ├── memory_files.py
│   │   ├── memory_mirroring.py
│   │   ├── memory_promotion.py
│   │   ├── memory_sessions.py
│   │   └── memory_work_items.py
│   ├── pipelines/
│   │   ├── __init__.py
│   │   ├── pipeline_git.py
│   │   ├── pipeline_graph_runner.py
│   │   └── pipeline_runner.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── route_admin.py
│   │   ├── route_agent_roles.py
│   │   ├── route_agents.py
│   │   ├── route_auth.py
│   │   ├── route_billing.py
│   │   ├── route_chat.py
│   │   ├── route_config_sync.py
│   │   ├── route_documents.py
│   │   ├── route_files.py
│   │   ├── route_git.py
│   │   ├── route_graph_workflows.py
│   │   ├── route_history.py
│   │   ├── route_logs.py
│   │   ├── route_memory.py
│   │   ├── route_projects.py
│   │   ├── route_prompts.py
│   │   ├── route_search.py
│   │   ├── route_system.py
│   │   ├── route_system_roles.py
│   │   ├── route_usage.py
│   │   ├── route_user_api_keys.py
│   │   ├── route_work_items.py
│   │   └── route_workflows.py
│   ├── __init__.py
│   ├── main.py
│   ├── pwa_router.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── start_backend.sh
├── tests/
│   ├── __init__.py
│   ├── test_context_builder.py
│   ├── test_cost_tracker.py
│   ├── test_memory.py
│   ├── test_memory_compaction.py
│   ├── test_providers_base.py
│   ├── test_session_store.py
│   └── test_workflow_runner.py
├── ui/
│   ├── electron/
│   │   ├── main.js
│   │   ├── preload.js
│   │   └── terminal.js
│   ├── frontend/
│   │   ├── stores/
│   │   ├── styles/
│   │   ├── utils/
│   │   ├── views/
│   │   ├── index.html
│   │   ├── main.js
│   │   └── mobile-patches.js
│   ├── package-lock.json
│   ├── package.json
│   ├── VERSION
│   └── vite.config.mjs
├── workspace/
│   ├── _templates/
│   │   ├── documents/
│   │   ├── history/
│   │   ├── memory/
│   │   ├── pipelines/
│   │   ├── sessions/
│   │   └── state/
│   ├── aicli/
│   │   ├── documents/
│   │   ├── history/
│   │   ├── logs/
│   │   ├── memory/
│   │   ├── pipelines/
│   │   ├── sessions/
│   │   ├── state/
│   │   └── project.yaml
│   ├── test-proj/
│   │   ├── _system/
│   │   ├── documents/
│   │   ├── history/
│   │   ├── prompts/
│   │   ├── workflows/
│   │   ├── CLAUDE.md
│   │   ├── PROJECT.md
│   │   └── project.yaml
│   └── test-verify/
│       ├── _system/
│       ├── documents/
│       ├── history/
│       ├── prompts/
│       ├── workflows/
│       ├── CLAUDE.md
│       ├── PROJECT.md
│       └── project.yaml
├── AGENTS.md
├── aicli.yaml
├── aicli_memory.md
├── CLAUDE.md
├── GEMINI.md
├── MEMORY.md
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Active Work Items

- **[pending]** `bug` Work Item UI Category Display Bug  _(due 2026-05-02)_
- **[open]** `use_case` Work Item Management & Metadata System  _(due 2026-05-02)_
- **[open]** `use_case` MCP Configuration
- **[pending]** `task` Verify Hook-Log DB Storage After Migration  _(due 2026-05-02)_
- **[in-progress]** `task` Audit and clean planner_tags table schema

## Coding Conventions

- **Python style**: Python 3.12+; type hints on all new functions; no `from X import *`
- **Imports**: stdlib → third-party → local; each group alphabetically sorted
- **Async**: use `async`/`await` throughout FastAPI routes; no blocking calls in async context
- **DB access**: always use `db.conn()` context manager (psycopg2 pool); parameterized queries only
- **Error handling**: log with `log.warning()` for expected errors, `log.exception()` for unexpected; return 422/404 from routes, never 500 for known cases
- **Naming**: `snake_case` for Python; `camelCase` for JS; `UPPER_SNAKE` for module-level constants
- **LLM prompts**: all prompts in `backend/prompts/*.yaml`; load via `prompt_loader.prompts.content(key)`; never inline strings
- **Work items**: `user_status` is TEXT (`open|pending|

## Recently Changed
_Last 20 symbol-level changes (class / method / function)._

| Symbol | Change | Commit | Summary |
|--------|--------|--------|---------|
| `m051_schema_refactor_user_id_updated_at` | modified | `b3d2fda3` | This migration function refactors the database schema to convert user  |
| `_resolve_user_id` | modified | `b3d2fda3` | The function now handles multiple input types (int, str, or None) and  |
| `MemoryFiles` | modified | `b3d2fda3` | The MemoryFiles class was updated to include additional fields (event_ |
| `MemoryFiles.get_top_events` | modified | `b3d2fda3` | The `get_top_events` method now converts database query results into a |
| `_loadSessions` | modified | `b48376c2` | The `_loadSessions` function was updated to restore the last known ses |
| `chat_history` | modified | `b48376c2` | The `chat_history` function was modified to fetch a larger set of data |
| `_normalize_jsonl_entry` | modified | `b4a10441` | This new function normalizes history.jsonl entries to match the databa |
| `m050_prompts_source_id_index` | modified | `d45c125b` | Added a database migration to create a unique partial index on `mem_mr |
| `_Database` | modified | `18dc4454` | The `_Database` class now validates database connections before use by |
| `_Database.conn` | modified | `18dc4454` | The `conn` method now validates database connections before returning  |
| `MemoryEmbedding.process_item` | modified | `25e5c306` | The method now includes error handling to catch and log exceptions dur |
| `MemoryEmbedding` | modified | `25e5c306` | I don't see a diff provided in your message. Could you please share th |
| `m047_events_is_system` | modified | `ec75b516` | Added a database migration to add an `is_system` BOOLEAN column to the |
| `_is_system_commit` | modified | `ec75b516` | The function `_is_system_commit` was added to detect auto-generated sy |
| `sync_commits` | modified | `ec75b516` |  |
| `_embed_commits_background` | modified | `ec75b516` | The `_embed_commits_background` function was enhanced to asynchronousl |
| `MemoryEmbedding.process_commit_batch` | modified | `ec75b516` | The method now detects and flags commits that only modify system files |

## Code Hotspots
_Files with highest commit frequency — candidates for refactoring._

| File | Score | Commits | Lines | Bug Fixes | Last Changed |
|------|-------|---------|-------|-----------|--------------|
| `backend/memory/memory_code_parser.py` | 58.9626 | 2 | 788 | 0 | 2026-04-22 |
| `backend/memory/memory_work_items.py` | 30.0 | 28 | 1378 | 0 | 2026-04-29 |
| `backend/memory/memory_files.py` | 20.0 | 18 | 1176 | 0 | 2026-04-27 |
| `backend/routers/route_projects.py` | 19.0 | 17 | 1693 | 0 | 2026-04-29 |
| `backend/core/db_migrations.py` | 14.0 | 12 | 3320 | 0 | 2026-04-29 |
| `ui/frontend/views/prompts.js` | 11.0 | 9 | 1623 | 0 | 2026-04-29 |
| `backend/agents/mcp/server.py` | 11.0 | 9 | 854 | 0 | 2026-04-27 |
| `ui/frontend/views/work_items.js` | 11.0 | 9 | 2595 | 0 | 2026-04-24 |
| `backend/routers/route_git.py` | 9.0 | 7 | 1691 | 0 | 2026-04-27 |
| `backend/routers/route_agent_roles.py` | 8.0 | 6 | 1343 | 0 | 2026-04-29 |
| `backend/routers/route_work_items.py` | 7.0 | 7 | 594 | 0 | 2026-04-27 |
| `backend/core/database.py` | 6.0 | 6 | 754 | 0 | 2026-04-29 |
| `backend/routers/route_memory.py` | 5.0 | 3 | 836 | 0 | 2026-04-27 |
| `backend/routers/route_chat.py` | 5.0 | 3 | 975 | 0 | 2026-04-27 |

## File Coupling
_Files frequently committed together — likely tightly coupled._

| File A | File B | Co-changes |
|--------|--------|------------|
| `backend/memory/memory_work_items.py` | `ui/frontend/views/work_items.js` | 8 |

---
_Generated by aicli. Run `/memory` to refresh._