"""
graph_runner.py — LangGraph-based execution engine for multi-LLM workflow DAGs.

Replaces the custom async work-queue runner with LangGraph StateGraph.
Every node is wrapped in an async LangGraph node function; conditional edges
use LangGraph's add_conditional_edges; MemorySaver enables pause/resume for
approval gates.

Stateless nodes receive only {user_input} as context (no accumulated history).
Stateful nodes receive the full accumulated context dict.

Public API:
    run_graph_workflow(workflow_id, user_input, run_id, project, work_item_id) -> dict
    resume_graph_workflow(run_id, workflow_id, project, ctx, start_node_ids,
                          approved, retry, reason) -> dict
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

from core.config import settings
from core.database import db, build_update

log = logging.getLogger(__name__)

# ── LangGraph imports (optional — falls back to legacy runner if not installed) ─

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    _LANGGRAPH_AVAILABLE = True
except ImportError:
    _LANGGRAPH_AVAILABLE = False
    log.warning("langgraph not installed — graph_runner will use legacy DAG mode")


# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_INSERT_NODE_RESULT = """
    INSERT INTO pr_graph_node_results
        (run_id, node_id, node_name, status, iteration)
    VALUES (%s, %s, %s, 'running', %s)
    RETURNING id
"""

# _SQL_UPDATE_NODE_RESULT — dynamic fields built via build_update(); WHERE clause:
_SQL_UPDATE_NODE_RESULT_WHERE = (
    "UPDATE pr_graph_node_results SET {set_clause}, finished_at=NOW() WHERE id=%s"
)


_SQL_UPSERT_SESSION_TAG = """
    INSERT INTO mng_session_tags (client_id, session_id, phase, feature, bug_ref)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (client_id, session_id)
    DO UPDATE SET phase = EXCLUDED.phase,
                  feature = EXCLUDED.feature,
                  bug_ref = EXCLUDED.bug_ref
"""

_SQL_GET_WORKFLOW = (
    "SELECT id, project, name, max_iterations, log_directory "
    "FROM pr_graph_workflows WHERE id=%s"
)

_SQL_GET_NODES = """
    SELECT n.id, n.name, n.role_file, n.role_prompt, n.provider, n.model,
           n.output_schema, n.inject_context, n.require_approval, n.approval_msg,
           n.role_id, n.stateless, n.retry_config, n.success_criteria,
           n.order_index, n.max_retry, n.continue_on_fail,
           COALESCE(n.auto_commit, ar.auto_commit, FALSE) AS auto_commit,
           COALESCE(NULLIF(n.role_prompt, ''), ar.system_prompt, '') AS effective_prompt,
           COALESCE(NULLIF(n.provider, ''), ar.provider, '') AS effective_provider,
           COALESCE(NULLIF(n.model, ''), ar.model, '') AS effective_model
    FROM   pr_graph_nodes n
    LEFT JOIN mng_agent_roles ar ON ar.id = n.role_id
    WHERE  n.workflow_id=%s
    ORDER  BY n.order_index, n.created_at
"""

_SQL_GET_EDGES = (
    "SELECT id, source_node_id, target_node_id, condition, label "
    "FROM pr_graph_edges WHERE workflow_id=%s"
)

# Terminal run update (done / stopped / error) — includes finished_at and error
_SQL_UPDATE_RUN_STATUS = """
    UPDATE pr_graph_runs
       SET status=%s, context=%s, total_cost_usd=%s,
           finished_at=NOW(), error=%s, current_node=NULL
     WHERE id=%s
"""

# Non-terminal run update (running / waiting_approval) — no finished_at
_SQL_UPDATE_RUN_PROGRESS = (
    "UPDATE pr_graph_runs SET status=%s, context=%s, total_cost_usd=%s WHERE id=%s"
)

_SQL_UPDATE_RUN_CURRENT_NODE = (
    "UPDATE pr_graph_runs SET current_node=%s WHERE id=%s"
)

_SQL_GET_WORK_ITEM_NAME = (
    "SELECT category_name, name FROM mem_ai_work_items WHERE id=%s::uuid"
)

_SQL_GET_RUN_RESUME = (
    "SELECT workflow_id, context, total_cost_usd FROM pr_graph_runs WHERE id=%s"
)

# ── Condition evaluation ───────────────────────────────────────────────────────

def _eval_condition(condition: dict | None, ctx: dict) -> bool:
    """Evaluate an edge condition against the current context.

    Condition schema: {"field": "score", "op": "gte", "value": 8}
    Supported ops: eq, neq, gte, gt, lt, lte, contains
    Returns True when condition is None (always traverse).
    """
    if not condition:
        return True
    field = condition.get("field", "")
    op = condition.get("op", "eq")
    value = condition.get("value")

    # Resolve field from context (search all node outputs)
    actual = None
    for node_output in ctx.values():
        if isinstance(node_output, dict) and field in node_output:
            actual = node_output[field]
            break
    if actual is None:
        return False

    try:
        if op == "eq":       return actual == value
        if op == "neq":      return actual != value
        if op == "gte":      return float(actual) >= float(value)
        if op == "gt":       return float(actual) > float(value)
        if op == "lt":       return float(actual) < float(value)
        if op == "lte":      return float(actual) <= float(value)
        if op == "contains": return str(value) in str(actual)
    except (TypeError, ValueError):
        return False
    return False


# ── Node execution ────────────────────────────────────────────────────────────

async def _execute_node(node: dict, run_id: str, ctx: dict, iteration: int, project: str) -> dict:
    """Execute a single graph node and persist its result.

    Returns: {"node_id": str, "node_name": str, "output": str,
              "structured": dict|None, "cost_usd": float,
              "input_tokens": int, "output_tokens": int, "status": str}
    """
    from data.dl_api_keys import get_key
    from agents.providers import call_claude, call_deepseek, call_gemini, call_grok
    from agents.providers.pr_costs import estimate_cost

    node_id = node["id"]
    node_name = node["name"]
    provider = node.get("provider", "claude")
    model = node.get("model", "") or None
    role_file = node.get("role_file")
    role_prompt = node.get("role_prompt", "")
    inject_context = node.get("inject_context", True)
    output_schema = node.get("output_schema")

    # Build system prompt — precedence: inline > role_file > pre-loaded from _load_workflow_from_db
    # NOTE: _load_workflow_from_db already JOINs mng_agent_roles and returns the effective prompt in
    # node["role_prompt"], so we skip the redundant DB queries that were here before.
    if role_file and not role_prompt:
        role_path = Path(settings.workspace_dir) / project / "prompts" / role_file
        if role_path.exists():
            role_prompt = role_path.read_text()
        else:
            log.warning(f"role_file not found: {role_path}")

    # Build user message — cap each prior node's output at 3000 chars to prevent
    # unbounded context growth as the pipeline advances.
    _CTX_CAP = 3000
    user_parts = []
    if inject_context and ctx:
        ctx_str = "\n\n".join(
            f"=== {k} output ===\n"
            + (v[:_CTX_CAP] + "\n[...truncated]" if isinstance(v, str) and len(v) > _CTX_CAP
               else (v if isinstance(v, str) else json.dumps(v)[:_CTX_CAP]))
            for k, v in ctx.items()
            if not k.startswith("_")   # skip internal keys like _work_item
        )
        if ctx_str:
            user_parts.append(f"<context>\n{ctx_str}\n</context>")

    # Add output schema instruction
    if output_schema:
        fields = output_schema.get("fields", [])
        user_parts.append(
            f"\nRespond with valid JSON only. Required fields: {', '.join(fields)}."
        )

    user_parts.append(f"\n<task>\nIteration {iteration + 1}. Proceed.\n</task>")
    user_msg = "\n".join(user_parts)

    result_id = None
    # Insert running record
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_NODE_RESULT,
                        (run_id, node_id, node_name, iteration),
                    )
                    result_id = cur.fetchone()[0]
        except Exception as e:
            log.warning(f"Could not insert node result record: {e}")

    api_key = get_key(provider)
    output = ""
    input_tokens = output_tokens = 0
    status = "done"
    structured = None

    try:
        messages = [{"role": "user", "content": user_msg}]

        if provider == "claude":
            resp = await call_claude(messages, system=role_prompt, model=model, api_key=api_key)
        elif provider == "openai":
            from agents.providers.pr_openai import _async_client as _async_openai_client
            client = _async_openai_client(api_key)
            full_msgs = []
            if role_prompt:
                full_msgs.append({"role": "system", "content": role_prompt})
            full_msgs.extend(messages)
            raw = await client.chat.completions.create(
                model=model or settings.openai_model,
                messages=full_msgs,
                max_tokens=4096,
            )
            resp = {
                "content": raw.choices[0].message.content or "",
                "input_tokens": raw.usage.prompt_tokens if raw.usage else 0,
                "output_tokens": raw.usage.completion_tokens if raw.usage else 0,
            }
        elif provider == "deepseek":
            resp = await call_deepseek(messages, system=role_prompt, api_key=api_key)
        elif provider == "gemini":
            resp = await call_gemini(user_msg, system=role_prompt, model=model, api_key=api_key)
        elif provider == "grok":
            resp = await call_grok(messages, system=role_prompt, api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        output = resp.get("content", "")
        input_tokens = resp.get("input_tokens", 0)
        output_tokens = resp.get("output_tokens", 0)

        # Note: work-item output is saved only on user approval (not on every run).
        # See save_approved_output() called from make_run_decision endpoint.

        # Parse structured output if schema requested
        if output_schema:
            try:
                json_match = re.search(r"\{.*\}", output, re.DOTALL)
                if json_match:
                    structured = json.loads(json_match.group())
            except (json.JSONDecodeError, AttributeError):
                pass

    except Exception as e:
        log.error(f"Node {node_name} execution failed: {e}")
        output = f"Error: {e}"
        status = "error"

    # Estimate cost
    cost_usd = 0.0
    try:
        cost_usd = estimate_cost(provider, model or provider, input_tokens, output_tokens)
    except Exception:
        pass

    # Update DB record
    if db.is_available() and result_id is not None:
        try:
            set_clause, vals = build_update({
                "status": status,
                "output": output,
                "structured": json.dumps(structured) if structured else None,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
            })
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_UPDATE_NODE_RESULT_WHERE.format(set_clause=set_clause),
                        vals + [result_id],
                    )
        except Exception as e:
            log.warning(f"Could not update node result: {e}")

    return {
        "node_id": node_id,
        "node_name": node_name,
        "output": output,
        "structured": structured,
        "cost_usd": cost_usd,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "status": status,
    }


# ── Document output saver ─────────────────────────────────────────────────────

def _save_node_output(project: str, pipeline_name: str, run_id: str, node_name: str, output: str) -> None:
    """Auto-save a node's text output to documents/pipelines/{pipeline}/{run_prefix}/{node}.md."""
    safe_pipeline = re.sub(r"[^a-z0-9_-]", "_", pipeline_name.lower().replace(" ", "_"))[:40]
    safe_node = re.sub(r"[^a-z0-9_]", "_", node_name.lower().replace(" ", "_"))[:40]
    run_prefix = run_id[:8]
    rel = f"pipelines/{safe_pipeline}/{run_prefix}/{safe_node}.md"
    dest = Path(settings.workspace_dir) / project / "documents" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"# {node_name}\n\n{output}\n")
    log.info(f"Saved node output → documents/{rel}")


def save_approved_output(project: str, work_item: dict, node_name: str, output: str) -> None:
    """Save an *approved* node output with versioning.

    Latest version is at: documents/{category}/{slug}/{node}.md
    Previous versions (and any old timestamped files) are in: documents/{category}/{slug}/old/

    Call this ONLY when the user clicks Approve (not on every node run).
    """
    safe_name = re.sub(r"[^a-z0-9_]", "", node_name.lower().replace(" ", "_"))[:50]
    slug = work_item.get("slug", "unknown")
    category = work_item.get("category", "feature")
    dest_dir = Path(settings.workspace_dir) / project / "documents" / category / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    old_dir = dest_dir / "old"
    ts = datetime.now(timezone.utc).strftime("%y%m%d_%H%M%S")

    # Move any existing timestamped files (from old runs) to old/
    for stale in dest_dir.glob(f"{safe_name}_*.md"):
        old_dir.mkdir(exist_ok=True)
        stale.rename(old_dir / stale.name)

    # Move current clean file to old/ before overwriting
    dest = dest_dir / f"{safe_name}.md"
    if dest.exists():
        old_dir.mkdir(exist_ok=True)
        dest.rename(old_dir / f"{safe_name}_{ts}.md")

    dest.write_text(f"# {node_name}\n\n{output}\n")
    log.info(f"Saved approved output → documents/{category}/{slug}/{safe_name}.md")


# ── Developer: code file extraction + git commit ───────────────────────────────

def _parse_code_changes(output: str) -> list[tuple[str, str]]:
    """Extract (file_path, content) pairs from LLM output.

    Recognized patterns:
      ### File: path/to/file.ext
      ```lang
      content
      ```
    Also handles:
      ## path/to/file.ext
      ```lang
      content
      ```
    """
    changes: list[tuple[str, str]] = []
    pattern = r'(?:###?\s+(?:File:\s*)?|##\s+)([^\n`]+?)\s*\n```(?:\w+)?\n(.*?)```'
    _EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.java', '.rs',
                   '.rb', '.md', '.yaml', '.yml', '.json', '.toml', '.sh',
                   '.css', '.html', '.sql', '.txt', '.env', '.cfg', '.ini')
    for m in re.finditer(pattern, output, re.DOTALL):
        path = m.group(1).strip().rstrip(':')
        content = m.group(2)
        # Only accept real file paths (must have extension or contain /)
        if any(path.lower().endswith(ext) for ext in _EXTENSIONS) or '/' in path:
            # Skip overly long "paths" (likely markdown headings)
            if len(path) <= 200 and '\n' not in path:
                changes.append((path, content))
    return changes


def _apply_code_and_commit(code_dir: str, changes: list[tuple[str, str]],
                           node_name: str, run_id: str) -> str:
    """Write file changes to code_dir and run git add/commit/push.

    Returns the short commit hash on success, '' if nothing to commit, or an error string.
    """
    import subprocess
    base = Path(code_dir).resolve()

    wrote = 0
    for rel_path, content in changes:
        dest = (base / rel_path.lstrip("/")).resolve()
        # Security: prevent path traversal
        if not str(dest).startswith(str(base)):
            log.warning(f"auto_commit: skipping traversal path {rel_path!r}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        log.info(f"auto_commit: wrote {rel_path}")
        wrote += 1

    if not wrote:
        log.info("auto_commit: no files written — skipping commit")
        return ""

    try:
        subprocess.run(["git", "add", "."], cwd=code_dir, check=True, capture_output=True)
        msg = f"auto: {node_name} [{run_id[:8]}]"
        subprocess.run(["git", "commit", "-m", msg], cwd=code_dir,
                       check=True, capture_output=True, text=True)
        hash_r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                cwd=code_dir, capture_output=True, text=True)
        commit_hash = hash_r.stdout.strip()
        # Push in background — don't block or fail if remote unreachable
        subprocess.Popen(["git", "push"], cwd=code_dir,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info(f"auto_commit: committed {commit_hash} for node '{node_name}'")
        return commit_hash
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
        if "nothing to commit" in stderr or "nothing added" in stderr:
            return ""
        log.warning(f"auto_commit git error: {stderr[:200]}")
        return f"error: {stderr[:100]}"


def _get_project_code_dir(project: str) -> str:
    """Get code directory for a project (project.yaml → code_dir, else settings.code_dir)."""
    try:
        import yaml
        proj_yaml = Path(settings.workspace_dir) / project / "project.yaml"
        if proj_yaml.exists():
            cfg = yaml.safe_load(proj_yaml.read_text()) or {}
            if cfg.get("code_dir"):
                return str(cfg["code_dir"])
    except Exception:
        pass
    return settings.code_dir


# ── LangGraph state type ───────────────────────────────────────────────────────

class WorkflowState(TypedDict):
    user_input: str
    context: dict          # {node_name: output}
    messages: list         # accumulated history for stateful nodes
    run_id: str
    project: str
    total_cost: float
    _work_item: Any        # work item dict or None


# ── In-memory registry of compiled LangGraph apps ─────────────────────────────
# run_id → (app, checkpointer)
_APP_REGISTRY: dict[str, tuple] = {}


def _make_node_fn(node: dict, run_id: str, project: str, log_dir: str = "", pipeline_name: str = ""):
    """Return an async LangGraph node function from a DB node dict.

    Applies per-node retry (max_retry) and continue_on_fail semantics.
    If auto_commit=True, parses code file changes from output and git commits them.
    If log_dir is set, appends node output to the run log file.
    Every node's output is auto-saved to documents/pipelines/{pipeline_name}/...
    """
    node_copy = dict(node)
    max_retry = int(node_copy.get("max_retry", 3))
    continue_on_fail = bool(node_copy.get("continue_on_fail", False))
    do_auto_commit = bool(node_copy.get("auto_commit", False))

    async def fn(state: WorkflowState) -> dict:
        # Mark this node as the currently running one in the run record
        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            _SQL_UPDATE_RUN_CURRENT_NODE,
                            (node_copy["name"], run_id),
                        )
            except Exception as _ce:
                log.debug(f"Could not update current_node: {_ce}")

        # Stateless: only pass user_input (no accumulated prior outputs)
        if node_copy.get("stateless"):
            effective_ctx: dict = {"user_input": state["user_input"]}
        else:
            effective_ctx = dict(state["context"])
        effective_ctx["_work_item"] = state.get("_work_item")

        # Per-node retry loop
        last_result: dict = {}
        for attempt in range(max(1, max_retry)):
            last_result = await _execute_node(node_copy, run_id, effective_ctx, attempt, project)
            if last_result.get("status") != "error":
                break
            if attempt < max_retry - 1:
                log.warning(f"Node '{node_copy['name']}' attempt {attempt+1} failed — retrying")
            else:
                if not continue_on_fail:
                    # Propagate error; LangGraph will surface it
                    log.error(f"Node '{node_copy['name']}' failed after {max_retry} attempts")

        output = last_result.get("structured") or last_result.get("output", "")
        new_ctx = {**state["context"], node_copy["name"]: output}

        # Developer auto-commit: parse code blocks from output and git commit
        if do_auto_commit and output and last_result.get("status") != "error" and isinstance(output, str):
            try:
                code_dir = _get_project_code_dir(project)
                changes = _parse_code_changes(output)
                if changes:
                    commit_hash = _apply_code_and_commit(code_dir, changes, node_copy["name"], run_id)
                    if commit_hash and not commit_hash.startswith("error:"):
                        # Store commit hash in context so downstream nodes and UI can see it
                        new_ctx[f"{node_copy['name']}_commit"] = commit_hash
                        log.info(f"Node '{node_copy['name']}' auto-committed: {commit_hash}")
                    elif commit_hash.startswith("error:"):
                        log.warning(f"Node '{node_copy['name']}' auto-commit failed: {commit_hash}")
                else:
                    log.info(f"Node '{node_copy['name']}': auto_commit=True but no code blocks found in output")
            except Exception as _ace:
                log.warning(f"auto_commit exception for '{node_copy['name']}': {_ace}")

        # Auto-save to documents/pipelines/... for every successful node
        if pipeline_name and output and last_result.get("status") != "error":
            try:
                _save_node_output(
                    project, pipeline_name, run_id,
                    node_copy["name"],
                    output if isinstance(output, str) else json.dumps(output),
                )
            except Exception as _ds:
                log.warning(f"Could not auto-save node output: {_ds}")

        # Append to run log file if log_dir is configured
        if log_dir:
            try:
                log_path = Path(log_dir)
                log_path.mkdir(parents=True, exist_ok=True)
                with (log_path / f"{run_id}.log").open("a") as _lf:
                    _lf.write(f"\n## {node_copy['name']}\n{output}\n")
            except Exception as _le:
                log.warning(f"Could not write run log: {_le}")

        if node_copy.get("stateless"):
            new_msgs: list = []
        else:
            new_msgs = list(state.get("messages", [])) + [
                {"role": "assistant", "content": str(output)}
            ]

        return {
            **state,
            "context": new_ctx,
            "messages": new_msgs,
            "total_cost": state.get("total_cost", 0.0) + last_result.get("cost_usd", 0.0),
        }

    fn.__name__ = re.sub(r"[^a-z0-9_]", "_", node_copy["name"].lower().replace(" ", "_"))
    return fn


def _make_router(out_edges: list, nodes: dict):
    """Return a router function that maps state → next node name (or END)."""
    def router(state: WorkflowState) -> str:
        for e in out_edges:
            condition = e.get("condition")
            if not condition or _eval_condition(condition, state["context"]):
                tgt = nodes.get(e["target"])
                return tgt["name"] if tgt else END
        return END
    return router


def _build_langgraph(
    nodes: dict[str, dict],
    edges: list[dict],
    run_id: str,
    project: str,
    log_dir: str = "",
    pipeline_name: str = "",
) -> tuple:
    """Construct, compile, and return (app, approval_node_names, checkpointer).

    nodes: {node_id: node_dict}
    edges: list of {id, source, target, condition, label}
    """
    builder: StateGraph = StateGraph(WorkflowState)  # type: ignore[type-arg]

    edges_by_src: dict[str, list] = defaultdict(list)
    for e in edges:
        edges_by_src[e["source"]].append(e)

    # Forward in-degree (for entry-point detection)
    fwd_in_degree: dict[str, int] = {nid: 0 for nid in nodes}
    for e in edges:
        if e["source"] in nodes and e["target"] in nodes:
            fwd_in_degree[e["target"]] += 1

    approval_names: list[str] = []

    for nid, node in nodes.items():
        builder.add_node(node["name"], _make_node_fn(node, run_id, project, log_dir=log_dir, pipeline_name=pipeline_name))
        if node.get("require_approval"):
            approval_names.append(node["name"])

    entry_nodes = [n["name"] for nid, n in nodes.items() if fwd_in_degree[nid] == 0]
    if entry_nodes:
        builder.set_entry_point(entry_nodes[0])

    for nid, node in nodes.items():
        out = edges_by_src.get(nid, [])
        if not out:
            builder.add_edge(node["name"], END)
        elif len(out) == 1 and not out[0].get("condition"):
            tgt = nodes.get(out[0]["target"])
            builder.add_edge(node["name"], tgt["name"] if tgt else END)
        else:
            router = _make_router(out, nodes)
            targets: dict[str, str] = {}
            for e in out:
                tgt = nodes.get(e["target"])
                if tgt:
                    targets[tgt["name"]] = tgt["name"]
            targets[END] = END
            builder.add_conditional_edges(node["name"], router, targets)

    cp = MemorySaver()
    interrupt_after = approval_names if approval_names else None
    app = builder.compile(
        checkpointer=cp,
        interrupt_after=interrupt_after,  # type: ignore[arg-type]
    )
    return app, approval_names, cp


def _load_workflow_from_db(workflow_id: str) -> tuple[dict, dict[str, dict], list[dict]]:
    """Load workflow, nodes (id→dict), edges from DB."""
    workflow: dict = {}
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_WORKFLOW, (workflow_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Workflow not found: {workflow_id}")
            workflow = {
                "id": row[0], "project": row[1], "name": row[2],
                "max_iterations": row[3], "log_directory": row[4] if len(row) > 4 else "",
            }

            cur.execute(_SQL_GET_NODES, (workflow_id,))
            for r in cur.fetchall():
                nodes[r[0]] = {
                    "id": r[0], "name": r[1], "role_file": r[2],
                    "role_prompt": r[18],           # effective_prompt (node or role)
                    "provider": r[19],              # effective_provider
                    "model": r[20],                 # effective_model
                    "output_schema": r[6], "inject_context": r[7],
                    "require_approval": r[8] if len(r) > 8 else False,
                    "approval_msg": r[9] if len(r) > 9 else "",
                    "role_id": r[10] if len(r) > 10 else None,
                    "stateless": r[11] if len(r) > 11 else False,
                    "retry_config": r[12] if len(r) > 12 else {},
                    "success_criteria": r[13] if len(r) > 13 else "",
                    "order_index": r[14] if len(r) > 14 else 0,
                    "max_retry": r[15] if len(r) > 15 else 3,
                    "continue_on_fail": r[16] if len(r) > 16 else False,
                    "auto_commit": r[17] if len(r) > 17 else False,
                }

            cur.execute(_SQL_GET_EDGES, (workflow_id,))
            for r in cur.fetchall():
                edges.append({
                    "id": r[0], "source": r[1], "target": r[2],
                    "condition": r[3], "label": r[4],
                })

    return workflow, nodes, edges


def _update_run_db(run_id: str, status: str, ctx: dict | None = None,
                   total_cost: float = 0.0, error: str | None = None) -> None:
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                if status in ("done", "stopped", "error"):
                    cur.execute(
                        _SQL_UPDATE_RUN_STATUS,
                        (status, json.dumps(ctx or {}), total_cost, error, run_id),
                    )
                else:
                    cur.execute(
                        _SQL_UPDATE_RUN_PROGRESS,
                        (status, json.dumps(ctx or {}), total_cost, run_id),
                    )
    except Exception as e:
        log.warning(f"Could not update run {run_id} status={status}: {e}")


# ── LangGraph-based main runner ────────────────────────────────────────────────

async def run_graph_workflow(
    workflow_id: str,
    user_input: str,
    run_id: str,
    project: str,
    work_item_id: str | None = None,
) -> dict:
    """Build a LangGraph StateGraph from DB workflow and run it asynchronously.

    Falls back to legacy DAG runner if langgraph is not installed.
    Returns the final context dict {node_name: output_or_structured}.
    """
    if not db.is_available():
        raise RuntimeError("PostgreSQL required for graph workflows")

    if not _LANGGRAPH_AVAILABLE:
        return await _run_graph_workflow_legacy(
            workflow_id, user_input, run_id, project, work_item_id=work_item_id
        )

    # 1. Load workflow, nodes, edges
    workflow, nodes, edges = _load_workflow_from_db(workflow_id)

    # 2. Load work item if provided
    work_item: dict | None = None
    if work_item_id and db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WORK_ITEM_NAME, (work_item_id,))
                    wi = cur.fetchone()
            if wi:
                slug = re.sub(r"[^a-z0-9_]", "", wi[1].lower().replace(" ", "_"))
                work_item = {"id": work_item_id, "category": wi[0], "name": wi[1], "slug": slug}
        except Exception as _we:
            log.warning(f"Could not load work_item {work_item_id}: {_we}")

    # 3. Build LangGraph (resolve log_dir from workflow config or workspace default)
    log_dir = workflow.get("log_directory", "")
    if not log_dir and project:
        log_dir = str(Path(settings.workspace_dir) / project / "pipeline_logs")
    app, approval_names, cp = _build_langgraph(nodes, edges, run_id, project, log_dir=log_dir, pipeline_name=workflow.get("name", ""))
    _APP_REGISTRY[run_id] = (app, cp)

    # 4. Build initial state
    initial_state: WorkflowState = {
        "user_input": user_input,
        "context": {"user_input": user_input},
        "messages": [],
        "run_id": run_id,
        "project": project,
        "total_cost": 0.0,
        "_work_item": work_item,
    }

    config = {"configurable": {"thread_id": run_id}}

    # 5. Run
    try:
        final_state = await app.ainvoke(initial_state, config)
    except Exception as e:
        log.error(f"LangGraph run {run_id} failed: {e}")
        _update_run_db(run_id, "error", error=str(e))
        return {"error": str(e)}

    ctx = dict(final_state.get("context", {}))
    # Carry _work_item into ctx so finalization callbacks can read it
    if final_state.get("_work_item"):
        ctx["_work_item"] = final_state["_work_item"]
    total_cost = float(final_state.get("total_cost", 0.0))

    # 6. Check if waiting at approval interrupt
    # snapshot.next[0] = the NEXT node to run after approval (e.g. "Architect").
    # The node whose output we're reviewing is the last approval_name whose output is in ctx.
    snapshot = app.get_state(config)
    if snapshot.next:
        next_node_name = snapshot.next[0]
        # Find the approval node that just ran (its output is already in ctx)
        last_ran_name = next_node_name  # fallback
        for aname in reversed(approval_names):
            if aname in ctx:
                last_ran_name = aname
                break
        # Look up node IDs for the waiting node and next node (needed by make_run_decision)
        waiting_node_id = next(
            (nid for nid, n in nodes.items() if n["name"] == last_ran_name), None
        )
        next_node_id = next(
            (nid for nid, n in nodes.items() if n["name"] == next_node_name), None
        )
        ctx["_waiting"] = {
            "node_name": last_ran_name,          # node whose output to show in approval panel
            "node_id": waiting_node_id,          # ID of the waiting node (for retry)
            "next_node": next_node_name,         # node that will run after approval
            "successors": [next_node_id] if next_node_id else [],  # IDs expected by decision endpoint
            "output": ctx.get(last_ran_name, ""),
            "approval_msg": next(
                (n.get("approval_msg", "") for n in nodes.values() if n["name"] == last_ran_name),
                f"Review {last_ran_name} output and approve to proceed to {next_node_name}.",
            ),
        }
        _update_run_db(run_id, "waiting_approval", ctx=ctx, total_cost=total_cost)
        log.info(f"Run {run_id}: '{last_ran_name}' complete — awaiting approval before '{next_node_name}'")
        return ctx

    # 7. Finalize
    _update_run_db(run_id, "done", ctx=ctx, total_cost=total_cost)

    # 8. Fire-and-forget: embed + memory refresh
    _fire_background(run_id, project)

    return ctx


async def resume_graph_workflow(
    run_id: str,
    workflow_id: str,
    project: str,
    ctx: dict,
    start_node_ids: list[str],
    approved: bool = True,
    retry: bool = False,
    reason: str = "",
) -> dict:
    """Resume a paused (waiting_approval) LangGraph run.

    approved=True  → continue from the interrupted node
    retry=True     → re-run the waiting node (clear its output from context)
    approved=False → stop the run
    """
    if not db.is_available():
        raise RuntimeError("PostgreSQL required for graph workflows")

    if not _LANGGRAPH_AVAILABLE:
        return await _resume_graph_workflow_legacy(run_id, start_node_ids, project)

    if not approved and not retry:
        _update_run_db(run_id, "stopped", ctx=ctx)
        _APP_REGISTRY.pop(run_id, None)
        return {"status": "stopped"}

    # Rebuild app if not in registry (server restart recovery)
    if run_id not in _APP_REGISTRY:
        _, nodes, edges = _load_workflow_from_db(workflow_id)
        app, _, cp = _build_langgraph(nodes, edges, run_id, project)
        _APP_REGISTRY[run_id] = (app, cp)

    app, cp = _APP_REGISTRY[run_id]
    config = {"configurable": {"thread_id": run_id}}

    if retry:
        # Remove the waiting node's output so it re-executes cleanly
        snapshot = app.get_state(config)
        if snapshot.next:
            waiting_name = snapshot.next[0]
            new_ctx = {k: v for k, v in snapshot.values.get("context", {}).items()
                       if k != waiting_name}
            new_ctx.pop("_waiting", None)
            app.update_state(config, {"context": new_ctx, "messages": []})

    try:
        final_state = await app.ainvoke(None, config)
    except Exception as e:
        log.error(f"LangGraph resume {run_id} failed: {e}")
        _update_run_db(run_id, "error", error=str(e))
        return {"error": str(e)}

    result_ctx = dict(final_state.get("context", {}))
    if final_state.get("_work_item"):
        result_ctx["_work_item"] = final_state["_work_item"]
    total_cost = float(final_state.get("total_cost", 0.0))

    snapshot = app.get_state(config)
    if snapshot.next:
        next_node_name = snapshot.next[0]
        # Reuse nodes from the registry build (or load once if registry was rebuilt above)
        _, resume_nodes, _ = _load_workflow_from_db(workflow_id)  # cheap — < 5 ms
        resume_approval_names = [n["name"] for n in resume_nodes.values() if n.get("require_approval")]
        last_ran_name = next_node_name
        for aname in reversed(resume_approval_names):
            if aname in result_ctx:
                last_ran_name = aname
                break
        waiting_node_id = next(
            (nid for nid, n in resume_nodes.items() if n["name"] == last_ran_name), None
        )
        next_node_id = next(
            (nid for nid, n in resume_nodes.items() if n["name"] == next_node_name), None
        )
        result_ctx["_waiting"] = {
            "node_name": last_ran_name,
            "node_id": waiting_node_id,
            "next_node": next_node_name,
            "successors": [next_node_id] if next_node_id else [],
            "output": result_ctx.get(last_ran_name, ""),
            "approval_msg": next(
                (n.get("approval_msg", "") for n in resume_nodes.values() if n["name"] == last_ran_name),
                f"Review {last_ran_name} output and approve to proceed to {next_node_name}.",
            ),
        }
        _update_run_db(run_id, "waiting_approval", ctx=result_ctx, total_cost=total_cost)
        return result_ctx

    _update_run_db(run_id, "done", ctx=result_ctx, total_cost=total_cost)
    _APP_REGISTRY.pop(run_id, None)
    _fire_background(run_id, project)
    return result_ctx


def _fire_background(run_id: str, project: str) -> None:
    """Fire-and-forget: embed node outputs + refresh project memory.

    Both tasks are wrapped so unhandled exceptions are logged (not surfaced as
    "Task exception was never retrieved" warnings).
    """
    async def _safe_embed():
        try:
            from memory.mem_embeddings import embed_node_outputs
            await embed_node_outputs(run_id, project)
        except Exception as _e:
            log.debug(f"Background embed failed (non-critical): {_e}")

    async def _refresh_memory():
        try:
            import httpx
            # Long timeout — memory synthesis may take 30-120 s
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
                await client.post(f"{settings.backend_url}/projects/{project}/memory")
            log.debug(f"Background memory refresh done for project={project}")
        except Exception as _e:
            log.debug(f"Background memory refresh failed (non-critical): {_e}")

    try:
        asyncio.create_task(_safe_embed())
    except Exception:
        pass

    try:
        asyncio.create_task(_refresh_memory())
    except Exception:
        pass


# ── Legacy DAG runner (fallback when langgraph not installed) ──────────────────

async def _run_graph_workflow_legacy(
    workflow_id: str,
    user_input: str,
    run_id: str,
    project: str,
    work_item_id: str | None = None,
) -> dict:
    """Original async DAG work-queue runner — used as fallback."""
    workflow, nodes, edges = _load_workflow_from_db(workflow_id)
    max_iter = workflow.get("max_iterations", 5)

    in_degree: dict[str, int] = {nid: 0 for nid in nodes}
    successors: dict[str, list[dict]] = {nid: [] for nid in nodes}
    fwd_in_degree: dict[str, int] = {nid: 0 for nid in nodes}

    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in nodes and tgt in nodes:
            successors[src].append(edge)
            fwd_in_degree[tgt] += 1

    ctx: dict[str, Any] = {"user_input": user_input}

    if work_item_id and db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_WORK_ITEM_NAME, (work_item_id,))
                    wi = cur.fetchone()
            if wi:
                slug = re.sub(r"[^a-z0-9_]", "", wi[1].lower().replace(" ", "_"))
                ctx["_work_item"] = {
                    "id": work_item_id, "category": wi[0], "name": wi[1], "slug": slug,
                }
        except Exception as _we:
            log.warning(f"Could not load work_item {work_item_id}: {_we}")

    total_cost = 0.0
    done_nodes: set[str] = set()
    iteration_count: dict[str, int] = {nid: 0 for nid in nodes}
    ready: list[str] = [nid for nid, deg in fwd_in_degree.items() if deg == 0]

    global_iter = 0
    while ready and global_iter < max_iter * len(nodes) + len(nodes):
        global_iter += 1

        # Mark first ready node as current (for progress tracking)
        if ready and db.is_available():
            try:
                with db.conn() as _cn:
                    with _cn.cursor() as _cr:
                        _cr.execute(
                            _SQL_UPDATE_RUN_CURRENT_NODE,
                            (nodes[ready[0]]["name"], run_id),
                        )
            except Exception:
                pass

        results = await asyncio.gather(
            *[_execute_node(nodes[nid], run_id, ctx, iteration_count[nid], project) for nid in ready],
            return_exceptions=True,
        )

        next_ready: list[str] = []

        for nid, result in zip(ready, results):
            if isinstance(result, Exception):
                log.error(f"Node {nid} raised: {result}")
                ctx[nodes[nid]["name"]] = f"error: {result}"
                done_nodes.add(nid)
                continue

            node_name = result["node_name"]
            output = result["structured"] if result["structured"] else result["output"]
            ctx[node_name] = output
            total_cost += result.get("cost_usd", 0)
            done_nodes.add(nid)
            # Auto-save legacy node output to documents/pipelines/
            if output and result.get("status") != "error" and workflow.get("name"):
                try:
                    _save_node_output(
                        project, workflow["name"], run_id, node_name,
                        output if isinstance(output, str) else json.dumps(output),
                    )
                except Exception as _soe:
                    log.debug(f"Legacy auto-save failed: {_soe}")

            if nodes[nid].get("require_approval") and result["status"] != "error":
                successor_ids = [e["target"] for e in successors.get(nid, [])]
                ctx["_waiting"] = {
                    "node_id": nid, "node_name": node_name,
                    "output": result["output"], "successors": successor_ids,
                    "approval_msg": nodes[nid].get("approval_msg", ""),
                }
                _update_run_db(run_id, "waiting_approval", ctx=ctx, total_cost=total_cost)
                log.info(f"Run {run_id} paused at '{node_name}' — waiting for user approval")
                return ctx

            for edge in successors.get(nid, []):
                tgt = edge["target"]
                if tgt not in nodes:
                    continue
                if not _eval_condition(edge.get("condition"), ctx):
                    continue
                if tgt in done_nodes:
                    if iteration_count[tgt] < max_iter:
                        iteration_count[tgt] += 1
                        done_nodes.discard(tgt)
                        next_ready.append(tgt)
                else:
                    preds_done = all(
                        e["source"] in done_nodes
                        for e in edges
                        if e["target"] == tgt and e["source"] != tgt
                    )
                    if preds_done and tgt not in next_ready:
                        next_ready.append(tgt)

        ready = next_ready

    _update_run_db(run_id, "done", ctx=ctx, total_cost=total_cost)
    _fire_background(run_id, project)
    return ctx


async def _resume_graph_workflow_legacy(
    run_id: str, start_node_ids: list[str], project: str
) -> dict:
    """Legacy resume — called by decision endpoint when langgraph not installed."""
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_RUN_RESUME, (run_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Run not found: {run_id}")
            workflow_id, ctx, total_cost = row[0], row[1] or {}, float(row[2])

    ctx.pop("_waiting", None)
    workflow, nodes, edges = _load_workflow_from_db(workflow_id)
    max_iter = workflow.get("max_iterations", 5)

    successors: dict[str, list[dict]] = {nid: [] for nid in nodes}
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in nodes and tgt in nodes:
            successors[src].append(edge)

    name_to_id = {n["name"]: nid for nid, n in nodes.items()}
    done_nodes: set[str] = set()
    for key in ctx:
        if key.startswith("_"):
            continue
        nid = name_to_id.get(key)
        if nid:
            done_nodes.add(nid)

    iteration_count: dict[str, int] = {nid: 0 for nid in nodes}
    ready = [nid for nid in start_node_ids if nid in nodes and nid not in done_nodes]

    if not ready:
        _update_run_db(run_id, "done", ctx=ctx, total_cost=total_cost)
        return ctx

    global_iter = 0
    while ready and global_iter < max_iter * len(nodes) + len(nodes):
        global_iter += 1
        results = await asyncio.gather(
            *[_execute_node(nodes[nid], run_id, ctx, iteration_count[nid], project) for nid in ready],
            return_exceptions=True,
        )
        next_ready: list[str] = []

        for nid, result in zip(ready, results):
            if isinstance(result, Exception):
                log.error(f"Node {nid} raised: {result}")
                ctx[nodes[nid]["name"]] = f"error: {result}"
                done_nodes.add(nid)
                continue

            node_name = result["node_name"]
            ctx[node_name] = result["structured"] if result["structured"] else result["output"]
            total_cost += result.get("cost_usd", 0)
            done_nodes.add(nid)

            if nodes[nid].get("require_approval") and result["status"] != "error":
                successor_ids = [e["target"] for e in successors.get(nid, [])]
                ctx["_waiting"] = {
                    "node_id": nid, "node_name": node_name,
                    "output": result["output"], "successors": successor_ids,
                    "approval_msg": nodes[nid].get("approval_msg", ""),
                }
                _update_run_db(run_id, "waiting_approval", ctx=ctx, total_cost=total_cost)
                return ctx

            for edge in successors.get(nid, []):
                tgt = edge["target"]
                if tgt not in nodes:
                    continue
                if not _eval_condition(edge.get("condition"), ctx):
                    continue
                if tgt in done_nodes:
                    if iteration_count[tgt] < max_iter:
                        iteration_count[tgt] += 1
                        done_nodes.discard(tgt)
                        next_ready.append(tgt)
                else:
                    preds_done = all(
                        e["source"] in done_nodes
                        for e in edges
                        if e["target"] == tgt and e["source"] != tgt
                    )
                    if preds_done and tgt not in next_ready:
                        next_ready.append(tgt)

        ready = next_ready

    _update_run_db(run_id, "done", ctx=ctx, total_cost=total_cost)
    return ctx
