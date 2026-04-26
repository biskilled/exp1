#!/usr/bin/env bash
# UserPromptSubmit hook — logs every Claude Code prompt to the unified project history.
#
# Claude Code sends JSON on stdin:
#   { "hook_event_name": "UserPromptSubmit", "session_id": "abc123", "prompt": "user text" }
#
# Writes to: workspace/{active_project}/state/history.jsonl (via backend hook-log)
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
# Task notifications and tool IDs are system messages, not real user prompts.
# Check only the START of the prompt to avoid filtering user messages that
# happen to MENTION these tag names in their text.
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

# ── Load config from aicli.yaml (single parse for all values) ─────────────────
AICLI_CONFIG=$(python3 -c "
import yaml, sys, os, json
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    sess = d.get('session', {}) or {}
    print(json.dumps({
        'backend_url':   d.get('backend_url', 'http://localhost:8000').rstrip('/'),
        'workspace_dir': d.get('workspace_dir', ''),
        'interval':      int(sess.get('tag_reminder_interval', 8)),
        'valid_keys':    sess.get('valid_tag_keys',
                             ['phase','feature','bug','task','component',
                              'doc_type','design','decision','meeting','customer']),
    }))
except Exception as e:
    print(json.dumps({'backend_url':'http://localhost:8000','workspace_dir':'',
                      'interval':8,'valid_keys':['phase','feature','bug','task']}))
" "$WORK_DIR" 2>/dev/null || echo '{"backend_url":"http://localhost:8000","workspace_dir":"","interval":8,"valid_keys":["phase","feature","bug","task"]}')

BACKEND_URL=$(echo "$AICLI_CONFIG" | python3 -c "import json,sys; print(json.load(sys.stdin)['backend_url'])" 2>/dev/null || echo "http://localhost:8000")
WORKSPACE_DIR=$(echo "$AICLI_CONFIG" | python3 -c "import json,sys; print(json.load(sys.stdin)['workspace_dir'])" 2>/dev/null || echo "")
TAG_INTERVAL=$(echo "$AICLI_CONFIG" | python3 -c "import json,sys; print(json.load(sys.stdin)['interval'])" 2>/dev/null || echo "8")
VALID_KEYS=$(echo "$AICLI_CONFIG" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin)['valid_keys']))" 2>/dev/null || echo '["phase","feature","bug","task"]')

if [ -z "$WORKSPACE_DIR" ]; then
    WORKSPACE_DIR="$WORK_DIR/workspace"
fi

CONTEXT_FILE="$WORKSPACE_DIR/$ACTIVE_PROJECT/state/.agent-context"

# ── /tag command interception ──────────────────────────────────────────────────
# Handles: /tag phase:development feature:work-items-ui bug:login-500
if echo "$PROMPT_TEXT" | grep -qE '^\s*/tag\b'; then
    TAG_RESULT=$(python3 -c "
import json, sys, re

prompt     = sys.argv[1]
valid_keys = json.loads(sys.argv[2])

pairs = re.findall(r'(\w+):(\S+)', prompt)
valid, invalid = [], []
for k, v in pairs:
    if k in valid_keys:
        valid.append((k, v))
    else:
        invalid.append(k)

if invalid:
    print('INVALID:' + ','.join(invalid))
elif not valid:
    print('EMPTY')
else:
    tags = {k: v for k, v in valid}
    print('OK:' + json.dumps(tags))
" "$PROMPT_TEXT" "$VALID_KEYS" 2>/dev/null || echo "EMPTY")

    if [[ "$TAG_RESULT" == INVALID:* ]]; then
        BAD=$(echo "$TAG_RESULT" | cut -d: -f2)
        echo ""
        echo "⚠ Unknown tag key(s): $BAD"
        echo "  Valid keys: $(echo "$VALID_KEYS" | python3 -c "import json,sys; print('  '.join(json.load(sys.stdin)))" 2>/dev/null)"
        echo "  Example: /tag phase:development feature:work-items-ui"
        echo ""
        exit 2
    elif [ "$TAG_RESULT" = "EMPTY" ]; then
        echo ""
        echo "⚠ No valid tags found. Usage:"
        echo "  /tag phase:development"
        echo "  /tag phase:development feature:auth bug:login-500"
        echo ""
        echo "  Valid keys: $(echo "$VALID_KEYS" | python3 -c "import json,sys; print('  '.join(json.load(sys.stdin)))" 2>/dev/null)"
        echo ""
        exit 2
    else
        TAGS_JSON=$(echo "$TAG_RESULT" | sed 's/^OK://')
        TAGS_DISPLAY=$(echo "$TAGS_JSON" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('  '.join(f'{k}:{v}' for k,v in d.items()))
" 2>/dev/null)

        # Save to .agent-context
        python3 -c "
import json, sys, os
ctx_file = sys.argv[1]
tags     = json.loads(sys.argv[2])
session  = sys.argv[3]
ts       = sys.argv[4]

# Preserve existing prompt_count if file already exists
existing_count = 0
try:
    existing = json.loads(open(ctx_file).read())
    existing_count = existing.get('prompt_count', 0)
except Exception:
    pass

ctx = {
    'session_id':   session,
    'session_src':  'claude_cli',
    'tags':         tags,
    'set_at':       ts,
    'prompt_count': existing_count,
}
os.makedirs(os.path.dirname(ctx_file), exist_ok=True)
open(ctx_file, 'w').write(json.dumps(ctx, indent=2))
" "$CONTEXT_FILE" "$TAGS_JSON" "$SESSION" "$TIMESTAMP" 2>/dev/null

        # POST to backend session-context
        python3 -c "
import json, sys, urllib.request
url     = sys.argv[1] + '/tags/session-context?project=' + sys.argv[2]
payload = json.dumps({'tags': json.loads(sys.argv[3])}).encode()
req     = urllib.request.Request(url, data=payload,
              headers={'Content-Type': 'application/json'}, method='POST')
try:
    urllib.request.urlopen(req, timeout=3)
except Exception:
    pass
" "$BACKEND_URL" "$ACTIVE_PROJECT" "$TAGS_JSON" 2>/dev/null

        echo ""
        echo "✓ Tags set: $TAGS_DISPLAY"
        echo "  Resubmit your message."
        echo ""
        exit 2
    fi
fi

# ── Read current session tags for logging ─────────────────────────────────────
CONTEXT_TAGS=$(python3 -c "
import json, sys, os
try:
    d = json.loads(open(sys.argv[1]).read())
    print(json.dumps(d.get('tags', {})))
except:
    print('{}')
" "$CONTEXT_FILE" 2>/dev/null || echo "{}")

# ── Increment prompt counter + periodic tag reminder ──────────────────────────
if [ "$TAG_INTERVAL" -gt 0 ] 2>/dev/null; then
    python3 -c "
import json, sys, os

ctx_file = sys.argv[1]
interval = int(sys.argv[2])

try:
    d = json.loads(open(ctx_file).read())
except Exception:
    sys.exit(0)

count = d.get('prompt_count', 0) + 1
d['prompt_count'] = count
try:
    open(ctx_file, 'w').write(json.dumps(d))
except Exception:
    pass

tags = d.get('tags', {})
if not tags or interval <= 0:
    sys.exit(0)

tags_str = '  '.join(f'{k}:{v}' for k, v in tags.items() if v)

if count % interval == 0:
    print(f'┄ Prompt #{count} ╌ still on: {tags_str}')
    print( '  (type /tag to update)')
" "$CONTEXT_FILE" "$TAG_INTERVAL" 2>/dev/null
fi

# ── Write prompt to DB via backend (primary) ──────────────────────────────────
python3 -c "
import json, sys, urllib.request, urllib.error

context_tags = json.loads(sys.argv[6])

payload = json.dumps({
    'ts':             sys.argv[1],
    'session_id':     sys.argv[2],
    'session_src_id': sys.argv[2],
    'prompt':         sys.argv[3],
    'source':         'claude_cli',
    'provider':       'claude',
    'context_tags':   context_tags,
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
