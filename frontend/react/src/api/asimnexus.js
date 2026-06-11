/**
 * ASIMNEXUS API Integration Layer
 * Connects React frontend to Python backend
 *
 * API host is configured via `REACT_APP_API_URL` or the unified API client.
 *
 * === API CONTRACT CLEANUP (RC-1) ===
 * All frontend routes have been cross-referenced against simple_backend.py (265 routes).
 * This file now calls ONLY backend routes that actually exist.
 * See docs/API_CONTRACT.md for the canonical route map.
 *
 * Auth flow: POST /auth/login and POST /auth/register expect JSON body with {email, password}.
 * Health: GET /health (aliased as /api/status, /api/db/health).
 * Chat: POST /api/chat (aliased as /chat, /llm/chat).
 */

import axios from 'axios';

// API base URL from environment variable (falls back to localhost:8000)
const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8081';

const api = axios.create({
  baseURL: BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout for LLM generation
});

// Request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('asimnexus_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for unified error handling
api.interceptors.response.use(
  (response) => {
    // Normalize successful responses: wrap non-standard shapes
    if (response.data && typeof response.data === 'object' && !response.data.success && !response.data.status) {
      response.data = { success: true, ...response.data };
    }
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data;

    // Auth failures — clear token on 401
    if (status === 401) {
      console.warn('[API] Unauthorized — clearing auth token');
      localStorage.removeItem('asimnexus_token');
      localStorage.removeItem('asimnexus_user');
    }

    // Build a structured error object
    const apiError = {
      status,
      message: data?.detail || data?.message || error.message || 'Unknown API error',
      data: data || null,
      config: {
        url: error.config?.url,
        method: error.config?.method,
      },
    };

    console.warn(`[API] ${error.config?.method?.toUpperCase() || '??'} ${error.config?.url || '??'} → ${status || 'ERR'}`, apiError.message);
    return Promise.reject(apiError);
  }
);

// ─── AUTH HELPERS ──────────────────────────────────────────────
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

// ═══════════════════════════════════════════════════════════════════
// AUTHENTICATION API
// Backend routes: POST /auth/login, POST /auth/register, GET /auth/me
// ═══════════════════════════════════════════════════════════════════

export const authAPI = {
  /** POST /auth/login — expects JSON body {email, password} */
  login: (email, password) =>
    api.post('/auth/login', { email, password }).then(res => {
      if (res.data?.success) {
        setAuth(res.data.token, res.data.user);
      }
      return res.data;
    }),

  /** POST /auth/register — expects JSON body {email, password, display_name?, phone?, country_code?, national_id?} */
  register: (displayName, email, password, phone = null, countryCode = 'NP', nationalId = null) =>
    api.post('/auth/register', {
      email,
      password,
      display_name: displayName,
      phone,
      country_code: countryCode,
      national_id: nationalId,
    }).then(res => {
      if (res.data?.success) {
        setAuth(res.data.token, res.data.user);
      }
      return res.data;
    }),

  /** GET /auth/me — returns user profile from Bearer token */
  getMe: () => api.get('/auth/me'),
};

// ═══════════════════════════════════════════════════════════════════
// USER PROFILE & TEAMS API
// Backend routes: /api/user/profile, /api/teams/*
// ═══════════════════════════════════════════════════════════════════

export const userProfileAPI = {
  /** GET /api/user/profile — get full profile */
  getProfile: () => api.get('/api/user/profile'),

  /** PUT /api/user/profile — update profile (display_name, bio, avatar_url) */
  updateProfile: (data) => api.put('/api/user/profile', data),

  /** GET /api/user/profiles/{user_id} — view public profile */
  getPublicProfile: (userId) => api.get(`/api/user/profiles/${userId}`),
};

export const teamsAPI = {
  /** GET /api/teams — list user's teams */
  list: () => api.get('/api/teams'),

  /** POST /api/teams — create a new team */
  create: (data) => api.post('/api/teams', data),

  /** GET /api/teams/{team_id} — get team details */
  get: (teamId) => api.get(`/api/teams/${teamId}`),

  /** PUT /api/teams/{team_id} — update team settings */
  update: (teamId, data) => api.put(`/api/teams/${teamId}`, data),

  /** POST /api/teams/{team_id}/members — invite member */
  inviteMember: (teamId, data) => api.post(`/api/teams/${teamId}/members`, data),

  /** GET /api/teams/{team_id}/members — list members */
  getMembers: (teamId) => api.get(`/api/teams/${teamId}/members`),

  /** DELETE /api/teams/{team_id}/members/{user_id} — remove member */
  removeMember: (teamId, userId) => api.delete(`/api/teams/${teamId}/members/${userId}`),

  /** PUT /api/teams/{team_id}/members/{user_id}/role — change member role */
  changeMemberRole: (teamId, userId, role) =>
    api.put(`/api/teams/${teamId}/members/${userId}/role`, { role }),

  /** GET /api/permissions — get current user permissions */
  getPermissions: () => api.get('/api/permissions'),
};

// ═══════════════════════════════════════════════════════════════════
// HEALTH API
// Backend routes: GET /health (aliased as /api/status, /api/db/health)
// ═══════════════════════════════════════════════════════════════════

export const healthAPI = {
  /** GET /health — system health + module status */
  check: () => api.get('/health'),
};

// ═══════════════════════════════════════════════════════════════════
// CORE CHAT API
// Backend routes: POST /chat, POST /llm/chat, POST /api/chat
//                 GET /status, GET /api/system/info
// ═══════════════════════════════════════════════════════════════════

export const chatAPI = {
  /** POST /api/chat — send message to ASIMNEXUS (aliased as /chat, /llm/chat) */
  sendMessage: (message, userId = 'web_user') =>
    api.post('/api/chat', { message, user_id: userId }),

  /** GET /status — full system status (OS, device, LLM, dharma, mesh) */
  getStatus: () => api.get('/status'),

  /** GET /api/system/info — system info (OS, Python, LLM, GGUF) */
  getSystemInfo: () => api.get('/api/system/info'),
};

// ═══════════════════════════════════════════════════════════════════
// LOCAL LLM API — maps to backend /api/local-llm/health alias
// Backend: GET /api/local-llm/health (aliased as /api/system/info)
// The /api/local-llm/* generate routes do NOT exist in backend yet.
// ═══════════════════════════════════════════════════════════════════

export const localLLMAPI = {
  /** GET /api/local-llm/health — alias for /api/system/info */
  getHealth: () => api.get('/api/local-llm/health'),

  /** @deprecated — No backend route exists for /api/local-llm/models.
   *  Use chatAPI.sendMessage() with "/models" command instead. */
  getModels: () => {
    console.warn('localLLMAPI.getModels() has no backend endpoint. Use chat.sendMessage() instead.');
    return api.get('/api/local-llm/health');
  },

  /** @deprecated — No backend route exists for /api/local-llm/generate.
   *  Use chatAPI.sendMessage() instead. */
  generate: (prompt, modelId = null, maxTokens = 512) => {
    console.warn('localLLMAPI.generate() has no backend endpoint. Use chat.sendMessage() instead.');
    return api.post('/api/chat', {
      message: prompt,
      user_id: 'web_user',
    });
  },

  /** @deprecated — No backend route exists for /api/local-llm/generate/gemma. */
  generateGemma: (prompt, maxTokens = 512) => {
    console.warn('localLLMAPI.generateGemma() has no backend endpoint. Use chat.sendMessage() instead.');
    return api.post('/api/chat', {
      message: prompt,
      user_id: 'web_user',
    });
  },
};

// ═══════════════════════════════════════════════════════════════════
// ASIM BRAIN API — frontend compatibility endpoints
// Backend routes: POST /api/brain/process, POST /api/brain/stream
// ═══════════════════════════════════════════════════════════════════

export const brainAPI = {
  /** POST /api/brain/process — process message through Asim Brain */
  process: (message, userId = 'web_user', mode = 'personal') =>
    api.post('/api/brain/process', { message, user_id: userId, mode }),

  /** POST /api/brain/stream — stream response from Asim Brain */
  stream: (message, userId = 'web_user') =>
    api.post('/api/brain/stream', { message, user_id: userId }),
};

// ═══════════════════════════════════════════════════════════════════
// MEMORY / HISTORY API
// Backend routes: GET /api/memory/stats, GET /api/memory/recent
//                 GET /api/memory/search?q=, DELETE /api/memory/{id}
// ═══════════════════════════════════════════════════════════════════

export const memoryAPI = {
  /** GET /api/memory/stats — total message count for user */
  getStats: () => api.get('/api/memory/stats'),

  /** GET /api/memory/recent?limit=N — recent messages */
  getRecent: (limit = 20) => api.get('/api/memory/recent', { params: { limit } }),

  /** GET /api/memory/search?q= — search messages */
  search: (query) => api.get('/api/memory/search', { params: { q: query } }),

  /** DELETE /api/memory/{messageId} — delete a message */
  deleteMessage: (messageId) => api.delete(`/api/memory/${messageId}`),

  /** GET /api/db/conversations/user/{userId} — user conversations */
  getConversations: (userId) => api.get(`/api/db/conversations/user/${userId}`),
};

// ═══════════════════════════════════════════════════════════════════
// PERSONAL OS & CLONES API
// Backend routes: GET /personal/status, GET /personal/clones (aliased /api/clones)
//                 GET /api/personal/status, GET /api/personal/universe
//                 GET /api/personal/contracts, POST /api/personal/resource-sharing
//                 POST /api/agent/mode/on, POST /api/agent/mode/off, GET /api/agent/status
// ═══════════════════════════════════════════════════════════════════

export const personalAPI = {
  /** GET /personal/status — user universe mode & theme */
  getStatus: () => api.get('/personal/status'),

  /** GET /personal/clones — list all 15 founder clones */
  getClones: () => api.get('/personal/clones'),

  /** GET /api/personal/status — detailed personal OS status */
  getPersonalStatus: () => api.get('/api/personal/status'),

  /** GET /api/personal/universe — personal universe info */
  getUniverse: () => api.get('/api/personal/universe'),

  /** GET /api/personal/contracts — personal contracts */
  getContracts: () => api.get('/api/personal/contracts'),

  /** POST /api/agent/mode/on — enable agent mode */
  agentModeOn: () => api.post('/api/agent/mode/on'),

  /** POST /api/agent/mode/off — disable agent mode */
  agentModeOff: () => api.post('/api/agent/mode/off'),

  /** GET /api/agent/status — agent status */
  getAgentStatus: () => api.get('/api/agent/status'),

  /** GET /api/universe/status — universe status */
  getUniverseStatus: () => api.get('/api/universe/status'),

  /** GET /api/personal/resource-sharing — get resource sharing config */
  getResourceSharing: () => api.get('/api/personal/resource-sharing'),

  /** POST /api/personal/resource-sharing — set resource sharing config */
  setResourceSharing: (enabled, percentage = 2) =>
    api.post('/api/personal/resource-sharing', { enabled, resource_percentage: percentage }),
};

// ═══════════════════════════════════════════════════════════════════
// AUTONOMOUS SYSTEM API
// Backend routes: POST /api/agent/mode/on, POST /api/agent/mode/off, GET /api/agent/status
// ═══════════════════════════════════════════════════════════════════

export const autonomousAPI = {
  /** GET /api/agent/status — autonomous system status */
  getStatus: () => api.get('/api/agent/status'),

  /** @deprecated — No backend route for /api/autonomous/founders */
  getFounders: () => {
    console.warn('autonomousAPI.getFounders() has no backend endpoint.');
    return api.get('/api/agent/status');
  },

  /** POST /api/agent/mode/on — toggle autopilot on */
  toggleAutopilot: (enabled) =>
    enabled ? api.post('/api/agent/mode/on') : api.post('/api/agent/mode/off'),

  /** @deprecated — No backend route for /api/autonomous/keys */
  getKeysStatus: () => {
    console.warn('autonomousAPI.getKeysStatus() has no backend endpoint.');
    return api.get('/api/agent/status');
  },

  /** @deprecated — No backend route for /api/autonomous/keys/add */
  addApiKey: (keyData) => {
    console.warn('autonomousAPI.addApiKey() has no backend endpoint.');
    return api.post('/api/keys/update', keyData);
  },

  /** @deprecated — No backend route for /api/autonomous/tasks */
  getTasks: () => {
    console.warn('autonomousAPI.getTasks() has no backend endpoint.');
    return api.get('/api/agent/status');
  },
};

// ═══════════════════════════════════════════════════════════════════
// GROUP CHAT API
// Backend: No /api/group-chat/* routes exist. Group chat is not yet
// exposed as a separate API module. Use chatAPI or personalAPI instead.
// ═══════════════════════════════════════════════════════════════════

export const groupChatAPI = {
  /** @deprecated — No backend route for /api/group-chat/status */
  getStatus: () => {
    console.warn('groupChatAPI.getStatus() — no backend endpoint.');
    return api.get('/status');
  },

  /** @deprecated — No backend route for /api/group-chat/history */
  getHistory: (limit = 50) => {
    console.warn('groupChatAPI.getHistory() — no backend endpoint. Use memoryAPI.getRecent() instead.');
    return api.get('/api/memory/recent', { params: { limit } });
  },

  /** @deprecated — No backend route for /api/group-chat/founders */
  getFounders: () => {
    console.warn('groupChatAPI.getFounders() — no backend endpoint.');
    return api.get('/personal/clones');
  },
};

// ═══════════════════════════════════════════════════════════════════
// ENHANCED CHAT API (Memory-aware conversations)
// Backend: No /api/chat/enhanced, /api/chat/stream, /api/chat/history routes exist.
// Use brainAPI, chatAPI, or memoryAPI instead.
// ═══════════════════════════════════════════════════════════════════

export const enhancedChatAPI = {
  /** @deprecated — No backend route for /api/chat/enhanced.
   *  Use brainAPI.process() or chatAPI.sendMessage() instead. */
  sendMessage: (message, userId = 1, conversationId = null, modelId = 'qwen3-4b') => {
    console.warn('enhancedChatAPI.sendMessage() deprecated. Use brainAPI.process() instead.');
    return api.post('/api/brain/process', {
      message,
      user_id: String(userId),
      mode: 'personal',
    });
  },

  /** @deprecated — No backend route for /api/chat/stream.
   *  Use brainAPI.stream() instead. */
  streamMessage: (message, userId = 1, conversationId = null, modelId = 'qwen3-4b') => {
    console.warn('enhancedChatAPI.streamMessage() deprecated. Use brainAPI.stream() instead.');
    return new EventSource(
      `${BASE}/api/brain/stream?message=${encodeURIComponent(message)}&user_id=${userId}`
    );
  },

  /** @deprecated — No backend route for /api/chat/history/{id}.
   *  Use memoryAPI.getRecent() instead. */
  getHistory: (conversationId, limit = 50) => {
    console.warn('enhancedChatAPI.getHistory() deprecated. Use memoryAPI.getRecent() instead.');
    return api.get('/api/memory/recent', { params: { limit } });
  },

  /** @deprecated — No backend route for /api/chat/clear-cache/{id} */
  clearCache: (conversationId) => {
    console.warn('enhancedChatAPI.clearCache() has no backend endpoint.');
    return Promise.resolve({ data: { success: true, message: 'No-op: backend cache clear not available' } });
  },

  /** @deprecated — No backend route for /api/chat/test-context */
  testContext: () => {
    console.warn('enhancedChatAPI.testContext() has no backend endpoint.');
    return api.get('/api/memory/stats');
  },
};

// ═══════════════════════════════════════════════════════════════════
// DATABASE API
// Backend has: GET /api/db/conversations/user/{userId}, GET /api/db/api-keys/{userId}
//              POST /api/keys/update, POST /api/db/health (aliased as /health)
// No /api/db/users, /api/db/messages, /api/admin/* routes exist.
// ═══════════════════════════════════════════════════════════════════

export const databaseAPI = {
  /** @deprecated — No POST /api/db/users in backend.
   *  Use authAPI.register() instead. */
  createUser: (username, email = null, password = null, preferences = {}) => {
    console.warn('databaseAPI.createUser() deprecated. Use authAPI.register() instead.');
    return authAPI.register(email || `${username}@local`, password);
  },

  /** @deprecated — No GET /api/db/users/{id} in backend.
   *  Use authAPI.getMe() instead. */
  getUser: (userId) => {
    console.warn('databaseAPI.getUser() deprecated. Use authAPI.getMe() instead.');
    return api.get('/auth/me');
  },

  /** @deprecated — No POST /api/db/conversations in backend. */
  createConversation: (userId, title = 'New Chat', modelUsed = 'qwen3-4b') => {
    console.warn('databaseAPI.createConversation() has no backend endpoint.');
    return Promise.resolve({ data: { success: true, conversation_id: 'local-' + Date.now() } });
  },

  /** GET /api/db/conversations/user/{userId} — user conversations (WORKS) */
  getUserConversations: (userId, limit = 10) =>
    api.get(`/api/db/conversations/user/${userId}`, { params: { limit } }),

  /** @deprecated — No POST /api/db/messages in backend.
   *  Messages are stored automatically by POST /api/chat. */
  addMessage: (conversationId, role, content, metadata = {}) => {
    console.warn('databaseAPI.addMessage() deprecated. Messages saved automatically on chat.');
    return Promise.resolve({ data: { success: true, message_id: 'auto-' + Date.now() } });
  },

  /** @deprecated — No GET /api/db/messages/{id} in backend.
   *  Use memoryAPI.getRecent() instead. */
  getMessages: (conversationId, limit = 100) => {
    console.warn('databaseAPI.getMessages() deprecated. Use memoryAPI.getRecent() instead.');
    return api.get('/api/memory/recent', { params: { limit } });
  },

  /** POST /api/keys/update — store API key (WORKS via backend /api/keys/update) */
  storeApiKey: (userId, provider, apiKey, config = {}) =>
    api.post('/api/keys/update', { user_id: userId, provider, api_key: apiKey, ...config }),

  /** GET /api/db/api-keys/{userId} — get stored API keys (WORKS) */
  getApiKeys: (userId, provider = null) =>
    api.get(`/api/db/api-keys/${userId}${provider ? `?provider=${provider}` : ''}`),

  /** @deprecated — No POST /api/admin/migrate-api-keys in backend. */
  migrateApiKeys: (adminPassword) => {
    console.warn('databaseAPI.migrateApiKeys() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Migration not available in backend' } });
  },

  /** GET /api/db/health — aliased as GET /health (WORKS) */
  health: () => api.get('/api/db/health'),
};

// ═══════════════════════════════════════════════════════════════════
// SYSTEM OPERATIONS API
// Backend has: GET /api/system/info, GET /api/system/complete
// No /api/system/folder/*, /api/system/file/*, /api/system/directory/* routes.
// ═══════════════════════════════════════════════════════════════════

export const systemOperationsAPI = {
  /** @deprecated — No POST /api/system/folder/create in backend */
  createFolder: (path) => {
    console.warn('systemOperationsAPI.createFolder() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No DELETE /api/system/folder/delete in backend */
  deleteFolder: (path, recursive = false) => {
    console.warn('systemOperationsAPI.deleteFolder() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No POST /api/system/file/create in backend */
  createFile: (path, content = '') => {
    console.warn('systemOperationsAPI.createFile() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No GET /api/system/file/read in backend */
  readFile: (path, maxLines = 100) => {
    console.warn('systemOperationsAPI.readFile() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No POST /api/system/file/write in backend */
  writeFile: (path, content, append = false) => {
    console.warn('systemOperationsAPI.writeFile() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No GET /api/system/directory/list in backend */
  listDirectory: (path = '.') => {
    console.warn('systemOperationsAPI.listDirectory() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No GET /api/system/files/search in backend */
  searchFiles: (pattern, path = '.') => {
    console.warn('systemOperationsAPI.searchFiles() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** @deprecated — No POST /api/system/execute in backend */
  executeCommand: (command, timeout = 30) => {
    console.warn('systemOperationsAPI.executeCommand() has no backend endpoint.');
    return Promise.resolve({ data: { success: false, message: 'Not available in backend' } });
  },

  /** GET /api/system/info — system info (WORKS) */
  getSystemInfo: () => api.get('/api/system/info'),
};

// ═══════════════════════════════════════════════════════════════════
// CACHE API
// Backend: No /api/cache/* routes exist.
// ═══════════════════════════════════════════════════════════════════

export const cacheAPI = {
  /** @deprecated — No GET /api/cache/stats in backend */
  getStats: () => {
    console.warn('cacheAPI.getStats() has no backend endpoint.');
    return api.get('/api/memory/stats');
  },

  /** @deprecated — No DELETE /api/cache/clear in backend */
  clear: () => {
    console.warn('cacheAPI.clear() has no backend endpoint.');
    return Promise.resolve({ data: { success: true, message: 'No-op: cache clear not implemented in backend' } });
  },
};

// ═══════════════════════════════════════════════════════════════════
// LIFECYCLE / LIFE JOURNEY API
// Backend routes: GET /api/universe/{user_id}/lifecycle, GET /api/universe/{user_id}/status
//                 POST /api/universe/{user_id}/layer/activate
// ═══════════════════════════════════════════════════════════════════

export const lifecycleAPI = {
  /** GET /api/universe/{user_id}/lifecycle — complete lifecycle summary */
  getLifecycle: (userId) => api.get(`/api/universe/${userId}/lifecycle`),

  /** GET /api/universe/{user_id}/status — universe status */
  getStatus: (userId) => api.get(`/api/universe/${userId}/status`),

  /** POST /api/universe/{user_id}/layer/activate — activate a universe layer */
  activateLayer: (userId, layerId) =>
    api.post(`/api/universe/${userId}/layer/activate`, { layer_id: layerId }),

  /** GET /api/universe/stats — overall universe statistics */
  getStats: () => api.get('/api/universe/stats'),
};

// ═══════════════════════════════════════════════════════════════════
// UNIVERSAL / GLOBAL SYSTEM API
// Backend routes: GET /api/universal/status, /api/universal/countries,
//                 /api/universal/currencies, /api/universal/languages,
//                 /api/universal/timezones, etc.
// ═══════════════════════════════════════════════════════════════════

export const universalAPI = {
  /** GET /api/universal/status — countries, currencies, languages */
  getStatus: () => api.get('/api/universal/status'),

  /** GET /api/universal/countries — all countries */
  getCountries: () => api.get('/api/universal/countries'),

  /** GET /api/universal/currencies — all currencies */
  getCurrencies: () => api.get('/api/universal/currencies'),

  /** GET /api/universal/languages — all languages */
  getLanguages: () => api.get('/api/universal/languages'),

  /** GET /api/universal/timezones — all timezones */
  getTimezones: () => api.get('/api/universal/timezones'),
};

// ═══════════════════════════════════════════════════════════════════
// DHARMA / ETHICS API
// Backend routes: GET /api/dharma/status, POST /api/dharma/veto,
//                 GET /api/dharma/veto-status, POST /api/dharma/veto-check,
//                 POST /api/dharma/cultural-check, etc.
// ═══════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════
// IDENTITY / ZKP API
// Backend routes: GET /api/identity/stats, GET /api/identity/list,
//                 POST /api/identity/create, POST /api/identity/verify
// ═══════════════════════════════════════════════════════════════════

export const identityAPI = {
  /** GET /api/identity/stats — identity system statistics */
  getStats: () => api.get('/api/identity/stats'),

  /** GET /api/identity/list — list all identities */
  getList: () => api.get('/api/identity/list'),

  /** POST /api/identity/create — create a new ZKP identity */
  create: (data) => api.post('/api/identity/create', data),

  /** POST /api/identity/verify — verify a ZKP identity */
  verify: (data) => api.post('/api/identity/verify', data),
};

// ═══════════════════════════════════════════════════════════════════
// SVT TOKEN API
// Backend routes: GET /api/svt/stats, POST /api/svt/wallet,
//                 POST /api/svt/mint, GET /api/svt/wallet/{did}
// ═══════════════════════════════════════════════════════════════════

export const svtAPI = {
  /** GET /api/svt/stats — SVT token system statistics */
  getStats: () => api.get('/api/svt/stats'),

  /** POST /api/svt/wallet — create wallet for a DID */
  createWallet: (did) => api.post('/api/svt/wallet', { did }),

  /** POST /api/svt/mint — mint SVT tokens */
  mint: (did, amount, memo = '') => api.post('/api/svt/mint', { did, amount, memo }),

  /** GET /api/svt/wallet/{did} — get wallet info */
  getWallet: (did) => api.get(`/api/svt/wallet/${did}`),
};

// ═══════════════════════════════════════════════════════════════════
// HDT (HUMAN DIGITAL TWIN) API
// Backend routes: POST /api/hdt/create, GET /api/hdt/{did}/status,
//                 POST /api/hdt/{did}/skill, POST /api/hdt/{did}/announce
// ═══════════════════════════════════════════════════════════════════

export const hdtAPI = {
  /** POST /api/hdt/create — create a Human Digital Twin */
  create: (data) => api.post('/api/hdt/create', data),

  /** GET /api/hdt/{did}/status — get HDT status */
  getStatus: (did) => api.get(`/api/hdt/${did}/status`),

  /** POST /api/hdt/{did}/skill — add a skill to HDT */
  addSkill: (did, data) => api.post(`/api/hdt/${did}/skill`, data),

  /** POST /api/hdt/{did}/announce — announce skills to DHT mesh */
  announce: (did) => api.post(`/api/hdt/${did}/announce`, {}),
};

// ═══════════════════════════════════════════════════════════════════
// WORLD OS / QUAD MESH API
// Backend routes: GET /api/quad/status, GET /api/bugs/stats,
//                 GET /api/dht/status, GET /api/firewall/status
// ═══════════════════════════════════════════════════════════════════

export const worldOSAPI = {
  /** GET /api/quad/status — quad mesh layer status */
  getQuadStatus: () => api.get('/api/quad/status'),

  /** GET /api/bugs/stats — self-healing bug pipeline stats */
  getBugStats: () => api.get('/api/bugs/stats'),

  /** GET /api/dht/status — Kademlia DHT status */
  getDHTStatus: () => api.get('/api/dht/status'),

  /** GET /api/firewall/status — cognitive firewall status */
  getFirewallStatus: () => api.get('/api/firewall/status'),
};

// ═══════════════════════════════════════════════════════════════════
// DHARMA / ETHICS API
// ═══════════════════════════════════════════════════════════════════

export const dharmaAPI = {
  /** GET /api/dharma/status — ΔT engine status */
  getStatus: () => api.get('/api/dharma/status'),

  /** POST /api/dharma/veto — ethical veto */
  veto: (reason, severity = 'warning') =>
    api.post('/api/dharma/veto', { reason, severity }),
};

// ═══════════════════════════════════════════════════════════════════
// INFRASTRUCTURE / MESH API
// Backend routes: GET /api/mesh/status, GET /api/mesh/peers,
//                 POST /api/mesh/discover/start, POST /api/mesh/discover/add-peer,
//                 POST /api/mesh/air-gap/engage, POST /api/mesh/air-gap/disengage,
//                 GET /api/mesh/air-gap/check, GET /api/mesh/nodes
// ═══════════════════════════════════════════════════════════════════

export const meshAPI = {
  /** GET /api/mesh/status — mesh network status */
  getStatus: () => api.get('/api/mesh/status'),

  /** GET /api/mesh/peers — connected peers */
  getPeers: () => api.get('/api/mesh/peers'),

  /** GET /api/mesh/nodes — all mesh nodes */
  getNodes: () => api.get('/api/mesh/nodes'),

  /** POST /api/mesh/discover/start — start LAN discovery */
  discoverStart: () => api.post('/api/mesh/discover/start'),

  /** POST /api/mesh/discover/add-peer — manually add a peer */
  addPeer: (ip, port = 8765) =>
    api.post('/api/mesh/discover/add-peer', { ip, port }),

  /** POST /api/mesh/air-gap/engage — engage air-gap isolation */
  airGapEngage: (level = 1, reason = 'Human-initiated') =>
    api.post('/api/mesh/air-gap/engage', { level, reason }),

  /** POST /api/mesh/air-gap/disengage — disengage air-gap */
  airGapDisengage: () => api.post('/api/mesh/air-gap/disengage'),

  /** GET /api/mesh/air-gap/check — check connectivity */
  checkConnectivity: (host = '8.8.8.8') =>
    api.get('/api/mesh/air-gap/check', { params: { host } }),

  /** POST /api/node/init — initialize local mesh node */
  initNode: () => api.post('/api/mesh/node/init'),
};

// ═══════════════════════════════════════════════════════════════════
// OFFLINE / SYNC API
// Backend routes: GET /api/sync/status, POST /api/sync/enqueue,
//                 POST /api/sync/flush, GET /api/sync/queue,
//                 POST /api/mesh/offline/operation,
//                 GET /api/mesh/offline/status/{user_id},
//                 GET /api/mesh/offline/capabilities
// ═══════════════════════════════════════════════════════════════════

export const offlineAPI = {
  /** GET /api/sync/status — sync engine status */
  getSyncStatus: () => api.get('/api/sync/status'),

  /** GET /api/sync/queue — list queued sync operations */
  getQueue: () => api.get('/api/sync/queue'),

  /** POST /api/sync/enqueue — queue an offline operation */
  enqueue: (opType, entityType, entityId, payload) =>
    api.post('/api/sync/enqueue', {
      op_type: opType,
      entity_type: entityType,
      entity_id: entityId,
      payload,
    }),

  /** POST /api/sync/flush — flush the sync queue */
  flushQueue: () => api.post('/api/sync/flush'),

  /** GET /api/mesh/offline/status/{user_id} — offline sync status for user */
  getUserOfflineStatus: (userId) =>
    api.get(`/api/mesh/offline/status/${userId}`),

  /** GET /api/mesh/offline/capabilities — offline functionality capabilities */
  getCapabilities: () => api.get('/api/mesh/offline/capabilities'),

  /** POST /api/mesh/offline/operation — create an offline operation */
  createOperation: (operationType, payload) =>
    api.post('/api/mesh/offline/operation', { operation_type: operationType, ...payload }),
};

// ═══════════════════════════════════════════════════════════════════
// ANALYTICS API
// Backend routes: GET /api/analytics/overview, GET /api/analytics/activity
// ═══════════════════════════════════════════════════════════════════

export const analyticsAPI = {
  /** GET /api/analytics/overview — user analytics */
  getOverview: () => api.get('/api/analytics/overview'),

  /** GET /api/analytics/activity — system activity log */
  getActivity: () => api.get('/api/analytics/activity'),
};

// ═══════════════════════════════════════════════════════════════════
// JOBS / MARKETPLACE API
// Backend routes: GET /api/jobs/stats, GET /api/jobs/list, POST /api/jobs/post
//                 GET /api/jobs/{job_id}, POST /api/jobs/{job_id}/apply
// ═══════════════════════════════════════════════════════════════════

export const jobsAPI = {
  /** GET /api/jobs/stats — jobs marketplace statistics */
  getStats: () => api.get('/api/jobs/stats'),

  /** GET /api/jobs/list?status=&category= — list marketplace jobs */
  list: (status = 'open', category = null) =>
    api.get('/api/jobs/list', { params: { status, category } }),

  /** POST /api/jobs/post — create a new job */
  post: (jobData) => api.post('/api/jobs/post', jobData),
};

// ═══════════════════════════════════════════════════════════════════
// DREAMING / AI CONSCIOUSNESS API
// Backend routes: GET /api/dreaming/status, GET /api/dreaming/briefing
//                 POST /api/dreaming/trigger
// ═══════════════════════════════════════════════════════════════════

export const dreamingAPI = {
  /** GET /api/dreaming/status — dreaming system status */
  getStatus: () => api.get('/api/dreaming/status'),

  /** GET /api/dreaming/briefing — AI dream briefing (overnight learning) */
  getBriefing: () => api.get('/api/dreaming/briefing'),

  /** POST /api/dreaming/trigger — manually trigger a dreaming cycle */
  trigger: () => api.post('/api/dreaming/trigger'),
};

// ═══════════════════════════════════════════════════════════════════
// CONSENSUS / CLONE VOTING API
// Backend routes: POST /api/consensus/vote, POST /api/consensus/{round_id}/override
//                 GET /api/consensus/stats, GET /api/consensus/pending, GET /api/consensus/list
// ═══════════════════════════════════════════════════════════════════

export const consensusAPI = {
  /** POST /api/consensus/vote — start a consensus round */
  vote: (topic, description = '', level = 'high') =>
    api.post('/api/consensus/vote', { topic, description, level }),

  /** POST /api/consensus/{round_id}/override — human override */
  override: (roundId, approved = true, reason = '') =>
    api.post(`/api/consensus/${roundId}/override`, { approved, reason }),

  /** GET /api/consensus/stats — consensus engine statistics */
  getStats: () => api.get('/api/consensus/stats'),

  /** GET /api/consensus/pending — rounds needing human approval */
  getPending: () => api.get('/api/consensus/pending'),

  /** GET /api/consensus/list — recent consensus rounds */
  getList: () => api.get('/api/consensus/list'),
};

// ═══════════════════════════════════════════════════════════════════
// CLONE SPECIALIZER API
// Backend routes: GET /api/clones/specs, GET /api/clones/{clone_id}/spec
//                 POST /api/clones/route
// ═══════════════════════════════════════════════════════════════════

export const clonesAPI = {
  /** GET /api/clones/specs — all clone specializations */
  getSpecs: () => api.get('/api/clones/specs'),

  /** GET /api/clones/{clone_id}/spec — single clone spec */
  getSpec: (cloneId) => api.get(`/api/clones/${cloneId}/spec`),

  /** POST /api/clones/route — route a query to the best clone */
  route: (query) => api.post('/api/clones/route', { query }),
};

// ═══════════════════════════════════════════════════════════════════
// HEALING / SYSTEM MAINTENANCE API
// Backend routes: GET /api/healing/status, POST /api/healing/heal,
//                 GET /api/healing/balance, etc.
// ═══════════════════════════════════════════════════════════════════

export const healingAPI = {
  /** GET /api/healing/status — system healing status */
  getStatus: () => api.get('/api/healing/status'),

  /** GET /api/healing/balance — system resource balance */
  getBalance: () => api.get('/api/healing/balance'),

  /** POST /api/healing/heal — trigger system healing */
  heal: () => api.post('/api/healing/heal'),
};

// ═══════════════════════════════════════════════════════════════════
// OS TOOLS API — OS Control & Tool Execution
// Backend routes: GET /api/os/tools, POST /api/os/execute,
//                 POST /api/os/approve/{call_id}, POST /api/os/reject/{call_id},
//                 GET /api/os/pending, GET /api/os/audit,
//                 GET /api/os/status, GET /api/os/metrics,
//                 GET /api/os/clipboard/status
// ═══════════════════════════════════════════════════════════════════

export const osToolsAPI = {
  /** GET /api/os/tools — list available OS tools */
  listTools: () => api.get('/api/os/tools'),

  /** POST /api/os/execute — execute an OS tool
   *  Backend expects: { tool_name, parameters, agent_name? } */
  execute: (toolName, params = {}, agentName = 'AutoModeAgent') =>
    api.post('/api/os/execute', { tool_name: toolName, parameters: params, agent_name: agentName }),

  /** GET /api/os/status — OS control system status */
  getStatus: () => api.get('/api/os/status'),

  /** GET /api/os/metrics — OS performance metrics */
  getMetrics: () => api.get('/api/os/metrics'),

  /** GET /api/os/pending — pending OS approval calls */
  getPending: () => api.get('/api/os/pending'),

  /** POST /api/os/approve/{call_id} — approve a pending OS call */
  approve: (callId) => api.post(`/api/os/approve/${callId}`),

  /** POST /api/os/reject/{call_id} — reject a pending OS call */
  reject: (callId) => api.post(`/api/os/reject/${callId}`),

  /** GET /api/os/audit — OS tool audit log */
  getAudit: (limit = 30) => api.get('/api/os/audit', { params: { limit } }),

  /** GET /api/os/clipboard/status — clipboard access status */
  getClipboardStatus: () => api.get('/api/os/clipboard/status'),
};

// ═══════════════════════════════════════════════════════════════════
// ECONOMY / MARKETPLACE EXPANDED API
// Backend routes: /api/credits/*, /api/contracts/*, /api/hybrid-economy/*
//                 /api/reputation/*, /api/task-bus/*, /api/bridge/*
//                 /api/marketplace/*
// ═══════════════════════════════════════════════════════════════════

export const hybridEconomyAPI = {
  getSummary: () => api.get('/api/hybrid-economy/summary'),
  setMode: (mode) => api.post('/api/hybrid-economy/mode', { mode }),
  createAccount: (ownerId, ownerType, initialBalance = 0) =>
    api.post('/api/hybrid-economy/account', { owner_id: ownerId, owner_type: ownerType, initial_balance: initialBalance }),
  getAccount: (ownerId) => api.get(`/api/hybrid-economy/account/${ownerId}`),
  listAccounts: (ownerType) => api.get('/api/hybrid-economy/accounts', { params: { owner_type: ownerType } }),
  deposit: (ownerId, amount, memo = '') => api.post('/api/hybrid-economy/deposit', { owner_id: ownerId, amount, memo }),
  withdraw: (ownerId, amount, memo = '') => api.post('/api/hybrid-economy/withdraw', { owner_id: ownerId, amount, memo }),
  transfer: (fromId, toId, amount, memo = '') => api.post('/api/hybrid-economy/transfer', { from_id: fromId, to_id: toId, amount, memo }),
  createTask: (description, requesterId, reward, category = 'general') =>
    api.post('/api/hybrid-economy/task', { description, requester_id: requesterId, reward, category }),
  assignTask: (taskId, executorId) => api.post('/api/hybrid-economy/task/assign', { task_id: taskId, executor_id: executorId }),
  listTasks: (params = {}) => api.get('/api/hybrid-economy/tasks', { params }),
};

export const reputationAPI = {
  getStats: () => api.get('/api/reputation/stats'),
  getLeaderboard: (limit = 10) => api.get('/api/reputation/leaderboard', { params: { limit } }),
  register: (entityId, initialScore = 0) => api.post('/api/reputation/register', { entity_id: entityId, initial_score: initialScore }),
  get: (entityId) => api.get(`/api/reputation/${entityId}`),
  getEvents: (entityId, limit = 50) => api.get(`/api/reputation/${entityId}/events`, { params: { limit } }),
  add: (entityId, amount, reason = '') => api.post('/api/reputation/add', { entity_id: entityId, amount, reason }),
  remove: (entityId, amount, reason = '') => api.post('/api/reputation/remove', { entity_id: entityId, amount, reason }),
  stake: (entityId, amount, reason = '') => api.post('/api/reputation/stake', { entity_id: entityId, amount, reason }),
  unstake: (stakeId) => api.post('/api/reputation/unstake', { stake_id: stakeId }),
  slash: (stakeId, penaltyPct = 1.0, reason = '') => api.post('/api/reputation/slash', { stake_id: stakeId, penalty_pct: penaltyPct, reason }),
};

export const taskBusAPI = {
  getStatus: () => api.get('/api/task-bus/status'),
  registerAgent: (agentId, capabilities = [], displayName = '', maxConcurrent = 5) =>
    api.post('/api/task-bus/agent/register', { agent_id: agentId, capabilities, display_name: displayName, max_concurrent: maxConcurrent }),
  unregisterAgent: (agentId) => api.post(`/api/task-bus/agent/${agentId}/unregister`),
  listAgents: (onlineOnly = false) => api.get('/api/task-bus/agents', { params: { online_only: onlineOnly } }),
  submitTask: (taskType, payload = {}, priority = 'medium', maxRetries = 3) =>
    api.post('/api/task-bus/task/submit', { task_type: taskType, payload, priority, max_retries: maxRetries }),
  assignNext: (agentId) => api.post('/api/task-bus/task/assign-next', { agent_id: agentId }),
  listTasks: (params = {}) => api.get('/api/task-bus/tasks', { params }),
  getTask: (taskId) => api.get(`/api/task-bus/task/${taskId}`),
  startTask: (taskId, agentId) => api.post(`/api/task-bus/task/${taskId}/start`, null, { params: { agent_id: agentId } }),
  completeTask: (taskId, agentId) => api.post(`/api/task-bus/task/${taskId}/complete`, { task_id: taskId, agent_id: agentId }),
  failTask: (taskId, agentId, error) => api.post(`/api/task-bus/task/${taskId}/fail`, { task_id: taskId, agent_id: agentId, error }),
  cancelTask: (taskId) => api.post(`/api/task-bus/task/${taskId}/cancel`),
  heartbeat: (agentId) => api.post(`/api/task-bus/agent/${agentId}/heartbeat`),
};

export const bridgeAPI = {
  getStats: () => api.get('/api/bridge/stats'),
  createPool: (chain, tokenSymbol, initialBalance = 0) =>
    api.post('/api/bridge/pool/create', { chain, token_symbol: tokenSymbol, initial_balance: initialBalance }),
  listPools: (chain) => api.get('/api/bridge/pools', { params: { chain } }),
  addLiquidity: (poolId, amount) => api.post('/api/bridge/pool/add-liquidity', { pool_id: poolId, amount }),
  removeLiquidity: (poolId, amount) => api.post('/api/bridge/pool/remove-liquidity', { pool_id: poolId, amount }),
  initiate: (fromChain, toChain, asset, amount, sender, recipient) =>
    api.post('/api/bridge/initiate', { from_chain: fromChain, to_chain: toChain, asset, amount, sender, recipient }),
  getTransaction: (txId) => api.get(`/api/bridge/tx/${txId}`),
  listTransactions: (params = {}) => api.get('/api/bridge/transactions', { params }),
  calculateFee: (fromChain, amount) => api.get('/api/bridge/fee', { params: { from_chain: fromChain, amount } }),
};

export const marketplaceAPI = {
  getGlobalStats: () => api.get('/api/marketplace/global-stats'),
  search: (q, module = null, limit = 10) => api.get('/api/marketplace/search', { params: { q, module, limit } }),

  // ── Listings ──
  createListing: (data, sellerId) => api.post('/api/marketplace/listings', data, { params: { seller_id: sellerId } }),
  listListings: (params) => api.get('/api/marketplace/listings', { params }),
  getListing: (id) => api.get(`/api/marketplace/listings/${id}`),
  updateListing: (id, data, sellerId) => api.put(`/api/marketplace/listings/${id}`, data, { params: { seller_id: sellerId } }),
  pauseListing: (id, sellerId) => api.post(`/api/marketplace/listings/${id}/pause`, {}, { params: { seller_id: sellerId } }),
  activateListing: (id, sellerId) => api.post(`/api/marketplace/listings/${id}/activate`, {}, { params: { seller_id: sellerId } }),
  cancelListing: (id, sellerId) => api.post(`/api/marketplace/listings/${id}/cancel`, {}, { params: { seller_id: sellerId } }),

  // ── Cart ──
  getCart: (userId) => api.get(`/api/marketplace/cart/${userId}`),
  addToCart: (userId, listingId, quantity = 1) => api.post(`/api/marketplace/cart/${userId}/add`, { listing_id: listingId, quantity }),
  removeFromCart: (userId, listingId) => api.post(`/api/marketplace/cart/${userId}/remove`, {}, { params: { listing_id: listingId } }),
  updateCartItem: (userId, listingId, quantity) => api.post(`/api/marketplace/cart/${userId}/update`, { listing_id: listingId, quantity }),
  clearCart: (userId) => api.post(`/api/marketplace/cart/${userId}/clear`),
  checkout: (userId, data) => api.post(`/api/marketplace/cart/${userId}/checkout`, data),

  // ── Orders ──
  listOrders: (params) => api.get('/api/marketplace/orders', { params }),
  getOrder: (id) => api.get(`/api/marketplace/orders/${id}`),
  payOrder: (id, paymentTxId) => api.post(`/api/marketplace/orders/${id}/pay`, { payment_tx_id: paymentTxId }),
  fulfillOrder: (id, sellerId) => api.post(`/api/marketplace/orders/${id}/fulfill`, {}, { params: { seller_id: sellerId } }),
  completeOrder: (id, buyerId) => api.post(`/api/marketplace/orders/${id}/complete`, {}, { params: { buyer_id: buyerId } }),
  cancelOrder: (id, userId) => api.post(`/api/marketplace/orders/${id}/cancel`, {}, { params: { user_id: userId } }),
  disputeOrder: (id, userId, reason) => api.post(`/api/marketplace/orders/${id}/dispute`, { reason }, { params: { user_id: userId } }),
  refundOrder: (id, resolverId) => api.post(`/api/marketplace/orders/${id}/refund`, {}, { params: { resolver_id: resolverId } }),

  // ── Reviews ──
  addReview: (orderId, reviewerId, rating, title = '', body = '') =>
    api.post(`/api/marketplace/orders/${orderId}/review`, { rating, title, body }, { params: { reviewer_id: reviewerId } }),
  listReviews: (params) => api.get('/api/marketplace/reviews', { params }),

  // ── Stats ──
  getEngineStats: () => api.get('/api/marketplace/stats'),
};

// ═══════════════════════════════════════════════════════════════════
// MAIN ASIMNEXUS API — Aggregator
// ═══════════════════════════════════════════════════════════════════

export const asimnexusAPI = {
  // ── Core Chat ──
  ...chatAPI,

  // ── Authentication ──
  ...authAPI,

  // ── Brain (frontend compatibility) ──
  ...brainAPI,

  // ── Personal OS & Clones ──
  ...personalAPI,

  // ── Memory ──
  ...memoryAPI,

  // ── Local LLM ──
  ...localLLMAPI,

  // ── Health ──
  ...healthAPI,

  // ── Autonomous System ──
  ...autonomousAPI,

  // ── Group Chat ──
  ...groupChatAPI,

  // ── Enhanced Chat ──
  ...enhancedChatAPI,

  // ── Database ──
  ...databaseAPI,

  // ── System Operations ──
  ...systemOperationsAPI,

  // ── Cache ──
  ...cacheAPI,

  // ── Universal (World OS) ──
  ...universalAPI,

  // ── Identity / ZKP ──
  ...identityAPI,

  // ── SVT Token ──
  ...svtAPI,

  // ── HDT (Human Digital Twin) ──
  ...hdtAPI,

  // ── World OS / Quad Mesh ──
  ...worldOSAPI,

  // ── Dharma / Ethics ──
  ...dharmaAPI,

  // ── Mesh ──
  ...meshAPI,

  // ── Offline / Sync ──
  ...offlineAPI,

  // ── Analytics ──
  ...analyticsAPI,

  // ── Jobs / Marketplace ──
  ...jobsAPI,

  // ── Hybrid Economy ──
  ...hybridEconomyAPI,

  // ── Reputation ──
  ...reputationAPI,

  // ── Task Bus ──
  ...taskBusAPI,

  // ── Token Bridge ──
  ...bridgeAPI,

  // ── Marketplace Search ──
  ...marketplaceAPI,

  // ── Dreaming / AI Consciousness ──
  ...dreamingAPI,

  // ── Healing ──
  ...healingAPI,

  // ── Consensus / Clone Voting ──
  ...consensusAPI,

  // ── Clone Specializer ──
  ...clonesAPI,

  // ── OS Tools ──
  ...osToolsAPI,

  // ── Lifecycle / Life Journey ──
  ...lifecycleAPI,

  // ═════════════════════════════════════════════════════════════════
  // LEGACY ROUTES — No backend equivalent exists for these paths.
  // They call /api-prefixed or /health-fallback routes where possible.
  // ═════════════════════════════════════════════════════════════════

  /** @legacy — No GET /founders in backend. Use personalAPI.getClones() */
  getFounders: () => {
    console.warn('asimnexusAPI.getFounders() — no backend route. Use personalAPI.getClones()');
    return api.get('/personal/clones');
  },

  /** @legacy — No GET /founders/{id} in backend */
  getFounder: (id) => {
    console.warn('asimnexusAPI.getFounder() — no backend route.');
    return api.get('/personal/clones');
  },

  /** @legacy — No POST /founders in backend */
  createFounder: (data) => {
    console.warn('asimnexusAPI.createFounder() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No PUT /founders/{id} in backend */
  updateFounder: (id, data) => {
    console.warn('asimnexusAPI.updateFounder() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No GET /agents in backend */
  getAgents: () => {
    console.warn('asimnexusAPI.getAgents() — no backend route.');
    return api.get('/api/agent/status');
  },

  /** @legacy — No GET /agents/{id} in backend */
  getAgent: (id) => {
    console.warn('asimnexusAPI.getAgent() — no backend route.');
    return api.get('/api/agent/status');
  },

  /** @legacy — No POST /agents in backend */
  createAgent: (data) => {
    console.warn('asimnexusAPI.createAgent() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No PUT /agents/{id} in backend */
  updateAgent: (id, data) => {
    console.warn('asimnexusAPI.updateAgent() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No DELETE /agents/{id} in backend */
  deleteAgent: (id) => {
    console.warn('asimnexusAPI.deleteAgent() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No GET /security/events in backend */
  getSecurityEvents: () => {
    console.warn('asimnexusAPI.getSecurityEvents() — no backend route.');
    return api.get('/api/firewall/status');
  },

  /** @legacy — No GET /security/metrics in backend */
  getSecurityMetrics: () => {
    console.warn('asimnexusAPI.getSecurityMetrics() — no backend route.');
    return api.get('/api/firewall/status');
  },

  /** @legacy — No GET /virtual-office/rooms in backend */
  getVirtualRooms: () => {
    console.warn('asimnexusAPI.getVirtualRooms() — no backend route.');
    return Promise.resolve({ data: { rooms: [], message: 'Virtual office not available in backend' } });
  },

  /** @legacy — No POST /virtual-office/rooms in backend */
  createVirtualRoom: (data) => {
    console.warn('asimnexusAPI.createVirtualRoom() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No POST /virtual-office/rooms/{id}/join in backend */
  joinVirtualRoom: (roomId) => {
    console.warn('asimnexusAPI.joinVirtualRoom() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No GET /vr/avatars in backend */
  getVRAvatars: () => {
    console.warn('asimnexusAPI.getVRAvatars() — no backend route.');
    return Promise.resolve({ data: { avatars: [], message: 'VR not available in backend' } });
  },

  /** @legacy — No POST /vr/avatars in backend */
  createVRAvatar: (data) => {
    console.warn('asimnexusAPI.createVRAvatar() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No PUT /vr/avatars/{id}/position in backend */
  updateAvatarPosition: (id, data) => {
    console.warn('asimnexusAPI.updateAvatarPosition() — no backend route.');
    return Promise.resolve({ data: { success: false, message: 'Not available' } });
  },

  /** @legacy — No GET /analytics in backend. Use analyticsAPI.getOverview() */
  getAnalytics: () => {
    console.warn('asimnexusAPI.getAnalytics() deprecated. Use analyticsAPI.getOverview()');
    return api.get('/api/analytics/overview');
  },

  /** @legacy — No GET /analytics/predictions in backend */
  getPredictions: (target) => {
    console.warn('asimnexusAPI.getPredictions() — no backend route.');
    return Promise.resolve({ data: { predictions: [], message: 'Not available' } });
  },

  /** @legacy — No GET /system/metrics in backend */
  getSystemMetrics: () => {
    console.warn('asimnexusAPI.getSystemMetrics() — no backend route. Use healthAPI.check()');
    return api.get('/health');
  },

  /** @legacy — No GET /system/status in backend. Use chatAPI.getStatus() */
  getSystemStatus: () => {
    console.warn('asimnexusAPI.getSystemStatus() deprecated. Use chatAPI.getStatus()');
    return api.get('/status');
  },
};

// ═══════════════════════════════════════════════════════════════════
// STARTUP HEALTH CHECK
// Call once on app init to verify backend connectivity.
// ═══════════════════════════════════════════════════════════════════

export async function checkBackendHealth() {
  try {
    const res = await api.get('/health');
    const data = res.data || res;
    const healthy = data?.status === 'ok' || data?.success || !!data;
    if (healthy) {
      console.log('[AsimNexus] ✅ Backend connected:', data?.status || 'healthy');
    }
    return { healthy, data };
  } catch (err) {
    console.warn('[AsimNexus] ⚠️ Backend unreachable — running in offline/fallback mode');
    return { healthy: false, data: null };
  }
}

export default api;
