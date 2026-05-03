#!/usr/bin/env bash
# Stop hook — auto-commit and push changed files after every Claude CLI session.
#
# Fires when Claude Code finishes responding (Stop event).
# Reads auto_commit_push from project.yaml — if false/absent, exits immediately.
#
# Strategy:
#   1. Try the aicli backend API (http://localhost:8000/git/{project}/commit-push) — preferred.
#      The backend writes to commit_log.jsonl itself (source: "aicli_backend").
#      This hook adds a thin wrapper entry (source: "claude_cli") with session_id + outcome.
#   2. Fallback: direct git when backend is not running.
#      This hook writes the log entry directly (source: "claude_cli_direct").
#
# ALL outcomes are logged — success, push failure, no changes, API errors.
# Log: workspace/{project}/history/commit_log.jsonl

INPUT=$(cat)  # Claude Code sends JSON on stdin; consume it

WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ── Helpers ───────────────────────────────────────────────────────────────────

_log_entry() {
    # Usage: _log_entry <json-string>
    python3 -c "
import json, sys
from pathlib import Path
entry = json.loads(sys.argv[1])
p = Path('$COMMIT_LOG')
p.parent.mkdir(parents=True, exist_ok=True)
with open(p, 'a') as f:
    f.write(json.dumps(entry) + '\n')
" "$1" 2>/dev/null || true
}

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
COMMIT_LOG="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/history/commit_log.jsonl"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

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

[ -z "$CODE_DIR" ] && CODE_DIR="$WORK_DIR"

# Must be a git repo
[ ! -d "${CODE_DIR}/.git" ] && exit 0

SESSION=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('session_id', ''))
except:
    print('')
" 2>/dev/null || echo "")

# ── Try aicli backend API ─────────────────────────────────────────────────────
BACKEND_URL=$(python3 -c "
import yaml, sys, os
config = os.path.join(sys.argv[1], 'aicli.yaml')
try:
    d = yaml.safe_load(open(config)) or {}
    print(d.get('backend_url', 'http://localhost:8000').rstrip('/'))
except:
    print('http://localhost:8000')
" "$WORK_DIR" 2>/dev/null || echo "http://localhost:8000")

BACKEND_OK=$(curl -sf --connect-timeout 2 "${BACKEND_URL}/health" -o /dev/null 2>/dev/null && echo "yes" || echo "no")

if [ "$BACKEND_OK" = "yes" ]; then
    CLAUDE_KEY="${ANTHROPIC_API_KEY:-}"
    SESSION_HINT="after claude cli session ${SESSION:0:8}"

    # The backend endpoint writes its own commit_log entry (source: "aicli_backend").
    # We capture the result and write a thin wrapper entry with source: "claude_cli"
    # so session_id is traceable even though the backend doesn't know it.
    RESULT=$(curl -sf --connect-timeout 5 --max-time 60 \
        -X POST "${BACKEND_URL}/git/${ACTIVE_PROJECT}/commit-push" \
        -H "Content-Type: application/json" \
        -H "X-Anthropic-Key: ${CLAUDE_KEY}" \
        -d "{\"message_hint\": \"${SESSION_HINT}\", \"provider\": \"claude\", \"skip_pull\": false, \"session_id\": \"${SESSION}\", \"source\": \"claude_cli\"}" \
        2>/dev/null)
    CURL_RC=$?

    if [ $CURL_RC -ne 0 ] || [ -z "$RESULT" ]; then
        # Backend call failed — log the error
        _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"api_error\",\"source\":\"claude_cli\",\"session_id\":\"$SESSION\",\"error\":\"curl failed (rc=$CURL_RC), backend may be unhealthy\"}"
        echo "[aicli] ✗ Backend call failed (curl rc=$CURL_RC). Falling through to direct git." >&2
    else
        COMMITTED=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('yes' if d.get('committed') else 'no')
except:
    print('no')
" 2>/dev/null || echo "no")

        REASON=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('reason', ''))
except:
    print('')
" 2>/dev/null || echo "")

        if [ "$COMMITTED" != "yes" ]; then
            # No changes — backend already logged a "skipped" entry; add session_id wrapper
            _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"skipped\",\"reason\":\"no_changes\",\"source\":\"claude_cli\",\"session_id\":\"$SESSION\"}"
            echo "[aicli] Nothing to commit." >&2
        else
            MSG=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    msg = d.get('commit_message', '')
    print(msg.replace('\"', '\\\\\"').replace('\n', ' '))
except:
    print('')
" 2>/dev/null || echo "")
            HASH=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('commit_hash', ''))
except:
    print('')
" 2>/dev/null || echo "")
            PUSHED=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print('true' if d.get('pushed') else 'false')
except:
    print('false')
" 2>/dev/null || echo "false")
            PUSH_ERR=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    err = d.get('push_error', '')[:200]
    print(err.replace('\"', '\\\\\"').replace('\n', ' '))
except:
    print('')
" 2>/dev/null || echo "")

            # Write claude_cli wrapper entry (session_id not known to the backend)
            _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"commit_push\",\"source\":\"claude_cli\",\"session_id\":\"$SESSION\",\"hash\":\"$HASH\",\"message\":\"$MSG\",\"pushed\":$PUSHED,\"push_error\":\"$PUSH_ERR\"}"

            if [ "$PUSHED" = "true" ]; then
                echo "[aicli] ↑ Auto-pushed: ${MSG}" >&2
            else
                echo "[aicli] ✓ Committed but push failed: ${PUSH_ERR}" >&2
            fi
        fi
        exit 0
    fi
fi

# ── Fallback: direct git (backend not running) ────────────────────────────────
echo "[aicli] Backend unavailable — using direct git." >&2
cd "$CODE_DIR" || exit 0

CHANGES=$(git status --porcelain 2>/dev/null)
if [ -z "$CHANGES" ]; then
    _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"skipped\",\"reason\":\"no_changes\",\"source\":\"claude_cli_direct\",\"session_id\":\"$SESSION\"}"
    exit 0
fi

# Load git credentials from state/.git_token
TOKEN_FILE="${WORK_DIR}/workspace/${ACTIVE_PROJECT}/state/.git_token"

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

# Stage and commit
git add -A 2>/dev/null

STAGED=$(git diff --name-only --cached 2>/dev/null | wc -l | tr -d ' ')
if [ "$STAGED" -eq 0 ]; then
    _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"skipped\",\"reason\":\"nothing_staged\",\"source\":\"claude_cli_direct\",\"session_id\":\"$SESSION\"}"
    exit 0
fi

TS_HUMAN=$(date -u +"%Y-%m-%d %H:%M UTC")
COMMIT_MSG="chore(cli): auto-commit after AI session — ${STAGED} file(s) — ${TS_HUMAN}"
COMMIT_OUT=$(git commit -m "$COMMIT_MSG" 2>&1) || {
    _log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"error\",\"reason\":\"commit_failed\",\"source\":\"claude_cli_direct\",\"session_id\":\"$SESSION\",\"error\":\"$(echo $COMMIT_OUT | head -c 200)\"}"
    exit 0
}

HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "")
PUSHED_OK="false"
PUSH_ERR_MSG=""

# Push with inline credentials (never writes to .git/config)
if [ -n "$GIT_TOKEN" ] && [ -n "$GITHUB_REPO" ]; then
    AUTHED_URL=$(python3 -c "
import sys
repo = sys.argv[1]; user = sys.argv[2]; token = sys.argv[3]
parts = repo.split('://', 1)
proto = parts[0] if len(parts) > 1 else 'https'
rest  = parts[1] if len(parts) > 1 else parts[0]
rest  = rest.split('@', 1)[-1]
print(f'{proto}://{user}:{token}@{rest}')
" "$GITHUB_REPO" "$GIT_USERNAME" "$GIT_TOKEN" 2>/dev/null)

    if [ -n "$AUTHED_URL" ]; then
        PUSH_OUT=$(git -c "remote.origin.url=${AUTHED_URL}" \
            push --set-upstream origin "$GIT_BRANCH" 2>&1) && {
            PUSHED_OK="true"
            echo "[aicli] ↑ Auto-pushed (direct): ${COMMIT_MSG}" >&2
        } || {
            PUSH_ERR_MSG=$(echo "$PUSH_OUT" | tail -3 | tr '\n' ' ' | head -c 200)
            echo "[aicli] ✓ Committed (push failed): ${PUSH_ERR_MSG}" >&2
        }
    else
        PUSH_ERR_MSG="could not build authenticated URL"
        echo "[aicli] ✓ Committed (no auth URL): ${COMMIT_MSG}" >&2
    fi
else
    PUSH_OUT=$(git push --set-upstream origin "$GIT_BRANCH" 2>&1) && {
        PUSHED_OK="true"
        echo "[aicli] ↑ Auto-pushed (direct, no token): ${COMMIT_MSG}" >&2
    } || {
        PUSH_ERR_MSG=$(echo "$PUSH_OUT" | tail -3 | tr '\n' ' ' | head -c 200)
        echo "[aicli] ✓ Committed (push failed): ${PUSH_ERR_MSG}" >&2
    }
fi

# Sanitise strings for JSON embedding
COMMIT_MSG_J=$(echo "$COMMIT_MSG" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo "\"$COMMIT_MSG\"")
PUSH_ERR_J=$(echo "$PUSH_ERR_MSG" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo "\"\"")

_log_entry "{\"ts\":\"$TIMESTAMP\",\"action\":\"commit_push\",\"source\":\"claude_cli_direct\",\"session_id\":\"$SESSION\",\"hash\":\"$HASH\",\"message\":$COMMIT_MSG_J,\"pushed\":$PUSHED_OK,\"push_error\":$PUSH_ERR_J}"

exit 0
