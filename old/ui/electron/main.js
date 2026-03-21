/**
 * Electron main process.
 *
 * Responsibilities:
 * - Create the BrowserWindow
 * - Spawn the FastAPI backend (python3.12 -m uvicorn backend.main:app)
 * - IPC handlers: fs read/write, shell open, dialog
 * - Gracefully kill backend on quit
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

const ENGINE_ROOT = path.resolve(__dirname, "../../..");  // old/ui/electron → aicli/
const UI_ROOT = path.resolve(__dirname, "..");            // old/ui/electron → old/ui/
const BACKEND_DIR = path.join(ENGINE_ROOT, "backend");    // aicli/backend/
const FRONTEND_DIR = path.join(UI_ROOT, "frontend");      // old/ui/frontend/

let mainWindow = null;
let backendProcess = null;
const BACKEND_PORT = 8000;

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
  backendProcess.on("error", (err) => {
    console.error(`[backend] spawn failed: ${err.message} (cwd: ${BACKEND_DIR})`);
    backendProcess = null;
  });
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

async function waitForBackend(maxWaitMs = 30000) {
  const http = require("http");
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const ok = await new Promise((resolve) => {
      const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on("error", () => resolve(false));
      req.end();
    });
    if (ok) return true;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

// ------------------------------------------------------------------
// Window
// ------------------------------------------------------------------

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Wait for backend before loading
  const ready = await waitForBackend();
  if (!ready) {
    console.error("Backend failed to start");
  }

  // In development, load Vite dev server; in production, load built index.html
  const isDev = process.env.NODE_ENV === "development";
  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    // DevTools NOT opened automatically — use Cmd+Option+I / Ctrl+Shift+I to open
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

// ------------------------------------------------------------------
// App lifecycle
// ------------------------------------------------------------------

app.whenReady().then(async () => {
  buildAppMenu();
  _stopCalled = false;         // reset guard for this app lifetime
  await freePort(BACKEND_PORT); // kill any stale backend before spawning
  startBackend();
  createWindow();

  app.on("activate", () => {
    // macOS: re-open window when clicking dock icon with no windows open
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});

// before-quit fires on Cmd+Q / app.quit() — stopBackend guard prevents double-kill
app.on("before-quit", stopBackend);
