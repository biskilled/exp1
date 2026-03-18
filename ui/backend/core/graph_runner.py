"""
graph_runner.py — Async DAG execution engine for graph-based multi-LLM workflows.

Nodes with no unresolved predecessors run in parallel via asyncio.gather.
Loop-back edges are supported via an iteration counter capped at workflow.max_iterations.
Every completed node output is appended to a shared context dict and persisted to
pr_local_{p}_graph_node_results + pr_local_{p}_graph_runs in PostgreSQL.

Public API:
    run_graph_workflow(workflow_id, user_input, run_id, project) -> dict
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from core.database import db

log = logging.getLogger(__name__)


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
    from core.api_keys import get_key
    from core.llm_clients import call_claude, call_deepseek, call_gemini, call_grok
    from core.cost_tracker import estimate_cost

    node_id = node["id"]
    node_name = node["name"]
    provider = node.get("provider", "claude")
    model = node.get("model", "") or None
    role_file = node.get("role_file")
    role_prompt = node.get("role_prompt", "")
    inject_context = node.get("inject_context", True)
    output_schema = node.get("output_schema")

    # Build system prompt — precedence: inline > role_file > mng_agent_roles DB
    if role_file and not role_prompt:
        role_path = Path(settings.workspace_dir) / project / "prompts" / role_file
        if role_path.exists():
            role_prompt = role_path.read_text()
        else:
            log.warning(f"role_file not found: {role_path}")

    if not role_prompt and node.get("role_id") and db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    tbl_ar = db.client_table("agent_roles")
                    cur.execute(
                        f"SELECT system_prompt FROM {tbl_ar} WHERE id=%s AND is_active=TRUE",
                        (node["role_id"],),
                    )
                    row = cur.fetchone()
                    if row:
                        role_prompt = row[0]
        except Exception as _re:
            log.warning(f"Could not load role {node['role_id']}: {_re}")

    # Build user message
    user_parts = []
    if inject_context and ctx:
        ctx_str = "\n\n".join(
            f"=== {k} output ===\n{v if isinstance(v, str) else json.dumps(v)}"
            for k, v in ctx.items()
        )
        user_parts.append(f"<context>\n{ctx_str}\n</context>")

    # Add output schema instruction
    if output_schema:
        fields = output_schema.get("fields", [])
        user_parts.append(
            f"\nRespond with valid JSON only. Required fields: {', '.join(fields)}."
        )

    user_parts.append(f"\n<task>\nIteration {iteration + 1}. Proceed.\n</task>")
    user_msg = "\n".join(user_parts)

    tbl_gnr = db.project_table("graph_node_results", project)

    result_id = None
    # Insert running record
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""INSERT INTO {tbl_gnr}
                           (run_id, node_id, node_name, status, iteration)
                           VALUES (%s, %s, %s, 'running', %s) RETURNING id""",
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
            from core.llm_clients import _openai_client
            import openai as _openai_lib
            client = _openai_client(api_key)
            full_msgs = []
            if role_prompt:
                full_msgs.append({"role": "system", "content": role_prompt})
            full_msgs.extend(messages)
            raw = client.chat.completions.create(
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
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""UPDATE {tbl_gnr} SET
                           status=%s, output=%s, structured=%s,
                           input_tokens=%s, output_tokens=%s, cost_usd=%s,
                           finished_at=NOW()
                           WHERE id=%s""",
                        (
                            status,
                            output,
                            json.dumps(structured) if structured else None,
                            input_tokens,
                            output_tokens,
                            cost_usd,
                            result_id,
                        ),
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


# ── Main DAG runner ───────────────────────────────────────────────────────────

async def run_graph_workflow(
    workflow_id: str,
    user_input: str,
    run_id: str,
    project: str,
) -> dict:
    """Execute a graph workflow asynchronously.

    Nodes run in parallel when they have no unresolved predecessors.
    Loop-back edges are supported up to workflow.max_iterations iterations.

    Returns the final context dict {node_name: output_or_structured}.
    """
    if not db.is_available():
        raise RuntimeError("PostgreSQL required for graph workflows")

    tbl_gw  = db.project_table("graph_workflows",    project)
    tbl_gn  = db.project_table("graph_nodes",        project)
    tbl_ge  = db.project_table("graph_edges",        project)
    tbl_gr  = db.project_table("graph_runs",         project)
    tbl_gnr = db.project_table("graph_node_results", project)

    # ── 1. Load workflow, nodes, edges ────────────────────────────────────────
    workflow: dict = {}
    nodes: dict[str, dict] = {}   # id → node
    edges: list[dict] = []

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT id, project, name, max_iterations FROM {tbl_gw} WHERE id=%s", (workflow_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Workflow not found: {workflow_id}")
            workflow = {"id": row[0], "project": row[1], "name": row[2], "max_iterations": row[3]}

            cur.execute(
                f"""SELECT id, name, role_file, role_prompt, provider, model,
                          output_schema, inject_context, require_approval, approval_msg, role_id
                   FROM {tbl_gn} WHERE workflow_id=%s""",
                (workflow_id,),
            )
            for r in cur.fetchall():
                nodes[r[0]] = {
                    "id": r[0], "name": r[1], "role_file": r[2],
                    "role_prompt": r[3], "provider": r[4], "model": r[5],
                    "output_schema": r[6], "inject_context": r[7],
                    "require_approval": r[8] if len(r) > 8 else False,
                    "approval_msg": r[9] if len(r) > 9 else "",
                    "role_id": r[10] if len(r) > 10 else None,
                }

            cur.execute(
                f"SELECT id, source_node_id, target_node_id, condition, label FROM {tbl_ge} WHERE workflow_id=%s",
                (workflow_id,),
            )
            for r in cur.fetchall():
                edges.append({
                    "id": r[0], "source": r[1], "target": r[2],
                    "condition": r[3], "label": r[4],
                })

    max_iter = workflow.get("max_iterations", 5)

    # ── 2. Build in-degree map and successors ─────────────────────────────────
    in_degree: dict[str, int] = {nid: 0 for nid in nodes}
    successors: dict[str, list[dict]] = {nid: [] for nid in nodes}

    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in nodes and tgt in nodes:
            # Only count forward edges for initial in_degree (loop-backs handled separately)
            successors[src].append(edge)

    # Forward-only in_degree (exclude back-edges for root detection)
    fwd_in_degree: dict[str, int] = {nid: 0 for nid in nodes}
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in nodes and tgt in nodes:
            fwd_in_degree[tgt] += 1

    ctx: dict[str, Any] = {"user_input": user_input}
    total_cost = 0.0
    done_nodes: set[str] = set()
    iteration_count: dict[str, int] = {nid: 0 for nid in nodes}

    # Root nodes = those with no incoming edges
    ready: list[str] = [nid for nid, deg in fwd_in_degree.items() if deg == 0]

    # ── 3. Work-queue loop ────────────────────────────────────────────────────
    global_iter = 0
    while ready and global_iter < max_iter * len(nodes) + len(nodes):
        global_iter += 1

        # Execute all ready nodes in parallel
        results = await asyncio.gather(
            *[
                _execute_node(
                    nodes[nid], run_id, ctx,
                    iteration_count[nid], project,
                )
                for nid in ready
            ],
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

            # ── User approval gate ────────────────────────────────────────────
            if nodes[nid].get("require_approval") and result["status"] != "error":
                # Collect successor node IDs for the decision endpoint
                successor_ids = [e["target"] for e in successors.get(nid, [])]
                ctx["_waiting"] = {
                    "node_id": nid,
                    "node_name": node_name,
                    "output": result["output"],
                    "successors": successor_ids,
                    "approval_msg": nodes[nid].get("approval_msg", ""),
                }
                if db.is_available():
                    try:
                        with db.conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    f"""UPDATE {tbl_gr} SET status='waiting_approval',
                                       context=%s, total_cost_usd=%s WHERE id=%s""",
                                    (json.dumps(ctx), total_cost, run_id),
                                )
                        with db.conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    f"""UPDATE {tbl_gnr} SET status='waiting_approval'
                                       WHERE run_id=%s AND node_id=%s
                                       ORDER BY id DESC LIMIT 1""",
                                    (run_id, nid),
                                )
                    except Exception as e:
                        log.warning(f"Could not save approval pause state: {e}")
                log.info(f"Run {run_id} paused at node '{node_name}' — waiting for user approval")
                return ctx  # Stop execution; decision endpoint will resume

            # Evaluate outgoing edges
            for edge in successors.get(nid, []):
                tgt = edge["target"]
                if tgt not in nodes:
                    continue
                condition = edge.get("condition")
                if not _eval_condition(condition, ctx):
                    continue

                # Loop-back detection: target already done → re-enqueue if under limit
                if tgt in done_nodes:
                    if iteration_count[tgt] < max_iter:
                        iteration_count[tgt] += 1
                        done_nodes.discard(tgt)
                        next_ready.append(tgt)
                else:
                    # Check all predecessors done (forward edges only)
                    preds_done = all(
                        e["source"] in done_nodes
                        for e in edges
                        if e["target"] == tgt and e["source"] != tgt
                    )
                    if preds_done and tgt not in next_ready:
                        next_ready.append(tgt)

        ready = next_ready

    # ── 4. Finalize run ───────────────────────────────────────────────────────
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""UPDATE {tbl_gr} SET
                           status='done', context=%s, total_cost_usd=%s, finished_at=NOW()
                           WHERE id=%s""",
                        (json.dumps(ctx), total_cost, run_id),
                    )
        except Exception as e:
            log.error(f"Could not finalize run {run_id}: {e}")

    # ── 5. Fire-and-forget: embed outputs + refresh memory ───────────────────
    try:
        from core.embeddings import embed_node_outputs
        asyncio.create_task(embed_node_outputs(run_id, project))
    except Exception:
        pass

    try:
        import httpx
        async def _refresh_memory():
            async with httpx.AsyncClient() as client:
                await client.post(f"{settings.backend_url}/projects/{project}/memory")
        asyncio.create_task(_refresh_memory())
    except Exception:
        pass

    return ctx


# ── Resume after user approval ────────────────────────────────────────────────

async def resume_graph_workflow(run_id: str, start_node_ids: list[str], project: str) -> dict:
    """Resume a paused run from the given node IDs.

    Called by the decision endpoint after user approves a node.
    Reconstructs done_nodes from the existing context and continues execution.
    """
    if not db.is_available():
        raise RuntimeError("PostgreSQL required for graph workflows")

    tbl_gw  = db.project_table("graph_workflows",    project)
    tbl_gn  = db.project_table("graph_nodes",        project)
    tbl_ge  = db.project_table("graph_edges",        project)
    tbl_gr  = db.project_table("graph_runs",         project)
    tbl_gnr = db.project_table("graph_node_results", project)

    # Load run state
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT workflow_id, context, total_cost_usd FROM {tbl_gr} WHERE id=%s",
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Run not found: {run_id}")
            workflow_id, ctx, total_cost = row[0], row[1] or {}, float(row[2])

    ctx.pop("_waiting", None)

    # Load workflow, nodes, edges
    workflow: dict = {}
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, project, name, max_iterations FROM {tbl_gw} WHERE id=%s",
                (workflow_id,),
            )
            r = cur.fetchone()
            if not r:
                raise ValueError(f"Workflow not found: {workflow_id}")
            workflow = {"id": r[0], "project": r[1], "name": r[2], "max_iterations": r[3]}

            cur.execute(
                f"""SELECT id, name, role_file, role_prompt, provider, model,
                          output_schema, inject_context, require_approval, approval_msg, role_id
                   FROM {tbl_gn} WHERE workflow_id=%s""",
                (workflow_id,),
            )
            for r in cur.fetchall():
                nodes[r[0]] = {
                    "id": r[0], "name": r[1], "role_file": r[2],
                    "role_prompt": r[3], "provider": r[4], "model": r[5],
                    "output_schema": r[6], "inject_context": r[7],
                    "require_approval": r[8] if len(r) > 8 else False,
                    "approval_msg": r[9] if len(r) > 9 else "",
                    "role_id": r[10] if len(r) > 10 else None,
                }

            cur.execute(
                f"SELECT id, source_node_id, target_node_id, condition, label FROM {tbl_ge} WHERE workflow_id=%s",
                (workflow_id,),
            )
            for r in cur.fetchall():
                edges.append({"id": r[0], "source": r[1], "target": r[2], "condition": r[3], "label": r[4]})

    max_iter = workflow.get("max_iterations", 5)
    successors: dict[str, list[dict]] = {nid: [] for nid in nodes}
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        if src in nodes and tgt in nodes:
            successors[src].append(edge)

    # Reconstruct done_nodes from ctx keys (node names that have outputs)
    name_to_id = {n["name"]: nid for nid, n in nodes.items()}
    done_nodes: set[str] = set()
    for key in ctx:
        if key.startswith("_"):
            continue
        nid = name_to_id.get(key)
        if nid:
            done_nodes.add(nid)

    iteration_count: dict[str, int] = {nid: 0 for nid in nodes}

    # Only start from valid, non-done nodes
    ready = [nid for nid in start_node_ids if nid in nodes and nid not in done_nodes]
    if not ready:
        # All start nodes already done — nothing to do
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {tbl_gr} SET status='done', context=%s, total_cost_usd=%s, finished_at=NOW() WHERE id=%s",
                    (json.dumps(ctx), total_cost, run_id),
                )
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
                if db.is_available():
                    try:
                        with db.conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    f"UPDATE {tbl_gr} SET status='waiting_approval', context=%s, total_cost_usd=%s WHERE id=%s",
                                    (json.dumps(ctx), total_cost, run_id),
                                )
                        with db.conn() as conn:
                            with conn.cursor() as cur:
                                cur.execute(
                                    f"UPDATE {tbl_gnr} SET status='waiting_approval' WHERE run_id=%s AND node_id=%s ORDER BY id DESC LIMIT 1",
                                    (run_id, nid),
                                )
                    except Exception as e:
                        log.warning(f"Could not save approval pause: {e}")
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

    # Finalize
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"UPDATE {tbl_gr} SET status='done', context=%s, total_cost_usd=%s, finished_at=NOW() WHERE id=%s",
                        (json.dumps(ctx), total_cost, run_id),
                    )
        except Exception as e:
            log.error(f"Could not finalize resumed run {run_id}: {e}")

    return ctx
