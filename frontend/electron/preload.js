/**
 * frontend/electron/preload.js
 * AsimNexus — Electron Preload Script
 *
 * Exposes a safe `electronAPI` bridge to the renderer process
 * via contextBridge, keeping Node.js APIs isolated.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // App info
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    getPlatform: () => ipcRenderer.invoke('get-platform'),

    // Notifications
    showNotification: (title, body) =>
        ipcRenderer.invoke('show-notification', { title, body }),

    // Badge (macOS)
    setBadge: (count) => ipcRenderer.invoke('set-badge', count),

    // External links
    openExternal: (url) => ipcRenderer.invoke('open-external', url),

    // Window management
    minimizeToTray: () => ipcRenderer.invoke('minimize-to-tray'),
    relaunchApp: () => ipcRenderer.invoke('relaunch-app'),

    // Event listeners
    onUpdateAvailable: (callback) =>
        ipcRenderer.on('update-available', (_event, info) => callback(info)),
    onUpdateDownloaded: (callback) =>
        ipcRenderer.on('update-downloaded', (_event, info) => callback(info)),
    onShortcut: (callback) =>
        ipcRenderer.on('shortcut', (_event, name) => callback(name)),

    // Cleanup
    removeAllListeners: (channel) =>
        ipcRenderer.removeAllListeners(channel),
});
