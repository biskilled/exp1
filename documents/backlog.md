# Backlog

> Approve entries with `[+]`, reject with `[-]`.
> Run `POST /memory/{project}/work-items` to merge into use cases.

## GROUP: discovery — Architecture review, memory layers, and system design (existing)
<!-- GROUP_SLUG: discovery -->
<!-- GROUP_TYPE: existing -->

PROMPTS 26/03/13-17:44 P100038 [+] [discovery] [task] (claude) — Explain aicli system to friend—shared AI memory platform

  Requirements: provide short explanation of aicli system
  Completed: described aicli core concept: shared AI memory across different AI tools (Claude CLI, Cursor, ChatGPT, etc.)

PROMPTS 26/03/16-17:42 P100068 [+] [discovery] [task] (claude) — Audit /memory architecture, MCP integration, and tagging system

  Requirements: review /memory output; explain data storage layer; explain MCP usage; verify tagging system works; test MCP availability in session
  Completed: /memory command executed successfully; reviewed MCP integration status; assessed memory layer architecture; identified synthesized flag status

PROMPTS 26/03/17-13:30 P100075 [+] [discovery] [task] (claude) — Use MCP tool and explain aicli project purpose

  Requirements: use MCP tool; explain project purpose
  Action items: invoke MCP tool to describe aicli purpose (acceptance: MCP tool called and project overview provided)

PROMPTS 26/03/17-18:18 P100078 [+] [discovery] [task] (claude) — Use MCP tool to explain aicli codebase functionality

  Requirements: use MCP tool; explain code functionality
  Completed: described aicli core functionality: shared AI memory platform enabling memory retention across different AI clients (Claude CLI, Cursor, ChatGPT, web UI)

PROMPTS 26/03/18-15:49 P100089 [+] [discovery] [task] (claude) — Review architecture for multi-client/project support and free user management

  Requirements: assess architecture for multi-client scenario; explain current client/project table design; recommend free/unregistered client management strategy
  Completed: reviewed three-tier naming pattern (mng_ → cl_local_ seeding); analyzed client/project hierarchy; provided architectural assessment for single-tenant tool
  Action items: define strategy for free/unregistered client lifecycle management (acceptance: strategy documented and aligned with multi-client architecture)

PROMPTS 26/03/18-20:17 P100094 [+] [discovery] [task] (claude) — Verify memory_items and project_facts update mechanism for multi-user clients

  Requirements: explain user relationship to client; verify memory_items and project_facts table updates; confirm memory mechanism implementation matches design
  Action items: audit memory_items and project_facts table update logic (acceptance: tables confirmed updated per specification or gaps identified with remediation plan)
---

## GROUP: ui-bugs — UI loading, visibility, and interaction issues (new)
<!-- GROUP_SLUG: ui-bugs -->
<!-- GROUP_TYPE: new -->

PROMPTS 26/03/10-00:11 P100023 [+] [ui-bugs] [bug] (claude) — Backend running fine; bind error caused by stale uvicorn instance on port 8000

  Requirements: Diagnose UI loading issue and bind address error
  Completed: Identified stale uvicorn process (PID 86671) still holding port 8000
  Action items: Kill stale backend process (acceptance: Port 8000 becomes available)

PROMPTS 26/03/10-00:19 P100024 [+] [ui-bugs] [task] (claude) — Clean backend restart; UI should load with dev script from ui/ directory

  Requirements: Restart backend and frontend cleanly with NODE_ENV=development
  Completed: Confirmed port 8000 is free; advised clean restart using dev script
  Action items: Run dev script from ui/ with NODE_ENV=development (acceptance: UI loads and connects to backend)

PROMPTS 26/03/10-01:42 P100029 [+] [ui-bugs] [feature] (claude) — Improve Planner action visibility and add archive toggle UI with 3-dot menu

  Requirements: Enlarge action buttons visibility in Planner; Add 3-dot menu to toggle archived items
  Completed: Identified import resolution errors; prepared UI refactor in views
  Action items: Implement 3-dot menu for archive toggle in Planner UI (acceptance: Archive/unarchive accessible via menu)

PROMPTS 26/03/10-02:33 P100032 [+] [ui-bugs] [task] (claude) — Clarify tag bar location and /memory command usage for Chat interface

  Requirements: Show user where to find accept button in tag bar
  Completed: Documented tag bar location as thin bar below title above messages
  Action items: Make tag bar more visually prominent (acceptance: User can easily locate tag bar)

PROMPTS 26/03/15-20:56 P100053 [+] [ui-bugs] [bug] (claude) — Fix phase not loading on app start and not updating on session switch

  Requirements: Load last phase from DB on startup instead of defaulting to required; Update phase when switching chat sessions
  Completed: Identified root causes: no DB load on startup, missing session switch phase sync
  Action items: Load phase from DB in session initialization (acceptance: Correct phase shows on app load)

PROMPTS 26/03/15-21:15 P100054 [+] [ui-bugs] [bug] (claude) — Fix phase save failure and session switch phase sync; add phase filter to commits

  Requirements: Fix phase save when changed; Fix phase display on session switch; Add phase filter to Commits view
  Completed: Removed _sessionId=null on phase change; restored proper session handling; wired api.putSessionTags
  Action items: Verify phase persists after save in chat (acceptance: Phase saves and retrieves correctly)

PROMPTS 26/03/15-21:45 P100055 [+] [ui-bugs] [bug] (claude) — Re-fix phase persistence in Chat; restore session phase metadata; default History to all phases

  Requirements: Phase must update when changed in Chat; All sessions load with correct phase; History default to all phases not just discovery
  Completed: Restored _sessionId=null flow; re-enabled api.putSessionTags; fixed phase metadata in sessions
  Action items: Test phase change persists across sessions (acceptance: Phase updates and syncs correctly)

PROMPTS 26/03/15-22:22 P100056 [+] [ui-bugs] [bug] (claude) — Fix Chat phase display and update when uploading/switching sessions

  Requirements: Show correct phase per session; Update phase display on session switch; Allow phase update
  Completed: Fixed phase change listener in chat.js; confirmed endpoint returns correct phase
  Action items: Verify phase displays correctly after session upload (acceptance: Phase matches session metadata)

PROMPTS 26/03/15-22:40 P100057 [+] [ui-bugs] [bug] (claude) — Mark all sessions missing mandatory fields with red warning regardless of source

  Requirements: Red mark sessions missing mandatory fields from all sources (UI/CLI/WF not just UI)
  Completed: Removed s.source==='ui' condition in session validation; now all sources checked
  Action items: Test red warning appears for CLI sessions without mandatory phase (acceptance: All sources show warning)

PROMPTS 26/03/15-22:51 P100058 [+] [ui-bugs] [bug] (claude) — Keep session order stable when phase changes; prevent reordering on tag updates

  Requirements: Maintain session sort order by date/prompt when changing phase
  Completed: Backend: patch_session_tags no longer updates updated_at for phase changes; Frontend: _loadSession preserves sort
  Action items: Verify session order stable after phase change (acceptance: Session position unchanged when phase updated)

PROMPTS 26/03/17-13:33 P100076 [+] [ui-bugs] [task] (claude) — Investigate slow project loading and History pagination performance issues

  Requirements: Check why project summary and History load slowly; Add loading feedback; Optimize existing pagination
  Completed: Prepared analysis of performance bottlenecks
  Action items: Profile project.md load and database queries (acceptance: Identify slow query or large file)

PROMPTS 26/03/17-14:35 P100077 [+] [ui-bugs] [bug] (claude) — Restore missing aiCli project in project list; speed up PROJECT.md file loading

  Requirements: Make aiCli project visible in recent projects list; Speed up PROJECT.md loading (currently >1min)
  Completed: Verified openProject function handles project discovery correctly
  Action items: Check if aiCli project exists in DB or is filtered out (acceptance: aiCli appears in project list)

PROMPTS 26/03/18-20:03 P100093 [+] [ui-bugs] [bug] (claude) — Fix project visibility in list; add retry logic for race conditions in project loading

  Requirements: Show aiCli as full project not just recent; Handle backend startup delay gracefully
  Completed: Added retry logic to _continueToApp for empty project results
  Action items: Test project loads after backend fully initializes (acceptance: Projects visible on fresh app start)

PROMPTS 26/04/01-09:00 P100122 [+] [ui-bugs] [bug] (claude_cli) — Fix drag-and-drop functionality and counter display

  Requirements: Drag and drop should work; Counter should update on changes
  Completed: Identified drag-drop and counter issues in entities view
  Action items: Test drag-drop updates work item tags (acceptance: Items drop correctly and counter increments)

PROMPTS 26/04/06-02:12 P100148 [+] [ui-bugs] [feature] (claude_cli) — Show full prompt and LLM response in History; add text copy functionality

  Requirements: Display full prompts and LLM responses not just snippet; Enable copy-to-clipboard in History
  Completed: Prepared History view updates to display full content
  Action items: Implement copy button in History prompts and responses (acceptance: User can copy text from History)

PROMPTS 26/04/06-02:18 P100149 [+] [ui-bugs] [bug] (claude_cli) — Restore LLM response display in History view that went missing

  Requirements: Show both prompt and LLM response in History (currently showing only prompt)
  Completed: Verified BACKEND_URL defined at line 46; confirmed all 4 background hooks present including response save
  Action items: Check hook-response saves LLM response correctly to DB (acceptance: Response column appears in History)

PROMPTS 26/04/06-14:17 P100154 [+] [ui-bugs] [bug] (claude_cli) — Fix ReferenceError for _plannerSelectAiSubtype and _plannerSync undefined

  Requirements: Resolve _plannerSelectAiSubtype undefined error; Fix _plannerSync function not found error
  Completed: Removed stale undefined reference that crashed init; _plannerSync now assigns correctly
  Action items: Verify planner initialization completes without errors (acceptance: No console errors on app load)

PROMPTS 26/04/06-18:02 P100156 [+] [ui-bugs] [bug] (claude_cli) — Fix drag-drop multi-hover selection and require page refresh to see linked results

  Requirements: Only selected tag should highlight on drag hover not all hovered tags; Show linked work items immediately after drop
  Completed: Identified drag-drop multi-hover and stale view rendering issues
  Action items: Fix drag hover to select only target tag (acceptance: Only intended tag highlights on drop)

PROMPTS 26/04/06-22:52 P100157 [+] [ui-bugs] [bug] (claude_cli) — Fix work items not appearing under dropped tag; filtering by wrong ai_category

  Requirements: Dropped work items should appear under target tag immediately
  Completed: Fixed _loadTagLinkedWorkItems: removed filtering by tag's category; now filters by work_item.ai_category
  Action items: Test drag-drop shows work item under correct tag (acceptance: Work item visible immediately after drop)

PROMPTS 26/04/09-00:33 P100179 [+] [ui-bugs] [task] (claude_cli) — UI changes not visible; require hard browser refresh

  Requirements: Verify UI updates are served correctly
  Completed: Confirmed Vite serving updated files correctly
  Action items: Hard refresh browser to clear cache (acceptance: Updated UI renders in browser)

PROMPTS 26/04/09-00:39 P100180 [+] [ui-bugs] [feature] (claude_cli) — Add work item details panel in Planner with commit and column headers

  Requirements: Show work item details in lower Planner tab; Display in Work item tab
  Completed: Added GET /work-items/{id} endpoint; updated _renderWiPanel with headers; formatted date display in entities.js
  Action items: Restart backend for SQL changes (acceptance: Work item details panel renders)

PROMPTS 26/04/09-00:47 P100181 [+] [ui-bugs] [feature] (claude_cli) — Improve work item panel header clarity with wider columns and better styling

  Requirements: Widen columns from 38px; Add visual header separation; Increase font size
  Completed: Widened columns; added header background; increased padding in _renderWiPanel hdr function
  Action items: Test header readability at different zoom levels (acceptance: Headers clearly visible and aligned)

PROMPTS 26/04/09-00:52 P100182 [+] [ui-bugs] [bug] (claude_cli) — Change date format to yy/mm/dd-hh:mm; remove non-work-item tags from display

  Requirements: Display dates as yy/mm/dd-hh:mm format; Filter out non-work-item tags like Shared-memory, billing
  Completed: Updated fmtDate format in entities.js; wired _wiPanelDelete handler for delete button
  Action items: Filter tags by ai_category='task' only in work item display (acceptance: Only task tags shown)

PROMPTS 26/04/09-01:23 P100185 [+] [ui-bugs] [feature] (claude_cli) — Add sticky headers to sortable columns; implement AI tag suggestions for work items

  Requirements: Make all column headers sticky not just Name; Add AI tag suggestion matching for work items
  Completed: Added position:sticky to all headers in _renderWiPanel; enhanced MemoryTagging.match_work_item_to_tags (+15/-2)
  Action items: Test AI tag suggestions appear in work item rows (acceptance: Suggestions match work item content)

PROMPTS 26/04/09-01:48 P100186 [+] [ui-bugs] [bug] (claude_cli) — Fix work item details loading on click; improve spacing and font sizing for Electron

  Requirements: Click work item to open details drawer; Reduce spacing between tags and approve/remove buttons; Increase font size for Electron UI
  Completed: Added GET /work-items/{id} endpoint call in _openWorkItemDrawer; refactored row layout
  Action items: Test click opens work item details immediately (acceptance: Details drawer renders with full item info)

PROMPTS 26/04/09-02:12 P100188 [+] [ui-bugs] [bug] (claude_cli) — Restore AI and user tag display in work item rows; use full row width for description

  Requirements: Show AI and user tags in rows; Description should use full row length not cut off mid-row
  Completed: Removed table-layout:fixed constraint; widened Name column; expanded description width in _renderWiPanel
  Action items: Verify tags display and description fills row (acceptance: Full description visible without wrapping)

PROMPTS 26/04/09-02:19 P100189 [+] [ui-bugs] [bug] (claude_cli) — Fix missing last column; add labeled tag sections (AI, User) with always-visible rows

  Requirements: Show UPDATED column; Label tag sections as AI: and User:; Show User: section even with no tags
  Completed: Restored table-layout:fixed; added labeled section headers; ensured User section always visible in _renderWiPanel
  Action items: Test all columns visible and tag sections labeled (acceptance: UPDATED column visible; sections labeled)

PROMPTS 26/04/09-02:26 P100190 [+] [ui-bugs] [feature] (claude_cli) — Add left padding; fix date format to yy/mm/dd-HH:mm; label AI tags as EXISTS or NEW

  Requirements: Add left table padding; Show full date not truncated; Distinguish AI(EXISTS) from AI(NEW) tags
  Completed: Fixed missing import json in route_work_items; added padding; updated date format and tag labels in _renderWiPanel
  Action items: Test date displays fully and tag labels show EXISTS/NEW status (acceptance: Full dates visible; tag status clear)

PROMPTS 26/04/12-22:53 P100222 [+] [ui-bugs] [bug] (claude_cli) — Fix Planner showing only work_item category; work items disappear when accepting AI tags

  Requirements: Show all categories (bug, feature, task) not just work_item; Keep work items visible after accepting tags
  Completed: Removed duplicate/conflicting category variable; fixed route_entities patch_value handling
  Action items: Test category filter shows all options (acceptance: All categories appear in dropdown)

PROMPTS 26/04/13-09:17 P100223 [+] [ui-bugs] [bug] (claude_cli) — Fix empty Electron load due to duplicate variable declaration conflict

  Requirements: Electron should load populated UI not empty
  Completed: Fixed duplicate const cats declaration in _wiPanelCreateTag by renaming second occurrence
  Action items: Restart Electron and verify UI loads with data (acceptance: Planner and work items display)

PROMPTS 26/04/15-18:41 P100230 [+] [ui-bugs] [bug] (claude_cli) — Fix latest prompts not showing in Chat; restore real-time chat updates from CLI

  Requirements: New CLI prompts should appear in Chat automatically; Fix silent DB error preventing latest prompts load
  Completed: Fixed migration m050 DB error; restored real-time prompt sync in chat view
  Action items: Verify new CLI prompts appear in Chat instantly (acceptance: Chat updates with each new prompt)

PROMPTS 26/04/15-18:51 P100231 [+] [ui-bugs] [feature] (claude_cli) — Add timestamp to prompts and session ID display in Chat; add per-prompt tags feature

  Requirements: Show YY/MM/DD-HH:MM timestamp next to YOU in Chat; Display session ID (last 5 chars) in Chat; Add tagging per prompt
  Completed: Updated history.js: sid.slice(-5) shows last 5 chars; added timestamp format; prepared per-prompt tag UI
  Action items: Test timestamps show on each prompt in Chat (acceptance: Timestamps visible next to prompt author)

PROMPTS 26/04/15-19:02 P100232 [+] [ui-bugs] [feature] (claude_cli) — Update Chat header to show CLI source label, phase, session ID and prompt count

  Requirements: Show session header as: CLI · phase · (session-id) · prompt-count · timestamp
  Completed: Updated session header display in chat.js; shows source label, phase, 5-char session ID, prompt count, timestamp
  Action items: Test Chat header displays full session info (acceptance: All info visible in session header)

PROMPTS 26/04/15-20:37 P100234 [+] [ui-bugs] [feature] (claude_cli) — Add session visibility in Chat left sidebar with source, phase, and session ID badges

  Requirements: Chat sessions in left sidebar should show source, phase, and session ID like History view
  Completed: Added session labels in Chat sidebar: 'CLI · phase · (session-id)' format; matches History visibility
  Action items: Test Chat sidebar shows session info badges (acceptance: Each session displays source/phase/ID)

PROMPTS 26/04/15-21:04 P100235 [+] [ui-bugs] [bug] (claude_cli) — Move session ID to tag bar; remove duplicate phase display from messages

  Requirements: Show session ID in tag bar not chat messages; Phase should display only once in tag bar not repeat
  Completed: Added session ID (ab3f9) badge in tag bar between entity chips and + Tag button
  Action items: Verify session ID shows in tag bar and phase shows only once (acceptance: Clean tag bar with session ID badge)

PROMPTS 26/04/15-21:12 P100236 [+] [ui-bugs] [bug] (claude_cli) — Fix incomplete Chat history loading on startup; loading only subset of prompts

  Requirements: Load all prompts on Chat startup not just recent subset
  Completed: Increased limit=500 in chat_history route; normalized _system session files to prevent stale data; fixed sorting April-to-March
  Action items: Verify all 389+ history entries load on startup (acceptance: Chat shows full history from oldest to newest)

PROMPTS 26/04/15-21:25 P100237 [+] [ui-bugs] [bug] (claude_cli) — Fix stale session ID loading on Chat startup; prevent old sessions from persisting

  Requirements: Load current session ID on startup not old stale session; Module-level _sessionId should not persist across navigations
  Completed: Reset _sessionId=null in renderChat(); read last_session_id from state immediately in _loadSessions
  Action items: Test Chat loads correct current session on startup (acceptance: Current session loads immediately)

PROMPTS 26/04/15-21:42 P100238 [+] [ui-bugs] [bug] (claude_cli) — Load current session immediately on Chat startup without 15-second delay

  Requirements: Current session should load immediately at app start not after delay
  Completed: Modified _loadSessions to read last_session_id from state at start; updated chat_history route to accept session param
  Action items: Test current session loads instantly on Chat view (acceptance: No delay; current session visible immediately)

COMMITS 26/04/06-12:58 C200149 [+] [ui-bugs] [task] (auto) — Update system docs and refactor work items after CLI session

  Completed: Updated system documentation files to reflect CLI session changes; Refactored work items structure and organization
---

## GROUP: db-schema-refactor — Database schema cleanup, migrations, and table optimization (new)
<!-- GROUP_SLUG: db-schema-refactor -->
<!-- GROUP_TYPE: new -->

PROMPTS 26/03/14-13:04 P100040 [+] [db-schema-refactor] [task] (claude) — I do see the option to add tag in history - can you make sure all tags are loade


PROMPTS 26/03/14-13:11 P100041 [+] [db-schema-refactor] [task] (claude) — can you run /memory, to make sure all updated. also can you check that system is


PROMPTS 26/03/14-19:08 P100043 [+] [db-schema-refactor] [task] (claude) —  I do see session_tags.json - is it used ? Also - history.jsonl start to be very


PROMPTS 26/03/14-21:36 P100044 [+] [db-schema-refactor] [task] (claude) — Something wit hooks is not working now, as I do not see any new prompts / llm re


PROMPTS 26/03/17-20:36 P100083 [+] [db-schema-refactor] [task] (claude) — before I continue - I do see quite lots of table used for this project. can you 


PROMPTS 26/03/17-21:06 P100084 [+] [db-schema-refactor] [task] (claude) — Can you run the command as well, as I dont see any change in the database . also


PROMPTS 26/03/18-10:46 P100085 [+] [db-schema-refactor] [task] (claude) — looks better. why memory_items and project_facts are under systeme managament ta


PROMPTS 26/03/18-11:51 P100086 [+] [db-schema-refactor] [task] (claude) — I do see the table mng_session_tags, I also see session_tags.json file at the pr


PROMPTS 26/03/31-16:50 P100096 [+] [db-schema-refactor] [task] (claude_cli) — Yes please fix that. about pr_embedding. in the prevous prompts I have mention t


PROMPTS 26/03/31-18:48 P100097 [+] [db-schema-refactor] [task] (claude_cli) — I am not sure all tagging functionality is implemented as I do not see the mng_a


PROMPTS 26/03/31-19:58 P100098 [+] [db-schema-refactor] [task] (claude_cli) — I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_rela


PROMPTS 26/03/31-20:42 P100099 [+] [db-schema-refactor] [task] (claude_cli) — I would like to make sure relation is managed properly.  relation can be managed


PROMPTS 26/03/31-21:23 P100100 [+] [db-schema-refactor] [task] (claude_cli) — I would like to make sure that the final layer include Work Items, Feature Snaps


PROMPTS 26/03/31-22:04 P100101 [+] [db-schema-refactor] [task] (claude_cli) — This task is related to current memory update (layer 1)  Create all memory files


PROMPTS 26/03/31-22:22 P100102 [+] [db-schema-refactor] [task] (claude_cli) — perfect. I would like to have an updated aicli_memory with all updated memory st


PROMPTS 26/03/31-22:30 P100103 [+] [db-schema-refactor] [task] (claude_cli) — Is it advised to merge pr_session_summeries into mem_ai_events. make sure there 


PROMPTS 26/03/31-23:02 P100104 [+] [db-schema-refactor] [task] (claude_cli) — I think llm_source is missing in mem_ai_events. I also see columns that I am not


PROMPTS 26/03/31-23:13 P100105 [+] [db-schema-refactor] [task] (claude_cli) — It seems that I cannot see the changes in the db 


PROMPTS 26/03/31-23:37 P100106 [+] [db-schema-refactor] [task] (claude_cli) — It is working noew. ddl is updated. still I do se columns that I am not sure are


PROMPTS 26/03/31-23:48 P100107 [+] [db-schema-refactor] [task] (claude_cli) — I would to refactor all mem_mrr_* tables as it seems there are columns that are 


PROMPTS 26/04/01-00:17 P100109 [+] [db-schema-refactor] [task] (claude_cli) — can you do the same for the mem_ai tables ? 


PROMPTS 26/04/01-00:39 P100111 [+] [db-schema-refactor] [task] (claude_cli) — It looks like database.py become really big. can you remove old migration and ma


PROMPTS 26/04/01-08:17 P100117 [+] [db-schema-refactor] [task] (claude_cli) — O would  like to cleanup the code more. I do see in Database old tables. can you


PROMPTS 26/04/02-09:39 P100126 [+] [db-schema-refactor] [task] (claude_cli) — I do not see  any update the table strucure (still see some  old tables)


PROMPTS 26/04/03-17:56 P100127 [+] [db-schema-refactor] [task] (claude_cli) — Let fix the tagging mechanism to my mirroring until work_items phase.  For each 


PROMPTS 26/04/03-20:02 P100129 [+] [db-schema-refactor] [task] (claude_cli) — I do see an error saying sycopg2.errors.UndefinedColumn: column t.lifecycle does


PROMPTS 26/04/05-11:00 P100130 [+] [db-schema-refactor] [task] (claude_cli) — The are soe errors on loading data - psycopg2.errors.UndefinedColumn: column p.w


PROMPTS 26/04/05-13:23 P100133 [+] [db-schema-refactor] [task] (claude_cli) — I would like to work on the mem_ai_events which takes events from all system. mo


PROMPTS 26/04/05-17:09 P100134 [+] [db-schema-refactor] [task] (claude_cli) — Please add the llem_source after project, and in all tables where there is embed


PROMPTS 26/04/05-17:27 P100135 [+] [db-schema-refactor] [task] (claude_cli) — I dont see any change in mem_ai_events. llm_source suppose to be after project, 


PROMPTS 26/04/05-17:30 P100136 [+] [db-schema-refactor] [task] (claude_cli) — Looks good, can you rename this table to mem_ai_events_old. create new table be 


PROMPTS 26/04/05-17:34 P100137 [+] [db-schema-refactor] [task] (claude_cli) —  What are the columns doc_type, language and file_path are used for ? also sessi


PROMPTS 26/04/05-17:46 P100138 [+] [db-schema-refactor] [task] (claude_cli) — I would like to add language as a tags into the tags. if that is updated on each


PROMPTS 26/04/05-18:13 P100139 [+] [db-schema-refactor] [task] (claude_cli) —  What is chunck and chunck_type are used for ? is it importnt information that c


PROMPTS 26/04/05-18:20 P100140 [+] [db-schema-refactor] [task] (claude_cli) — I am looking at the table and see lots for event from history that not makes any


PROMPTS 26/04/06-00:12 P100145 [+] [db-schema-refactor] [task] (claude_cli) — I would like to add mng_projects table that will be used for project data. curre


PROMPTS 26/04/06-01:54 P100146 [+] [db-schema-refactor] [task] (claude_cli) — verify prompt after client_id fix


PROMPTS 26/04/06-02:08 P100147 [+] [db-schema-refactor] [task] (claude_cli) — final verify prompt


PROMPTS 26/04/06-10:30 P100152 [+] [db-schema-refactor] [task] (claude_cli) — I am checking the aiCli_memory - and it is looks likje it is not updated at all.


PROMPTS 26/04/06-13:09 P100153 [+] [db-schema-refactor] [task] (claude_cli) — I would like to make sure columns are aligned in work_items. What is source_sess


PROMPTS 26/04/08-18:51 P100174 [+] [db-schema-refactor] [task] (claude_cli) — I would like to sapparte database.py in order to have methgods and tables schema


PROMPTS 26/04/11-13:00 P100207 [+] [db-schema-refactor] [task] (claude_cli) — I am not sre what is start_id used for . Also code_summenry - what is it for ? t


PROMPTS 26/04/11-22:56 P100208 [+] [db-schema-refactor] [task] (claude_cli) — I still dont understand what is summery column used for . also tags - I do see t


PROMPTS 26/04/11-23:02 P100209 [+] [db-schema-refactor] [task] (claude_cli) — What is summery used for, I do see ai_desc, what is summery for ?


PROMPTS 26/04/11-23:10 P100210 [+] [db-schema-refactor] [task] (claude_cli) — I think summery suppose to be part of ai_desc as there are alreadt 3 column for 


PROMPTS 26/04/12-11:17 P100212 [+] [db-schema-refactor] [task] (claude_cli) — I am looking on planner_tag table. seq_num - never populated. is it needed? sour


PROMPTS 26/04/12-11:25 P100213 [+] [db-schema-refactor] [task] (claude_cli) — Yes. please about createor - it must be woth a value . if user create it will be


PROMPTS 26/04/13-12:15 P100224 [+] [db-schema-refactor] [task] (claude_cli) — Events - I would like to make sure events are working properly in order to have 


PROMPTS 26/04/13-17:07 P100225 [+] [db-schema-refactor] [task] (claude_cli) — Can you try again the table migration (using the column order I have mention) th


PROMPTS 26/04/13-18:01 P100226 [+] [db-schema-refactor] [task] (claude_cli) — In events table is there is any point to have importance ? I think its more rele


PROMPTS 26/04/13-18:03 P100227 [+] [db-schema-refactor] [task] (claude_cli) — yes


PROMPTS 26/04/13-18:12 P100228 [+] [db-schema-refactor] [task] (claude_cli) — I still see old tags in event is that intenional? it suppose to show only users 


PROMPTS 26/04/14-11:42 P100229 [+] [db-schema-refactor] [task] (claude_cli) — yes drop that. also change mem_mrr_prompts column order - after client_id add pr


PROMPTS 26/04/15-22:38 P100239 [+] [db-schema-refactor] [task] (claude_cli) — I would like to move to another database refactor - user_id this suppose to be i


PROMPTS 26/04/15-23:03 P100240 [+] [db-schema-refactor] [task] (claude_cli) — I did ask to change the position in the table as well which not happend . for ex


COMMITS 26/03/31-15:37 C200132 [+] [db-schema-refactor] [task] (auto) — Update system files and refactor backend routes

  Completed: System configuration files updated; Backend route structure refactored

COMMITS 26/03/31-16:33 C200133 [+] [db-schema-refactor] [task] (auto) — Update AI session state and memory after session 17cd46bd

  Completed: AI session state synchronized; Memory files updated post-session

COMMITS 26/04/01-02:11 C200134 [+] [db-schema-refactor] [task] (auto) — Update AI session state and memory files

  Completed: Session state files refreshed; Memory tracking files updated

COMMITS 26/04/01-18:01 C200135 [+] [db-schema-refactor] [task] (auto) — Update system state and memory after claude session d7be5539

  Completed: System state synchronized; Memory files updated for session d7be5539

COMMITS 26/04/01-18:02 C200136 [+] [db-schema-refactor] [task] (auto) — Update memory, rules, and session state files

  Completed: MEMORY.md refreshed; Rules files updated; Session state synchronized

COMMITS 26/04/01-18:05 C200137 [+] [db-schema-refactor] [feature] (auto) — Enhance memory files, MCP server, and entities UI

  Completed: Memory files enhanced with new context; MCP server functionality improved; Entities UI components updated

COMMITS 26/04/01-18:05 C200138 [+] [db-schema-refactor] [task] (auto) — Update MEMORY.md and project docs after claude session

  Completed: MEMORY.md refreshed with session data; Project documentation updated

COMMITS 26/04/01-18:06 C200139 [+] [db-schema-refactor] [task] (auto) — Update memory and rules files after claude session

  Completed: Memory files synchronized; Rules documentation updated

COMMITS 26/04/01-18:06 C200140 [+] [db-schema-refactor] [task] (auto) — Update memory, rules, and project docs after claude session

  Completed: Memory context files updated; Rules files refreshed; Project documentation synchronized

COMMITS 26/04/01-18:07 C200141 [+] [db-schema-refactor] [task] (auto) — Clean up system files after claude cli session d7be5539

  Completed: Stale system files removed; Session d7be5539 artifacts cleaned up

COMMITS 26/04/01-18:07 C200142 [+] [db-schema-refactor] [task] (auto) — Update AI context files and trim MEMORY.md after session

  Completed: AI context files refreshed; MEMORY.md trimmed for optimization

COMMITS 26/04/01-18:16 C200143 [+] [db-schema-refactor] [task] (auto) — Sync system files and update memory/chat after claude session

  Completed: System files synchronized; Memory and chat history updated

COMMITS 26/04/03-19:28 C200144 [+] [db-schema-refactor] [task] (auto) — Update system files and memory after claude session 6ffb562b

  Completed: System configuration refreshed; Memory files updated for session 6ffb562b

COMMITS 26/04/05-17:06 C200145 [+] [db-schema-refactor] [task] (auto) — Update system files and memory after claude session 04d3b8ba

  Completed: System state updated; Memory files synchronized for session 04d3b8ba

COMMITS 26/04/05-17:25 C200146 [+] [db-schema-refactor] [task] (auto) — Update system state and simplify database core module

  Completed: System state refreshed; Database core module simplified

COMMITS 26/04/06-02:08 C200147 [+] [db-schema-refactor] [task] (auto) — Update system context and CLAUDE.md files post-session

  Completed: System context files synchronized; CLAUDE.md documentation updated

COMMITS 26/04/06-12:23 C200148 [+] [db-schema-refactor] [task] (auto) — Update system context and memory files after claude session

  Completed: System context refreshed; Memory files updated post-session

COMMITS 26/04/06-12:59 C200150 [+] [db-schema-refactor] [task] (auto) — Update system context and memory files after claude session

  Completed: System context synchronized; Memory documentation updated

COMMITS 26/04/06-12:59 C200151 [+] [db-schema-refactor] [task] (auto) — Remove aicli system context and claude session files

  Completed: aicli system context files removed; Stale claude session files cleaned up

COMMITS 26/04/07-01:10 C200152 [+] [db-schema-refactor] [task] (auto) — Update system prompts and memory after claude session

  Completed: System prompts refreshed; Memory files synchronized post-session

COMMITS 26/04/08-00:28 C200153 [+] [db-schema-refactor] [task] (auto) — Update system prompts and memory after CLI session 14a417f0

  Completed: System prompts updated; Memory files refreshed for session 14a417f0

COMMITS 26/04/08-00:28 C200154 [+] [db-schema-refactor] [task] (auto) — Remove stale system context and claude session files

  Completed: Stale system context removed; Obsolete claude session files deleted

COMMITS 26/04/08-11:26 C200155 [+] [db-schema-refactor] [task] (auto) — Update system context and memory files after CLI session 9315de75

  Completed: System context refreshed; Memory files updated for session 9315de75
---

## GROUP: tagging-system — Tag management, linking, and unified tagging across layers (new)
<!-- GROUP_SLUG: tagging-system -->
<!-- GROUP_TYPE: new -->

PROMPTS 26/03/14-13:59 P100042 [+] [tagging-system] [feature] (claude) — Link commits to prompt IDs within sessions

  Requirements: Create bidirectional link between commits and prompt IDs
  Completed: Created commit-to-prompt relationships in database (5 real links established)
  Action items: Verify all historical commits are linked to their source prompts (acceptance: All commits show prompt_source_id in queries)

PROMPTS 26/03/15-16:47 P100045 [+] [tagging-system] [feature] (claude) — Add pagination to history, chats, and commits views

  Requirements: Implement pagination UI with < > navigation showing current/total counts; Apply pagination to History, Chats, and Commits tabs
  Completed: Updated _load_unified_history() to read history.jsonl + archives (204 entries); Added pagination controls to frontend views
  Action items: Test pagination navigation across all three tabs (acceptance: Users can navigate through pages and see entry count)

PROMPTS 26/03/15-17:28 P100046 [+] [tagging-system] [feature] (claude) — Deduplicate tags and add removal (x) button

  Requirements: Verify no duplicate tags across system; Add UI option to remove tags affecting all screens
  Completed: Confirmed 149 tags with 0 duplicates; Backend uses ON CONFLICT DO NOTHING for tag insertion; Added tag removal UI with impact across History/Chat/Commits
  Action items: Verify tag removal cascades to all linked entities (acceptance: Removing a tag updates all screens in real-time)

PROMPTS 26/03/15-17:44 P100047 [+] [tagging-system] [task] (claude) — Validate tagging architecture across sessions/prompts/commits

  Requirements: Verify session-level tags, prompt-level tags, and commit-to-prompt linkage; Confirm all relationships are properly mapped
  Completed: Validated history.py _load_unified_history reads archives; Confirmed history.js uses data-ts attributes; Verified prompt-to-commit linking integrity
  Action items: Document the complete tagging relationship schema (acceptance: Architecture diagram shows all tag levels and linkages)

PROMPTS 26/03/15-18:11 P100048 [+] [tagging-system] [feature] (claude) — Link commits to prompts in Chat view instead of session-level

  Requirements: Show commits grouped by their source prompt in Chat view; Add prompt_source_id to commit data structure
  Completed: /history/commits endpoint updated to return prompt_source_id; Frontend _commitData.commits structure includes prompt linking
  Action items: Test Chat view displays commits under correct prompts (acceptance: Commits appear grouped by parent prompt in UI)

PROMPTS 26/03/15-23:13 P100060 [+] [tagging-system] [task] (claude) — Optimize database schema for tagging and memory efficiency

  Requirements: Verify database schema supports tagging use case; Confirm saving mechanism is optimal for memory management
  Completed: Added phase, feature, session_id as real columns in core/database.py; Reviewed and optimized tag storage structure
  Action items: Benchmark query performance with new schema (acceptance: Tag queries execute within target time limits)

PROMPTS 26/03/15-23:29 P100061 [+] [tagging-system] [feature] (claude) — Implement 5-step memory system and add entities summary endpoint

  Requirements: Align tagging to 5-step memory model; Add ability to retrieve detailed project information; Support feature/bug/task management
  Completed: Created GET /entities/summary endpoint in entities.py; Implemented three enhancements for memory retrieval
  Action items: Test summary endpoint returns accurate project feature/bug/task counts (acceptance: Endpoint provides complete entity overview)

PROMPTS 26/03/15-23:49 P100063 [+] [tagging-system] [feature] (claude) — Add metrics table for prompt count and memory status check

  Requirements: Create management table to track prompt count; Display /memory status and run recommendation to user; Run check on project upload
  Completed: Assistant outlined implementation approach
  Action items: Create mng_metrics table tracking prompt counts (acceptance: Table populated and /memory status endpoint returns count); Add upload-time memory check (acceptance: Project upload triggers memory status check)

PROMPTS 26/03/16-01:26 P100066 [+] [tagging-system] [task] (claude) — Audit tag usage and memory improvements from summarization

  Requirements: Verify tags are properly used across system; Assess memory improvement from summarization; Evaluate MCP enhancement potential
  Completed: Audited event_tags system across chat/history/sync; Identified and documented tagging gaps
  Action items: Review memory compression metrics post-summarization (acceptance: Memory usage reduced by X% measured)

PROMPTS 26/03/16-01:34 P100067 [+] [tagging-system] [task] (claude) — Summarize all system improvements and performance impact

  Requirements: Provide comprehensive improvement summary; Assess memory performance gains; Evaluate workflow and project management capabilities
  Completed: Created 7-part improvement summary; Documented transition from raw JSONL to tagged system
  Action items: Measure end-to-end system performance improvement (acceptance: Performance benchmarks show improvement vs baseline)

PROMPTS 26/03/16-18:52 P100072 [+] [tagging-system] [feature] (claude) — Locate pipeline configuration and restore parent-child support

  Requirements: Find where default pipeline is configured; Restore parent-child relationships (UI -> dropbox); Link pipeline to workflow engine
  Completed: Identified pipeline configuration in ui/backend/core/work_item_pipeline.py; Documented Planner tab 'Run Pipeline' mechanism
  Action items: Re-implement parent-child work item relationships (acceptance: Parent-child links visible in UI and persist in DB)

PROMPTS 26/03/17-18:50 P100081 [+] [tagging-system] [feature] (claude) — Reorganize Planner and Workflow tabs with tag-based mapping

  Requirements: Align Planner and Workflow features; Use tagging system for prompt/commit mapping; Implement approval workflow for AI suggestions
  Completed: Renamed 'Workflow' → 'Pipelines' in main.js PROJECT_TABS; Renamed 'Prompts' → 'Roles'; Updated tab navigation in sidebar
  Action items: Test all renamed tabs function correctly (acceptance: All Planner/Pipeline/Roles tabs accessible and functional)

PROMPTS 26/03/18-12:00 P100087 [+] [tagging-system] [task] (claude) — Remove legacy graph references and clarify mng_graph table ownership

  Requirements: Clean up unused mng_graph_* references; Document how graph tables should be managed; Verify server-side management vs client-side
  Completed: Eliminated mng_graph_* references from 4 files including routers/graph_workflows.py
  Action items: Confirm graph functionality removed completely (acceptance: No mng_graph tables referenced in codebase)

PROMPTS 26/03/31-18:48 P100097 [+] [tagging-system] [task] (claude_cli) — Verify complete tagging system implementation

  Requirements: Review all tagging functionality matches requirements; Verify mng_ai_tags_relations table exists and is used; Confirm all event types capture tags
  Completed: Reviewed tagging implementation across prompts, commits, history
  Action items: Create missing mng_ai_tags_relations table if needed (acceptance: Table exists and query references work)

PROMPTS 26/04/01-01:56 P100116 [+] [tagging-system] [feature] (claude_cli) — Implement merge tags feature with drag-drop in Planner

  Requirements: Add drag-and-drop UI to Planner tab; Implement feature merge when dropped on another feature; Update source feature with target feature ID
  Completed: Designed merge tags feature with drag-drop behavior
  Action items: Implement drag-drop listeners in Planner view (acceptance: Users can drag features and merge succeeds); Update database to reflect merged tags (acceptance: Source feature retains metadata and links to target)

PROMPTS 26/04/01-08:39 P100120 [+] [tagging-system] [bug] (claude_cli) — Fix critical database schema errors in routes

  Requirements: Fix 'event_type' column missing error in route_history.py line 228; Fix 'log' undefined error; Fix 'c.id' missing column error in route_entities.py line 1033
  Completed: Fixed query references to use correct column names
  Action items: Test all three routes return data without column errors (acceptance: Queries execute without schema validation errors)

PROMPTS 26/04/01-08:52 P100121 [+] [tagging-system] [task] (claude_cli) — Clean up Lifecycle tags and fix bug counter display

  Requirements: Remove irrelevant Lifecycle tagging; Fix bug counter update next to tag; Ensure AI-suggested bugs appear under ai_suggestion with tag
  Completed: Identified Lifecycle tags issue; Documented bug categorization requirements
  Action items: Remove Lifecycle tag from bug/feature/task classifications (acceptance: Lifecycle tag no longer appears on work items); Fix bug counter increment logic (acceptance: Bug count updates when new bug added)

PROMPTS 26/04/01-12:25 P100123 [+] [tagging-system] [task] (claude_cli) — Evaluate necessity of Lifecycle tags

  Requirements: Determine if Lifecycle tags serve a purpose
  Completed: Reviewed Lifecycle tag usage
  Action items: Document Lifecycle tag removal decision (acceptance: Decision documented with rationale)

PROMPTS 26/04/01-12:27 P100124 [+] [tagging-system] [bug] (claude_cli) — Remove irrelevant Lifecycle tags from work items

  Requirements: Remove Lifecycle tags appearing on bugs, features, and tasks
  Completed: Identified Lifecycle tags for removal across work item types
  Action items: Delete Lifecycle tag entries from database (acceptance: Tag no longer visible on any work items)

PROMPTS 26/04/01-12:49 P100125 [+] [tagging-system] [feature] (claude_cli) — Reorganize AI suggestions and create AI category section

  Requirements: Move AI-suggested bugs to ai_suggestion category; Prevent user creation of tags under ai_suggestion; Create separate AI section for AI-generated suggestions; Create main categories for AI suggestions
  Completed: Added tag routing in backend; Enhanced entities view with API updates; Updated AI rules and memory
  Action items: Test AI suggestions appear in dedicated section (acceptance: AI(SUGGESTED) tags visible in separate AI section); Verify users cannot manually create ai_suggestion tags (acceptance: Create tag UI blocks ai_suggestion category)

PROMPTS 26/04/03-19:37 P100128 [+] [tagging-system] [bug] (claude_cli) — Fix tag UI display error and 422 validation issue

  Requirements: Fix [object object] display error when adding tags; Resolve 422 unprocessable entity backend error; Verify commit-prompt tag linking works
  Completed: Updated backend tag handling to return proper string format
  Action items: Test tag creation returns correct JSON without [object object] (acceptance: Tag display shows proper tag names in UI); Verify 422 errors resolved (acceptance: Tags save successfully with 200 response)

PROMPTS 26/04/05-11:09 P100131 [+] [tagging-system] [bug] (claude_cli) — Restore tag loading and category suggestion in UI

  Requirements: Fix tag loading when adding tags to prompts/commits; Restore ability to select from existing tags by category; Re-enable tag persistence for previously added tags
  Completed: Updated system context and history loading
  Action items: Test existing tags load when tag input focused (acceptance: Tag dropdown shows all existing tags by category); Verify previously attached tags reappear (acceptance: Tags persist and display correctly after reload)

PROMPTS 26/04/05-23:06 P100141 [+] [tagging-system] [task] (claude_cli) — Make 'Show LLM' tag visible in UI

  Requirements: Add Show LLM option to tag visibility controls
  Completed: Identified Show LLM tag visibility requirement
  Action items: Add Show LLM toggle to tag view options (acceptance: Tag visibility toggle available in UI)

PROMPTS 26/04/08-22:37 P100175 [+] [tagging-system] [bug] (claude_cli) — Fix tag property panel display when tag clicked

  Requirements: Display tag properties on left panel when tag clicked (like work_items); Fix catName undefined error in _renderDrawer()
  Completed: Fixed catName scope issue by using v.category_name || _plannerState.selectedCatName; Updated _renderDrawer() function
  Action items: Test tag property panel appears on left side when tag clicked (acceptance: Tag properties display without errors)

PROMPTS 26/04/09-00:52 P100182 [+] [tagging-system] [task] (claude_cli) — Update date format and remove non-work-item tags

  Requirements: Change date format to yy/mm/dd-hh:mm; Remove non-work-item tags (Shared-memory, billing) from work_items view
  Completed: Updated fmtDate function in entities.js (+6/-5); Implemented _wiPanelDelete with confirmation flow; Added × button for work item deletion
  Action items: Test delete confirmation shows before removal (acceptance: Clicking × shows confirm dialog then removes item)

PROMPTS 26/04/09-01:58 P100187 [+] [tagging-system] [feature] (claude_cli) — Update AI tag format to category:name with suggestion colors

  Requirements: Change ai_tags format to feature:name, bug:name, task:name; Show existing tag suggestions with different color for new tags; Update tag suggestion and display logic
  Completed: Updated tag routing in route_work_items.py; Enhanced _renderWiPanel with new tag format (+27/-12)
  Action items: Test AI tag suggestions show as category:name format (acceptance: Tags display as 'bug:auth' and 'feature:dropbox' format); Verify new tags display in different color than existing (acceptance: Color distinction visible between existing/new suggestions)

PROMPTS 26/04/09-02:54 P100191 [+] [tagging-system] [feature] (claude_cli) — Improve AI tag suggestion priority to task/bug/feature first

  Requirements: Suggest task/bug/feature tags from categories first; Fall back to new task/bug/feature if no match found; Can suggest metadata tags (doc_type, phase) as secondary
  Completed: Updated AI suggestion logic with category prioritization; Background matching improved to handle 103 AI(EXISTS) + 15 AI(NEW)
  Action items: Test suggestion priority matches task/bug/feature before metadata (acceptance: Primary category suggestions appear before secondary tags)

PROMPTS 26/04/09-09:42 P100193 [+] [tagging-system] [bug] (claude_cli) — Fix AI tag population and add refresh button for work items

  Requirements: Fix empty AI suggestions showing only AI(EXISTS); Add refresh button instead of new work_item option (since creation from UI unavailable); Ensure AI tags properly populate
  Completed: Fixed MemoryPromotion._match_new_work_item (+26/-0); Updated MemoryPromotion.extract_work_items_from_events; Added _backlink_tag_to_events method (+46/-0)
  Action items: Test refresh button loads latest work items and updates AI suggestions (acceptance: Refresh populates AI(NEW) suggestions from recent events)

PROMPTS 26/04/09-10:45 P100194 [+] [tagging-system] [task] (claude_cli) — Document AI tag and work item prompt locations

  Requirements: Provide location reference for all AI tag and work item prompts
  Completed: Documented work_item_extraction in prompts/memory/work_items/work_item_extraction.md; Mapped prompts to their usage locations
  Action items: Create prompt index documentation (acceptance: All prompt locations documented and indexed)

PROMPTS 26/04/09-10:52 P100195 [+] [tagging-system] [task] (claude_cli) — Consolidate duplicate internal memory work items

  Requirements: Consolidate work_item #20398 and similar internal operations into single work item; Prevent duplicate entries for update_memory/sync_memory operations
  Completed: Fixed work_item_extraction prompt to exclude internal AI memory operations; Updated extraction rules to prevent duplicate internal work items
  Action items: Verify single sync_memory work item consolidates all internal operations (acceptance: Only one internal work item per session type)

PROMPTS 26/04/09-11:00 P100196 [+] [tagging-system] [task] (claude_cli) — Provide query for retrieving prompts/commits/events per work item

  Requirements: Share SQL query used for work item event retrieval; Verify accuracy for work_item #20399 (ai-tags-query)
  Completed: Verified event_count reduced from 221 → 10 entries; Updated query to show only digest events from work item's session
  Action items: Document complete SQL query for work item event retrieval (acceptance: Query documented and tested for accuracy)

PROMPTS 26/04/09-12:16 P100197 [+] [tagging-system] [feature] (claude_cli) — Add periodic tag confirmation mechanism to session management

  Requirements: Force tag addition at session start; Ask user every 5-10 prompts if prompts relate to added tags; Handle long sessions with multiple compressions
  Completed: Updated server.py list_tools with new mechanism (+12/-5); Documented session compression and tag confirmation flow
  Action items: Implement periodic tag confirmation dialog every 5-10 prompts (acceptance: User prompted for tag confirmation at intervals); Test tag confirmation updates session metadata (acceptance: Confirmed tags appear in session_tags)

PROMPTS 26/04/09-13:44 P100198 [+] [tagging-system] [feature] (claude_cli) — Make /tag skill available in Claude Code

  Requirements: Implement /tag skill for aicli; Allow tagging prompts as phase:development feature:work-items-x
  Completed: Created /tag skill in Claude Code; Demonstrated usage with proper session tags
  Action items: Verify /tag skill works in new session (acceptance: Running /tag updates session tags correctly)

PROMPTS 26/04/10-15:12 P100203 [+] [tagging-system] [feature] (claude_cli) — Improve AI tag approval flow and work item transitions

  Requirements: Remove confirm button for AI tag approval (keep delete only); Move confirmed work item from list to tag section; Handle new tag creation with proper linking
  Completed: Updated _wiPanelApproveTag to remove confirm after approval; Implemented work item removal from pending list on tag confirmation
  Action items: Test AI(EXISTS) approval removes work item from list (acceptance: Item moves to tag section, no confirm button shown); Test new tag creation links work item properly (acceptance: Work item appears under newly created tag)

PROMPTS 26/04/10-15:20 P100204 [+] [tagging-system] [feature] (claude_cli) — Enable /tag command for session tagging without new session

  Requirements: Allow /tag usage in current session to tag prompts
  Completed: /tag command integrated into current session; Updates .agent-context and calls PUT /history/session-tags
  Action items: Test /tag command applies tags to all session prompts (acceptance: Tags persist in history after session ends)

PROMPTS 26/04/10-15:23 P100205 [+] [tagging-system] [bug] (claude_cli) — Resolve /tag skill name conflict in Claude Code

  Requirements: Fix 'unknown skill tag' error from reserved name conflict; Implement alternative skill naming
  Completed: Renamed /tag to /ac in Claude Code; Session tagged with phase:development feature:work_items
  Action items: Document /ac as the correct command for tagging (acceptance: Users use /ac instead of /tag without errors)

PROMPTS 26/04/10-15:41 P100206 [+] [tagging-system] [bug] (claude_cli) — Fix secondary AI tags disappearing on approval

  Requirements: Prevent work item disappearance when secondary tag (doc_type, phase) added; Keep work item in list with metadata tag attached
  Completed: Fixed _wiSecApprove to handle secondary tags correctly; Updated backend migrations m021_rename_work_item_columns and m022_backfill_event_work_item_ids
  Action items: Test secondary tag approval keeps work item in list (acceptance: Item stays visible with tag added to metadata)

PROMPTS 26/04/12-11:10 P100211 [+] [tagging-system] [task] (claude_cli) — Update session to feature:planner tag

  Requirements: Set session tags to phase:development and feature:planner
  Completed: Session tagged with phase:development and feature:planner; All prompts and commits tagged accordingly
  Action items: Verify all session events show planner feature tag (acceptance: All session prompts/commits display feature:planner)

PROMPTS 26/04/12-20:31 P100217 [+] [tagging-system] [task] (claude_cli) — Add feature:feature_snapshot session tag

  Requirements: Add feature:feature_snapshot to session tags
  Completed: Session tag updated to feature:feature_snapshot
  Action items: Confirm feature_snapshot tag applied to session (acceptance: New prompts in session receive feature_snapshot tag)

PROMPTS 26/04/13-18:12 P100228 [+] [tagging-system] [task] (claude_cli) — Remove legacy tags and consolidate to user-defined tags only

  Requirements: Show only user-merged/updated tags in event display; Remove legacy system tags from view; Clean up corrupt tag entries
  Completed: Fixed 6 corrupt session_summary events with JSON array tags; Stripped system meta tags from event display; Implemented backfill_event_tags (+191/-0) in route_admin.py
  Action items: Test event tags show only user-defined entries (acceptance: Legacy tags removed, only user tags visible)

COMMITS 26/04/12-00:03 C200156 [+] [tagging-system] [task] (auto) — Refactor memory promotion and planner for work item AI columns

  Completed: Added m025_rename_work_item_ai_columns migration in backend/core/db_migrations.py; Updated MemoryPlanner class methods to use renamed columns in backend/memory/memory_planner.py; Refactored MemoryPromotion.promote_work_item and added promote_all_work_items in backend/memory/memory_promotion.py

COMMITS 26/04/12-11:08 C200157 [+] [tagging-system] [feature] (auto) — Add work item embedding and memory search handling

  Completed: Implemented _handle_search_memory in backend/agents/tools/tool_memory.py; Added _embed_work_item function in backend/memory/memory_promotion.py; Enhanced MemoryPromotion.promote_work_item and extract_work_items_from_events methods

COMMITS 26/04/12-20:31 C200158 [+] [tagging-system] [feature] (auto) — Add deliveries support and update tag routing

  Completed: Created m028_add_deliveries migration in backend/core/db_migrations.py; Added DeliveryCreate and TagUpdate schemas in backend/routers/route_tags.py; Enhanced _row_to_tag and _row_to_tag_detail conversion functions; Updated update_tag method and added list_deliveries endpoint

COMMITS 26/04/12-21:15 C200159 [+] [tagging-system] [feature] (auto) — Add feature snapshot memory system with LLM integration

  Completed: Created m029_feature_snapshot migration in backend/core/db_migrations.py; Implemented MemoryFeatureSnapshot class with LLM-based code analysis in backend/memory/memory_feature_snapshot.py; Added helper methods: _parse_json, _slugify, _get_code_dir, _load_baseline, _build_user_message

COMMITS 26/04/12-22:39 C200160 [+] [tagging-system] [feature] (auto) — Add pipeline run tracking and logging system

  Completed: Created m030_pipeline_runs migration in backend/core/db_migrations.py; Implemented pipeline_run_sync and pipeline_run context managers in backend/core/pipeline_log.py; Added _insert_run and _finish_run functions for tracking pipeline execution; Updated git commit processing in backend/routers/route_git.py background tasks

COMMITS 26/04/13-14:49 C200161 [+] [tagging-system] [task] (auto) — Clean up stale agent context and legacy system files


COMMITS 26/04/13-17:07 C200162 [+] [tagging-system] [feature] (auto) — Add database maintenance utilities and vacuum endpoint

  Completed: Implemented run_maintenance and run_maintenance_async functions in backend/data/clean_pg_db.py; Added database connection and size conversion utilities (_raw_conn, _bytes_to_mb); Added CLI interface in backend/data/clean_pg_db.py; Created db_vacuum endpoint in backend/routers/route_admin.py
---

## GROUP: performance-optimization — Database query optimization and system speed improvements (new)
<!-- GROUP_SLUG: performance-optimization -->
<!-- GROUP_TYPE: new -->

PROMPTS 26/03/10-00:52 P100025 [+] [performance-optimization] [performance] (claude) — Cache tags in memory on project load to eliminate repeated DB calls

  Requirements: Avoid multiple SQL calls for tags; Load tags once into memory when project accessed; Update DB only on save
  Completed: Modified chat.js _pickerPopulateCats() to read from cache instead of DB

PROMPTS 26/03/10-01:11 P100026 [+] [performance-optimization] [feature] (claude) — Design nested tags hierarchy beyond current 2-level category/tag structure

  Requirements: Optimize SQL queries to load once per project; Support nested tags (tags under tags); Provide design before implementation
  Completed: Designed entity_values schema change to support parent_tag_id column for nested hierarchy
  Action items: Implement nested tags schema and UI in tag picker (acceptance: Users can create tags nested under other tags and hierarchy loads efficiently)

PROMPTS 26/03/17-13:33 P100076 [+] [performance-optimization] [bug] (claude) — Fix slow project summary and history loading with pagination and loading indicators

  Requirements: Investigate slow project load time; Fix missing project in recent list ordering; Add UX flow to explain loading state
  Completed: Added pagination to history and loading flow indicators (assistant-described work only)
  Action items: Verify history pagination and summary load performance (acceptance: Project loads in <2s, summary/history visible with clear loading state)

PROMPTS 26/04/09-13:55 P100199 [+] [performance-optimization] [bug] (claude_cli) — Optimize planner tab and work item queries with composite database indexes

  Requirements: Fix slow planner tabs and work items loading; Ensure query declarations at top of files per convention
  Completed: Added m020 migration in db_migrations.py with 5 composite indexes on mem_ai_events(project_id, session_id); Cleaned up TagBySourceIdBody and ValueCreate in route_entities.py; Simplified create_value() method
  Action items: Verify planner tab load time after index deployment (acceptance: Planner tabs load <1s with new indexes on mem_ai_events)

PROMPTS 26/04/09-14:21 P100200 [+] [performance-optimization] [bug] (claude_cli) — Clarify DIGEST column purpose and fix unlinked work items display with NULLS LAST sorting

  Requirements: Explain DIGEST column vs event counter; Identify why work items appear without linked prompts/commits; Understand work item creation source
  Completed: Added NULLS LAST fix to route_work_items.py get_unlinked_work_items(); Updated entities.js _renderWiPanel() and _renderWorkItemTable() to show proper event counts
  Action items: Verify work items 20428 and similar display correct event/prompt linkage (acceptance: All work items show source (prompt/commit) and accurate event counts)

PROMPTS 26/04/09-16:07 P100201 [+] [performance-optimization] [bug] (claude_cli) — Fix missing work item counters and prompts display for commit-sourced items

  Requirements: Restore event/prompt counters in UI; Handle work items without events correctly; Ensure work items link properly: events→prompts→commits chain
  Completed: Applied _SQL_UNLINKED_WORK_ITEMS fix in route_work_items.py get_unlinked_work_items() for commit count; Updated entities.js _renderWiPanel() to display counters correctly
  Action items: Verify work item 20431 and similar old items display correctly (acceptance: Counters visible for all work items, chain events→prompts→commits intact)

PROMPTS 26/04/15-21:12 P100236 [+] [performance-optimization] [bug] (claude_cli) — Fix incomplete prompt loading and optimize history sorting with correct limit

  Requirements: Load all prompts on startup, not just recent subset; Investigate _system/session files accumulation; Fix history sorting and pagination
  Completed: Fixed route_history.py chat_history() sorting with limit=500 and NULLS LAST; Updated _normalize_jsonl_entry() to properly parse all 389 historical entries; Clarified that old code was reading DB-only subset instead of complete history
  Action items: Clean up obsolete _system/session files and document retention policy (acceptance: Only active session files in _system/, load time <3s for all 389 prompts)
---

## GROUP: work-items-features — Work items UI, drag-drop, snapshots, and feature linking (new)
<!-- GROUP_SLUG: work-items-features -->
<!-- GROUP_TYPE: new -->

PROMPTS 26/03/15-23:49 P100063 [+] [work-items-features] [feature] (claude) — 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many pr


PROMPTS 26/04/01-01:11 P100112 [+] [work-items-features] [feature] (claude_cli) — Implement 1 and 2. pipeline is trigerred from the planer tab. for example there 


PROMPTS 26/04/01-01:17 P100113 [+] [work-items-features] [feature] (claude_cli) — Why there is no embedding in project_facts and work_items ? this is not suppose 


PROMPTS 26/04/01-01:39 P100114 [+] [work-items-features] [feature] (claude_cli) — Not sure if you remember the previous memory config. if you do (you can check ai


PROMPTS 26/04/01-01:43 P100115 [+] [work-items-features] [feature] (claude_cli) — yes . fix that all 


PROMPTS 26/04/01-08:52 P100121 [+] [work-items-features] [feature] (claude_cli) — I would like to work on the planer tab - I do see Lifecucle tagging which I am n


PROMPTS 26/04/06-17:45 P100155 [+] [work-items-features] [feature] (claude_cli) — is it possilbe to actual move the work_item (drag) and drop that under the item 


PROMPTS 26/04/06-18:02 P100156 [+] [work-items-features] [feature] (claude_cli) — There are some issue - when I drag all tabs that I hoover on top are marked (not


PROMPTS 26/04/06-22:52 P100157 [+] [work-items-features] [feature] (claude_cli) — Looks better, still when I drag work_item - I do not see that droped under the i


PROMPTS 26/04/06-23:02 P100158 [+] [work-items-features] [feature] (claude_cli) — I would like to be able to move work_item back to work_item or to another items.


PROMPTS 26/04/07-01:11 P100159 [+] [work-items-features] [feature] (claude_cli) — can you update all memory_items (maybe run /memory) to have an uodated data 


PROMPTS 26/04/07-01:21 P100160 [+] [work-items-features] [feature] (claude_cli) — I do have some errors loading data - route_work_items line 249 - cur.execute(_SQ


PROMPTS 26/04/07-14:59 P100161 [+] [work-items-features] [feature] (claude_cli) — Can you use aiCli_memeory to describe the followng : how flow works from mirror.


PROMPTS 26/04/07-15:02 P100162 [+] [work-items-features] [feature] (claude_cli) — Can you use aiCli_memeory to describe the followng : how flow works from mirror.


PROMPTS 26/04/07-16:10 P100163 [+] [work-items-features] [feature] (claude_cli) — In addtion to your reccomendation, I would like to check the following -  mem_ai


PROMPTS 26/04/07-16:46 P100164 [+] [work-items-features] [feature] (claude_cli) — dont you have any moemry, did you see the previous file you din - aicli_memoy.md


PROMPTS 26/04/07-17:11 P100165 [+] [work-items-features] [feature] (claude_cli) — I still see the columns in commit table - diif_summery and diff_details . is it 


PROMPTS 26/04/07-21:20 P100166 [+] [work-items-features] [feature] (claude_cli) — I would like to understand the commit table - do you have my previous comment? m


PROMPTS 26/04/07-23:23 P100167 [+] [work-items-features] [feature] (claude_cli) — Where simple extraction flow can be something like that:  pr_tags_map   WHERE re


PROMPTS 26/04/08-17:50 P100171 [+] [work-items-features] [feature] (claude_cli) — Can you explain how commit data statitics are connected to work_items ? Is there


PROMPTS 26/04/08-17:59 P100172 [+] [work-items-features] [feature] (claude_cli) — three is link from prompts to commits. each five prompts summeries to event, whi


PROMPTS 26/04/08-18:40 P100173 [+] [work-items-features] [feature] (claude_cli) — There is a problem to load work_items - line 331 in route_work_items -column w.a


PROMPTS 26/04/08-23:37 P100177 [+] [work-items-features] [feature] (claude_cli) — I would like to understand how work_item are populated. work_item suppose to be 


PROMPTS 26/04/09-00:28 P100178 [+] [work-items-features] [feature] (claude_cli) — In the UI - work_items shows as a row. I would each row to have name - desc colu


PROMPTS 26/04/09-01:13 P100184 [+] [work-items-features] [feature] (claude_cli) — I would like that the header wont disappear when user scroll down in work_items.


PROMPTS 26/04/09-03:04 P100192 [+] [work-items-features] [feature] (claude_cli) — Can you explain how do I see work_item #20006 as the one that was last updated ?


PROMPTS 26/04/09-16:07 P100201 [+] [work-items-features] [feature] (claude_cli) — now I dont see the counter or the promts. also, I still see work item   that  ar


PROMPTS 26/04/10-14:51 P100202 [+] [work-items-features] [feature] (claude_cli) — I still dont understand how there are work_items without any linked prompts. can


PROMPTS 26/04/12-14:11 P100214 [+] [work-items-features] [feature] (claude_cli) — I am planning to add a layer that will merge planner_tags with wor_item - this l


PROMPTS 26/04/12-20:06 P100216 [+] [work-items-features] [feature] (claude_cli) — This start to look good. I would like to add one more column - deliveries that w


PROMPTS 26/04/12-20:34 P100218 [+] [work-items-features] [feature] (claude_cli) — Feature_snapshot  I would like to create the final stage - mem_ai_feature_snapsh


PROMPTS 26/03/09-04:08 P100020 [+] [work-items-features] [feature] (claude) — Assuming I will improve the project management page, workflow processes. can you


PROMPTS 26/03/09-17:56 P100021 [+] [work-items-features] [feature] (claude) — The last prompts was asking for a new feature (clinet install/ support multiple 


PROMPTS 26/03/09-23:51 P100022 [+] [work-items-features] [feature] (claude) — I dont think your update works. lets start from Planer - there is not need to ha


PROMPTS 26/03/10-01:14 P100027 [+] [work-items-features] [feature] (claude) — yes. just to clarify when I add login - it will be first level only ? 


PROMPTS 26/03/10-01:19 P100028 [+] [work-items-features] [feature] (claude) — yes


PROMPTS 26/03/10-02:00 P100030 [+] [work-items-features] [feature] (claude) — why there is sometime problem to restart the app (I do see that beckend is exite


PROMPTS 26/03/10-02:12 P100031 [+] [work-items-features] [feature] (claude) — I do see the save button - and when I save I do see the tag, when I am checking 


PROMPTS 26/03/10-02:40 P100033 [+] [work-items-features] [feature] (claude) — can you run /memory, and make the UI more clear. add your sujjestion in a clear 


PROMPTS 26/03/10-02:57 P100034 [+] [work-items-features] [feature] (claude) — can you run /memory and run some tests? I do not see any sujjestion on all the e


PROMPTS 26/03/10-03:14 P100035 [+] [work-items-features] [feature] (claude) — Are you using the mcp server in order to reciave all project information ? Also,


PROMPTS 26/03/10-03:16 P100036 [+] [work-items-features] [feature] (claude) — hellow, how are you ?


PROMPTS 26/03/10-03:22 P100037 [+] [work-items-features] [feature] (claude) — I understand the issue. I am using your claude cli and hooks to store propts and


PROMPTS 26/03/14-11:10 P100039 [+] [work-items-features] [feature] (claude) — I do have some concern how commit/hash are linked to prompts/llm answers. also a


PROMPTS 26/03/15-18:15 P100049 [+] [work-items-features] [feature] (claude) — let me summerise not. first run /memroy to update all sumeeries, db tagging and 


PROMPTS 26/03/15-19:42 P100050 [+] [work-items-features] [feature] (claude) — I would like to set that up , and also add that to new prokect as autoamted set 


PROMPTS 26/03/15-20:33 P100051 [+] [work-items-features] [feature] (claude) — The last commit was b255366 which suppose to be linked to the last prompt. it di


PROMPTS 26/03/15-20:44 P100052 [+] [work-items-features] [feature] (claude) — When I run memory through the aiCli - I did see some usefull suggestion that app


PROMPTS 26/03/15-22:57 P100059 [+] [work-items-features] [feature] (claude) — It looks good and working as expected. the issue now is how it is linked to Hist


PROMPTS 26/03/15-23:38 P100062 [+] [work-items-features] [feature] (claude) — Is there is any addiotnal improvement that I can implemet for having full memroy


PROMPTS 26/03/16-00:19 P100064 [+] [work-items-features] [feature] (claude) — I would like to optimise the code : check each file, make sure code is in used a


PROMPTS 26/03/16-00:48 P100065 [+] [work-items-features] [feature] (claude) — I have started to look in some other solution like https://github.com/danshapiro


PROMPTS 26/03/16-18:02 P100069 [+] [work-items-features] [feature] (claude) — Keys are stored at my .env file which you can load - for claude api the key is u


PROMPTS 26/03/16-18:26 P100070 [+] [work-items-features] [feature] (claude) — are you using the mcp now? 


PROMPTS 26/03/16-18:34 P100071 [+] [work-items-features] [feature] (claude) — I would like to start working on the workflows - the goal is to be able to be si


PROMPTS 26/03/16-19:00 P100073 [+] [work-items-features] [feature] (claude) — I do mention to sotre the prompts in database, would there be a way to change th


PROMPTS 26/03/16-19:02 P100074 [+] [work-items-features] [feature] (claude) — yes


PROMPTS 26/03/17-18:28 P100079 [+] [work-items-features] [feature] (claude) — What is the claude agent sdk is uded for can it be used for my use cases for mut


PROMPTS 26/03/17-18:29 P100080 [+] [work-items-features] [feature] (claude) — I dont see nay changes from the last improvement - current planner do not suppos


PROMPTS 26/03/17-20:13 P100082 [+] [work-items-features] [feature] (claude) — Planner works partial - I do see the nested work on some category like doc_type 


PROMPTS 26/03/18-12:51 P100088 [+] [work-items-features] [feature] (claude) — I would like to make sure the client table are also aligned - for example mng_se


PROMPTS 26/03/18-16:00 P100090 [+] [work-items-features] [feature] (claude) — That is correct. it is bed pattern to use clinet name. there is already mng_user


PROMPTS 26/03/18-17:44 P100091 [+] [work-items-features] [feature] (claude) — it looks like it is a bit broken, I have got an error - '_Database' object has n


PROMPTS 26/03/18-18:15 P100092 [+] [work-items-features] [feature] (claude) — There are some error - on the first load, it lookls like Backend is failing (aft


PROMPTS 26/03/31-16:35 P100095 [+] [work-items-features] [feature] (claude_cli) — Is it makes more sense, before I continue to the secopnd phase (refactor embeddi


PROMPTS 26/04/01-00:15 P100108 [+] [work-items-features] [feature] (claude_cli) — test prompt after migration


PROMPTS 26/04/01-00:38 P100110 [+] [work-items-features] [feature] (claude_cli) — test after mem_ai cleanup


PROMPTS 26/04/01-08:26 P100118 [+] [work-items-features] [feature] (claude_cli) — Under backend folder, I do see a workspace foldr. is it used ? 


PROMPTS 26/04/01-08:27 P100119 [+] [work-items-features] [feature] (claude_cli) — plese delete that 


PROMPTS 26/04/05-12:39 P100132 [+] [work-items-features] [feature] (claude_cli) — I have got an error on /history/commits/sync?project=aicli rest api in     execu


PROMPTS 26/04/05-23:33 P100142 [+] [work-items-features] [feature] (claude_cli) — I would like to build the aicli_memory.md for scratch in order to get a final vi


PROMPTS 26/04/05-23:44 P100143 [+] [work-items-features] [feature] (claude_cli) — About orocess_item / messeges - trigger in /memroy (for all new items at the mom


PROMPTS 26/04/06-00:00 P100144 [+] [work-items-features] [feature] (claude_cli) — test prompt after fix


PROMPTS 26/04/06-09:43 P100150 [+] [work-items-features] [feature] (claude_cli) — I have  got the following error -  cur.execute(b''.join(parts)) started  route_h


PROMPTS 26/04/06-09:54 P100151 [+] [work-items-features] [feature] (claude_cli) — I still dont see the same issue in route_history line 470. cur.execute(b''.join(


PROMPTS 26/04/08-11:31 P100168 [+] [work-items-features] [feature] (claude_cli) — I do not see any update at the database 


PROMPTS 26/04/08-13:48 P100169 [+] [work-items-features] [feature] (claude_cli) — yes please


PROMPTS 26/04/08-13:51 P100170 [+] [work-items-features] [feature] (claude_cli) — can you explain where are the  prompts that used for update new commit ? 


PROMPTS 26/04/08-23:18 P100176 [+] [work-items-features] [feature] (claude_cli) — I do not see mem_mrr_commits_code populated on every commit. is that suppose to 


PROMPTS 26/04/09-01:05 P100183 [+] [work-items-features] [feature] (claude_cli) — What did you do now ?


PROMPTS 26/04/12-18:36 P100215 [+] [work-items-features] [feature] (claude_cli) — yes


PROMPTS 26/04/12-21:19 P100219 [+] [work-items-features] [feature] (claude_cli) — Assuming all will work properly. having a way to store all project history using


PROMPTS 26/04/12-22:10 P100220 [+] [work-items-features] [feature] (claude_cli) — How can I improve points 4 and 5 ? for point 4 - I did make prompts in sappasret


PROMPTS 26/04/12-22:15 P100221 [+] [work-items-features] [feature] (claude_cli) — ok. can you implement that. make sure dashboard is a new tab. pipeline will be a


PROMPTS 26/04/15-19:31 P100233 [+] [work-items-features] [feature] (claude_cli) — test: is hook-log working now after m050?


COMMITS 26/04/15-17:28 C200163 [+] [work-items-features] [task] (auto) — Remove stale agent context and system documentation files

  Completed: Deleted legacy _system/ agent context files

COMMITS 26/04/15-18:23 C200164 [+] [work-items-features] [task] (auto) — Clean up stale agent context and generated system files

  Completed: Deleted stale agent context and generated system files

COMMITS 26/04/15-18:32 C200165 [+] [work-items-features] [feature] (auto) — Add database migration for prompts source_id index

  Completed: backend/core/db_migrations.py: Added m050_prompts_source_id_index migration

COMMITS 26/04/15-23:45 C200166 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/15-23:59 C200167 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-00:11 C200168 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context and documentation files

  Completed: Deleted legacy _system/ agent context and documentation files

COMMITS 26/04/16-00:41 C200169 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-00:41 C200170 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-00:42 C200171 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-00:52 C200172 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-01:08 C200173 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context and documentation files

  Completed: Deleted legacy _system/ agent context and documentation files

COMMITS 26/04/16-09:43 C200174 [+] [work-items-features] [task] (auto) — Remove legacy _system/ agent context files

  Completed: Deleted legacy _system/ agent context files after CLI session

COMMITS 26/04/16-16:29 C200175 [+] [work-items-features] [task] (auto) — Update 63 files

  Completed: Modified 63 files with unspecified changes

COMMITS 26/04/16-16:51 C200176 [+] [work-items-features] [task] (auto) — Update 73 files

  Completed: Modified 73 files with unspecified changes

COMMITS 26/04/17-10:43 C200177 [+] [work-items-features] [task] (auto) — Update 63 files

  Completed: Modified 63 files with unspecified changes

COMMITS 26/04/17-11:55 C200178 [+] [work-items-features] [task] (auto) — Update 66 files

  Completed: Modified 66 files with unspecified changes

COMMITS 26/04/17-13:01 C200179 [+] [work-items-features] [task] (auto) — Update 69 files

  Completed: Modified 69 files with unspecified changes

COMMITS 26/04/17-13:27 C200180 [+] [work-items-features] [task] (auto) — Update 62 files

  Completed: Modified 62 files with unspecified changes

COMMITS 26/04/17-17:57 C200181 [+] [work-items-features] [task] (auto) — Update 65 files

  Completed: Modified 65 files with unspecified changes

COMMITS 26/04/17-18:15 C200182 [+] [work-items-features] [task] (auto) — Update 62 files

  Completed: Modified 62 files with unspecified changes

COMMITS 26/04/17-18:50 C200183 [+] [work-items-features] [task] (auto) — Update 58 files

  Completed: Modified 58 files with unspecified changes

COMMITS 26/04/17-18:59 C200184 [+] [work-items-features] [task] (auto) — Update 65 files

  Completed: Modified 65 files with unspecified changes

---

PROMPTS 26/04/17-00:00 P100266 [ ] [discovery] [feature] (auto) — Add pagination controls for prompts, chats, and commits lists

  Requirements:
  - Display total count of items (e.g., '24/204')
  - Add pagination controls (< >) in top right near filter tab
  - Apply same pagination to prompts, chats, and commits views
  - Load unified history from current and archived jsonl files

  Completed:
  - Updated `_load_unified_history()` to read history.jsonl + all history_*.jsonl archives, increased visible entries from 26 to 204 (code)
  - Commit efabeb5f: chore: update system files and history after claude session 03f774e9 (code)

  Action items:
  - Implement pagination UI controls in frontend for prompts, chats, and commits (acceptance: Pagination displays with < > buttons and item count indicator)

---

PROMPTS 26/04/17-00:00 P100267 [ ] [discovery] [feature] (auto) — Add tag management with deduplication and removal capability

  Requirements:
  - Verify no duplicate tags across history, chat, and commits
  - Implement tag removal (×) functionality affecting all screens
  - Align tag data across all views
  - Prevent duplicate tag inserts via backend constraints

  Completed:
  - Backend tag deduplication using ON CONFLICT DO NOTHING on inserts (code)
  - Frontend in-memory deduplication before API calls (code)
  - Commit 7d7445c2: feat: add entity routing and enhance history/chat UI views (code)

  Action items:
  - Complete tag removal (×) UI implementation across all screens (acceptance: Users can remove tags and changes propagate to history, chat, and commits)

---

PROMPTS 26/04/17-00:00 P100268 [ ] [discovery] [task] (auto) — Verify tag linking logic across sessions, prompts, and commits

  Requirements:
  - Confirm session-level tags added via Chat work correctly
  - Confirm prompt-level tags managed via History/Prompts work correctly
  - Verify commit-to-prompt tag linking is properly defined
  - Validate tag propagation logic across all components

  Completed:
  - Verified `_load_unified_history` reads current + archived jsonl files (code)
  - Verified history.js implements `_jumpToPrompt` with CSS.escape and `_removeTag` with × buttons (code)
  - Verified entities.py implements `_propagate_tags_phase` logic (code)
  - Commit 6f3cc130: chore: update system state and history after claude session (code)

  Action items:
  - Perform end-to-end testing of tag lifecycle across all features (acceptance: Tags correctly propagate from prompts to commits and vice versa)

---

PROMPTS 26/04/17-00:00 P100269 [ ] [discovery] [feature] (auto) — Link commits to individual prompts instead of session-level display

  Requirements:
  - Move commit display from session-level strip to per-prompt view
  - Ensure `/history/commits` endpoint returns `prompt_source_id`
  - Update History Chat view to show commits grouped by prompt
  - Maintain commit-to-prompt relationship consistency

  Completed:
  - Confirmed `/history/commits` endpoint returns `prompt_source_id` for each commit row (code)
  - Frontend `_commitData.commits` updated to receive prompt source IDs (code)
  - Updated History Chat view to display commits per prompt instead of per session (code)
  - Commit 6958c335: chore: update system docs and history after claude session 03f774e9 (code)

  Action items:
  - Test commit linking across multiple prompts in single session (acceptance: Each prompt displays only its associated commits, not all session commits)

---

PROMPTS 26/04/17-00:00 P100270 [ ] [discovery] [task] (auto) — Update memory system and define MCP integration for new sessions

  Requirements:
  - Run /memory command to update all summaries and db tagging
  - Generate CLAUDE.md with auto-load capability for new sessions
  - Document MCP integration path for new CLI/LLM sessions
  - Define how new sessions access shared memory without duplication
  - Ensure new sessions inherit same context understanding

  Completed:
  - Generated CLAUDE.md in project root for auto-loading by Claude Code on session start (docs)
  - Generated MEMORY.md with LLM-synthesized digest of recent changes (docs)
  - Updated .cursor/ rule files with latest session context (docs)
  - Commit 523f5fd0: docs: update AI context files after claude session 03f774e9 (code)

  Action items:
  - Document MCP protocol for memory access from new CLI/LLM sessions (acceptance: New sessions can invoke /memory to fetch full context without redundant re-analysis)
  - Test new session initialization using different LLM to verify context inheritance (acceptance: New session demonstrates same understanding of project state as current session)

