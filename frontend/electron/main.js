/**
 * frontend/electron/main.js
 * AsimNexus — Electron Desktop App Main Process
 *
 * Wraps the React frontend in a native desktop window with:
 *   - System tray integration
 *   - Auto-updater
 *   - Native notifications
 *   - Custom title bar
 *   - Keyboard shortcuts
 *   - Background running
 */

const { app, BrowserWindow, Tray, Menu, nativeImage, Notification,
    ipcMain, shell, globalShortcut } = require('electron');
const path = require('path');
const { autoUpdater } = require('electron-updater');

// ── Configuration ────────────────────────────────────────────────────────

const IS_DEV = process.env.NODE_ENV === 'development' || !app.isPackaged;
const DEV_SERVER_URL = process.env.DEV_SERVER_URL || 'http://localhost:3000';
const PROD_APP_URL = process.env.PROD_APP_URL || 'https://asimnexus.app';
const APP_NAME = 'ASIMNEXUS';
const TRAY_ICON_SIZE = 16;

let mainWindow = null;
let tray = null;
let isQuitting = false;

// ── Main Window ──────────────────────────────────────────────────────────

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 900,
        minHeight: 600,
        title: APP_NAME,
        icon: path.join(__dirname, 'icons', 'icon.png'),
        show: false,
        backgroundColor: '#0f172a',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            sandbox: false,
        },
        frame: true,
        titleBarStyle: 'default',
    });

    // Load the app
    if (IS_DEV) {
        mainWindow.loadURL(DEV_SERVER_URL);
        mainWindow.webContents.openDevTools({ mode: 'detach' });
    } else {
        mainWindow.loadURL(PROD_APP_URL);
    }

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
        if (!IS_DEV) {
            checkForUpdates();
        }
    });

    // Minimize to tray instead of closing
    mainWindow.on('close', (event) => {
        if (!isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });

    // Open external links in default browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Register IPC handlers
    registerIpcHandlers();
}

// ── System Tray ──────────────────────────────────────────────────────────

function createTray() {
    // Create a simple 16x16 tray icon
    const icon = nativeImage.createEmpty();
    tray = new Tray(icon);

    const contextMenu = Menu.buildFromTemplate([
        {
            label: `Open ${APP_NAME}`,
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                }
            },
        },
        { type: 'separator' },
        {
            label: 'Check for Updates',
            click: () => checkForUpdates(true),
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true;
                app.quit();
            },
        },
    ]);

    tray.setToolTip(APP_NAME);
    tray.setContextMenu(contextMenu);

    tray.on('double-click', () => {
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

// ── Auto-Updater ─────────────────────────────────────────────────────────

function checkForUpdates(manual = false) {
    if (manual) {
        autoUpdater.checkForUpdatesAndNotify();
    } else {
        autoUpdater.checkForUpdates();
    }
}

autoUpdater.on('update-available', (info) => {
    if (mainWindow) {
        mainWindow.webContents.send('update-available', info);
    }
    showNotification('Update Available', `Version ${info.version} is ready to download.`);
});

autoUpdater.on('update-downloaded', (info) => {
    if (mainWindow) {
        mainWindow.webContents.send('update-downloaded', info);
    }
    showNotification('Update Ready', 'Restart to apply the update.');

    // Prompt user to restart
    const dialogOpts = {
        type: 'info',
        buttons: ['Restart', 'Later'],
        title: 'Update Ready',
        message: `Version ${info.version} has been downloaded. Restart to apply?`,
    };
    const { dialog } = require('electron');
    dialog.showMessageBox(mainWindow, dialogOpts).then(({ response }) => {
        if (response === 0) {
            autoUpdater.quitAndInstall();
        }
    });
});

autoUpdater.on('error', (err) => {
    console.error('Auto-updater error:', err);
});

// ── Notifications ────────────────────────────────────────────────────────

function showNotification(title, body) {
    if (Notification.isSupported()) {
        const notification = new Notification({ title, body });
        notification.on('click', () => {
            if (mainWindow) {
                mainWindow.show();
                mainWindow.focus();
            }
        });
        notification.show();
    }
}

// ── IPC Handlers ─────────────────────────────────────────────────────────

function registerIpcHandlers() {
    // Get app version
    ipcMain.handle('get-app-version', () => app.getVersion());

    // Get platform info
    ipcMain.handle('get-platform', () => ({
        platform: process.platform,
        arch: process.arch,
        electronVersion: process.versions.electron,
        chromeVersion: process.versions.chrome,
        nodeVersion: process.versions.node,
    }));

    // Show notification from renderer
    ipcMain.handle('show-notification', (_event, { title, body }) => {
        showNotification(title, body);
    });

    // Set badge count (macOS)
    ipcMain.handle('set-badge', (_event, count) => {
        if (process.platform === 'darwin') {
            app.setBadgeCount(count);
        }
    });

    // Open external URL
    ipcMain.handle('open-external', (_event, url) => {
        shell.openExternal(url);
    });

    // Minimize to tray
    ipcMain.handle('minimize-to-tray', () => {
        if (mainWindow) {
            mainWindow.hide();
        }
    });

    // Relaunch app
    ipcMain.handle('relaunch-app', () => {
        autoUpdater.quitAndInstall();
    });
}

// ── Keyboard Shortcuts ───────────────────────────────────────────────────

function registerShortcuts() {
    globalShortcut.register('CommandOrControl+Shift+N', () => {
        if (mainWindow) {
            mainWindow.webContents.send('shortcut', 'new-chat');
        }
    });

    globalShortcut.register('CommandOrControl+Shift+F', () => {
        if (mainWindow) {
            mainWindow.webContents.send('shortcut', 'search');
        }
    });

    globalShortcut.register('CommandOrControl+Shift+I', () => {
        if (mainWindow) {
            mainWindow.webContents.send('shortcut', 'toggle-sidebar');
        }
    });
}

// ── App Lifecycle ────────────────────────────────────────────────────────

app.whenReady().then(() => {
    createMainWindow();
    createTray();
    registerShortcuts();

    app.on('activate', () => {
        if (mainWindow) {
            mainWindow.show();
        } else {
            createMainWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    isQuitting = true;
    globalShortcut.unregisterAll();
});

app.on('will-quit', () => {
    globalShortcut.unregisterAll();
});
