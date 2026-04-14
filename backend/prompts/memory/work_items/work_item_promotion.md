Given a work item's name, current status, acceptance criteria, action items,
and all linked events/commits as context, produce a structured PM update.

Return JSON only:
{
  "summary_ai": "2-4 sentences covering: what this item is and why it matters, what was done recently, what remains open",
  "acceptance_criteria_ai": "- [ ] Specific, testable outcome\n- [ ] ...",
  "action_items_ai": "- Concrete next step\n- ..."
}

Rules:
- summary_ai: combine definition + progress. Start with what the item is (1 sentence), then recent progress and open gaps.
- acceptance_criteria_ai: 1-3 bullet lines starting with "- [ ]". Testable and specific.
- action_items_ai: 1-4 bullet lines starting with "-". Concrete imperative phrases.
- No preamble, no markdown fences, return ONLY valid JSON.
