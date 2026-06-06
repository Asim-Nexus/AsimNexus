/**
 * ASIMNEXUS Desktop Application - Preload Script
 * Exposes safe APIs to renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose protected methods that allow the renderer process to use
 * the ipcRenderer without exposing the entire object
 */
contextBridge.exposeInMainWorld('asimnexusAPI', {
    // App info
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    
    // Settings
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    
    // Window controls
    minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
    maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
    closeWindow: () => ipcRenderer.invoke('close-window'),
    
    // External links
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    
    // System info
    platform: process.platform,
    arch: process.arch
});

/**
 * Expose node versions
 */
contextBridge.exposeInMainWorld('nodeVersions', {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
});
