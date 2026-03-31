#!/usr/bin/env bash
# UserPromptSubmit hook — enforces session context before allowing prompts.
#
# Fires FIRST in UserPromptSubmit (before log_user_prompt.sh).
# On first prompt of a session (when .agent-context is missing or stale):
#   1. Fetches last known tags from GET /tags/session-context
#   2. Writes .agent-context file
#   3. Prints context to user, blocks prompt (exit 1)
#   4. Second attempt passes (exit 0)
#
# .agent-context format:
#   {"session_id":"abc123","session_src":"claude_cli","tags":{"stage":"discovery"},"set_at":"..."}

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

# ── If context file exists and has matching session_id → pass through ──────────
if [ -f "$CONTEXT_FILE" ]; then
    CONTEXT_SESSION=$(python3 -c "
import json, sys
try:
    d = json.loads(open(sys.argv[1]).read())
    print(d.get('session_id', ''))
except:
    print('')
" "$CONTEXT_FILE" 2>/dev/null || echo "")

    # If no session_id in file OR session matches → allow
    if [ -z "$CONTEXT_SESSION" ] || [ "$CONTEXT_SESSION" = "$SESSION" ]; then
        exit 0
    fi
fi

# ── Context missing or stale — fetch from backend and write file ───────────────
mkdir -p "$(dirname "$CONTEXT_FILE")"

FETCHED_TAGS=$(python3 -c "
import json, sys, urllib.request, urllib.error
url = sys.argv[1] + '/tags/session-context?project=' + sys.argv[2]
try:
    resp = urllib.request.urlopen(url, timeout=2)
    data = json.loads(resp.read())
    print(json.dumps(data.get('tags', {'stage': 'discovery'})))
except:
    print('{\"stage\": \"discovery\"}')
" "$BACKEND_URL" "$ACTIVE_PROJECT" 2>/dev/null || echo '{"stage": "discovery"}')

# Write .agent-context
python3 -c "
import json, sys
tags = json.loads(sys.argv[1])
ctx = {
    'session_id': sys.argv[2],
    'session_src': 'claude_cli',
    'tags': tags,
    'set_at': sys.argv[3],
}
open(sys.argv[4], 'w').write(json.dumps(ctx, indent=2))
" "$FETCHED_TAGS" "$SESSION" "$TIMESTAMP" "$CONTEXT_FILE" 2>/dev/null

# ── Print context to user and block this prompt ────────────────────────────────
TAGS_DISPLAY=$(python3 -c "
import json, sys
try:
    tags = json.loads(sys.argv[1])
    lines = ['  {}: {}'.format(k, v) for k, v in tags.items()]
    print('\n'.join(lines))
except:
    print('  stage: discovery')
" "$FETCHED_TAGS" 2>/dev/null || echo "  stage: discovery")

echo ""
echo "⚡ Session context loaded. Review tags and re-send your message."
echo ""
echo "Tags applied to this session:"
echo "$TAGS_DISPLAY"
echo ""
echo "To change: edit $CONTEXT_FILE"
echo "Your prompt was held. Re-send to proceed."
echo ""

# ── Refresh top_events.md so Claude Code loads fresh memory at session start ──
curl -sf --connect-timeout 2 --max-time 10 \
    -X POST "${BACKEND_URL}/memory/${ACTIVE_PROJECT}/regenerate?scope=root" \
    -H "Content-Type: application/json" \
    -o /dev/null 2>/dev/null &   # run in background, don't block session

# Exit 2 = block the prompt (Claude Code shows output above to user)
exit 2
