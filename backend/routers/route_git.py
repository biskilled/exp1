"""
Git router — status, credential setup, commit & push.

All git operations run in the project's code_dir (resolved from project.yaml).
Credentials (GitHub token) are stored in _system/.git_token (never in project.yaml).
"""

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml
import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from core.config import settings
from core.database import db
from core.prompt_loader import prompts as _prompts
from agents.providers import call_claude
from core.pipeline_log import pipeline_run, pipeline_run_sync, _finish_run

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_UPSERT_COMMIT = """
    INSERT INTO mem_mrr_commits
            (project_id, commit_hash, session_id, commit_msg, summary, diff_summary,
             author, author_email, created_at, tags, src, wi_id, user_id,
             commit_type, is_external)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (commit_hash) DO UPDATE
            SET session_id   = COALESCE(EXCLUDED.session_id,   mem_mrr_commits.session_id),
                commit_msg   = COALESCE(EXCLUDED.commit_msg,   mem_mrr_commits.commit_msg),
                summary      = CASE WHEN mem_mrr_commits.summary = '' THEN EXCLUDED.summary
                                    ELSE mem_mrr_commits.summary END,
                diff_summary = COALESCE(EXCLUDED.diff_summary, mem_mrr_commits.diff_summary),
                author       = CASE WHEN EXCLUDED.author != '' THEN EXCLUDED.author
                                    ELSE mem_mrr_commits.author END,
                author_email = CASE WHEN EXCLUDED.author_email != '' THEN EXCLUDED.author_email
                                    ELSE mem_mrr_commits.author_email END,
                created_at   = COALESCE(EXCLUDED.created_at, mem_mrr_commits.created_at),
                tags         = CASE WHEN EXCLUDED.tags != '{}' THEN EXCLUDED.tags
                                    ELSE mem_mrr_commits.tags END,
                src          = COALESCE(EXCLUDED.src, mem_mrr_commits.src),
                wi_id        = COALESCE(EXCLUDED.wi_id, mem_mrr_commits.wi_id),
                user_id      = COALESCE(EXCLUDED.user_id, mem_mrr_commits.user_id),
                commit_type  = CASE WHEN mem_mrr_commits.commit_type IS NULL THEN EXCLUDED.commit_type
                                    ELSE mem_mrr_commits.commit_type END
"""

# Link commit → most-recent prompt in the same session that occurred BEFORE the commit.
# created_at is passed as %s so we only link to prompts that predated the commit.
# Always updates (no IS NULL guard) so re-linking after backfill works correctly.
_SQL_LINK_COMMIT_TO_PROMPT = """
    UPDATE mem_mrr_commits SET prompt_id = (
        SELECT p.id FROM mem_mrr_prompts p
        WHERE p.project_id=%s
          AND p.session_id = %s
          AND p.created_at <= %s
        ORDER BY p.created_at DESC
        LIMIT 1
    )
    WHERE commit_hash = %s
"""

_SQL_LIST_COMMITS = """
    SELECT c.commit_hash, c.commit_msg, c.summary, c.tags,
           c.session_id, c.created_at,
           p.source_id AS prompt_source_id
    FROM mem_mrr_commits c
    LEFT JOIN mem_mrr_prompts p ON p.id = c.prompt_id
    WHERE c.project_id=%s
    ORDER BY c.created_at DESC NULLS LAST, c.created_at DESC
    LIMIT %s
"""

_SQL_GET_SESSION_COMMITS_WITH_WINDOW = """
    SELECT commit_hash, commit_msg, tags, created_at
          FROM mem_mrr_commits
         WHERE project_id=%s
           AND (session_id = %s
            OR (created_at BETWEEN %s::timestamptz AND %s::timestamptz))
         ORDER BY created_at
"""

_SQL_GET_SESSION_COMMITS_BY_ID = """
    SELECT commit_hash, commit_msg, tags, created_at
          FROM mem_mrr_commits
         WHERE project_id=%s AND session_id = %s
         ORDER BY created_at
"""

_SQL_GET_SESSION_TAGS = (
    "SELECT phase, feature, bug_ref, extra FROM mng_session_tags WHERE project_id=%s"
)

_SQL_UPSERT_SESSION_TAGS = """
    INSERT INTO mng_session_tags (project_id, phase, feature, bug_ref, extra, updated_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (project_id) DO UPDATE SET
        phase = EXCLUDED.phase,
        feature = EXCLUDED.feature,
        bug_ref = EXCLUDED.bug_ref,
        extra = EXCLUDED.extra,
        updated_at = NOW()
"""

# ── Router definition ─────────────────────────────────────────────────────────

router = APIRouter()


# ── Commit log helper ─────────────────────────────────────────────────────────

def _write_commit_log(project_name: str, entry: dict) -> None:
    """Append one JSON line to workspace/{project}/_system/commit_log.jsonl.

    Called from every commit-push code path — backend API, direct git fallback,
    and MCP tool — so the file becomes a single audit trail across all callers.
    The 'source' field distinguishes who triggered the commit:
      'aicli_backend'  — commit-push endpoint called (UI, aicli CLI, or hook via backend)
      'direct_git'     — hook fallback when backend is not running
      'cursor_mcp'     — Cursor triggered via MCP commit_push tool
    """
    try:
        if "ts" not in entry:
            entry["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_path = Path(settings.workspace_dir) / project_name / "_system" / "commit_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never break git operations because of logging


# ── Generated-file filter ──────────────────────────────────────────────────────

import re as _re
_GEN_FILE_PAT = _re.compile(
    r'^\s*(CLAUDE\.md|\.cursorrules|MEMORY\.md|\.ai/|\.cursor/|\.github/copilot|'
    r'workspace/.*/_system/|history\.jsonl|.*\.claude/memory)',
    _re.IGNORECASE,
)

def _filter_diff_stat(diff_stat: str) -> tuple[str, str]:
    """Return (code_stat, gen_stat) — split diff --stat by generated vs code files."""
    code_lines, gen_lines = [], []
    for line in (diff_stat or "").splitlines():
        if _GEN_FILE_PAT.match(line):
            gen_lines.append(line)
        else:
            code_lines.append(line)
    # Keep summary line (last line, has "N files changed") in both
    if code_lines or gen_lines:
        summary = (diff_stat or "").splitlines()[-1] if diff_stat else ""
        if summary and not _re.match(r'^\s*\w', summary.lstrip()):
            code_lines.append(summary)
    return "\n".join(code_lines), "\n".join(gen_lines)


# ── Commit embedding background task ───────────────────────────────────────────

def _read_commit_batch_size(project: str) -> int:
    """Read commit_embed.batch_size from project.yaml (default 5)."""
    try:
        cfg_path = Path(settings.workspace_dir) / project / "project.yaml"
        cfg = yaml.safe_load(cfg_path.read_text()) if cfg_path.exists() else {}
        return int(cfg.get("commit_embed", {}).get("batch_size", 5))
    except Exception:
        return 5


async def _embed_commit_background(project: str, commit_hash: str) -> None:
    """Threshold-based commit batch embedding.

    Counts pending commits (event_id IS NULL). When count >= batch_size (default 5,
    configurable via project.yaml commit_embed.batch_size), runs process_commit_batch()
    to digest all pending commits grouped by tag context into batch events.
    Otherwise defers — the next commit push or /embed-commits call will process them.
    """
    if not db.is_available():
        return
    project_id = db.get_or_create_project_id(project)
    async with pipeline_run(project_id, "commit_embed", commit_hash) as ctx:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_commits "
                        "WHERE project_id=%s AND event_id IS NULL",
                        (project_id,),
                    )
                    pending = cur.fetchone()[0] or 0
        except Exception as e:
            log.debug(f"_embed_commit_background pending count error: {e}")
            return
        ctx["items_in"] = pending
        batch_size = _read_commit_batch_size(project)
        if pending >= batch_size:
            log.debug(
                f"_embed_commit_background: {pending} pending commits queued for backlog (batch_size={batch_size})"
            )
        else:
            log.debug(
                f"_embed_commit_background: deferred ({pending} pending < batch_size={batch_size})"
            )


async def _check_backlog_threshold(project: str, source_type: str) -> None:
    """Trigger work-item classification if mode=threshold and pending count is met."""
    try:
        from memory.memory_work_items import MemoryWorkItems
        await MemoryWorkItems(project).check_and_trigger(source_type)
    except Exception as e:
        log.debug(f"_check_backlog_threshold({source_type}) error: {e}")


def _extract_commit_code_background(project: str, commit_hash: str) -> None:
    """Run tree-sitter symbol extraction and insert rows into mem_mrr_commits_code."""
    import asyncio
    from core.pipeline_log import pipeline_run_sync, _finish_run
    p_id = db.get_project_id(project)
    run_id, t0 = pipeline_run_sync(p_id or 0, "commit_code_extract", commit_hash) if p_id else (None, 0)
    loop = asyncio.new_event_loop()
    try:
        from memory.memory_code_parser import extract_commit_code
        loop.run_until_complete(extract_commit_code(project, commit_hash))
        _finish_run(run_id, "ok", 1, 1, t0)
    except Exception as e:
        log.debug(f"_extract_commit_code_background error ({commit_hash[:8]}): {e}")
        _finish_run(run_id, "error", 1, 0, t0, str(e))
    finally:
        loop.close()




# ── Commit→prompt linking background task ─────────────────────────────────────

def _extract_commit_type(message: str) -> str | None:
    """Derive work item type hint from conventional commit prefix."""
    msg = (message or "").lower().strip()
    if msg.startswith(("fix", "bug")):
        return "bug"
    if msg.startswith(("feat", "feature")):
        return "feature"
    if msg.startswith(("chore", "refactor", "perf", "style")):
        return "task"
    if msg.startswith(("test", "ci", "docs")):
        return "task"
    return None


def _sync_commit_and_link(project: str, commit_hash: str, session_id: str | None,
                          commit_msg: str, committed_at: str,
                          diff_summary: str = "",
                          author: str = "", author_email: str = "",
                          summary: str = "",
                          commit_type: str | None = None,
                          is_external: bool = False) -> None:
    """Upsert the new commit into mem_mrr_commits and link it to its triggering prompt."""
    if not db.is_available():
        return
    project_id = db.get_or_create_project_id(project)
    from core.pipeline_log import pipeline_run_sync, _finish_run
    run_id, t0 = pipeline_run_sync(project_id, "commit_store", commit_hash)
    try:
        # tags = user intent only: phase/feature/bug from active session tags
        tags_dict: dict = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_SESSION_TAGS, (project_id,))
                    st_row = cur.fetchone()
                    if st_row:
                        _phase, _feature, _bug_ref = st_row[0], st_row[1], st_row[2]
                        if _phase:   tags_dict["phase"]   = _phase
                        if _feature: tags_dict["feature"] = _feature
                        if _bug_ref: tags_dict["bug"]     = _bug_ref
        except Exception:
            pass

        from core.auth import ADMIN_USER_ID
        # Auto-SKIP commits that only changed generated/memory files — no code content to classify
        wi_id_val = "SKIP" if not diff_summary or not diff_summary.strip() else None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_COMMIT,
                    (project_id, commit_hash, session_id, commit_msg, summary or "",
                     diff_summary or None,
                     author, author_email,
                     committed_at or datetime.now(timezone.utc),  # git timestamp → created_at
                     json.dumps(tags_dict), "git", wi_id_val, ADMIN_USER_ID,
                     commit_type, is_external),
                )
                if session_id:
                    commit_ts = committed_at or datetime.now(timezone.utc)
                    cur.execute(_SQL_LINK_COMMIT_TO_PROMPT,
                                (project_id, session_id, commit_ts, commit_hash))
                    if cur.rowcount:
                        log.info(f"Commit {commit_hash[:8]} linked to prompt (session {session_id[:8]})")
        _finish_run(run_id, "ok", 1, 1, t0)
    except Exception as exc:
        log.warning(f"_sync_commit_and_link failed for {commit_hash}: {exc}")
        _finish_run(run_id, "error", 1, 0, t0, str(exc))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _proj_dir(project_name: str) -> Path:
    return Path(settings.workspace_dir) / project_name


def _resolve_code_dir(project_name: str) -> Path:
    proj_dir = _proj_dir(project_name)
    proj_yaml = proj_dir / "project.yaml"
    cfg = {}
    if proj_yaml.exists():
        try:
            cfg = yaml.safe_load(proj_yaml.read_text()) or {}
        except Exception:
            pass
    code_dir = cfg.get("code_dir", "")
    if not code_dir:
        return proj_dir
    p = Path(code_dir)
    if not p.is_absolute():
        p = (proj_dir / code_dir).resolve()
    return p


def _git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _is_git_repo(code_dir: Path) -> bool:
    rc, _, _ = _git(["rev-parse", "--git-dir"], code_dir)
    return rc == 0


def _build_authed_url(repo_url: str, username: str, token: str) -> str:
    """Embed PAT into HTTPS URL: https://username:token@github.com/user/repo"""
    if "://" not in repo_url:
        return repo_url
    proto, rest = repo_url.split("://", 1)
    if "@" in rest:          # strip existing creds
        rest = rest.split("@", 1)[1]
    if username and token:
        return f"{proto}://{username}:{token}@{rest}"
    if token:
        return f"{proto}://oauth2:{token}@{rest}"
    return repo_url


def _load_creds(project_name: str) -> dict:
    token_file = _proj_dir(project_name) / "_system" / ".git_token"
    if token_file.exists():
        try:
            return json.loads(token_file.read_text())
        except Exception:
            pass
    return {}


def _apply_creds_to_remote(project_name: str, code_dir: Path):
    """Set the remote URL to include the stored token (used only during setup)."""
    creds = _load_creds(project_name)
    token = creds.get("token", "")
    if not token:
        return
    proj_dir = _proj_dir(project_name)
    try:
        cfg = yaml.safe_load((proj_dir / "project.yaml").read_text()) or {}
    except Exception:
        return
    github_repo = cfg.get("github_repo", "")
    if not github_repo:
        return
    authed_url = _build_authed_url(github_repo, creds.get("username", ""), token)
    rc, _, _ = _git(["remote", "get-url", "origin"], code_dir)
    if rc == 0:
        _git(["remote", "set-url", "origin", authed_url], code_dir)
    else:
        _git(["remote", "add", "origin", authed_url], code_dir)


def _authed_url(project_name: str) -> str:
    """Return an authenticated remote URL built from stored credentials.
    Does NOT modify any files — credentials are passed inline to git via -c.
    Returns empty string if no credentials are stored.
    """
    creds = _load_creds(project_name)
    token = creds.get("token", "")
    if not token:
        return ""
    try:
        cfg = yaml.safe_load((_proj_dir(project_name) / "project.yaml").read_text()) or {}
    except Exception:
        return ""
    repo = cfg.get("github_repo", "")
    return _build_authed_url(repo, creds.get("username", ""), token) if repo else ""


def _git_authed(args: list[str], cwd: Path, project_name: str) -> tuple[int, str, str]:
    """Run git with inline credentials via -c remote.origin.url=<authed>.
    This avoids modifying .git/config on every call (which would cause uvicorn --reload
    to restart the server).  Falls back to plain _git() if no credentials are stored.
    """
    url = _authed_url(project_name)
    if url:
        return _git(["-c", f"remote.origin.url={url}"] + args, cwd)
    return _git(args, cwd)


def _ensure_upstream(branch: str, code_dir: Path) -> None:
    """Configure the local branch to track origin/<branch>.
    Idempotent and fails silently (remote branch may not exist yet on first push).
    After this runs, bare 'git pull' / 'git push' work without specifying remote + branch.
    """
    _git(["branch", f"--set-upstream-to=origin/{branch}", branch], code_dir)


# ── .gitignore management ─────────────────────────────────────────────────────

# Patterns that must always be in .gitignore — credentials and private data.
# Use **/ prefix so they match at ANY depth, not just the repo root.
_MUST_IGNORE = [
    "**/_system/",     # _system/ dir anywhere in the tree
    "**/.git_token",   # token file anywhere
    "**/.env",
    "**/.env.*",
    "**/.envrc",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/*.cert",
    "**/secrets/",
    "**/credentials/",
]

_GITIGNORE_DEFAULT = """\
# ── Secrets & credentials (DO NOT REMOVE) ─────────────────────────────────────
# **/ prefix matches at any depth (e.g. workspace/aicli/_system/.git_token)
**/_system/
**/.git_token
**/.env
**/.env.*
**/.envrc
**/*.pem
**/*.key
**/*.p12
**/*.pfx
**/*.cert
**/secrets/
**/credentials/

# ── Python ─────────────────────────────────────────────────────────────────────
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.Python
*.egg-info/
.eggs/
dist/
build/
.venv/
venv/
env/
ENV/

# ── Node / Frontend ────────────────────────────────────────────────────────────
node_modules/
npm-debug.log*
yarn-debug.log*
.npm/
.yarn/
.vite/
dist/

# ── OS / Editor ────────────────────────────────────────────────────────────────
.DS_Store
._*
Thumbs.db
desktop.ini
ehthumbs.db
.vscode/
.idea/
*.swp
*.swo
*~

# ── Logs & temp ────────────────────────────────────────────────────────────────
*.log
logs/
tmp/
.cache/
"""


def _ensure_gitignore(code_dir: Path) -> list[str]:
    """Create or update .gitignore, guaranteeing all sensitive patterns are present.
    Returns list of action strings for logging.
    """
    gi = code_dir / ".gitignore"
    actions: list[str] = []

    if not gi.exists():
        gi.write_text(_GITIGNORE_DEFAULT)
        actions.append("Created .gitignore with secure defaults")
        return actions

    # Check which required entries are missing and append them
    content = gi.read_text()
    missing = [p for p in _MUST_IGNORE if p not in content]
    if missing:
        addition = (
            "\n# ── aicli secrets (auto-added) ────────────────────────────────\n"
            + "\n".join(missing)
            + "\n"
        )
        gi.write_text(content.rstrip("\n") + "\n" + addition)
        actions.append(f"Updated .gitignore: added {', '.join(missing)}")

    return actions


def _untrack_secrets(code_dir: Path) -> list[str]:
    """Remove sensitive files from git tracking without deleting them from disk.

    This handles the case where secrets were committed BEFORE .gitignore was set up.
    git rm --cached removes files from the index; the actual files are left intact.
    Returns list of action strings for logging.
    """
    # Find all currently-tracked files
    _, tracked_out, _ = _git(["ls-files"], code_dir)
    tracked = tracked_out.splitlines()

    to_remove: list[str] = []
    for f in tracked:
        f_path   = Path(f)
        parts    = f_path.parts        # e.g. ('workspace', 'aicli', '_system', '.git_token')
        name     = f_path.name.lower() # filename only, e.g. '.git_token'
        parts_lc = {p.lower() for p in parts}
        if (
            "_system"     in parts_lc   # _system/ anywhere in the path tree
            or "secrets"      in parts_lc
            or "credentials"  in parts_lc
            or name == ".git_token"
            or name == ".env"
            or name == ".envrc"
            or name.startswith(".env.")
            or name.endswith(".pem")
            or name.endswith(".key")
            or name.endswith(".p12")
            or name.endswith(".pfx")
            or name.endswith(".cert")
        ):
            to_remove.append(f)

    if not to_remove:
        return []

    _git(["rm", "--cached", "-r", "--ignore-unmatch", "--quiet"] + to_remove, code_dir)
    return [f"Untracked secrets from git index: {', '.join(to_remove)}"]


# ── GitHub Device Flow OAuth ─────────────────────────────────────────────────

class DeviceFlowStartRequest(BaseModel):
    client_id: str


@router.post("/oauth/device/start")
async def oauth_device_start(body: DeviceFlowStartRequest):
    """Start GitHub Device Flow — returns user_code to display and device_code for polling."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/device/code",
            data={"client_id": body.client_id, "scope": "repo user:email"},
            headers={"Accept": "application/json"},
            timeout=15,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {resp.status_code}")
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data.get("error_description", data["error"]))
    return data   # device_code, user_code, verification_uri, expires_in, interval


class DevicePollRequest(BaseModel):
    client_id: str
    device_code: str
    project_name: str = ""


@router.post("/oauth/device/poll")
async def oauth_device_poll(body: DevicePollRequest):
    """Poll GitHub for OAuth token. Returns {status} = pending|authorized|slow_down|expired|denied|error."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": body.client_id,
                "device_code": body.device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
            timeout=15,
        )
    data = resp.json()

    if "error" in data:
        err = data["error"]
        if err == "authorization_pending":
            return {"status": "pending"}
        if err == "slow_down":
            return {"status": "slow_down", "interval": data.get("interval", 10)}
        if err == "expired_token":
            return {"status": "expired"}
        if err == "access_denied":
            return {"status": "denied"}
        return {"status": "error", "detail": data.get("error_description", err)}

    token = data.get("access_token", "")
    if not token:
        return {"status": "error", "detail": "No access token returned"}

    # Fetch GitHub user info
    username = ""
    email = ""
    async with httpx.AsyncClient() as client:
        ur = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if ur.status_code == 200:
            ud = ur.json()
            username = ud.get("login", "")
            email = ud.get("email") or ""
            if not email:
                er = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                    timeout=10,
                )
                if er.status_code == 200:
                    emails_list = er.json()
                    primary = next((e for e in emails_list if e.get("primary")), None)
                    email = (primary or (emails_list[0] if emails_list else {})).get("email", "")

    # Persist credentials
    if body.project_name:
        sys_dir = _proj_dir(body.project_name) / "_system"
        sys_dir.mkdir(parents=True, exist_ok=True)
        (sys_dir / ".git_token").write_text(json.dumps(
            {"token": token, "username": username, "auth_method": "oauth"}
        ))
        code_dir = _resolve_code_dir(body.project_name)
        if code_dir.exists() and _is_git_repo(code_dir):
            if username:
                _git(["config", "user.name", username], code_dir)
            if email:
                _git(["config", "user.email", email], code_dir)
        try:
            proj_yaml = _proj_dir(body.project_name) / "project.yaml"
            existing = yaml.safe_load(proj_yaml.read_text()) if proj_yaml.exists() else {}
            if username:
                existing["git_username"] = username
            if email:
                existing["git_email"] = email
            proj_yaml.write_text(yaml.dump(existing, default_flow_style=False, allow_unicode=True))
        except Exception:
            pass

    return {"status": "authorized", "username": username, "email": email}


# ── Branches ─────────────────────────────────────────────────────────────────

@router.get("/{project_name}/branches")
async def git_branches(project_name: str):
    """List local and remote branches for the project's code_dir."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists() or not _is_git_repo(code_dir):
        return {"is_git_repo": False, "local_branches": [], "remote_branches": [],
                "current": "", "default_branch": ""}

    _, current, _ = _git(["branch", "--show-current"], code_dir)

    _, local_out, _ = _git(["branch", "--format=%(refname:short)"], code_dir)
    local_branches = [b.strip() for b in local_out.splitlines() if b.strip()]

    # Use inline credentials so ls-remote can reach private repos without touching .git/config
    _, remote_out, _ = _git_authed(["ls-remote", "--heads", "origin"], code_dir, project_name)
    remote_branches = []
    for line in remote_out.splitlines():
        if "\t" in line:
            ref = line.split("\t")[1].strip()
            name = ref.replace("refs/heads/", "")
            if name:
                remote_branches.append(name)

    # Detect remote default branch via symref
    _, head_out, _ = _git_authed(["ls-remote", "--symref", "origin", "HEAD"], code_dir, project_name)
    default_branch = ""
    for line in head_out.splitlines():
        if line.startswith("ref:") and "\t" in line:
            ref_part = line.split("\t")[0].replace("ref:", "").strip()
            default_branch = ref_part.replace("refs/heads/", "")
            break

    return {
        "is_git_repo": True,
        "current": current,
        "local_branches": local_branches,
        "remote_branches": remote_branches,
        "default_branch": default_branch,
    }


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/{project_name}/status")
async def git_status(project_name: str):
    """Return git status for the project's code_dir."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)

    if not code_dir.exists():
        return {"is_git_repo": False, "code_dir": str(code_dir), "error": "code_dir does not exist"}

    if not _is_git_repo(code_dir):
        return {"is_git_repo": False, "code_dir": str(code_dir)}

    _, branch, _   = _git(["branch", "--show-current"], code_dir)
    _, remote, _   = _git(["remote", "get-url", "origin"], code_dir)
    _, staged, _   = _git(["diff", "--name-only", "--cached"], code_dir)
    _, unstaged, _ = _git(["diff", "--name-only"], code_dir)
    _, untracked, _ = _git(["ls-files", "--others", "--exclude-standard"], code_dir)
    _, last_commit, _ = _git(["log", "--oneline", "-1"], code_dir)

    changed = list(dict.fromkeys(
        f for f in (staged + "\n" + unstaged + "\n" + untracked).splitlines() if f
    ))

    creds = _load_creds(project_name)

    return {
        "is_git_repo": True,
        "code_dir": str(code_dir),
        "branch": branch,
        "remote_url": remote,
        "changed_files": changed,
        "changed_count": len(changed),
        "last_commit": last_commit,
        "has_credentials": bool(creds.get("token")),
        "git_username": creds.get("username", ""),
    }


# ── Setup credentials ─────────────────────────────────────────────────────────

class GitSetupRequest(BaseModel):
    git_username: str = ""
    git_email: str = ""
    git_token: str = ""
    github_repo: str = ""        # repo URL — saves to project.yaml + sets up remote
    github_client_id: str = ""   # OAuth App client ID — saves to project.yaml
    git_branch: str = ""         # default push branch — saves to project.yaml
    init_if_needed: bool = True
    initial_commit: bool = False  # stage all files, create .gitignore + README.md


@router.post("/{project_name}/setup")
async def setup_git(project_name: str, body: GitSetupRequest):
    """Initialize git repo (if needed) and store credentials."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        raise HTTPException(status_code=404, detail=f"code_dir does not exist: {code_dir}")

    sys_dir = proj_dir / "_system"
    sys_dir.mkdir(parents=True, exist_ok=True)
    actions: list[str] = []

    # Load existing project.yaml to merge updates
    proj_yaml_path = proj_dir / "project.yaml"
    try:
        proj_cfg = yaml.safe_load(proj_yaml_path.read_text()) if proj_yaml_path.exists() else {}
    except Exception:
        proj_cfg = {}

    # Effective repo URL: request takes priority over stored value
    effective_repo = body.github_repo.strip() or proj_cfg.get("github_repo", "")

    # Init repo if needed
    if not _is_git_repo(code_dir):
        if not body.init_if_needed:
            raise HTTPException(status_code=400, detail="Not a git repository. Set init_if_needed=true.")
        _git(["init"], code_dir)
        actions.append("Initialized git repository")

    # git config user.name / user.email
    if body.git_username:
        _git(["config", "user.name", body.git_username], code_dir)
        actions.append(f"Set user.name = {body.git_username}")
    if body.git_email:
        _git(["config", "user.email", body.git_email], code_dir)
        actions.append(f"Set user.email = {body.git_email}")

    # Store new PAT credentials if provided
    if body.git_token:
        (sys_dir / ".git_token").write_text(json.dumps(
            {"token": body.git_token, "username": body.git_username}
        ))
        actions.append("Saved PAT to _system/.git_token")

    # Configure remote with PLAIN URL (credentials are never stored in .git/config;
    # they are injected at runtime via 'git -c remote.origin.url=<authed>' to avoid
    # triggering uvicorn --reload on every pull/push).
    if effective_repo:
        rc, _, _ = _git(["remote", "get-url", "origin"], code_dir)
        if rc == 0:
            _git(["remote", "set-url", "origin", effective_repo], code_dir)
            actions.append(f"Updated remote origin → {effective_repo}")
        else:
            _git(["remote", "add", "origin", effective_repo], code_dir)
            actions.append(f"Added remote origin: {effective_repo}")

    # Ensure .gitignore exists and protects all sensitive paths
    actions.extend(_ensure_gitignore(code_dir))

    # Remove any secrets that were accidentally committed before .gitignore was set up
    actions.extend(_untrack_secrets(code_dir))

    # Initial commit — stage all files and commit
    if body.initial_commit:
        # Create README.md if missing
        readme = code_dir / "README.md"
        if not readme.exists():
            display = project_name.replace("_", " ").replace("-", " ").title()
            readme.write_text(f"# {display}\n\nProject managed with [aicli](https://github.com).\n")
            actions.append("Created README.md")

        _git(["add", "-A"], code_dir)
        _, staged_out, _ = _git(["diff", "--name-only", "--cached"], code_dir)
        if staged_out.strip():
            rc_c, _, stderr_c = _git(["commit", "-m", "init: initial commit"], code_dir)
            if rc_c != 0:
                actions.append(f"Warning: initial commit failed: {stderr_c}")
            else:
                _, commit_hash, _ = _git(["rev-parse", "HEAD"], code_dir)
                file_count = len(staged_out.splitlines())
                actions.append(f"Initial commit ({file_count} files): {commit_hash[:8] if commit_hash else ''}")
        else:
            actions.append("Nothing to commit (working tree clean)")

    # Persist all non-sensitive fields to project.yaml in one write
    cfg_updates: dict = {}
    if body.git_username:  cfg_updates["git_username"]     = body.git_username
    if body.git_email:     cfg_updates["git_email"]        = body.git_email
    if effective_repo:     cfg_updates["github_repo"]      = effective_repo
    if body.github_client_id: cfg_updates["github_client_id"] = body.github_client_id
    if body.git_branch:    cfg_updates["git_branch"]       = body.git_branch
    if cfg_updates:
        try:
            proj_cfg.update(cfg_updates)
            proj_yaml_path.write_text(yaml.dump(proj_cfg, default_flow_style=False, allow_unicode=True))
        except Exception:
            pass

    return {"ok": True, "actions": actions, "code_dir": str(code_dir)}


# ── Create GitHub repo ────────────────────────────────────────────────────────

class CreateRepoRequest(BaseModel):
    project_name: str
    repo_name: str
    private: bool = True
    description: str = ""


@router.post("/oauth/create-repo")
async def create_github_repo(body: CreateRepoRequest):
    """Create a new GitHub repo using the stored OAuth/PAT token, then init locally."""
    creds = _load_creds(body.project_name)
    token = creds.get("token", "")
    if not token:
        raise HTTPException(status_code=400, detail="No stored credentials. Authenticate first (Browser Login or PAT Token).")

    username = creds.get("username", "")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.github.com/user/repos",
            json={
                "name": body.repo_name,
                "private": body.private,
                "description": body.description,
                "auto_init": False,
            },
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=15,
        )
    data = resp.json()
    if resp.status_code not in (200, 201):
        msg = data.get("message", str(resp.status_code))
        errors = "; ".join(e.get("message", "") for e in data.get("errors", []))
        raise HTTPException(status_code=400, detail=f"GitHub: {msg}" + (f" — {errors}" if errors else ""))

    clone_url = data["clone_url"]   # HTTPS URL
    html_url  = data["html_url"]
    actions: list[str] = [f"Created GitHub repo: {html_url}"]

    # Save URL to project.yaml
    proj_yaml_path = _proj_dir(body.project_name) / "project.yaml"
    try:
        proj_cfg = yaml.safe_load(proj_yaml_path.read_text()) if proj_yaml_path.exists() else {}
        proj_cfg["github_repo"] = clone_url
        proj_yaml_path.write_text(yaml.dump(proj_cfg, default_flow_style=False, allow_unicode=True))
    except Exception:
        pass

    # Init local repo and connect remote
    code_dir = _resolve_code_dir(body.project_name)
    if code_dir.exists():
        if not _is_git_repo(code_dir):
            _git(["init"], code_dir)
            actions.append("Initialized local git repository")

        actions.extend(_ensure_gitignore(code_dir))
        actions.extend(_untrack_secrets(code_dir))

        readme = code_dir / "README.md"
        if not readme.exists():
            display = body.repo_name.replace("_", " ").replace("-", " ").title()
            readme.write_text(f"# {display}\n\n{body.description or 'Project managed with aicli.'}\n")
            actions.append("Created README.md")

        authed_url = _build_authed_url(clone_url, username, token)
        rc, _, _ = _git(["remote", "get-url", "origin"], code_dir)
        if rc == 0:
            _git(["remote", "set-url", "origin", authed_url], code_dir)
        else:
            _git(["remote", "add", "origin", authed_url], code_dir)
        actions.append(f"Set remote origin → {clone_url}")

        if username:
            _git(["config", "user.name", username], code_dir)

        # Initial commit
        _git(["add", "-A"], code_dir)
        _, staged_out, _ = _git(["diff", "--name-only", "--cached"], code_dir)
        if staged_out.strip():
            _git(["commit", "-m", "init: initial commit"], code_dir)
            _, h, _ = _git(["rev-parse", "HEAD"], code_dir)
            actions.append(f"Initial commit ({len(staged_out.splitlines())} files): {h[:8] if h else ''}")

    return {"ok": True, "clone_url": clone_url, "html_url": html_url, "actions": actions}


# ── Test connection ────────────────────────────────────────────────────────────

@router.get("/{project_name}/test")
async def test_git_connection(project_name: str):
    """Test actual connectivity to the remote by running git ls-remote."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        return {"ok": False, "error": f"code_dir does not exist: {code_dir}"}
    if not _is_git_repo(code_dir):
        return {"ok": False, "error": "Not a git repository — run ⚙ Setup Git first"}

    rc, out, err = _git_authed(["ls-remote", "--heads", "origin"], code_dir, project_name)
    if rc != 0:
        return {"ok": False, "error": err or "Could not reach remote — check credentials and repo URL"}

    branches = []
    for line in out.splitlines():
        if "\t" in line:
            branches.append(line.split("\t")[1].strip().replace("refs/heads/", ""))

    _, raw_url, _ = _git(["remote", "get-url", "origin"], code_dir)
    # Strip embedded credentials from display URL
    display_url = raw_url
    if "@" in raw_url:
        try:
            proto, rest = raw_url.split("://", 1)
            display_url = f"{proto}://{rest.split('@', 1)[1]}"
        except Exception:
            pass

    return {"ok": True, "branches": branches, "remote_url": display_url}


# ── Commit & push ─────────────────────────────────────────────────────────────

class CommitRequest(BaseModel):
    message_hint: str = ""   # last user message / context for LLM
    provider: str = "claude"
    api_key: str = ""
    branch: str = ""         # optional push target; falls back to project.yaml git_branch → current branch
    skip_pull: bool = False  # set True to skip the pre-push pull step
    source: str = "aicli_backend"  # audit source: "aicli_backend" | "claude_cli" | "cursor_mcp" | "aicli_ui"
    session_id: str = ""     # Claude/aicli session UUID; used for prompt→commit linking


@router.post("/{project_name}/commit-push")
async def commit_and_push(project_name: str, body: CommitRequest, request: Request,
                          background: BackgroundTasks = None):
    """Stage changed files, generate commit message via LLM, commit and push."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Code directory not found: {code_dir}. Set the correct path in Settings → Project → Code directory."
        )

    if not _is_git_repo(code_dir):
        raise HTTPException(
            status_code=400,
            detail=f"Not a git repository: {code_dir}. Go to Settings → Project → Git and click 'Save & Setup Git'."
        )

    # Ensure .gitignore protects secrets and untrack any that slipped through
    _ensure_gitignore(code_dir)
    _untrack_secrets(code_dir)

    # Collect changed files
    _, staged, _    = _git(["diff", "--name-only", "--cached"], code_dir)
    _, unstaged, _  = _git(["diff", "--name-only"], code_dir)
    _, untracked, _ = _git(["ls-files", "--others", "--exclude-standard"], code_dir)
    changed = list(dict.fromkeys(
        f for f in (staged + "\n" + unstaged + "\n" + untracked).splitlines() if f
    ))

    if not changed:
        _write_commit_log(project_name, {
            "action": "skipped",
            "reason": "no_changes",
            "source": body.source,
        })
        return {"committed": False, "reason": "No changes to commit"}

    # Diff stat for commit message context
    _, diff_stat, _ = _git(["diff", "--stat"], code_dir)
    if not diff_stat:
        _, diff_stat, _ = _git(["diff", "--stat", "--cached"], code_dir)

    # Capture staged diff for structured commit analysis (capped for LLM token budget)
    _, staged_diff, _ = _git(["diff", "--cached"], code_dir)
    staged_diff = (staged_diff or "")[:8000]

    # Count meaningful diff lines (added + removed, excluding file headers)
    _diff_line_count = sum(
        1 for ln in staged_diff.splitlines()
        if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
    )

    # Read min_diff_lines from project.yaml (default 5)
    _min_diff_lines = 5
    try:
        _pcfg = yaml.safe_load((_proj_dir(project_name) / "project.yaml").read_text()) or {}
        _min_diff_lines = int(_pcfg.get("commit_code_extraction", {}).get("min_diff_lines", 5))
    except Exception:
        pass

    # Resolve API key: body field takes priority, then request header
    api_key = body.api_key or request.headers.get("X-Anthropic-Key") or None

    # Generate commit message (+ optional structured analysis)
    # Skip LLM for tiny commits (below min_diff_lines threshold)
    if _diff_line_count < _min_diff_lines:
        if body.message_hint:
            commit_message = body.message_hint[:72]
        elif len(changed) == 1:
            commit_message = f"chore: update {changed[0]}"
        else:
            commit_message = f"chore: update {len(changed)} files"
        commit_analysis = {}
        commit_summary = ""
        commit_type_val = _extract_commit_type(commit_message)
        log.debug(f"Skipping LLM commit analysis: diff_lines={_diff_line_count} < min={_min_diff_lines}")
    else:
        commit_message, commit_analysis = await _generate_commit_message(
            hint=body.message_hint,
            diff_stat=diff_stat,
            changed_files=changed,
            staged_diff=staged_diff,
            api_key=api_key,
        )
        commit_summary = commit_analysis.get("summary", "") if commit_analysis else ""
        commit_type_val = _extract_commit_type(commit_message)

    # Stage all changed files
    _git(["add", "--"] + changed, code_dir)

    # Commit
    rc, _, stderr = _git(["commit", "-m", commit_message], code_dir)
    if rc != 0:
        raise HTTPException(status_code=500, detail=f"Commit failed: {stderr}")

    _, commit_hash, _ = _git(["rev-parse", "HEAD"], code_dir)

    # Capture author info from the just-created commit
    commit_author = ""
    commit_author_email = ""
    try:
        _, author_info, _ = _git(["log", "--format=%an\t%ae", "-1", "HEAD"], code_dir)
        parts = author_info.split("\t", 1)
        commit_author = parts[0].strip() if parts else ""
        commit_author_email = parts[1].strip() if len(parts) > 1 else ""
    except Exception:
        pass

    # Determine push target: explicit > project.yaml git_branch > current local branch > "main"
    push_target = body.branch.strip()
    if not push_target:
        try:
            _proj_cfg = yaml.safe_load((_proj_dir(project_name) / "project.yaml").read_text()) or {}
            push_target = _proj_cfg.get("git_branch", "")
        except Exception:
            pass
    if not push_target:
        _, push_target, _ = _git(["branch", "--show-current"], code_dir)
    if not push_target:
        push_target = "main"

    # Pull (rebase) from remote to stay in sync before pushing
    pull_message = ""
    if not body.skip_pull:
        rc_pull, pull_out, pull_err = _git_authed(
            ["pull", "--rebase", "origin", push_target], code_dir, project_name
        )
        if rc_pull != 0:
            no_remote = any(x in pull_err.lower() for x in [
                "couldn't find remote ref", "does not appear to be a git repository",
                "no such ref", "unable to access",
            ])
            if no_remote:
                # First push — remote branch doesn't exist yet, skip pull
                pull_message = "first push (remote branch not yet created)"
            elif any(x in (pull_out + pull_err).lower() for x in ["conflict", "merge conflict"]):
                _git(["rebase", "--abort"], code_dir)
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Merge conflict during pull —  resolve conflicts manually "
                        f"(git pull + fix + git add + git rebase --continue), then push again.\n{pull_err[:300]}"
                    ),
                )
            else:
                # Non-fatal pull warning — still attempt push
                pull_message = f"pull warning: {pull_err[:120]}"
        else:
            first_line = (pull_out.strip().splitlines() or [""])[0]
            if first_line and "Already up to date" not in first_line:
                pull_message = f"pulled: {first_line[:100]}"

    # Always use --set-upstream so bare 'git pull' / 'git push' work in the future
    rc_push, _, stderr_push = _git_authed(
        ["push", "--set-upstream", "origin", push_target], code_dir, project_name
    )
    pushed = rc_push == 0

    if pushed:
        # Ensure local branch tracks the remote branch (idempotent)
        _ensure_upstream(push_target, code_dir)

    push_error = stderr_push if not pushed else ""
    _write_commit_log(project_name, {
        "action": "commit_push",
        "source": body.source,
        "session_id": body.session_id or "",
        "hash": commit_hash[:8] if commit_hash else "",
        "message": commit_message,
        "files_count": len(changed),
        "pushed": pushed,
        "push_error": push_error[:300] if push_error else "",
        "branch": push_target,
        "pull_message": pull_message,
    })

    # Immediately link this commit to its triggering prompt in the background
    if commit_hash and background is not None:
        # Filter generated/memory files from diff_summary so code stats are clean
        code_stat, _ = _filter_diff_stat(diff_stat or "")
        background.add_task(
            _sync_commit_and_link,
            project_name,
            commit_hash,        # full 40-char hash (not truncated)
            body.session_id or None,
            commit_message,
            datetime.now(timezone.utc).isoformat(),
            code_stat,          # only code file stats stored
            commit_author,
            commit_author_email,
            commit_summary,
            commit_type_val,
        )
        # Threshold-based commit batch check — queues embedding when batch_size reached
        background.add_task(_embed_commit_background, project_name, commit_hash)
        # Tree-sitter symbol extraction → mem_mrr_commits_code in background
        background.add_task(_extract_commit_code_background, project_name, commit_hash)
        # Backlog threshold check — process pending commits if threshold reached
        background.add_task(_check_backlog_threshold, project_name, "commits")

    return {
        "committed": True,
        "commit_hash": commit_hash[:8] if commit_hash else "",
        "commit_message": commit_message,
        "files": changed,
        "pull_message": pull_message,
        "pushed": pushed,
        "push_error": push_error,
    }


# ── Pull ─────────────────────────────────────────────────────────────────────

@router.post("/{project_name}/pull")
async def pull_from_remote(project_name: str):
    """Pull latest changes from remote (rebase strategy)."""
    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        return {"ok": False, "error": f"code_dir does not exist: {code_dir}"}
    if not _is_git_repo(code_dir):
        return {"ok": False, "error": "Not a git repository — run ⚙ Setup Git first"}

    _, current_branch, _ = _git(["branch", "--show-current"], code_dir)
    if not current_branch:
        current_branch = "main"

    # Set upstream tracking so bare 'git pull' works after this (idempotent, fails silently)
    _ensure_upstream(current_branch, code_dir)

    rc, out, err = _git_authed(
        ["pull", "--rebase", "origin", current_branch], code_dir, project_name
    )
    if rc != 0:
        combined = (out + "\n" + err).lower()
        if any(x in err.lower() for x in ["couldn't find remote ref", "does not appear to be", "no such ref"]):
            return {"ok": True, "pulled": False, "message": "No remote branch yet — push first to create it"}
        if "conflict" in combined or "merge conflict" in combined:
            _git(["rebase", "--abort"], code_dir)
            return {"ok": False, "error": "Merge conflict during pull. Use ↑ Push to force your local version to the remote, then pull again."}
        if any(x in combined for x in ["unstaged changes", "commit or stash", "cannot pull with rebase"]):
            _git(["rebase", "--abort"], code_dir)
            return {"ok": False, "error": "Cannot pull: you have uncommitted changes. Use ↑ Push to commit and upload them first, then pull."}
        if any(x in combined for x in ["diverged", "divergent", "non-fast-forward", "rejected"]):
            _git(["rebase", "--abort"], code_dir)
            return {"ok": False, "error": "Branches have diverged. Use ↑ Push (force) to replace remote with your local version, or resolve manually."}
        # Abort any in-progress rebase so the repo is not left in a broken state
        _git(["rebase", "--abort"], code_dir)
        error_line = next((l for l in (err or out).splitlines() if l.strip() and not l.startswith("hint:")), (err or out)[:200])
        return {"ok": False, "error": error_line.strip()[:300]}

    # Ensure tracking is set (first pull may have just created the remote ref)
    _ensure_upstream(current_branch, code_dir)

    lines = [l for l in out.strip().splitlines() if l.strip()]
    message = lines[0][:120] if lines else "Already up to date"
    return {"ok": True, "pulled": True, "message": message}


# ── Sync missing commits ───────────────────────────────────────────────────────

@router.post("/{project_name}/sync-commits")
async def sync_missing_commits(project_name: str, background: BackgroundTasks):
    """Ingest git commits not yet stored in mem_mrr_commits (external collaborators, imports).

    Walks git log from the last known commit to HEAD, stores each unknown commit
    as is_external=True, and queues tree-sitter extraction in the background.
    """
    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        raise HTTPException(status_code=404, detail=f"code_dir does not exist: {code_dir}")
    if not _is_git_repo(code_dir):
        raise HTTPException(status_code=400, detail="Not a git repository")

    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")

    project_id = db.get_or_create_project_id(project_name)

    # Find last stored commit
    last_hash: str | None = None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT commit_hash FROM mem_mrr_commits "
                    "WHERE project_id=%s ORDER BY created_at DESC LIMIT 1",
                    (project_id,),
                )
                row = cur.fetchone()
                last_hash = row[0] if row else None
    except Exception as e:
        log.warning(f"sync-commits: failed to get last hash: {e}")

    # Build git log range
    log_range = f"{last_hash}..HEAD" if last_hash else "HEAD"
    rc, raw_log, err = _git(
        ["log", log_range, "--format=%H\t%s\t%an\t%ae\t%aI", "--reverse"],
        code_dir,
    )
    if rc != 0:
        return {"synced": 0, "skipped": 0, "already_known": 0, "latest_hash": None, "error": err[:200]}

    lines = [l for l in raw_log.splitlines() if l.strip()][:200]
    synced = 0
    skipped = 0
    already_known = 0
    latest_hash: str | None = None

    for line in lines:
        parts = line.split("\t", 4)
        if len(parts) < 2:
            continue
        chash = parts[0].strip()
        commit_msg = parts[1].strip() if len(parts) > 1 else ""
        author = parts[2].strip() if len(parts) > 2 else ""
        author_email = parts[3].strip() if len(parts) > 3 else ""
        committed_at = parts[4].strip() if len(parts) > 4 else ""

        # Skip if already stored
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM mem_mrr_commits WHERE commit_hash=%s", (chash,)
                    )
                    if cur.fetchone():
                        already_known += 1
                        latest_hash = chash
                        continue
        except Exception:
            skipped += 1
            continue

        # Get diff stat for this commit (code files only)
        _, diff_raw, _ = _git(["show", "--stat", "--format=", chash], code_dir)
        code_stat, _ = _filter_diff_stat(diff_raw or "")

        ctype = _extract_commit_type(commit_msg)
        _sync_commit_and_link(
            project_name, chash, None, commit_msg, committed_at or "",
            code_stat, author, author_email,
            summary="", commit_type=ctype, is_external=True,
        )
        background.add_task(_extract_commit_code_background, project_name, chash)
        synced += 1
        latest_hash = chash

    return {
        "synced":       synced,
        "skipped":      skipped,
        "already_known": already_known,
        "latest_hash":  latest_hash,
    }


# ── Push-all (force sync local → remote) ─────────────────────────────────────

@router.post("/{project_name}/push-all")
async def push_all(project_name: str):
    """Force-sync local files to remote using an orphan branch.

    Uses an orphan branch (no parent commits) so the entire git history is
    replaced with a single clean commit.  This is the only reliable way to
    purge secrets that were committed in previous commits — GitHub's secret
    scanning inspects every commit being pushed, not just the latest tree.

    Safe: local files are never deleted.  The remote history is replaced.
    """
    import datetime

    proj_dir = _proj_dir(project_name)
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    code_dir = _resolve_code_dir(project_name)
    if not code_dir.exists():
        return {"ok": False, "error": f"code_dir does not exist: {code_dir}"}
    if not _is_git_repo(code_dir):
        return {"ok": False, "error": "Not a git repository — run ⚙ Setup Git first"}

    # Determine push target
    try:
        _proj_cfg = yaml.safe_load((_proj_dir(project_name) / "project.yaml").read_text()) or {}
        push_target = _proj_cfg.get("git_branch", "")
    except Exception:
        push_target = ""
    if not push_target:
        _, push_target, _ = _git(["branch", "--show-current"], code_dir)
    if not push_target:
        push_target = "main"

    # Abort any in-progress rebase/merge so we start clean
    _git(["rebase", "--abort"], code_dir)
    _git(["merge", "--abort"], code_dir)

    # Ensure .gitignore is comprehensive BEFORE staging anything
    _ensure_gitignore(code_dir)

    # ── Orphan branch approach ─────────────────────────────────────────────────
    # Create a branch with NO parent commits.  This means no git history is
    # pushed — only the current snapshot.  GitHub secret scanning only inspects
    # commits in the push, so a single fresh commit with no secrets passes.
    TEMP = "_aicli_push_clean"

    # Clean up temp branch from a previous failed attempt
    _git(["branch", "-D", TEMP], code_dir)   # ignore error if doesn't exist

    rc_orphan, _, orphan_err = _git(["checkout", "--orphan", TEMP], code_dir)
    if rc_orphan != 0:
        return {"ok": False, "error": f"Could not create clean branch: {orphan_err[:200]}"}

    try:
        # Stage everything (respects the freshly-written .gitignore)
        _git(["add", "-A"], code_dir)

        # Count what's staged
        _, status_out, _ = _git(["status", "--porcelain"], code_dir)
        staged_count = len([l for l in status_out.splitlines() if l.strip()])

        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        commit_message = f"chore: clean push — {staged_count} file(s) — {ts}"

        rc_c, _, commit_err = _git(["commit", "-m", commit_message], code_dir)
        if rc_c != 0:
            # Nothing to commit (unlikely but handle gracefully)
            if "nothing to commit" in commit_err.lower():
                commit_message = "(working tree clean — nothing to commit)"
            else:
                # Restore original branch before bailing
                _git(["checkout", push_target], code_dir)
                _git(["branch", "-D", TEMP], code_dir)
                return {"ok": False, "error": f"Commit failed: {commit_err[:200]}"}

        # Replace the target branch with the orphan commit
        # (delete old branch, rename orphan to it)
        _git(["branch", "-D", push_target], code_dir)
        _git(["branch", "-m", push_target], code_dir)

        # Force-push — the orphan has no shared history so --force is required
        rc_push, _, stderr_push = _git_authed(
            ["push", "--force", "--set-upstream", "origin", push_target],
            code_dir,
            project_name,
        )
        pushed = rc_push == 0

        if pushed:
            _ensure_upstream(push_target, code_dir)

        return {
            "ok": pushed,
            "commit_message": commit_message,
            "staged_count": staged_count,
            "pushed": pushed,
            "push_error": stderr_push if not pushed else "",
        }

    except Exception as exc:
        # Emergency restore: switch back to original branch
        _git(["checkout", push_target], code_dir)
        _git(["branch", "-D", TEMP], code_dir)
        raise HTTPException(status_code=500, detail=str(exc))


async def _generate_commit_message(
    hint: str, diff_stat: str, changed_files: list[str],
    staged_diff: str = "", api_key: str | None = None
) -> tuple[str, dict]:
    """Ask Claude to write a commit message and extract structured analysis from the diff.

    Returns (commit_message, analysis_dict).
    Falls back to a simple chore message with empty analysis on failure.
    """
    sys_prompt = _prompts.content("commit_analysis") or ""

    _CONVENTIONAL = ("feat", "fix", "chore", "test", "refactor", "docs", "style", "perf", "ci", "build")

    # Try structured JSON extraction when we have a diff and a system prompt
    if sys_prompt and staged_diff:
        user_msg_parts = [f"Changed files: {', '.join(changed_files[:15])}"]
        if hint:
            user_msg_parts.append(f"Developer context: {hint[:200]}")
        user_msg_parts.append(f"Diff:\n{staged_diff[:8000]}")

        try:
            import re as _re
            result = await call_claude(
                messages=[{"role": "user", "content": "\n\n".join(user_msg_parts)}],
                system=sys_prompt,
                api_key=api_key,
            )
            raw = result.get("content", "").strip()
            cleaned = _re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
            parsed = json.loads(cleaned)
            msg = (parsed.get("message") or "").strip().split("\n")[0].strip('"\'')
            # Validate conventional prefix
            if msg and any(msg.startswith(p + ":") or msg.startswith(p + "(") for p in _CONVENTIONAL):
                analysis = {k: v for k, v in parsed.items() if k != "message"}
                return msg[:72], analysis
        except Exception:
            pass

    # Fallback: simple single-line message without structured analysis
    context_parts = [f"Changed files: {', '.join(changed_files[:15])}"]
    if diff_stat:
        context_parts.append(f"Diff summary:\n{diff_stat[:600]}")
    if hint:
        context_parts.append(f"Developer context: {hint[:200]}")

    prompt = (
        "Write a single-line git commit message (under 72 characters) for these changes.\n"
        "Format: <type>: <description>   (e.g. feat: add login, fix: resolve auth bug)\n"
        "Reply with ONLY the commit message, no quotes or explanation.\n\n"
        + "\n\n".join(context_parts)
    )
    _commit_system = (
        _prompts.content("commit_message")
        or "You write short, professional git commit messages."
    )
    try:
        result = await call_claude(
            messages=[{"role": "user", "content": prompt}],
            system=_commit_system,
            api_key=api_key,
        )
        msg = result.get("content", "").strip().split("\n")[0].strip('"\'')
        if msg and len(msg) > 5:
            return msg[:72], {}
    except Exception:
        pass

    # Last resort fallback — no LLM available
    if len(changed_files) == 1:
        return f"chore: update {changed_files[0]}", {}
    return f"chore: update {len(changed_files)} files", {}
