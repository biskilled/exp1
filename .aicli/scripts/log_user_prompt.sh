#!/usr/bin/env bash
# UserPromptSubmit hook — logs every Claude Code prompt to the unified project history.
#
# Claude Code sends JSON on stdin:
#   { "hook_event_name": "UserPromptSubmit", "session_id": "abc123", "prompt": "user text" }
#
# Writes to: workspace/{active_project}/_system/history.jsonl
# Also keeps legacy: .aicli/prompt_log.jsonl (for backward compat)
#
# CLAUDE_PROJECT_DIR is set by Claude Code to the project root (aicli/).

INPUT=$(cat)

PROMPT_TEXT=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('prompt', ''))
" 2>/dev/null || echo "")

SESSION=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', ''))
" 2>/dev/null || echo "")

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Detect active project from aicli.yaml
ACTIVE_PROJECT=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config))
    print(d.get('active_project', 'aicli'))
except:
    print('aicli')
" "$WORK_DIR" 2>/dev/null || echo "aicli")

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Write to unified history.jsonl ────────────────────────────────────────────
HIST_DIR="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/_system"
HIST_FILE="${HIST_DIR}/history.jsonl"
mkdir -p "$HIST_DIR"

python3 -c "
import json, sys

entry = {
    'ts': '$TIMESTAMP',
    'source': 'claude_cli',
    'session_id': '$SESSION',
    'provider': 'claude',
    'user_input': sys.argv[1],
    'output': '',
    'user': None,
    'feature': None,
    'tags': [],
}
print(json.dumps(entry))
" "$PROMPT_TEXT" >> "$HIST_FILE" 2>/dev/null

# ── Also keep legacy prompt_log.jsonl for backward compat ────────────────────
LOG_DIR="${WORK_DIR}/.aicli"
LOG_FILE="${LOG_DIR}/prompt_log.jsonl"
mkdir -p "$LOG_DIR"

python3 -c "
import json, sys

entry = {
    'ts': '$TIMESTAMP',
    'source': 'claude_cli',
    'session': '$SESSION',
    'provider': 'claude',
    'role': '',
    'user_input': sys.argv[1],
    'output_preview': '',
}
print(json.dumps(entry))
" "$PROMPT_TEXT" >> "$LOG_FILE" 2>/dev/null

exit 0
