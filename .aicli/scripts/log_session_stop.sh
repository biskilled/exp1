#!/usr/bin/env bash
# Stop hook — fires when Claude Code finishes responding to a session.
#
# Claude Code sends JSON on stdin:
#   { "hook_event_name": "Stop", "session_id": "abc123", "stop_reason": "end_turn" }
#
# This hook reads the session transcript from Claude Code's local storage
# to capture the assistant response and complete the history entry.
#
# If the transcript is unavailable, it marks the session as completed.

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

# Try to read the latest response from Claude Code's conversation transcript.
# Claude Code stores conversations in ~/.claude/projects/ keyed by project path hash.
# We look for the most recent session file matching our session_id.
RESPONSE_TEXT=$(python3 -c "
import json, os, sys, hashlib, glob
from pathlib import Path

session_id = sys.argv[1]
work_dir = sys.argv[2]

# Claude Code stores projects under ~/.claude/projects/{hash}/
claude_dir = Path.home() / '.claude' / 'projects'
if not claude_dir.exists():
    sys.exit(0)

# Hash the project path (Claude Code uses MD5 or SHA of the path)
# Try both common hash formats
for proj_dir in sorted(claude_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
    # Look for conversation files containing our session_id
    for ext in ['*.jsonl', '*.json']:
        for f in glob.glob(str(proj_dir / '**' / ext), recursive=True):
            try:
                content = Path(f).read_text()
                if session_id in content:
                    # Found a file with our session. Extract last assistant message.
                    lines = content.strip().split('\n')
                    for line in reversed(lines):
                        try:
                            msg = json.loads(line)
                            role = msg.get('role') or msg.get('type', '')
                            if role == 'assistant':
                                content_val = msg.get('content', '')
                                if isinstance(content_val, list):
                                    # Extract text blocks
                                    texts = [b.get('text','') for b in content_val if isinstance(b,dict) and b.get('type')=='text']
                                    print('\n'.join(texts)[:500])
                                elif isinstance(content_val, str):
                                    print(content_val[:500])
                                sys.exit(0)
                        except:
                            pass
            except:
                pass
" "$SESSION" "$WORK_DIR" 2>/dev/null || echo "")

# Update the last claude_cli entry for this session with the response (if found)
# This is best-effort — if we can't find it, no harm done
if [ -n "$RESPONSE_TEXT" ] && [ -f "$HIST_FILE" ]; then
python3 -c "
import json, sys
from pathlib import Path

hist_file = Path(sys.argv[1])
session_id = sys.argv[2]
response = sys.argv[3]

lines = hist_file.read_text().strip().split('\n')
updated = False
new_lines = []
# Walk backwards to find the latest claude_cli entry for this session
for i, line in enumerate(reversed(lines)):
    idx = len(lines) - 1 - i
    try:
        e = json.loads(line)
        if not updated and e.get('source') == 'claude_cli' and e.get('session_id') == session_id and not e.get('output'):
            e['output'] = response
            lines[idx] = json.dumps(e)
            updated = True
            break
    except:
        pass

if updated:
    hist_file.write_text('\n'.join(lines) + '\n')
" "$HIST_FILE" "$SESSION" "$RESPONSE_TEXT" 2>/dev/null
fi

exit 0
