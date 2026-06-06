/**
 * ASIMNEXUS Desktop Application - Main Process
 * Electron main process for desktop app
 */

const { app, BrowserWindow, ipcMain, Menu, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store();
let mainWindow;

/**
 * Create main application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            enableRemoteModule: false,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'assets', 'icon.png'),
        titleBarStyle: 'default',
        backgroundColor: '#1a1a2e'
    });

    // Load the app
    mainWindow.loadFile(path.join(__dirname, 'electron', 'index.html'));

    // Open DevTools in development
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/**
 * Create application menu
 */
function createMenu() {
    const template = [
        {
            label: 'ASIMNEXUS',
            submenu: [
                {
                    label: 'About ASIMNEXUS',
                    click: () => {
                        shell.openExternal('https://asimnexus.ai');
                    }
                },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Window',
            submenu: [
                { role: 'minimize' },
                { role: 'close' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: () => {
                        shell.openExternal('https://docs.asimnexus.ai');
                    }
                },
                {
                    label: 'Report Issue',
                    click: () => {
                        shell.openExternal('https://github.com/asimnexus/asimnexus/issues');
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

/**
 * IPC handlers
 */
function setupIpcHandlers() {
    // Get app version
    ipcMain.handle('get-app-version', () => {
        return app.getVersion();
    });

    // Get stored settings
    ipcMain.handle('get-settings', () => {
        return store.get('settings', {});
    });

    // Save settings
    ipcMain.handle('save-settings', (event, settings) => {
        store.set('settings', settings);
        return true;
    });

    // Open external link
    ipcMain.handle('open-external', (event, url) => {
        shell.openExternal(url);
        return true;
    });

    // Minimize window
    ipcMain.handle('minimize-window', () => {
        if (mainWindow) {
            mainWindow.minimize();
        }
        return true;
    });

    // Maximize window
    ipcMain.handle('maximize-window', () => {
        if (mainWindow) {
            if (mainWindow.isMaximized()) {
                mainWindow.unmaximize();
            } else {
                mainWindow.maximize();
            }
        }
        return true;
    });

    // Close window
    ipcMain.handle('close-window', () => {
        if (mainWindow) {
            mainWindow.close();
        }
        return true;
    });
}

/**
 * App event handlers
 */
app.whenReady().then(() => {
    createWindow();
    createMenu();
    setupIpcHandlers();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Cleanup before quit
    console.log('ASIMNEXUS Desktop shutting down...');
});
