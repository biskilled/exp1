#!/usr/bin/env bash
# UserPromptSubmit hook — enforces session context before allowing prompts.
#
# Fires FIRST in UserPromptSubmit (before log_user_prompt.sh).
#
# Flow:
#   1. If prompt starts with "/tag phase:xxx [feature:yyy] [bug:zzz]":
#      → parse tags, POST to /tags/session-context, write .agent-context, exit 2
#   2. If .agent-context exists with matching session_id AND has phase tag → exit 0
#   3. Else: GET /tags/session-context from backend
#      → If phase present: write .agent-context, show tags, exit 0
#      → If no phase: exit 2 with instructions
#
# .agent-context format:
#   {"session_id":"abc","session_src":"claude_cli","tags":{"phase":"discovery","feature":"auth"},
#    "tags_list":["phase:discovery","feature:auth"],"set_at":"..."}

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

# ── Skip tool noise ────────────────────────────────────────────────────────────
PROMPT_START=$(echo "$PROMPT_TEXT" | head -c 30)
case "$PROMPT_START" in
    "<task-notification>"*|"<tool-use-id>"*|"<task-id>"*|"<parameter>"*)
        exit 0
        ;;
esac

if [ -z "$PROMPT_TEXT" ]; then
    exit 0
fi

# ── Detect active project ──────────────────────────────────────────────────────
ACTIVE_PROJECT=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config))
    print(d.get('active_project', 'aicli'))
except:
    print('aicli')
" "$WORK_DIR" 2>/dev/null || echo "aicli")

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

CONTEXT_FILE="$WORKSPACE_DIR/$ACTIVE_PROJECT/_system/.agent-context"
BACKEND_URL=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('backend_url', 'http://localhost:8000').rstrip('/'))
except:
    print('http://localhost:8000')
" "$WORK_DIR" 2>/dev/null || echo "http://localhost:8000")

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$(dirname "$CONTEXT_FILE")"

# ── Check if this is a /tag command ──────────────────────────────────────────
TAG_RESULT=$(python3 -c "
import sys, re, json

prompt = sys.argv[1]

# Detect /tag command
if not prompt.strip().startswith('/tag'):
    print('NOT_TAG_CMD')
    sys.exit(0)

# Parse: /tag phase:xxx [feature:yyy] [bug:zzz]
tags = {}
tags_list = []
for m in re.finditer(r'(phase|feature|bug):(\S+)', prompt):
    k, v = m.group(1), m.group(2)
    tags[k] = v
    tags_list.append(f'{k}:{v}')

if 'phase' not in tags:
    print('MISSING_PHASE')
    sys.exit(0)

# Output parsed tags as JSON
print(json.dumps({'tags': tags, 'tags_list': tags_list}))
" "$PROMPT_TEXT" 2>/dev/null || echo "NOT_TAG_CMD")

if [ "$TAG_RESULT" = "MISSING_PHASE" ]; then
    echo ""
    echo "⚠ /tag requires a phase. Example:"
    echo "  /tag phase:discovery"
    echo "  /tag phase:development feature:auth"
    echo "  /tag phase:bugfix bug:login-500"
    echo ""
    echo "Valid phases: discovery | development | testing | review | production | maintenance | bugfix"
    echo ""
    exit 2
fi

if [ "$TAG_RESULT" != "NOT_TAG_CMD" ] && [ -n "$TAG_RESULT" ]; then
    # Parse the JSON result
    TAGS_JSON=$(echo "$TAG_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('tags', {})))")
    TAGS_LIST=$(echo "$TAG_RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('tags_list', [])))")
    TAGS_DISPLAY=$(echo "$TAGS_LIST" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin)))")

    # POST to backend to save session tags
    python3 -c "
import json, sys, urllib.request
url = sys.argv[1] + '/tags/session-context?project=' + sys.argv[2]
payload = json.dumps({'tags': json.loads(sys.argv[3])}).encode()
req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
try:
    urllib.request.urlopen(req, timeout=3)
except Exception:
    pass
" "$BACKEND_URL" "$ACTIVE_PROJECT" "$TAGS_JSON" 2>/dev/null

    # Write .agent-context
    python3 -c "
import json, sys
tags = json.loads(sys.argv[1])
tags_list = json.loads(sys.argv[2])
ctx = {
    'session_id': sys.argv[3],
    'session_src': 'claude_cli',
    'tags': tags,
    'tags_list': tags_list,
    'set_at': sys.argv[4],
    'prompt_count': 0,
}
open(sys.argv[5], 'w').write(json.dumps(ctx, indent=2))
" "$TAGS_JSON" "$TAGS_LIST" "$SESSION" "$TIMESTAMP" "$CONTEXT_FILE" 2>/dev/null

    echo ""
    echo "✓ Tags set: $TAGS_DISPLAY"
    echo "  Resubmit your message."
    echo ""
    exit 2
fi

# ── Context file check: matching session_id with phase tag ──────────────────
if [ -f "$CONTEXT_FILE" ]; then
    CTX_CHECK=$(python3 -c "
import json, sys
try:
    d = json.loads(open(sys.argv[1]).read())
    sid = d.get('session_id', '')
    tags = d.get('tags', {})
    tags_list = d.get('tags_list', [])
    has_phase = bool(tags.get('phase')) or any(t.startswith('phase:') for t in tags_list)
    match = (not sid or sid == sys.argv[2]) and has_phase
    print('PASS' if match else 'FAIL')
except:
    print('FAIL')
" "$CONTEXT_FILE" "$SESSION" 2>/dev/null || echo "FAIL")

    if [ "$CTX_CHECK" = "PASS" ]; then
        # ── Increment prompt counter + periodic tag reminder ──────────────────
        REMINDER=$(python3 -c "
import json, sys, os

ctx_file = sys.argv[1]
interval  = int(sys.argv[2])   # reminder every N prompts

try:
    d = json.loads(open(ctx_file).read())
except:
    sys.exit(0)

count = d.get('prompt_count', 0) + 1
d['prompt_count'] = count
open(ctx_file, 'w').write(json.dumps(d))

tags_list = d.get('tags_list', [])
tags_str  = '  '.join(tags_list) if tags_list else '(no tags)'

# Soft reminder at every interval; hard check at 3× interval
if count % interval == 0:
    print(f'SOFT|#{count}|{tags_str}')
elif count % (interval * 3) == 0:
    print(f'HARD|#{count}|{tags_str}')
" "$CONTEXT_FILE" "${TAG_REMINDER_INTERVAL:-8}" 2>/dev/null || echo "")

        if [[ "$REMINDER" == SOFT* ]]; then
            NUM=$(echo "$REMINDER" | cut -d'|' -f2)
            TAGS=$(echo "$REMINDER" | cut -d'|' -f3)
            echo ""
            echo "┄ Prompt $NUM ╌ still on: $TAGS"
            echo "  (type /tag to update)"
            echo ""
        elif [[ "$REMINDER" == HARD* ]]; then
            NUM=$(echo "$REMINDER" | cut -d'|' -f2)
            TAGS=$(echo "$REMINDER" | cut -d'|' -f3)
            echo ""
            echo "┄ Prompt $NUM ╌ Tags check ╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"
            echo "  Current: $TAGS"
            echo "  Still correct? Re-send your prompt to continue."
            echo "  Or: /tag phase:development feature:new-feature"
            echo "┄╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"
            echo ""
        fi

        exit 0
    fi
fi

# ── Context missing or stale — fetch from backend ─────────────────────────────
FETCHED=$(python3 -c "
import json, sys, urllib.request, urllib.error
url = sys.argv[1] + '/tags/session-context?project=' + sys.argv[2]
try:
    resp = urllib.request.urlopen(url, timeout=2)
    data = json.loads(resp.read())
    tags = data.get('tags', {})
    phase = tags.get('phase') or ''
    if not phase:
        print('NO_PHASE')
    else:
        tags_list = []
        for k in ('phase', 'feature', 'bug_ref'):
            if tags.get(k):
                key = 'bug' if k == 'bug_ref' else k
                tags_list.append(f'{key}:{tags[k]}')
        print(json.dumps({'tags': tags, 'tags_list': tags_list}))
except:
    print('NO_PHASE')
" "$BACKEND_URL" "$ACTIVE_PROJECT" 2>/dev/null || echo "NO_PHASE")

if [ "$FETCHED" = "NO_PHASE" ]; then
    echo ""
    echo "⚡ No session tags. Start with:"
    echo ""
    echo "  /tag phase:<phase> [feature:name] [bug:ref]"
    echo ""
    echo "  Phases: discovery | development | testing | review | production | maintenance | bugfix"
    echo ""
    echo "  Examples:"
    echo "    /tag phase:development"
    echo "    /tag phase:development feature:auth"
    echo "    /tag phase:bugfix bug:login-500"
    echo ""
    exit 2
fi

# Write .agent-context from fetched data
TAGS_JSON=$(echo "$FETCHED" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('tags', {})))")
TAGS_LIST=$(echo "$FETCHED" | python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get('tags_list', [])))")
TAGS_DISPLAY=$(echo "$TAGS_LIST" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin)))")

python3 -c "
import json, sys
tags = json.loads(sys.argv[1])
tags_list = json.loads(sys.argv[2])
ctx = {
    'session_id': sys.argv[3],
    'session_src': 'claude_cli',
    'tags': tags,
    'tags_list': tags_list,
    'set_at': sys.argv[4],
    'prompt_count': 0,
}
open(sys.argv[5], 'w').write(json.dumps(ctx, indent=2))
" "$TAGS_JSON" "$TAGS_LIST" "$SESSION" "$TIMESTAMP" "$CONTEXT_FILE" 2>/dev/null

echo ""
echo "⚡ Session tags: $TAGS_DISPLAY"
echo ""

# Refresh memory files in background
curl -sf --connect-timeout 2 --max-time 10 \
    -X POST "${BACKEND_URL}/memory/${ACTIVE_PROJECT}/regenerate?scope=root" \
    -H "Content-Type: application/json" \
    -o /dev/null 2>/dev/null &

exit 0
