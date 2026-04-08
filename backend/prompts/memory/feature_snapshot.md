Given memory events for a feature (from prompt batches, commits, requirements/decisions/meetings,
messages, sessions, and agent actions), plus current project facts and work item status,
produce a comprehensive 4-layer snapshot.

Input sections you may receive:
  ## Prompt Batches — summaries of developer prompts
  ## Commits — git commit digests
  ## Requirements / Decisions / Meetings — items and meeting notes
  ## Messages — Slack/Teams thread summaries
  ## Sessions — session-level summaries
  ## Agent Actions — workflow agent outputs
  ## Current Project Facts — durable facts (stack, conventions, constraints)
  Work Item Status: lifecycle_status of associated work item

Return valid JSON with these keys:
  requirements (str): what the feature must do — synthesised from all evidence
  action_items (str): remaining work items and next steps
  work_item_status (str): current lifecycle status (pass through from input)
  design (object): {
    high_level: "architectural overview",
    low_level: "implementation details",
    patterns_used: ["pattern1", "pattern2"]
  }
  code_summary (object): {
    files: ["path/to/file.py"],
    key_classes: ["ClassName"],
    key_methods: ["method_name"],
    dependencies_added: ["package"],
    dependencies_removed: ["package"]
  }
  project_facts (object): key facts from context relevant to this feature {key: value}
  relations (array): relationships detected between this and other features/modules.
    Each item: {"from": "tag-slug", "relation": "part_of|depends_on|blocks|relates_to|replaces|extracted_from", "to": "tag-slug", "note": "brief reason"}
    Use empty array if no clear relationships detected.

Base your answer only on the provided evidence. Return ONLY valid JSON, no preamble.
