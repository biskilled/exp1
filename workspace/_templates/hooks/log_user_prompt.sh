#!/usr/bin/env bash
# UserPromptSubmit hook — logs every Claude Code prompt to the unified project history.
#
# Claude Code sends JSON on stdin:
#   { "hook_event_name": "UserPromptSubmit", "session_id": "abc123", "prompt": "user text" }
#
# Writes to: workspace/{active_project}/_system/history.jsonl
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

# ── Skip internal Claude Code tool noise ──────────────────────────────────────
PROMPT_START=$(echo "$PROMPT_TEXT" | head -c 30)
case "$PROMPT_START" in
    "<task-notification>"*|"<tool-use-id>"*|"<task-id>"*|"<parameter>"*)
        exit 0
        ;;
esac

# Skip empty prompts
if [ -z "$PROMPT_TEXT" ]; then
    exit 0
fi

BACKEND_URL=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('backend_url', 'http://localhost:8000').rstrip('/'))
except:
    print('http://localhost:8000')
" "$WORK_DIR" 2>/dev/null || echo "http://localhost:8000")

WORKSPACE_DIR=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('workspace_dir', ''))
except:
    print('')
" "$WORK_DIR" 2>/dev/null || echo "")

if [ -z "$WORKSPACE_DIR" ]; then
    WORKSPACE_DIR="$WORK_DIR/workspace"
fi

# ── Read session context tags from .agent-context ─────────────────────────────
CONTEXT_TAGS=$(python3 -c "
import json, sys, os
ctx_file = os.path.join(sys.argv[1], sys.argv[2], '_system', '.agent-context')
try:
    d = json.loads(open(ctx_file).read())
    print(json.dumps(d.get('tags', {})))
except:
    print('{}')
" "$WORKSPACE_DIR" "$ACTIVE_PROJECT" 2>/dev/null || echo "{}")

# ── Write prompt to DB via backend (primary) ──────────────────────────────────
python3 -c "
import json, sys, urllib.request, urllib.error

context_tags = json.loads(sys.argv[6])

payload = json.dumps({
    'ts':           sys.argv[1],
    'session_id':   sys.argv[2],
    'session_src_id': sys.argv[2],
    'prompt':       sys.argv[3],
    'source':       'claude_cli',
    'provider':     'claude',
    'context_tags': context_tags,
}).encode()

req = urllib.request.Request(
    sys.argv[4] + '/chat/' + sys.argv[5] + '/hook-log',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
try:
    urllib.request.urlopen(req, timeout=3)
except Exception:
    pass  # backend unavailable — no JSONL fallback needed; /memory will still run
" "$TIMESTAMP" "$SESSION" "$PROMPT_TEXT" "$BACKEND_URL" "$ACTIVE_PROJECT" "$CONTEXT_TAGS" 2>/dev/null

exit 0
