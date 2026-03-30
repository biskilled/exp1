/**
 * electron/main.js — Electron main process
 *
 * Manages the app lifecycle: spawns the Python backend (uvicorn) when running locally,
 * creates the BrowserWindow, handles IPC for file system / dialogs / settings,
 * and cleans up on exit. Settings (server URL) are persisted to userData/settings.json.
 */

const { app, BrowserWindow, ipcMain, dialog, shell, Menu, globalShortcut } = require("electron");

// Suppress harmless Chromium DevTools protocol warnings (Autofill.enable etc.)
app.commandLine.appendSwitch("disable-features", "Autofill,AutofillServerCommunication");
// Suppress renderer console noise from protocol errors
app.commandLine.appendSwitch("log-level", "3");
const path = require("path");
const { spawn, execSync } = require("child_process");
const net = require("net");
const fs = require("fs");

const ENGINE_ROOT = path.resolve(__dirname, "../..");
const UI_ROOT = path.resolve(__dirname, "..");
const BACKEND_DIR = path.join(ENGINE_ROOT, "backend");  // new location: aicli/backend/
const FRONTEND_DIR = path.join(UI_ROOT, "frontend");

let mainWindow = null;
let backendProcess = null;
const BACKEND_PORT = 8000;

// ------------------------------------------------------------------
// Settings (persisted to Electron userData/settings.json)
// ------------------------------------------------------------------

let _settingsCache = null;

function getSettingsPath() {
  return path.join(app.getPath("userData"), "settings.json");
}

function loadSettings() {
  if (_settingsCache) return _settingsCache;
  try {
    _settingsCache = JSON.parse(fs.readFileSync(getSettingsPath(), "utf-8"));
  } catch {
    _settingsCache = {};
  }
  return _settingsCache;
}

function saveSettings(updates) {
  _settingsCache = { ...loadSettings(), ...updates };
  try {
    fs.writeFileSync(getSettingsPath(), JSON.stringify(_settingsCache, null, 2), "utf-8");
  } catch (e) {
    console.error("[settings] Failed to save:", e.message);
  }
}

function getServerUrl() {
  const { serverUrl } = loadSettings();
  return (serverUrl && serverUrl.trim()) || `http://127.0.0.1:${BACKEND_PORT}`;
}

function isLocalServer(url) {
  return url.includes("127.0.0.1") || url.includes("localhost");
}

// ------------------------------------------------------------------
// Backend lifecycle
// ------------------------------------------------------------------

/**
 * Check if a TCP port is already in use on localhost.
 * Returns true if busy (something is listening), false if free.
 */
function isPortBusy(port) {
  return new Promise((resolve) => {
    const tester = net.createServer();
    tester.once("error", () => resolve(true));   // EADDRINUSE → busy
    tester.once("listening", () => { tester.close(); resolve(false); });
    tester.listen(port, "127.0.0.1");
  });
}

/**
 * Kill whatever process is holding the port, then wait for the OS to release it.
 * Safe to call even if nothing is listening.
 */
async function freePort(port) {
  if (!(await isPortBusy(port))) return;  // already free

  console.log(`[backend] Port ${port} busy — killing stale process…`);
  try {
    if (process.platform === "win32") {
      // Windows: find PID via netstat, then taskkill
      execSync(
        `for /f "tokens=5" %a in ('netstat -aon ^| findstr :${port}') do taskkill /F /PID %a`,
        { shell: true, stdio: "ignore" }
      );
    } else {
      // macOS / Linux: lsof → kill -9
      execSync(`lsof -ti tcp:${port} | xargs kill -9 2>/dev/null || true`, {
        shell: true,
        stdio: "ignore",
      });
    }
  } catch { /* ignore — process may have already exited */ }

  // Wait up to 2 s for the OS to release the port
  const deadline = Date.now() + 2000;
  while (Date.now() < deadline) {
    if (!(await isPortBusy(port))) return;
    await new Promise((r) => setTimeout(r, 150));
  }
  console.warn(`[backend] Port ${port} still busy after kill attempt`);
}

function startBackend() {
  const python = process.platform === "win32" ? "python" : "python3.12";
  const env = Object.assign({}, process.env, { PYTHONPATH: ENGINE_ROOT });

  backendProcess = spawn(
    python,
    ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    { cwd: BACKEND_DIR, env, stdio: ["ignore", "pipe", "pipe"] }
  );

  backendProcess.stdout.on("data", (d) => console.log("[backend]", d.toString().trim()));
  backendProcess.stderr.on("data", (d) => console.error("[backend]", d.toString().trim()));
  backendProcess.on("exit", (code) => {
    console.log(`[backend] exited (${code})`);
    if (backendProcess) backendProcess = null;
  });
}

let _stopCalled = false;

function stopBackend() {
  // Guard against double-call (window-all-closed + before-quit both fire on macOS quit)
  if (_stopCalled) return;
  _stopCalled = true;

  if (backendProcess) {
    const proc = backendProcess;
    backendProcess = null;
    proc.kill("SIGTERM");

    // Force-kill after 2 s if SIGTERM wasn't enough (e.g. uvicorn hung)
    setTimeout(() => {
      try { proc.kill("SIGKILL"); } catch { /* already dead */ }
    }, 2000);
  }
}

// ------------------------------------------------------------------
// Wait for backend to be ready
// ------------------------------------------------------------------

async function waitForBackend(serverUrl, maxWaitMs = 15000) {
  const http = require("http");
  // Backend: check /health for 200. Vite dev server: any response means it's up.
  const isVite = serverUrl.includes("5173");
  const checkUrl = isVite ? serverUrl + "/" : serverUrl + "/health";
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const ok = await new Promise((resolve) => {
      const req = http.get(checkUrl, (res) => resolve(isVite ? true : res.statusCode === 200));
      req.on("error", () => resolve(false));
      req.setTimeout(1000, () => { req.destroy(); resolve(false); });
      req.end();
    });
    if (ok) return true;
    await new Promise((r) => setTimeout(r, 300));
  }
  return false;
}

// ------------------------------------------------------------------
// Window
// ------------------------------------------------------------------

async function createWindow(serverUrl) {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    // Push traffic lights down a bit so they sit inside the custom titlebar
    trafficLightPosition: { x: 12, y: 13 },
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Content Security Policy — suppress the Electron security warning
  const { session } = require("electron");
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [
          "default-src 'self' http://localhost:* http://127.0.0.1:*; " +
          "script-src 'self' 'unsafe-inline' http://localhost:*; " +
          "style-src 'self' 'unsafe-inline'; " +
          "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:*; " +
          "img-src 'self' data: blob:; " +
          "font-src 'self' data:;"
        ],
      },
    });
  });

  // Wait for backend before loading (local: already spawned; remote: may need a moment)
  const ready = await waitForBackend(serverUrl);
  if (!ready) {
    console.error(`[main] Backend not reachable at ${serverUrl}`);
  }

  // Dev mode: explicit flag OR dist not built yet (auto-detect)
  const isDev = process.env.NODE_ENV === "development" ||
    !fs.existsSync(path.join(UI_ROOT, "dist", "index.html"));

  if (isDev) {
    // Wait for the Vite dev server to be ready before loading — prevents blank white
    // page when Electron starts faster than Vite after `npm start`.
    await waitForBackend("http://localhost:5173", 20000);
    mainWindow.loadURL("http://localhost:5173");
    // Retry on load failure (Vite HMR reconnect after file watch)
    mainWindow.webContents.on("did-fail-load", (_, code, _desc, url) => {
      if (url.startsWith("http://localhost:5173")) {
        console.log("[main] Vite not ready, retrying in 1s…");
        setTimeout(() => mainWindow && mainWindow.loadURL("http://localhost:5173"), 1000);
      }
    });
  } else {
    const indexPath = path.join(UI_ROOT, "dist", "index.html");
    mainWindow.loadFile(indexPath);
  }

  // ── Context menu for copy / paste ─────────────────────────────────────────
  mainWindow.webContents.on("context-menu", (_, params) => {
    const menu = Menu.buildFromTemplate([
      { label: "Cut",        role: "cut",       enabled: params.editFlags.canCut },
      { label: "Copy",       role: "copy",      enabled: params.editFlags.canCopy },
      { label: "Paste",      role: "paste",     enabled: params.editFlags.canPaste },
      { label: "Select All", role: "selectAll", enabled: params.editFlags.canSelectAll },
      { type: "separator" },
      { label: "Copy Link Address", visible: !!params.linkURL,
        click: () => { require("electron").clipboard.writeText(params.linkURL); } },
    ]);
    menu.popup();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

// ── Application menu with Edit commands (enables Cmd+C/V/X/A on macOS) ───────

function buildAppMenu() {
  const isMac = process.platform === "darwin";
  const template = [
    ...(isMac ? [{ role: "appMenu" }] : []),
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        {
          label: "Toggle Developer Tools",
          accelerator: isMac ? "Cmd+Option+I" : "Ctrl+Shift+I",
          click: () => {
            if (mainWindow) mainWindow.webContents.toggleDevTools();
          },
        },
        { role: "reload" },
        { role: "togglefullscreen" },
      ],
    },
    { role: "windowMenu" },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ------------------------------------------------------------------
// IPC handlers
// ------------------------------------------------------------------

ipcMain.handle("fs:readFile", async (_, filePath) => {
  try {
    return { content: fs.readFileSync(filePath, "utf-8") };
  } catch (e) {
    return { error: e.message };
  }
});

ipcMain.handle("fs:writeFile", async (_, filePath, content) => {
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, "utf-8");
    return { success: true };
  } catch (e) {
    return { error: e.message };
  }
});

ipcMain.handle("fs:exists", async (_, filePath) => {
  return fs.existsSync(filePath);
});

ipcMain.handle("dialog:openFile", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openFile"],
    filters: [{ name: "Markdown", extensions: ["md"] }],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("dialog:openDirectory", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ["openDirectory"],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle("shell:openExternal", async (_, url) => {
  await shell.openExternal(url);
});

ipcMain.handle("app:getEnginePath", () => ENGINE_ROOT);

// Settings IPC — synchronous variant for preload bootstrapping
ipcMain.on("settings:getServerUrl", (event) => {
  event.returnValue = getServerUrl();
});

// Settings IPC — async variants for renderer use
ipcMain.handle("settings:getServerUrl", async () => getServerUrl());
ipcMain.handle("settings:setServerUrl", async (_, url) => {
  const trimmed = (url || "").trim();
  saveSettings({ serverUrl: trimmed });
  return { success: true, serverUrl: trimmed || `http://127.0.0.1:${BACKEND_PORT}` };
});

// ------------------------------------------------------------------
// App lifecycle
// ------------------------------------------------------------------

app.whenReady().then(async () => {
  buildAppMenu();
  _stopCalled = false;

  // Global shortcuts — work even when the window doesn't have keyboard focus
  const isMac = process.platform === "darwin";
  globalShortcut.register(isMac ? "Cmd+R" : "Ctrl+R", () => {
    if (mainWindow) mainWindow.webContents.reloadIgnoringCache();
  });
  globalShortcut.register(isMac ? "Cmd+Option+I" : "Ctrl+Shift+I", () => {
    if (mainWindow) mainWindow.webContents.toggleDevTools();
  });

  const serverUrl = getServerUrl();

  if (isLocalServer(serverUrl)) {
    // Local mode: reuse existing backend if already running (e.g. start_backend.sh),
    // otherwise spawn a fresh one. Never kill a process we didn't start.
    if (await isPortBusy(BACKEND_PORT)) {
      console.log(`[main] Backend already running on port ${BACKEND_PORT} — reusing it`);
    } else {
      startBackend();
      console.log(`[main] Local backend starting at ${serverUrl}`);
    }
  } else {
    // Remote mode: skip backend spawn entirely
    console.log(`[main] Connecting to remote server: ${serverUrl}`);
  }

  createWindow(serverUrl);

  app.on("activate", () => {
    // macOS: re-open window when clicking dock icon with no windows open
    if (BrowserWindow.getAllWindows().length === 0) createWindow(getServerUrl());
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

// before-quit fires on Cmd+Q / app.quit() — stopBackend guard prevents double-kill
app.on("before-quit", () => {
  globalShortcut.unregisterAll();
  stopBackend();
});
