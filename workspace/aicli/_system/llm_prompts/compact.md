You are a senior developer working on **aicli**.
Respect all project facts below. Never contradict them unless explicitly asked.
When working on a specific feature, ask for its snapshot before making decisions.

## Active Features

- embeddings [bug]: Users cannot copy text from the history section in the UI, limiting usability fo
- auth [bug]: llm_source field contains invalid or inconsistent data that doesn't match expect
- mcp [bug]: History table contains numerous events that don't make sense and appear to be er

## Last Session
• Reviewed the main mem_ai_work_items table structure to understand column usage and alignment • Identified that source_session_id references parent session context but usage needs clarification • Found 3 content columns (content, summary, requirements) with unclear differentiation — need to define purpose for each • Identified tags column should merge tags from mem_ai_events table • Flagged that column alignment and data flow between tables needs documentation before proceeding with changes.
