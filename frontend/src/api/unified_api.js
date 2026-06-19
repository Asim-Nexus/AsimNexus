/**
 * ASIMNEXUS Unified API Client
 * =============================
 * Centralized API client for all frontend components.
 * Provides unified interface to all backend services.
 *
 * IMPORTANT: Auth keys MUST match asimnexus.js for cross-file compatibility.
 *   - localStorage keys: asimnexus_token / asimnexus_user
 *   - Env var: REACT_APP_API_URL (falls back to http://localhost:8000)
 */

import axios from 'axios';

// API Configuration — single source of truth for base URL
// NOTE: asimnexus.js also reads REACT_APP_API_URL with fallback http://localhost:8000
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8081';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || ((typeof window !== 'undefined' && window.location) ? ((window.location.protocol === 'https:') ? 'wss://' : 'ws://') + window.location.host : '');

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — uses same localStorage keys as asimnexus.js
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('asimnexus_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor — retry on timeout (max 3 retries)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.code === 'ECONNABORTED' && !originalRequest._retry) {
      originalRequest._retry = true;
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

      if (originalRequest._retryCount < 3) {
        console.log(`Retrying request (${originalRequest._retryCount}/3)...`);
        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export { API_BASE_URL, WS_BASE_URL };

// ─── AUTH HELPERS ──────────────────────────────────────
// Keys MUST match asimnexus.js so both clients share the same auth session.
export const getStoredToken = () => localStorage.getItem('asimnexus_token');
export const getStoredUser = () => {
  try { return JSON.parse(localStorage.getItem('asimnexus_user') || 'null'); }
  catch { return null; }
};
export const setAuth = (token, user) => {
  localStorage.setItem('asimnexus_token', token);
  localStorage.setItem('asimnexus_user', JSON.stringify(user));
};
export const clearAuth = () => {
  localStorage.removeItem('asimnexus_token');
  localStorage.removeItem('asimnexus_user');
};

// ─── AUTH API ──────────────────────────────────────────
export const authAPI = {
  register: async (displayName, email, password, phone, countryCode, nationalId) => {
    const response = await apiClient.post('/auth/register', {
      display_name: displayName, email, password,
      phone: phone || null,
      country_code: countryCode || 'NP',
      national_id: nationalId || null,
    });
    if (response.data?.success) {
      setAuth(response.data.token, response.data.user);
    }
    return response.data;
  },

  login: async (email, password) => {
    const response = await apiClient.post('/auth/login', { email, password });
    if (response.data?.success) {
      setAuth(response.data.token, response.data.user);
    }
    return response.data;
  },

  me: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  logout: () => clearAuth(),
};

// ─── PERSONAL OS API ───────────────────────────────────
export const personalOSAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/personal/status');
    return response.data;
  },
  getClones: async () => {
    const response = await apiClient.get('/personal/clones');
    return response.data;
  },
  setMode: async (mode) => {
    const response = await apiClient.post('/api/universe/set', { mode });
    return response.data;
  },
  setTheme: async (theme) => {
    const response = await apiClient.post('/api/theme/set', { theme });
    return response.data;
  },
};

// ─── MESH API ──────────────────────────────────────────
export const meshAPI = {
  getNodes: async () => {
    const response = await apiClient.get('/mesh/nodes');
    return response.data;
  },
  joinMesh: async (name, country = 'NP') => {
    const response = await apiClient.post('/api/infrastructure/mesh/join', {
      user_id: name,
      country,
    });
    return response.data;
  },
};

// ─── CHAT API (fixed URLs) ─────────────────────────────
export const chatAPI = {
  sendMessage: async (message, options = {}) => {
    const response = await apiClient.post('/llm/chat', {
      message,
      max_tokens: options.maxTokens || 512,
      temperature: options.temperature || 0.7,
    });
    return response.data;
  },

  getConversationHistory: async () => {
    // Stored locally in PersonalOS — no server call needed
    return { history: [] };
  },

  clearConversation: async () => {
    return { success: true };
  }
};

/**
 * System Metrics API
 */
export const systemMetricsAPI = {
  getCurrentMetrics: async () => {
    const response = await apiClient.get('/status');
    return response.data;
  },

  getHistoricalMetrics: async (timeRange = '1h') => {
    const response = await apiClient.get('/status');
    return response.data;
  }
};

/**
 * File Manager API
 */
export const fileManagerAPI = {
  listFiles: async (path = '.') => {
    const response = await apiClient.get('/files/list', { params: { path } });
    return response.data;
  },

  readFile: async (path) => {
    const response = await apiClient.get('/files/read', { params: { path } });
    return response.data;
  },

  writeFile: async (path, content) => {
    const response = await apiClient.post('/files/write', { path, content });
    return response.data;
  },

  deleteFile: async (path) => {
    const response = await apiClient.delete('/files/delete', { params: { path } });
    return response.data;
  },

  createDirectory: async (path) => {
    const response = await apiClient.post('/files/create_directory', { path });
    return response.data;
  },

  searchFiles: async (query) => {
    const response = await apiClient.get('/files/search', { params: { query } });
    return response.data;
  }
};

/**
 * Codebase API
 */
export const codebaseAPI = {
  indexCodebase: async () => {
    const response = await apiClient.get('/codebase/index');
    return response.data;
  },

  searchCodebase: async (query) => {
    const response = await apiClient.get('/codebase/search', { params: { query } });
    return response.data;
  },

  getCodebaseSummary: async () => {
    const response = await apiClient.get('/codebase/summary');
    return response.data;
  },

  getFileContent: async (path) => {
    const response = await apiClient.get(`/codebase/file/${encodeURIComponent(path)}`);
    return response.data;
  }
};

/**
 * Terminal API
 */
export const terminalAPI = {
  executeCommand: async (command) => {
    const response = await apiClient.post('/terminal/execute', { command });
    return response.data;
  }
};

/**
 * Automation API
 */
export const automationAPI = {
  createTask: async (task) => {
    const response = await apiClient.post('/automation/create', task);
    return response.data;
  },

  listTasks: async () => {
    const response = await apiClient.get('/automation/list');
    return response.data;
  },

  executeTask: async (taskId) => {
    const response = await apiClient.post('/automation/execute', { task_id: taskId });
    return response.data;
  },

  deleteTask: async (taskId) => {
    const response = await apiClient.delete(`/automation/${taskId}`);
    return response.data;
  }
};

/**
 * Multi-Agent API
 */
export const multiAgentAPI = {
  getAgents: async () => {
    const response = await apiClient.get('/personal/clones');
    return response.data;
  },

  getAgentStatus: async (agentId) => {
    const response = await apiClient.get('/personal/status');
    return response.data;
  },

  consultAgent: async (agentId, message) => {
    const response = await apiClient.post('/llm/chat', { message });
    return response.data;
  },

  getFounderClones: async () => {
    const response = await apiClient.get('/personal/clones');
    return response.data;
  },

  consultFounder: async (founderId, message) => {
    const response = await apiClient.post('/llm/chat', { message });
    return response.data;
  }
};

/**
 * World OS API
 */
export const worldOSAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/status');
    return response.data;
  },

  getAgents: async () => {
    const response = await apiClient.get('/personal/clones');
    return response.data;
  },

  getTasks: async () => {
    const response = await apiClient.get('/status');
    return response.data;
  },

  getMemory: async () => {
    const response = await apiClient.get('/personal/status');
    return response.data;
  },

  searchMemory: async (query) => {
    const response = await apiClient.post('/llm/chat', { message: query });
    return response.data;
  },

  processRequest: async (request) => {
    const response = await apiClient.post('/llm/chat', { message: request.message || JSON.stringify(request) });
    return response.data;
  }
};

/**
 * Analytics API
 */
export const analyticsAPI = {
  getOverview: async () => {
    const response = await apiClient.get('/api/analytics/overview');
    return response.data;
  },

  getPerformance: async () => {
    const response = await apiClient.get('/api/analytics/performance');
    return response.data;
  },

  getUsage: async () => {
    const response = await apiClient.get('/api/analytics/usage');
    return response.data;
  }
};

/**
 * Security API
 */
export const securityAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/api/security/status');
    return response.data;
  },

  getVulnerabilities: async () => {
    const response = await apiClient.get('/api/security/vulnerabilities');
    return response.data;
  },

  runScan: async () => {
    const response = await apiClient.post('/api/security/scan');
    return response.data;
  }
};

/**
 * Virtual Office API
 */
export const virtualOfficeAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/api/virtual_office/status');
    return response.data;
  },

  getRooms: async () => {
    const response = await apiClient.get('/api/virtual_office/rooms');
    return response.data;
  },

  joinRoom: async (roomId) => {
    const response = await apiClient.post('/api/virtual_office/join', { room_id: roomId });
    return response.data;
  },

  leaveRoom: async (roomId) => {
    const response = await apiClient.post('/api/virtual_office/leave', { room_id: roomId });
    return response.data;
  }
};

/**
 * Autonomous API
 */
export const autonomousAPI = {
  getStatus: async () => {
    const response = await apiClient.get('/api/autonomous/status');
    return response.data;
  },

  enableAutopilot: async () => {
    const response = await apiClient.post('/api/autonomous/enable');
    return response.data;
  },

  disableAutopilot: async () => {
    const response = await apiClient.post('/api/autonomous/disable');
    return response.data;
  }
};

/**
 * Human Digital Twin (HDT) API
 */
export const hdtAPI = {
  getMyTwin: async () => {
    const response = await apiClient.get('/hdt/me');
    return response.data;
  },

  update: async (updates) => {
    const response = await apiClient.post('/hdt/update', updates);
    return response.data;
  },

  getTopClones: async () => {
    const response = await apiClient.get('/hdt/top-clones');
    return response.data;
  },
};

/**
 * Level-3 ZKP Human Confirmation API
 */
export const zkpAPI = {
  listPending: async () => {
    const response = await apiClient.get('/zkp/pending');
    return response.data;
  },

  confirm: async (token) => {
    const response = await apiClient.post(`/zkp/confirm/${token}`);
    return response.data;
  },

  reject: async (token) => {
    const response = await apiClient.post(`/zkp/reject/${token}`);
    return response.data;
  },

  getStatus: async (token) => {
    const response = await apiClient.get(`/zkp/status/${token}`);
    return response.data;
  },
};

/**
 * World Clones API — 15 World-Role Founder Clones
 */
export const worldClonesAPI = {
  listClones: async () => {
    const response = await apiClient.get('/clones/list');
    return response.data;
  },

  chat: async (message) => {
    const response = await apiClient.post('/clones/chat', { message });
    return response.data;
  },

  directMessage: async (roleName, message) => {
    const response = await apiClient.post(`/clones/direct/${encodeURIComponent(roleName)}`, { message });
    return response.data;
  },

  setAgentMode: async (enabled) => {
    const response = await apiClient.post(`/clones/agent-mode?enabled=${enabled}`);
    return response.data;
  },
};

/**
 * Health API
 */
export const healthAPI = {
  check: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
  localLLM: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  }
};

/**
 * WebSocket Manager
 */
class WebSocketManager {
  constructor() {
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
  }

  connect() {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/ws`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected');
        // Request clone status immediately on connect
        this.requestCloneStatus();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('reconnect_failed');
    }
  }

  requestCloneStatus() {
    this.send({ type: 'clone_status_request' });
  }

  zkpConfirm(tokenId) {
    this.send({ type: 'zkp_confirm', token_id: tokenId });
  }

  zkpReject(tokenId) {
    this.send({ type: 'zkp_reject', token_id: tokenId });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Create singleton instance
const wsManager = new WebSocketManager();

// Auto-connect on load
if (typeof window !== 'undefined') {
  wsManager.connect();
}

/**
 * Export unified API object
 */
export const unifiedAPI = {
  auth: authAPI,
  personalOS: personalOSAPI,
  mesh: meshAPI,
  chat: chatAPI,
  systemMetrics: systemMetricsAPI,
  fileManager: fileManagerAPI,
  codebase: codebaseAPI,
  terminal: terminalAPI,
  automation: automationAPI,
  multiAgent: multiAgentAPI,
  worldOS: worldOSAPI,
  analytics: analyticsAPI,
  security: securityAPI,
  virtualOffice: virtualOfficeAPI,
  autonomous: autonomousAPI,
  health: healthAPI,
  websocket: wsManager
};

export default unifiedAPI;
