#!/usr/bin/env bash
# Stop hook — fires when Claude Code finishes responding to a session.
#
# Claude Code sends JSON on stdin:
#   { "hook_event_name": "Stop", "session_id": "abc123", "stop_reason": "end_turn" }
#
# This hook:
#   1. Reads the Claude Code session transcript to capture the assistant response
#   2. Updates the history.jsonl entry with the response (output field)
#   3. Updates dev_runtime_state.json with session metadata

INPUT=$(cat)

SESSION=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('session_id', ''))
" 2>/dev/null || echo "")

STOP_REASON=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('stop_reason', 'end_turn'))
" 2>/dev/null || echo "end_turn")

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Detect active project
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
HIST_DIR="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/_system"
HIST_FILE="${HIST_DIR}/history.jsonl"
RUNTIME_FILE="${HIST_DIR}/dev_runtime_state.json"

# ── Read assistant response from Claude Code session file ─────────────────────
# Claude Code stores sessions at: ~/.claude/projects/{project-hash}/{session_id}.jsonl
# Each line has: { "type": "assistant"|"user", "message": "<python-dict-string>", ... }
# The message field is a Python repr (single quotes) — use ast.literal_eval, not json.loads

RESPONSE_TEXT=$(python3 -c "
import ast, sys, json
from pathlib import Path

session_id = sys.argv[1]
work_dir   = sys.argv[2]

# Direct path: Claude Code names files by session_id
claude_dir = Path.home() / '.claude' / 'projects'
if not claude_dir.exists():
    sys.exit(0)

# Find the session file (search all project dirs)
session_file = None
for proj_dir in claude_dir.iterdir():
    if not proj_dir.is_dir():
        continue
    candidate = proj_dir / f'{session_id}.jsonl'
    if candidate.exists():
        session_file = candidate
        break

if not session_file:
    sys.exit(0)

# Read all lines, find the last assistant message
lines = session_file.read_text(encoding='utf-8').strip().split('\n')
for line in reversed(lines):
    try:
        entry = json.loads(line)
    except Exception:
        continue
    if entry.get('type') != 'assistant':
        continue
    # 'message' can be a dict (new Claude Code format) OR a Python repr string (old format)
    raw = entry.get('message', {})
    if not raw:
        continue
    # Normalise to dict
    if isinstance(raw, str):
        try:
            msg = json.loads(raw)
        except Exception:
            try:
                msg = ast.literal_eval(raw)
            except Exception:
                continue
    elif isinstance(raw, dict):
        msg = raw
    else:
        continue
    content = msg.get('content', '')
    if isinstance(content, list):
        # Extract text blocks only (skip tool_use, tool_result, etc.)
        texts = [b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text']
        result = '\n'.join(t for t in texts if t).strip()
        if result:
            # Truncate to 2000 chars for history storage
            print(result[:2000])
            sys.exit(0)
    elif isinstance(content, str) and content.strip():
        print(content[:2000])
        sys.exit(0)
" "$SESSION" "$WORK_DIR" 2>/dev/null || echo "")

# ── Update history.jsonl: fill in output for this session's entry ────────────
if [ -f "$HIST_FILE" ]; then
python3 -c "
import json, sys
from pathlib import Path

hist_file   = Path(sys.argv[1])
session_id  = sys.argv[2]
response    = sys.argv[3]
stop_reason = sys.argv[4]

lines = hist_file.read_text(encoding='utf-8').strip().split('\n')
updated = False
# Walk backwards to find the latest claude_cli entry for this session without output
for i in range(len(lines) - 1, -1, -1):
    try:
        e = json.loads(lines[i])
    except Exception:
        continue
    if (e.get('source') == 'claude_cli'
            and e.get('session_id') == session_id
            and not e.get('output')):
        e['output']      = response
        e['stop_reason'] = stop_reason
        lines[i] = json.dumps(e)
        updated = True
        break

if updated:
    hist_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
" "$HIST_FILE" "$SESSION" "$RESPONSE_TEXT" "$STOP_REASON" 2>/dev/null
fi

# ── Update dev_runtime_state.json ────────────────────────────────────────────
python3 -c "
import json, sys
from pathlib import Path
from datetime import datetime, timezone

runtime_file = Path(sys.argv[1])
session_id   = sys.argv[2]

try:
    state = json.loads(runtime_file.read_text()) if runtime_file.exists() else {}
except Exception:
    state = {}

state['last_updated']     = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
state['last_session_id']  = session_id
state['last_session_ts']  = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
state['session_count']    = state.get('session_count', 0) + 1
state['last_provider']    = 'claude'
state['source']           = 'claude_cli'

runtime_file.write_text(json.dumps(state, indent=2))
" "$RUNTIME_FILE" "$SESSION" 2>/dev/null

# ── Auto-regenerate MEMORY.md so next session starts with fresh context ───────
# Call the backend /memory endpoint if it's running.
# This means Claude (and any LLM) always reads up-to-date history at next startup.
BACKEND_URL=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('backend_url', 'http://localhost:8000').rstrip('/'))
except:
    print('http://localhost:8000')
" "$WORK_DIR" 2>/dev/null || echo "http://localhost:8000")

curl -sf --connect-timeout 2 --max-time 15 \
    -X POST "${BACKEND_URL}/projects/${ACTIVE_PROJECT}/memory" \
    -H "Content-Type: application/json" \
    -o /dev/null 2>/dev/null &   # run in background, don't block

# Auto-detect bugs mentioned in this session → create work items
curl -sf --connect-timeout 2 --max-time 30 \
    -X POST "${BACKEND_URL}/projects/${ACTIVE_PROJECT}/auto-detect-bugs" \
    -H "Content-Type: application/json" \
    -o /dev/null 2>/dev/null &   # fire-and-forget

exit 0
