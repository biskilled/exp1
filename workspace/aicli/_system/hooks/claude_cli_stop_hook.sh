#!/usr/bin/env bash
# Claude Code native Stop hook
# Fires after EVERY Claude CLI response (when using `claude` directly, not aicli).
# Input: JSON on stdin with fields: hook_event_name, stop_hook_active, last_assistant_message
#
# To enable: place (or symlink) this file, then configure .claude/settings.json:
#   { "hooks": { "Stop": [{ "hooks": [{ "type": "command", "command": "bash /path/to/this.sh" }] }] } }

set -euo pipefail

# Read stdin JSON (Claude CLI always sends it)
INPUT=$(cat)

# Avoid infinite loop — Stop hook won't fire again if stop_hook_active=true
STOP_ACTIVE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('stop_hook_active', False))" 2>/dev/null || echo "False")
if [ "$STOP_ACTIVE" = "True" ]; then
    exit 0
fi

# Check for git changes
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

CHANGED=$(git diff --name-only 2>/dev/null; git diff --name-only --cached 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)

if [ -z "$CHANGED" ]; then
    exit 0
fi

echo "Auto-committing changes..."

# Generate a commit message from the last assistant message
LAST_MSG=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
msg = d.get('last_assistant_message', '')
# Truncate to first 200 chars for a rough commit msg
print(msg[:200].replace('\n', ' ').strip())
" 2>/dev/null || echo "AI-assisted changes")

BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
COMMIT_MSG="[AI] ${LAST_MSG:0:80} (${TIMESTAMP})"

# Stage all non-ignored files
git add -A

git commit -m "$COMMIT_MSG" --quiet && echo "Committed: ${COMMIT_MSG:0:60}"
git push --quiet && echo "Pushed to $BRANCH"
