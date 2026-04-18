# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items` to merge approved items into use cases.

## **discovery** · 26/03/13-17:44 [ ] (claude)
> Type: existing
> Total: 8 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Discovery, architecture review, and system explanation
> Requirements: explain aicli system to non-technical audience; use MCP tool to explain aicli project; use MCP tool to explain code functionality; review architecture for multi-client/multi-project scenarios; advise on free/unregistered client management

  PROMPTS P101273 [ ] [task] [in-progress] [0] — Explained aicli as shared AI memory platform for developers
    Requirements: explain aicli system to non-technical audience
    Deliveries: described core problem (multi-AI tools lose context) and solution (unified memory across all tools) in df7f6829

  PROMPTS P101310 [ ] [task] [in-progress] [0] — Request to use MCP tool to explain project (no response)
    Requirements: use MCP tool to explain aicli project

  PROMPTS P101313 [ ] [task] [in-progress] [0] — Explained aicli code architecture: 5-layer memory system
    Requirements: use MCP tool to explain code functionality
    Deliveries: described 5-layer memory system (/memory command synthesis) across conversation→session→project→history→templates layers

  PROMPTS P101324 [ ] [task] [in-progress] [0] — Architectural review: 3-layer client/project tables at scale
    Requirements: review architecture for multi-client/multi-project scenarios; advise on free/unregistered client management
    Deliveries: identified table proliferation concern (120 client + 2000 project tables at 20×10 scale); noted current 3-tier naming and mng_→cl_local_ seeding pattern works for single-tenant

  PROMPTS P101329 [ ] [task] [in-progress] [0] — Request to verify memory_items/project_facts update mechanism (no response)
    Requirements: confirm users are part of client model; verify memory_items and project_facts tables are updated per design spec

  PROMPTS P101396 [ ] [task] [in-progress] [0] — Complete memory pipeline flow analysis (mirror→project_facts→work_items)
    Requirements: describe mirror table triggers, LLM prompts, and column usage; analyze project_facts and work_items stages; map relevant scores (0-5) for all columns
    Deliveries: documented mirror tables as pure capture in 7c2992ce; analyzed column responsibility (User/LLM/Trigger) and relevance ratings; confirmed 60-second migration time from diagnostic

  PROMPTS P101397 [ ] [task] [in-progress] [0] — Full memory pipeline analysis with relevance scoring per column
    Requirements: complete flow analysis from mirror tables through project_facts to work_items; include LLM prompts and trigger conditions; score column relevance 0-5
    Deliveries: documented Stage 1 mirror tables (mem_mrr_prompts, mem_mrr_commits) with trigger conditions and column relevance in 3d2b5555; mapped LLM-used prompts and calculated columns across all stages

  PROMPTS P101399 [ ] [task] [in-progress] [0] — Updated aicli_memory.md with complete layer documentation
    Requirements: reference existing aicli_memory.md file; document all 4 layers with responsible party and relevance ratings; update mem_mrr_commits, mem_ai_events, mem_ai_work_items columns
    Deliveries: updated aicli_memory.md at project root in d37c3057 with per-column Responsible and Relevance (0-5) ratings; updated mem_mrr_commits to reflect dropped diff_summary/diff_details and actual tags columns; documented mem_ai_events.importance as LLM-scored 0-10; fully documented mem_ai_work_items structure

---

## **ui-ux-improvements** · 26/03/10-00:11 [ ] (claude)
> Type: new
> Total: 48 prompts
> User tags:
> AI existing:
> AI new:
> Summary: UI/UX fixes: visibility, loading, layout, drag-drop
> Requirements: UI not loading, bind address 127.0.0.1:8000 error; Port 8000 still bound, cannot see data on project click; Improve action visibility in planner UI; Enable archived item reactivation; Add 3-dot menu for task details (remark, due_date, created, archived)

  PROMPTS P101264 [ ] [feature] [in-progress] [0] — Add action button visibility, archive reactivation, details modal with 3-dot menu
    Requirements: Improve action visibility in planner UI; Enable archived item reactivation; Add 3-dot menu for task details (remark, due_date, created, archived); Add sub-tags window to keep main screen clean; Add tags to new chats
    Deliveries: Confirmed no syntax errors in codebase

  PROMPTS P101289 [ ] [feature] [in-progress] [0] — Persist phase changes per session, add phase filter to commits
    Requirements: Phase changes not saving; Phase doesn't update on session switch; Add phase filter to commits (display only), same as chat filter
    Deliveries: Removed _sessionId = null from phase change handler; Added PATCH /chat/sessions/{id}/tags endpoint; api.patchSessionTags(id, {phase}) called on phase change; PUT /history/session-tags persists globally

  PROMPTS P101383 [ ] [feature] [in-progress] [0] — Show full prompt and LLM response in history, add copy text ability
    Requirements: History shows small text instead of full prompt/response; Add copy text functionality to UI

  PROMPTS P101390 [ ] [feature] [in-progress] [0] — Enable drag-drop work items under tags, resize bottom panel
    Requirements: Drag work_item to remove from bottom and move under tag; Resize bottom panel height via line separator
    Deliveries: Verified key sections of drag handler

  PROMPTS P101391 [ ] [feature] [in-progress] [0] — Fix drag-drop hover state, show linked immediately, enable details on linked items, implement merge
    Requirements: Multiple tabs marked on hover (only target should show); Dropped item not visible until page reload; Cannot see details when work_item under tag; Add merge functionality with rollback via merge_id

  PROMPTS P101413 [ ] [feature] [in-progress] [0] — Add table columns: name, description, prompts count, commits count, last update date, sortable
    Requirements: Work_items display as rows with columns: name, desc, prompts, commits, date; Sortable by prompts, commits, or date
    Deliveries: Added column structure with draggable attribute on rows

  PROMPTS P101415 [ ] [feature] [in-progress] [0] — Add SQL column and update UI to show work_item table with counts
    Requirements: Add work_item table to bottom panel with metrics
    Deliveries: Backend: new SQL endpoints for work item list with counts; Frontend: _renderWiPanel with table structure; Restart backend for SQL changes

  PROMPTS P101419 [ ] [feature] [in-progress] [0] — Make table header sticky on scroll, add AI tag suggestions, run /memory
    Requirements: Header disappears on scroll; Add AI tag suggestions per work_item; Run /memory to update events/work_items; Show approval/removal for AI tags
    Deliveries: Added position:sticky;top:0;z-index:1 to all th cells; Each work_item row shows suggestion row when ai_tag_name present; Approve button calls PATCH with tag_id = ai_tag_id; Remove button calls PATCH with ai_tag_id = ''

  PROMPTS P101422 [ ] [feature] [in-progress] [0] — Show category:name format for tags, display user tags, rectangular button for delete
    Requirements: AI tags should show category:name (bug:auth, feature:dropbox); Show existing tags vs new suggestions in different colors; Display user tags alongside AI tags; Make × button rectangular like ✓
    Deliveries: Updated tag suggestion format to category:name; Added user tags retrieval and display; Color coding: AI_existing (color1) vs AI_new (color2) vs user (color3); Rectangular button shape for × delete

  PROMPTS P101424 [ ] [feature] [in-progress] [0] — Add section labels (AI, User) for tags, show even when empty
    Requirements: Need labels to identify tag type; AI and User sections must always show
    Deliveries: Added labeled rows for AI: and User:; Always display both sections regardless of content; Show '—' placeholder when no tags in User section

  PROMPTS P101465 [ ] [feature] [in-progress] [0] — Auto-update chat with latest prompts, add tag selection per prompt
    Requirements: UI changes not reflecting; Latest prompts from CLI not appearing in chat; Chat not auto-updating with new prompts; Add tag selection per prompt like History/Prompts
    Deliveries: Migration m050 fixed silent DB error in hook-log endpoint; All prompts now storing correctly; Added reload UI button in History tab (top-right); Chat view reflects latest prompts after reload

  PROMPTS P101466 [ ] [feature] [in-progress] [0] — Show timestamp per prompt, session ID on left and top, add tag selection
    Requirements: Timestamp missing next to YOU in history; Session ID not visible (left panel and top); Add per-prompt tag selection with existing user tags
    Deliveries: Session ID badge shows last 5 chars (…xxxxx) in left panel header; Right pane shows blue banner with full session ID + copy button; All tags per prompt (not just phase:) now displayed

  PROMPTS P101467 [ ] [feature] [in-progress] [0] — Show full session context in Chat tab header and per-message
    Requirements: Chat tab needs session ID visibility; Add timestamp YY/MM/DD-HH:MM to each prompt; Show all tags and option to add tags per prompt
    Deliveries: Session header shows CLI · phase · (last5chars) · entry count · date; Each prompt shows YOU — YY/MM/DD-HH:MM; Top of body shows full session ID banner with copy; Tag selection added per prompt

  PROMPTS P101469 [ ] [feature] [in-progress] [0] — Add Chat-specific visibility for session ID, timestamp, tags, and approval
    Requirements: Chat tab needs same visibility as History prompts; Each message needs timestamp YY/MM/DD-HH:MM; Add all tags and option to add tags per message; Left sidebar show last 5 session chars, top panel show full ID
    Deliveries: Left sidebar: CLI · development · (ab3f9) with tooltip full ID; Right panel sticky banner: full session ID + copy + phase chip; Each YOU message: YOU — YY/MM/DD-HH:MM format; All tags displayed with add option per message

  PROMPTS P101258 [ ] [bug] [in-progress] [0] — Backend healthy, frontend reload needed after uvicorn port conflict
    Requirements: UI not loading, bind address 127.0.0.1:8000 error
    Deliveries: Verified backend running, due_date column live in API; Confirmed entities.js and chat.js syntax valid; Identified stale uvicorn process (PID 86671)

  PROMPTS P101259 [ ] [bug] [in-progress] [0] — Kill stale backend process, restart dev server with npm script
    Requirements: Port 8000 still bound, cannot see data on project click
    Deliveries: Terminated old uvicorn process (PID 86671); Instructed npm run dev from ui/ directory with NODE_ENV=development

  PROMPTS P101288 [ ] [bug] [in-progress] [0] — Fix phase not persisting per session on app load and session switch
    Requirements: Phase shows 'required' on app load regardless of actual phase; Phase doesn't update when switching chat sessions
    Deliveries: Root cause: no code loaded last phase from DB on startup; Root cause: session.metadata.tags could be missing for old sessions; Root cause: PUT /history/session-tags never called on phase change; Fixed: load phase from DB on init, call PUT /history/session-tags on phase dropdown change

  PROMPTS P101290 [ ] [bug] [in-progress] [0] — Restore session-specific phases, fix history default to all, fix commit filter
    Requirements: Cannot change/update phase in Chat; Chat sessions not showing correct phase; History/Chat defaults to discovery instead of all phases; Commits filter disappears after change, shows wrong phases
    Deliveries: Restored _sessionId = null logic for phase-per-session; api.putSessionTags(project, {phase}) persists globally; On init: api.getSessionTags(project) pre-fills dropdown; Fixed session switch with _chatLoad using session.metadata.tags + _sessionCache fallback

  PROMPTS P101291 [ ] [bug] [in-progress] [0] — Fix phase loading and update for each session
    Requirements: Upload session doesn't show correct phase; Session switch doesn't update phase properly; Need phase per session visible and updatable
    Deliveries: Phase change listener no longer resets _sessionId = null; Phase change on existing session calls api.patchSessionTags(_sessionId, {phase}); Phase change on new chat updates _sessionTags.phase in memory; Endpoint PATCH /chat/sessions/{id}/tags verified live

  PROMPTS P101292 [ ] [bug] [in-progress] [0] — Mark all sessions missing phase with red ⚠, persist phase for CLI sessions
    Requirements: Red session flag not working correctly, unrelated to phase; CLI sessions not persisting phase changes
    Deliveries: Removed s.source === 'ui' condition, now ALL sessions without phase show red ⚠ badge; Removed red left border display limitation; PATCH /chat/sessions/{id}/tags now falls back to _system/session_phases.json for CLI sessions; No 404 thrown for non-existent session IDs

  PROMPTS P101293 [ ] [bug] [in-progress] [0] — Preserve session list order when phase changes
    Requirements: Session order changes on phase modification
    Deliveries: Backend patch_session_tags no longer updates updated_at on tag change; Frontend _loadSessions now sorts by created_at instead of updated_at

  PROMPTS P101312 [ ] [bug] [in-progress] [0] — Optimize project loading speed, fix PROJECT.md slow read
    Requirements: aiCli project not visible in recent/project list; Loading PROJECT.md takes >1 minute; Free Railway DB may be bottleneck
    Deliveries: Analyzed openProject function

  PROMPTS P101328 [ ] [bug] [in-progress] [0] — Fix project display in recent list, handle backend startup delay
    Requirements: aiCli in recent but not in projects list; Backend slow to load on startup
    Deliveries: Fixed _continueToApp to retry if projects load succeeds but returns empty

  PROMPTS P101357 [ ] [bug] [in-progress] [0] — Debug drag-drop and counter functionality not working
    Requirements: Drag and drop not functional; Counter not updating

  PROMPTS P101384 [ ] [bug] [in-progress] [0] — Fix history to show LLM response alongside prompt
    Requirements: History shows only prompt, no LLM response
    Deliveries: Verified hook-response saves LLM response to mem_mrr_prompts.response; Verified session-summary creates mem_ai_events entries; Verified memory and auto-detect-bugs hooks present; Both hook files (log_session_stop.sh) now identical and correct

  PROMPTS P101389 [ ] [bug] [in-progress] [0] — Fix JS reference errors blocking initialization
    Requirements: ReferenceError: _plannerSelectAiSubtype not defined; TypeError: window._plannerSync not a function
    Deliveries: Removed stray line causing init crash; window._plannerSync now properly assigned

  PROMPTS P101392 [ ] [bug] [in-progress] [0] — Fix work_item link persistence under tags
    Requirements: Dropped work_item not persisting under tag after reload
    Deliveries: Root cause: _loadTagLinkedWorkItems filtered by tag's category, not work_item category; Removed category filter from api.workItems.list({project}); Now fetches all work items for project without category restriction

  PROMPTS P101410 [ ] [bug] [in-progress] [0] — Fix tag property drawer crash when opening tag
    Requirements: Tag click doesn't show properties (works for work_items)
    Deliveries: Root cause: catName not in scope in _renderDrawer(); Fixed catName → v.category_name || _plannerState.selectedCatName; Fixed field name v.short_desc → v.description

  PROMPTS P101416 [ ] [bug] [in-progress] [0] — Improve table header clarity and spacing
    Requirements: Columns too narrow (38px), header lacks visual separation, text tiny
    Deliveries: Increased column widths; Added header background color for visual separation; Increased padding and font sizes in _renderWiPanel and hdr functions

  PROMPTS P101417 [ ] [bug] [in-progress] [0] — Fix date format to yy/mm/dd-hh:mm, remove non-work_item tags
    Requirements: Date format unclear; Tags under work_items (Shared-memory, billing) shouldn't display
    Deliveries: Changed date format to yy/mm/dd-hh:mm in fmtDate(); Updated _renderWiPanel to filter work item display; Added delete handler _wiPanelDelete for removing items

  PROMPTS P101418 [ ] [bug] [in-progress] [0] — Wire up delete button handler for work_item rows
    Requirements: Delete button (×) present but handler missing
    Deliveries: Defined window._wiPanelDelete function inside _renderWiPanel; Shows confirm dialog before deletion; Calls api.workItems.delete(id, proj); Removes from _wiPanelItems cache and re-renders

  PROMPTS P101420 [ ] [bug] [in-progress] [0] — Fix AI tag suggestions display and matching logic
    Requirements: AI suggestions not visible per row; Tag matching needs improvement
    Deliveries: Made sticky header persist on scroll; Fixed ai_tag_name field display in suggestion rows; Updated MemoryTagging.match_work_item_to_tags with better matching; Added vector search and Claude judge for candidate selection

  PROMPTS P101421 [ ] [bug] [in-progress] [0] — Fix work_item details drawer, compact tag layout, increase fonts, style delete button
    Requirements: Work_item details not loading on click; Tag suggestions too spread out; Font too small in Electron; Delete button (×) gray on gray, invisible; Date column cut off
    Deliveries: Added GET /work-items/{id} endpoint; _openWorkItemDrawer calls api.workItems.get directly; Tag suggestion uses inline-flex for compact layout; Bumped all font sizes for Electron visibility; Changed × to bold red color on gray background

  PROMPTS P101423 [ ] [bug] [in-progress] [0] — Fix table display to show all columns, restore column widths
    Requirements: Only first column (commits) visible, others cut off
    Deliveries: Updated colgroup column widths; Restored table-layout:fixed to prevent Name column expansion; Adjusted date column width to prevent overflow

  PROMPTS P101425 [ ] [bug] [in-progress] [0] — Add padding, fix date truncation, color-code tags, investigate missing AI suggestions
    Requirements: Left padding missing; Date truncated (yy:mm:dd-HH only); Need tag type colors: AI(EXIST)=green, AI(NEW)=red, USER=blue; Many work_items have no AI recommendations
    Deliveries: Added left padding to table; Fixed date display to full format; AI tag suggestions running in background with proper color coding; Matching logic improved with level 4 fallback when embedding fails

  PROMPTS P101436 [ ] [bug] [in-progress] [0] — Fix commit counter query to join via source_id, add NULLS LAST
    Requirements: Counter or prompts not showing; Work_items without events display incorrectly
    Deliveries: Root cause: 418/444 commits have event_id = NULL; Changed join from event_id to mem_ai_events.source_id → commit_short_hash; Added NULLS LAST to sort unlinked items to bottom

  PROMPTS P101457 [ ] [bug] [in-progress] [0] — Fix UI crashing, top screen empty after tag approval
    Requirements: Planner shows only work_items, no bug/category sections; Work_item disappears on tag approval but top screen stays empty
    Deliveries: Fixed import json missing in route_work_items.py; Removed stray conn.commit() outside with block; Improved level 4 fallback matching logic

  PROMPTS P101458 [ ] [bug] [in-progress] [0] — Fix Electron loading empty, resolve variable scope conflict
    Requirements: Electron loads empty page
    Deliveries: Fixed duplicate const cats declaration in _wiPanelCreateTag; Renamed second declaration to cacheCats to resolve scope conflict; Added database cleanup migration m031 for commits

  PROMPTS P101471 [ ] [bug] [in-progress] [0] — Fix chat session loading to show current session not stale from JSON
    Requirements: Chat loads old session initially, only updates after 15 seconds; Missing latest prompts on startup
    Deliveries: Sort fixed with limit=500, April first (newest) to March last (oldest); Total merged entries: 531 (389 DB + ~142 JSONL); Full history from March 9 to April 15 now visible

  PROMPTS P101472 [ ] [bug] [in-progress] [0] — Fix stale session ID on load, auto-select current session immediately
    Requirements: Chat loads with old session (7d89c79f...) instead of current (f664...); Takes 15 seconds to update to correct session
    Deliveries: _sessionId reset to null at start of renderChat(); _appliedEntities and _pendingEntities also reset; localStorage cache rendered without highlight (since _sessionId=null); After fetch completes, auto-selects current session

  PROMPTS P101473 [ ] [bug] [in-progress] [0] — Load current session synchronously on startup without delay
    Requirements: Chat loads stale session for 15 seconds before updating
    Deliveries: Flow: renderChat() → _sessionId=null → _loadSessions() → reads state.currentProject.dev_runtime_state.last_session_id synchronously; Sets _sessionId immediately without network call; Cache renders with correct session highlighted; Full fetch confirms/updates _sessionId after network completes

  PROMPTS P101267 [ ] [task] [in-progress] [0] — Explain tag bar location and approve/queue flow with visible chips
    Requirements: User confused about accept button location in Chat
    Deliveries: Documented tag bar location (thin bar below chat title); Explained chip interaction: ✓ to queue (pending/dashed blue), 💾 Save to confirm; Fixed overflow:hidden clipping wrapping chips to second line

  PROMPTS P101268 [ ] [task] [in-progress] [0] — Run /memory, clarify AI suggestions banner, show session source
    Requirements: Make UI clearer for AI suggestions with approval required; Show which session suggestion came from; Clarify Phase (required) is mandatory, not a session identifier
    Deliveries: Session label changed from 'Session:' to 'Phase:' in tag bar; AI suggestions now in dedicated amber banner between tag bar and messages; Banner shows session ID (abc12345…) with Dismiss all button

  PROMPTS P101311 [ ] [task] [in-progress] [0] — Investigate project loading order and slow history/summary load
    Requirements: Projects not in order by recent; Project summary and history load slowly with pagination
    Deliveries: Reviewed project loading flow

  PROMPTS P101414 [ ] [task] [in-progress] [0] — Hard refresh UI to see table changes
    Requirements: UI not showing changes
    Deliveries: Instructed Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows) for hard refresh

  PROMPTS P101434 [ ] [task] [in-progress] [0] — Add database indexes for performance, clean up duplicate queries
    Requirements: Planner tabs and work_items load slowly; Verify query documentation at top of files
    Deliveries: Added 5 composite indexes in migration m020; idx_mae_project_session on mem_ai_events; idx_mae_project_etype on mem_ai_events; idx_mmrrc_project_session on mem_mrr_commits; idx_mmrrc_project_hash on mem_mrr_commits

  PROMPTS P101435 [ ] [task] [in-progress] [0] — Investigate DIGEST column, work_items without events, purple tag color
    Requirements: DIGEST column purpose unclear; Work_items appear without linked prompts/commits/events; User cannot approve/remove additional AI tags
    Deliveries: Verified DIGEST is event counter (not separately tracked); Work_items without events are valid (not all come from prompts); Purple tag added for additional AI suggestions

  PROMPTS P101470 [ ] [task] [in-progress] [0] — Move session ID to tag bar, remove duplicate phase display
    Requirements: Session ID should only appear in tag bar (not message banner); Phase already shown in dropdown, remove duplicates
    Deliveries: Session ID badge (ab3f9) added between entity chips and + Tag button; Click copies full ID to clipboard with ✓ flash confirmation; Removed session banner from message display; Phase shown only in left dropdown

---

## **performance-optimization** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 9 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Query optimization, DB calls, loading speed
> Requirements: Reduce multiple SQL calls by loading all tags once into memory; Update memory and database only on save; Create smart dropdown with category filter and add new value option; Optimize SQL queries to load once on project load and update on save; Support nested tags beyond current 2-level hierarchy (category → tag)

  PROMPTS P101260 [ ] [feature] [in-progress] [0] — Optimize database calls by caching tags in memory with smart dropdown UI
    Requirements: Reduce multiple SQL calls by loading all tags once into memory; Update memory and database only on save; Create smart dropdown with category filter and add new value option
    Deliveries: Implemented tag cache population in chat.js via _pickerPopulateCats() reading from cache; Created category dropdown with counts (e.g., feature (5)) in chat.js; Added live filter and Add button in floating dropdown via _pickerValFilter() in chat.js

  PROMPTS P101261 [ ] [feature] [in-progress] [0] — Design nested tags support with unlimited hierarchy depth
    Requirements: Optimize SQL queries to load once on project load and update on save; Support nested tags beyond current 2-level hierarchy (category → tag); Show full path in chat tab but allow editing only at leaf level
    Deliveries: Designed database schema addition: parent_id column in entity_values for unlimited nesting; Proposed planner tree view displaying all properties at every level; Proposed chat tab showing only leaf-level tags with full path display

  PROMPTS P101280 [ ] [feature] [in-progress] [0] — Add pagination for chat prompts, chats, and commits with 24/page limit
    Requirements: Display pagination controls (< > 24/xxx) on chat tab top right; Implement same pagination for chats and commits tabs
    Deliveries: Extended backend _load_unified_history() to read history.jsonl and all history_*.jsonl archives; Added frontend pagination UI showing page bounds (e.g., 1–100 / 204) with arrow controls; Increased total history capacity from 26 to 204 entries covering Feb 23–Mar 15 range

  PROMPTS P101434 [ ] [feature] [in-progress] [0] — Add database indexes for planner/work items queries and document top-level queries
    Requirements: Optimize queries for planner tabs and work items loading; Document query statements at top of each class file
    Deliveries: Added migration m020 with 5 composite indexes in db_migrations.py including idx_mae_project_session, idx_mae_project_etype, idx_mmrrc_project_session; Optimized route_entities.py by removing unused TagBySourceIdBody and ValueCreate parameters; Simplified create_value, session_bulk_tag, and other methods reducing code complexity

  PROMPTS P101265 [ ] [bug] [in-progress] [0] — Fix port binding issue preventing app restart
    Requirements: Resolve uvicorn exit code 1 when attempting to bind 127.0.0.1:8000; Handle orphaned processes preventing port release
    Deliveries: Added freePort() function to check port availability and kill processes holding port 8000; Integrated freePort() into app startup sequence before uvicorn spawn; Added 2-second wait for OS confirmation port is free

  PROMPTS P101275 [ ] [bug] [in-progress] [0] — Cache all tags once and save tag colors with proper persistence
    Requirements: Load all tags once into memory to avoid repeated database queries when adding tags; Preserve tag color from combolist when saving tag selection; Unify commits tag mechanism with history tag adding (dropdown instead of 3-column list)
    Deliveries: Implemented _buildTagCache() in history.js loading categories once via Promise.all; Created _tagCache (grouped) and _tagCacheMap (flat lookup) in history.js for color preservation; Documented tag persistence mechanism and commits save/update alignment

  PROMPTS P101311 [ ] [bug] [in-progress] [0] — Investigate slow project loading and improve planner/history performance
    Requirements: Diagnose why project list appears out of order by recent access; Identify why project opening and history loading takes excessive time; Add UI feedback explaining loading progress
    Deliveries: Verified sanity of pagination implementation and performance baseline

  PROMPTS P101435 [ ] [bug] [in-progress] [0] — Fix work items sort order and allow user approval/removal of AI tags
    Requirements: Clarify DIGEST column purpose and justify work items display order; Explain orphaned work items appearing without linked prompts/commits/events; Enable user approval/removal of purple AI tags matching manual tag behavior
    Deliveries: Fixed sort order in route_work_items.py with NULLS LAST clause for correct ordering; Updated _renderWiPanel and _wiRenderRows in entities.js (frontend) to reflect corrected ordering; Removed stale columns and simplified row rendering logic

  PROMPTS P101471 [ ] [bug] [in-progress] [0] — Fix history loading to include all prompts from start; merge session files correctly
    Requirements: Ensure all prompts load from beginning, not truncated from arbitrary point; Clarify why _system/session files exist and prevent stale data; Update stale session files to reflect latest prompts
    Deliveries: Implemented _normalize_jsonl_entry() in route_history.py handling 35 lines of schema normalization; Updated chat_history endpoint to merge database entries with JSONL archive (531 total vs 389 before); Corrected sort order showing April 15 (newest) first through March 6 (oldest) with NULLS LAST

---

## **memory-layers-refactor** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 61 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Memory layer architecture, schema design, migration

  PROMPTS P101255 [ ] [task] [in-progress] [0] — Assuming I will improve the project management page, workflow processes. can you

  PROMPTS P101268 [ ] [task] [in-progress] [0] — can you run /memory, and make the UI more clear. add your sujjestion in a clear 

  PROMPTS P101269 [ ] [task] [in-progress] [0] — can you run /memory and run some tests? I do not see any sujjestion on all the e

  PROMPTS P101276 [ ] [task] [in-progress] [0] — can you run /memory, to make sure all updated. also can you check that system is

  PROMPTS P101284 [ ] [task] [in-progress] [0] — let me summerise not. first run /memroy to update all sumeeries, db tagging and 

  PROMPTS P101296 [ ] [task] [in-progress] [0] — is it align to the 5 steps memory? is there is any addiotnal requirement in orde

  PROMPTS P101297 [ ] [task] [in-progress] [0] — Is there is any addiotnal improvement that I can implemet for having full memroy

  PROMPTS P101303 [ ] [task] [in-progress] [0] — Can you run the /memory and go over current architecure - how data is stored, ho

  PROMPTS P101330 [ ] [task] [in-progress] [0] — Is it makes more sense, before I continue to the secopnd phase (refactor embeddi

  PROMPTS P101331 [ ] [task] [in-progress] [0] — Yes please fix that. about pr_embedding. in the prevous prompts I have mention t

  PROMPTS P101332 [ ] [task] [in-progress] [0] — I am not sure all tagging functionality is implemented as I do not see the mng_a

  PROMPTS P101333 [ ] [task] [in-progress] [0] — I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_rela

  PROMPTS P101334 [ ] [task] [in-progress] [0] — I would like to make sure relation is managed properly.  relation can be managed

  PROMPTS P101335 [ ] [task] [in-progress] [0] — I would like to make sure that the final layer include Work Items, Feature Snaps

  PROMPTS P101336 [ ] [task] [in-progress] [0] — This task is related to current memory update (layer 1)  Create all memory files

  PROMPTS P101337 [ ] [task] [in-progress] [0] — perfect. I would like to have an updated aicli_memory with all updated memory st

  PROMPTS P101338 [ ] [task] [in-progress] [0] — Is it advised to merge pr_session_summeries into mem_ai_events. make sure there 

  PROMPTS P101339 [ ] [task] [in-progress] [0] — I think llm_source is missing in mem_ai_events. I also see columns that I am not

  PROMPTS P101340 [ ] [task] [in-progress] [0] — It seems that I cannot see the changes in the db 

  PROMPTS P101341 [ ] [task] [in-progress] [0] — It is working noew. ddl is updated. still I do se columns that I am not sure are

  PROMPTS P101342 [ ] [task] [in-progress] [0] — I would to refactor all mem_mrr_* tables as it seems there are columns that are 

  PROMPTS P101343 [ ] [task] [in-progress] [0] — test prompt after migration

  PROMPTS P101344 [ ] [task] [in-progress] [0] — can you do the same for the mem_ai tables ? 

  PROMPTS P101345 [ ] [task] [in-progress] [0] — test after mem_ai cleanup

  PROMPTS P101346 [ ] [task] [in-progress] [0] — It looks like database.py become really big. can you remove old migration and ma

  PROMPTS P101349 [ ] [task] [in-progress] [0] — Not sure if you remember the previous memory config. if you do (you can check ai

  PROMPTS P101350 [ ] [task] [in-progress] [0] — yes . fix that all 

  PROMPTS P101368 [ ] [task] [in-progress] [0] — I would like to work on the mem_ai_events which takes events from all system. mo

  PROMPTS P101369 [ ] [task] [in-progress] [0] — Please add the llem_source after project, and in all tables where there is embed

  PROMPTS P101370 [ ] [task] [in-progress] [0] — I dont see any change in mem_ai_events. llm_source suppose to be after project, 

  PROMPTS P101371 [ ] [task] [in-progress] [0] — Looks good, can you rename this table to mem_ai_events_old. create new table be 

  PROMPTS P101372 [ ] [task] [in-progress] [0] —  What are the columns doc_type, language and file_path are used for ? also sessi

  PROMPTS P101373 [ ] [task] [in-progress] [0] — I would like to add language as a tags into the tags. if that is updated on each

  PROMPTS P101374 [ ] [task] [in-progress] [0] —  What is chunck and chunck_type are used for ? is it importnt information that c

  PROMPTS P101375 [ ] [task] [in-progress] [0] — I am looking at the table and see lots for event from history that not makes any

  PROMPTS P101377 [ ] [task] [in-progress] [0] — I would like to build the aicli_memory.md for scratch in order to get a final vi

  PROMPTS P101378 [ ] [task] [in-progress] [0] — About orocess_item / messeges - trigger in /memroy (for all new items at the mom

  PROMPTS P101379 [ ] [task] [in-progress] [0] — test prompt after fix

  PROMPTS P101387 [ ] [task] [in-progress] [0] — I am checking the aiCli_memory - and it is looks likje it is not updated at all.

  PROMPTS P101394 [ ] [task] [in-progress] [0] — can you update all memory_items (maybe run /memory) to have an uodated data 

  PROMPTS P101398 [ ] [task] [in-progress] [0] — In addtion to your reccomendation, I would like to check the following -  mem_ai

  PROMPTS P101400 [ ] [task] [in-progress] [0] — I still see the columns in commit table - diif_summery and diff_details . is it 

  PROMPTS P101401 [ ] [task] [in-progress] [0] — I would like to understand the commit table - do you have my previous comment? m

  PROMPTS P101405 [ ] [task] [in-progress] [0] — can you explain where are the  prompts that used for update new commit ? 

  PROMPTS P101407 [ ] [task] [in-progress] [0] — three is link from prompts to commits. each five prompts summeries to event, whi

  PROMPTS P101412 [ ] [task] [in-progress] [0] — I would like to understand how work_item are populated. work_item suppose to be 

  PROMPTS P101429 [ ] [task] [in-progress] [0] — Where are all the rpompts for ai_tags and work_item are ?

  PROMPTS P101430 [ ] [task] [in-progress] [0] — I do see same work item working on mention document summery and update ai memory

  PROMPTS P101431 [ ] [task] [in-progress] [0] — Can you share the quesry you are suing the get all promotps, commit, event per w

  PROMPTS P101437 [ ] [task] [in-progress] [0] — I still dont understand how there are work_items without any linked prompts. can

  PROMPTS P101442 [ ] [task] [in-progress] [0] — I am not sre what is start_id used for . Also code_summenry - what is it for ? t

  PROMPTS P101443 [ ] [task] [in-progress] [0] — I still dont understand what is summery column used for . also tags - I do see t

  PROMPTS P101444 [ ] [task] [in-progress] [0] — What is summery used for, I do see ai_desc, what is summery for ?

  PROMPTS P101445 [ ] [task] [in-progress] [0] — I think summery suppose to be part of ai_desc as there are alreadt 3 column for 

  PROMPTS P101459 [ ] [task] [in-progress] [0] — Events - I would like to make sure events are working properly in order to have 

  PROMPTS P101460 [ ] [task] [in-progress] [0] — Can you try again the table migration (using the column order I have mention) th

  PROMPTS P101461 [ ] [task] [in-progress] [0] — In events table is there is any point to have importance ? I think its more rele

  PROMPTS P101462 [ ] [task] [in-progress] [0] — yes

  PROMPTS P101463 [ ] [task] [in-progress] [0] — I still see old tags in event is that intenional? it suppose to show only users 

  PROMPTS P101464 [ ] [task] [in-progress] [0] — yes drop that. also change mem_mrr_prompts column order - after client_id add pr

  PROMPTS P101468 [ ] [task] [in-progress] [0] — test: is hook-log working now after m050?

---

## **tagging-system** · 26/03/10-03:14 [ ] (claude)
> Type: new
> Total: 42 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Tag management, relations, merging, and AI suggestions
> Requirements: Explain MCP server integration vs direct tools; Address missing suggestions in chat; Clarify session commit/footer display; Link commits to prompts by source_id; Separate history (all entries) from chat (summaries)

  PROMPTS P101274 [ ] [feature] [in-progress] [0] — Implement commit-to-prompt linking and history/chat separation
    Requirements: Link commits to prompts by source_id; Separate history (all entries) from chat (summaries); Enable memory updates with embedded data
    Deliveries: Added `POST /entities/events/tag-by-source-id` endpoint in `ui/backend/routers/entities.py`; Implemented idempotent tagging by timestamp lookup; Added `api.entities.tagBySourceId()` in `ui/frontend/utils/api.js`

  PROMPTS P101275 [ ] [feature] [in-progress] [0] — Cache tags in memory and sync colors on save
    Requirements: Load all tags once on history tab open; Save tag with color from combolist; Use same mechanism for commit tags as history
    Deliveries: Added `_buildTagCache()` in `ui/frontend/views/history.js` loading categories in parallel; Created `_tagCache` (grouped) and `_tagCacheMap` (flat {id→{color,name,icon}})

  PROMPTS P101277 [ ] [feature] [in-progress] [0] — Link commits to specific prompt IDs
    Requirements: Create link between commit hash and prompt source_id; Support multiple commits per prompt
    Deliveries: Successfully linked 5 commits to prompts using prompt source_id; Sample shows d0f14c21→prompt, 951768bc→prompt mappings

  PROMPTS P101278 [ ] [feature] [in-progress] [0] — Review session_tags.json usage and implement history rotation
    Requirements: Determine session_tags.json necessity; Implement history.jsonl rotation on /memory call; Archive to history_YYMMDDHHDD format per 500 rows
    Deliveries: Confirmed `_rotate_history()` in `projects.py` called on `generate_memory()`; Rotation triggered with configurable `history_max_rows` from `project.yaml`; Rotated 2110 lines to `history_2602230915.jsonl` archive

  PROMPTS P101281 [ ] [feature] [in-progress] [0] — Deduplicate tags across history/commit/chat and add removal option
    Requirements: Ensure no duplicate tags across screens; Add remove (×) tag buttons affecting all screens
    Deliveries: Verified 149 tags with 0 duplicates using `ON CONFLICT DO NOTHING`; Added `DELETE /entities/events/tag-by-source-id` and `DELETE /entities/session-tag` endpoints; Frontend deduplicates tags before API calls

  PROMPTS P101283 [ ] [feature] [in-progress] [0] — Display commits per prompt in history chat view
    Requirements: Link each commit to the specific prompt that triggered it; Show commits inline per prompt, not at session level
    Deliveries: `/history/commits` returns `prompt_source_id` for each commit; Updated history view to show commits inline at bottom of each prompt entry with `⑂ hash ↗` link; Commits now grouped by `prompt_source_id` instead of session-wide

  PROMPTS P101298 [ ] [feature] [in-progress] [0] — Add prompt count management table and memory status prompts
    Requirements: Create management table to track prompt counts; Prompt user when /memory runs; Show prompt count on project upload
    Deliveries: Designed but implementation pending

  PROMPTS P101315 [ ] [feature] [in-progress] [0] — Add parent-child tag support and align UI with new infrastructure
    Requirements: Restore nested (parent-child) tagging capability; Verify UI alignment with new workflow infrastructure; Ensure work items inherit parent-child relationships
    Deliveries: Added `parent_id: Optional[str] = None` to `WorkItemCreate` model; Updated INSERT query to include `parent_id` column in `work_items.py`; Updated SELECT query to return `w.parent_id` cast to string

  PROMPTS P101332 [ ] [feature] [in-progress] [0] — Implement complete tagging system with AI suggestions
    Requirements: Create mng_ai_tags_relations for tag relationships; Populate tags from memory dictionary for event tagging; Support claude cli tags: session_id, session_src, tagid
    Deliveries: Enhanced memory tagging system in response; AI context files updated

  PROMPTS P101351 [ ] [feature] [in-progress] [0] — Implement drag-drop tag merge in planner
    Requirements: Add drag-drop merge functionality to planner tab; Support parent-child relationships via drag; Support merge to same/different categories; Update planner_tag table on merge
    Deliveries: Designed feature specification for tag merging

  PROMPTS P101360 [ ] [feature] [in-progress] [0] — Move AI suggestions to separate section and enable drag-drop nesting
    Requirements: Move AI suggestions below main categories; Create AI section with suggested task/bug/feature; Enable drag-drop for parent-child tagging; Prevent user creation in ai_suggestion
    Deliveries: Added tag routing in `route_entities.py`; Enhanced entities view with API updates

  PROMPTS P101362 [ ] [feature] [in-progress] [0] — Mirror tagging mechanism to work_items phase with user-editable tags
    Requirements: Add tags column to mirror each mrr row; Support tag add/remove via UI in history; Enforce minimum tags in aicli (e.g., phase); Propagate user tags to planner
    Deliveries: Designed tagging architecture for mirroring phase

  PROMPTS P101373 [ ] [feature] [in-progress] [0] — Add language tag and improve file_change metadata
    Requirements: Add language as tag to events/mrr on commit; Enhance file_change with list of files and row counts; Change file_path to files[] tag with detailed metadata
    Deliveries: Designed tag migration approach

  PROMPTS P101376 [ ] [feature] [in-progress] [0] — Make show_llm tag visible in UI
    Requirements: Display show_llm as visible tag in history/chat
    Deliveries: Implemented visibility for show_llm tag

  PROMPTS P101422 [ ] [feature] [in-progress] [0] — Implement category-aware AI tag suggestions with user tags display
    Requirements: Show AI suggestions as category:name (e.g., bug:auth); Display existing tags first, new tags with different color; Show user tags as separate pills; Update button symbol styling
    Deliveries: Added tag suggestion chip with category:name format in `entities.js` at `_renderWiPanel`; Implemented user tags pills display

  PROMPTS P101426 [ ] [feature] [in-progress] [0] — Implement smart AI suggestion priority: task/bug/feature first, then metadata
    Requirements: Prioritize task/bug/feature category suggestions; Fall back to metadata tags (doc_type, phase); Create new task/bug/feature if no match; Show category in suggestion format
    Deliveries: Updated `_load_all_tags()` in `memory_tagging.py` to ORDER BY category first; Updated `_claude_judge_candidates()` prompt to instruct Haiku on priorities; Returns 103 AI(EXISTS) matches and 15 AI(NEW) suggestions with proper categories

  PROMPTS P101433 [ ] [feature] [in-progress] [0] — Implement /stag skill for session tagging
    Requirements: Create /stag skill to replace /tag (naming conflict); Enable users to tag session with phase:category format
    Deliveries: Created `/stag` skill in aicli; Tagged session with phase:development and feature:work-items

  PROMPTS P101439 [ ] [feature] [in-progress] [0] — Enable /stag usage in current session without new session
    Requirements: Allow /stag to tag current session without restart
    Deliveries: Confirmed /stag works immediately with `log_user_prompt.sh` hook reading `.agent-context`; Tags take effect on all future prompts in session

  PROMPTS P101448 [ ] [feature] [in-progress] [0] — Add creator/updater columns and reorder planner_tag columns
    Requirements: Enforce creator with value (username or 'ai'); Add updater column tracking last modifier; Reorder: project_id after client_id, timestamps last
    Deliveries: Applied migration m026 in `db_migrations.py` with 85 lines; Updated `memory_files.py` class signature and methods; Reordered columns: client_id, project_id, created/updated cols moved to end

  PROMPTS P101317 [ ] [bug] [in-progress] [0] — Fix planner nesting consistency across all categories
    Requirements: Unify nested tag behavior across doc_type, bug, feature categories; Ensure UI consistency; Clarify lifecycle/pipeline purpose
    Deliveries: Removed split between `entity_values` and `work_items` renderers; All categories now use `_renderTagTable` from `entity_values`; Nesting works identically for feature/bug/task as doc_type

  PROMPTS P101356 [ ] [bug] [in-progress] [0] — Fix lifecycle tags, bug counter, and drag-drop functionality
    Requirements: Remove or clarify lifecycle tagging; Fix bug counter not updating; Move AI suggestions to separate section; Enable drag-drop nesting
    Deliveries: Identified lifecycle tags as unused/confusing; Noted bug counter display issue; Proposed AI suggestion section restructure

  PROMPTS P101363 [ ] [bug] [in-progress] [0] — Fix tag UI error [object object] and cross-entity tag propagation
    Requirements: Fix 422 unprocessable entity error on tag add; Ensure tag added to prompt propagates to linked commits; Ensure tag added to commit propagates to linked prompt; Show commit↔prompt connection reference
    Deliveries: Applied session artifact cleanup

  PROMPTS P101364 [ ] [bug] [in-progress] [0] — Fix UndefinedColumn lifecycle error and optimize commit loading
    Requirements: Remove lifecycle column from work_items query; Remove unused PHASE column from commits; Optimize commit/event loading queries
    Deliveries: Fixed sycopg2.errors.UndefinedColumn in `route_entities.py:359`; Removed lifecycle references from work item SELECT query

  PROMPTS P101366 [ ] [bug] [in-progress] [0] — Restore tag loading and selection UI with search/create capability
    Requirements: Fix tag loading when attaching new tag; Restore category:tag dropdown UI; Support search existing or create new tag
    Deliveries: Updated system context and runtime state files

  PROMPTS P101410 [ ] [bug] [in-progress] [0] — Fix tag property drawer display when tag selected
    Requirements: Show property panel on left when tag clicked; Ensure drawer content displays correctly
    Deliveries: Fixed `catName` scope in `_renderDrawer()` at line 1541 in `entities.js`; Changed `v.short_desc` to `v.description` for field alignment; Root cause was ReferenceError preventing innerHTML from setting

  PROMPTS P101440 [ ] [bug] [in-progress] [0] — Fix unknown skill error and implement /stag as workaround
    Requirements: Resolve unknown skill /tag error; Provide working alternative
    Deliveries: Root cause: `tag` conflicts with reserved skill name in Claude Code; Created `/stag` renamed skill as replacement; Tagged current session: phase:development feature:work_items

  PROMPTS P101270 [ ] [task] [in-progress] [0] — Clarify MCP server usage vs direct file reading tools
    Requirements: Explain MCP server integration vs direct tools; Address missing suggestions in chat; Clarify session commit/footer display
    Deliveries: Explained aicli MCP server (`ui/mcp_server.py`) is separate integration for CLI context, not used in web sessions

  PROMPTS P101282 [ ] [task] [in-progress] [0] — Audit tagging logic across session/prompt/commit boundaries
    Requirements: Verify session tags, prompt tags, commit tags are linked correctly; Confirm propagation across boundaries
    Deliveries: Confirmed `_load_unified_history` reads current+archived entries; Verified `_propagate_tags_phase4` in `entities.py` for cross-boundary propagation; Confirmed `untag_event_by_source_id` and `remove_session_tag` endpoints working

  PROMPTS P101295 [ ] [task] [in-progress] [0] — Review database schema for tagging and optimize for MCP retrieval
    Requirements: Verify tagging is properly mapped in schema; Ensure optimal DB structure for MCP tool queries; Confirm saving mechanism is efficient
    Deliveries: Added `phase`, `feature`, `session_id` as real columns to `events_{p}` table in `core/database.py`; Added indexes `idx_{e}_session` and `idx_{e}_phase` for fast filtered queries; Moved migrations to per-statement try/except blocks

  PROMPTS P101301 [ ] [task] [in-progress] [0] — Audit memory improvements and tag system effectiveness
    Requirements: Review tag usage across system; Assess memory improvement from summarization; Evaluate MCP answer accuracy and workflow creation
    Deliveries: Fixed `session_bulk_tag()` to write both `event_tags_{project}` and `interaction_tags`; Verified individual `tag_by_source_id` endpoint writes both tables for work items

  PROMPTS P101302 [ ] [task] [in-progress] [0] — Summarize complete system improvements and deliverables
    Requirements: Document 7-part improvement; Compare before/after system state; Assess impact on performance, memory, MCP accuracy
    Deliveries: Documented two distillation layers between raw history and LLM; Implemented 4-agent work item pipeline; Enhanced MCP to actively manage project state

  PROMPTS P101316 [ ] [task] [in-progress] [0] — Plan tagging/nested tagging and planner/workflow integration
    Requirements: Review tagging mechanism alignment with planner; Ensure nested hierarchy support; Verify tag suggestions propagate to planner
    Deliveries: Renamed 'Workflow'→'Pipelines' and 'Prompts'→'Roles' in `main.js` PROJECT_TABS; Added `+▸` button to every regular tag row in `entities.js`; Widened actions column from 44px→80px in header

  PROMPTS P101321 [ ] [task] [in-progress] [0] — Verify tagging is wired to database and MCP retrieval
    Requirements: Confirm tagging linked/mapped properly in schema; Verify MCP tool uses tags for memory management; Assess database structure optimization
    Deliveries: Schema reviewed: 24 tables total (14 mng_ global, 10 pr_local_aicli_ project); Confirmed memory tables: work_items, interactions, interaction_tags, memory_items, project_facts

  PROMPTS P101358 [ ] [task] [in-progress] [0] — Clarify lifecycle tags purpose
    Requirements: Determine if lifecycle tags are needed
    Deliveries: Identified as unused component from previous development

  PROMPTS P101359 [ ] [task] [in-progress] [0] — Remove lifecycle tags from bug/feature/task
    Requirements: Remove lifecycle tags display
    Deliveries: Identified lifecycle tags as irrelevant to current scope

  PROMPTS P101429 [ ] [task] [in-progress] [0] — Document AI tag and work item prompts locations
    Requirements: Identify where all AI tagging and work item extraction prompts live
    Deliveries: Mapped work_item_extraction to `prompts/memory/work_items/work_item_extraction.md`; Mapped work_item_promotion to `prompts/memory/work_items/work_item_promotion.md`; Identified AI tag matching hardcoded in `memory_tagging.py:380`

  PROMPTS P101446 [ ] [task] [in-progress] [0] — Set session tags to phase:development feature:planner
    Requirements: Tag session for planner feature work
    Deliveries: Session tags set: phase:development, feature:planner

  PROMPTS P101447 [ ] [task] [in-progress] [0] — Review planner_tag schema and clean up unused columns
    Requirements: Audit planner_tag table columns for necessity; Consolidate source/creator fields; Remove code_summary from planner_tag; Simplify user-editable fields
    Deliveries: Identified seq_num as always null - DROP; Identified source/creator redundancy - DROP source; Identified dual status columns - consolidate to one; Proposed simplified user edit fields

  PROMPTS P101452 [ ] [task] [in-progress] [0] — Tag session for feature_snapshot work
    Requirements: Set session tag for feature snapshot feature
    Deliveries: Session tag set: feature:feature_snapshot

  PROMPTS P101428 [ ] [bug|feature] [in-progress] [0] — Fix AI tag display, add refresh button, backlink user tags to events
    Requirements: Show all AI suggestions (not just AI(EXISTS)); Replace new work item creation with refresh button; Backlink user tags from work_item to all connected events; Add event counter column to work_item
    Deliveries: Added `_backlink_tag_to_events()` in `route_work_items.py` with 46 lines; Added event counter column to work_items view; Implemented refresh button in `_loadWiPanel()`; Updated work item select to JOINs and count events

  PROMPTS P101438 [ ] [bug|feature] [in-progress] [0] — Fix AI tag approval flow: approve removes work_item from list, adds to tag
    Requirements: Remove confirm button for AI(EXISTS) approval; Move work_item under tag when approved (existing); Move work_item to new tag when AI(NEW) approved; Show work_item immediately in target location
    Deliveries: Updated `_wiPanelApproveTag()` to call `_loadTagLinkedWorkItems` for immediate display; Updated `_wiSecApprove()` for secondary tag approval; Added green ✓ button for AI(NEW) approval with `_wiPanelCreateTag()`

  PROMPTS P101441 [ ] [bug|feature] [in-progress] [0] — Fix AI tag save behavior: secondary tags stay as metadata, not primary link
    Requirements: Prevent work_item disappearance on secondary tag add; Store metadata tags in ai_tags.confirmed[]; Keep item in list after metadata save; Add loading indicator
    Deliveries: Fixed `_wiSecApprove()` to store in `ai_tags.confirmed[]` instead of `tag_id`; Item now stays in list after metadata tag save; Added toast message: 'Saved phase:development as metadata'; Migration m021, m022 in `db_migrations.py` applied

---

## **database-schema-cleanup** · 26/03/17-20:36 [ ] (claude)
> Type: new
> Total: 17 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Remove unused tables, refactor schema, split database.py
> Requirements: Remove unused tables; Rename global tables to mng_ prefix; Rename client tables to cl_ prefix; Rename project tables to pr_[client]_[project]_ prefix; Run database migration commands

  PROMPTS P101326 [ ] [bug] [in-progress] [0] — Fix database initialization errors: '_Database' has no 'ensure_project_schema', project not found
    Requirements: Fix AttributeError on ensure_project_schema; Resolve missing aicli project loading; Clean up duplicate tables from database; Fix schema initialization
    Deliveries: main.py: Removed stale db.ensure_project_schema(settings.active_project) call; database.py: Changed DDL to statement-by-statement execution, added missing ALTER TABLE for mng_session_tags.client_id and mng_entity_values columns; Verified project loading and schema consistency

  PROMPTS P101327 [ ] [bug] [in-progress] [0] — Fix backend startup errors, memory endpoint code_dir undefined variable, missing current project
    Requirements: Fix backend first-load failures; Fix CLAUDE.md code_dir variable undefined in line 1120; Display aicli as current project; Fix memory endpoint
    Deliveries: Memory endpoint verified working; Identified code_dir undefined variable issue in CLAUDE.md line 1120

  PROMPTS P101355 [ ] [bug] [in-progress] [0] — Fix UI errors: missing event_type column, undefined log variable, missing c.id column
    Requirements: Fix route_history.py line 228: column 'event_type' does not exist; Fix undefined 'log' variable in chat_history fallback; Fix route_entities.py line 1033: column c.id does not exist; Fix Chat history loading
    Deliveries: route_history.py: Fixed event_type column reference; Fixed undefined log variable in chat_history error handler; route_entities.py: Fixed c.id column reference (commit 19cc32ab)

  PROMPTS P101318 [ ] [task] [in-progress] [0] — Remove unused tables and restructure naming with mng_/cl_/pr_ prefixes
    Requirements: Remove unused tables; Rename global tables to mng_ prefix; Rename client tables to cl_ prefix; Rename project tables to pr_[client]_[project]_ prefix
    Deliveries: Assistant verified work_item_pipeline.py core file

  PROMPTS P101319 [ ] [task] [in-progress] [0] — Execute database cleanup: drop 5 stale tables, rename 19 global tables to mng_
    Requirements: Run database migration commands; Drop stale tables: commits, embeddings, events, event_tags, event_links; Verify 24 tables remain with proper naming
    Deliveries: Dropped 5 pre-project-split bare tables (commits, embeddings, events, event_tags, event_links); Renamed 19 global tables to mng_ prefix (users, entity_values, graph_workflows, etc.); Verified final schema: 14 mng_ + 10 pr_local_aicli_ tables

  PROMPTS P101320 [ ] [task] [in-progress] [0] — Clarify why memory_items and project_facts are under system management
    Requirements: Explain memory_items and project_facts table placement
    Deliveries: Updated MEMORY.md to reflect final table structure with 24 tables organized by prefix

  PROMPTS P101321 [ ] [task] [in-progress] [0] — Investigate mng_session_tags table and session_tags.json file usage
    Requirements: Verify if session_tags.json is actively used; Clarify purpose of mng_session_tags table
    Deliveries: Confirmed 24 tables organized: 14 mng_ (global), 10 pr_local_aicli_ (project data); Documented work_items, interactions, interaction_tags, memory_items, project_facts in pr_ namespace

  PROMPTS P101322 [ ] [task] [in-progress] [0] — Remove mng_graph_ references and determine graph table management layer
    Requirements: Eliminate all mng_graph_* references; Clarify whether graph tables should be client-level or global; Update graph table management
    Deliveries: routers/graph_workflows.py: Added project parameter to 12 endpoints, replaced mng_graph_* with db.project_table(); core/graph_runner.py: Added tbl_g* variables in _execute_node, run_graph_workflow, resume_graph_workflow; routers/work_items.py: Added graph table variables in run_pipeline and _ensure_pipeline_

  PROMPTS P101323 [ ] [task] [in-progress] [0] — Implement 3-layer table structure: mng_ (global), cl_ (client), pr_ (project)
    Requirements: Rename mng_session_tags to cl_local_session_tags; Align client tables with cl_ prefix; Ensure entity tables are per-client; Create 3-layer schema: mng_, cl_, pr_
    Deliveries: Identified mng_session_tags and mng_entity_values as client-level tables requiring cl_ prefix

  PROMPTS P101325 [ ] [task] [in-progress] [0] — Refactor schema: remove cl_[client] pattern, keep only mng_ and pr_ with unified large tables
    Requirements: Remove cl_[client] naming pattern; Keep only mng_ and pr_ prefixes; Unify large history/commit tables across clients instead of per-client; Use mng_users for client management; Plan dedicated instances for large customers
    Deliveries: Assistant acknowledged that mng_users table manages clients, history/commits unified across clients, free users on default client instance

  PROMPTS P101352 [ ] [task] [in-progress] [0] — Review and remove old unused table definitions from database.py
    Requirements: Review database.py for stale table definitions; Remove table schemas that no longer exist; Clean up database code
    Deliveries: Assistant committed database cleanup (1444ad94)

  PROMPTS P101353 [ ] [task] [in-progress] [0] — Determine if workspace folder under backend is actively used
    Requirements: Investigate backend/workspace folder usage; Determine if folder can be deleted
    Deliveries: Identified backend/workspace folder for review

  PROMPTS P101354 [ ] [task] [in-progress] [0] — Delete unused workspace folder from backend directory
    Requirements: Delete backend/workspace folder
    Deliveries: Deleted backend/workspace folder (commit 31002ada)

  PROMPTS P101361 [ ] [task] [in-progress] [0] — Verify database table structure changes are persisted and old tables removed
    Requirements: Confirm old tables are removed from database; Verify updated table structure reflects naming changes
    Deliveries: Committed system state and memory updates (43cbb0ca, ba6edb1d)

  PROMPTS P101409 [ ] [task] [in-progress] [0] — Create db_schema.sql canonical schema file with migration strategy
    Requirements: Separate database.py schema definitions into db_schema.sql; Include all CREATE TABLE IF NOT EXISTS statements; Add remarks, indexes, and foreign keys; Create migration method for table renames and data migration
    Deliveries: backend/core/db_schema.sql: Created (~350 lines) with mng_*, planner_*, mem_mrr_*, mem_ai_*, pr_* sections organized with comments explaining each table purpose, indexes, and FK constraints; Schema is single source of truth for database structure

  PROMPTS P101474 [ ] [task] [in-progress] [0] — Refactor user_id from string to int, add updated_at to mirror tables
    Requirements: Change user_id type from string to int (SERIAL); Add updated_at column to mirror tables after created_at; Add user_id after project_id in all mirror tables; Preserve old UUID in uuid_id column
    Deliveries: Migration m051 executed: mng_users.id now SERIAL INT, uuid_id VARCHAR preserves old UUID; updated_at added to: mng_users, mng_clients, mem_mrr_*, mem_ai_events, mem_ai_project_facts, mem_pipeline_runs, planner_tags; user_id INT added after project_id to all mirror tables; mem_ai_events.is_system → event_system; auth.py._resolve_user_id refactored; memory_files.py: MemoryFiles and get_top_events updated for new user_id int type (b3d2fda3)

  PROMPTS P101475 [ ] [task] [in-progress] [0] — Reorganize table column order: id, client_id, project_id, user_id, then created_at, updated_at, embe
    Requirements: Reposition user_id after project_id in all tables; Move created_at, updated_at to end before embedding; Remove committed_at from mem_mrr_commits (preserve in created_at); Update embedding to always be last column; Create migration m052 with rename _old, create new, insert data, drop old
    Deliveries: Migration m052 executed: 18 tables rebuilt with correct column ordering; All tables follow: id → client_id → project_id → user_id → [data] → created_at → updated_at → embedding; mem_mrr_commits: committed_at removed, git timestamp preserved via COALESCE(committed_at, created_at); mem_ai_events.event_system repositioned after event_type; All tables renamed with _old suffix, rebuilt, data migrated, old tables dropped (22736c54, 506c9b0f)

---

## **workflows-pipelines** · 26/03/09-17:56 [ ] (claude)
> Type: new
> Total: 55 prompts
> User tags:
> AI existing:
> AI new:
> Summary: Workflow pipelines, planner integration, feature snapshots

  PROMPTS P101256 [ ] [feature] [in-progress] [0] — The last prompts was asking for a new feature (clinet install/ support multiple 

  PROMPTS P101257 [ ] [feature] [in-progress] [0] — I dont think your update works. lets start from Planer - there is not need to ha

  PROMPTS P101285 [ ] [feature] [in-progress] [0] — I would like to set that up , and also add that to new prokect as autoamted set 

  PROMPTS P101286 [ ] [feature] [in-progress] [0] — The last commit was b255366 which suppose to be linked to the last prompt. it di

  PROMPTS P101287 [ ] [feature] [in-progress] [0] — When I run memory through the aiCli - I did see some usefull suggestion that app

  PROMPTS P101294 [ ] [feature] [in-progress] [0] — It looks good and working as expected. the issue now is how it is linked to Hist

  PROMPTS P101300 [ ] [feature] [in-progress] [0] — I have started to look in some other solution like https://github.com/danshapiro

  PROMPTS P101306 [ ] [feature] [in-progress] [0] — I would like to start working on the workflows - the goal is to be able to be si

  PROMPTS P101307 [ ] [feature] [in-progress] [0] — I do see you have crete a defualt pipe line in the Planner tab that run defualt 

  PROMPTS P101308 [ ] [feature] [in-progress] [0] — I do mention to sotre the prompts in database, would there be a way to change th

  PROMPTS P101314 [ ] [feature] [in-progress] [0] — What is the claude agent sdk is uded for can it be used for my use cases for mut

  PROMPTS P101316 [ ] [feature] [in-progress] [0] — I would like to go over on all the feutre and plan propery to Planer and Worklow

  PROMPTS P101347 [ ] [feature] [in-progress] [0] — Implement 1 and 2. pipeline is trigerred from the planer tab. for example there 

  PROMPTS P101348 [ ] [feature] [in-progress] [0] — Why there is no embedding in project_facts and work_items ? this is not suppose 

  PROMPTS P101356 [ ] [feature] [in-progress] [0] — I would like to work on the planer tab - I do see Lifecucle tagging which I am n

  PROMPTS P101358 [ ] [feature] [in-progress] [0] — There is lifecycle tags which I am not sure are relevant. is it needed ?

  PROMPTS P101367 [ ] [feature] [in-progress] [0] — I have got an error on /history/commits/sync?project=aicli rest api in     execu

  PROMPTS P101393 [ ] [feature] [in-progress] [0] — I would like to be able to move work_item back to work_item or to another items.

  PROMPTS P101403 [ ] [feature] [in-progress] [0] — I do not see any update at the database 

  PROMPTS P101404 [ ] [feature] [in-progress] [0] — yes please

  PROMPTS P101406 [ ] [feature] [in-progress] [0] — Can you explain how commit data statitics are connected to work_items ? Is there

  PROMPTS P101408 [ ] [feature] [in-progress] [0] — There is a problem to load work_items - line 331 in route_work_items -column w.a

  PROMPTS P101411 [ ] [feature] [in-progress] [0] — I do not see mem_mrr_commits_code populated on every commit. is that suppose to 

  PROMPTS P101413 [ ] [feature] [in-progress] [0] — In the UI - work_items shows as a row. I would each row to have name - desc colu

  PROMPTS P101426 [ ] [feature] [in-progress] [0] — I would like to update the ai_sujjestion - it suppose to sujjest one tag from ca

  PROMPTS P101427 [ ] [feature] [in-progress] [0] — Can you explain how do I see work_item #20006 as the one that was last updated ?

  PROMPTS P101428 [ ] [feature] [in-progress] [0] — Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujje

  PROMPTS P101449 [ ] [feature] [in-progress] [0] — I am planning to add a layer that will merge planner_tags with wor_item - this l

  PROMPTS P101450 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P101451 [ ] [feature] [in-progress] [0] — This start to look good. I would like to add one more column - deliveries that w

  PROMPTS P101452 [ ] [feature] [in-progress] [0] — can you add tag feature:feature_snapshot

  PROMPTS P101453 [ ] [feature] [in-progress] [0] — Feature_snapshot  I would like to create the final stage - mem_ai_feature_snapsh

  PROMPTS P101454 [ ] [feature] [in-progress] [0] — Assuming all will work properly. having a way to store all project history using

  PROMPTS P101455 [ ] [feature] [in-progress] [0] — How can I improve points 4 and 5 ? for point 4 - I did make prompts in sappasret

  PROMPTS P101456 [ ] [feature] [in-progress] [0] — ok. can you implement that. make sure dashboard is a new tab. pipeline will be a

  PROMPTS P101262 [ ] [feature] [in-progress] [0] — yes. just to clarify when I add login - it will be first level only ? 

  PROMPTS P101263 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P101266 [ ] [feature] [in-progress] [0] — I do see the save button - and when I save I do see the tag, when I am checking 

  PROMPTS P101271 [ ] [feature] [in-progress] [0] — hellow, how are you ?

  PROMPTS P101272 [ ] [feature] [in-progress] [0] — I understand the issue. I am using your claude cli and hooks to store propts and

  PROMPTS P101279 [ ] [feature] [in-progress] [0] — Something wit hooks is not working now, as I do not see any new prompts / llm re

  PROMPTS P101299 [ ] [feature] [in-progress] [0] — I would like to optimise the code : check each file, make sure code is in used a

  PROMPTS P101304 [ ] [feature] [in-progress] [0] — Keys are stored at my .env file which you can load - for claude api the key is u

  PROMPTS P101305 [ ] [feature] [in-progress] [0] — are you using the mcp now? 

  PROMPTS P101309 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P101365 [ ] [feature] [in-progress] [0] — The are soe errors on loading data - psycopg2.errors.UndefinedColumn: column p.w

  PROMPTS P101380 [ ] [feature] [in-progress] [0] — I would like to add mng_projects table that will be used for project data. curre

  PROMPTS P101381 [ ] [feature] [in-progress] [0] — verify prompt after client_id fix

  PROMPTS P101382 [ ] [feature] [in-progress] [0] — final verify prompt

  PROMPTS P101385 [ ] [feature] [in-progress] [0] — I have  got the following error -  cur.execute(b''.join(parts)) started  route_h

  PROMPTS P101386 [ ] [feature] [in-progress] [0] — I still dont see the same issue in route_history line 470. cur.execute(b''.join(

  PROMPTS P101388 [ ] [feature] [in-progress] [0] — I would like to make sure columns are aligned in work_items. What is source_sess

  PROMPTS P101395 [ ] [feature] [in-progress] [0] — I do have some errors loading data - route_work_items line 249 - cur.execute(_SQ

  PROMPTS P101402 [ ] [feature] [in-progress] [0] — Where simple extraction flow can be something like that:  pr_tags_map   WHERE re

  PROMPTS P101432 [ ] [feature] [in-progress] [0] — before you desing. is it possible to add some mechanism to our converstion. for

---

## **general-commits** · 26/04/12-00:03 [+] (auto)
> Type: existing
> Total: 7 commits
> User tags:
> AI existing:
> AI new:
> Summary: 7 commits updating: backend/core/db_migrations.py, backend/memory/memory_planner.py, backend/memory/memory_promotion.py, backend/memory/memory_tagging.py, backend/routers/route_projects.py, backend/routers/route_work_items.py… | classes: MemoryFeatureSnapshot, MemoryPlanner, MemoryPromotion, MemoryTagging

  COMMITS C200638 [+] [feature] [completed] [5] — Enhance memory promotion with embedding and search support
    Deliveries: backend/agents/tools/tool_memory.py: _handle_search_memory (+21/-0); backend/memory/memory_promotion.py: MemoryPromotion (+10/-1); backend/memory/memory_promotion.py: _embed_work_item (+19/-0); backend/memory/memory_promotion.py: MemoryPromotion.promote_work_item (+6/-0); backend/memory/memory_promotion.py: MemoryPromotion.extract_work_items_from_events (+4/-1)

  COMMITS C200639 [+] [feature] [completed] [5] — Add delivery management and tag system enhancements
    Deliveries: backend/core/db_migrations.py: m028_add_deliveries (+30/-0); backend/routers/route_tags.py: TagUpdate (+1/-0); backend/routers/route_tags.py: DeliveryCreate (+5/-0); backend/routers/route_tags.py: CategoryCreate (+0/-1); backend/routers/route_tags.py: _row_to_tag (+8/-6)

  COMMITS C200640 [+] [feature] [completed] [5] — Create feature snapshot memory module with LLM integration
    Deliveries: backend/core/db_migrations.py: m029_feature_snapshot (+44/-0); backend/memory/memory_feature_snapshot.py: MemoryFeatureSnapshot (+435/-0); backend/memory/memory_feature_snapshot.py: _parse_json (+9/-0); backend/memory/memory_feature_snapshot.py: _slugify (+2/-0); backend/memory/memory_feature_snapshot.py: _call_llm (+21/-0)

  COMMITS C200641 [+] [feature] [completed] [5] — Implement pipeline run logging and workflow orchestration
    Deliveries: backend/core/db_migrations.py: m030_pipeline_runs (+44/-0); backend/core/pipeline_log.py: pipeline_run_sync (+14/-0); backend/core/pipeline_log.py: _insert_run (+20/-0); backend/core/pipeline_log.py: _finish_run (+25/-0); backend/core/pipeline_log.py: pipeline_run (+18/-0)

  COMMITS C200637 [+] [task] [completed] [5] — Refactor memory promotion and tagging columns in work items
    Deliveries: backend/core/db_migrations.py: m025_rename_work_item_ai_columns (+15/-0); backend/memory/memory_planner.py: MemoryPlanner (+5/-5); backend/memory/memory_planner.py: MemoryPlanner._build_user_message (+3/-3); backend/memory/memory_planner.py: MemoryPlanner._write_document (+2/-2); backend/memory/memory_promotion.py: MemoryPromotion (+93/-20)

  COMMITS C200642 [+] [task] [completed] [5] — Add database maintenance and cleanup utilities
    Deliveries: backend/data/clean_pg_db.py: _raw_conn (+8/-0); backend/data/clean_pg_db.py: _bytes_to_mb (+2/-0); backend/data/clean_pg_db.py: run_maintenance (+170/-0); backend/data/clean_pg_db.py: run_maintenance_async (+4/-0); backend/data/clean_pg_db.py: _cli (+34/-0)

  COMMITS C200643 [+] [task] [completed] [5] — Add database index on prompts source_id column
    Deliveries: backend/core/db_migrations.py: m050_prompts_source_id_index (+21/-0)
