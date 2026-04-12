Given a work item's name, description, current status, acceptance criteria, action items,
and all linked events/commits as context, produce a structured PM update.

Return JSON only:
{
  "desc_ai": "1-2 sentence explanation of what this item is and why it matters",
  "acceptance_criteria_ai": "- [ ] Specific, testable outcome\n- [ ] ...",
  "action_items_ai": "- Concrete next step\n- ...",
  "summary_ai": "2-4 sentence PM digest: what was done, what remains, and test coverage status",
  "status_ai": "active|in_progress|done"
}

Rules:
- desc_ai: short, factual. What it is.
- acceptance_criteria_ai: 1-3 bullet lines starting with "- [ ]". Testable.
- action_items_ai: 1-4 bullet lines starting with "-". Concrete imperative phrases.
- summary_ai: PM-facing. Mention recent progress, open gaps, and whether tested.
- status_ai: reflect actual progress from linked events.
- No preamble, no markdown fences, return ONLY valid JSON.
