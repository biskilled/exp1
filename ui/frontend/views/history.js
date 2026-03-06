/**
 * History view — JSONL chat history, commits CSV, workflow run logs.
 *
 * Tabs:
 *   Chat History  |  Commits  |  Workflow Runs  |  Prompt Evals
 */

import { state } from '../stores/state.js';

// Build a history API URL, injecting the current project as a query param.
function _histUrl(path) {
  const base = (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
  const project = state.currentProject?.name;
  const sep = path.includes('?') ? '&' : '?';
  const proj = project ? `${sep}project=${encodeURIComponent(project)}` : '';
  return `${base}${path}${proj}`;
}

export class HistoryView {
  constructor(container) {
    this.container = container;
    this.activeTab = "chat";
    this._render();
    this._loadTab("chat");
  }

  _render() {
    this.container.innerHTML = `
      <div class="history-layout" style="display:flex;flex-direction:column;height:100%">
        <div class="tab-bar" style="display:flex;gap:4px;padding:8px 12px;border-bottom:1px solid var(--border)">
          ${["chat", "commits", "runs", "evals"]
            .map(
              (t) =>
                `<button class="tab-btn" data-tab="${t}"
                  style="padding:6px 14px;border-radius:6px;border:1px solid var(--border);cursor:pointer;background:${this.activeTab === t ? "var(--accent)" : "var(--surface)"}"
                  onclick="window._historyView._loadTab('${t}')">
                  ${t.charAt(0).toUpperCase() + t.slice(1)}
                </button>`
            )
            .join("")}
          <div style="flex:1"></div>
          <input id="history-search" placeholder="Search..." style="padding:4px 8px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text)" />
        </div>
        <div id="history-content" style="flex:1;overflow-y:auto;padding:12px"></div>
      </div>
    `;
    window._historyView = this;
    document.getElementById("history-search")?.addEventListener("input", (e) => {
      this._filterContent(e.target.value);
    });
  }

  async _loadTab(tab) {
    this.activeTab = tab;
    // Update tab styles
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.style.background = btn.dataset.tab === tab ? "var(--accent)" : "var(--surface)";
    });

    const content = document.getElementById("history-content");
    if (!content) return;
    content.innerHTML = "<div style='padding:20px;color:var(--muted)'>Loading...</div>";

    try {
      if (tab === "chat") await this._renderChat(content);
      else if (tab === "commits") await this._renderCommits(content);
      else if (tab === "runs") await this._renderRuns(content);
      else if (tab === "evals") await this._renderEvals(content);
    } catch (e) {
      content.innerHTML = `<div style="color:red;padding:20px">Error: ${e.message}</div>`;
    }
  }

  async _renderChat(container) {
    const res = await fetch(_histUrl('/history/chat?limit=100'));
    const data = await res.json();
    const entries = data.entries || [];

    if (!entries.length) {
      container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No chat history yet.</div>";
      return;
    }

    container.innerHTML = entries
      .map(
        (e) => `
        <div class="history-entry" style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px">
          <div style="display:flex;gap:8px;margin-bottom:6px;font-size:12px;color:var(--muted);flex-wrap:wrap;align-items:center">
            <span>${e.ts?.slice(0, 16) || ""}</span>
            <span style="color:var(--accent)">${e.provider || ""}</span>
            ${e.source === "claude_code" ? `<span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">claude-code</span>` : ""}
            ${e.source === "ui" ? `<span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">ui</span>` : ""}
            ${e.feature ? `<span>#${e.feature}</span>` : ""}
            ${e.tag ? `<span style="color:orange">#${e.tag}</span>` : ""}
          </div>
          <div style="font-weight:500;margin-bottom:4px">${this._escapeHtml(e.user_input?.slice(0, 150) || "")}</div>
          ${e.output ? `<div style="color:var(--muted);font-size:13px;margin-top:4px;border-left:2px solid var(--border);padding-left:8px">${this._escapeHtml(e.output.slice(0, 250))}${e.output.length > 250 ? "…" : ""}</div>` : ""}
        </div>
      `
      )
      .join("");
  }

  async _renderCommits(container) {
    const res = await fetch(_histUrl('/history/commits?limit=50'));
    const data = await res.json();
    const commits = data.commits || [];

    if (!commits.length) {
      container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No commits recorded.</div>";
      return;
    }

    container.innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead>
          <tr style="background:var(--surface)">
            ${["Hash", "Date", "Feature", "Tag", "Message"].map((h) => `<th style="padding:8px;text-align:left;border-bottom:1px solid var(--border)">${h}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          ${commits
            .map(
              (c) => `
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:6px 8px;font-family:monospace">${c.hash?.slice(0, 8) || ""}</td>
              <td style="padding:6px 8px">${c.date || ""}</td>
              <td style="padding:6px 8px;color:var(--accent)">${c.feature || ""}</td>
              <td style="padding:6px 8px;color:orange">${c.tag || ""}</td>
              <td style="padding:6px 8px">${this._escapeHtml(c.message || "")}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  }

  async _renderRuns(container) {
    const res = await fetch(_histUrl('/history/runs?limit=20'));
    const data = await res.json();
    const runs = data.runs || [];

    if (!runs.length) {
      container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No workflow runs yet.</div>";
      return;
    }

    container.innerHTML = runs
      .map(
        (r) => `
        <div class="run-entry" style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px;cursor:pointer"
          onclick="window._historyView._showRunDetail('${r.file}')">
          <div style="display:flex;gap:12px;align-items:center">
            <strong>${r.workflow || r.file}</strong>
            <span style="color:var(--muted);font-size:12px">${r.started_at?.slice(0, 16) || ""}</span>
            <span>${r.steps || 0} steps</span>
            <span style="color:green">$${(r.total_cost_usd || 0).toFixed(5)}</span>
            <span style="color:var(--muted)">${r.duration_secs || 0}s</span>
          </div>
        </div>
      `
      )
      .join("");
  }

  async _showRunDetail(filename) {
    const res = await fetch(_histUrl(`/history/runs/${filename}`));
    const run = await res.json();

    const modal = document.createElement("div");
    modal.style.cssText =
      "position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:1000";
    modal.innerHTML = `
      <div style="background:var(--bg);border-radius:8px;padding:24px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
        <div style="display:flex;justify-content:space-between;margin-bottom:16px">
          <strong>Run: ${run.workflow}</strong>
          <button onclick="this.closest('div[style*=fixed]').remove()">✕</button>
        </div>
        <pre style="font-size:12px;background:var(--surface);padding:12px;border-radius:4px;overflow-x:auto">${JSON.stringify(run, null, 2)}</pre>
      </div>
    `;
    document.body.appendChild(modal);
  }

  async _renderEvals(container) {
    const res = await fetch(_histUrl('/history/evals'));
    const data = await res.json();
    const evals = data.evals || [];

    if (!evals.length) {
      container.innerHTML =
        "<div style='padding:20px;color:var(--muted)'>No prompt evaluations yet. Use /compare in the CLI.</div>";
      return;
    }

    container.innerHTML = evals
      .map(
        (e) => `
        <div style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px">
          <div style="display:flex;gap:8px;margin-bottom:8px">
            <span style="color:var(--muted);font-size:12px">${e.ts?.slice(0, 16) || ""}</span>
            <span style="color:var(--accent)">${e.prompt_file || ""}</span>
            <span style="color:green">Winner: ${e.winner || "(none)"}</span>
          </div>
          <div style="font-size:12px;color:var(--muted)">Providers: ${(e.providers || []).join(", ")}</div>
          ${e.notes ? `<div style="margin-top:4px;font-size:12px">${this._escapeHtml(e.notes)}</div>` : ""}
        </div>
      `
      )
      .join("");
  }

  _filterContent(query) {
    const entries = document.querySelectorAll(".history-entry, .run-entry");
    entries.forEach((el) => {
      el.style.display = el.textContent.toLowerCase().includes(query.toLowerCase()) ? "" : "none";
    });
  }

  _escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
}
