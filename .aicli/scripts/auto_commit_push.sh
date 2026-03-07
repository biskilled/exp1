#!/usr/bin/env bash
# Stop hook — auto-commit and push changed files after every Claude CLI session.
#
# Fires when Claude Code finishes responding (Stop event).
# Reads auto_commit_push from project.yaml — if false/absent, exits immediately.
#
# Strategy:
#   1. Try the aicli backend API (http://localhost:8000) — preferred path because
#      it handles credentials, .gitignore, and LLM commit message generation.
#   2. Fallback: direct git operations using creds from _system/.git_token.

INPUT=$(cat)  # Claude Code sends JSON on stdin; consume it

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ── Detect active project from aicli.yaml ────────────────────────────────────
ACTIVE_PROJECT=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('active_project', 'aicli'))
except:
    print('aicli')
" "$WORK_DIR" 2>/dev/null || echo "aicli")

PROJ_YAML="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/project.yaml"

# ── Check if auto_commit_push is enabled ─────────────────────────────────────
ENABLED=$(python3 -c "
import yaml, sys
try:
    d = yaml.safe_load(open(sys.argv[1])) or {}
    print('yes' if d.get('auto_commit_push') else 'no')
except:
    print('no')
" "$PROJ_YAML" 2>/dev/null || echo "no")

[ "$ENABLED" != "yes" ] && exit 0

# ── Read code_dir from project.yaml ──────────────────────────────────────────
CODE_DIR=$(python3 -c "
import yaml, sys
try:
    d = yaml.safe_load(open(sys.argv[1])) or {}
    print(d.get('code_dir', '').strip())
except:
    print('')
" "$PROJ_YAML" 2>/dev/null || echo "")

# Default to WORK_DIR if code_dir not set
[ -z "$CODE_DIR" ] && CODE_DIR="$WORK_DIR"

# Must be a git repo
[ ! -d "${CODE_DIR}/.git" ] && exit 0

# ── Try aicli backend API (preferred — uses LLM commit message + credentials) ─
BACKEND_URL="http://localhost:8000"

BACKEND_OK=$(curl -sf --connect-timeout 2 \
    "${BACKEND_URL}/health" \
    -o /dev/null 2>/dev/null && echo "yes" || echo "no")

if [ "$BACKEND_OK" = "yes" ]; then
    CLAUDE_KEY="${ANTHROPIC_API_KEY:-}"
    SESSION_HINT=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print('after claude cli session ' + d.get('session_id','')[:8])
except:
    print('after claude cli session')
" 2>/dev/null || echo "after claude cli session")

    RESULT=$(curl -sf --connect-timeout 5 --max-time 60 \
        -X POST "${BACKEND_URL}/git/${ACTIVE_PROJECT}/commit-push" \
        -H "Content-Type: application/json" \
        -H "X-Anthropic-Key: ${CLAUDE_KEY}" \
        -d "{\"message_hint\": \"${SESSION_HINT}\", \"provider\": \"claude\", \"skip_pull\": false}" \
        2>/dev/null)

    # Parse result
    COMMITTED=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('committed') else 'no')
except:
    print('no')
" 2>/dev/null || echo "no")

    if [ "$COMMITTED" = "yes" ]; then
        PUSHED=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('pushed') else 'no')
except:
    print('no')
" 2>/dev/null || echo "no")
        MSG=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('commit_message', ''))
except:
    print('')
" 2>/dev/null || echo "")
        if [ "$PUSHED" = "yes" ]; then
            echo "[aicli] ↑ Auto-pushed: ${MSG}" >&2
        else
            PUSH_ERR=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('push_error', '')[:120])
except:
    print('')
" 2>/dev/null || echo "")
            echo "[aicli] ✓ Committed but push failed: ${PUSH_ERR}" >&2
        fi
    else
        # "committed": false means no changes — silent
        :
    fi
    exit 0
fi

# ── Fallback: direct git (backend not running) ────────────────────────────────
cd "$CODE_DIR" || exit 0

# Any changes?
CHANGES=$(git status --porcelain 2>/dev/null)
[ -z "$CHANGES" ] && exit 0

# Load git credentials from _system/.git_token
TOKEN_FILE="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/_system/.git_token"

eval "$(python3 -c "
import json, sys, yaml
from pathlib import Path

token_file = Path(sys.argv[1])
proj_yaml  = Path(sys.argv[2])

token = username = repo = branch = ''
try:
    creds = json.loads(token_file.read_text())
    token    = creds.get('token', '')
    username = creds.get('username', '')
except Exception:
    pass
try:
    cfg    = yaml.safe_load(proj_yaml.read_text()) or {}
    repo   = cfg.get('github_repo', '')
    branch = cfg.get('git_branch', '')
except Exception:
    pass

print(f'GIT_TOKEN={token!r}')
print(f'GIT_USERNAME={username!r}')
print(f'GITHUB_REPO={repo!r}')
print(f'GIT_BRANCH={branch!r}')
" "$TOKEN_FILE" "$PROJ_YAML" 2>/dev/null || echo "")"

[ -z "$GIT_BRANCH" ] && GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "master")

# Protect secrets in .gitignore
GITIGNORE="${CODE_DIR}/.gitignore"
for pattern in "**/_system/" "**/.git_token" "**/.env" "**/.env.*" "**/*.pem" "**/*.key"; do
    grep -qF "$pattern" "$GITIGNORE" 2>/dev/null || echo "$pattern" >> "$GITIGNORE"
done

# Stage and commit
git add -A 2>/dev/null

STAGED=$(git diff --name-only --cached 2>/dev/null | wc -l | tr -d ' ')
[ "$STAGED" -eq 0 ] && exit 0

TS=$(date -u +"%Y-%m-%d %H:%M UTC")
COMMIT_MSG="chore(cli): auto-commit after AI session — ${STAGED} file(s) — ${TS}"
git commit -m "$COMMIT_MSG" 2>/dev/null || exit 0

# Push with inline credentials (never writes to .git/config)
if [ -n "$GIT_TOKEN" ] && [ -n "$GITHUB_REPO" ]; then
    AUTHED_URL=$(python3 -c "
import sys
repo = sys.argv[1]; user = sys.argv[2]; token = sys.argv[3]
# Strip any existing credentials from the URL
parts = repo.split('://', 1)
proto = parts[0] if len(parts) > 1 else 'https'
rest  = parts[1] if len(parts) > 1 else parts[0]
rest  = rest.split('@', 1)[-1]  # remove existing user@
print(f'{proto}://{user}:{token}@{rest}')
" "$GITHUB_REPO" "$GIT_USERNAME" "$GIT_TOKEN" 2>/dev/null)

    if [ -n "$AUTHED_URL" ]; then
        git -c "remote.origin.url=${AUTHED_URL}" \
            push --set-upstream origin "$GIT_BRANCH" 2>/dev/null \
            && echo "[aicli] ↑ Auto-pushed (direct): ${COMMIT_MSG}" >&2 \
            || echo "[aicli] ✓ Committed (push failed): ${COMMIT_MSG}" >&2
    else
        echo "[aicli] ✓ Committed (no credentials for push): ${COMMIT_MSG}" >&2
    fi
else
    git push --set-upstream origin "$GIT_BRANCH" 2>/dev/null \
        && echo "[aicli] ↑ Auto-pushed (direct): ${COMMIT_MSG}" >&2 \
        || echo "[aicli] ✓ Committed (push skipped): ${COMMIT_MSG}" >&2
fi

exit 0
