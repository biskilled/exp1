/**
 * pipeline.js — Data Dashboard view.
 *
 * Three sections:
 *   1. Mirror Data  — mem_mrr_* counts (commits, prompts, items, messages)
 *   2. AI / LLM     — mem_ai_* counts (events, work_items, feature snapshots)
 *   3. Pipeline Runs — last-24h health per background job
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

      <div class="dd-section-label">AI / LLM</div>
      <div id="dd-ai" class="dd-grid dd-grid-3" style="margin-bottom:1.5rem">
        ${_skeleton(3)}
      </div>

      <div class="dd-section-label">Pipeline Runs <span style="font-weight:400;color:var(--muted)">(last 24h)</span></div>
      <div id="dd-pipeline" class="dd-grid dd-grid-6" style="margin-bottom:1.5rem">
        ${_skeleton(6)}
      </div>

      <div id="dd-errors" style="margin-bottom:1.2rem"></div>

      <div class="dd-section-label">Work Item Health</div>
      <div id="dd-health" style="margin-bottom:1.5rem">
        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
      </div>

      <div class="dd-section-label">LLM Pipeline Costs</div>
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
      .dd-grid-3 { grid-template-columns:repeat(3,1fr) }
      .dd-grid-6 { grid-template-columns:repeat(6,1fr) }
      @media(max-width:780px){
        .dd-grid-4{grid-template-columns:repeat(2,1fr)}
        .dd-grid-6{grid-template-columns:repeat(3,1fr)}
      }
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
      .dd-stats { display:flex;gap:1rem;align-items:flex-end }
      .dd-stat { display:flex;flex-direction:column }
      .dd-stat-val { font-size:1.35rem;font-weight:700;color:var(--text);line-height:1 }
      .dd-stat-lbl { font-size:0.62rem;color:var(--muted);margin-top:0.15rem;text-transform:uppercase }
      .dd-card-footer {
        font-size:0.65rem;color:var(--muted);
        display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.1rem
      }
      .dd-tag { background:var(--surface3,rgba(128,128,128,.12));padding:0.1rem 0.35rem;
                border-radius:3px;white-space:nowrap }
      .dd-pipe-card {
        background:var(--surface2);border:1px solid var(--border);
        border-radius:var(--radius);padding:0.55rem 0.6rem;min-width:0
      }
      .dd-pipe-name { font-size:0.62rem;font-weight:600;color:var(--muted);
                      font-family:monospace;margin-bottom:0.35rem;
                      overflow:hidden;text-overflow:ellipsis;white-space:nowrap }
      .dd-pipe-counts { display:flex;gap:0.4rem;font-size:0.72rem;align-items:center }
      .dd-pipe-last { font-size:0.6rem;color:var(--muted);margin-top:0.25rem }
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
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
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

/** Status dot: green=active 24h, orange=stale, gray=empty, red=errors */
function _dot(total, last24h, hasError) {
  if (hasError)    return '#e74c3c';
  if (last24h > 0) return 'var(--green, #27ae60)';
  if (total > 0)   return '#f39c12';
  return 'var(--muted)';
}

async function _loadAll(container, project) {
  if (!project) {
    container.querySelector('#dd-mirror').innerHTML =
      '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">No project selected</div>';
    return;
  }
  try {
    const [dash, runsData, costsData] = await Promise.all([
      api.pipeline.dashboard(project).catch(() => null),
      api.graphWorkflows.recentRuns(project, 8).catch(() => null),
      api.pipeline.llmCosts(project).catch(() => null),
    ]);
    _renderMirror(container, dash?.mirror);
    _renderAI(container, dash?.ai);
    _renderPipeline(container, dash?.pipeline);
    _renderErrors(container, dash?.recent_errors);
    _renderHealth(container, dash?.health, project);
    _renderCosts(container, costsData);
    _renderRuns(container, runsData);
  } catch (e) {
    console.warn('Dashboard load error:', e);
  }
}

// ── Mirror cards ──────────────────────────────────────────────────────────────

const _MIRROR_DEFS = [
  { key: 'commits',  icon: '⊙', label: 'Commits',  extra: d => _pendingTag(d?.pending_embed, 'pending') },
  { key: 'prompts',  icon: '◎', label: 'Prompts',  extra: d => _pendingTag(d?.pending_embed, 'pending') },
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

// ── AI cards ──────────────────────────────────────────────────────────────────

function _renderAI(container, ai) {
  const el = container.querySelector('#dd-ai');
  if (!el) return;
  if (!ai) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">AI data unavailable</div>';
    return;
  }

  const ev = ai.events || {};
  const wi = ai.work_items || {};

  // Events by-type breakdown (top 3)
  const byType = ev.by_type || {};
  const typeLines = Object.entries(byType)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([t, n]) => `<span class="dd-tag">${t}: ${n}</span>`)
    .join('');

  const cards = [
    // Events  (row 1, col 1)
    `<div class="dd-card">
      <div class="dd-card-hdr">
        <span class="dd-card-icon">⚡</span>
        <span class="dd-card-title">Events</span>
        <div class="dd-dot" style="background:${_dot(ev.total, ev.last_24h, false)}"></div>
      </div>
      <div class="dd-stats">
        <div class="dd-stat">
          <div class="dd-stat-val">${_fmtNum(ev.total)}</div>
          <div class="dd-stat-lbl">Total</div>
        </div>
        <div class="dd-stat">
          <div class="dd-stat-val" style="color:${ev.last_24h > 0 ? 'var(--accent)' : 'var(--text)'}">${_fmtNum(ev.last_24h)}</div>
          <div class="dd-stat-lbl">24h</div>
        </div>
      </div>
      <div class="dd-card-footer">
        <span>Last: ${_fmtTime(ev.last_at)}</span>
      </div>
      <div class="dd-card-footer" style="margin-top:0.2rem">${typeLines}</div>
    </div>`,

    // Work Items  (row 2, full-width)
    `<div class="dd-card" style="grid-column:1/-1">
      <div class="dd-card-hdr">
        <span class="dd-card-icon">▦</span>
        <span class="dd-card-title">Work Items</span>
        <div class="dd-dot" style="background:${_dot(wi.total, wi.promoted_24h ?? wi.last_24h, false)}"></div>
      </div>

      <!-- Row 1: volume stats -->
      <div class="dd-stats">
        <div class="dd-stat">
          <div class="dd-stat-val">${_fmtNum(wi.total)}</div>
          <div class="dd-stat-lbl">Total</div>
        </div>
        <div class="dd-stat">
          <div class="dd-stat-val" style="color:${(wi.last_24h??0) > 0 ? 'var(--accent)' : 'var(--text)'}">${_fmtNum(wi.last_24h)}</div>
          <div class="dd-stat-lbl">New 24h</div>
        </div>
        <div class="dd-stat" title="Items whose AI summary was refreshed in the last 24h (via /memory or Refresh AI)">
          <div class="dd-stat-val" style="color:${(wi.promoted_24h??0) > 0 ? '#27ae60' : 'var(--text)'}">${_fmtNum(wi.promoted_24h)}</div>
          <div class="dd-stat-lbl">Promoted 24h</div>
        </div>
        <div class="dd-stat">
          <div class="dd-stat-val">${_fmtNum(wi.active)}</div>
          <div class="dd-stat-lbl">Open</div>
        </div>
        <div class="dd-stat">
          <div class="dd-stat-val">${_fmtNum(wi.done)}</div>
          <div class="dd-stat-lbl">Done</div>
        </div>
      </div>

      <!-- Row 2: linkage quality (hallucination guard) -->
      <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin:0.4rem 0 0.2rem;align-items:center">
        <span style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-right:0.2rem">Linkage</span>
        <span class="dd-tag" style="color:#27ae60;border-color:#27ae6044"
              title="User confirmed the planner tag link">✓ user-linked: ${wi.linked ?? 0}</span>
        <span class="dd-tag" style="color:#f39c12;border-color:#f39c1244"
              title="AI suggested a tag match, waiting for user confirmation">✦ ai-suggested: ${wi.ai_suggested ?? 0}</span>
        <span class="dd-tag" style="color:${(wi.unlinked_ai_only??0) > 20 ? '#e74c3c' : 'var(--muted)'};border-color:${(wi.unlinked_ai_only??0) > 20 ? '#e74c3c44' : 'var(--border)'}"
              title="No tag link at all — fully AI-managed, may include hallucinated items">⚠ unlinked: ${wi.unlinked_ai_only ?? 0}</span>
      </div>

      <!-- Row 3: AI score distribution -->
      ${(() => {
        const bs = wi.by_score || {};
        const total = Object.values(bs).reduce((s,v)=>s+(v||0), 0) || 1;
        const cols = ['#e74c3c','#e67e22','#f1c40f','#2ecc71','#27ae60','#1abc9c'];
        const labels = ['0 – not started','1 – early','2 – in progress','3 – good progress','4 – nearly done','5 – complete'];
        const bars = [0,1,2,3,4,5].map(i => {
          const cnt = bs[String(i)] || 0;
          const pct = Math.round(cnt/total*100);
          return `<div style="display:flex;flex-direction:column;align-items:center;gap:1px;min-width:28px" title="${labels[i]}: ${cnt}">
            <div style="font-size:0.55rem;color:${cols[i]};font-weight:600">${cnt}</div>
            <div style="width:22px;height:${Math.max(2,Math.round(pct*0.32))}px;background:${cols[i]};border-radius:2px;opacity:0.85"></div>
            <div style="font-size:0.48rem;color:var(--muted)">${i}</div>
          </div>`;
        }).join('');
        return `<div style="display:flex;gap:0;align-items:flex-end;margin-top:0.35rem">
          <span style="font-size:0.5rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-right:0.5rem;align-self:center">Score</span>
          ${bars}
        </div>`;
      })()}

      <div class="dd-card-footer" style="margin-top:0.4rem">
        <span>Created: ${_fmtTime(wi.last_at)}</span>
        <span style="margin-left:0.5rem">Promoted: ${_fmtTime(wi.last_promoted_at)}</span>
      </div>
    </div>`,
  ];

  el.innerHTML = cards.join('');
}

// ── Pipeline tiles ────────────────────────────────────────────────────────────

const _PL_LABELS = {
  commit_embed:        'commit_embed',
  commit_store:        'commit_store',
  commit_code_extract: 'commit_code',
  session_summary:     'session',
  tag_match:           'tag_match',
  work_item_embed:     'wi_embed',
  work_item_promote:   'wi_promote',
};

function _renderPipeline(container, pipeline) {
  const el = container.querySelector('#dd-pipeline');
  if (!el) return;
  if (!pipeline) { el.innerHTML = ''; return; }

  el.innerHTML = Object.entries(_PL_LABELS).map(([key, label]) => {
    const s = pipeline[key] || { ok: 0, error: 0, skipped: 0, last_run: null };
    const hasActivity = s.ok > 0 || s.error > 0 || s.skipped > 0;
    const dotColor = !hasActivity ? 'var(--muted)' : s.error > 0 ? '#e74c3c' : 'var(--green,#27ae60)';
    return `
      <div class="dd-pipe-card">
        <div style="display:flex;align-items:center;gap:0.35rem;margin-bottom:0.3rem">
          <div class="dd-dot" style="background:${dotColor}"></div>
          <div class="dd-pipe-name" title="${key}">${label}</div>
        </div>
        <div class="dd-pipe-counts">
          <span style="color:var(--green,#27ae60)">✓${s.ok}</span>
          <span style="color:${s.error > 0 ? '#e74c3c' : 'var(--muted)'}">✗${s.error}</span>
          <span style="color:var(--muted)">⊘${s.skipped}</span>
        </div>
        <div class="dd-pipe-last">${_fmtTime(s.last_run)}</div>
      </div>
    `;
  }).join('');
}

// ── Errors ────────────────────────────────────────────────────────────────────

function _renderErrors(container, errors) {
  const el = container.querySelector('#dd-errors');
  if (!el) return;
  if (!errors?.length) { el.innerHTML = ''; return; }
  el.innerHTML = `
    <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                color:var(--muted);margin-bottom:0.5rem">Recent Errors</div>
    ${errors.map(e => `
      <div style="font-size:0.72rem;color:var(--muted);margin-bottom:0.25rem;
                  display:flex;gap:0.5rem;align-items:baseline">
        <span style="color:#e74c3c;font-family:monospace;flex-shrink:0">${e.pipeline}</span>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${e.error_msg}">${e.error_msg || '(no message)'}</span>
        <span style="flex-shrink:0">${_fmtTime(e.at)}</span>
      </div>
    `).join('')}
  `;
}

// ── LLM Pipeline Costs ────────────────────────────────────────────────────────

function _renderHealth(container, h, project) {
  const el = container.querySelector('#dd-health');
  if (!el) return;
  if (!h) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">No health data</div>';
    return;
  }

  const orphanPct   = Math.round((h.orphan_rate   || 0) * 100);
  const coveragePct = Math.round((h.coverage_rate || 0) * 100);
  const orphanOk    = orphanPct < 15;
  const coverageOk  = coveragePct >= 80;
  const orphanColor = orphanOk ? 'var(--green,#27ae60)' : '#e67e22';
  const covColor    = coverageOk ? 'var(--green,#27ae60)' : '#e67e22';

  function bar(pct, color) {
    const filled = Math.round(pct / 10);
    return Array.from({length: 10}, (_, i) =>
      `<span style="color:${i < filled ? color : 'var(--border)'};font-size:0.65rem">█</span>`
    ).join('');
  }

  const scope = h.scope_breakdown || {};
  const maxRec = h.max_recommended_wi || 5;

  el.innerHTML = `
    <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:0.85rem 1rem">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.6rem 1.4rem;margin-bottom:0.75rem">
        <div style="display:flex;align-items:center;gap:0.5rem">
          <span style="font-size:0.65rem;color:var(--muted);width:90px;flex-shrink:0">Orphan Rate</span>
          <span style="font-size:0.6rem">${bar(orphanPct, orphanColor)}</span>
          <span style="font-size:0.65rem;color:${orphanColor};flex-shrink:0;font-weight:600">${orphanPct}%</span>
          <span style="font-size:0.6rem;color:var(--muted)">${orphanOk ? '✓ &lt;15%' : '⚠ &gt;15%'}</span>
        </div>
        <div style="display:flex;align-items:center;gap:0.5rem">
          <span style="font-size:0.65rem;color:var(--muted);width:90px;flex-shrink:0">Coverage</span>
          <span style="font-size:0.6rem">${bar(coveragePct, covColor)}</span>
          <span style="font-size:0.65rem;color:${covColor};flex-shrink:0;font-weight:600">${coveragePct}%</span>
          <span style="font-size:0.6rem;color:var(--muted)">${coverageOk ? '✓ &gt;80%' : '⚠ &lt;80%'}</span>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;font-size:0.65rem;color:var(--muted);margin-bottom:0.6rem">
        ${scope.feature != null ? `<span style="color:#3498db">⬡ feature ${scope.feature}</span>` : ''}
        ${scope.bug != null ? `<span style="color:#e74c3c">⚠ bug ${scope.bug}</span>` : ''}
        ${scope.task != null ? `<span style="color:#27ae60">✓ task ${scope.task}</span>` : ''}
        <span>Staging: <b>${h.staging_count || 0}</b></span>
        <span>Rejected: <b>${h.rejected_count || 0}</b></span>
        <span>Max recommended: <b>${maxRec}</b></span>
        <span style="color:var(--muted)">(${h.total_planner_tags || 0} planner tags × 1.5)</span>
      </div>
      <button
        style="font-size:0.65rem;padding:0.22rem 0.7rem;background:var(--surface3,rgba(128,128,128,.15));
               border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
               color:var(--text2);font-family:var(--font)"
        onclick="window._runQualityCheck('${project}', this)">
        Run Quality Check
      </button>
      <span id="dd-health-status" style="font-size:0.62rem;color:var(--muted);margin-left:0.5rem"></span>
    </div>
  `;

  window._runQualityCheck = async (proj, btn) => {
    const status = document.getElementById('dd-health-status');
    btn.disabled = true;
    if (status) status.textContent = 'Running…';
    try {
      const result = await api.pipeline.qualityCheck(proj);
      if (status) status.textContent =
        `Done: ${result.approved} approved, ${result.rejected} rejected, ${result.still_staging} staging`;
    } catch (e) {
      if (status) status.textContent = `Error: ${e.message}`;
    } finally {
      btn.disabled = false;
    }
  };
}

function _renderCosts(container, data) {
  const el = container.querySelector('#dd-costs');
  if (!el) return;
  if (!data) {
    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">Cost data unavailable</div>';
    return;
  }

  function _table(title, bucket) {
    const rows = bucket?.by_model || [];
    const total = bucket?.total_cost_usd ?? 0;
    const calls = bucket?.total_calls ?? 0;
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
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right">${m.calls}</td>
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right"
                  >${_fmtNum(m.input_tokens + m.output_tokens)}</td>
                <td style="padding:0.2rem 0 0.2rem 0.4rem;text-align:right;color:var(--accent)"
                  >$${m.cost_usd.toFixed(4)}</td>
              </tr>
            `).join('') : `
              <tr><td colspan="5" style="color:var(--muted);padding:0.5rem 0">No data</td></tr>
            `}
            <tr style="border-top:2px solid var(--border);font-weight:700">
              <td colspan="2" style="padding:0.25rem 0">Total</td>
              <td style="text-align:right;padding:0.25rem 0 0.25rem 0.4rem">${calls}</td>
              <td></td>
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
