/**
 * pipeline.js — Pipeline Health Dashboard view.
 *
 * Renders background task health stats (commit_embed, session_summary, tag_match, etc.)
 * with 30-second auto-refresh and links to recent workflow runs.
 */

import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

let _refreshTimer = null;
let _currentProject = null;

export function destroyPipeline() {
  if (_refreshTimer) {
    clearInterval(_refreshTimer);
    _refreshTimer = null;
  }
}

export async function renderPipeline(container, project) {
  destroyPipeline();
  _currentProject = project;
  container.innerHTML = `
    <div style="padding:1.5rem;max-width:900px;margin:0 auto;overflow-y:auto;height:100%">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem">
        <h2 style="margin:0;font-size:1.1rem">Pipeline Health</h2>
        <button id="pipeline-refresh-btn" class="btn btn-ghost btn-sm" onclick="window._pipelineRefresh()">↻ Refresh</button>
      </div>
      <div id="pipeline-cards" style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1.5rem">
        <div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Loading…</div>
      </div>
      <div id="pipeline-pending" style="margin-bottom:1.2rem"></div>
      <div id="pipeline-errors" style="margin-bottom:1.5rem"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
        <h3 style="margin:0;font-size:0.95rem">Recent Workflow Runs</h3>
        <button class="btn btn-ghost btn-sm" onclick="window._nav('workflow')">→ Pipelines</button>
      </div>
      <div id="pipeline-runs">
        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
      </div>
    </div>
  `;

  window._pipelineRefresh = () => _loadAll(container, project);
  await _loadAll(container, project);

  // Auto-refresh every 30s
  _refreshTimer = setInterval(() => {
    if (_currentProject === project) {
      _loadAll(container, project);
    }
  }, 30_000);
}

const _PIPELINE_LABELS = {
  commit_embed:         'commit_embed',
  commit_store:         'commit_store',
  commit_code_extract:  'commit_code',
  session_summary:      'session_summary',
  tag_match:            'tag_match',
  work_item_embed:      'wi_embed',
};

function _fmtTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  if (diff < 60_000)  return `${Math.floor(diff/1000)}s ago`;
  if (diff < 3600_000) return `${Math.floor(diff/60_000)}m ago`;
  if (diff < 86400_000) return `${Math.floor(diff/3600_000)}h ago`;
  return d.toLocaleDateString();
}

async function _loadAll(container, project) {
  if (!project) {
    container.querySelector('#pipeline-cards').innerHTML =
      '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">No project selected</div>';
    return;
  }

  try {
    const [statusData, runsData] = await Promise.all([
      api.pipeline.status(project).catch(() => null),
      api.graphWorkflows.recentRuns(project, 10).catch(() => null),
    ]);

    _renderCards(container, statusData);
    _renderPending(container, statusData);
    _renderErrors(container, statusData);
    _renderRuns(container, runsData);
  } catch (e) {
    console.warn('Pipeline load error:', e);
  }
}

function _renderCards(container, data) {
  const el = container.querySelector('#pipeline-cards');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Pipeline data unavailable</div>';
    return;
  }

  const last24h = data.last_24h || {};
  const pipelines = Object.keys(_PIPELINE_LABELS);

  el.innerHTML = pipelines.map(key => {
    const stats = last24h[key] || { ok: 0, error: 0, skipped: 0, last_run: null };
    const hasData = stats.ok > 0 || stats.error > 0 || stats.skipped > 0;
    const dotColor = !hasData ? 'var(--muted)' : stats.error > 0 ? 'var(--red, #e74c3c)' : 'var(--green, #27ae60)';
    const label = _PIPELINE_LABELS[key] || key;
    return `
      <div style="background:var(--surface2);border-radius:var(--radius);padding:0.75rem;
                  border:1px solid var(--border)">
        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.5rem">
          <div style="width:7px;height:7px;border-radius:50%;background:${dotColor};flex-shrink:0"></div>
          <span style="font-size:0.72rem;font-weight:600;color:var(--text);font-family:monospace">${label}</span>
        </div>
        <div style="font-size:0.72rem;color:var(--muted);display:flex;gap:0.6rem">
          <span style="color:var(--green,#27ae60)">&#10003;${stats.ok}</span>
          <span style="color:${stats.error>0?'var(--red,#e74c3c)':'var(--muted)'}">&#10007;${stats.error}</span>
          <span>&#9197;${stats.skipped}</span>
        </div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem">${_fmtTime(stats.last_run)}</div>
      </div>
    `;
  }).join('');
}

function _renderPending(container, data) {
  const el = container.querySelector('#pipeline-pending');
  if (!el) return;
  const pending = data?.pending || {};
  const items = [];
  if (pending.commits_not_embedded > 0)
    items.push(`&#9888; Pending: ${pending.commits_not_embedded} commit${pending.commits_not_embedded !== 1 ? 's' : ''} not embedded`);
  if (pending.work_items_unmatched > 0)
    items.push(`&#9888; Pending: ${pending.work_items_unmatched} work item${pending.work_items_unmatched !== 1 ? 's' : ''} unmatched`);
  el.innerHTML = items.map(t =>
    `<div style="font-size:0.78rem;color:var(--accent);margin-bottom:0.3rem">${t}</div>`
  ).join('');
}

function _renderErrors(container, data) {
  const el = container.querySelector('#pipeline-errors');
  if (!el) return;
  const errors = data?.recent_errors || [];
  if (!errors.length) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <div style="font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;color:var(--text)">Recent Errors</div>
    ${errors.slice(0, 5).map(e => `
      <div style="font-size:0.72rem;color:var(--muted);margin-bottom:0.25rem;
                  display:flex;gap:0.5rem;align-items:baseline">
        <span style="color:var(--red,#e74c3c);font-family:monospace">${e.pipeline}</span>
        <span style="color:var(--muted);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${e.error_msg}">${e.error_msg || '(no message)'}</span>
        <span style="flex-shrink:0">${_fmtTime(e.at)}</span>
      </div>
    `).join('')}
  `;
}

function _renderRuns(container, data) {
  const el = container.querySelector('#pipeline-runs');
  if (!el) return;
  const runs = data?.runs || data || [];
  if (!Array.isArray(runs) || !runs.length) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">No recent runs</div>';
    return;
  }
  el.innerHTML = runs.slice(0, 8).map(r => {
    const statusColor = r.status === 'done' ? 'var(--green,#27ae60)'
      : r.status === 'running' ? 'var(--accent)'
      : r.status === 'error' ? 'var(--red,#e74c3c)'
      : 'var(--muted)';
    const statusDot = r.status === 'running'
      ? `<span style="color:${statusColor}">&#9679; running</span>`
      : `<span style="color:${statusColor}">${r.status}</span>`;
    return `
      <div style="display:flex;gap:0.75rem;align-items:baseline;font-size:0.78rem;
                  padding:0.35rem 0;border-bottom:1px solid var(--border)">
        <span style="color:var(--muted);font-family:monospace;font-size:0.68rem">${r.workflow_name || r.workflow_id?.slice(0,8) || '?'}</span>
        <span style="flex:1;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${r.user_input||''}">${(r.user_input||'').slice(0,60)}</span>
        ${statusDot}
        <span style="color:var(--muted);flex-shrink:0">${_fmtTime(r.started_at)}</span>
      </div>
    `;
  }).join('');
}
