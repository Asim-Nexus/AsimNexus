const { ipcRenderer } = require('electron');

// ASIMNEXUS Desktop App - Renderer Process
// Connects to backend via IPC with proper loading/error states

// API Client for Renderer Process
const asimAPI = {
  async health() {
    return await ipcRenderer.invoke('asim:health');
  },

  async chat(message, useWorldOS = true) {
    return await ipcRenderer.invoke('asim:chat', message, useWorldOS);
  },

  async getWorldOSStatus() {
    return await ipcRenderer.invoke('asim:world_os_status');
  },

  async getWorldOSAgents() {
    return await ipcRenderer.invoke('asim:world_os_agents');
  },

  async getAnalytics() {
    return await ipcRenderer.invoke('asim:analytics');
  },

  async getSecurity() {
    return await ipcRenderer.invoke('asim:security');
  },

  async getAgents() {
    return await ipcRenderer.invoke('asim:agents');
  },

  async getFounders() {
    return await ipcRenderer.invoke('asim:founders');
  }
};

// DOM element helpers
function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

function setMetricValue(metricClass, value) {
  const el = $(`.metric-card.${metricClass} .metric-value`);
  if (el) el.textContent = value;
}

function setMetricError(metricClass) {
  const el = $(`.metric-card.${metricClass} .metric-value`);
  if (el) {
    el.textContent = '—';
    el.style.color = '#ef4444';
  }
}

function setMetricLoading(metricClass) {
  const el = $(`.metric-card.${metricClass} .metric-value`);
  if (el) el.textContent = '...';
}

function showLoading() {
  const grid = $('.metrics-grid');
  if (grid) grid.style.opacity = '0.5';
  const statusEl = $('#connection-status');
  if (statusEl) {
    statusEl.textContent = 'Connecting...';
    statusEl.className = 'status-pending';
  }
}

function hideLoading() {
  const grid = $('.metrics-grid');
  if (grid) grid.style.opacity = '1';
}

function showError(message) {
  const errorEl = $('#error-banner');
  if (errorEl) {
    errorEl.textContent = '⚠ ' + message;
    errorEl.style.display = 'block';
  }
  const statusEl = $('#connection-status');
  if (statusEl) {
    statusEl.textContent = 'Disconnected';
    statusEl.className = 'status-error';
  }
}

function clearError() {
  const errorEl = $('#error-banner');
  if (errorEl) errorEl.style.display = 'none';
  const statusEl = $('#connection-status');
  if (statusEl) {
    statusEl.textContent = 'Connected';
    statusEl.className = 'status-ok';
  }
}

// Update dashboard with real data from backend
async function updateDashboard() {
  try {
    showLoading();
    clearError();

    // Get analytics / status data
    const analytics = await asimAPI.getAnalytics();
    if (analytics && !analytics.error) {
      setMetricValue('cpu', (analytics.cpu_usage || '—') + '%');
      setMetricValue('memory', (analytics.ram_usage || '—') + '%');
      setMetricValue('network', (analytics.network_usage || analytics.status || '—'));
      setMetricValue('storage', (analytics.disk_usage || '—') + '%');
    } else {
      // Fallback: try health endpoint
      const health = await asimAPI.health();
      if (health && !health.error) {
        setMetricValue('cpu', '—');
        setMetricValue('memory', '—');
        setMetricValue('network', health.status || '—');
        setMetricValue('storage', '—');
      } else {
        throw new Error(health?.error || 'No data from backend');
      }
    }

    // Get World OS status
    const worldOSStatus = await asimAPI.getWorldOSStatus();
    if (worldOSStatus && !worldOSStatus.error) {
      const statusEl = $('#worldos-status');
      if (statusEl) {
        statusEl.textContent = worldOSStatus.status || 'Active';
        statusEl.className = 'status-ok';
      }
    }

    hideLoading();
  } catch (error) {
    console.error('Error updating dashboard:', error);
    hideLoading();
    showError('Backend unavailable: ' + (error.message || 'connection failed'));
    setMetricError('cpu');
    setMetricError('memory');
    setMetricError('network');
    setMetricError('storage');
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  console.log('ASIMNEXUS Desktop App initialized');

  // Initial load
  await updateDashboard();

  // Periodic refresh every 5 seconds
  setInterval(() => {
    updateDashboard();
  }, 5000);
});

console.log('ASIMNEXUS Desktop App renderer loaded');
