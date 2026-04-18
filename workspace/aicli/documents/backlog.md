# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items` to merge approved items into use cases.

## **discovery** · 26/03/10-03:16 [ ] (claude)
> Type: existing
> Total: 10 prompts
> User tags:
> AI existing: [task:discovery]
> AI new:
> Summary: Project overview, architecture review, and system explanation
> Requirements: User greeted and asked about current state; Explain aicli system to a friend in simple terms; Run /memory command and assess current architecture; Review how data is stored; Verify MCP usage and tagging mechanisms
> Deliveries: [task|completed|4|4] Documented aicli's 5-layer memory system with architecture, pipeline flows, and relevance scoring; [task|completed|4|2] Reviewed 3-layer client/project architecture and identified scalability concerns for multi-client scenarios; [task|completed|4|2] Explained aicli unified AI memory concept and core system functionality through multiple approaches; [task|in-progress|1|2] Analyzed mirror table triggers, project_facts stage flows, and LLM prompt usage with partial completion

  PROMPTS P102155 [ ] [task] [completed] [2] — Greeting and project context refresh
    Requirements: User greeted and asked about current state
    Deliveries: Acknowledged aicli project status; Summarized recent work (AI suggestion banners, session tags, planner UI, port binding fixes); Offered to help with next steps

  PROMPTS P102157 [ ] [task] [completed] [4] — Explained aicli core concept: unified AI memory across tools
    Requirements: Explain aicli system to a friend in simple terms
    Deliveries: Defined aicli as shared AI memory platform for developers; Described core problem: different AI tools lack persistent memory; Explained solution: unified history, git commit tagging, memory files; Commit df7f6829 shows system docs updated

  PROMPTS P102187 [ ] [task] [completed] [4] — Ran /memory audit, reviewed architecture, data storage, MCP usage, and tagging system
    Requirements: Run /memory command and assess current architecture; Review how data is stored; Verify MCP usage and tagging mechanisms; Test memory quality and retrieval; Check if tagging works for embedding/retrieval
    Deliveries: Executed /memory successfully, generated 5 files at 17:43 UTC; Confirmed 5-layer memory system architecture; Documented file layer structure (workspace/aicli/_system/history.jsonl); Assessed synthesis cache status; Provided architectural assessment

  PROMPTS P102194 [ ] [task] [in-progress] [0] — Request to use MCP tool and explain project (no response)
    Requirements: Use MCP tool to explain what the project is about

  PROMPTS P102197 [ ] [task] [completed] [4] — Used MCP tool to explain aicli code: 5-layer memory system
    Requirements: Use MCP tool and explain what the code does
    Deliveries: Described aicli as shared AI memory platform solving context loss across AI tools; Explained 5-layer memory system architecture; Outlined core functionality: persistent memory across clients (Claude CLI, Cursor, ChatGPT, web UI); Started describing /memory command synthesis

  PROMPTS P102208 [ ] [task] [completed] [4] — Architectural review: 3-layer client/project design with scale concerns
    Requirements: Review architecture for multi-client, multi-project scenarios; Advise on managing free/unregistered clients
    Deliveries: Confirmed 3-tier naming structure is clear; Documented seeding pattern (mng_ → cl_local_) works for single-tenant; Identified scale concern: table proliferation (120 client tables + 2000 project tables at 20×10 scale); Provided PostgreSQL capacity assessment; Recommended consolidation strategy for free/unregistered clients

  PROMPTS P102213 [ ] [task] [in-progress] [0] — Question about user-client relationship and memory_items/project_facts updates (no response)
    Requirements: Clarify users as part of client structure (multiple users per client); Verify memory_items and project_facts are being updated correctly for better memory mechanism

  PROMPTS P102280 [ ] [task] [in-progress] [2] — Requested detailed flow analysis of mirror tables, triggers, and LLM prompts (partial response)
    Requirements: Describe mirror table flow: triggers, data stored, LLM prompts used; Explain project_fact stage: triggers, LLM usage, prompts; Explain work_items stage: triggers, LLM usage, prompts; Show important columns per table with source (LLM/calculated); Create comparison table of all important columns
    Deliveries: Referenced prior diagnostic on 60-second migration time; Commit 7c2992ce shows system context and memory files updated

  PROMPTS P102281 [ ] [task] [completed] [4] — Detailed memory pipeline analysis: 4 stages with column sources and relevance scoring
    Requirements: Describe mirror tables flow, triggers, data storage, LLM prompts; Analyze project_fact stage with triggers and LLM usage; Analyze work_items stage with triggers and LLM usage; Show important columns with source attribution (LLM/calculated); Create comprehensive column comparison table with relevance scores
    Deliveries: Documented Stage 1: Mirror tables (mem_mrr_*) as pure capture with no LLM; Detailed mem_mrr_prompts trigger, columns, and relevance ratings; Showed column-by-column source attribution (Raw user text, Raw LLM text, etc.); Documented trigger types and data flow; Commit 3d2b5555 shows system context and memory files updated with complete analysis

  PROMPTS P102283 [ ] [task] [completed] [5] — Updated aicli_memory.md with complete layer documentation and relevance scoring
    Requirements: Access and review aicli_memory.md file from project root; Update with all 4 layers, column responsibility, and relevance ratings
    Deliveries: Updated aicli_memory.md at correct location (/Users/user/Documents/gdrive_cellqlick/2026/aicli/); Added per-column Responsible attribution (User/LLM/Trigger) and Relevance (0-5) ratings for all 4 layers; Updated mem_mrr_commits documentation to reflect dropped columns (diff_summary/diff_details) and actual columns (tags[files], tags[symbols], tags[languages]); Documented mem_ai_events.importance now LLM-scored 0-10 (previously hardcoded 1); Fully documented mem_ai_work_items with status tracking

---

## **ui-rendering-bugs** · 26/03/10-00:11 [ ] (claude)
> Type: new
> Total: 30 prompts
> User tags:
> AI existing:
> AI new: [bug:ui-rendering]
> Summary: UI loading, display, and rendering issues
> Requirements: UI not loading properly with bind address 127.0.0.1:8000 error; Cannot see anything after shutting down Electron and running fresh; No UI display when clicking on project name; Suspected PostgreSQL network connection issue; Action options too small and hard to see
> Deliveries: [bug|completed|4|5] Fixed phase persistence across sessions and UI display in Chat, History, and Commit views; [bug|completed|4|3] Resolved backend connectivity and project loading issues with retry logic and session initialization; [feature|completed|4|4] Enhanced Work Items panel with sticky headers, AI tag suggestions, improved layout, and visual formatting; [feature|in-progress|3|5] Improving Chat UI with timestamps, session ID display, per-prompt tags, and tag color coding; [bug|in-progress|3|3] Addressing Work Items display bugs including tag visibility, description truncation, and category filtering

  PROMPTS P102148 [ ] [feature] [in-progress] [2] — Addressed planner UI visibility issues and proposed contextual menu with task details.
    Requirements: Action options too small and hard to see; Archive feature prevents reactivation of items; Request to add 3-dot menu for task details (remark, due date, created, archived status); Request to add tags to new chats for association
    Deliveries: Reviewed code for import resolution errors and syntax validation; Commit delivered with UI view updates and AI workspace system file sync

  PROMPTS P102267 [ ] [feature] [in-progress] [1] — User reports history shows only small text instead of full prompt/LLM response and requests copy fun
    Requirements: History should display full prompt and LLM response, not truncated text; Add ability to copy text from history UI
    Deliveries: Acknowledged requirements via documentation update commit

  PROMPTS P102299 [ ] [feature] [completed] [4] — Added work items UI panel with date formatting and visual improvements after backend SQL restart.
    Requirements: User asked where new feature was added in the UI (Work item tab in Planner); Clarify implementation location
    Deliveries: Implemented _renderWiPanel function with work items display; Added fmtDate function for date formatting; Added hdr function for header rendering; Updated backend route_work_items.py to support get_unlinked_work_items

  PROMPTS P102304 [ ] [feature] [completed] [4] — Implemented sticky headers, AI tag suggestions per row with approve/reject actions, and improved tag
    Requirements: User asked if AI suggestions appear on each row in work_items; Display AI tag suggestions with approve/reject capability
    Deliveries: Made all 3 sortable column headers sticky (position:sticky; top:0; z-index:1); Added ai_tag_name suggestion display on each work item row; Implemented approve button (✓) to PATCH tag_id = ai_tag_id; Implemented reject button (×) to PATCH ai_tag_id = ''; Enhanced MemoryTagging.match_work_item_to_tags logic with better matching

  PROMPTS P102309 [ ] [feature] [in-progress] [3] — Add table padding, fix date display, implement tag color coding (green/red/blue), and debug missing 
    Requirements: Add left padding to table; UPDATED column shows truncated date (yy:mm:dd-HH:..); Color-code tags: AI(EXIST)=green, AI(NEW)=red, USER=blue; Clarify why many work_items lack AI recommendations
    Deliveries: Added missing import json in route_work_items.py for suggested_new persistence; Fixed stray conn.commit() outside context manager; Implemented Level 4 fallback logic in match_work_item_to_tags() to trigger on empty results

  PROMPTS P102349 [ ] [feature] [in-progress] [3] — Fix UI not updating, restore latest prompts display, add tag option to user prompts, and investigate
    Requirements: UI changes not visible; latest prompts from claude cli not appearing in chat; Chat used to auto-update with new prompts; now no update occurs; Add tag option to user prompts (same functionality as History/prompts, store in mem_mrr_prompts); Clarify if local JSON session storage is still working
    Deliveries: Fixed silent DB error in hook-log endpoint via migration m050; all prompts now stored correctly; Added ⟳ reload UI button in History tab header to force window.location.reload(); Confirmed Vite dev server serving updated history.js

  PROMPTS P102350 [ ] [feature] [in-progress] [3] — Add timestamp next to YOU, display session ID in left/top panels, and add per-prompt tag functionali
    Requirements: Each prompt missing timestamp next to YOU; Session ID should appear on left panel (last 5 chars) and top of right pane; Add per-prompt tag option with access to all existing user tags (with default tags per prompt/session)
    Deliveries: Session ID badge displays last 5 chars as …xxxxx in left panel header; Added styled session ID banner in right pane with copy button (⎘); Changed tag filtering logic to show all tags per prompt (phase: filter replaced)

  PROMPTS P102351 [ ] [feature] [in-progress] [3] — Update session header display, add session ID banner, and implement per-prompt tags in chat tab.
    Requirements: Session number and 5-char ID should appear in CLI header <phase>; Session ID should display in row with Phase/tags at top; Add tag option to prompts in chat tab; show all existing tags per prompt
    Deliveries: Session header now shows: ▼ CLI · development · (ab3f9) · 3 prompts · 26/04/15-19:31; Source label mapping: claude_cli→CLI, ui→UI, workflow→Workflow; Phase chip extracted from entry tags; Session ID in (xxxxx) format (last 5 chars); Each prompt entry displays YOU — YY/MM/DD-HH:MM format

  PROMPTS P102142 [ ] [bug] [completed] [4] — Diagnosed bind error on port 8000 caused by stale uvicorn instance; verified backend is healthy.
    Requirements: UI not loading properly with bind address 127.0.0.1:8000 error
    Deliveries: Identified root cause: old uvicorn process (PID 86671) still holding port 8000; Verified backend is healthy and `due_date` column is live in API; Confirmed JS syntax is valid in both entities.js and chat.js; Provided fix: Cmd+R reload in Electron window to pick up new JS files

  PROMPTS P102172 [ ] [bug] [completed] [4] — Fixed phase persistence issue where app load showed 'required' and phase didn't update on session sw
    Requirements: Phase shows as 'required' (default) on app load; Phase doesn't update properly when switching between chat sessions
    Deliveries: Root cause 1: No code loaded last phase from DB on startup; Root cause 2: session.metadata.tags could be missing for old sessions; PUT endpoint never called; Root cause 3: Phase dropdown changes were never persisted to DB; Implemented fix: Load phase from DB on app init with proper fallbacks

  PROMPTS P102173 [ ] [bug] [completed] [4] — Implemented phase persistence across sessions and added phase filtering to Commit history view.
    Requirements: Cannot save phase changes in chat; Phase doesn't update when switching sessions; Need phase display in commits with filtering capability; History should filter by phases; Chat should update per session
    Deliveries: Removed `_sessionId = null` on phase change to preserve session context; Created PATCH /chat/sessions/{id}/tags endpoint for phase updates; Implemented api.patchSessionTags(id, {phase}) called on phase change; Added phase filter to commit view matching chat filter functionality; Ensured PUT /history/session-tags persists globally for app restart

  PROMPTS P102174 [ ] [bug] [completed] [4] — Restored session-specific phase handling and fixed phase visibility across Chat, History, and Commit
    Requirements: Cannot change/update phase in Chat; Most chat sessions lack correct phase; Phase doesn't update when switching sessions; History default should show all phases, not 'discovery'; Commit filter cannot be changed and disappears after change
    Deliveries: Restored phase isolation: _sessionId = null per phase creates separate sessions; Added api.putSessionTags(project, {phase}) for global persistence; Implemented on init: api.getSessionTags(project) to pre-fill dropdown; Fixed session switch with session.metadata.tags + _sessionCache fallback; Corrected default filter display across all views

  PROMPTS P102175 [ ] [bug] [completed] [4] — Verified phase change persistence and session metadata updates for both new and existing sessions.
    Requirements: Uploaded session doesn't show correct phase; Phase doesn't change properly when switching sessions; Need correct phase per session and ability to update it
    Deliveries: Confirmed PATCH /chat/sessions/{id}/tags endpoint is live and working; Phase change on existing session calls api.patchSessionTags(_sessionId, {phase}) and refreshes session list; Phase change on new chat updates _sessionTags.phase in memory until session created; Verified endpoint returns correct 404 for non-existent sessions

  PROMPTS P102176 [ ] [bug] [completed] [4] — Fixed red warning badge display for all sessions without phase and phase persistence for CLI/WF sess
    Requirements: Red flags on sessions not related to phase status; CLI-loaded sessions not flagged as missing phase; Phase configuration not saving properly; All sessions should be tagged with proper phase and saved
    Deliveries: Removed source === 'ui' condition; now ALL sessions (UI, CLI, WF) without phase show red ⚠ badge and border; Fixed PATCH /chat/sessions/{id}/tags to handle CLI sessions via fallback to _system/session_phases.json; Ensured phase saves globally keyed by session ID regardless of source; Verified red badge and visual indicators now correctly reflect phase status across all session types

  PROMPTS P102196 [ ] [bug] [in-progress] [1] — User reports missing aiCli project and slow PROJECT.md loading (>1min), suspects DB query issue.
    Requirements: aiCli project disappeared from recent projects list; Loading PROJECT.md file takes over a minute; Investigate if slow load is due to database query on free Railway tier
    Deliveries: Acknowledged issue and indicated final check on openProject function

  PROMPTS P102212 [ ] [bug] [completed] [4] — Fixed project loading retry logic to handle empty results and backend startup delays.
    Requirements: aiCli missing from projects list despite appearing in Recent; Backend fails to load initially, succeeds after couple seconds
    Deliveries: Updated _continueToApp to retry once if projects load succeeds but returns empty; Improved handling of race condition between frontend and backend startup

  PROMPTS P102268 [ ] [bug] [completed] [4] — Fixed history display to show both prompt and LLM response using consistent hooks and backend calls.
    Requirements: History previously showed prompt and LLM response, now only shows prompt; Restore full history display with both prompt and response
    Deliveries: Verified BACKEND_URL is defined before use (line 46); Confirmed all four background hooks are present and functional (hook-response, session-summary, memory, auto-detect-bugs); Aligned hooks in both workspace/_templates/hooks/log_session_stop.sh and workspace/aicli/_system/hooks/log_session_stop.sh

  PROMPTS P102300 [ ] [bug] [completed] [4] — Improved work items panel header clarity with wider columns, better padding, and visual separation.
    Requirements: Work items UI columns too close together (38px too narrow); Header lacks visual separation and is hard to read; Make header more clear and readable
    Deliveries: Widened columns from 38px to appropriate width; Added proper background styling to header; Increased header padding for better readability; Improved text clarity in column labels

  PROMPTS P102301 [ ] [bug] [in-progress] [3] — Fixed date formatting to yy/mm/dd-hh:mm and removed non-work-item tags (Shared-memory, billing) from
    Requirements: Date format should be yy/mm/dd-hh:mm instead of current format; Tags under work_items (Shared-memory, billing) should not be displayed as they are not work items
    Deliveries: Updated fmtDate function to format dates as yy/mm/dd-hh:mm; Implemented work item deletion functionality via _wiPanelDelete handler; Added delete API call DELETE /work-items/{id}?project={proj}; Implemented confirmation dialog before deletion; Updated _wiPanelItems cache and re-render on successful deletion

  PROMPTS P102307 [ ] [bug] [in-progress] [3] — Fixed work items panel layout to display tags properly and expand description to full row width.
    Requirements: Tags (AI and user) are not visible on work item rows; Description text is truncated in middle of row instead of using full row width
    Deliveries: Updated colgroup to make Name column more flexible; Adjusted date column width to be narrower; Removed table-layout:fixed to allow flexible column sizing; Expanded description to use full available row width; Modified _renderWiPanel to improve tag and text display

  PROMPTS P102308 [ ] [bug] [completed] [4] — Restore table layout and add labeled tag rows (AI/User) with descriptions.
    Requirements: Last column (commits) is invisible; need to restore table-layout:fixed; Add labeled rows to identify tag types: AI, AI(new), and User; User tags must always display, showing '—' if empty
    Deliveries: Restored table-layout:fixed in CSS to prevent Name column expansion; Added labeled rows: AI (always), User (always with '—' fallback); Repositioned description to span full Name column width

  PROMPTS P102341 [ ] [bug] [in-progress] [2] — Fix UI category/bug display issue and work_item disappearance after tag acceptance.
    Requirements: Planner view shows only work_item, missing bug/category; When accepting AI tag, work_item disappears but top screen becomes empty
    Deliveries: Verified backend state with route_entities.py refactoring; Fixed tag session handling in patch_value and session_bulk_tag; Updated _renderWiPanel UI panel rendering (+19/-2)

  PROMPTS P102342 [ ] [bug] [completed] [4] — Fix duplicate const declaration causing Electron empty load.
    Requirements: Electron loads empty on startup
    Deliveries: Identified duplicate const cats declaration in _wiPanelCreateTag function; Renamed second declaration to cacheCats to resolve scope conflict; Cleaned up legacy system context files and database migrations

  PROMPTS P102355 [ ] [bug] [completed] [4] — Fix incomplete prompt loading by merging DB entries with JSONL file data and correct sorting.
    Requirements: On system start, only prompts from certain point visible (not all history); Investigate if loading from _system/session files; clarify reason for many files and why not updated to latest
    Deliveries: Implemented limit=500 to load full history with correct sort (April newest first, March oldest); Merged DB entries (389) with JSONL file data (~142) for total of 531 entries; Fixed entry normalization in _normalize_jsonl_entry; sort now shows March 9 through current date

  PROMPTS P102356 [ ] [bug] [in-progress] [3] — Fix stale session ID loading by resetting module variables and implementing auto-select for current 
    Requirements: Loads with old session ID (7d89c79f-...) instead of current session (f6648726-...); eventually updates after delay; Clarify why many JSON files exist in workspace/aicli/.. session folder
    Deliveries: Reset _sessionId to null at start of renderChat() to clear stale session persistence; Also reset _appliedEntities/_pendingEntities to prevent carryover; Prevented localStorage cache render from highlighting old session (since _sessionId=null initially)

  PROMPTS P102357 [ ] [bug] [completed] [5] — Load current session on startup by synchronously reading last_session_id from runtime state.
    Requirements: On startup, loads old session (7d89c79f-...) for ~15 seconds before switching to current session (f6648726-...); need immediate correct load
    Deliveries: Modified _loadSessions() to immediately read last_session_id from state.currentProject.dev_runtime_state synchronously; Set _sessionId before cache renders, ensuring correct session highlighted on load; Flow: renderChat() clears _sessionId → _loadSessions() sets from runtime state (no network call) → cache renders with correct session → full fetch confirms

  PROMPTS P102143 [ ] [task] [completed] [4] — Provided clean restart procedure using dev script with NODE_ENV=development after killing stale back
    Requirements: Cannot see anything after shutting down Electron and running fresh; No UI display when clicking on project name; Suspected PostgreSQL network connection issue
    Deliveries: Confirmed port 8000 is now free and stale backend (PID 86671) is gone; Provided clean restart command: `cd ui && npm run dev`; Explained the chain of events that caused the bind error and black screen

  PROMPTS P102151 [ ] [task] [completed] [4] — Explained tag bar location and accept workflow; fixed overflow clipping issue.
    Requirements: User cannot find where to click accept in Chat; Looking for accept button at top of chat
    Deliveries: Located tag bar: thin bar at top of chat area below title, above messages; Explained workflow: click ✓ to queue, click 💾 Save to confirm; Fixed overflow:hidden clipping issue to allow tag bar to wrap to second line; Provided visual feedback examples (amber/gold italic chips)

  PROMPTS P102195 [ ] [task] [in-progress] [1] — Investigated project loading performance issues and requested details on slow Summary and History lo
    Requirements: Project not visible in proper order at latest project list; Long load time for Summary and History when opening project; Need explanation of what is happening during load; Pagination was added to History but still takes long
    Deliveries: Initiated sanity check on key changes for correctness

  PROMPTS P102298 [ ] [task] [completed] [4] — Instructed user to perform hard refresh to see UI changes (Cmd+Shift+R or Ctrl+Shift+R).
    Requirements: User does not see UI changes despite backend updates
    Deliveries: Provided hard refresh instructions for browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows/Linux); Alternative reload instruction for Electron window (Cmd+R)

---

## **database-schema-refactor** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 47 prompts
> User tags:
> AI existing:
> AI new: [task:db-schema-refactor]
> Summary: Database schema design, table restructuring, and migration
> Requirements: Update /memory for project management page and workflow improvements; Update all project summary, current features, and ongoing features; Remove unused tables from database; Rename all managed tables to mng_TABLE_NAME for global management tables; Rename client-level tables to cl_TABLE_NAME
> Deliveries: [task|completed|4|15] Completed database migration: removed 5 stale tables, consolidated to 24, applied 18+ migrations with column cleanup and reordering; [feature|completed|4|8] Completed memory event table refactoring: merged embeddings/summaries into mem_ai_events, implemented tagging system with mem_ai_tags_relations; [task|completed|4|3] Completed auto-regeneration of memory files (CLAUDE.md, MEMORY.md) on project facts/work items upsert with new structure documentation; [task|in-progress|2|4] In-progress: implementing 3-layer table hierarchy (mng_/cl_/pr_ prefixes), resolving table categorization, and cleaning obsolete schema references; [bug|in-progress|1|14] In-progress: fixing undefined column errors in routes, restructuring mem_ai_events columns, implementing mng_projects foreign key migration, and tagging enhancements

  PROMPTS P102215 [ ] [feature] [in-progress] [3] — Merged pr_embeddings and pr_memory_events into single mem_ai_events table.
    Requirements: Merge pr_embeddings and pr_memory_events into mem_ai_events table; Include fields: id (uuid), project_id, session_id, session_desc, chunk, content, created_at; Implement smart embedding with chunking mechanism; Support code understanding for commits
    Deliveries: Commit 7ea756e6: chore: update ai context files and memory after cli session; mem_ai_events table schema designed with merged functionality

  PROMPTS P102216 [ ] [feature] [in-progress] [3] — Enhanced memory tagging system with mem_ai_tags_relations and tag management.
    Requirements: Implement mng_ai_tags_relations table for tagging relationships; Review and verify tagging functionality against previous specifications; Implement dictionary-based tag management in memory; Support event-level tagging with session metadata
    Deliveries: Commit 5ec5d26e: feat: enhance memory tagging system and update AI context files; mem_ai_tags_relations table structure verified; Tagging system design documented with event metadata support; Tag dictionary management approach implemented

  PROMPTS P102218 [ ] [feature] [in-progress] [3] — Implemented manual tag relations management via developer CLI commands.
    Requirements: Support manual tag relations declared by developers; Enable relations via CLI command, admin UI, or direct SQL; Support relation types like depends_on, replaces, etc.; Store relations in pr_tag_relations table with from_tag_id, relation, to_tag_id, note
    Deliveries: Commit dd2dc520: chore: update 38 files; Manual tag relations feature architecture documented; INSERT statement example provided for relation management; Developer workflow for declaring relationships specified

  PROMPTS P102246 [ ] [feature] [in-progress] [0] — Implement tagging mechanism with user-editable tags column in work items.
    Requirements: Replace ai_tags with tags [text] column in MRR table; Enable tags to be updated via UI (history → Add tag) or Claude CLI; Support minimum tags (e.g., phase) in CLI prompts; Example: tag this session as 'phase: discovery' and 'memory refactor'

  PROMPTS P102257 [ ] [feature] [in-progress] [1] — Add language tags, improve file_change data structure with file paths and row counts.
    Requirements: Add language as a tag into tags dictionary; If language updated per commit, add tag to mrr table; if at event creation, add to event table; Improve file_change data to include list of files with row changes; Add files tag storing file_name and row changes, populate in mrr or event table based on update timing

  PROMPTS P102264 [ ] [feature] [in-progress] [0] — Create mng_projects table and migrate project references from text to foreign key.
    Requirements: Create mng_projects table with id, name, desc, and project defaults; Replace project (text) columns with project_id foreign keys across all tables; Store project configuration data (local file paths, git connectivity, creation defaults); Support the client-users-projects hierarchy (client → multiple users, client → multiple projects)

  PROMPTS P102217 [ ] [bug] [completed] [4] — Fixed table naming error: mng_ai_tags_relations corrected to mem_ai_tags_relations.
    Requirements: Fix incorrect table name mng_ai_tags_relations; Correct to mem_ai_tags_relations
    Deliveries: Commit dc615099: chore: update ai context files and memory after cli session; Table naming error corrected in schema and documentation

  PROMPTS P102224 [ ] [bug] [completed] [4] — Fix database DDL changes not visible in database; refactor database.py for persistence.
    Requirements: Ensure DDL schema changes are persisted to database; Make database.py changes reflect in actual database
    Deliveries: Commit b6f68047: Updated AI context files and refactored database.py for proper schema application

  PROMPTS P102248 [ ] [bug] [in-progress] [1] — Fix undefined column error (lifecycle) and optimize slow commit loading queries.
    Requirements: Fix psycopg2.errors.UndefinedColumn for t.lifecycle in route_entities line 359; Remove unnecessary PHASE column not in UI or database; Optimize pagination/commit loading queries for performance
    Deliveries: System context and session state updated

  PROMPTS P102249 [ ] [bug] [in-progress] [1] — Fix undefined column error (work_item_id) in work items route query.
    Requirements: Fix psycopg2.errors.UndefinedColumn for p.work_item_id in route_work_items line 351; Ensure work_item_id column exists or query is corrected
    Deliveries: System files and memory updated after session

  PROMPTS P102254 [ ] [bug] [in-progress] [1] — Verify column reordering in mem_ai_events table—llm_source and embedding not updated.
    Requirements: Confirm llm_source column is positioned after project in mem_ai_events; Confirm embedding column is positioned as last column in mem_ai_events
    Deliveries: AI system context and memory files updated after session

  PROMPTS P102139 [ ] [task] [completed] [4] — Updated /memory context files and project documentation for next steps.
    Requirements: Update /memory for project management page and workflow improvements; Update all project summary, current features, and ongoing features
    Deliveries: MEMORY.md updated with LLM synthesis; All context files copied to code_dir; Commit fa868e8c: docs: update AI context files and project documentation

  PROMPTS P102202 [ ] [task] [in-progress] [3] — Restructured database tables with mng_, cl_, pr_ naming convention.
    Requirements: Remove unused tables from database; Rename all managed tables to mng_TABLE_NAME for global management tables; Rename client-level tables to cl_TABLE_NAME; Rename project tables to pr_[Client_name]_[project_name]_TABLE_NAME pattern
    Deliveries: Database schema refactoring plan documented; Table naming convention established (mng_, cl_, pr_ prefixes); Verified work_item_pipeline.py core file

  PROMPTS P102203 [ ] [task] [completed] [4] — Executed database migration removing 5 stale tables, consolidated to 24 tables.
    Requirements: Run database migration command to apply changes; Remove old unused tables from database
    Deliveries: Dropped 5 stale legacy tables: commits, embeddings, events, event_tags, event_links; Consolidated from 29 to 24 tables; Reorganized 19 global mng_ tables with consistent naming; Migration executed and verified

  PROMPTS P102204 [ ] [task] [in-progress] [2] — Clarified table categorization: memory_items and project_facts belong in project tables.
    Requirements: Explain why memory_items and project_facts are categorized under system management; Verify correct table placement
    Deliveries: MEMORY.md updated to reflect final table structure; Verified all endpoints working; Confirmed table categorization

  PROMPTS P102205 [ ] [task] [completed] [4] — Verified mng_session_tags usage and clarified project table structure.
    Requirements: Verify mng_session_tags table purpose and usage; Check session_tags.json file in project workspace
    Deliveries: Confirmed 24 tables in clean split: 14 mng_ and 10 pr_local_aicli_; Listed all tables per category; Documented memory tables: work_items, interactions, interaction_tags, memory_items, project_facts; Updated database.py DDL for memory tables migration

  PROMPTS P102207 [ ] [task] [in-progress] [2] — Implemented 3-layer table structure: mng_ (general), cl_ (client), pr_ (project).
    Requirements: Align client tables with mng_ global prefix; Create 3-layer hierarchy: general management (mng_), per-client (cl_), per-project (pr_); Rename mng_session_tags to cl_local_session_tags for client-specific data; Ensure entity tables are per-client
    Deliveries: 3-layer architecture defined and documented; Client-level table naming established with cl_ prefix; Planning for multi-client support with paid clients

  PROMPTS P102219 [ ] [task] [completed] [4] — Rename project facts and work items tables, add features table with upsert triggers.
    Requirements: Rename pr_project_facts to mem_ai_project_facts; Rename pr_work_items to mem_ai_work_items; Add mem_ai_features table; Implement work item upsert trigger after sprint/milestone with status sync to pr_tag_meta
    Deliveries: Commit 98d3af91: Updated AI system files and memory after claude session

  PROMPTS P102220 [ ] [task] [completed] [4] — Auto-regenerate memory files (CLAUDE.md, MEMORY.md, etc.) based on project facts and work items upse
    Requirements: Auto-regenerate CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md on project_facts upsert; Regenerate feature-specific CLAUDE.md on work_items upsert; Regenerate root CLAUDE.md on pr_session_summaries insert; Regenerate affected CLAUDE.md on pr_tag_relations insert
    Deliveries: Commit 46ec6642: Updated AI context files and memory after CLI session

  PROMPTS P102221 [ ] [task] [completed] [4] — Provide updated aicli_memory structure and document new memory layers and tagging relationships.
    Requirements: Update aicli_memory with revised memory structure; Document new structure layers; Explain relationships to tagging and feature mechanism
    Deliveries: Commit 75a18a27: Updated AI context files and session history with new structure

  PROMPTS P102222 [ ] [task] [completed] [4] — Merge pr_session_summaries into mem_ai_events with event_type column for session summary events.
    Requirements: Merge pr_session_summaries into mem_ai_events; Add event_type column (event_type=session_summary) to distinguish AI events
    Deliveries: Commit ee845bc6: Updated AI system files and memory after claude session

  PROMPTS P102223 [ ] [task] [completed] [4] — Add missing llm_source column to mem_ai_events and audit unused columns like language and file_path.
    Requirements: Add llm_source column to mem_ai_events; Audit and remove unused columns (language, file_path, others) from mem_ai_events
    Deliveries: Commit dad26199: Updated AI workspace files and memory docs post-session with column audit

  PROMPTS P102225 [ ] [task] [completed] [4] — Remove unused columns from mem_ai_events; move summary_tags to mem_ai_tags linked by row ID with AI-
    Requirements: Remove unused columns (language, file_path) from mem_ai_events; Move summary_tags array to mem_ai_tags table as separate rows linked by event row ID; Add column in mem_ai_tags to flag tags suggested by AI vs. sourced from MRR
    Deliveries: Commit da3644d4: Improved memory tagging and routing stability; refactored tags storage

  PROMPTS P102226 [ ] [task] [completed] [4] — Refactor mem_mrr_* tables: remove unused columns, consolidate tags, change commit ID to integer, fix
    Requirements: Remove unused columns from mem_mrr_* tables (session_src_desc, session_src_id, tags[]); Consolidate tag storage; note mem_mrr_prompts now stores tags; Change commit table to use integer ID instead of commit hash; Fix primary and foreign keys across 4 mem_mrr_* tables
    Deliveries: Commit 5f1cda6c: Updated AI context files and refactored mem_mrr_* tables with key and column cleanup

  PROMPTS P102228 [ ] [task] [completed] [4] — Apply same refactoring (remove unused columns, fix keys) to all mem_ai_* tables.
    Requirements: Audit and remove unused columns from all mem_ai_* tables; Fix primary and foreign keys across mem_ai_* tables; Consolidate tag storage consistent with mem_mrr_* refactoring
    Deliveries: Commit 5df58ee0: Updated AI system files and refactored mem_ai_* tables for consistency

  PROMPTS P102230 [ ] [task] [completed] [4] — Reduce database.py file size by removing old migrations and boilerplate code.
    Requirements: Remove old migration code from database.py; Remove boilerplate to reduce file size and improve maintainability
    Deliveries: Commit 56e37c54: Updated aicli workspace state and trimmed database.py boilerplate

  PROMPTS P102236 [ ] [task] [in-progress] [1] — Review database files and remove obsolete tables from codebase.
    Requirements: Review database files for old/unused tables; Remove tables that no longer exist in the schema
    Deliveries: System files and memory updated after session

  PROMPTS P102245 [ ] [task] [in-progress] [1] — Address incomplete table structure cleanup—old tables still present.
    Requirements: Remove old/unused tables from database schema; Ensure table structure reflects current system state
    Deliveries: System state and memory updated after session

  PROMPTS P102252 [ ] [task] [in-progress] [1] — Restructure mem_ai_events table: move llm_source, consolidate tags/metadata, use JSONB.
    Requirements: Move llm_source column to be after project; Identify where and when llm_source is populated; Consolidate tags (from MRR) and metadata (from events) into single column; Merge all MRR tags into event records; Convert list columns to JSONB type for flexibility
    Deliveries: System files and memory updated after session

  PROMPTS P102253 [ ] [task] [in-progress] [0] — Reorder table columns (llm_source after project, embedding at end) and clean database.py.
    Requirements: Move llm_source column to position after project in all tables; Move embedding column to last position in all tables; Update database.py to remove old/unused tables and reduce length

  PROMPTS P102255 [ ] [task] [completed] [4] — Rename mem_ai_events to old, create new table, and migrate data.
    Requirements: Rename existing mem_ai_events table to mem_ai_events_old; Create new mem_ai_events table with updated schema; Insert/migrate data from old table to new table
    Deliveries: System files trimmed and memory updated after session

  PROMPTS P102256 [ ] [task] [in-progress] [1] — Clarify usage of doc_type, language, file_path columns and session_action_item reusability.
    Requirements: Explain purpose and usage of doc_type column; Explain purpose and usage of language column; Explain purpose and usage of file_path column; Assess whether session_action_item can be reused for other sources (items, prompts)
    Deliveries: System state and memory updated after session

  PROMPTS P102258 [ ] [task] [completed] [2] — Investigate chunk and chunk_type fields; consider moving to tags dictionary.
    Requirements: Clarify purpose and usage of chunk and chunk_type columns; Determine if these fields should be moved to tags dictionary in work_items
    Deliveries: System state and memory documentation updated

  PROMPTS P102259 [ ] [task] [in-progress] [2] — Clean invalid historical events, verify llm_source population, update memory table.
    Requirements: Remove invalid historical events from database that don't make sense; Verify llm_source column is properly populated; Run /memory command to update tables
    Deliveries: System state and memory updated after session

  PROMPTS P102265 [ ] [task] [completed] [2] — Verify prompt structure after client_id fix.
    Requirements: Verify and validate prompt structure following client_id schema corrections
    Deliveries: System context and memory documentation updated

  PROMPTS P102272 [ ] [task] [completed] [4] — Audit work_items columns: clarify source_session_id, content, summary, requirements usage.
    Requirements: Clarify purpose of source_session_id in work_items; Document usage of content, summary, requirements columns; Explain how tags merge from mem_ai_events; Align work_items as main table for event aggregation and merging non-closed items; Clarify relationship and comparison between work_items and planned_tags
    Deliveries: Complete column audit of mem_ai_work_items with 20 columns analyzed; Clear purpose documentation for each column with status (Keep/Remove/Merge); System context and memory files updated with analysis

  PROMPTS P102284 [ ] [task] [completed] [4] — Verify diff_summary and diff_details columns in commits table are necessary.
    Requirements: Confirm purpose of diff_summary and diff_details in mem_ai_commits; Determine if both columns should remain or be removed
    Deliveries: Clarified diff_summary stays (git --stat output from route_git.py); Confirmed diff_details removed (never populated, cleaned from schema and code); Documentation updated in aicli_memory.md

  PROMPTS P102285 [ ] [task] [in-progress] [3] — Investigate commit table data capture: verify hook functionality, row change counts, files tag usage
    Requirements: Verify git hook properly captures real file changes (not just internal docs); Clarify how row +/- counts are calculated and ensure relevance; Verify files tag stores file names and row change counts properly; Extract actual code changes per commit
    Deliveries: Identified backfill in progress: ~195 of 391 commits processed; Large commit (238 files) architecture restructure causing processing delay; Multiple memory and system context files updated; Documentation of backfill status provided

  PROMPTS P102286 [ ] [task] [in-progress] [0] — Design extraction flow for aggregating commits linked via pr_tags_map.
    Requirements: Design data extraction flow using pr_tags_map to fetch related commits; Aggregate commit data across multiple related commits (files, features, tests); Show clear example of fetching commits by tag_id and aggregating changes

  PROMPTS P102287 [ ] [task] [completed] [4] — Verify database updates: confirm commit_short_hash and generated columns applied.
    Requirements: Verify commit_short_hash column added to database; Confirm generated column full_symbol properly applied to mem_mrr_commits_code
    Deliveries: commit_short_hash column added to mem_mrr_commits; mem_mrr_commits_code schema updated with 19 columns including full_symbol generated column; Identified and resolved DDL runner issue preventing generated column application; Legacy CLAUDE.md and CONTEXT.md files removed and restructured

  PROMPTS P102293 [ ] [task] [completed] [4] — Created db_schema.sql canonical schema file with all tables, indexes, and FK constraints.
    Requirements: Separate database.py into methods and table schemas; Create db_schema.sql with all table schemas using IF NOT EXISTS; Include remarks, indexes, and foreign keys in schema file; Define migration strategy: rename tables with prefix, create new, insert data
    Deliveries: Created backend/core/db_schema.sql (~350 lines) as single source of truth for schema; Organized schema in sections: mng_* → planner_* → mem_mrr_* → mem_ai_* → pr_*; Included all indexes and FK constraints; Added comprehensive comments explaining table purpose and invariants

  PROMPTS P102344 [ ] [task] [completed] [4] — Implemented table migrations m035-m036 with column reordering and cleanup of old tables.
    Requirements: Retry table migration using specified column order; Drop _old tables after migration to save space
    Deliveries: Created m035_reorder_mem_mrr_commits migration (+80 lines); Created m036_reorder_mem_ai_events migration (+70 lines); Added trim_events endpoint to backend/routers/route_admin.py; Updated _Database._ensure_shared_schema to support new migrations

  PROMPTS P102345 [ ] [task] [completed] [3] — Analyzed importance column usage in events table.
    Requirements: Evaluate whether importance column is needed in events table; Determine if importance is better suited for work_items table
    Deliveries: Code analysis of importance column usage across codebase; Confirmed importance is more relevant for work_items than events

  PROMPTS P102346 [ ] [task] [completed] [5] — Applied migration m037 to drop importance column from mem_ai_events table.
    Requirements: Drop importance column from mem_ai_events table; Update all code references to remove importance usage
    Deliveries: Created m037_drop_events_importance migration (+10 lines); Updated db_schema.sql to remove importance from mem_ai_events; Updated memory_embedding.py: _SQL_UPSERT_EVENT to remove parameter, _parse_haiku_json to return 2-tuple; Updated all event processing methods across 7 files to remove importance handling

  PROMPTS P102348 [ ] [task] [completed] [5] — Applied migrations m037-m047 including column drops, reordering, and system event tracking.
    Requirements: Drop importance from events (m037); Drop embedding from mem_mrr_commits_code (m038); Reorder mem_mrr_prompts columns: after client_id add project_id and event_id; Use standard drop/rename/recreate migration mechanism
    Deliveries: Created m038_drop_commits_code_embedding: freed ~4.5 MB by removing embedding column; Created m039_reorder_mem_mrr_prompts: moved project_id and event_id from end to after client_id (+63 lines); Created m040_backfill_event_cnt_and_tags (+97 lines); Created m041_drop_diff_file_chunks for memory_embedding cleanup; Created m042_drop_source_event_id from memory promotion

  PROMPTS P102358 [ ] [task] [completed] [5] — Created migration m051 to convert user_id from string to int and add updated_at to all tables.
    Requirements: Change user_id from string to int (same as project_id and client_id); Add updated_at column to all mirror tables after created_at; Add user_id after project_id in all mirror tables; updated_at tracks row modifications; created_at is immutable
    Deliveries: Created m051_schema_refactor_user_id_updated_at migration (+359 lines); Converted mng_users.id to SERIAL INT primary key; Preserved old UUID as uuid_id VARCHAR(36) column; Added updated_at to: mng_users, mng_clients, all mem_mrr_* tables, mem_ai_events, mem_ai_project_facts, mem_pipeline_runs, planner_tags; Added user_id INT to all mirror tables and planner_tags after project_id

  PROMPTS P102359 [ ] [task] [completed] [5] — Created migration m052 to reorder all table columns with standard column ordering rules.
    Requirements: Reorder columns: id → client_id → project_id → user_id; Move created_at, updated_at to end of table (before embedding if present); Remove committed_at from mem_mrr_commits (preserve as COALESCE with created_at); Embedding column always last if present; Apply rename-add-migrate-drop pattern for all 18 tables
    Deliveries: Created m052 migration rebuilding 18 tables with correct column order; Ensured id → client_id → project_id → user_id ordering in all tables; Positioned created_at → updated_at → embedding at end of all tables; Removed committed_at from mem_mrr_commits; preserved git timestamp via COALESCE(committed_at, created_at); Moved mem_ai_events.event_system to after event_type column

---

## **memory-layer-implementation** · 26/03/09-17:56 [ ] (claude)
> Type: new
> Total: 62 prompts
> User tags:
> AI existing:
> AI new: [feature:memory-layers]
> Summary: Memory layers, embedding, events, and AI tagging system
> Requirements: Summarize large feature responses in chat history instead of full output; Add AI suggestion tags via /memory function; Clarify UI confusion in History tab (chat, commit, run, workflow management); Consolidate Planner tabs (Feature, Tags, Bugs, Tags) into one tag management interface; Support category-based tag hierarchy with properties (status, description, due date, user created)
> Deliveries: [feature|completed|4|22] Memory layer infrastructure completed with tagging, linking, and database optimization; [feature|completed|4|15] Work items and event system implemented with AI tag suggestions and prompt-to-commit linking; [bug|completed|4|11] Bug fixes across tagging, commits, hooks, and UI rendering for memory operations; [feature|in-progress|2|8] Tag hierarchy redesign, AI suggestion workflow, and category-aware tagging in progress; [task|in-progress|2|6] Memory documentation, schema validation, and roadmap planning for phase 2 refactor

  PROMPTS P102141 [ ] [feature] [in-progress] [2] — User proposes redesigning Planner from 4 tabs to single tag management interface with category hiera
    Requirements: Consolidate Planner tabs (Feature, Tags, Bugs, Tags) into one tag management interface; Support category-based tag hierarchy with properties (status, description, due date, user created); Add tag listbox in chat (+) menu showing active tags with add option

  PROMPTS P102152 [ ] [feature] [completed] [4] — AI suggestions banner added to chat UI, Phase selector clarified, and session context improved.
    Requirements: Make AI suggestions more visible with clear approval mechanism; Clarify which session suggestions apply to; Clarify whether 'Phase' in tag bar is session or mandatory feature
    Deliveries: Phase label in tag bar confirmed as phase selector (not session identifier); AI suggestions moved to dedicated amber banner between tag bar and message area; Banner shows session context (e.g., 'session abc12345…') with dismiss option

  PROMPTS P102153 [ ] [feature] [completed] [4] — Fixed /memory suggestions to work offline, added history router, and enabled session-to-commit linki
    Requirements: Run /memory and show suggestions in existing sessions; Display commit logs in history tab with GitHub links; Show which commits were done in each session
    Deliveries: /memory suggestions now work without PostgreSQL (best-effort with fallback to recent history); History router added (commit d012fcfb implies UI improvements); History tab now displays commit information

  PROMPTS P102159 [ ] [feature] [completed] [4] — Optimized tag loading with caching, persisted tag colors, and unified tag save mechanism for commits
    Requirements: Cache all tags in memory on first load to reduce DB calls; Persist tag color selection when choosing tags; Unify commit tag saving with history tag mechanism; Link automated commits to all related prompts
    Deliveries: Tag cache implementation: `_tagCache` (grouped) and `_tagCacheMap` (flat lookup) loaded once on tab open; Tags loaded in parallel with history, commits, categories in `_renderChat`; Tag color preservation integrated into selection

  PROMPTS P102161 [ ] [feature] [completed] [4] — Added prompt-to-commit linking, showing which specific prompts triggered which commits in sessions.
    Requirements: Create link between commit/push and prompt ID (not just session ID); Support multiple commits per session, each linked to its triggering prompt
    Deliveries: Commit-to-prompt linking established and tested; 5 real sample links verified (d0f14c21, 951768bc, 0336f3e5, 8e37699 linked to specific prompts); Entity CRUD endpoints added (commit 2507af7b)

  PROMPTS P102165 [ ] [feature] [completed] [4] — Deduplicated 149 tags across History/Chat/Commits and added DELETE endpoints for tag removal.
    Requirements: Ensure all tags are aligned with no duplicates across History, Commit, and Chat screens; Add option to remove (×) tags that affects all screens
    Deliveries: Confirmed 149 event tags with 0 duplicates via backend deduplication logic; Implemented `DELETE /entities/events/tag-by-source-id` endpoint to remove tags from history entries and commits; Frontend deduplication before API calls; Commit 7d7445c2: entity routing and history/chat UI view enhancements

  PROMPTS P102167 [ ] [feature] [completed] [4] — Linked commits to specific prompts in History/Chat view using prompt_source_id matching.
    Requirements: Link each commit to the prompt that triggered it (same relationship as prompt→commit); Display commits per prompt in History Chat view
    Deliveries: `/history/commits` endpoint already returns `prompt_source_id` in every commit row; Frontend now shows linked commits inline at bottom of each prompt entry with `⑂ hash ↗` display; Uses `prompt_source_id` to match commits to exact triggering prompt; Commit 6958c335: history system docs update with prompt-commit linking

  PROMPTS P102171 [ ] [feature] [completed] [4] — Auto-save AI suggestions as tags to session with proper category, filter by phase, and remove featur
    Requirements: Save AI suggestions from aiCli memory command properly for the session; Save in proper category and add to Planner as new tags; Fix phase filter/update that stays open without proper stage; Save in one place (Chat) and filter by it in History or Commit; Remove option to update feature column in commit (only update via Chat)
    Deliveries: `_acceptSuggestedTag` made async to immediately save tags via `_saveEntitiesToSession()`; Tags created with proper category via `api.entities.sessionTag()` and added to Planner; Pending entities stored if no session yet, auto-saved on first message; Phase filter issue fixed; Feature column edit removed from commit view (updates only via Chat)

  PROMPTS P102180 [ ] [feature] [completed] [4] — Implemented `GET /entities/summary` endpoint and enhanced `/memory` command to retrieve and synthesi
    Requirements: Verify alignment with 5-step memory process; Identify additional requirements to retrieve details information about the project; Ensure Claude CLI, Cursor, and other tools can retrieve data properly for MCP; Verify `/memory` command uses retrieved data for proper summarization
    Deliveries: New `GET /entities/summary` endpoint returns all non-archived entity values grouped by category with description, status, due_date, event_count, commit_count; `/memory` command enhanced—entity summary loaded before Haiku synthesis and passed to context; Entity data now used in memory summarization for project feature/bug/task management; MCP tools can now retrieve structured project entities

  PROMPTS P102182 [ ] [feature] [in-progress] [0] — User requested adding mng table to track prompt count and notify via aicli when /memory runs.
    Requirements: Add another mng table to check how many prompts exist; Prompt the user in aicli that /memory is running; Run this check on project upload and suggest running memory

  PROMPTS P102190 [ ] [feature] [in-progress] [3] — Designed workflow system comparing specrails and paperclip, proposed role-based architecture with ag
    Requirements: Design workflows similar to specrails (agents/roles like web developer, AWS architect); Review paperclip project for integration potential; Compare with existing YAML-based workflow tab; Plan role-based system instead of simple workflows
    Deliveries: Comprehensive comparison of specrails (Claude Code agent system with 12 specialized roles) vs current system; Analysis of paperclip integration potential; Identified specrails uses prompt files (.md) + slash commands with Claude Code multi-turn; Proposed database-driven agent role system (not visual DAG)

  PROMPTS P102192 [ ] [feature] [completed] [4] — Designed database schema for agent roles with versioning, supporting prompt editing by admins/super-
    Requirements: Store prompts in database rather than as local md files; Allow prompts to be improved over time; Provide only roles to end users; Enable admin/super-user ability to review and change prompts/LLM properties
    Deliveries: Designed agent_roles + agent_role_versions schema for storing role definitions; Implemented per-project ('_global') role system; Created structure supporting system_prompt, model_hints, parameter overrides; Planned version history and role auditing for admin changes

  PROMPTS P102200 [ ] [feature] [completed] [4] — Implemented nested tag hierarchy and mapped tagging to Planner, including inline child tag creation.
    Requirements: Verify all tagging and nested tagging working properly; Ensure tags appear in Planner when added; Support nested tag hierarchy (e.g., Dropbox under UI, Database under Backend); Map prompt/commit tags to proper planning structure
    Deliveries: Renamed tabs: 'Workflow' → 'Pipelines', 'Prompts' → 'Roles'; Added +▸ nested tag button to every regular tag row in entities.js; Implemented inline 'Child of X:' form for creating nested tags; Widened actions column from 44px → 80px for button visibility; Integrated parent_id linking into tag structure

  PROMPTS P102232 [ ] [feature] [in-progress] [2] — User questioned lack of embeddings in project_facts and work_items, requested MCP server update for 
    Requirements: Add embeddings to project_facts table as part of memory layers; Add embeddings to work_items table; Update MCP server to use all memory layers for other LLMs
    Deliveries: Commit d3c9f49e: Updated AI context files and session state after cli session

  PROMPTS P102247 [ ] [feature] [completed] [4] — Implemented tag bidirectional linking and referencing between commits and prompts.
    Requirements: Fix UI error displaying [object object] instead of tag string; Fix backend 422 Unprocessable Entity error on tag operations; Implement bidirectional tag sync: tags added to prompt show on linked commit and vice versa; Add reference mention and jump link in commit showing connection to linked prompt
    Deliveries: Commit 41bdb6bf: system state and session artifacts update with tag linking implementation

  PROMPTS P102252 [ ] [feature] [completed] [4] — Refactored mem_ai_events table schema to consolidate tags/metadata and use JSONB columns.
    Requirements: Move llm_source column to position after project in mem_ai_events; Identify population sources and triggers for mem_ai_events; Consolidate tags and metadata columns (reconcile mrr tags with event metadata); Merge all tags from mrr into event table; Convert all list columns to JSONB type for better data handling
    Deliveries: Commit cf4a7845: mem_ai_events schema refactoring with column reordering and JSONB type conversion

  PROMPTS P102262 [ ] [feature] [in-progress] [1] — Consolidated feature_snapshot into tags, linked work_items to events, and aligned three-layer archit
    Requirements: Merge feature_snapshot with planned_tags and rename appropriately; Link work_items to events storing prompts/session data; Implement three-layer architecture: mirrors → events → working_items; Configure working_items to aggregate events and create session end events; Fix and refactor project_facts layer

  PROMPTS P102291 [ ] [feature] [completed] [4] — Implemented prompt-to-event-to-commit linking and work item event aggregation
    Requirements: Link 5 prompt summaries to events and associate all related commits to that event; Link remaining unlinked commits and new commits to events when triggered; Apply user tags to all linked events or merge AI tags if no user tag exists; Create work_item table to gather and deduplicate events (new vs existing work items)
    Deliveries: Optimistic removal of work items in UI lower panel before API confirmation; Fixed work items query performance by replacing 5 correlated subqueries; Implemented event-to-commit linking logic; Added work_item aggregation from multi-event sources

  PROMPTS P102296 [ ] [feature] [completed] [4] — Implemented FK-based work item to event/commit linking via migrations
    Requirements: Create table/structure linking work_items to all related events (by tags); Connect work_items to all commits of related events (multiple prompts/items/messages); Add mem_ai_work_items_links table with work_item_id, event_id, commit_id, tags, tags_ai
    Deliveries: Designed FK approach: mem_mrr_commits.event_id UUID → mem_ai_events, mem_ai_events.work_item_id UUID; Applied migration m019 dropping mem_ai_work_items_links, adding event_id FK columns; Updated memory_embedding.py MemoryEmbedding.process_commit to set event_id; Updated memory_promotion.py extract_work_items_from_events to link work items to events; Updated route_work_items.py list_work_items query for proper joining

  PROMPTS P102303 [ ] [feature] [completed] [4] — Implemented sticky header and AI tag suggestion approval workflow in UI
    Requirements: Keep header visible when user scrolls down in work_items; Add /memory command to refresh and update events/work_items; Show AI tag suggestions for each work_item with approve/remove actions; Verify recent prompts are reflected as work_items
    Deliveries: Added position:sticky;top:0;z-index:1 to all sortable <th> header cells; Implemented AI tag suggestion row display with ✦ icon format; Added [✓] approve button → PATCH with tag_id to link tag; Added [×] remove button → PATCH with empty ai_tag_id to unlink; Updated _renderWiPanel and hdr functions in entities.js

  PROMPTS P102310 [ ] [feature] [in-progress] [3] — Implemented category-aware AI tag suggestion prioritizing task/bug/feature
    Requirements: Update AI suggestion to suggest one tag from categories (task, bug, feature) first; Also suggest tags under tags (doc_type, phase, etc.) after category attempt; If no match, suggest new task/bug/feature (e.g., Task: summary, phase: discovery); Fix mismatched work_item #20112 (verify-commit-integrity) appearing as suggestion
    Deliveries: Updated _load_all_tags() to JOIN mng_tags_categories and order task/bug/feature first; Modified _claude_judge_candidates() prompt to show [category] tag-name format; Instructed Haiku to prioritize task/bug/feature and include suggested_category field; Processed 103 AI(EXISTS) and 15 AI(NEW) with proper categories; Background matching still running

  PROMPTS P102312 [ ] [feature] [in-progress] [3] — Fixed AI tag suggestion visibility and added event counter to work items
    Requirements: Debug why AI tag suggestions not visible (showing empty AI(EXISTS) instead); Replace 'new work_item' option with refresh button to load latest work_items; Link user tags connected to work_items to all related events; Add event counter column to work_items UI showing linked event count
    Deliveries: Updated _match_new_work_item() in memory_promotion.py with proper matching logic; Added _backlink_tag_to_events() function to propagate user tags to all linked events; Updated PATCH /work_items endpoint to call _backlink_tag_to_events; Modified _renderWiPanel to show event counter between commits and update columns; Updated _loadWiPanel to refresh and update ai_tags on reload

  PROMPTS P102319 [ ] [feature] [completed] [4] — Addressed query performance, DIGEST column confusion, and enabled user approval for AI tags.
    Requirements: Explain why DIGEST column exists and why it's slower; Clarify how work_items without linked prompts are created (e.g., #20428); Enable users to approve or remove AI tags like other tags
    Deliveries: Added NULLS LAST sorting fix to properly order work items; Implemented purple 'AI' tag for AI-generated tags with UI controls; Modified UI to allow users to approve/remove AI tags alongside user tags; Fixed query performance and result ordering

  PROMPTS P102326 [ ] [feature] [completed] [5] — Populated work_item tags from mirror events and enabled code_summary and AI criteria fields.
    Requirements: Explain start_id and code_summary columns; Merge tags from all mirror events into work_item tags; Populate acceptance_criteria_ai and action_item_ai fields
    Deliveries: start_date auto-sets to NOW() when status_user changes to 'in_progress'; code_summary populated by MemoryExtraction.extract_work_item_code_summary() from tagged commits; Created migrations m023 (tags TEXT[] → JSONB) and m024 (backfill tags from source events); Enabled tags merging from mirror events into work_items; Modified MemoryPromotion to populate acceptance_criteria_ai and action_item_ai

  PROMPTS P102163 [ ] [bug] [completed] [4] — Fixed hook noise filtering, corrected task-notification logging errors, added pagination and prompt-
    Requirements: Fix hooks not logging new prompts/LLM responses to history.jsonl; Remove task-notification entries appearing as user prompts; Add pagination display (showing current page / total count); Enable jump from commit to related prompt in history; Replace Feature/Bug/Task columns with tag selection and save
    Deliveries: Hook fixed by filtering noise (task-notification, tool-use-id, task-id, parameter) at write time; Old deployed hook and template updated with `head -c 30` startswith check; Empty prompt filtering added; Commit-to-prompt tracing enabled; Feature/Bug/Task columns replaced with tag selection UI

  PROMPTS P102170 [ ] [bug] [completed] [4] — Fixed git hook to properly link last 9 commits to prompts via session_id and Phase 5 sync.
    Requirements: Last commit b255366 should be linked to the last prompt; Last 9 commits are not linked to any prompts—fix the linking issue
    Deliveries: Root cause identified: `auto_commit_push.sh` hook never triggered Phase 5 DB sync or passed `session_id`; Fixed hook to pass `session_id` to `POST /git/{project}/commit-push` API; Phase 5 now runs after every git push, retroactively linking commits to prompts; Commit 588663e5: git router enhancements and system docs update

  PROMPTS P102178 [ ] [bug] [completed] [4] — Fixed session tag propagation to History/Commits: backfilled phase field and populated commit phase 
    Requirements: Tags saved by session should be linked to all prompts in that session and all commits; History Chat filter by phase returns no results when session is tagged post-facto; Commit phase column is empty—show proper phase the commit is linked to
    Deliveries: `_backfill_session_phase()` now rewrites matching `session_id` entries in history.jsonl with phase when session phase is set; Commits `phase` column now populated—added `session_id` to `commits_aicli` schema retroactively; History filter now correctly retrieves prompts with matching phase; Commit phase column displays proper phase linked to commit

  PROMPTS P102239 [ ] [bug] [completed] [4] — Fixed database column and naming errors in chat history loading routes.
    Requirements: Fix 'event_type' column does not exist error at line 228 in route_history.py; Fix 'log' is not defined error in log.warning statement; Fix 'c.id' column does not exist error at line 1033 in route_entities.py; Resolve Chat history loading failures
    Deliveries: Commit 19cc32ab: backend router fixes addressing column and naming errors

  PROMPTS P102250 [ ] [bug] [completed] [4] — Restored tag attachment functionality and tag selection UI with search and creation.
    Requirements: Fix missing tag persistence on prompts/commits; Fix tag loading failure when attaching new tags; Restore tag selection UI with search and filter by existing tags (category:tag format); Restore ability to create new tags from UI
    Deliveries: Commit 8c84e6af: system context and history state update restoring tag functionality

  PROMPTS P102251 [ ] [bug] [completed] [3] — Fixed commit sync error in /history/commits/sync API batch upsert operation.
    Requirements: Fix execute_values error in cur.execute at route_history line 441 during commit sync
    Deliveries: Commit 0477b67b: documentation and runtime state update addressing commit sync issue

  PROMPTS P102282 [ ] [bug] [completed] [4] — Removed non-existent diff_summary column and fixed commit code extraction logic
    Requirements: Check if diff_details column is necessary in mem_ai_commits; Verify hook properly updates real code files, not just docs; Fix row +/- count data extraction; Ensure tags.files dict properly stores commit code changes
    Deliveries: Removed diff_summary from _SQL_GET_WI_COMMITS (column doesn't exist post-migration 008); Updated memory_planner.py to use tags["files"] dict instead; Removed source_session_id from memory_promotion.py (dropped in migration 012); Applied start_date TIMESTAMPTZ column manually to Railway DB (migration 014)

  PROMPTS P102292 [ ] [bug] [completed] [4] — Fixed missing ai_tags JSONB column in mem_ai_work_items table
    Requirements: Fix work_items endpoint error at line 331 due to missing w.ai_tags column
    Deliveries: Added ai_tags JSONB column to mem_ai_work_items via migration; Registered as work_items_alters_v1 in schema version tracking; Applied ALTER TABLE directly to live DB without restart; Endpoint now returns correctly with ai_tags populated

  PROMPTS P102294 [ ] [bug] [completed] [4] — Fixed tag drawer rendering crash and field name mismatch in UI
    Requirements: Fix missing tag properties display when user clicks a tag (drawer stays blank); Debug why work_items display properties but tags do not
    Deliveries: Fixed catName ReferenceError by using v.category_name || _plannerState.selectedCatName in _renderDrawer(); Corrected field name mismatch: v.short_desc → v.description (line 1412); Resolved scope issue preventing drawer innerHTML from rendering

  PROMPTS P102314 [ ] [bug] [completed] [4] — Fixed over-extraction of internal memory sync work items by adding exclusion rules to prompt.
    Requirements: Explain why internal memory operations (CLAUDE.md updates) were being extracted as separate work items; Reduce duplicate work item #20398 for sync_memory operations
    Deliveries: Root cause identified: work_item_extraction prompt had no exclusion rules for internal AI memory operations; Added NEVER extract block to work_item_extraction.md covering memory/context file updates; Reduced duplicate extraction of internal memory operations

  PROMPTS P102315 [ ] [bug] [completed] [4] — Fixed event counter query to show only digest events and fixed UI column naming.
    Requirements: Share the SQL query used to fetch prompts, commits, and events per work_item; Verify work item #20399 event linking
    Deliveries: Fixed event_count query: filtered to show only prompt_batch and session_summary events (excluding commit chunk events); Reduced event count for work item #20399 from 221 → 10 (accurate digest count); Renamed UI column 'Events' → 'Digests' for clarity; Explained why commits create multiple events in the system

  PROMPTS P102320 [ ] [bug] [completed] [4] — Fixed work item-to-commit linking by correcting source_id join logic in database query.
    Requirements: Make sure work_items are properly connected to events, prompts, and commits; Restore event and prompt counters in UI; Fix work_items with no linked events (e.g., #20431)
    Deliveries: Identified root cause: 418/444 commits had event_id = NULL, breaking commit_ct CTE join; Corrected join logic to use mem_ai_events.source_id (short hash) → mem_mrr_commits.commit_short_hash; Modified route_work_items.py with proper source_id mapping; Restored event counters and prompt linking

  PROMPTS P102327 [ ] [bug] [completed] [4] — Fixed migration to correctly map ai_phase and ai_feature tags from session/commit sources.
    Requirements: Clarify summary column usage; Ensure tags are populated from mirror tables; Handle both session and commit-sourced event tag mappings
    Deliveries: Fixed m024 migration to correctly map ai_phase→phase and ai_feature→feature for commit-sourced events; Completed migrations m021-m024: column renames, work_item_id backfill, tags JSONB conversion, tag backfill; Properly handles one-to-many session event relationship; Tags now merge from source events into work_items

  PROMPTS P102347 [ ] [bug] [completed] [4] — Cleaned up event tags by removing system metadata and backfilling from mirror tables
    Requirements: Show only user tags (phase, feature, bug, source) merged/updated from all mirror tables; Remove old system metadata tags (llm, event, chunk_type, commit_hash, etc.) from events
    Deliveries: Fixed 6 corrupt session_summary events with malformed tags; Stripped system metadata from 1441 events, preserving only {phase, feature, bug, source}; Backfilled 1440 commit events with tags from mem_mrr_commits.tags; Implemented backfill_event_tags function in backend/routers/route_admin.py (+191 lines); Cleaned up legacy system root files across 4 commits

  PROMPTS P102140 [ ] [task] [in-progress] [1] — User requests AI to summarize large feature responses and improve /memory function with tagging sugg
    Requirements: Summarize large feature responses in chat history instead of full output; Add AI suggestion tags via /memory function; Clarify UI confusion in History tab (chat, commit, run, workflow management)

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server usage (not directly used by Claude Code) and improved project context routing.
    Requirements: Explain if/how MCP server is used for project information; Clarify why /memory suggestions don't appear; Show commit count and details in chat footer
    Deliveries: Explained MCP server is separate integration for Claude CLI, not used by this Claude Code session; Identified that API key configuration affects suggestion quality; Improved project routing and chat view (commit 0c3a9cb3)

  PROMPTS P102160 [ ] [task] [completed] [5] — System aligned to CLAUDE.md memory layers, /memory verification run successful, and project features
    Requirements: Run /memory to verify all updates; Check system alignment to CLAUDE.md memory layer specification; Add all newly created features to documentation
    Deliveries: /memory command confirmed working and graph router returning empty workflows; PROJECT.md updated to v2.2.0 with Planner Tab + Entity Tagging Backend features; Goal 9 status changed from In Progress to Implemented; All feature lists synchronized with current implementation

  PROMPTS P102162 [ ] [task] [completed] [5] — Implemented history.jsonl rotation, verified session_tags.json usage, and performed full codebase cl
    Requirements: Check if session_tags.json is used; clean up if unused; Implement history.jsonl rotation (every 500 rows into history_YYMMDDHHSS archive); Review and remove all old/unused code
    Deliveries: History rotation implemented in `_rotate_history()`: configured via `history_max_rows` (default 500); Rotation triggered on every `/memory` call; Verified rotation working (2110 lines → 1610 rows archive in history_2602230915.jsonl); Full codebase cleanup performed

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session tags via Chat, prompt tags via History, commit tags linked to 
    Requirements: Verify tags per session can be added by Chat; Verify tags per prompts can be managed by History/prompts; Confirm commit prompt tags are linked properly
    Deliveries: Confirmed `_load_unified_history` reads current and archived history files; Verified `_removeTag` with × buttons working in frontend; `_propagate_tags_phase4` and `untag_event_by_source_id` confirmed in backend; `_removeAppliedTag` and tag API endpoints verified; Commit 6f3cc130: system state and history updates

  PROMPTS P102168 [ ] [task] [completed] [4] — Updated memory/docs for all sessions and explained MCP accessibility for new CLI/LLM sessions.
    Requirements: Run /memory to update all summaries, DB tagging, and new changes; Explain how new Claude CLI or other LLM sessions can use MCP to receive memory fast and clean; Explain if new session will have same understanding as current session
    Deliveries: Ran `/memory` command—generated 5 context files: CLAUDE.md, MEMORY.md, aicli.mdrules, copilot-instructions.md, rules.md; Explained MCP memory access mechanism via updated context files; New sessions inherit understanding through auto-loaded CLAUDE.md and MEMORY.md; Commit 523f5fd0: AI context files updated after session

  PROMPTS P102179 [ ] [task] [completed] [4] — Optimized database schema with real columns, indexes, and improved tag/phase retrieval for MCP effic
    Requirements: Ensure all tagging is linked, mapped properly in database schema; Verify tagging is used properly for data retrieval via MCP tool; Confirm DB structure and saving mechanism is optimal for memory management
    Deliveries: Added `phase`, `feature`, `session_id` as real columns to `events_{project}` table (not just JSONB); Added indexes: `idx_{e}_session` and `idx_{e}_phase` for fast filtered queries; Separated migrations into per-statement try/except blocks for robustness; `_do_sync` in `routers/entities.py` properly syncs event tags with phase propagation; All schema changes verified and working

  PROMPTS P102181 [ ] [task] [in-progress] [4] — Provided prioritized roadmap for full memory and project management lifecycle with quick wins and lo
    Requirements: Identify additional improvements for full memory management; Provide roadmap for complete project management lifecycle
    Deliveries: Prioritized roadmap with quick wins: `create_entity` MCP tool (Claude CLI/Cursor can create features/bugs/tasks), enhanced entity retrieval, audit trail fields; Medium-term improvements: status transitions (e.g., discovery→backlog→in-progress), due date alerts, relationship tracking between entities; Long-term: dashboard/burndown charts, automated entity linking via code patterns, notification system; Clear implementation guidance for each item

  PROMPTS P102185 [ ] [task] [in-progress] [3] — Audited tag usage, fixed gaps in interaction_tags pipeline and session_bulk_tag function.
    Requirements: Check if tags are well used across the system; Verify memory is improved by new summarisation process; Assess if MCP can be improved for answering and storing project data; Determine if better workflows can be created
    Deliveries: Identified two gaps in tag system: session_bulk_tag() only wrote to event_tags_{project}; Fixed session_bulk_tag() to write interaction_tags rows for matching work items; Confirmed event_tags_{project} system is fully wired across chat, history sync, and tag-by-source-id UI

  PROMPTS P102186 [ ] [task] [completed] [4] — Provided comprehensive summary of 7-part system improvements including memory stack, distillation la
    Requirements: Summarise all improvements made to the system; Assess if system performance improves; Evaluate if memory works better; Determine if MCP can provide more accurate answers for work item management; Assess if workflows can be created based on new items and deliver projects faster
    Deliveries: Described before/after comparison: 40 raw JSONL entries → two distillation layers; Documented 4-agent pipeline for work items; Explained MCP now actively manages project (not read-only); Detailed how memory stack improves LLM context and project understanding

  PROMPTS P102206 [ ] [task] [completed] [4] — Eliminated all mng_graph_* references, refactored to use dynamic project_table() calls across 4 file
    Requirements: Clean up mng_graph_* references from codebase; Clarify how graph tables are used in app; Determine if graph management should be server-side, not client-level
    Deliveries: Removed all mng_graph_* table references from routers/graph_workflows.py (12 endpoints updated); Updated core/graph_runner.py to use dynamic db.project_table() calls; Refactored routers/work_items.py with tbl_g* variables in pipeline execution; Clarified graph table management is server-side (not client-level)

  PROMPTS P102214 [ ] [task] [in-progress] [2] — User requested review of system state before phase 2 refactor; commit made with AI context and sessi
    Requirements: Assess if current state makes sense before proceeding to embedding logic refactor (phase 2); Recommend any final adjustments or cleanup needed
    Deliveries: Commit cad8c096: Updated AI context files and session history logs

  PROMPTS P102233 [ ] [task] [in-progress] [2] — User requested comparison of current memory config vs previous version to assess improvement in proj
    Requirements: Compare current memory config to previous version (reference aiCli_memory.md); Assess if memory layers are improved; Evaluate if LLMs can better understand project structure; Determine if feature/bug mapping to project structure is better; Assess if workflows have better information for success
    Deliveries: Commit d2c4222a: Updated AI context files and session memory logs

  PROMPTS P102260 [ ] [task] [in-progress] [0] — Mark 'llm_source' tag as visible in UI.
    Requirements: Make 'llm_source' tag visible in UI display

  PROMPTS P102261 [ ] [task] [in-progress] [0] — Create comprehensive memory layer documentation describing all layers and data flow.
    Requirements: Build aicli_memory.md documentation from scratch; Describe all memory layers (mirror, event, working_items, project_facts); Explain mirroring layer operation and event handling mechanisms; Document triggers for each step in the pipeline; Document prompts used at each stage

  PROMPTS P102271 [ ] [task] [in-progress] [3] — Updated memory documentation and assessed need for session memory layer in infrastructure.
    Requirements: Update aicli_memory.md to reflect current table structure; Evaluate necessity of mem_session.py for session memory layer; Review all memory layer architecture and advise on updates needed; Align memory layer to track work_items and project_facts; Address feature request/bug tracking aspects
    Deliveries: Commit 581e4039: updated system context and memory files with architectural review

  PROMPTS P102278 [ ] [task] [completed] [5] — Synced and updated all memory files with incremental data from 211 history rows.
    Requirements: Run /memory endpoint to update all memory_items with current data
    Deliveries: Generated MEMORY.md, CLAUDE.md, rules.md, context.md, and copilot.md files; Copied files to code root for distribution; Synced from 211 incremental history rows as of 2026-04-07T01:11:00Z; Identified suggested tags from session; Commit aeefbb0f: system context and memory files update

  PROMPTS P102289 [ ] [task] [completed] [4] — Traced and documented full commit pipeline showing prompt usage locations
    Requirements: Explain where prompts are used for updating new commits; Show full commit pipeline for prompts
    Deliveries: Identified PromptLoader class and PromptConfig in backend/core/prompt_loader.py; Traced commit processing through memory_embedding.py with diff stat counting; Showed prompt usage in route_chat.py (_backfill_session_tags, patch_session_tags); Documented git operations in route_git.py (commit_and_push)

  PROMPTS P102295 [ ] [task] [completed] [4] — Assessed cost and completeness of mem_mrr_commits_code population
    Requirements: Verify if mem_mrr_commits_code should be populated on every commit; Assess cost of per-class/method population
    Deliveries: Cost breakdown: Tree-sitter ~1ms, git show ~20ms, Haiku ~$0.0003, embedding ~$0.0001 per symbol; Typical commit cost: ~$0.004 max (20 commits/day = ~$0.08/day); Provided two cost-reduction knobs: raise min_lines in project.yaml config; Confirmed population is cheap and feasible

  PROMPTS P102313 [ ] [task] [completed] [4] — Located and documented all prompts for ai_tags and work_item extraction across memory system.
    Requirements: Find locations of all prompts used for ai_tags and work_item operations
    Deliveries: Provided comprehensive mapping table showing prompt files (work_item_extraction.md, work_item_promotion.md) and their usage; Identified ai tag matching logic hardcoded in memory_tagging.py:380; Documented which functions use each prompt (MemoryEmbedding.extract_work_items_from_events, MemoryPromotion.promote_work_item)

  PROMPTS P102321 [ ] [task] [completed] [4] — Explained why commit-sourced work items have no linked prompts and ran memory update.
    Requirements: Clarify why work_items exist without linked prompts (e.g., #20442); Update all work_items using /memory endpoint
    Deliveries: Extracted new work item #20443 via memory run; Documented that items #20436-#20443 are commit-sourced (src=commit, sess=None) from 2026-04-07 backfill; Explained that prompts=0 is correct for historical commits with no associated CLI session; Provided source/session/prompts/commits distribution table

  PROMPTS P102328 [ ] [task] [completed] [4] — Clarified distinction between ai_desc (extracted) and summary (generated by promotion).
    Requirements: Explain what summary column is used for; Distinguish from ai_desc field
    Deliveries: summary: human-readable 2-4 sentence status update generated on-demand by promote_work_item() LLM call; ai_desc: extracted at creation time from session digest, 1-2 sentence explanation of work item; Clarified that summary is a manual/generated field while ai_desc is automatic/extraction-time

  PROMPTS P102343 [ ] [task] [in-progress] [1] — Structured events table schema redesign and clarified source_id linking for multi-event items.
    Requirements: Reorganize events table columns: move project_id after client_id, move created_at/processed_at/embedding to end; Clarify source_id population and how it links multiple prompts to one work item; Evaluate action_item column usage; consider consolidating commits as group rather than per-event

  PROMPTS P102352 [ ] [task] [in-progress] [0] — User asked to verify hook-log functionality after m050 migration
    Requirements: Verify hook-log is working correctly after m050 changes

---

## **performance-optimization** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 11 prompts
> User tags:
> AI existing:
> AI new: [task:perf-optimization]
> Summary: SQL query optimization, database performance, and code cleanup
> Requirements: Reduce multiple database calls by loading data once on project access; Cache tags in memory for chat and tag tab usage; Implement smart dropdown with category filter and add new value option; Update memory and database in background on save; Optimize SQL queries (load once at project load, save on update)
> Deliveries: [feature|completed|4|2] Optimized database performance with caching, indexes, and query documentation; [bug|completed|4|3] Fixed critical bugs in database schema, backend startup, and nested work item rendering; [task|completed|4|2] Cleaned up codebase by removing hardcoded values and consolidating configuration; [task|completed|4|2] Designed nested tags architecture with unlimited depth and explained pipeline integration; [task|in-progress|1|2] Investigated performance, memory optimization, and UI issues requiring resolution

  PROMPTS P102144 [ ] [feature] [completed] [4] — Optimized database calls by caching tags in memory and implementing smart category-value dropdown wi
    Requirements: Reduce multiple database calls by loading data once on project access; Cache tags in memory for chat and tag tab usage; Implement smart dropdown with category filter and add new value option; Update memory and database in background on save
    Deliveries: New picker flow in chat.js: _pickerPopulateCats() reads from cache (zero DB calls); Category select populated with counts (e.g., '⬡ feature (5)'); _pickerCatChange() enables text input and renders dropdown with active values; _pickerValFilter() filters dropdown live with '+ Add' option for new values; Commit 8d851bf: implemented changes to chat.js

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed nested work item rendering inconsistency across categories and clarified lifecycle and pipelin
    Requirements: Fix nested work partial display (works in doc_type, broken in bug/feature UI); Explain lifecycle project usage and relevance; Clarify hardcoded pipeline purpose and effectiveness
    Deliveries: Fixed Planner consistency: removed split between entity_values and work_items; Now ALL categories use same _renderTagTable renderer reading from entity_values; Nesting works identically for feature/bug/task as doc_type; Tags created via Chat session tagging immediately appear in Planner; Child button (+▸) works same across all types

  PROMPTS P102210 [ ] [bug] [completed] [4] — Fixed database schema errors, missing project loading, and removed duplicate tables.
    Requirements: Fix '_Database' object missing 'ensure_project_schema' attribute error; Resolve AiCli project not appearing (except in Recent); Fix project loading failure; Clean up duplicate database tables
    Deliveries: Removed stale db.ensure_project_schema() call from main.py; Fixed database.py: rewrote DDL execution statement-by-statement; Added missing ALTER TABLE mng_session_tags ADD COLUMN client_id; Added missing ALTER TABLE mng_entity_values columns; Cleaned up duplicate table definitions

  PROMPTS P102211 [ ] [bug] [completed] [3] — Fixed backend startup failures, memory endpoint code_dir variable error, and project selection displ
    Requirements: Fix backend failing on first load (succeeds after retry); Fix memory endpoint line 1120 code_dir undefined error; Fix aicli not shown as current project
    Deliveries: Memory endpoint fixed and working; Fixed first load backend failures; Resolved aicli current project display; 2 commits: 2a160dd7, 8fda25cc

  PROMPTS P102241 [ ] [bug] [in-progress] [1] — No response provided to drag-and-drop and counter visibility issues.
    Requirements: Fix drag and drop functionality not working; Fix counter not showing changes
    Deliveries: Commit 6ea736e5: update ai workspace state and trim MEMORY.md

  PROMPTS P102145 [ ] [task] [completed] [4] — Designed nested tags architecture with unlimited depth using parent_id and answered feasibility befo
    Requirements: Optimize SQL queries (load once at project load, save on update); Add option to create nested tags beyond current 2-level hierarchy; Ensure full path displays in chat tab with only last level editable; Verify feasibility before development
    Deliveries: Feasibility answer: Yes, nested tags are absolutely feasible; Database design: ALTER TABLE entity_values ADD COLUMN parent_id INTEGER REFERENCES entity_values(id); Supports unlimited depth: category → tag → subtag → sub-subtag; Tree view design for Planner tab with all properties at every level; Commit 28fda59b: documented design decisions in CLAUDE.md

  PROMPTS P102183 [ ] [task] [completed] [4] — Cleaned up codebase by removing hardcoded values, moving config to dedicated config file, and optimi
    Requirements: Check each file for unused code and unnecessary methods; Move hardcoded strings (e.g., backend URL, model names) to config file; Ensure all properties managed through config file for environment flexibility; Verify database and JSON file structure
    Deliveries: Added haiku_model config: 'claude-haiku-4-5-20251001'; Added backend_url config: 'http://localhost:8000'; Added db_pool_max config: 10; Fixed CORS allow_origins to respect cors_origins setting in main.py; Cleaned up hardcoded values across 6+ files

  PROMPTS P102184 [ ] [task] [in-progress] [0] — No response provided to restructure memory capabilities with compressed layers.
    Requirements: Research and implement memory_items table for compressed summaries of prompt/response groups; Address gap between raw JSONL history (too much) and CLAUDE.md (too little); Follow trycycle and specrails architecture patterns

  PROMPTS P102191 [ ] [task] [completed] [4] — Explained hardcoded pipeline in work_item_pipeline.py and identified path to merge with workflow eng
    Requirements: Locate pipeline configuration in Planner tab; Explain parent-child support disappearance; Link pipeline runner to workflow engine; Explore renaming workflow engine to pipelines
    Deliveries: Identified pipeline config in ui/backend/core/work_item_pipeline.py (completely hardcoded); Explained 4-stage pipeline: PM → Architect → Developer → Reviewer (Python-coded, Anthropic API); Located ▶ Pipeline button trigger: POST /work-items/{id}; Clarified pipeline is parallel isolated implementation, separate from graph workflow engine

  PROMPTS P102318 [ ] [task] [completed] [4] — Optimized Planner and work items loading with 5 composite database indexes and followed query docume
    Requirements: Optimize slow Planner tab and work items loading; Verify query optimization (not being added at top of each file class); Follow role to document queries at top of each file class
    Deliveries: Migration m020: 5 new composite indexes in db_migrations.py; idx_mae_project_session on mem_ai_events(project_id, session_id); idx_mae_project_etype on mem_ai_events(project_id, event_type); idx_mmrrc_project_session on mem_mrr_commits(project_id, session_id); Cleaned up route_entities.py (removed 3 unused POST bodies, simplified methods)

  PROMPTS P102319 [ ] [task] [in-progress] [2] — Addressed query performance, DIGEST column purpose, orphaned work items, and AI tag permissions.
    Requirements: Explain why query takes longer and what DIGEST column represents; Clarify how work items without linked prompts/commits/events are created (e.g. #20428); Explain why users cannot approve or remove the AI purple tag
    Deliveries: Implemented NULLS LAST fix in backend query to improve performance; Modified get_unlinked_work_items() endpoint to surface orphaned work items; Updated UI rendering in _renderWiPanel and _renderWorkItemTable to display AI tag; Backend cleanup: removed stale auto-generated context and CLAUDE.md files

---

## **planner-tagging-workflow** · 26/03/10-01:14 [ ] (claude)
> Type: new
> Total: 49 prompts
> User tags:
> AI existing:
> AI new: [feature:planner-workflow]
> Summary: Planner UI, tagging system, and workflow pipeline
> Requirements: User asked for clarification on tag creation behavior in chat picker vs Planner; User confirmed completion of parent-child tag relationship implementation; User reported app restart failures with 'address already in use' error on 127.0.0.1:8000; Tags disappear when switching sessions (possible UI or persistence bug); Request to verify /memory functionality
> Deliveries: [feature|completed|5|5] Hierarchical tagging system with nested tag support (parent_id) fully implemented in database, frontend, and UI; [feature|completed|4|12] Work item planner UI complete: pagination, drag-drop nesting, tag suggestions, persistent linking, and category organization; [feature|completed|4|8] Tag persistence and session-level tracking with /tag command, work item association, and AI tag acceptance workflow; [task|completed|4|6] Database schema cleanup: planner_tags migration removing redundant columns, added creator/updater tracking and deliveries taxonomy; [feature|in-progress|2|6] Session management, memory updates, and feature snapshot table for use-case delivery tracking in progress

  PROMPTS P102147 [ ] [feature] [completed] [5] — Confirmed hierarchical tag support (parent_id) implemented in database and frontend cache helpers.
    Requirements: User confirmed completion of parent-child tag relationship implementation
    Deliveries: Backend: Added parent_id column to entity_values with foreign key reference; Backend: Integrated parent_id into ValueCreate, ValuePatch, SELECT, INSERT, PATCH handlers; Frontend: New tagCache.js helpers (getCacheRoots, getCacheChildren) with zero extra DB calls

  PROMPTS P102158 [ ] [feature] [in-progress] [3] — Implemented tag-by-source-id endpoint to link history entries to entity tags for /memory updates.
    Requirements: Concern about commit/hash linking to prompts and LLM answers; Need to use /memory to update summarized and embedded data; Confusion between History (summary + prompt) and Chat (all responses) display; Desire to store full history (prompts + LLM answers) while Chat shows short responses
    Deliveries: Backend: POST /entities/events/tag-by-source-id endpoint accepting source_id (history.jsonl timestamp); Backend: Automatic event creation from history.jsonl if not found in database; Backend: Idempotent tagging safe for multiple calls; Frontend: api.entities.tagBySourceId() added to api.js

  PROMPTS P102164 [ ] [feature] [completed] [5] — Implemented pagination (◀ [page] / total ▶) for Chat, History, and Commits tabs.
    Requirements: Add pagination UI to Chat showing < > 24/xxx on top right near filter tab; Apply same pagination to Chats and Commits tabs; Support loading multiple history archive files
    Deliveries: Backend: _load_unified_history() now reads history.jsonl + all history_*.jsonl archives; Backend: Results increased from 26 to 204 entries with proper deduplication and noise filtering; Frontend: Pagination UI always visible with disabled/grayed arrows at boundaries; Frontend: Format: ◀ [start–end] / [total] ▶ displayed on all three tabs; Data range expanded from 2026-02-23 to 2026-03-15 covering all archives

  PROMPTS P102169 [ ] [feature] [completed] [4] — Fixed MCP config for current project and created automated MCP setup for new projects with IDE suppo
    Requirements: Set up MCP config for current project; Add automated MCP setup when creating new projects; Support IDE configs: Claude CLI, Claude Code, Cursor, OpenAI, DeepSeek, Gemini, Grok; Ensure non-Cursor/Code IDEs can understand config from aicli API
    Deliveries: Fixed .mcp.json path typo (/user/ /gdrive → /user/Documents/gdrive); Unified .cursor/mcp.json format to args-based matching .mcp.json (not env-based); Both configs now point to ui/mcp_server.py --project aicli --backend http://localhost:8000; Created automated MCP setup flow for new projects supporting all 7 IDE types; Ensured API-based IDEs (OpenAI, DeepSeek, Gemini, Grok) receive config via aicli

  PROMPTS P102200 [ ] [feature] [in-progress] [4] — Documented tagging mechanism with nested hierarchy and planner integration plan.
    Requirements: Implement tagging mechanism to map prompt/commit to proper tags; Support nested tag hierarchy (e.g., Dropbox under UI, Database under Backend); Verify tags appear in Planner after approval; Test nested tagging functionality end-to-end
    Deliveries: Tab renames in main.js: 'Workflow' → 'Pipelines', 'Prompts' → 'Roles'; Added +▸ button in every regular tag row for creating child tags; Widened actions column header from 44px to 80px; Implemented inline 'Child of X:' form for nested tag creation; Added parent_id support to work items for hierarchy

  PROMPTS P102240 [ ] [feature] [in-progress] [2] — Addressed Planner issues: lifecycle tags, bug counter, drag-drop nesting, and ai_suggestion placemen
    Requirements: Clarify purpose of Lifecycle tagging; Update bug counter next to bug tab; Move AI-suggested bugs to ai_suggestion section with proper tag; Implement drag-drop functionality to create nested parent-child relationships; Implement drag-drop to merge two tags
    Deliveries: System documentation updated (commit fc265cbe)

  PROMPTS P102244 [ ] [feature] [in-progress] [3] — Reorganized AI suggestions into separate section and enhanced drag-drop tag nesting.
    Requirements: Move AI-suggested bugs from bug category to separate ai_suggestion section; Prevent user tag creation in ai_suggestion area; Create main AI-suggested categories (bug, feature, etc.); Implement drag-drop to create parent-child tag relationships; Determine complexity of drag-drop for tag nesting
    Deliveries: Tag routing and entities view enhancement (commit 61db51e1); API updates implemented for tag routing; Memory and AI rules documentation updated (commit 0a280e50, aed5228f)

  PROMPTS P102274 [ ] [feature] [in-progress] [2] — System documentation updated; drag-drop work item movement and panel resizing addressed.
    Requirements: Implement drag-drop to move work items from lower screen to upper screen under target item; Implement resizable separator between top and bottom panels for height adjustment
    Deliveries: System documentation and memory updated (commit 36dfee39)

  PROMPTS P102277 [ ] [feature] [completed] [4] — Implemented work_item move/merge functionality with tag cleanup and side panel UI.
    Requirements: Move work_items back to work_items or other items; Add merge functionality for work_items only (in side tab, like TAG merge); Show only work_items under current parent in merge list; Remove merge option from tags/items
    Deliveries: Modified _loadTagLinkedWorkItems to clear all .wi-sub-row elements before re-injection; Updated _wiPanelDrop to use _loadTagLinkedWorkItems for faster item removal; Removed merge functionality from bottom panel items (_renderWiPanel)

  PROMPTS P102297 [ ] [feature] [in-progress] [2] — Added multi-column work_item table with name, desc, prompts, commits, date and sorting.
    Requirements: Display work_items in rows with name and desc columns; Add prompts column showing total prompts count; Add commits column showing total commits count; Add date column with last update (yymmddhhmm format); Enable sorting by prompts, commits, or date
    Deliveries: Sanity check on draggable attribute for _attachWorkItemDnd compatibility

  PROMPTS P102303 [ ] [feature] [completed] [4] — Made header sticky, added AI tag suggestions with approve/remove, and prepared memory update.
    Requirements: Keep header visible when user scrolls down in work_items; Add /memory endpoint to update events and work_items; Verify last prompts are reflected as work_items; Show AI tag suggestions for each work_item in UI; Add ability to approve/remove suggested tags
    Deliveries: Added position:sticky;top:0;z-index:1 to all 3 sortable <th> cells in hdr(); Implemented suggestion row showing ✦ tag_name with [✓] approve and [×] remove buttons; Approve button calls PATCH to link tag to item; Remove button calls PATCH to clear ai_tag_id

  PROMPTS P102306 [ ] [feature] [completed] [4] — Implemented category:name AI tags (bug/feature/task), user tags display, and new tag suggestions wit
    Requirements: AI tags should use format category:name (e.g., bug:auth, feature:dropbox) at lowest level; Show tag suggestions from existing tags, show new tags with different color if no match; Display user tags derived from merged events connected to work_items; Add rectangular shape for × button like ✓ button
    Deliveries: Modified get_unlinked_work_items to return category:name format; Updated _renderWiPanel to show category:name AI tag suggestions; Added user tags display as informational pills; Styled × button with rectangular shape matching ✓ button

  PROMPTS P102310 [ ] [feature] [completed] [4] — Implemented hierarchical AI tag suggestion prioritizing task/bug/feature, then suggesting new catego
    Requirements: AI suggestion should suggest one tag from task/bug/feature categories first; If no match in task/bug/feature, suggest tags from other categories (doc_type, phase, etc.); If still no match, suggest new task/bug/feature; Verify work_items reflect current session context (UI improvements, AI tags) not unrelated items
    Deliveries: Modified _load_all_tags() to JOIN mng_tags_categories and order task/bug/feature first; Updated _claude_judge_candidates() prompt to show [category] tag-name format; Implemented hierarchical matching: existing task/bug/feature → other categories → suggest new category; Result: 103 AI(EXISTS) tags matched, 15 AI(NEW) suggested

  PROMPTS P102332 [ ] [feature] [completed] [4] — Applied migration to clean planner_tags table with creator/updater fields and reordered columns.
    Requirements: Creator must have value (username if user-created, 'ai' if AI-created); Add updater field to track who last modified the row; Reorder columns: project_id after client_id, timestamps (create, created_at, updated, updated_at) as last columns
    Deliveries: Created migration m026_planner_tags_cleanup with column reordering; Added creator and updater fields with proper constraints; Updated memory_files.py to work with new schema; Verified API returns correct new structure

  PROMPTS P102334 [ ] [feature] [completed] [5] — Applied m027 migration removing AI-generated columns from planner_tags table.
    Requirements: Remove summary, design, embedding, extra columns from planner_tags
    Deliveries: Migration m027_planner_tags_drop_ai_cols applied successfully; Updated memory_files.py render_feature_claude_md removing summary and design references; Cleaned up memory_planner.py and memory_promotion.py to remove AI column dependencies; Verified API response shows only clean columns: name, status, description, creator, requirements, action_items, updater

  PROMPTS P102335 [ ] [feature] [in-progress] [1] — Planning to add deliveries column to planner_tags with category/type taxonomy from mng_deliveries ta
    Requirements: Add deliveries JSONB column after action_items; Deliveries updated by user input (list selection); Support multiple delivery types: code (python, js, c#...), document (md, doc...), architect design (visio...), ppt; Create static mng_deliveries table to store delivery categories and types; User should select from predefined categories

  PROMPTS P102337 [ ] [feature] [in-progress] [2] — Design specification for mem_ai_feature_snapshot table with use cases and delivery types.
    Requirements: Create final stage table mem_ai_feature_snapshot that merges user requirements/tags and work items; Include summary, use cases, types (bug/feature/task), and delivery types (code, design docs, AWS architecture, marketing presentations); Map each use case to delivery types from planned_tags
    Deliveries: Design specification for mem_ai_feature_snapshot table structure with requirements

  PROMPTS P102338 [ ] [feature] [completed] [4] — Implemented feature_snapshot table with migration, schema, and Haiku prompt for use-case generation.
    Requirements: Store complete project history using all layers with strong MCP support; Enable deployment and code management with event-to-work-item and user-requirement mapping; Create feature snapshot as input for developer/tester/reviewer workflows and additional workflows for design/cloud maintenance
    Deliveries: Added m029_feature_snapshot() migration function; Created mem_ai_feature_snapshot table with 3 indexes in db_schema.sql; Created feature_snapshot_v2.md Haiku prompt for use-case generation and delivery mapping; Updated prompts.yaml with feature_snapshot_v2 prompt definition; Cleaned up stale agent context files

  PROMPTS P102340 [ ] [feature] [in-progress] [1] — Implementation request for dashboard tab and pipeline execution from multiple entry points.
    Requirements: Create dashboard as a new tab in UI; Enable pipeline execution from planner, docs (where features exist), or directly from chat

  PROMPTS P102353 [ ] [feature] [completed] [4] — Enhanced chat history view with session sidebar, full session IDs, timestamps (YY/MM/DD-HH:MM), and 
    Requirements: Add session visibility in chat tab similar to history tab (left sidebar per session); Add YY/MM/DD-HH:MM timestamps to history prompts (YOU messages); Add all tags display and ability to add tags in history; Show last 5 digits of session ID in left sidebar, full session_id at top when user enters
    Deliveries: Left sidebar now displays session items with source badge, phase chip, and last 5 chars of session ID (monospace); Added full session ID tooltip on hover of session items; Right panel sticky banner shows full session UUID with phase chip; Implemented YY/MM/DD-HH:MM timestamp display for user messages (YOU); Added tag display and management to history view

  PROMPTS P102149 [ ] [bug] [completed] [5] — Fixed port binding restart issue by implementing freePort() to kill orphan uvicorn processes.
    Requirements: User reported app restart failures with 'address already in use' error on 127.0.0.1:8000
    Deliveries: Implemented freePort() function to check and kill process holding the port via lsof; Added 2-second wait for OS to confirm port is free; Ensured freePort() runs on every app start to handle orphaned uvicorn processes

  PROMPTS P102150 [ ] [bug] [in-progress] [3] — Added session-level tag persistence and GET endpoint to retrieve tagged entities per session.
    Requirements: Tags disappear when switching sessions (possible UI or persistence bug); Request to verify /memory functionality; Ensure tags are stored across all session data; Explanation of how sessions work in the CLI
    Deliveries: Backend: New GET /entities/session-tags endpoint to query event_tags joined to events and values; Frontend: Added getEntitySessionTags(sessionId, project) to api.entities; Frontend: Integrated _restoreTagBar in chat.js _chatLoad to restore tags after session switch; Confirmed syntax is correct with no errors

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed Planner inconsistency by unifying tag renderers across all categories.
    Requirements: Fix nested work items display inconsistency between doc_type and bug/feature tabs; Explain lifecycle project purpose and relevance; Explain hardcoded pipeline purpose
    Deliveries: Removed split between entity_values and work_items renderers; All categories now use same _renderTagTable renderer from entity_values; Nested tags work identically across feature/bug/task categories; Tags created via Chat session tagging now appear immediately in Planner; +▸ child button works consistently across all categories

  PROMPTS P102275 [ ] [bug] [in-progress] [0] — Multiple drag-drop and work item management issues identified: hover highlighting, persistence, deta
    Requirements: Fix hover highlighting showing all hovered tabs instead of just target tag; Fix work item link not persisting without page refresh; Enable work item details view when item is nested under tag; Implement work item merge with new merged row and rollback capability via merge_id column

  PROMPTS P102276 [ ] [bug] [completed] [4] — Fixed work item link persistence bug in tag view by removing category filter.
    Requirements: Fix work items not appearing under dropped tag after drag-drop operation; Ensure persistence across page navigation
    Deliveries: Root cause identified: _loadTagLinkedWorkItems filtered by tag's category instead of all project items; Fixed api.workItems.list to fetch all work items without category filter; Work items now correctly appear under linked tag regardless of category mismatch; System context files updated (commit cc038181)

  PROMPTS P102302 [ ] [bug] [completed] [4] — Completed missing delete handler for work_item rows in bottom panel.
    Requirements: Wire up missing _wiPanelDelete handler function for × dismiss button; Fix JS error from clicking × button without handler
    Deliveries: Defined window._wiPanelDelete async function inside _renderWiPanel; Handler confirms deletion, calls api.workItems.delete(id, proj), removes from cache, re-renders

  PROMPTS P102311 [ ] [bug] [completed] [5] — Debugged work_item ordering by fixing seq_num NULL handling and ensuring prompts/commits link to wor
    Requirements: Explain why #20006 appears as last updated item despite being unrelated; Verify prompts and commits are properly associated with work_items; Ensure at least 1 prompt and 1 commit are linked to work_items
    Deliveries: Identified root cause: seq_num is NULL for most items, ORDER BY seq_num DESC puts NULLs first; Fixed: Changed to ORDER BY created_at DESC for correct chronological ordering; Modified MemoryPromotion.extract_work_items_from_events to use global next_seq() instead of local max+1; Verified prompt-to-commit-to-work_item linkage chain is complete

  PROMPTS P102322 [ ] [bug] [completed] [4] — Fixed UI behavior for AI tag acceptance and existing tag confirmation in work item planner.
    Requirements: When user accepts AI tag, confirm button should be removed (only delete stays); When user confirms existing tag, work_item should be removed from list and moved under the tag; When user confirms new tag, new tag should be added to planned and work_item moved into it; All linking should occur automatically
    Deliveries: Modified _wiPanelApproveTag to call _loadTagLinkedWorkItems after linking so item appears immediately under tag; Modified _wiSecApprove to show linked item immediately in tag table; Added green ✓ button for AI(NEW) row creation

  PROMPTS P102324 [ ] [bug] [completed] [4] — Resolved tag command conflict by creating /stag alias and tagged session with development and work_i
    Requirements: User reported error about unknown skill tag
    Deliveries: Identified /tag conflicts with reserved name in Claude Code's skill loader; Created /stag as renamed skill with same functionality; Tagged session directly with phase:development feature:work_items

  PROMPTS P102325 [ ] [bug] [completed] [4] — Fixed bug where adding AI tags caused work_items to disappear; metadata tags now stay in list.
    Requirements: When user accepts AI tag (doc_type, feature...), tag should be added as metadata, work_item should NOT disappear; Only AI(EXISTS) should link work_item to existing tag; Only AI(NEW) should create new tag and link work_item to it; Reduce loading time (1-2 second delay)
    Deliveries: Fixed _wiSecApprove to store in ai_tags.confirmed[] array instead of setting tag_id; Secondary chip now disappears while item stays in list with metadata confirmation toast; ✓ button now shown for all cases including suggested_new; Added loading indicator for better UX feedback

  PROMPTS P102341 [ ] [bug] [completed] [4] — Fixed UI bug where planner doesn't display bug/category categories and work items disappear on tag a
    Requirements: Fix planner UI not showing bug/category items, only work_item; Fix work_item disappearing when AI tag accepted with empty top screen display
    Deliveries: Fixed _renderWiPanel in entities.js (+19 lines); Updated route_entities.py functions: create_value, patch_value, delete_value, get_value_by_number, session_bulk_tag; Fixed tool_memory.py _handle_get_tag_context; Updated MCP server dispatch logic; Cleaned up legacy context files

  PROMPTS P102146 [ ] [task] [completed] [4] — Clarified that new tags in chat picker are created at root level; nested tags require Planner.
    Requirements: User asked for clarification on tag creation behavior in chat picker vs Planner
    Deliveries: Explained root-level tag creation in chat picker flow; Clarified nested sub-tag creation requires Planner with tree view and + child button

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session-level tags (Chat), prompt-level tags (History), commit linkage
    Requirements: Verify tags per session can be added in Chat; Verify tags per prompts managed in History; Verify commit-prompt tag linkage is proper; Check all logic is well-defined
    Deliveries: Confirmed history.py _load_unified_history reads current + all history_*.jsonl archives; Confirmed history.js uses data-ts attribute on entries and _jumpToPrompt with CSS.escape; Confirmed entities.py has _propagate_tags_phase4, untag_event_by_source_id, remove_session_tag; Confirmed chat.js _removeAppliedTag with untagSession integration; Confirmed api.js untagBySourceId and untagSession implementations

  PROMPTS P102191 [ ] [task] [in-progress] [3] — Identified hardcoded Pipeline in work_item_pipeline.py; explained merge path with workflow engine.
    Requirements: Locate where default Pipeline is configured; Identify missing parent-child tag support that disappeared; Desire to link Pipeline to workflow engine (possibly rename to 'Pipelines'); Explain how to merge both systems
    Deliveries: Located Pipeline configuration: ui/backend/core/work_item_pipeline.py (hardcoded); Documented 4 stages: PM → Architect → Developer → Reviewer as Python code; Explained Pipeline calls Anthropic API directly, does not use graph workflow engine; Identified POST /work-items/{id}/run-pipeline endpoint in Planner; Clarified Pipeline and workflow engine are parallel, isolated implementations

  PROMPTS P102198 [ ] [task] [in-progress] [3] — Explained Claude Agent SDK capabilities and assessment of fit for multi-agent PM/Dev/Tester/Reviewer
    Requirements: Explain what Claude Agent SDK is used for; Assess if it can replace current multi-agent system (PM, Developer, Tester, Reviewer)
    Deliveries: Explained Claude Agent SDK is Anthropic's framework for building AI agents with tools, subagents, state management, and streaming; Documented Agent SDK capabilities: tool execution, delegation to subagents, conversation state, user approvals; Provided assessment of fit for PM → Developer → Tester → Reviewer pipeline

  PROMPTS P102199 [ ] [task] [completed] [4] — Verified parent_id field added to work items for nested tag support.
    Requirements: Check that nested (parent-child) tags are supported in the planner; Verify UI is aligned with infrastructure changes from workflow improvements
    Deliveries: Confirmed parent_id: Optional[str] = None added to WorkItemCreate model; Verified INSERT query includes parent_id column; Verified SELECT query returns w.parent_id; Confirmed row serialization casts parent_id UUID to string

  PROMPTS P102242 [ ] [task] [in-progress] [1] — System files updated after session (no specific delivery details provided).
    Requirements: Clarify if Lifecycle tags are needed and relevant to current scope
    Deliveries: System files updated (commit f341693a)

  PROMPTS P102243 [ ] [task] [in-progress] [1] — System context and AI rules updated after session.
    Requirements: Address Lifecycle tags visibility in bug, feature, and task categories
    Deliveries: System context and AI rules files updated (commit 80a905d7)

  PROMPTS P102301 [ ] [task] [completed] [4] — Fixed date format to yy/mm/dd-hh:mm and removed non-work_item tags from display.
    Requirements: Change date format from yymmddhhmm to yy/mm/dd-hh:mm; Remove tags (Shared-memory, billing, etc.) from work_items display as they are not work_items
    Deliveries: Implemented fmtDate function with correct yy/mm/dd-hh:mm format; Modified _renderWiPanel to filter out non-work_item tags; Confirmed api.workItems.delete(id, project) exists at line 374 with proper handler wiring

  PROMPTS P102316 [ ] [task] [in-progress] [3] — Explained session management, context compression, and provided architectural overview of tag tracki
    Requirements: Add mechanism to conversation for forcing tag addition and periodic user confirmation every 5-10 prompts; Explain if new session is created for data compression; Clarify session ID behavior and context compression in CLI
    Deliveries: Explained that same session_id persists throughout entire CLI session; Context compression is invisible — no new session_id needed; New session_id only created when user quits Claude and runs fresh; Current session 9315de75 has been running entire time, explaining 37 commits / 9 prompts across work_items; Updated list_tools in backend/agents/mcp/server.py with 12 new lines

  PROMPTS P102323 [ ] [task] [completed] [4] — Clarified that /tag command works in current session without needing new session.
    Requirements: User asked if they can add tags to prompts using /tag or if new session is needed
    Deliveries: Explained /tag updates .agent-context and calls PUT /history/session-tags; Clarified log_user_prompt.sh reads .agent-context on every prompt; Noted /tag does not retroactively tag existing prompts

  PROMPTS P102330 [ ] [task] [completed] [4] — Changed session tags from work_items to planner feature tag.
    Requirements: Change tag to feature:planner for session tracking
    Deliveries: Session tags set to phase:development, feature:planner; Confirmed all future prompts and commits will be tagged accordingly

  PROMPTS P102331 [ ] [task] [completed] [4] — Analyzed planner_tag table schema and proposed cleanup of redundant/unused columns.
    Requirements: Analyze seq_num field - is it needed?; Clarify source vs creator columns - should one be removed?; Clarify status vs status_new - why two columns?; Determine if code_summary is needed in planner_tags; Identify which fields require user input vs AI generation
    Deliveries: Recommended dropping seq_num (always null, never populated); Recommended dropping source, keep creator only (source is redundant); Confirmed only one status column needed; Clarified code_summary belongs in work_items, not planner_tags; Proposed clean set of user-maintained columns: name, status, description, creator, requirements, acceptance_criteria, action_items

  PROMPTS P102333 [ ] [task] [completed] [3] — Planned removal of AI-generated columns from planner_tags and clarified extra column usage.
    Requirements: Plan to merge planner_tags with work_item for AI-generated summary and design; Remove summary, design, embedding columns from planner_tags; Clarify what extra column is used for
    Deliveries: Proposed creating merger layer for AI-generated fields (summary, design); Identified summary, design, embedding, extra as candidates for removal; Planned cleanup while keeping user-facing fields

  PROMPTS P102336 [ ] [task] [completed] [4] — Session tag 'feature: feature_snapshot' set for development tracking.
    Requirements: Add tag feature:feature_snapshot to session
    Deliveries: Session tag set to 'feature: feature_snapshot'; Cleaned up stale agent context and legacy system files

  PROMPTS P102339 [ ] [task] [completed] [4] — Analyzed aicli product architecture and provided recommendations for improving flow visibility and p
    Requirements: Improve point 4 - increase visibility on all flows with managed prompts in separate files; Improve point 5 - enhance workflow system that runs based on approved features, originally built as prompt management for flows
    Deliveries: Product analysis document explaining aicli as shared AI memory platform; Identified core problem: AI tools lose project context between sessions; Explained architecture that intercepts development lifecycle (prompts, commits, work items); Recommendations for improving flow visibility and prompt management integration

  PROMPTS P102347 [ ] [task] [completed] [4] — Cleaned up event tags to show only user-managed tags, removed system metadata from 1441 events and b
    Requirements: Remove old system tags from events, show only user-merged/updated tags; Only retain phase, feature, bug, source tags and remove system metadata
    Deliveries: Pass 0: Fixed 6 corrupt session_summary events with malformed JSON tag arrays; Pass 1: Stripped system metadata tags (llm, event, chunk_type, commit_hash, commit_msg, file, etc.) from 1441 events; Pass 2: Backfilled 1440 commit events with {} tags from mem_mrr_commits.tags; Implemented backfill_event_tags endpoint (+191 lines in route_admin.py); Cleaned up legacy system root files and reorganized context

  PROMPTS P102354 [ ] [task] [completed] [4] — Moved session ID display to tag bar and fixed chat loading to sync latest chats from local JSON file
    Requirements: Show session ID only in tag bar (feature list/tag area) not in messages, without duplicate phase display; Fix chat auto-loading from outdated JSON files; ensure last chats update to local files quickly for fast loading
    Deliveries: Moved session ID badge to tag bar between entity chips and + Tag button; Session ID shows last 5 chars (ab3f9) with click-to-copy full UUID functionality; Removed session banner from message headers to avoid duplication; Phase dropdown already shown on left, no longer repeated in multiple locations; Identified chat loading issue: local JSON cache not synced with latest sessions

  PROMPTS P102305 [ ] [bug|feature] [completed] [5] — Fixed work_item detail loading, improved tag suggestion layout, increased fonts, styled × button, an
    Requirements: Fix work_item details not loading on click; Move tag and approve/remove buttons closer together; Increase font size for Electron app visibility; Make × button bold red instead of gray; Add right padding so full date/hour is visible
    Deliveries: Fixed _openWorkItemDrawer to call api.workItems.get(id, project) directly instead of searching list; Changed suggestion row to use inline-flex for compact layout; Increased all font sizes throughout UI; Styled × button with bold red color; Added right padding to date column for full visibility

---

## **mcp-integration-setup** · 26/03/10-03:14 [ ] (claude)
> Type: new
> Total: 26 prompts
> User tags:
> AI existing:
> AI new: [task:mcp-setup]
> Summary: MCP server setup, project integration, and CLI configuration
> Requirements: Explain if Claude Code uses MCP server to receive project information; Explain why no suggestions appear in sessions; Clarify session/commit tracking in chat footer; Understand if hook configuration needed for session-commits connection; Verify how Claude CLI stores prompts and responses with commits
> Deliveries: [bug|completed|4|6] Fixed 6 critical bugs in database queries, session ordering, and planner UI state; [task|completed|4|4] Configured MCP server integration and clarified architecture for Claude Code sessions; [task|completed|4|3] Documented aicli memory system, session-commit pipeline, and work-item tracking; [feature|completed|4|2] Implemented Agent Roles feature and tag merge pipeline with AI/MRR data sources; [task|completed|4|2] Refactored memory naming convention and workspace cleanup

  PROMPTS P102193 [ ] [feature] [completed] [4] — Completed Agent Roles implementation with auto-population and UI updates
    Requirements: Agent Roles implementation in graph_workflow.js with role selection and config auto-population
    Deliveries: _gwOnRoleChange(val): auto-populates cfg-provider/cfg-model from role defaults and updates UI; _saveNodeConfig(): reads role_id from dropdown instead of role_file

  PROMPTS P102231 [ ] [feature] [completed] [3] — Implement tag pipeline from planner merging AI and MRR data sources
    Requirements: Implement pipeline triggered from planner tab; Project manager agent merges tag info with ai table (mem_ai_tags) and MRR tables (mem_mrr_tags)
    Deliveries: Backend tagging logic updated with memory integration (commit 5b05724a)

  PROMPTS P102235 [ ] [feature] [in-progress] [1] — Design drag-and-drop merge feature for planner tab with parent-child support
    Requirements: Create new feature to merge tags in UI via drag-and-drop; Extend planner tab with drag-and-drop functionality; Support merging within category or from AI suggested to other categories; Support parent-child relationships during merge; Update planner_tag table on merge

  PROMPTS P102188 [ ] [bug] [completed] [4] — Fixed database array parsing bug and confirmed end-to-end memory pipeline working.
    Requirements: Verify API keys can be loaded from .env file; Ensure full pipeline works with proper key configuration
    Deliveries: Fixed ARRAY_AGG(uuid[]) parsing from psycopg2 string to proper UUID list; Created 2 session memory items with Trycycle scores; Extracted 7 project facts from summaries via Haiku; Confirmed end-to-end pipeline functioning correctly

  PROMPTS P102317 [ ] [bug] [completed] [4] — Resolved /tag skill unknown error and explained session restart requirement.
    Requirements: Fix unknown skill /tag error; Clarify when new session needed to pick up skill changes
    Deliveries: Explained /tag skill requires new Claude Code session to load; Provided valid tag keys from aicli.yaml: phase, feature, bug, task, component, doc_type, design, decision, meeting, customer; Showed example /tag usage patterns; Explained error handling for unknown keys

  PROMPTS P102177 [ ] [bug] [completed] [4] — Fixed session ordering to use creation date instead of update timestamp
    Requirements: Session order should remain stable by prompt or session date, not change when phase is modified
    Deliveries: Backend: patch_session_tags no longer updates updated_at timestamp; Frontend: _loadSessions now sorts by created_at instead of updated_at for stable ordering

  PROMPTS P102269 [ ] [bug] [completed] [4] — Fixed JSONB type casting error in route_history upsert query
    Requirements: Fix PostgreSQL execute_values error in route_history line 470; Resolve type mismatch in tags merge operation using || operator
    Deliveries: Fixed line 466: cast EXCLUDED.tags to ::jsonb to match jsonb type for || operator; Explanation of root cause: text type incompatibility with jsonb || operator (commit 66772877)

  PROMPTS P102270 [ ] [bug] [completed] [4] — Fixed ON CONFLICT DO UPDATE duplicate constraint error in sync_commits route
    Requirements: Fix ON CONFLICT DO UPDATE command cannot affect row a second time error in route_history line 470; Ensure commit sync returns correct count of 364 unique hashes from 683 entries
    Deliveries: Identified and fixed duplicate constraint violation in cur.execute(b''.join(parts)); Verified fix allows POST /history/commits/sync to return {imported: 364, project: aicli}; Ensured Commits tab loads from DB with proper prompt links, tags, and full messages

  PROMPTS P102273 [ ] [bug] [completed] [4] — Fixed ReferenceError: _plannerSelectAiSubtype and window._plannerSync undefined errors
    Requirements: Fix Uncaught ReferenceError: _plannerSelectAiSubtype is not defined; Fix TypeError: window._plannerSync is not a function in route_logs
    Deliveries: Removed problematic line causing init function crash; Fixed window._plannerSync assignment by removing undefined _plannerSelectAiSubtype reference; Cleaned up system context and session files across 6 commits

  PROMPTS P102279 [ ] [bug] [completed] [3] — Diagnosed slow data loading in route_work_items due to 60+ second migration on Railway
    Requirements: Fix errors loading data in route_work_items line 249 cur.execute(_SQL_UNLINKED_WORK_ITEMS); Fix missing column definition at line 288 w.merged_into, w.start_date
    Deliveries: Identified migration performance issue (60+ seconds) on Railway infrastructure; Confirmed backend IS working, issue is latency not code failure; Updated system context documentation in 2 commits

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server architecture and why Claude doesn't use it directly in web sessions.
    Requirements: Explain if Claude Code uses MCP server to receive project information; Explain why no suggestions appear in sessions; Clarify session/commit tracking in chat footer
    Deliveries: Explained MCP server is for Claude CLI only, not web UI Claude; Clarified that direct file reading is used instead of MCP in this context; Outlined how session context flows through the system

  PROMPTS P102156 [ ] [task] [completed] [4] — Confirmed session-commit connection already exists in hooks; UI display was the missing piece.
    Requirements: Understand if hook configuration needed for session-commits connection; Verify how Claude CLI stores prompts and responses with commits
    Deliveries: Confirmed auto_commit_push.sh hook already writes session_id to commit_log.jsonl; Explained full pipeline from Claude Code CLI session to hook execution; Showed session_id is properly stored and connected to commits

  PROMPTS P102189 [ ] [task] [completed] [4] — Configured .mcp.json for project root and clarified MCP will activate in next Claude Code session.
    Requirements: Determine if MCP is being used in current session; Explain MCP configuration status
    Deliveries: Confirmed MCP not used in current session; all calls via direct HTTP/curl; .mcp.json placed at project root for Claude Code discovery; Explained enableAllProjectMcpServers: true setting to avoid approval prompts

  PROMPTS P102194 [ ] [task] [in-progress] [0] — Request to use MCP tool to explain project — response empty.
    Requirements: Use MCP tool to get and explain project information

  PROMPTS P102197 [ ] [task] [completed] [4] — Explained aicli's 5-layer memory system architecture and core functionality.
    Requirements: Use MCP tool to explain what the code does; Describe aicli project purpose and functionality
    Deliveries: Described aicli as shared AI memory platform solving context loss across tools; Explained 5-layer memory system: live conversation → session → project docs → history → templates; Outlined /memory command functionality and context synthesis; Clarified how persistent memory is shared between Claude CLI, Cursor, ChatGPT, and web UI

  PROMPTS P102209 [ ] [task] [in-progress] [0] — Request to refactor database schema removing client-specific tables — response empty.
    Requirements: Remove cl_[client] prefixed tables to avoid client name pattern; Consolidate to mng_ and pr_ tables with multi-tenancy support; Leverage existing mng_users table for client-user management; Keep history/commits unified per client rather than per-client tables

  PROMPTS P102237 [ ] [task] [in-progress] [0] — Identified workspace folder under backend; status of usage not stated.
    Requirements: Determine if backend/workspace folder is actively used

  PROMPTS P102238 [ ] [task] [completed] [4] — Deleted workspace folder per user request.
    Requirements: Delete backend/workspace folder
    Deliveries: Removed workspace folder from backend directory

  PROMPTS P102227 [ ] [task] [in-progress] [0] — Test prompt after migration (no changes recorded)
    Requirements: Test system after migration

  PROMPTS P102229 [ ] [task] [in-progress] [0] — Test after mem_ai cleanup (no changes recorded)
    Requirements: Verify system functionality after mem_ai cleanup

  PROMPTS P102234 [ ] [task] [completed] [2] — Fixed workspace state and memory after session update
    Requirements: Fix issues across all affected systems
    Deliveries: Workspace state corrections applied (commit d79175fa)

  PROMPTS P102263 [ ] [task] [in-progress] [0] — Test prompt after fix (no changes recorded)
    Requirements: Verify functionality after recent fixes

  PROMPTS P102266 [ ] [task] [in-progress] [0] — Final verification prompt (no changes recorded)
    Requirements: Final verification of system state

  PROMPTS P102288 [ ] [task] [completed] [5] — Refactored memory module naming convention and updated all 11 callers consistently
    Requirements: Ensure all memory files follow memory_*.py naming pattern; Delete mem_embeddings.py and update all callers; Rename mem_sessions.py to memory_sessions.py and update references; Update __init__.py to reflect current 9 modules
    Deliveries: Deleted mem_embeddings.py and updated 11 callers across 7 files to use memory.memory_embedding; Renamed mem_sessions.py to memory_sessions.py and updated route_chat.py; Updated __init__.py with accurate list of all 9 current memory modules; Updated 10 function references across backend (embed_text, _fire_background, _safe_embed, etc.)

  PROMPTS P102290 [ ] [task] [completed] [4] — Explained commit-to-work-item linkage chain and how to track metrics per work item
    Requirements: Explain how commit data statistics connect to work_items; Describe method to know rows/prompts used for specific work item; Provide example: auth work item - prompts count, commits count, rows changed
    Deliveries: Documented complete linkage chain from session tags → mng_session_tags → mem_mrr_commits → mem_mrr_commits_code; Showed how mem_ai_work_items.id connects to commit tags (work-item UUID); Explained extract_commit_code background job creates per-symbol/file tracking rows; Demonstrated how to query work item metrics using work item UUID

  PROMPTS P102329 [ ] [task] [in-progress] [0] — Column naming refactor and work_item enhancement incomplete - awaiting implementation
    Requirements: Rename ai_name to name_ai, ai_category to category_ai, ai_desc to desc_ai for consistency; Add summary_ai column if needed; Ensure prompt_work_item() runs during /memory endpoint call; Update work_item columns with new system data to provide full project view

---

## **general-commits** · 26/04/12-00:03 [+] (auto)
> Type: existing
> Total: 7 commits
> User tags:
> AI existing:
> AI new:
> Summary: 7 commits updating: backend/core/db_migrations.py, backend/memory/memory_planner.py, backend/memory/memory_promotion.py, backend/memory/memory_tagging.py, backend/routers/route_projects.py, backend/routers/route_work_items.py… | classes: MemoryFeatureSnapshot, MemoryPlanner, MemoryPromotion, MemoryTagging

  COMMITS C200666 [+] [feature] [completed] [5] — Add memory embedding and event extraction to memory promotion flow
    Deliveries: backend/agents/tools/tool_memory.py: _handle_search_memory (+21/-0); backend/memory/memory_promotion.py: MemoryPromotion (+10/-1); backend/memory/memory_promotion.py: _embed_work_item (+19/-0); backend/memory/memory_promotion.py: MemoryPromotion.promote_work_item (+6/-0); backend/memory/memory_promotion.py: MemoryPromotion.extract_work_items_from_events (+4/-1)

  COMMITS C200667 [+] [feature] [completed] [5] — Introduce deliveries feature with DB migration and tag/delivery CRUD endpoints
    Deliveries: backend/core/db_migrations.py: m028_add_deliveries (+30/-0); backend/routers/route_tags.py: TagUpdate (+1/-0); backend/routers/route_tags.py: DeliveryCreate (+5/-0); backend/routers/route_tags.py: CategoryCreate (+0/-1); backend/routers/route_tags.py: _row_to_tag (+8/-6)

  COMMITS C200668 [+] [feature] [completed] [5] — Add feature snapshot memory module with LLM-based snapshot generation
    Deliveries: backend/core/db_migrations.py: m029_feature_snapshot (+44/-0); backend/memory/memory_feature_snapshot.py: MemoryFeatureSnapshot (+435/-0); backend/memory/memory_feature_snapshot.py: _parse_json (+9/-0); backend/memory/memory_feature_snapshot.py: _slugify (+2/-0); backend/memory/memory_feature_snapshot.py: _call_llm (+21/-0)

  COMMITS C200669 [+] [feature] [completed] [5] — Add pipeline run logging and workflow/pipeline status tracking endpoints
    Deliveries: backend/core/db_migrations.py: m030_pipeline_runs (+44/-0); backend/core/pipeline_log.py: pipeline_run_sync (+14/-0); backend/core/pipeline_log.py: _insert_run (+20/-0); backend/core/pipeline_log.py: _finish_run (+25/-0); backend/core/pipeline_log.py: pipeline_run (+18/-0)

  COMMITS C200670 [+] [feature] [completed] [5] — Add PostgreSQL database maintenance and cleanup utilities
    Deliveries: backend/data/clean_pg_db.py: _raw_conn (+8/-0); backend/data/clean_pg_db.py: _bytes_to_mb (+2/-0); backend/data/clean_pg_db.py: run_maintenance (+170/-0); backend/data/clean_pg_db.py: run_maintenance_async (+4/-0); backend/data/clean_pg_db.py: _cli (+34/-0)

  COMMITS C200665 [+] [task] [completed] [5] — Refactor memory promotion and work item column naming across DB/memory/router modules
    Deliveries: backend/core/db_migrations.py: m025_rename_work_item_ai_columns (+15/-0); backend/memory/memory_planner.py: MemoryPlanner (+5/-5); backend/memory/memory_planner.py: MemoryPlanner._build_user_message (+3/-3); backend/memory/memory_planner.py: MemoryPlanner._write_document (+2/-2); backend/memory/memory_promotion.py: MemoryPromotion (+93/-20)

  COMMITS C200671 [+] [task] [completed] [5] — Add database index on prompts source_id column for query optimization
    Deliveries: backend/core/db_migrations.py: m050_prompts_source_id_index (+21/-0)
