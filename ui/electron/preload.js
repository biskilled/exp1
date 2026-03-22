/**
 * electron/preload.js — contextBridge IPC shim
 *
 * Runs in an isolated context before the renderer loads. Injects window.__BACKEND_URL__
 * synchronously and exposes window.electronAPI (file system, dialogs, shell, settings,
 * terminal) via contextBridge — no direct Node.js access from the renderer.
 */

const { contextBridge, ipcRenderer } = require("electron");

// Inject backend URL into renderer world before any page scripts run.
// ipcRenderer.sendSync is used here because contextBridge runs synchronously.
const _serverUrl = ipcRenderer.sendSync("settings:getServerUrl");
contextBridge.exposeInMainWorld("__BACKEND_URL__", _serverUrl);

contextBridge.exposeInMainWorld("electronAPI", {
  // File system
  readFile: (filePath) => ipcRenderer.invoke("fs:readFile", filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke("fs:writeFile", filePath, content),
  fileExists: (filePath) => ipcRenderer.invoke("fs:exists", filePath),

  // Dialogs
  openFile: () => ipcRenderer.invoke("dialog:openFile"),
  openDirectory: () => ipcRenderer.invoke("dialog:openDirectory"),

  // Shell
  openExternal: (url) => ipcRenderer.invoke("shell:openExternal", url),

  // App info
  getEnginePath: () => ipcRenderer.invoke("app:getEnginePath"),

  // Server settings
  settings: {
    getServerUrl: () => ipcRenderer.invoke("settings:getServerUrl"),
    setServerUrl: (url) => ipcRenderer.invoke("settings:setServerUrl", url),
  },

  // Terminal (spawned via terminal.js)
  terminal: {
    spawn: (options) => ipcRenderer.invoke("terminal:spawn", options),
    write: (id, data) => ipcRenderer.send("terminal:write", id, data),
    resize: (id, cols, rows) => ipcRenderer.send("terminal:resize", id, cols, rows),
    kill: (id) => ipcRenderer.invoke("terminal:kill", id),
    onData: (id, callback) =>
      ipcRenderer.on(`terminal:data:${id}`, (_, data) => callback(data)),
    onExit: (id, callback) =>
      ipcRenderer.once(`terminal:exit:${id}`, (_, code) => callback(code)),
  },
});
