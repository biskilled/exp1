/**
 * Electron preload script.
 *
 * Exposes a safe API to the renderer via window.electronAPI.
 * Uses contextBridge to avoid exposing Node.js directly.
 */

const { contextBridge, ipcRenderer } = require("electron");

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
