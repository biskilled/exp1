/**
 * Electron IPC bridge — replaces the old @tauri-apps/api shim.
 *
 * All calls go through window.electronAPI (exposed by preload.js via contextBridge).
 * Falls back to mock responses when running in a plain browser (Vite dev without Electron).
 */

const _isElectron = typeof window !== "undefined" && !!window.electronAPI;

// ── Core invoke (maps old Tauri command names to Electron IPC) ────────────────

export async function invoke(cmd, args = {}) {
  if (_isElectron) {
    return _electronInvoke(cmd, args);
  }
  return _mockInvoke(cmd, args);
}

async function _electronInvoke(cmd, args) {
  const api = window.electronAPI;
  switch (cmd) {
    case "settings_exist":
      return api.fileExists(args.path || _settingsPath());
    case "load_settings": {
      const res = await api.readFile(_settingsPath());
      if (res.error) return _defaultSettings();
      try { return JSON.parse(res.content); } catch { return _defaultSettings(); }
    }
    case "save_settings": {
      const res = await api.writeFile(_settingsPath(), JSON.stringify(args.settings, null, 2));
      return !res.error;
    }
    case "list_projects":
      return [];
    case "get_recent_projects":
      return [];
    default:
      console.warn(`[electron] invoke not mapped: ${cmd}`, args);
      return null;
  }
}

function _settingsPath() {
  // Store settings next to the engine root; fallback to home dir
  return (window.__ENGINE_PATH__ || "") + "/.aicli/ui_settings.json";
}

function _defaultSettings() {
  return {
    api_keys: {},
    default_models: {},
    ui: { theme: "dark", font_size: 13, sidebar_width: 220 },
    backend_url: "http://localhost:8000",
  };
}

// ── Window controls ───────────────────────────────────────────────────────────

export async function closeWindow() {
  if (_isElectron) {
    // Electron handles window close via the native title bar; nothing needed here.
    // If using frameless window, call window.close() which Electron intercepts.
    window.close();
  }
}

export async function minimizeWindow() {
  if (_isElectron) window.close(); // no-op in Electron (native controls handle it)
}

export async function maximizeWindow() {
  // no-op — native macOS/Windows controls handle this
}

// ── File dialogs (delegated to Electron IPC) ──────────────────────────────────

export async function openFileDialog(filters = []) {
  if (_isElectron) {
    return window.electronAPI.openFile();
  }
  return null;
}

export async function saveFileDialog(defaultName = "workflow.yaml") {
  // Electron doesn't expose a save dialog by default in preload; return null
  // and let the caller write via writeFile() directly.
  return null;
}

// ── External links ────────────────────────────────────────────────────────────

export async function openExternal(url) {
  if (_isElectron) {
    return window.electronAPI.openExternal(url);
  }
  window.open(url, "_blank", "noopener");
}

// ── Mock (browser-only fallback for Vite dev without Electron) ────────────────

async function _mockInvoke(cmd, args) {
  console.log(`[mock] ${cmd}`, args);
  const mocks = {
    settings_exist:      () => false,
    load_settings:       () => _defaultSettings(),
    save_settings:       () => null,
    list_projects:       () => [],
    get_recent_projects: () => [],
    create_project:      (a) => ({
      id: "mock-1", name: a.name, description: a.description,
      path: a.path, created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      llm_docs: {}, code_files: [], workflows: [], tags: [],
    }),
    list_workflows:      () => [],
  };
  if (mocks[cmd]) return mocks[cmd](args);
  throw new Error(`Mock not implemented: ${cmd}`);
}
