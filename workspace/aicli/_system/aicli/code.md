<!-- Last updated: 2026-04-26 18:22 UTC -->
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
│   │   ├── prompt_loader.py
│   │   └── tags.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── clean_pg_db.py
│   │   ├── dl_api_keys.py
│   │   ├── dl_seq.py
│   │   └── dl_user.py
│   ├── memory/
│   │   ├── __init__.py
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
│   ├── prompts/
│   │   ├── commit.yaml
│   │   ├── conflict_detection.yaml
│   │   ├── memory_files.yaml
│   │   ├── memory_synthesis.yaml
│   │   ├── misc.yaml
│   │   ├── react_base.yaml
│   │   └── work_items.yaml
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
├── cli/
│   ├── core/
│   ├── __init__.py
│   └── cli.py
├── documents/
│   └── use_cases/
│       ├── mcp-configuration.md
│       └── work-item-management-metadata-system.md
├── features/
│   └── shared-memory/
│       ├── feature_ai.md
│       └── feature_final.md
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
│   │   ├── cli/
│   │   ├── memory/
│   │   ├── pipelines/
│   │   ├── roles/
│   │   ├── starters/
│   │   ├── use_cases/
│   │   ├── workflows/
│   │   └── backlog_config.yaml
│   ├── aicli/
│   │   ├── _system/
│   │   ├── documents/
│   │   ├── logs/
│   │   ├── pipeline_logs/
│   │   ├── prompts/
│   │   ├── runs/
│   │   ├── workflows/
│   │   ├── commits.csv
│   │   ├── PROJECT.md
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
├── aicli.yaml
├── aicli_memory.md
├── CLAUDE.md
├── MEMORY.md
├── pyproject.toml
├── README.md
└── requirements.txt
```

---
_Generated by aicli. Run `/memory` to refresh._