# Commit Analysis — aicli
_Generated: 2026-04-18 18:15 UTC_

## Summary
| | Count |
|---|---|
| Linked commits (via prompt_id) | 255 |
| Standalone commits | 353 |
| Pending (not yet processed) | 3 |

| Unique files touched | 35 |
| Total rows added | 7133 |
| Total rows removed | 2521 |

## Linked Commits by Prompt Ref
| Prompt | Commits | Files | +Lines | -Lines |
|--------|---------|-------|--------|--------|
| P102348 | 52 | 17 | 1850 | 891 |
| P102285 | 7 | 0 | 0 | 0 |
| P102273 | 6 | 0 | 0 | 0 |
| P102289 | 6 | 10 | 318 | 355 |
| P102210 | 4 | 0 | 0 | 0 |
| P102347 | 4 | 1 | 191 | 0 |
| P102272 | 3 | 0 | 0 | 0 |
| P102325 | 3 | 8 | 262 | 183 |
| P102287 | 3 | 0 | 0 | 0 |
| P102244 | 3 | 0 | 0 | 0 |
| P102312 | 2 | 3 | 124 | 13 |
| P102341 | 2 | 4 | 39 | 47 |
| P102211 | 2 | 0 | 0 | 0 |
| P102316 | 2 | 1 | 12 | 5 |
| P102279 | 2 | 0 | 0 | 0 |
| P102245 | 2 | 0 | 0 | 0 |
| P102295 | 2 | 0 | 0 | 0 |
| P102315 | 2 | 1 | 1 | 1 |
| P102342 | 2 | 5 | 35 | 46 |
| P102359 | 2 | 0 | 0 | 0 |
| P102156 | 1 | 0 | 0 | 0 |
| P102154 | 1 | 0 | 0 | 0 |
| P102147 | 1 | 0 | 0 | 0 |
| P102168 | 1 | 0 | 0 | 0 |
| P102167 | 1 | 0 | 0 | 0 |
| P102153 | 1 | 0 | 0 | 0 |
| P102169 | 1 | 0 | 0 | 0 |
| P102170 | 1 | 0 | 0 | 0 |
| P102171 | 1 | 0 | 0 | 0 |
| P102172 | 1 | 0 | 0 | 0 |
| P102166 | 1 | 0 | 0 | 0 |
| P102165 | 1 | 0 | 0 | 0 |
| P102152 | 1 | 0 | 0 | 0 |
| P102146 | 1 | 0 | 0 | 0 |
| P102143 | 1 | 0 | 0 | 0 |
| P102164 | 1 | 0 | 0 | 0 |
| P102163 | 1 | 0 | 0 | 0 |
| P102151 | 1 | 0 | 0 | 0 |
| P102217 | 1 | 0 | 0 | 0 |
| P102216 | 1 | 0 | 0 | 0 |
| P102162 | 1 | 0 | 0 | 0 |
| P102215 | 1 | 0 | 0 | 0 |
| P102218 | 1 | 0 | 0 | 0 |
| P102219 | 1 | 0 | 0 | 0 |
| P102220 | 1 | 0 | 0 | 0 |
| P102221 | 1 | 0 | 0 | 0 |
| P102222 | 1 | 0 | 0 | 0 |
| P102223 | 1 | 0 | 0 | 0 |
| P102224 | 1 | 0 | 0 | 0 |
| P102214 | 1 | 0 | 0 | 0 |

## Top Files Changed (Linked Commits)
| File | Commits | +Lines | -Lines |
|------|---------|--------|--------|
| `backend/core/db_migrations.py` | 18 | 1134 | 13 |
| `ui/frontend/views/entities.js` | 17 | 513 | 290 |
| `backend/memory/memory_promotion.py` | 14 | 630 | 381 |
| `backend/routers/route_work_items.py` | 13 | 362 | 263 |
| `backend/memory/memory_embedding.py` | 8 | 136 | 364 |
| `backend/memory/memory_files.py` | 7 | 84 | 130 |
| `backend/routers/route_memory.py` | 6 | 468 | 11 |
| `backend/memory/memory_tagging.py` | 4 | 143 | 67 |
| `backend/routers/route_snapshots.py` | 4 | 40 | 43 |
| `backend/routers/route_git.py` | 4 | 37 | 18 |
| `backend/memory/memory_planner.py` | 4 | 18 | 33 |
| `backend/routers/route_admin.py` | 3 | 263 | 11 |
| `backend/routers/route_history.py` | 3 | 74 | 27 |
| `backend/core/database.py` | 3 | 58 | 219 |
| `backend/agents/mcp/server.py` | 3 | 21 | 14 |
| `backend/routers/route_projects.py` | 3 | 12 | 12 |
| `backend/memory/memory_code_parser.py` | 3 | 2 | 23 |
| `backend/routers/route_tags.py` | 2 | 85 | 123 |
| `backend/routers/route_entities.py` | 2 | 40 | 147 |
| `backend/routers/route_chat.py` | 2 | 28 | 15 |
| `backend/agents/tools/tool_memory.py` | 2 | 4 | 4 |
| `ui/frontend/views/pipeline.js` | 1 | 267 | 90 |
| `backend/core/prompt_loader.py` | 1 | 192 | 0 |
| `ui/frontend/views/chat.js` | 1 | 12 | 14 |
| `backend/memory/memory_extraction.py` | 1 | 10 | 10 |
| `backend/memory/memory_feature_snapshot.py` | 1 | 8 | 12 |
| `backend/core/auth.py` | 1 | 6 | 2 |
| `backend/routers/route_search.py` | 1 | 3 | 3 |
| `backend/pipelines/pipeline_graph_runner.py` | 1 | 2 | 2 |
| `backend/routers/route_prompts.py` | 1 | 1 | 1 |

## Standalone Commits (no prompt link)
| Hash | Message | Files | +Lines | -Lines |
|------|---------|-------|--------|--------|
| `8a2ae639` | chore: restructure _system context files after claude cli se | 0 | 0 | 0 |
| `aaede1b7` | chore: remove stale auto-generated system context and agent  | 0 | 0 | 0 |
| `c7001c6b` | chore: remove stale agent context and legacy system docs aft | 0 | 0 | 0 |
| `085cc952` | chore: remove legacy flat _system files after claude cli ses | 0 | 0 | 0 |
| `d0a47ec2` | chore: restructure _system docs — remove flat files, migrate | 0 | 0 | 0 |
| `af46ffea` | chore: clean up legacy flat _system files after claude cli s | 0 | 0 | 0 |
| `2f9e42e9` | chore: remove stale agent context and system documentation f | 0 | 0 | 0 |
| `0e20a582` | chore: remove stale agent context and flattened system docs  | 0 | 0 | 0 |
| `829bebdd` | chore: remove legacy flat _system files after claude cli ses | 0 | 0 | 0 |
| `d2b5ed76` | chore: remove stale auto-generated system context and agent- | 0 | 0 | 0 |
| `4da0f35b` | chore: remove legacy flat system files after claude cli sess | 0 | 0 | 0 |
| `eab544df` | chore: remove stale auto-generated context and agent files a | 0 | 0 | 0 |
| `50722392` | chore: remove legacy flat _system files after claude cli ses | 0 | 0 | 0 |
| `3ba4ec91` | chore: remove stale agent context and flat system docs after | 0 | 0 | 0 |
| `3548438b` | chore: remove stale generated context files after claude cli | 0 | 0 | 0 |
| `d278e841` | chore: consolidate agent context files after claude cli sess | 0 | 0 | 0 |
| `f38b39e5` | chore: remove deprecated flat _system context files after cl | 0 | 0 | 0 |
| `918224d7` | chore: remove stale auto-generated system context files afte | 0 | 0 | 0 |
| `62a855dc` | after claude cli session 54a71132 | 0 | 0 | 0 |
| `b77fdbf0` | chore: clean up stale backlog, agent-context, and system doc | 0 | 0 | 0 |
| `73944455` | chore: clean up legacy flat _system files after session 54a7 | 0 | 0 | 0 |
| `18c7342d` | chore: remove stale agent context and auto-generated system  | 0 | 0 | 0 |
| `5b020ca2` | chore: remove legacy flat _system context files after sessio | 0 | 0 | 0 |
| `a1970829` | chore: remove stale agent context and generated system docs  | 0 | 0 | 0 |
| `856c4884` | chore: remove stale agent context and flat system docs after | 0 | 0 | 0 |
| `8e8be227` | chore: clean up legacy _system root files after claude cli s | 0 | 0 | 0 |
| `bcc1e36d` | chore: clean up legacy _system flat files after claude cli s | 0 | 0 | 0 |
| `e6ca2f0b` | chore: clean up legacy _system flat files after claude cli s | 0 | 0 | 0 |
| `fdfe5d7f` | chore: remove legacy flat _system context files after claude | 0 | 0 | 0 |
| `b73469fa` | chore: clean up legacy _system root files after claude cli s | 0 | 0 | 0 |
| `c5bd8ecd` | chore: clean up stale agent context and deprecated system fi | 0 | 0 | 0 |
| `19aae8c0` | chore: remove auto-generated system context files after clau | 0 | 0 | 0 |
| `9d627aa7` | chore: clean up stale agent context and generated system fil | 0 | 0 | 0 |
| `7883c111` | chore: remove legacy _system/ context files after claude cli | 0 | 0 | 0 |
| `04b2c503` | chore: remove legacy _system/ context files after claude cli | 0 | 0 | 0 |
| `5b320a84` | chore: remove legacy _system/ root files and migrate to stru | 0 | 0 | 0 |
| `a9a2ed70` | chore: clean up legacy _system/ context files after claude c | 0 | 0 | 0 |
| `d1a33930` | chore: remove legacy _system/ context files after claude cli | 0 | 0 | 0 |
| `d1299d65` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `348521e0` | chore: update 65 files | 0 | 0 | 0 |
| `92b268ab` | chore: update 58 files | 0 | 0 | 0 |
| `7bb11602` | chore: update 62 files | 0 | 0 | 0 |
| `98da5b6c` | chore: update 65 files | 0 | 0 | 0 |
| `500d8a20` | chore: update 61 files | 0 | 0 | 0 |
| `c082991c` | chore: update 64 files | 0 | 0 | 0 |
| `aa343f49` | chore: update 62 files | 0 | 0 | 0 |
| `04658339` | chore: update 69 files | 0 | 0 | 0 |
| `d6da27a1` | chore: update 66 files | 0 | 0 | 0 |
| `e46c4a8e` | chore: update 65 files | 0 | 0 | 0 |
| `399efdf6` | chore: update 63 files | 0 | 0 | 0 |
| `b6bf37ff` | chore: update 73 files | 0 | 0 | 0 |
| `181e9fb2` | chore: update 63 files | 0 | 0 | 0 |
| `975afe30` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `0179952b` | chore: remove legacy _system/ agent context and documentatio | 0 | 0 | 0 |
| `59133295` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `fca917f2` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `516965c2` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `6e5cd17f` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `88e0f377` | chore: remove legacy _system/ agent context and documentatio | 0 | 0 | 0 |
| `52e1aa09` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `7e289f4e` | chore: remove legacy _system/ agent context files after clau | 0 | 0 | 0 |
| `d45c125b` | chore: remove stale agent context and generated system docs  | 1 | 21 | 0 |
| `529543b5` | chore: clean up stale agent context and generated system fil | 0 | 0 | 0 |
| `9024d41b` | chore: remove stale agent context and system documentation f | 0 | 0 | 0 |
| `9bf6684a` | chore: consolidate and restructure _system context/memory fi | 6 | 235 | 0 |
| `79e56286` | chore: clean up stale agent context and legacy system files  | 0 | 0 | 0 |
| `bf7be2be` | chore: clean up legacy system context files after claude cli | 30 | 768 | 40 |
| `f3885e5d` | chore: clean up stale agent context and auto-generated syste | 18 | 989 | 0 |
| `6a0fd1c7` | chore: remove legacy _system root context files after claude | 10 | 108 | 10 |
| `7d08fdd6` | chore: clean up stale agent context and system documentation | 5 | 60 | 2 |
| `587c92e8` | chore: clean up stale agent context and system memory files  | 29 | 299 | 127 |
| `7cd83d05` | docs: update system context and memory files after CLI sessi | 0 | 0 | 0 |
| `c7df759d` | chore: remove stale system context and claude session files | 0 | 0 | 0 |
| `ad89aa95` | docs: update system prompts and memory after CLI session 14a | 0 | 0 | 0 |
| `46b5b785` | docs: update system prompts and memory after claude session | 0 | 0 | 0 |
| `00179d1b` | chore: remove aicli system context and claude session files | 0 | 0 | 0 |
| `e369b6a3` | docs: update system context and memory files after claude se | 0 | 0 | 0 |
| `0377afac` | feat: update system docs and refactor work items after CLI s | 0 | 0 | 0 |
| `3e9f3511` | docs: update system context and memory files after claude se | 0 | 0 | 0 |
| `dfeac41a` | chore: clean up system context and CLAUDE.md files after ses | 0 | 0 | 0 |
| `0eb32eb` | chore(cli): auto-commit after AI session — 2 file(s) — 2026- | 0 | 0 | 0 |
| `91e47c03` | docs: update system context and CLAUDE.md files post-session | 0 | 0 | 0 |
| `0c856f94` | docs: update memory and rules after claude cli session b9e39 | 0 | 0 | 0 |
| `d54f4027` | chore: remove stale system context and claude config files | 0 | 0 | 0 |
| `7eb54cee` | docs: update system context and memory files post-session | 0 | 0 | 0 |
| `48e3613b` | docs: update MEMORY.md session notes | 0 | 0 | 0 |
| `fc6a89ab` | docs: update MEMORY.md session notes | 0 | 0 | 0 |
| `b3cf472b` | docs: update system context and memory files post-session | 0 | 0 | 0 |
| `140e9f3a` | docs: clean up system context and memory files after claude  | 0 | 0 | 0 |
| `da1e51dc` | docs: update system context and memory after claude session  | 0 | 0 | 0 |
| `64d5ca25` | chore: remove aicli system context and claude session files | 0 | 0 | 0 |
| `9a9a32de` | docs: update system context and memory files after claude se | 0 | 0 | 0 |
| `6870d3b3` | docs: update system context and memory files post-session | 0 | 0 | 0 |
| `5a5271c7` | docs: update system context and memory after CLI session 8b9 | 0 | 0 | 0 |
| `afa2c384` | docs: update memory and rules after claude cli session 8b91f | 0 | 0 | 0 |
| `bae8be3a` | chore: remove stale system context and claude session files | 0 | 0 | 0 |
| `3252ac04` | docs: update system context and memory files after claude se | 0 | 0 | 0 |
| `d3a6cec8` | docs: update system context and memory files after CLI sessi | 0 | 0 | 0 |
| `a2a7912b` | docs: update MEMORY.md and system docs after claude session | 0 | 0 | 0 |
| `6b1d2912` | docs: update system context and memory files after CLI sessi | 0 | 0 | 0 |
