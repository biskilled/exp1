/**
 * pipeline.js — Dashboard (analytics & overview)
 *
 * Shows pipeline run statistics, recent runs across all pipelines,
 * and quick cost/token summaries. Read-only reporting view.
 */

import { api } from '../utils/api.js';

export function destroyPipeline() {}   // nothing to clean up

export async function renderPipeline(container, project) {
  container.innerHTML = `
    <div style="padding:1.25rem 1.5rem 2rem;max-width:900px;margin:0 auto;overflow-y:auto;height:100%;box-sizing:border-box">
      <div style="font-size:1rem;font-weight:700;margin-bottom:1.1rem">Dashboard</div>

      <!-- Stats row -->
      <div id="pl-stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1.25rem">
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius,6px);padding:0.85rem 1rem">
          <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:0.3rem">Total Runs</div>
          <div id="stat-runs" style="font-size:1.5rem;font-weight:700">—</div>
        </div>
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius,6px);padding:0.85rem 1rem">
          <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:0.3rem">Total Cost</div>
          <div id="stat-cost" style="font-size:1.5rem;font-weight:700">—</div>
        </div>
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius,6px);padding:0.85rem 1rem">
          <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:0.3rem">Total Tokens</div>
          <div id="stat-tokens" style="font-size:1.5rem;font-weight:700">—</div>
        </div>
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius,6px);padding:0.85rem 1rem">
          <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:0.3rem">Approval Rate</div>
          <div id="stat-approval" style="font-size:1.5rem;font-weight:700">—</div>
        </div>
      </div>

      <!-- Recent runs -->
      <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);margin-bottom:0.5rem">
        Recent Pipeline Runs
      </div>
      <div id="pl-runs" style="border:1px solid var(--border);border-radius:var(--radius,6px);overflow:hidden">
        <div style="padding:0.75rem 1rem;color:var(--muted);font-size:0.78rem">Loading…</div>
      </div>

      <div style="margin-top:0.75rem;font-size:0.72rem;color:var(--muted)">
        Go to <b>Pipelines</b> (◈) to build and run pipelines.
        Go to <b>History</b> (⏱) for full run details.
      </div>
    </div>
  `;

  if (!project) return;

  try {
    const data = await api.agents.listPipelineRuns(project, null, 50);
    const runs  = data.runs || [];

    // Stats
    const totalCost   = runs.reduce((s, r) => s + (r.total_cost_usd || 0), 0);
    const totalTokens = runs.reduce((s, r) => s + (r.total_input_tokens||0) + (r.total_output_tokens||0), 0);
    const approved    = runs.filter(r => r.final_verdict === 'approved').length;
    const finished    = runs.filter(r => ['approved','rejected','done'].includes(r.final_verdict || r.status)).length;

    document.getElementById('stat-runs').textContent    = runs.length;
    document.getElementById('stat-cost').textContent    = `$${totalCost.toFixed(3)}`;
    document.getElementById('stat-tokens').textContent  = totalTokens >= 1000 ? `${(totalTokens/1000).toFixed(1)}k` : String(totalTokens);
    document.getElementById('stat-approval').textContent = finished ? `${Math.round(approved/finished*100)}%` : '—';

    // Recent runs table
    const el = document.getElementById('pl-runs');
    if (!runs.length) {
      el.innerHTML = '<div style="padding:0.75rem 1rem;color:var(--muted);font-size:0.78rem">No runs yet — start a pipeline from the Pipelines tab.</div>';
      return;
    }
    el.innerHTML = `
      <div style="display:grid;grid-template-columns:140px 120px 65px 65px 70px 80px;
                  gap:0.35rem;font-size:0.68rem;font-weight:700;color:var(--muted);
                  padding:0.45rem 0.75rem;border-bottom:1px solid var(--border)">
        <span>Date</span><span>Pipeline</span><span>Duration</span>
        <span>Tokens</span><span>Cost</span><span>Verdict</span>
      </div>
      ${runs.slice(0, 30).map(r => {
        const at  = r.started_at ? new Date(r.started_at).toLocaleString() : '—';
        const dur = r.duration_s != null ? _fmtDur(r.duration_s) : '—';
        const tok = (r.total_input_tokens||0) + (r.total_output_tokens||0);
        const cost = r.total_cost_usd != null ? `$${Number(r.total_cost_usd).toFixed(4)}` : '—';
        const v = r.final_verdict || r.status || '—';
        const vc = v === 'approved' ? 'var(--green,#27ae60)' : v === 'rejected' ? '#e74c3c' : 'var(--muted)';
        return `
          <div style="display:grid;grid-template-columns:140px 120px 65px 65px 70px 80px;
                      gap:0.35rem;font-size:0.72rem;padding:0.35rem 0.75rem;
                      border-bottom:1px solid var(--border);align-items:center">
            <span style="color:var(--muted)">${at}</span>
            <span title="${r.task||''}" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.pipeline_name||'—'}</span>
            <span>${dur}</span>
            <span>${tok >= 1000 ? (tok/1000).toFixed(1)+'k' : tok || '—'}</span>
            <span style="color:var(--accent)">${cost}</span>
            <span style="color:${vc};font-weight:600">${v}</span>
          </div>`;
      }).join('')}
    `;
  } catch (e) {
    const el = document.getElementById('pl-runs');
    if (el) el.innerHTML = `<div style="padding:0.75rem 1rem;color:#e74c3c;font-size:0.78rem">${e.message}</div>`;
  }
}

function _fmtDur(s) {
  if (s == null) return '—';
  const sec = Math.round(s);
  return sec < 60 ? `${sec}s` : `${Math.floor(sec/60)}m ${sec%60}s`;
}
