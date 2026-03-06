/**
 * Explorer view — file tree (left) + Monaco editor (right).
 *
 * Also hosts the prompt compare split-pane when a .md file is open
 * and the user clicks "Compare Providers".
 *
 * Layout:
 *   ┌──────────────┬───────────────────────────────────┐
 *   │  File tree   │  Monaco editor / Compare pane      │
 *   └──────────────┴───────────────────────────────────┘
 */

import { state } from '../stores/state.js';

function _api() {
  return (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
}

export class ExplorerView {
  constructor(container) {
    this.container = container;
    this.selectedFile = null;
    this.monacoEditor = null;
    this.compareMode = false;
    this._render();
    this._loadTree();
  }

  // ------------------------------------------------------------------
  // Render skeleton
  // ------------------------------------------------------------------

  _render() {
    this.container.innerHTML = `
      <div class="explorer-layout" style="display:flex;height:100%;gap:0">
        <div class="file-tree" id="file-tree"
          style="width:260px;min-width:180px;border-right:1px solid var(--border);overflow-y:auto;padding:8px">
          <div class="tree-header" style="display:flex;align-items:center;gap:8px;padding:4px 0 8px">
            <strong style="flex:1">Workspace</strong>
            <button id="btn-new-file" title="New file" style="font-size:18px;background:none;border:none;cursor:pointer">+</button>
          </div>
          <div id="tree-content">Loading...</div>
        </div>

        <div class="editor-pane" style="flex:1;display:flex;flex-direction:column;overflow:hidden">
          <div class="editor-toolbar" style="display:flex;align-items:center;gap:8px;padding:6px 12px;border-bottom:1px solid var(--border)">
            <span id="editor-filename" style="flex:1;font-size:13px;color:var(--muted)">(no file open)</span>
            <button id="btn-save" style="display:none">Save</button>
            <button id="btn-compare" style="display:none">Compare Providers</button>
          </div>
          <div id="monaco-container" style="flex:1;overflow:hidden"></div>
          <div id="compare-container" style="display:none;flex:1;overflow-y:auto;padding:12px;gap:12px"></div>
        </div>
      </div>
    `;

    document.getElementById("btn-save")?.addEventListener("click", () => this._saveFile());
    document.getElementById("btn-compare")?.addEventListener("click", () => this._startCompare());
    document.getElementById("btn-new-file")?.addEventListener("click", () => this._newFile());

    this._initMonaco();
  }

  // ------------------------------------------------------------------
  // Monaco editor
  // ------------------------------------------------------------------

  _initMonaco() {
    // Monaco loaded via CDN or bundled
    if (typeof monaco === "undefined") {
      const monacoEl = document.getElementById("monaco-container");
      if (monacoEl) monacoEl.innerHTML = `<textarea id="fallback-editor"
        style="width:100%;height:100%;font-family:monospace;font-size:13px;border:none;resize:none;padding:12px;background:var(--bg);color:var(--text)"
        placeholder="(Monaco not loaded — using fallback textarea)"></textarea>`;
      return;
    }

    this.monacoEditor = monaco.editor.create(
      document.getElementById("monaco-container"),
      {
        value: "",
        language: "markdown",
        theme: "vs-dark",
        fontSize: 13,
        wordWrap: "on",
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
      }
    );

    window.addEventListener("resize", () => this.monacoEditor?.layout());
  }

  // ------------------------------------------------------------------
  // File tree
  // ------------------------------------------------------------------

  async _loadTree() {
    try {
      const res = await fetch(`${_api()}/files/workspace`);
      const data = await res.json();
      const treeEl = document.getElementById("tree-content");
      if (treeEl) treeEl.innerHTML = this._renderNode(data, 0);

      // Attach click handlers
      treeEl?.querySelectorAll("[data-path]").forEach((el) => {
        el.addEventListener("click", (e) => {
          e.stopPropagation();
          const path = el.dataset.path;
          const type = el.dataset.type;
          if (type === "file") this._openFile(path);
        });
      });
    } catch (e) {
      const treeEl = document.getElementById("tree-content");
      if (treeEl) treeEl.innerHTML = `<span style="color:red">Failed to load tree: ${e.message}</span>`;
    }
  }

  _renderNode(node, depth) {
    const indent = depth * 16;
    if (node.type === "dir") {
      const children = (node.children || []).map((c) => this._renderNode(c, depth + 1)).join("");
      return `
        <div class="tree-dir" style="padding-left:${indent}px;cursor:pointer;user-select:none"
          onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
          📁 ${node.name}
        </div>
        <div class="tree-children">${children}</div>
      `;
    } else {
      const icon = node.name.endsWith(".md") ? "📝" : node.name.endsWith(".yaml") ? "⚙️" : "📄";
      return `
        <div class="tree-file" data-path="${node.path}" data-type="file"
          style="padding-left:${indent}px;cursor:pointer;padding:3px 4px 3px ${indent}px;border-radius:4px"
          onmouseover="this.style.background='var(--hover)'" onmouseout="this.style.background=''">
          ${icon} ${node.name}
        </div>
      `;
    }
  }

  // ------------------------------------------------------------------
  // Open / save file
  // ------------------------------------------------------------------

  async _openFile(relPath) {
    this.selectedFile = relPath;
    const filenameEl = document.getElementById("editor-filename");
    if (filenameEl) filenameEl.textContent = relPath;

    try {
      const res = await fetch(`${_api()}/files/read?path=${encodeURIComponent(relPath)}&root=workspace`);
      const data = await res.json();

      if (data.error) {
        this._setEditorValue(`// Error: ${data.error}`);
        return;
      }

      this._setEditorValue(data.content || "");

      // Show/hide toolbar buttons
      const isMarkdown = relPath.endsWith(".md");
      document.getElementById("btn-save").style.display = "inline-block";
      document.getElementById("btn-compare").style.display = isMarkdown ? "inline-block" : "none";

      // Hide compare, show editor
      document.getElementById("monaco-container").style.display = "block";
      document.getElementById("compare-container").style.display = "none";
      this.compareMode = false;

      // Set language
      if (this.monacoEditor) {
        const lang = relPath.endsWith(".yaml") || relPath.endsWith(".yml") ? "yaml"
          : relPath.endsWith(".md") ? "markdown"
          : relPath.endsWith(".py") ? "python"
          : relPath.endsWith(".js") ? "javascript"
          : "plaintext";
        monaco.editor.setModelLanguage(this.monacoEditor.getModel(), lang);
      }
    } catch (e) {
      this._setEditorValue(`// Failed to load: ${e.message}`);
    }
  }

  async _saveFile() {
    if (!this.selectedFile) return;
    const content = this._getEditorValue();
    try {
      await fetch(`${_api()}/files/write-content?path=${encodeURIComponent(this.selectedFile)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      console.log("Saved:", this.selectedFile);
    } catch (e) {
      alert(`Save failed: ${e.message}`);
    }
  }

  _setEditorValue(content) {
    if (this.monacoEditor) {
      this.monacoEditor.setValue(content);
    } else {
      const fallback = document.getElementById("fallback-editor");
      if (fallback) fallback.value = content;
    }
  }

  _getEditorValue() {
    if (this.monacoEditor) return this.monacoEditor.getValue();
    return document.getElementById("fallback-editor")?.value || "";
  }

  // ------------------------------------------------------------------
  // Prompt compare
  // ------------------------------------------------------------------

  async _startCompare() {
    if (!this.selectedFile) return;
    const content = this._getEditorValue();
    const providers = ["claude", "deepseek", "openai"];

    document.getElementById("monaco-container").style.display = "none";
    const compareEl = document.getElementById("compare-container");
    compareEl.style.display = "flex";
    compareEl.innerHTML = `<div style="width:100%;text-align:center;padding:20px">Running comparison...</div>`;

    const results = await Promise.allSettled(
      providers.map(async (p) => {
        const res = await fetch(`${_api()}/chat/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: content, provider: p }),
        });
        const data = await res.json();
        return { provider: p, output: data.response || data.error || "(no output)" };
      })
    );

    compareEl.innerHTML = results
      .map((r, i) => {
        const provider = providers[i];
        const output = r.status === "fulfilled" ? r.value.output : `Error: ${r.reason}`;
        return `
          <div style="flex:1;border:1px solid var(--border);border-radius:6px;overflow:hidden;min-width:280px">
            <div style="padding:8px 12px;background:var(--surface);font-weight:bold">${i + 1}. ${provider.toUpperCase()}</div>
            <div style="padding:12px;white-space:pre-wrap;font-size:13px;max-height:400px;overflow-y:auto">${this._escapeHtml(output)}</div>
            <div style="padding:8px 12px;border-top:1px solid var(--border)">
              <button onclick="window._explorerView._logWinner('${provider}', '${this.selectedFile}')">
                Pick as winner
              </button>
            </div>
          </div>
        `;
      })
      .join("");

    window._explorerView = this;
    this._compareOutputs = Object.fromEntries(
      results.map((r, i) => [
        providers[i],
        r.status === "fulfilled" ? r.value.output : "",
      ])
    );
  }

  async _logWinner(winner, promptFile) {
    await fetch(`${_api()}/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: `Log compare winner: ${winner} for prompt: ${promptFile}`,
        provider: "claude",
      }),
    });
    alert(`Winner logged: ${winner}`);
  }

  _newFile() {
    const name = prompt("New file name (e.g. prompts/roles/new_role.md):");
    if (!name) return;
    this._openFile(name);
  }

  _escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
}
