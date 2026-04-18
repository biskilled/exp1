# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items` to merge approved items into use cases.

## **discovery** · 26/03/13-17:44 [ ] (claude)
> Type: existing
> Total: 5 prompts
> User tags:
> AI existing:
> AI new:
> Summary: System overview, architecture explanation, and project understanding
> Requirements: Provide short explanation of aicli system purpose; Run /memory command and review current architecture; Verify how data is stored and MCP integration; Check tagging accuracy for embed/retrieve operations; Test memory information quality using MCP in session
> Deliveries: [task|in-progress|0] Explain aicli system to non-technical user; [task|in-progress|0] Audit memory layer architecture and data quality via MCP; [task|in-progress|0] Use MCP tool to explain project purpose; [task|in-progress|0] Use MCP tool to explain codebase functionality; [task|in-progress|0] Review architecture for multi-client/project scaling and free user management

  PROMPTS P100831 [ ] [task] [in-progress] [0] — Explain aicli system to non-technical user
    Requirements: Provide short explanation of aicli system purpose
    Deliveries: Described aicli as shared AI memory platform solving multi-tool context loss problem; Explained unified history, git commit tagging, and memory file features

  PROMPTS P100861 [ ] [task] [in-progress] [0] — Audit memory layer architecture and data quality via MCP
    Requirements: Run /memory command and review current architecture; Verify how data is stored and MCP integration; Check tagging accuracy for embed/retrieve operations; Test memory information quality using MCP in session
    Deliveries: Executed /memory command successfully, generated 5 files with current synthesis state; Analyzed file layer architecture in workspace/aicli/_system/ (history.jsonl structure); Assessed 5-layer memory system design from live conversation to global templates

  PROMPTS P100868 [ ] [task] [in-progress] [0] — Use MCP tool to explain project purpose
    Requirements: Use MCP tool to retrieve and explain aicli project

  PROMPTS P100871 [ ] [task] [in-progress] [0] — Use MCP tool to explain codebase functionality
    Requirements: Use MCP tool to describe what the code does
    Deliveries: Described 5-layer memory system architecture storing context across multiple levels; Explained /memory command synthesis and context retrieval across different AI tools; Covered persistent memory solution for multi-tool context switching problem

  PROMPTS P100882 [ ] [task] [in-progress] [0] — Review architecture for multi-client/project scaling and free user management
    Requirements: Evaluate current architecture assuming multiple clients with different projects; Provide recommendations for managing free/unregistered clients; Assess scalability concerns
    Deliveries: Identified three-tier naming pattern (mng_, cl_local_ seeding) as clean for single-tenant; Flagged table proliferation risk: 20 clients × 10 projects = 120 client tables + 2000 project tables in public schema; Analyzed PostgreSQL DDL scalability: 6 statements per client, 10 per project

---

## **ui-bugs** · 26/03/10-00:11 [ ] (claude)
> Type: new
> Total: 29 prompts
> User tags:
> AI existing:
> AI new:
> Summary: UI rendering issues, loading problems, visibility and interaction bugs
> Requirements: Fix UI loading issue; Resolve port 8000 bind error; Restart Electron and backend cleanly; Verify UI visibility; Increase action button visibility
> Deliveries: [bug|in-progress|0] UI not loading due to port 8000 bind error from stale uvicorn; [task|in-progress|0] Clean backend/frontend restart needed after stale process cleanup; [feature|in-progress|0] Improve planner UI action visibility and add 3-dot menu for task details; [bug|in-progress|0] Fix tag bar visibility when showing memory chips after /memory command; [bug|in-progress|0] Fix phase dropdown not persisting when switching chat sessions; [bug|in-progress|0] Fix phase save error and add phase filtering in History/Commits views; [bug|in-progress|0] Restore phase change functionality and fix session metadata initialization

  PROMPTS P100822 [ ] [feature] [in-progress] [0] — Improve planner UI action visibility and add 3-dot menu for task details
    Requirements: Increase action button visibility; Add 3-dot menu for task metadata; Add subtags/window for properties; Add tag support to new chats
    Deliveries: Verified no syntax errors in UI imports

  PROMPTS P100941 [ ] [feature] [in-progress] [0] — Add text selection and improve prompt/response display in history
    Requirements: Show full prompt and LLM response in history; Enable text copying from history UI
    Deliveries: Updated history display to show full prompt and response text

  PROMPTS P100978 [ ] [feature] [in-progress] [0] — Add sticky headers and AI tag suggestions to work items panel
    Requirements: Make column headers sticky; Show AI tag suggestions with approve/reject buttons
    Deliveries: Added position:sticky to all 3 column headers in work items; Implemented AI tag suggestion row with ✓ approve and × remove buttons; Fixed tag matching logic in MemoryTagging class

  PROMPTS P100983 [ ] [feature] [in-progress] [0] — Add color-coded AI tag types and improve layout padding
    Requirements: Label AI tags as AI(EXIST) or AI(NEW) with colors; Color code: green for EXIST, red for NEW, blue for USER; Add left padding to table; Show full date timestamps; Explain missing AI recommendations
    Deliveries: Fixed import json in route_work_items.py; Removed stray conn.commit() outside context; Updated Level 4 fallback in match_work_item_to_tags to trigger on empty results

  PROMPTS P101023 [ ] [feature] [in-progress] [0] — Add prompt tagging in chat and implement auto-reload for new prompts
    Requirements: Show latest prompts in chat auto-updating; Add tag option to user prompts like History view; Store tags in mem_mrr_prompts table
    Deliveries: Fixed hook-log endpoint to store all prompts correctly via migration m050; Created ⟳ reload UI button in History tab; Confirmed all prompt storage working

  PROMPTS P101024 [ ] [feature] [in-progress] [0] — Add session ID display and timestamp to prompts in history
    Requirements: Show session ID last 5 characters in left panel; Display session ID at top of right pane; Add tag options per prompt; Show all existing user tags per prompt
    Deliveries: Added sid.slice(-5) for last 5 chars display; Created styled session ID banner in history.js with copy button; Changed tag filter to show all tags not just phase:*

  PROMPTS P101025 [ ] [feature] [in-progress] [0] — Display session info in chat header and add prompt tagging UI
    Requirements: Show CLI <phase> (session_id) format in chat header; Display full session ID when accessing session; Add tag input for prompts; Show all existing tags per prompt
    Deliveries: Updated session header to show source/phase/session_id/prompt_count/timestamp; Fixed source label mapping (claude_cli→CLI, ui→UI, workflow→Workflow); Added each prompt showing timestamp and tag info

  PROMPTS P101028 [ ] [feature] [in-progress] [0] — Relocate session ID to tag bar and remove redundant phase display
    Requirements: Show session ID in tag bar between chips and +Tag button; Remove phase from messages header since phase in dropdown; Ensure session ID clickable for copy to clipboard
    Deliveries: Added session ID badge (ab3f9) to tag bar; Implemented click-to-copy with ✓ copied flash; Removed _renderSessionHeader from messages display

  PROMPTS P100816 [ ] [bug] [in-progress] [0] — UI not loading due to port 8000 bind error from stale uvicorn
    Requirements: Fix UI loading issue; Resolve port 8000 bind error
    Deliveries: Identified stale uvicorn PID 86671 still holding port 8000; Confirmed backend health and API functionality

  PROMPTS P100825 [ ] [bug] [in-progress] [0] — Fix tag bar visibility when showing memory chips after /memory command
    Requirements: Show memory tag chips after /memory command; Fix overflow clipping of multiple chips
    Deliveries: Removed overflow:hidden clipping; Enabled text wrapping for tag chips

  PROMPTS P100846 [ ] [bug] [in-progress] [0] — Fix phase dropdown not persisting when switching chat sessions
    Requirements: Load last phase from DB on app startup; Update phase UI when switching sessions; Persist phase changes to DB
    Deliveries: Added phase load on init after tag bar setup; Fixed _setupTagBar to call api.getSessionTags; Added PUT /history/session-tags persistence endpoint

  PROMPTS P100847 [ ] [bug] [in-progress] [0] — Fix phase save error and add phase filtering in History/Commits views
    Requirements: Enable phase changes to save properly; Add phase dropdown to Commits view; Allow phase filtering in both views
    Deliveries: Removed _sessionId=null from phase change listener; Added PATCH /chat/sessions/{id}/tags endpoint; Implemented api.patchSessionTags call on phase change

  PROMPTS P100848 [ ] [bug] [in-progress] [0] — Restore phase change functionality and fix session metadata initialization
    Requirements: Restore _sessionId=null behavior for phase changes; Fix History default to show all phases not just discovery; Fix Commits phase filter persistence
    Deliveries: Restored _sessionId=null to create new session per phase; Re-added api.putSessionTags global persistence; Fixed session init with api.getSessionTags pre-fill

  PROMPTS P100849 [ ] [bug] [in-progress] [0] — Fix phase not updating when switching between chat sessions
    Requirements: Show correct phase for each session; Update phase when loading session; Persist phase changes
    Deliveries: Removed _sessionId=null reset from phase listener; Added api.patchSessionTags call to update session JSON metadata; Fixed session list refresh after phase change

  PROMPTS P100850 [ ] [bug] [in-progress] [0] — Mark all sessions without phase with red warning and fix phase persistence
    Requirements: Show red ⚠ badge on sessions missing phase; Fix phase save for CLI sessions; Ensure all session types save phase consistently
    Deliveries: Removed source==='ui' condition from phase warning badge; Added fallback to _system/session_phases.json for non-UI sessions; Fixed PATCH endpoint to handle CLI session IDs

  PROMPTS P100886 [ ] [bug] [in-progress] [0] — Fix project loading race condition and backend startup delay visibility
    Requirements: Improve project display on initial load; Handle backend startup latency gracefully
    Deliveries: Added retry logic to _continueToApp for empty project load; Documented backend latency expectations in logs

  PROMPTS P100913 [ ] [bug] [in-progress] [0] — Fix database column reference errors in route_history and route_entities
    Requirements: Fix missing event_type column in history queries; Fix undefined log reference; Fix missing c.id column in entities queries
    Deliveries: Fixed column reference errors in route_history.py line 228; Fixed undefined log name reference; Fixed c.id reference in route_entities.py line 1033

  PROMPTS P100915 [ ] [bug] [in-progress] [0] — Fix drag and drop and counter display in planner UI
    Requirements: Enable drag and drop functionality; Show counter updates
    Deliveries: Analyzed drag and drop and counter components

  PROMPTS P100942 [ ] [bug] [in-progress] [0] — Restore LLM response display in history and fix hook definitions
    Requirements: Show both prompt and LLM response in history; Ensure background hooks are properly defined and called
    Deliveries: Fixed hook-response to save response to mem_mrr_prompts.response; Verified session-summary, memory, and auto-detect-bugs hooks; Aligned workspace/_templates/hooks and workspace/aicli/_system/hooks definitions

  PROMPTS P100979 [ ] [bug] [in-progress] [0] — Fix work item detail loading and improve tag suggestion UI layout
    Requirements: Load work item details when clicking row; Move tag suggestions closer to item; Increase font sizes for readability; Fix color contrast of close button; Show full date/time column
    Deliveries: Added GET /work-items/{id} endpoint for direct item fetch; Changed tag suggestion to inline-flex layout; Increased font sizes across UI; Changed × button to bold red; Added right padding to date column

  PROMPTS P100981 [ ] [bug] [in-progress] [0] — Fix table layout to show all columns and improve name column width
    Requirements: Display all table columns including last column; Allow description to use full name column width; Show AI and user tags
    Deliveries: Updated colgroup to balance column widths in entities.js _renderWiPanel

  PROMPTS P100982 [ ] [bug] [in-progress] [0] — Restore table layout and add labeled tag sections in work items
    Requirements: Show all table columns including rightmost column; Add AI/User tag labels for clarity; Show USER section even when empty
    Deliveries: Restored table-layout:fixed to prevent column overflow; Added labeled rows for AI: and USER: sections; Made USER: section always visible with '—' placeholder

  PROMPTS P101015 [ ] [bug] [in-progress] [0] — Fix planner categories display and work item acceptance flow
    Requirements: Show bugs/categories in planner view not just work_items; Keep work item visible after accepting AI tag; Update top screen after tag acceptance
    Deliveries: Verified backend API and database state correct

  PROMPTS P101016 [ ] [bug] [in-progress] [0] — Fix duplicate const declaration breaking Electron startup
    Requirements: Fix JavaScript const conflict in entities.js
    Deliveries: Renamed second const cats to cacheCats in _wiPanelCreateTag; Removed duplicate variable declaration

  PROMPTS P101029 [ ] [bug] [in-progress] [0] — Fix chat history loading to show all prompts not partial cache
    Requirements: Load full chat history on startup not just partial; Fix sort order with all 500+ entries; Merge DB and JSONL data correctly
    Deliveries: Added limit=500 to fetch query to get all 389 DB entries; Merged JSONL fallback entries (~142) correctly; Fixed sort order April newest to March oldest; Total 531 entries (389 DB + ~142 JSONL)

  PROMPTS P101030 [ ] [bug] [in-progress] [0] — Fix stale session ID on load and auto-select current session
    Requirements: Load with current session not stale old session; Auto-select current session without delay; Update session list to show current as highlighted
    Deliveries: Reset _sessionId to null at start of renderChat(); Read last_session_id synchronously from dev_runtime_state; Updated localStorage cache render to show no highlight initially

  PROMPTS P101031 [ ] [bug] [in-progress] [0] — Synchronously load current session on startup without delay
    Requirements: Load current session immediately on app start; Remove 15 second delay before showing correct session
    Deliveries: Updated _loadSessions to read last_session_id synchronously before network fetch; Cache renders with correct session highlighted immediately; Full fetch confirms or updates session after network call

  PROMPTS P100817 [ ] [task] [in-progress] [0] — Clean backend/frontend restart needed after stale process cleanup
    Requirements: Restart Electron and backend cleanly; Verify UI visibility
    Deliveries: Freed port 8000 by killing stale uvicorn; Instructed dev script startup with NODE_ENV=development

  PROMPTS P100972 [ ] [task] [in-progress] [0] — Force UI reload to pick up updated history.js changes
    Requirements: Apply updated history display logic
    Deliveries: Confirmed Vite serving updated history.js correctly

---

## **performance-optimization** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 9 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Database query optimization, caching, and system performance tuning
> Requirements: Reduce multiple database calls by loading tags once into memory; Implement smart dropdown with category filter and add new value option; Update memory and DB only on save, not on access; Optimize SQL queries to load once on project load and update on save; Add nested tags support (unlimited depth beyond current 2-level hierarchy)
> Deliveries: [task|in-progress|0] Optimize tag loading with smart dropdown picker and cache; [feature|in-progress|0] Design nested tags hierarchy and optimize SQL queries; [task|in-progress|0] Cache all tags in memory and fix tag color persistence; [feature|in-progress|0] Add pagination to chat, commits, and chats views; [bug|in-progress|0] Investigate project load performance and ordering issues; [bug|in-progress|0] Fix aiCli project visibility and optimize PROJECT.md loading; [task|in-progress|0] Add composite indexes and enforce query documentation pattern

  PROMPTS P100819 [ ] [feature] [in-progress] [0] — Design nested tags hierarchy and optimize SQL queries
    Requirements: Optimize SQL queries to load once on project load and update on save; Add nested tags support (unlimited depth beyond current 2-level hierarchy); Show full tag path in chat tab but allow users to create only at leaf level
    Deliveries: Documented feasibility of nested tags with parent_id column addition to entity_values; Designed database schema for unlimited tag depth: category → tag → subtag → sub-subtag; Planned tree view in planner tab showing all properties at every level

  PROMPTS P100838 [ ] [feature] [in-progress] [0] — Add pagination to chat, commits, and chats views
    Requirements: Add pagination UI (< > X/XXX) for chat showing 24 prompts per page; Implement pagination for chats view; Implement pagination for commits view
    Deliveries: Backend: _load_unified_history() now reads history.jsonl + all history_*.jsonl archives (204 total entries); Frontend: Chat tab shows ◀ [disabled] 1–100 / 204 ▶ pagination always visible on top right; Data deduped and noise filtered, range: 2026-02-23 → 2026-03-15

  PROMPTS P100869 [ ] [bug] [in-progress] [0] — Investigate project load performance and ordering issues
    Requirements: Fix project ordering in recent projects list; Add loading flow indicators to explain what is happening; Optimize summary and history loading speed
    Deliveries: Identified performance bottlenecks in project load and pagination

  PROMPTS P100870 [ ] [bug] [in-progress] [0] — Fix aiCli project visibility and optimize PROJECT.md loading
    Requirements: Restore missing aiCli project in recent projects; Optimize PROJECT.md file loading (currently >1 minute on free Railway); Reduce DB query overhead for project file loading
    Deliveries: Diagnosed PROJECT.md loading bottleneck related to DB queries

  PROMPTS P100993 [ ] [bug] [in-progress] [0] — Fix work item query logic and user tag approval controls
    Requirements: Clarify DIGEST column purpose (event counter vs. other); Fix work items appearing without linked prompts, commits, or events; Explain why work item #20428 appears at top; Allow users to approve/remove AI-added purple tags
    Deliveries: Fixed get_unlinked_work_items query in route_work_items.py with NULLS LAST ordering; Modified _renderWiPanel and _renderWorkItemTable in entities.js to fix row rendering; Added user approval/removal controls for AI-added tags in _wiRenderRows (+4/-2)

  PROMPTS P100994 [ ] [bug] [in-progress] [0] — Fix work item event linking and commit counter display
    Requirements: Restore prompt counter display in work items; Fix work items appearing without linked events/prompts; Ensure work items properly connect to events → prompts/commits chain; Maintain work items as main link between mirror data and user action items
    Deliveries: Fixed _SQL_UNLINKED_WORK_ITEMS commit_ct CTE in route_work_items.py; Corrected join logic: mc.event_id = NULL for 418/444 commits → use mem_ai_events.source_id → mem_mrr_commits.commit_short_hash; Added e.source_id AS src_source_id to event queries; Updated _renderWiPanel in entities.js (+8/-3) to display commit counter correctly

  PROMPTS P100818 [ ] [task] [in-progress] [0] — Optimize tag loading with smart dropdown picker and cache
    Requirements: Reduce multiple database calls by loading tags once into memory; Implement smart dropdown with category filter and add new value option; Update memory and DB only on save, not on access
    Deliveries: New picker flow in chat.js: _pickerPopulateCats() reads from cache (zero DB calls); _pickerCatChange() enables text input and renders values in floating dropdown; _pickerValFilter() filters dropdown live with + Add option for new values

  PROMPTS P100833 [ ] [task] [in-progress] [0] — Cache all tags in memory and fix tag color persistence
    Requirements: Load all tags once into memory to avoid repeated DB calls on tag add; Preserve selected tag color when saving; Unify commits tag-saving mechanism with history tag-adding flow
    Deliveries: Added _buildTagCache(project, categories) in history.js to load tags once on tab open; Stored cache in _tagCache (grouped by category) and _tagCacheMap (flat {id → {color, name, icon}}); Integrated listCategories into initial Promise.all(4 parallel requests)

  PROMPTS P100992 [ ] [task] [in-progress] [0] — Add composite indexes and enforce query documentation pattern
    Requirements: Optimize planner tabs and work items query performance; Add SQL query documentation at top of each file/class; Ensure composite indexes cover common filter patterns
    Deliveries: Added migration m020 with 5 composite indexes in db_migrations.py; Created idx_mae_project_session on mem_ai_events(project_id, session_id); Created idx_mae_project_etype on mem_ai_events(project_id, event_type); Created idx_mmrrc_project_session on mem_mrr_commits(project_id, session_id); Removed duplicate tag columns from route_entities.py (TagBySourceIdBody, ValueCreate)

---

## **memory-schema-refactor** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 71 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Database schema design, memory layer architecture, and table restructuring
> Deliveries: [task|in-progress|0] Assuming I will improve the project management page, workflow processes. can you; [task|in-progress|0] The last prompts was asking for a new feature (clinet install/ support multiple ; [task|in-progress|0] can you run /memory, and make the UI more clear. add your sujjestion in a clear ; [task|in-progress|0] can you run /memory and run some tests? I do not see any sujjestion on all the e; [task|in-progress|0] Are you using the mcp server in order to reciave all project information ? Also,; [task|in-progress|0] I understand the issue. I am using your claude cli and hooks to store propts and; [task|in-progress|0] can you run /memory, to make sure all updated. also can you check that system is

  PROMPTS P100813 [ ] [task] [in-progress] [0] — Assuming I will improve the project management page, workflow processes. can you

  PROMPTS P100814 [ ] [task] [in-progress] [0] — The last prompts was asking for a new feature (clinet install/ support multiple 

  PROMPTS P100826 [ ] [task] [in-progress] [0] — can you run /memory, and make the UI more clear. add your sujjestion in a clear 

  PROMPTS P100827 [ ] [task] [in-progress] [0] — can you run /memory and run some tests? I do not see any sujjestion on all the e

  PROMPTS P100828 [ ] [task] [in-progress] [0] — Are you using the mcp server in order to reciave all project information ? Also,

  PROMPTS P100830 [ ] [task] [in-progress] [0] — I understand the issue. I am using your claude cli and hooks to store propts and

  PROMPTS P100834 [ ] [task] [in-progress] [0] — can you run /memory, to make sure all updated. also can you check that system is

  PROMPTS P100836 [ ] [task] [in-progress] [0] —  I do see session_tags.json - is it used ? Also - history.jsonl start to be very

  PROMPTS P100837 [ ] [task] [in-progress] [0] — Something wit hooks is not working now, as I do not see any new prompts / llm re

  PROMPTS P100842 [ ] [task] [in-progress] [0] — let me summerise not. first run /memroy to update all sumeeries, db tagging and 

  PROMPTS P100853 [ ] [task] [in-progress] [0] — now that there is porper tagging - can you make sure all is linked, mapped prope

  PROMPTS P100854 [ ] [task] [in-progress] [0] — is it align to the 5 steps memory? is there is any addiotnal requirement in orde

  PROMPTS P100855 [ ] [task] [in-progress] [0] — Is there is any addiotnal improvement that I can implemet for having full memroy

  PROMPTS P100856 [ ] [task] [in-progress] [0] — 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many pr

  PROMPTS P100857 [ ] [task] [in-progress] [0] — I would like to optimise the code : check each file, make sure code is in used a

  PROMPTS P100858 [ ] [task] [in-progress] [0] — I have started to look in some other solution like https://github.com/danshapiro

  PROMPTS P100859 [ ] [task] [in-progress] [0] — After this refactor - can you check if tags are well used ? is memroy improved b

  PROMPTS P100860 [ ] [task] [in-progress] [0] — Can you summersie all improvement - would that make the systme better perfromed 

  PROMPTS P100861 [ ] [task] [in-progress] [0] — Can you run the /memory and go over current architecure - how data is stored, ho

  PROMPTS P100862 [ ] [task] [in-progress] [0] — Keys are stored at my .env file which you can load - for claude api the key is u

  PROMPTS P100876 [ ] [task] [in-progress] [0] — before I continue - I do see quite lots of table used for this project. can you 

  PROMPTS P100877 [ ] [task] [in-progress] [0] — Can you run the command as well, as I dont see any change in the database . also

  PROMPTS P100878 [ ] [task] [in-progress] [0] — looks better. why memory_items and project_facts are under systeme managament ta

  PROMPTS P100879 [ ] [task] [in-progress] [0] — I do see the table mng_session_tags, I also see session_tags.json file at the pr

  PROMPTS P100880 [ ] [task] [in-progress] [0] — clean that up . also I do remember there was graph support for memroy usage, but

  PROMPTS P100881 [ ] [task] [in-progress] [0] — I would like to make sure the client table are also aligned - for example mng_se

  PROMPTS P100882 [ ] [task] [in-progress] [0] — I would like to know what do you think about the architecure ? Assuming there mi

  PROMPTS P100883 [ ] [task] [in-progress] [0] — That is correct. it is bed pattern to use clinet name. there is already mng_user

  PROMPTS P100884 [ ] [task] [in-progress] [0] — it looks like it is a bit broken, I have got an error - '_Database' object has n

  PROMPTS P100885 [ ] [task] [in-progress] [0] — There are some error - on the first load, it lookls like Backend is failing (aft

  PROMPTS P100888 [ ] [task] [in-progress] [0] — Is it makes more sense, before I continue to the secopnd phase (refactor embeddi

  PROMPTS P100889 [ ] [task] [in-progress] [0] — Yes please fix that. about pr_embedding. in the prevous prompts I have mention t

  PROMPTS P100890 [ ] [task] [in-progress] [0] — I am not sure all tagging functionality is implemented as I do not see the mng_a

  PROMPTS P100891 [ ] [task] [in-progress] [0] — I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_rela

  PROMPTS P100892 [ ] [task] [in-progress] [0] — I would like to make sure relation is managed properly.  relation can be managed

  PROMPTS P100893 [ ] [task] [in-progress] [0] — I would like to make sure that the final layer include Work Items, Feature Snaps

  PROMPTS P100894 [ ] [task] [in-progress] [0] — This task is related to current memory update (layer 1)  Create all memory files

  PROMPTS P100895 [ ] [task] [in-progress] [0] — perfect. I would like to have an updated aicli_memory with all updated memory st

  PROMPTS P100896 [ ] [task] [in-progress] [0] — Is it advised to merge pr_session_summeries into mem_ai_events. make sure there 

  PROMPTS P100897 [ ] [task] [in-progress] [0] — I think llm_source is missing in mem_ai_events. I also see columns that I am not

  PROMPTS P100898 [ ] [task] [in-progress] [0] — It seems that I cannot see the changes in the db 

  PROMPTS P100899 [ ] [task] [in-progress] [0] — It is working noew. ddl is updated. still I do se columns that I am not sure are

  PROMPTS P100900 [ ] [task] [in-progress] [0] — I would to refactor all mem_mrr_* tables as it seems there are columns that are 

  PROMPTS P100902 [ ] [task] [in-progress] [0] — can you do the same for the mem_ai tables ? 

  PROMPTS P100904 [ ] [task] [in-progress] [0] — It looks like database.py become really big. can you remove old migration and ma

  PROMPTS P100907 [ ] [task] [in-progress] [0] — Not sure if you remember the previous memory config. if you do (you can check ai

  PROMPTS P100910 [ ] [task] [in-progress] [0] — O would  like to cleanup the code more. I do see in Database old tables. can you

  PROMPTS P100919 [ ] [task] [in-progress] [0] — I do not see  any update the table strucure (still see some  old tables)

  PROMPTS P100926 [ ] [task] [in-progress] [0] — I would like to work on the mem_ai_events which takes events from all system. mo

  PROMPTS P100927 [ ] [task] [in-progress] [0] — Please add the llem_source after project, and in all tables where there is embed

  PROMPTS P100928 [ ] [task] [in-progress] [0] — I dont see any change in mem_ai_events. llm_source suppose to be after project, 

  PROMPTS P100929 [ ] [task] [in-progress] [0] — Looks good, can you rename this table to mem_ai_events_old. create new table be 

  PROMPTS P100930 [ ] [task] [in-progress] [0] —  What are the columns doc_type, language and file_path are used for ? also sessi

  PROMPTS P100931 [ ] [task] [in-progress] [0] — I would like to add language as a tags into the tags. if that is updated on each

  PROMPTS P100932 [ ] [task] [in-progress] [0] —  What is chunck and chunck_type are used for ? is it importnt information that c

  PROMPTS P100933 [ ] [task] [in-progress] [0] — I am looking at the table and see lots for event from history that not makes any

  PROMPTS P100935 [ ] [task] [in-progress] [0] — I would like to build the aicli_memory.md for scratch in order to get a final vi

  PROMPTS P100938 [ ] [task] [in-progress] [0] — I would like to add mng_projects table that will be used for project data. curre

  PROMPTS P100945 [ ] [task] [in-progress] [0] — I am checking the aiCli_memory - and it is looks likje it is not updated at all.

  PROMPTS P100954 [ ] [task] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100955 [ ] [task] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100956 [ ] [task] [in-progress] [0] — In addtion to your reccomendation, I would like to check the following -  mem_ai

  PROMPTS P100957 [ ] [task] [in-progress] [0] — dont you have any moemry, did you see the previous file you din - aicli_memoy.md

  PROMPTS P100958 [ ] [task] [in-progress] [0] — I still see the columns in commit table - diif_summery and diff_details . is it 

  PROMPTS P100959 [ ] [task] [in-progress] [0] — I would like to understand the commit table - do you have my previous comment? m

  PROMPTS P100967 [ ] [task] [in-progress] [0] — I would like to sapparte database.py in order to have methgods and tables schema

  PROMPTS P101017 [ ] [task] [in-progress] [0] — Events - I would like to make sure events are working properly in order to have 

  PROMPTS P101018 [ ] [task] [in-progress] [0] — Can you try again the table migration (using the column order I have mention) th

  PROMPTS P101019 [ ] [task] [in-progress] [0] — In events table is there is any point to have importance ? I think its more rele

  PROMPTS P101020 [ ] [task] [in-progress] [0] — yes

  PROMPTS P101022 [ ] [task] [in-progress] [0] — yes drop that. also change mem_mrr_prompts column order - after client_id add pr

---

## **tagging-system** · 26/03/09-23:51 [ ] (claude)
> Type: new
> Total: 37 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Tag management, tagging mechanism, AI tag suggestions, and tag relations
> Deliveries: [feature|in-progress|0] I dont think your update works. lets start from Planer - there is not need to ha; [feature|in-progress|0] I do have some concern how commit/hash are linked to prompts/llm answers. also a; [feature|in-progress|0] I do see that there is a link between commit and session ID. is it possible to h; [feature|in-progress|0] Taggin - there is a wau to add tags in History, commit and chat - which is good.; [feature|in-progress|0] Let me summersie and make sure all work properly - tags (per session) - can be a; [feature|in-progress|0] Currently the commit tags in Chat are all on a session phase. I would like to li; [feature|in-progress|0] When I run memory through the aiCli - I did see some usefull suggestion that app

  PROMPTS P100815 [ ] [feature] [in-progress] [0] — I dont think your update works. lets start from Planer - there is not need to ha

  PROMPTS P100832 [ ] [feature] [in-progress] [0] — I do have some concern how commit/hash are linked to prompts/llm answers. also a

  PROMPTS P100835 [ ] [feature] [in-progress] [0] — I do see that there is a link between commit and session ID. is it possible to h

  PROMPTS P100839 [ ] [feature] [in-progress] [0] — Taggin - there is a wau to add tags in History, commit and chat - which is good.

  PROMPTS P100840 [ ] [feature] [in-progress] [0] — Let me summersie and make sure all work properly - tags (per session) - can be a

  PROMPTS P100841 [ ] [feature] [in-progress] [0] — Currently the commit tags in Chat are all on a session phase. I would like to li

  PROMPTS P100845 [ ] [feature] [in-progress] [0] — When I run memory through the aiCli - I did see some usefull suggestion that app

  PROMPTS P100851 [ ] [feature] [in-progress] [0] — That looks better. the problem now is that on any change of the phase the sessio

  PROMPTS P100852 [ ] [feature] [in-progress] [0] — It looks good and working as expected. the issue now is how it is linked to Hist

  PROMPTS P100873 [ ] [feature] [in-progress] [0] — I dont see nay changes from the last improvement - current planner do not suppos

  PROMPTS P100874 [ ] [feature] [in-progress] [0] — I would like to go over on all the feutre and plan propery to Planer and Worklow

  PROMPTS P100875 [ ] [feature] [in-progress] [0] — Planner works partial - I do see the nested work on some category like doc_type 

  PROMPTS P100918 [ ] [feature] [in-progress] [0] — I do see lots of bug under the bug category which I did not opend. should that b

  PROMPTS P100920 [ ] [feature] [in-progress] [0] — Let fix the tagging mechanism to my mirroring until work_items phase.  For each 

  PROMPTS P100921 [ ] [feature] [in-progress] [0] — When I am adding tags I do see in the UI error [object object] - not the real st

  PROMPTS P100924 [ ] [feature] [in-progress] [0] — Looks like bug are fixed, and commit, prompts loading fast, but there is not con

  PROMPTS P100934 [ ] [feature] [in-progress] [0] — Yes please. about Sho llm in the ui - make it visible tag 

  PROMPTS P100968 [ ] [feature] [in-progress] [0] — In the ui when I press any tag, I do not the property on the left (I do see that

  PROMPTS P100975 [ ] [feature] [in-progress] [0] — The data is not cleared can you change that to yy/mm/dd-hh:mm ? also I do see ta

  PROMPTS P100980 [ ] [feature] [in-progress] [0] — I do see there is one ai_tags which is good. but ai_tags suppose to be feature, 

  PROMPTS P100984 [ ] [feature] [in-progress] [0] — I would like to update the ai_sujjestion - it suppose to sujjest one tag from ca

  PROMPTS P100986 [ ] [feature] [in-progress] [0] — Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujje

  PROMPTS P100987 [ ] [feature] [in-progress] [0] — Where are all the rpompts for ai_tags and work_item are ?

  PROMPTS P100988 [ ] [feature] [in-progress] [0] — I do see same work item working on mention document summery and update ai memory

  PROMPTS P100989 [ ] [feature] [in-progress] [0] — Can you share the quesry you are suing the get all promotps, commit, event per w

  PROMPTS P100990 [ ] [feature] [in-progress] [0] — before you desing. is it possible to add some mechanism to our converstion. for 

  PROMPTS P100991 [ ] [feature] [in-progress] [0] — I have just tried that, got unknow skill /tag. do I have to open a new session ?

  PROMPTS P100996 [ ] [feature] [in-progress] [0] — In the ui - when I accept AI tag - configrm should be remove (only delete suppos

  PROMPTS P100997 [ ] [feature] [in-progress] [0] — can I add tags  here for my prompts using /tag or I need to use a new session ?

  PROMPTS P100998 [ ] [feature] [in-progress] [0] — I always get an error saying ynknow skill tag. 

  PROMPTS P100999 [ ] [feature] [in-progress] [0] — ok. I do see it is possible to add AI tags, but when I add that, it seems that w

  PROMPTS P101000 [ ] [feature] [in-progress] [0] — I am not sre what is start_id used for . Also code_summenry - what is it for ? t

  PROMPTS P101001 [ ] [feature] [in-progress] [0] — I still dont understand what is summery column used for . also tags - I do see t

  PROMPTS P101002 [ ] [feature] [in-progress] [0] — What is summery used for, I do see ai_desc, what is summery for ?

  PROMPTS P101003 [ ] [feature] [in-progress] [0] — I think summery suppose to be part of ai_desc as there are alreadt 3 column for 

  PROMPTS P101004 [ ] [feature] [in-progress] [0] — I would like to woek on planner_tag. can you change the tag to feature:planner 

  PROMPTS P101010 [ ] [feature] [in-progress] [0] — can you add tag feature:feature_snapshot

---

## **workflow-pipeline** · 26/03/16-18:34 [ ] (claude)
> Type: new
> Total: 35 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Workflow management, pipeline configuration, automation, and job execution
> Requirements: Create roles (web developer, AWS architect) similar to specrails agents; Compare with paperclip integration; Define workflow engine design; Locate default pipeline configuration in Planner tab; Re-enable parent-child support for work items
> Deliveries: [task|in-progress|0] Define workflow system design comparing specrails, paperclip, and current YAML approach; [task|in-progress|0] Explain Run Pipeline feature and merge with workflow engine; [feature|in-progress|0] Design agent roles database schema with versioning and admin controls; [feature|in-progress|0] Complete Agent Roles UI implementation in graph_workflow.js; [feature|in-progress|0] Implement pipeline trigger from Planner with tag merging and agent routing; [feature|in-progress|0] Design drag-drop feature merge in Planner with parent-child nesting; [bug|in-progress|0] Fix Planner tab issues: lifecycle tags, AI bug counters, drag-drop nesting

  PROMPTS P100866 [ ] [feature] [in-progress] [0] — Design agent roles database schema with versioning and admin controls
    Requirements: Store prompts in database with ability to improve over time; Provide only roles to regular users; Allow admin/super user to review and change prompts/LLM properties
    Deliveries: Designed agent_roles and agent_role_versions schema; Planned _global project scope for shared roles; Outlined permission model for admin controls

  PROMPTS P100867 [ ] [feature] [in-progress] [0] — Complete Agent Roles UI implementation in graph_workflow.js
    Requirements: Auto-populate cfg-provider and cfg-model from selected role; Update description text on role change; Show/hide admin prompt preview panel
    Deliveries: Implemented _gwOnRoleChange(val) with role defaults auto-population in graph_workflow.js; Updated _saveNodeConfig() to read role_id instead of role_file; Added admin prompt preview panel toggle

  PROMPTS P100905 [ ] [feature] [in-progress] [0] — Implement pipeline trigger from Planner with tag merging and agent routing
    Requirements: Pipeline triggered from Planner tab (e.g. Auth bug tag); Project Manager agent merges tag info with mem_ai_tags and mem_mrr data; Route through multi-agent workflow
    Deliveries: Commit 5b05724a applied with updated ai system files and memory/tagging backend logic

  PROMPTS P100909 [ ] [feature] [in-progress] [0] — Design drag-drop feature merge in Planner with parent-child nesting
    Requirements: Extend Planner tab with drag-drop merge capability; Features dragged into another feature trigger merge; Drag only within category or from AI suggested to other categories; Support parent-child relationships; Update planner_tags on change
    Deliveries: Designed merge UX with drag-drop detection; Planned parent-child nesting support; Outlined merge logic preserving original features as history

  PROMPTS P100948 [ ] [feature] [in-progress] [0] — Enable work item drag-drop under parent and resizable panel height
    Requirements: Move work item (drag) under another item (remove from bottom, move to top); Make bottom screen resizable by line separator (up-down)
    Deliveries: Commit 36dfee39 applied with docs and memory updates

  PROMPTS P100951 [ ] [feature] [in-progress] [0] — Add move and merge capability for work items with context-aware merge UI
    Requirements: Move work item back to work item or another item; Merge only for work items with side panel UI (Merge into...); Show only work items under current parent in merge list; Remove merge from tags/items
    Deliveries: Removed merge UI from tags in _renderTagTableFromCache; Added work item move in _wiPanelDrop using _loadTagLinkedWorkItems; Implemented merge-into context filtering in entities.js; Commit d760cb38 applied with system context updates

  PROMPTS P100965 [ ] [feature] [in-progress] [0] — Link prompts to commits via events with automatic tagging and work item aggregation
    Requirements: 5 prompts summarize to 1 event; related commits linked to event; Remaining commits linked when event triggered; User tags propagate to events; AI tags auto-merge into event; Work items gather all new events and update data
    Deliveries: Fixed UI optimistic removal in entities.js when dragging work items; Optimized work items query replacing 5 correlated subqueries in route_work_items.py; Commit 4757f036 applied

  PROMPTS P100970 [ ] [feature] [in-progress] [0] — Add foreign key relationships linking commits to events to work items
    Requirements: Create mem_ai_work_items_links table with work_item_id, event_id, commit_id, tags, tags_ai; Link all events and commits to work items; Populate via user tags or AI tags
    Deliveries: Applied migration m019: added event_id FK to mem_mrr_commits, work_item_id FK to mem_ai_events; Dropped short-lived m018 mem_ai_work_items_links table; Updated process_commit() in memory_embedding.py and extract_work_items_from_events() in memory_promotion.py; Commit acb15b89 applied with FK columns

  PROMPTS P100971 [ ] [feature] [in-progress] [0] — Add work item table columns: name, desc, prompts count, commits count, last update date
    Requirements: Display work items as rows with: name, desc, prompts, commits, date columns; Support sorting by prompts, commits, or date; Show last update timestamp (yymmddhhm format)
    Deliveries: Added computed columns in route_work_items.py list endpoint calculating prompt_count and commit_count; Modified _renderWiPanel in entities.js to display new columns in table header; Commit 9a68574a applied

  PROMPTS P100977 [ ] [feature] [in-progress] [0] — Add sticky headers, AI tag suggestions, and approval workflow for work items
    Requirements: Make column headers sticky during scroll; Show AI tag suggestions below each work item; Implement approve (✓) and remove (×) for suggested tags
    Deliveries: Added position:sticky to all sortable <th> in hdr() with z-index:1; Added suggestion rows showing AI tag with approval UI; Implemented PATCH handlers for tag_id approval and ai_tag_id removal; Commit 896e88b5 applied

  PROMPTS P101006 [ ] [feature] [in-progress] [0] — Add creator, updater, and timestamp columns to mem_ai_work_items
    Requirements: Add creator column (user name if user-created, 'ai' if AI-created); Add updater column tracking last modifier; Reorder columns: project_id after client_id, timestamps last
    Deliveries: Migration m026 applied with planner_tags cleanup; Updated column order in mem_ai_work_items; Added creator and updater tracking in memory modules; Commit a5807126 applied

  PROMPTS P101007 [ ] [feature] [in-progress] [0] — Plan feature snapshot merge layer combining planner_tags with work_items
    Requirements: Remove summary, design, embedding columns from planner_tags (redundant); Clarify 'extra' column usage; Design mem_ai_feature_snapshot layer merging tags and work items
    Deliveries: Identified summary, design, embedding, extra as candidates for removal; Planned feature_snapshot as separate table with AI-generated content; Commit c490590b applied

  PROMPTS P101008 [ ] [feature] [in-progress] [0] — Remove unused columns from planner_tags and simplify storage
    Requirements: Drop summary, design, embedding, extra from planner_tags; Verify API returns only clean columns
    Deliveries: Migration m027 applied dropping unused columns; Updated memory_files.py render_feature_claude_md and related methods; API now returns: name, status, description, creator, requirements, action_items, updater; Commit cd4f2fb9 applied

  PROMPTS P101009 [ ] [feature] [in-progress] [0] — Add deliveries column to planner_tags with category and type selection
    Requirements: Add deliveries JSONB column after action_items; Support user selection from mng_deliveries table; Deliveries include: code (python/js/c#), document (md/doc), architect design (visio), ppt
    Deliveries: Designed deliveries schema mapping to mng_deliveries static lookup table; Planned UI selection interface for delivery types

  PROMPTS P101011 [ ] [feature] [in-progress] [0] — Create mem_ai_feature_snapshot final stage merging requirements with work items
    Requirements: Create mem_ai_feature_snapshot table merging user requirements and work items; Include summary, use cases, delivery types (code stack, document, architecture, ppt); Each use case has type (bug/feature/task) and delivery type
    Deliveries: Table designed with use-case generation and delivery mapping; Feature snapshot will serve as input to workflows (developer, tester, reviewer)

  PROMPTS P101012 [ ] [feature] [in-progress] [0] — Implement mem_ai_feature_snapshot with use-case scoring and delivery mapping
    Requirements: Implement feature snapshot with use-case generation and scoring; Map deliveries from planned_tags to snapshot; Generate via Haiku with feature_snapshot_v2 prompt
    Deliveries: Migration m029_feature_snapshot() added to db_migrations.py; mem_ai_feature_snapshot table added with 3 indexes in db_schema.sql; New prompt backend/prompts/memory/feature_snapshot_v2.md created; Added feature_snapshot_v2 to prompts.yaml config; Commit 9339bcf3 applied

  PROMPTS P101014 [ ] [feature] [in-progress] [0] — Implement dashboard tab and multi-entry pipeline execution
    Requirements: Create new dashboard tab with workflow visibility; Enable pipeline run from Planner, Docs, or Chat directly; Show all flow execution history and metrics
    Deliveries: Dashboard tab design planned separate from Planner; Pipeline execution entry points identified: Planner tab, Docs (where features exist), Chat interface

  PROMPTS P100914 [ ] [bug] [in-progress] [0] — Fix Planner tab issues: lifecycle tags, AI bug counters, drag-drop nesting
    Requirements: Clarify Lifecycle tagging purpose; Show counter updates for bug suggestions; Display AI suggested bugs under ai_suggestion with suggested tag; Fix drag-drop for nesting and merging
    Deliveries: Commit fc265cbe applied with system docs and memory updates

  PROMPTS P100917 [ ] [bug] [in-progress] [0] — Remove Lifecycle tags from bugs, features, and tasks
    Requirements: Remove Lifecycle tags from all work item types
    Deliveries: Commit 80a905d7 applied with system context and memory updates

  PROMPTS P100949 [ ] [bug] [in-progress] [0] — Fix drag-drop hover marking, link persistence, detail access, and work item merge
    Requirements: Fix all hover tags being marked (not just target tag); Show link immediately without page refresh; Access work item details when nested under tag; Implement work item merge with rollback and merge_id tracking
    Deliveries: Identified drag-drop over-marking issue; Planned immediate link visibility fix; Designed merge with version history and undo capability

  PROMPTS P100950 [ ] [bug] [in-progress] [0] — Fix work item not appearing under parent after drag-drop
    Requirements: Work item should appear under tag after drop and persist on page reload
    Deliveries: Root cause: _loadTagLinkedWorkItems filtered by tag's category instead of all items; Fixed category filter in api.workItems.list() call in entities.js; Commit cc038181 applied with system context updates

  PROMPTS P100961 [ ] [bug] [in-progress] [0] — Verify mem_mrr_commits_code database population with full_symbol column
    Requirements: Ensure mem_mrr_commits_code is populated on every commit; Include commit_short_hash and full_symbol generated column
    Deliveries: Added commit_short_hash column; Verified full_symbol generated column with 19 total columns; Commit 313c7257, 9cc59b6e, 741653e1 applied

  PROMPTS P100974 [ ] [bug] [in-progress] [0] — Improve work item table header clarity and column spacing
    Requirements: Widen columns (38px too narrow); Add visual separation in header; Increase text readability
    Deliveries: Increased column widths from 38px; Added header background color and padding; Improved label clarity in _renderWiPanel header in entities.js; Commit 63d0fbbc applied

  PROMPTS P100976 [ ] [bug] [in-progress] [0] — Wire up work item deletion handler for × dismiss button
    Requirements: Implement missing window._wiPanelDelete handler for × button; Confirm deletion before removing work item row
    Deliveries: Added window._wiPanelDelete function in _renderWiPanel calling api.workItems.delete(); Confirmation dialog before deletion; Commit 05d0f28a applied

  PROMPTS P100985 [ ] [bug] [in-progress] [0] — Fix work item ordering, populate prompts and commits counts, clarify extraction
    Requirements: Explain why #20006 appeared as last updated; Show work items with prompts and commits attached; Verify extraction pipeline working
    Deliveries: Fixed ordering: changed from seq_num DESC (null-first) to created_at DESC in route_work_items.py; Clarified event-to-work-item extraction via memory_promotion.py MemoryPromotion class; Commit caeaffc4 applied with ordering fix

  PROMPTS P100864 [ ] [task] [in-progress] [0] — Define workflow system design comparing specrails, paperclip, and current YAML approach
    Requirements: Create roles (web developer, AWS architect) similar to specrails agents; Compare with paperclip integration; Define workflow engine design
    Deliveries: Analyzed specrails Claude Code agent system with 12 specialized prompts; Reviewed current YAML-based workflow tab; Provided design proposal for role-based workflow system

  PROMPTS P100865 [ ] [task] [in-progress] [0] — Explain Run Pipeline feature and merge with workflow engine
    Requirements: Locate default pipeline configuration in Planner tab; Re-enable parent-child support for work items; Link pipeline execution to workflow engine
    Deliveries: Located hardcoded 4-stage pipeline in work_item_pipeline.py (PM→Architect→Developer→Reviewer); Identified that pipeline calls Anthropic API directly, separate from graph workflow engine; Explained POST /work-items/{id} endpoint triggering pipeline

  PROMPTS P100916 [ ] [task] [in-progress] [0] — Evaluate relevance of Lifecycle tags in work item management
    Requirements: Assess whether Lifecycle tags are needed
    Deliveries: Commit f341693a applied with system files and memory updates

  PROMPTS P100960 [ ] [task] [in-progress] [0] — Design commit-to-tag extraction flow aggregating commits across code symbols
    Requirements: Extract commits linked via pr_tags_map where related_type=commit; Show commit aggregation across files and symbols; Aggregate commit statistics (total lines, files changed)
    Deliveries: Designed extraction flow from pr_tags_map to commits to code symbols; Outlined aggregation logic across multiple commits

  PROMPTS P100962 [ ] [task] [in-progress] [0] — Rename memory modules to consistent memory_*.py naming convention
    Requirements: Standardize memory module naming; Update all import references
    Deliveries: Deleted mem_embeddings.py, renamed mem_sessions.py to memory_sessions.py; Updated 11 callers across 7 files in route_chat.py and others; Updated __init__.py documentation with 9 current modules; Commit ccec6af9 applied

  PROMPTS P100963 [ ] [task] [in-progress] [0] — Trace and document commit processing prompts and embedding workflow
    Requirements: Identify all prompts used in commit update pipeline; Document embedding and extraction flow
    Deliveries: Traced commit pipeline through process_commit in memory_embedding.py; Identified PromptLoader initialization in database.py refactoring; Commits e0c5a0ee, d4bc5875 applied with prompt system updates

  PROMPTS P100964 [ ] [task] [in-progress] [0] — Explain commit statistics linkage to work items with prompt and row tracking
    Requirements: Document connection between commit data and work items; Show how to track prompts/commits/rows per work item (e.g., auth)
    Deliveries: Mapped linkage chain: session_tags → mem_mrr_commits → mem_mrr_commits_code → mem_ai_work_items; Explained mem_ai_tags linking work items to commits; Commit 187d0a84 applied

  PROMPTS P100969 [ ] [task] [in-progress] [0] — Assess cost and frequency of mem_mrr_commits_code population
    Requirements: Verify mem_mrr_commits_code population per commit; Determine cost of per-class/method extraction
    Deliveries: Cost assessment: ~10ms CPU per commit, $0.003-0.004 per commit max; Identified tuning knobs: min_lines threshold, batch processing; Commits 82217a26, 09b5ca11 applied

  PROMPTS P100973 [ ] [task] [in-progress] [0] — Add sticky column headers and confirm work item table in lower Planner panel
    Requirements: Verify work item columns added to Work items tab (lower screen) in Planner; Ensure headers are sticky during scroll
    Deliveries: Confirmed _renderWiPanel changes in entities.js; Added sticky positioning to table headers; Commit 615919ef applied

  PROMPTS P101013 [ ] [task] [in-progress] [0] — Improve workflow visibility and pipeline management capabilities
    Requirements: Improve point 4: manage separate prompt files for user visibility; Improve point 5: current single workflow, system started as prompt management; Provide more visibility on all flows
    Deliveries: Analyzed aicli as shared AI memory platform for software development; Reviewed core problem: AI starts each session with zero context; Identified workflow system strengths and improvement areas; Commit 459e229c applied

---

## **user-client-management** · 26/03/10-01:14 [ ] (claude)
> Type: new
> Total: 37 prompts
> User tags:
> AI existing:
> AI new:
> Summary: User authentication, client management, multi-project support, and access control
> Requirements: Confirm tag creation scope in UI; Add parent_id support to database and API; Support MCP in project setup flow for Claude CLI, Claude Code, Cursor, OpenAI, DeepSeek, Gemini, Grok; Enable API-based tools to understand MCP config; Link recent commits to prompts; fix missing prompt associations
> Deliveries: [task|in-progress|0] Clarified tag creation behavior in chat picker vs. Planner; [feature|in-progress|0] Implemented parent_id hierarchy for entity values in backend; [feature|in-progress|0] Set up MCP server auto-configuration for multi-IDE support; [bug|in-progress|0] Fixed commit log sync to Phase 5 processing for prompt linking; [task|in-progress|0] Confirmed MCP server status and future session integration; [task|in-progress|0] Analyzed Claude Agent SDK for multi-agent use case applicability; [task|in-progress|0] Reviewed user-client-project-user relationship and memory mechanism

  PROMPTS P100821 [ ] [feature] [in-progress] [0] — Implemented parent_id hierarchy for entity values in backend
    Requirements: Add parent_id support to database and API
    Deliveries: database.py: Added parent_id INTEGER column with FK reference; entities.py: Updated ValueCreate/ValuePatch/SELECT/INSERT/PATCH handlers; tagCache.js: Added getCacheRoots() and getCacheChildren() helpers without extra DB calls

  PROMPTS P100843 [ ] [feature] [in-progress] [0] — Set up MCP server auto-configuration for multi-IDE support
    Requirements: Support MCP in project setup flow for Claude CLI, Claude Code, Cursor, OpenAI, DeepSeek, Gemini, Grok; Enable API-based tools to understand MCP config
    Deliveries: Fixed .mcp.json path typo; .cursor/mcp.json unified to args-based format; Created automated IDE detection and config generation in new project flow

  PROMPTS P101032 [ ] [feature] [in-progress] [0] — Refactored user_id to INT and added updated_at to all mirror tables
    Requirements: Change user_id from string to int; Add updated_at to mirror tables and event tables; Position user_id after project_id; Preserve created_at and use updated_at for change tracking
    Deliveries: db_migrations.py: Migration m051 completed; mng_users.id: SERIAL INT PK, old UUID as uuid_id VARCHAR(36); added updated_at to: mng_users, mng_clients, mem_mrr_* tables, mem_ai_events, mem_ai_project_facts, mem_pipeline_runs, planner_tags; added user_id INT to all mirror tables and planner_tags; changed mem_ai_events is_system to event_system

  PROMPTS P101033 [ ] [feature] [in-progress] [0] — Reorganized all 18 tables with correct column ordering per requirements
    Requirements: Reorder columns: id→client_id→project_id→user_id→data→created_at→updated_at→embedding; Remove committed_at from mem_mrr_commits; Ensure embedding always last if present
    Deliveries: db_migrations.py: Migration m052 rebuilt 18 tables with rename _old pattern; All tables now follow order: id, client_id, project_id, user_id, business columns, created_at, updated_at, embedding; removed committed_at from mem_mrr_commits (git timestamp preserved in created_at via COALESCE); moved mem_ai_events.event_system after event_type

  PROMPTS P100906 [ ] [feature] [in-progress] [0] — Added missing embedding columns to project_facts and work_items
    Requirements: Add embedding to mem_ai_project_facts and mem_ai_work_items; Update MCP server to expose all memory layers
    Deliveries: No code shown but commit references embedding additions; MCP server updated to serve all layers for LLM consumption

  PROMPTS P100936 [ ] [feature] [in-progress] [0] — Planned restructuring of process items, feature snapshots, and work_item event linking
    Requirements: Merge planner_tags into feature_snapshot concept; Link work_items to events storing prompts/session data; Ensure 3-layer flow: mirrors→events→work_items; Fix project_facts
    Deliveries: Planned refactor but no code changes yet

  PROMPTS P101021 [ ] [feature] [in-progress] [0] — Cleaned event tags to remove system metadata and keep only user tags
    Requirements: Remove system tags (llm, event, chunk_type, commit_hash, etc) from mem_ai_events; Keep only user/business tags (phase, feature, bug, source); Merge mirror table tags into event tags
    Deliveries: route_admin.py: Added backfill_event_tags(+191/-0) function; Pass 0: Fixed 6 corrupt session_summary events with JSON array tags → reset to {}; Pass 1: Stripped system metadata from 1441 events (llm, event, chunk_type, commit_hash, commit_msg, file, files, languages, symbols, rows_changed removed); Pass 2: Backfilled 1440 commit events with {} tags from mem_mrr_commits.tags; Current state: Only {phase, feature, bug, source} tags remain

  PROMPTS P101027 [ ] [feature] [in-progress] [0] — Added session visibility and formatting to Chat and History views
    Requirements: Chat: Show sessions on left like history, display session_id/phase/source; History: Add YY/MM/DD-HH:MM timestamps to prompts, add tags display, allow tag editing; Show last 5 session digits on left, full UUID when clicked
    Deliveries: Chat left sidebar: Each session shows 'CLI · development · (ab3f9)' with full tooltip; Chat sticky header: Full session UUID with phase chip and copy button; Chat YOU messages: Format 'YOU — YY/MM/DD-HH:MM' with timestamp; History prompts: Added YY/MM/DD-HH:MM format + all tags display + tag add/edit UI; Session display: Last 5 chars in monospace on list, full UUID at top

  PROMPTS P100844 [ ] [bug] [in-progress] [0] — Fixed commit log sync to Phase 5 processing for prompt linking
    Requirements: Link recent commits to prompts; fix missing prompt associations
    Deliveries: Identified root cause: auto_commit_push.sh hook never triggered /entities/events/sync Phase 5; Modified hook to pass session_id to POST /git/{project}/commit-push; Enhanced git router to call Phase 5 after each commit

  PROMPTS P100947 [ ] [bug] [in-progress] [0] — Fixed ReferenceError for _plannerSelectAiSubtype and _plannerSync initialization
    Requirements: Remove broken reference causing initialization crash
    Deliveries: Removed single problematic line that prevented window._plannerSync assignment

  PROMPTS P100953 [ ] [bug] [in-progress] [0] — Fixed SQL errors in route_work_items for unlinked work items query
    Requirements: Fix _SQL_UNLINKED_WORK_ITEMS execution at line 249; Fix missing columns in SELECT at line 288
    Deliveries: route_work_items line 249/288: Fixed SQL for loading work_items; Confirmed backend processing completes (60+ seconds on Railway expected)

  PROMPTS P100966 [ ] [bug] [in-progress] [0] — Added missing ai_tags JSONB column to mem_ai_work_items table
    Requirements: Fix column w.ai_tags does not exist error at line 331
    Deliveries: database.py: Added migration _DDL_WORK_ITEMS_ALTERS with ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS ai_tags JSONB DEFAULT '{}'; Registered as work_items_alters_v1 in schema version tracking; Applied to live DB without restart

  PROMPTS P100823 [ ] [bug] [in-progress] [0] — Fixed port binding issues and orphaned uvicorn process cleanup
    Requirements: Prevent exit code 1 when port 127.0.0.1:8000 already in use
    Deliveries: Added freePort() function to check port, kill holder via lsof -ti tcp:8000 | xargs kill -9; Runs on every app start before uvicorn spawn; Waits up to 2s for OS to confirm port is free; Handles orphaned uvicorn from Electron force-quit

  PROMPTS P100824 [ ] [bug] [in-progress] [0] — Fixed tag persistence across session switches in UI
    Requirements: Tags disappear when viewing another session then returning; Ensure tags stored in all session data; Implement session tag recovery endpoint
    Deliveries: entities.py: Added GET /entities/session-tags?session_id=X&project=Y endpoint; Queries event_tags_{p} joined to events, values, categories; api.js: Added getEntitySessionTags(sessionId, project) to api.entities; chat.js _chatLoad: After _restoreTagBar, now calls _restoreSessionTags to reload tags

  PROMPTS P100908 [ ] [bug] [in-progress] [0] — Fixed embedding issues across memory tables
    Requirements: Correct embedding presence in all tables
    Deliveries: Executed fixes for embedding columns

  PROMPTS P100922 [ ] [bug] [in-progress] [0] — Fixed UndefinedColumn lifecycle in route_entities and removed PHASE
    Requirements: Fix psycopg2.errors.UndefinedColumn: column t.lifecycle at line 359; Remove unused PHASE column; Optimize pagination and commit loading
    Deliveries: route_entities: Removed reference to t.lifecycle column; Removed unused PHASE column from entities table; Optimized queries for faster commit loading

  PROMPTS P100923 [ ] [bug] [in-progress] [0] — Fixed UndefinedColumn work_item_id in route_work_items
    Requirements: Fix psycopg2.errors.UndefinedColumn: column p.work_item_id at line 351
    Deliveries: route_work_items: Fixed query referencing non-existent p.work_item_id; Corrected planner_tags/work_items join logic

  PROMPTS P100925 [ ] [bug] [in-progress] [0] — Fixed JSONB merge operator in batch commit upsert
    Requirements: Fix execute_values error in route_history line 441 commit sync
    Deliveries: route_history: Fixed _SQL_BATCH_UPSERT to cast tags as JSONB before || merge

  PROMPTS P100943 [ ] [bug] [in-progress] [0] — Fixed JSONB concatenation operator in batch commit upsert
    Requirements: Fix execute_values error at route_history line 470
    Deliveries: route_history line 466: Changed tags = mem_mrr_commits.tags || EXCLUDED.tags to cast EXCLUDED.tags::jsonb; Fixed type mismatch: jsonb || text now becomes jsonb || jsonb

  PROMPTS P100944 [ ] [bug] [in-progress] [0] — Resolved duplicate key conflict in commit upsert
    Requirements: Fix ON CONFLICT DO UPDATE duplicate rows error; Ensure all 364 commits load correctly
    Deliveries: route_history: Fixed three issues in commit sync (JSONB type, duplicate constraint, tag merging); Confirmed 364 unique commit hashes out of 683 entries expected to import

  PROMPTS P100820 [ ] [task] [in-progress] [0] — Clarified tag creation behavior in chat picker vs. Planner
    Requirements: Confirm tag creation scope in UI
    Deliveries: Documented that chat picker creates root-level tags only; Planner UI enables nested sub-tags with +child button

  PROMPTS P100863 [ ] [task] [in-progress] [0] — Confirmed MCP server status and future session integration
    Requirements: Confirm MCP usage in current session
    Deliveries: Verified MCP not active in this session (using direct HTTP); Confirmed .mcp.json ready at project root for next Claude Code session

  PROMPTS P100872 [ ] [task] [in-progress] [0] — Analyzed Claude Agent SDK for multi-agent use case applicability
    Requirements: Evaluate if Claude Agent SDK suits PM→Dev→Tester→Reviewer pipeline
    Deliveries: Documented Claude Agent SDK capabilities (tools, subagents, state management); Compared against current architecture

  PROMPTS P100887 [ ] [task] [in-progress] [0] — Reviewed user-client-project-user relationship and memory mechanism
    Requirements: Model clients with multiple users; Verify memory_items and project_facts update behavior
    Deliveries: No code changes recorded

  PROMPTS P100939 [ ] [task] [in-progress] [0] — Verified prompt linking after client_id schema fix
    Requirements: Validate schema changes work correctly
    Deliveries: System context and memory documentation updated per fdbcd8ea

  PROMPTS P100940 [ ] [task] [in-progress] [0] — Final verification of schema and data integrity
    Requirements: Confirm all changes stable
    Deliveries: No code changes; verification completed

  PROMPTS P100946 [ ] [task] [in-progress] [0] — Audited mem_ai_work_items columns and defined proper alignment
    Requirements: Clarify source_session_id usage; Define purpose of content/summary/requirements/tags columns; Plan work_items as merge of all events filtered by status
    Deliveries: mem_ai_work_items: Documented all 20 columns with purposes (id, client_id, project_id, user_id, seq_num, created_at, updated_at, embedding, ai_name, ai_category, ai_desc, status, source_session_id, source_event_id, ai_tags, content, summery, requirements, merged_into, start_date); Identified that content/summery/requirements should be extracted from events and planned_tags; Confirmed ai_tags merged from event_tags tables and mem_ai_events

  PROMPTS P100829 [ ] [task] [in-progress] [0] — Greeting and status check on aicli project
    Requirements: Acknowledge user and assess project status
    Deliveries: Confirmed recent work on AI suggestions, session tags, planner UI, port fixes

  PROMPTS P100901 [ ] [task] [in-progress] [0] — Test prompt after migration m051/m052
    Requirements: Verify migrations applied successfully
    Deliveries: No code changes; test confirmation

  PROMPTS P100903 [ ] [task] [in-progress] [0] — Test prompt after mem_ai cleanup
    Requirements: Verify cleanup of mem_ai tables
    Deliveries: No code changes; test confirmation

  PROMPTS P100911 [ ] [task] [in-progress] [0] — Investigated backend/workspace folder usage
    Requirements: Determine if workspace folder is still used
    Deliveries: Assessment completed

  PROMPTS P100912 [ ] [task] [in-progress] [0] — Deleted unused backend/workspace folder
    Requirements: Remove workspace folder if not in use
    Deliveries: Workspace folder removed from backend

  PROMPTS P100937 [ ] [task] [in-progress] [0] — Test prompt after fix
    Requirements: Verify previous fixes
    Deliveries: Test confirmation

  PROMPTS P100952 [ ] [task] [in-progress] [0] — Synced memory items with updated project data via /memory endpoint
    Requirements: Update all memory files with current project state
    Deliveries: Generated: claude/MEMORY.md, claude/CLAUDE.md, cursor/rules.md, aicli/context.md, aicli/copilot.md; Copied to code root: CLAUDE.md, MEMORY.md, .cursor/rules/aicli.mdrules, .github/copilot-instructions.md, .ai/rules.md; Synthesized from 211 history rows incremental since 2026-04-07T01:11:00Z

  PROMPTS P100995 [ ] [task] [in-progress] [0] — Investigated work_items without prompt links and backfilled commit sources
    Requirements: Understand why work_items #20436-20443 have no linked prompts; Verify memory /memory extraction includes recent items
    Deliveries: Identified pattern: recent items (#20436-#20443) sourced from commit backfill (2026-04-07) with session=None (correct); Memory ran and extracted new work_item #20443; Documented why historical commits have no CLI session association

  PROMPTS P101005 [ ] [task] [in-progress] [0] — Audited planner_tags schema for redundant/unused columns
    Requirements: Identify unnecessary columns: seq_num, source vs creator, duplicate status fields, code_summary; Simplify user-managed tag structure
    Deliveries: Identified seq_num: always null, DROP; Identified source + creator redundancy: DROP source, keep creator; Identified duplicate status columns: clarified one needed; Identified code_summary: belongs in work_items not tags; Documented user-manageable fields should be: short_desc, full_desc, requirements, acceptance_criteria, summary, action_items, design

  PROMPTS P101026 [ ] [task] [in-progress] [0] — Test hook-log functionality after m050 migration
    Requirements: Verify hook logging works post-migration
    Deliveries: Test confirmation

---

## **general-commits** · 26/04/12-00:03 [+] (auto)
> Type: existing
> Total: 7 commits
> User tags:
> AI existing:
> AI new:
> Summary: 7 commits updating: backend/core/db_migrations.py, backend/memory/memory_planner.py, backend/memory/memory_promotion.py, backend/memory/memory_tagging.py, backend/routers/route_projects.py, backend/routers/route_work_items.py… | classes: MemoryFeatureSnapshot, MemoryPlanner, MemoryPromotion, MemoryTagging
> Deliveries: [task|completed|5] Refactor work item AI columns and update memory promotion logic; [feature|completed|5] Add embedding and memory search improvements to promotion logic; [feature|completed|5] Add deliveries feature and update tag management endpoints; [feature|completed|5] Add feature snapshot memory system with LLM integration; [feature|completed|5] Add pipeline run logging and workflow execution endpoints; [feature|completed|5] Add PostgreSQL database maintenance and cleaning utilities; [task|completed|5] Add index on prompts source_id for query optimization

  COMMITS C200624 [+] [feature] [completed] [5] — Add embedding and memory search improvements to promotion logic
    Deliveries: backend/agents/tools/tool_memory.py: _handle_search_memory (+21/-0); backend/memory/memory_promotion.py: MemoryPromotion (+10/-1); backend/memory/memory_promotion.py: _embed_work_item (+19/-0); backend/memory/memory_promotion.py: MemoryPromotion.promote_work_item (+6/-0); backend/memory/memory_promotion.py: MemoryPromotion.extract_work_items_from_events (+4/-1)

  COMMITS C200625 [+] [feature] [completed] [5] — Add deliveries feature and update tag management endpoints
    Deliveries: backend/core/db_migrations.py: m028_add_deliveries (+30/-0); backend/routers/route_tags.py: TagUpdate (+1/-0); backend/routers/route_tags.py: DeliveryCreate (+5/-0); backend/routers/route_tags.py: CategoryCreate (+0/-1); backend/routers/route_tags.py: _row_to_tag (+8/-6)

  COMMITS C200626 [+] [feature] [completed] [5] — Add feature snapshot memory system with LLM integration
    Deliveries: backend/core/db_migrations.py: m029_feature_snapshot (+44/-0); backend/memory/memory_feature_snapshot.py: MemoryFeatureSnapshot (+435/-0); backend/memory/memory_feature_snapshot.py: _parse_json (+9/-0); backend/memory/memory_feature_snapshot.py: _slugify (+2/-0); backend/memory/memory_feature_snapshot.py: _call_llm (+21/-0)

  COMMITS C200627 [+] [feature] [completed] [5] — Add pipeline run logging and workflow execution endpoints
    Deliveries: backend/core/db_migrations.py: m030_pipeline_runs (+44/-0); backend/core/pipeline_log.py: pipeline_run_sync (+14/-0); backend/core/pipeline_log.py: _insert_run (+20/-0); backend/core/pipeline_log.py: _finish_run (+25/-0); backend/core/pipeline_log.py: pipeline_run (+18/-0)

  COMMITS C200628 [+] [feature] [completed] [5] — Add PostgreSQL database maintenance and cleaning utilities
    Deliveries: backend/data/clean_pg_db.py: _raw_conn (+8/-0); backend/data/clean_pg_db.py: _bytes_to_mb (+2/-0); backend/data/clean_pg_db.py: run_maintenance (+170/-0); backend/data/clean_pg_db.py: run_maintenance_async (+4/-0); backend/data/clean_pg_db.py: _cli (+34/-0)

  COMMITS C200623 [+] [task] [completed] [5] — Refactor work item AI columns and update memory promotion logic
    Deliveries: backend/core/db_migrations.py: m025_rename_work_item_ai_columns (+15/-0); backend/memory/memory_planner.py: MemoryPlanner (+5/-5); backend/memory/memory_planner.py: MemoryPlanner._build_user_message (+3/-3); backend/memory/memory_planner.py: MemoryPlanner._write_document (+2/-2); backend/memory/memory_promotion.py: MemoryPromotion (+93/-20)

  COMMITS C200629 [+] [task] [completed] [5] — Add index on prompts source_id for query optimization
    Deliveries: backend/core/db_migrations.py: m050_prompts_source_id_index (+21/-0)
