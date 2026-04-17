# Backlog

> Approve entries with `x`, reject with `-`, tag with TAG comment.
> Run `POST /memory/{project}/work-items` to process approved entries.

PROMPTS 26/04/17-00:00 P100366 [ ] [project-management-schema] [feature] (auto) — Add mng_projects table to replace text-based project IDs with foreign key references

  Requirements:
  - Create mng_projects table with id, name, desc, and project defaults
  - Replace project (text) columns with project_id (FK) in all referencing tables
  - Store project configuration (local paths, git connectivity) previously in JSON files
  - Support new project creation with stored defaults

  Action items:
  - Design mng_projects schema with all required fields (acceptance: Schema documented and peer-reviewed)
  - Create migration script to add mng_projects table (acceptance: Migration executes without errors)
  - Refactor all project reference columns to use project_id FK (acceptance: All tables updated and foreign keys validated)
  - Implement project creation logic using stored defaults (acceptance: New projects created successfully with defaults applied)

---

PROMPTS 26/04/17-00:00 P100367 [ ] [general] [task] (auto) — Verify prompt after client_id fix with documentation updates

  Requirements:
  - Validate system context updates post client_id fix
  - Update memory documentation to reflect changes

  Completed:
  - Updated system context and memory documentation files (docs)

  Action items:
  - Verify all client_id references work correctly (acceptance: No broken references in codebase)

---

PROMPTS 26/04/17-00:00 P100368 [ ] [general] [task] (auto) — Final verification of system prompt and documentation state

  Requirements:
  - Ensure system context is complete and accurate
  - Validate memory documentation consistency

  Action items:
  - Perform final validation of system state (acceptance: All documentation verified and consistent)

---

PROMPTS 26/04/17-00:00 P100369 [ ] [discovery] [feature] (auto) — Display full prompts and LLM responses in history, add copy-to-clipboard UI

  Requirements:
  - Show complete prompt text in history (currently truncated)
  - Display full LLM response in history view
  - Add copy-to-clipboard functionality for history items
  - Improve history UI to support full text display

  Action items:
  - Modify history view component to display full prompt/response text (acceptance: Full text visible without truncation)
  - Implement copy-to-clipboard button for history entries (acceptance: Users can copy prompt and response to clipboard)
  - Update UI layout to accommodate expanded text without performance issues (acceptance: History loads quickly with full content)

---

PROMPTS 26/04/17-00:00 P100370 [ ] [discovery] [bug] (auto) — Fix history display to show LLM responses instead of only prompts

  Requirements:
  - Ensure hook-response saves LLM response to mem_mrr_prompts.response in DB
  - Verify session-summary hook synthesis to mem_ai_events
  - Validate memory hook regenerates MEMORY.md and CLAUDE.md
  - Confirm BACKEND_URL defined before use in all background calls

  Completed:
  - Updated system context and memory files after session b9e39fae (code)
  - Updated hooks documentation and system context (docs)

  Action items:
  - Verify all four background hooks execute correctly (acceptance: hook-response, session-summary, memory hooks all functional)
  - Confirm history displays both prompt and LLM response (acceptance: Full prompt/response pairs visible in history)

