const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

// ASIMNEXUS Backend API Configuration
const API_BASE_URL = 'http://localhost:8000';

// API Client for ASIMNEXUS
const asimAPI = {
  // Health check
  async health() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/health`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // Chat
  async chat(message, useWorldOS = true) {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        message,
        use_world_os: useWorldOS
      });
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // World OS
  async getWorldOSStatus() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/world_os/status`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  async getWorldOSAgents() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/world_os/agents`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // Analytics
  async getAnalyticsOverview() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/analytics/overview`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // Security
  async getSecurityStatus() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/security/status`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // Agents
  async getAgents() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/agents`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  },

  // Founders
  async getFounders() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/founders`);
      return response.data;
    } catch (error) {
      return { error: error.message };
    }
  }
};

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile('index.html');
}

// IPC Handlers for Renderer Process
ipcMain.handle('asim:health', async () => {
  return await asimAPI.health();
});

ipcMain.handle('asim:chat', async (event, message, useWorldOS) => {
  return await asimAPI.chat(message, useWorldOS);
});

ipcMain.handle('asim:world_os_status', async () => {
  return await asimAPI.getWorldOSStatus();
});

ipcMain.handle('asim:world_os_agents', async () => {
  return await asimAPI.getWorldOSAgents();
});

ipcMain.handle('asim:analytics', async () => {
  return await asimAPI.getAnalyticsOverview();
});

ipcMain.handle('asim:security', async () => {
  return await asimAPI.getSecurityStatus();
});

ipcMain.handle('asim:agents', async () => {
  return await asimAPI.getAgents();
});

ipcMain.handle('asim:founders', async () => {
  return await asimAPI.getFounders();
});

app.whenReady().then(() => {
  createWindow();

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
