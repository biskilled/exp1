Given a work item's name, current status, acceptance criteria, action items,
and all linked events/commits as context, produce a structured PM update.

Return JSON only:
{
  "summary_ai": "2-4 sentences covering: what this item is and why it matters, what was done recently, what remains open",
  "acceptance_criteria_ai": "- [ ] Specific, testable outcome\n- [ ] ...",
  "action_items_ai": "- Concrete next step\n- ...",
  "score_ai": 0
}

Rules:
- summary_ai: combine definition + progress. Start with what the item is (1 sentence), then recent progress and open gaps.
- acceptance_criteria_ai: 1-3 bullet lines starting with "- [ ]". Testable and specific.
- action_items_ai: 1-4 bullet lines starting with "-". Concrete imperative phrases.
- score_ai: integer 0-5 reflecting completion based on evidence in linked events:
    0 = not started — no linked events or only setup activity
    1 = early stage — direction set but little concrete progress
    2 = in progress — meaningful work done but blockers or gaps remain
    3 = good progress — majority of work done, a few items left
    4 = nearly done — acceptance criteria mostly met, minor polish/testing remaining
    5 = complete — all acceptance criteria met, verified, nothing open
  Base the score ONLY on evidence in the linked events. Default to 1 if unclear.
- No preamble, no markdown fences, return ONLY valid JSON.
