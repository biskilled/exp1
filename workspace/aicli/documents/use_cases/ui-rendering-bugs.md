# ui-rendering-bugs

<!-- STATUS: 1 -->
<!-- STATUS_VALUES: 1=not started | 2=in progress | 3=done -->
<!-- CREATED: 2026-04-18 -->
<!-- UPDATED: 2026-04-18 -->
<!-- EVENTS: 29 -->
<!-- PROMPTS: 29 -->
<!-- COMMITS: 0 -->
<!-- MESSAGES: 0 -->
<!-- ITEMS: 0 -->
<!-- NOTE: counters updated automatically on each work-items/sync run -->

## Summary

User reports history shows only small text instead of full prompt/LLM response and requests copy fun

## Requirements

- User reports history shows only small text instead of full prompt/LLM response and requests copy fun


## Delivery

### Code

| Stack      | Location                  | Commits |
|------------|---------------------------|---------|
| {language} | {backend/frontend/path/}  | 0       |

### Documents

| Name | Type | Path | Summary |
|------|------|------|---------|
| —    | —    | —    | —       |

---

## Completed

### Action Items

<!-- Each item: YY/MM/DD HH:MM | events: N | summary -->

| Done        | Events | Summary |
|-------------|--------|---------|
| —           | —      | —       |

### Bugs Fixed

<!-- Each item: YY/MM/DD HH:MM | events: N | summary -->

| Fixed       | Events | Summary |
|-------------|--------|---------|
| —           | —      | —       |

---

## Open Items
<!-- AI-appended from approved backlog entries -->
- [ ] AI:4  Instructed user to perform hard refresh to see UI changes (Cmd+Shift+R or Ctrl+Shift+R).
  Linked: P102298

- [ ] AI:1  Investigated project loading performance issues and requested details on slow Summary and History lo
  Linked: P102195

- [ ] AI:4  Explained tag bar location and accept workflow; fixed overflow clipping issue.
  Linked: P102151

- [ ] AI:4  Provided clean restart procedure using dev script with NODE_ENV=development after killing stale back
  Linked: P102143

- [ ] AI:3  Update session header display, add session ID banner, and implement per-prompt tags in chat tab.
  Linked: P102351

- [ ] AI:3  Add timestamp next to YOU, display session ID in left/top panels, and add per-prompt tag functionali
  Linked: P102350

- [ ] AI:3  Fix UI not updating, restore latest prompts display, add tag option to user prompts, and investigate
  Linked: P102349

- [ ] AI:3  Add table padding, fix date display, implement tag color coding (green/red/blue), and debug missing
  Linked: P102309

- [ ] AI:4  Implemented sticky headers, AI tag suggestions per row with approve/reject actions, and improved tag
  Linked: P102304

- [ ] AI:4  Added work items UI panel with date formatting and visual improvements after backend SQL restart.
  Linked: P102299

- [ ] AI:1  User reports history shows only small text instead of full prompt/LLM response and requests copy fun
  Linked: P102267


<!-- Format:  [ ] AI:N  summary -->
<!-- AI score: 0=not started  1=discussed  2=design ready  3=partial  4=implemented  5=needs test -->

- [ ] AI:0  {action item description}
  Acceptance: {what "done" looks like}
  Linked: {REF_ID}

## Open Bugs
<!-- AI-appended from approved backlog entries -->
- [ ] AI:5  Load current session on startup by synchronously reading last_session_id from runtime state.
  Linked: P102357

- [ ] AI:3  Fix stale session ID loading by resetting module variables and implementing auto-select for current
  Linked: P102356

- [ ] AI:4  Fix incomplete prompt loading by merging DB entries with JSONL file data and correct sorting.
  Linked: P102355

- [ ] AI:4  Fix duplicate const declaration causing Electron empty load.
  Linked: P102342

- [ ] AI:2  Fix UI category/bug display issue and work_item disappearance after tag acceptance.
  Linked: P102341

- [ ] AI:4  Restore table layout and add labeled tag rows (AI/User) with descriptions.
  Linked: P102308

- [ ] AI:3  Fixed work items panel layout to display tags properly and expand description to full row width.
  Linked: P102307

- [ ] AI:3  Fixed date formatting to yy/mm/dd-hh:mm and removed non-work-item tags (Shared-memory, billing) from
  Linked: P102301

- [ ] AI:4  Improved work items panel header clarity with wider columns, better padding, and visual separation.
  Linked: P102300

- [ ] AI:4  Fixed history display to show both prompt and LLM response using consistent hooks and backend calls.
  Linked: P102268

- [ ] AI:4  Fixed project loading retry logic to handle empty results and backend startup delays.
  Linked: P102212

- [ ] AI:1  User reports missing aiCli project and slow PROJECT.md loading (>1min), suspects DB query issue.
  Linked: P102196

- [ ] AI:4  Fixed red warning badge display for all sessions without phase and phase persistence for CLI/WF sess
  Linked: P102176

- [ ] AI:4  Verified phase change persistence and session metadata updates for both new and existing sessions.
  Linked: P102175

- [ ] AI:4  Restored session-specific phase handling and fixed phase visibility across Chat, History, and Commit
  Linked: P102174

- [ ] AI:4  Implemented phase persistence across sessions and added phase filtering to Commit history view.
  Linked: P102173

- [ ] AI:4  Fixed phase persistence issue where app load showed 'required' and phase didn't update on session sw
  Linked: P102172

- [ ] AI:4  Diagnosed bind error on port 8000 caused by stale uvicorn instance; verified backend is healthy.
  Linked: P102142


<!-- Format:  [ ] AI:N  summary -->

- [ ] AI:0  {bug description}
  Acceptance: {what "fixed" looks like}
  Linked: {REF_ID}

---

## Events

<!-- ═══════════════════════════════════════════════════════════════════════ -->
<!-- SYSTEM-MANAGED — items appended here on each work-items/sync run.     -->
<!-- Rebuild from DB: POST /memory/{p}/regenerate-use-case?slug={slug}     -->
<!-- ═══════════════════════════════════════════════════════════════════════ -->

<!-- EVENTS_START -->

### P102267 · 26/04/18-00:00 · PROMPTS · feature · in-progress · AI:1

User reports history shows only small text instead of full prompt/LLM response and requests copy fun

---

### P102299 · 26/04/18-00:00 · PROMPTS · feature · completed · AI:4

Added work items UI panel with date formatting and visual improvements after backend SQL restart.

---

### P102304 · 26/04/18-00:00 · PROMPTS · feature · completed · AI:4

Implemented sticky headers, AI tag suggestions per row with approve/reject actions, and improved tag

---

### P102309 · 26/04/18-00:00 · PROMPTS · feature · in-progress · AI:3

Add table padding, fix date display, implement tag color coding (green/red/blue), and debug missing

---

### P102349 · 26/04/18-00:00 · PROMPTS · feature · in-progress · AI:3

Fix UI not updating, restore latest prompts display, add tag option to user prompts, and investigate

---

### P102350 · 26/04/18-00:00 · PROMPTS · feature · in-progress · AI:3

Add timestamp next to YOU, display session ID in left/top panels, and add per-prompt tag functionali

---

### P102351 · 26/04/18-00:00 · PROMPTS · feature · in-progress · AI:3

Update session header display, add session ID banner, and implement per-prompt tags in chat tab.

---

### P102142 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Diagnosed bind error on port 8000 caused by stale uvicorn instance; verified backend is healthy.

---

### P102172 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fixed phase persistence issue where app load showed 'required' and phase didn't update on session sw

---

### P102173 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Implemented phase persistence across sessions and added phase filtering to Commit history view.

---

### P102174 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Restored session-specific phase handling and fixed phase visibility across Chat, History, and Commit

---

### P102175 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Verified phase change persistence and session metadata updates for both new and existing sessions.

---

### P102176 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fixed red warning badge display for all sessions without phase and phase persistence for CLI/WF sess

---

### P102196 · 26/04/18-00:00 · PROMPTS · bug · in-progress · AI:1

User reports missing aiCli project and slow PROJECT.md loading (>1min), suspects DB query issue.

---

### P102212 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fixed project loading retry logic to handle empty results and backend startup delays.

---

### P102268 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fixed history display to show both prompt and LLM response using consistent hooks and backend calls.

---

### P102300 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Improved work items panel header clarity with wider columns, better padding, and visual separation.

---

### P102301 · 26/04/18-00:00 · PROMPTS · bug · in-progress · AI:3

Fixed date formatting to yy/mm/dd-hh:mm and removed non-work-item tags (Shared-memory, billing) from

---

### P102307 · 26/04/18-00:00 · PROMPTS · bug · in-progress · AI:3

Fixed work items panel layout to display tags properly and expand description to full row width.

---

### P102308 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Restore table layout and add labeled tag rows (AI/User) with descriptions.

---

### P102341 · 26/04/18-00:00 · PROMPTS · bug · in-progress · AI:2

Fix UI category/bug display issue and work_item disappearance after tag acceptance.

---

### P102342 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fix duplicate const declaration causing Electron empty load.

---

### P102355 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:4

Fix incomplete prompt loading by merging DB entries with JSONL file data and correct sorting.

---

### P102356 · 26/04/18-00:00 · PROMPTS · bug · in-progress · AI:3

Fix stale session ID loading by resetting module variables and implementing auto-select for current

---

### P102357 · 26/04/18-00:00 · PROMPTS · bug · completed · AI:5

Load current session on startup by synchronously reading last_session_id from runtime state.

---

### P102143 · 26/04/18-00:00 · PROMPTS · task · completed · AI:4

Provided clean restart procedure using dev script with NODE_ENV=development after killing stale back

---

### P102151 · 26/04/18-00:00 · PROMPTS · task · completed · AI:4

Explained tag bar location and accept workflow; fixed overflow clipping issue.

---

### P102195 · 26/04/18-00:00 · PROMPTS · task · in-progress · AI:1

Investigated project loading performance issues and requested details on slow Summary and History lo

---

### P102298 · 26/04/18-00:00 · PROMPTS · task · completed · AI:4

Instructed user to perform hard refresh to see UI changes (Cmd+Shift+R or Ctrl+Shift+R).

---

<!-- EVENTS_END -->
