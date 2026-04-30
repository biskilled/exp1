/**
 * pipeline.js — Data Dashboard view.
 *
 * Sections:
 *   1. Mirror Data  — mem_mrr_* counts (commits, prompts, items, messages)
 *   2. Work Items   — approved vs draft, embedded, status breakdown
 *   3. LLM Usage    — token + cost per provider/model (24h + all-time)
 *   4. Recent Workflow Runs
 */

import { api } from '../utils/api.js';

let _refreshTimer = null;
let _currentProject = null;

export function destroyPipeline() {
  if (_refreshTimer) { clearInterval(_refreshTimer); _refreshTimer = null; }
}

export async function renderPipeline(container, project) {
  destroyPipeline();
  _currentProject = project;

  container.innerHTML = `
    <div style="padding:1.5rem 1.5rem 2rem;max-width:1000px;margin:0 auto;overflow-y:auto;height:100%;box-sizing:border-box">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem">
        <h2 style="margin:0;font-size:1.05rem;font-weight:600">Data Dashboard</h2>
        <button id="dd-refresh-btn" class="btn btn-ghost btn-sm" style="font-size:0.78rem">↻ Refresh</button>
      </div>

      <div class="dd-section-label">Mirror Data</div>
      <div id="dd-mirror" class="dd-grid dd-grid-4" style="margin-bottom:1.5rem">
        ${_skeleton(4)}
      </div>

      <div class="dd-section-label">Work Items / Use Cases</div>
      <div id="dd-workitems" style="margin-bottom:1.5rem">
        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
      </div>

      <div class="dd-section-label">LLM Usage <span style="font-weight:400;color:var(--muted)">(all sources)</span></div>
      <div id="dd-costs" style="margin-bottom:1.5rem">
        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
      </div>

      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem">
        <div class="dd-section-label" style="margin-bottom:0">Recent Workflow Runs</div>
        <button class="btn btn-ghost btn-sm" style="font-size:0.72rem" onclick="window._nav('workflow')">→ Pipelines</button>
      </div>
      <div id="dd-runs"><div style="color:var(--muted);font-size:0.8rem">Loading…</div></div>
    </div>

    <style>
      .dd-section-label {
        font-size:0.7rem;font-weight:700;text-transform:uppercase;
        letter-spacing:0.07em;color:var(--muted);margin-bottom:0.6rem
      }
      .dd-grid { display:grid;gap:0.65rem }
      .dd-grid-4 { grid-template-columns:repeat(4,1fr) }
      @media(max-width:780px){ .dd-grid-4{grid-template-columns:repeat(2,1fr)} }
      .dd-card {
        background:var(--surface2);border:1px solid var(--border);
        border-radius:var(--radius);padding:0.8rem 0.85rem 0.65rem;
        display:flex;flex-direction:column;gap:0.4rem;min-width:0
      }
      .dd-card-hdr {
        display:flex;align-items:center;gap:0.4rem;
        font-size:0.72rem;font-weight:600;color:var(--muted);
        text-transform:uppercase;letter-spacing:0.04em
      }
      .dd-card-icon { font-size:0.85rem;flex-shrink:0 }
      .dd-card-title { flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap }
      .dd-dot { width:7px;height:7px;border-radius:50%;flex-shrink:0 }
      .dd-stats { display:flex;gap:1rem;align-items:flex-end;flex-wrap:wrap }
      .dd-stat { display:flex;flex-direction:column }
      .dd-stat-val { font-size:1.35rem;font-weight:700;color:var(--text);line-height:1 }
      .dd-stat-lbl { font-size:0.62rem;color:var(--muted);margin-top:0.15rem;text-transform:uppercase }
      .dd-card-footer {
        font-size:0.65rem;color:var(--muted);
        display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.1rem
      }
      .dd-tag { background:var(--surface3,rgba(128,128,128,.12));padding:0.1rem 0.35rem;
                border-radius:3px;white-space:nowrap }
      .dd-skel { background:var(--surface2);border:1px solid var(--border);
                 border-radius:var(--radius);padding:0.8rem;opacity:.5;min-height:90px }
    </style>
  `;

  document.getElementById('dd-refresh-btn').onclick = () => _loadAll(container, project);
  await _loadAll(container, project);

  _refreshTimer = setInterval(() => {
    if (_currentProject === project) _loadAll(container, project);
  }, 30_000);
}

function _skeleton(n) {
  return Array(n).fill('<div class="dd-skel"></div>').join('');
}

function _fmtNum(n) {
  if (n == null) return '—';
  return n >= 1_000_000 ? (n / 1_000_000).toFixed(1) + 'M'
       : n >= 1000      ? (n / 1000).toFixed(1) + 'k'
       : String(n);
}

function _fmtTime(iso) {
  if (!iso) return 'never';
  const d = new Date(iso), now = new Date(), diff = now - d;
  if (diff < 60_000)    return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600_000)  return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}h ago`;
  if (diff < 604800_000) return `${Math.floor(diff / 86400_000)}d ago`;
  return d.toLocaleDateString();
}

function _dot(total, last24h, hasError) {
  if (hasError)    return '#e74c3c';
  if (last24h > 0) return 'var(--green,#27ae60)';
  if (total > 0)   return '#f39c12';
  return 'var(--muted)';
}

async function _loadAll(container, project) {
  if (!project) {
    const el = container.querySelector('#dd-mirror');
    if (el) el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">No project selected</div>';
    return;
  }
  try {
    const [dash, runsData, costsData] = await Promise.all([
      api.pipeline.dashboard(project).catch(() => null),
      api.graphWorkflows.recentRuns(project, 8).catch(() => null),
      api.pipeline.llmCosts(project).catch(() => null),
    ]);
    _renderMirror(container, dash?.mirror);
    _renderWorkItems(container, dash?.ai?.work_items);
    _renderCosts(container, costsData);
    _renderRuns(container, runsData);
  } catch (e) {
    console.warn('Dashboard load error:', e);
  }
}

// ── Mirror cards ──────────────────────────────────────────────────────────────

const _MIRROR_DEFS = [
  { key: 'commits',  icon: '⊙', label: 'Commits',  extra: d => _pendingTag(d?.pending_embed, 'embed pending') },
  { key: 'prompts',  icon: '◎', label: 'Prompts',  extra: d => _pendingTag(d?.pending_backlog, 'backlog pending') },
  { key: 'items',    icon: '◈', label: 'Items',    extra: () => '' },
  { key: 'messages', icon: '✉', label: 'Messages', extra: () => '' },
];

function _pendingTag(n, label) {
  if (!n) return '';
  return `<span class="dd-tag" style="color:#f39c12">${label}: ${n}</span>`;
}

function _renderMirror(container, mirror) {
  const el = container.querySelector('#dd-mirror');
  if (!el) return;
  if (!mirror) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Mirror data unavailable</div>';
    return;
  }
  el.innerHTML = _MIRROR_DEFS.map(({ key, icon, label, extra }) => {
    const d = mirror[key] || { total: 0, last_24h: 0, last_at: null };
    const dotColor = _dot(d.total, d.last_24h, false);
    return `
      <div class="dd-card">
        <div class="dd-card-hdr">
          <span class="dd-card-icon">${icon}</span>
          <span class="dd-card-title">${label}</span>
          <div class="dd-dot" style="background:${dotColor}" title="${d.last_24h > 0 ? 'Active' : d.total > 0 ? 'Stale' : 'Empty'}"></div>
        </div>
        <div class="dd-stats">
          <div class="dd-stat">
            <div class="dd-stat-val">${_fmtNum(d.total)}</div>
            <div class="dd-stat-lbl">Total</div>
          </div>
          <div class="dd-stat">
            <div class="dd-stat-val" style="color:${d.last_24h > 0 ? 'var(--accent)' : 'var(--text)'}">${_fmtNum(d.last_24h)}</div>
            <div class="dd-stat-lbl">24h</div>
          </div>
        </div>
        <div class="dd-card-footer">
          <span>Last: ${_fmtTime(d.last_at)}</span>
          ${extra(d)}
        </div>
      </div>
    `;
  }).join('');
}

// ── Work Items card ───────────────────────────────────────────────────────────

function _renderWorkItems(container, wi) {
  const el = container.querySelector('#dd-workitems');
  if (!el) return;
  if (!wi) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">Work item data unavailable</div>';
    return;
  }

  const approvedPct = wi.total > 0 ? Math.round(wi.approved / wi.total * 100) : 0;
  const embeddedPct = wi.total > 0 ? Math.round(wi.embedded / wi.total * 100) : 0;

  el.innerHTML = `
    <div class="dd-card" style="padding:0.8rem 1rem">
      <div style="display:flex;flex-wrap:wrap;gap:1.2rem;align-items:flex-start">

        <!-- Approval status -->
        <div style="flex:1;min-width:160px">
          <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                      color:var(--muted);margin-bottom:0.5rem">Approval Status</div>
          <div class="dd-stats">
            <div class="dd-stat">
              <div class="dd-stat-val">${_fmtNum(wi.total)}</div>
              <div class="dd-stat-lbl">Total</div>
            </div>
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:var(--green,#27ae60)">${_fmtNum(wi.approved)}</div>
              <div class="dd-stat-lbl">Approved</div>
            </div>
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:#f39c12">${_fmtNum(wi.draft)}</div>
              <div class="dd-stat-lbl">Waiting</div>
            </div>
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:var(--muted)">${_fmtNum(wi.done)}</div>
              <div class="dd-stat-lbl">Done</div>
            </div>
          </div>
          <!-- Approval progress bar -->
          ${wi.total > 0 ? `
          <div style="margin-top:0.55rem">
            <div style="height:4px;background:var(--border);border-radius:2px;overflow:hidden">
              <div style="height:100%;width:${approvedPct}%;background:var(--green,#27ae60);border-radius:2px;transition:width 0.4s"></div>
            </div>
            <div style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem">${approvedPct}% approved</div>
          </div>` : ''}
        </div>

        <!-- Vertical divider -->
        <div style="width:1px;background:var(--border);align-self:stretch;flex-shrink:0"></div>

        <!-- Embeddings -->
        <div style="min-width:120px">
          <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                      color:var(--muted);margin-bottom:0.5rem">Embeddings</div>
          <div class="dd-stats">
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:var(--accent)">${_fmtNum(wi.embedded)}</div>
              <div class="dd-stat-lbl">Embedded</div>
            </div>
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:var(--muted)">${_fmtNum((wi.approved || 0) - (wi.embedded || 0))}</div>
              <div class="dd-stat-lbl">Pending</div>
            </div>
          </div>
          ${wi.approved > 0 ? `
          <div style="margin-top:0.55rem">
            <div style="height:4px;background:var(--border);border-radius:2px;overflow:hidden">
              <div style="height:100%;width:${embeddedPct}%;background:var(--accent);border-radius:2px;transition:width 0.4s"></div>
            </div>
            <div style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem">${embeddedPct}% of total embedded</div>
          </div>` : ''}
        </div>

        <!-- Vertical divider -->
        <div style="width:1px;background:var(--border);align-self:stretch;flex-shrink:0"></div>

        <!-- Activity -->
        <div style="min-width:100px">
          <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                      color:var(--muted);margin-bottom:0.5rem">Activity</div>
          <div class="dd-stats">
            <div class="dd-stat">
              <div class="dd-stat-val" style="color:${wi.last_24h > 0 ? 'var(--accent)' : 'var(--text)'}">${_fmtNum(wi.last_24h)}</div>
              <div class="dd-stat-lbl">Updated 24h</div>
            </div>
          </div>
          <div class="dd-card-footer" style="margin-top:0.5rem">
            Last: ${_fmtTime(wi.last_at)}
          </div>
        </div>

      </div>
    </div>
  `;
}

// ── LLM Usage / Costs ─────────────────────────────────────────────────────────

function _renderCosts(container, data) {
  const el = container.querySelector('#dd-costs');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">Usage data unavailable</div>';
    return;
  }

  function _table(title, bucket) {
    const rows  = bucket?.by_model || [];
    const total = bucket?.total_cost_usd ?? 0;
    const calls = bucket?.total_calls ?? 0;
    const totalTok = rows.reduce((s, m) => s + (m.input_tokens || 0) + (m.output_tokens || 0), 0);
    return `
      <div style="flex:1;min-width:280px">
        <div style="font-size:0.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;
                    letter-spacing:0.06em;margin-bottom:0.45rem">${title}</div>
        <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
          <thead>
            <tr style="color:var(--muted);font-size:0.65rem;text-transform:uppercase;letter-spacing:.04em">
              <th style="text-align:left;padding:0.1rem 0.4rem 0.1rem 0;font-weight:600">Provider</th>
              <th style="text-align:left;padding:0.1rem 0.4rem;font-weight:600">Model</th>
              <th style="text-align:right;padding:0.1rem 0 0.1rem 0.4rem;font-weight:600">Calls</th>
              <th style="text-align:right;padding:0.1rem 0 0.1rem 0.4rem;font-weight:600">Tokens</th>
              <th style="text-align:right;padding:0.1rem 0 0.1rem 0.4rem;font-weight:600">Cost</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map(m => `
              <tr style="border-top:1px solid var(--border)">
                <td style="padding:0.2rem 0.4rem 0.2rem 0;color:var(--text)">${m.provider}</td>
                <td style="padding:0.2rem 0.4rem;color:var(--muted);font-family:monospace;font-size:0.65rem"
                  >${m.model}</td>
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right">${_fmtNum(m.calls)}</td>
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right"
                  >${_fmtNum((m.input_tokens || 0) + (m.output_tokens || 0))}</td>
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right;color:var(--accent)"
                  >$${m.cost_usd.toFixed(4)}</td>
              </tr>
            `).join('') : `
              <tr><td colspan="5" style="color:var(--muted);padding:0.5rem 0;font-size:0.75rem">No data yet</td></tr>
            `}
            <tr style="border-top:2px solid var(--border);font-weight:700">
              <td colspan="2" style="padding:0.25rem 0">Total</td>
              <td style="text-align:right;padding:0.25rem 0 0.25rem 0.4rem">${_fmtNum(calls)}</td>
              <td style="text-align:right;padding:0.25rem 0 0.25rem 0.4rem">${_fmtNum(totalTok)}</td>
              <td style="text-align:right;padding:0.25rem 0 0.25rem 0.4rem;color:var(--accent)">$${total.toFixed(4)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  el.innerHTML = `
    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;
                background:var(--surface2);border:1px solid var(--border);
                border-radius:var(--radius);padding:0.85rem 1rem">
      ${_table('Last 24h', data.last_24h)}
      <div style="width:1px;background:var(--border);flex-shrink:0"></div>
      ${_table('All Time', data.all_time)}
    </div>
  `;
}

// ── Workflow runs ─────────────────────────────────────────────────────────────

function _renderRuns(container, data) {
  const el = container.querySelector('#dd-runs');
  if (!el) return;
  const runs = data?.runs || data || [];
  if (!Array.isArray(runs) || !runs.length) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">No recent runs</div>';
    return;
  }
  el.innerHTML = runs.slice(0, 8).map(r => {
    const statusColor = r.status === 'done' ? 'var(--green,#27ae60)'
      : r.status === 'running' ? 'var(--accent)'
      : r.status === 'error'   ? '#e74c3c'
      : 'var(--muted)';
    return `
      <div style="display:flex;gap:0.75rem;align-items:baseline;font-size:0.78rem;
                  padding:0.35rem 0;border-bottom:1px solid var(--border)">
        <span style="color:var(--muted);font-family:monospace;font-size:0.65rem;flex-shrink:0"
              >${r.workflow_name || r.workflow_id?.slice(0, 8) || '?'}</span>
        <span style="flex:1;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${r.user_input || ''}">${(r.user_input || '').slice(0, 65)}</span>
        <span style="color:${statusColor};flex-shrink:0">${r.status}</span>
        <span style="color:var(--muted);flex-shrink:0">${_fmtTime(r.started_at)}</span>
      </div>
    `;
  }).join('');
}
