/**
 * electron/terminal.js — node-pty terminal session manager
 *
 * Handles IPC events for terminal:spawn / terminal:write / terminal:resize / terminal:kill.
 * Creates PTY sessions (xterm-256color) and forwards data/exit events back to the renderer.
 * Gracefully stubs all handlers if node-pty is not installed.
 */

const { ipcMain } = require("electron");
const path = require("path");

// node-pty is optional — gracefully skip if not installed
let pty = null;
try {
  pty = require("node-pty");
} catch (e) {
  console.warn("[terminal] node-pty not installed — terminal disabled. Run: npm install node-pty");
}

const ENGINE_ROOT = path.resolve(__dirname, "../..");
const sessions = new Map();
let nextId = 1;

// ------------------------------------------------------------------

if (pty) {
  ipcMain.handle("terminal:spawn", (event, options = {}) => {
    const id = String(nextId++);
    const shell = process.platform === "win32" ? "cmd.exe" : (process.env.SHELL || "/bin/zsh");
    const cols = options.cols || 120;
    const rows = options.rows || 40;

    // Default: open aicli REPL
    const python = process.platform === "win32" ? "python" : "python3.12";
    const cliArgs = options.shell ? [] : [path.join(ENGINE_ROOT, "cli.py")];
    const command = options.shell ? shell : python;

    const proc = pty.spawn(command, cliArgs, {
      name: "xterm-color",
      cols,
      rows,
      cwd: ENGINE_ROOT,
      env: Object.assign({}, process.env, {
        PYTHONPATH: ENGINE_ROOT,
        TERM: "xterm-256color",
      }),
    });

    sessions.set(id, proc);

    proc.onData((data) => {
      event.sender.send(`terminal:data:${id}`, data);
    });

    proc.onExit(({ exitCode }) => {
      sessions.delete(id);
      event.sender.send(`terminal:exit:${id}`, exitCode);
    });

    return { id };
  });

  ipcMain.on("terminal:write", (_, id, data) => {
    const proc = sessions.get(id);
    if (proc) proc.write(data);
  });

  ipcMain.on("terminal:resize", (_, id, cols, rows) => {
    const proc = sessions.get(id);
    if (proc) proc.resize(cols, rows);
  });

  ipcMain.handle("terminal:kill", (_, id) => {
    const proc = sessions.get(id);
    if (proc) {
      proc.kill();
      sessions.delete(id);
    }
    return { killed: id };
  });
} else {
  // Stub handlers when node-pty is not available
  ipcMain.handle("terminal:spawn", () => ({ id: "stub", error: "node-pty not installed" }));
  ipcMain.on("terminal:write", () => {});
  ipcMain.on("terminal:resize", () => {});
  ipcMain.handle("terminal:kill", () => ({ killed: null }));
}
