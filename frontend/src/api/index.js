/**
 * ASIMNEXUS Unified API Index
 * =============================
 * Single entry point for ALL frontend API modules.
 *
 * Usage:
 *   import { authAPI, chatAPI, meshAPI, healthAPI } from '../../api';
 *   import { agentAPI, toolsAPI, mcpAPI } from '../../api';
 *   import { wsManager, websocketAPI } from '../../api';
 *
 * All modules map to routes in simple_backend.py (FastAPI backend).
 * See docs/API_CONTRACT.md for the canonical route map.
 *
 * Auth storage key: localStorage('asimnexus_token')
 * Env var: REACT_APP_API_URL (default: http://localhost:8000)
 */

// ─── Core API Modules (from asimnexus.js) ──────────────────────
export {
  // Axios instance & auth helpers
  getStoredToken,
  getStoredUser,
  setAuth,
  clearAuth,

  // Domain API modules
  authAPI,
  userProfileAPI,
  teamsAPI,
  healthAPI,
  chatAPI,
  localLLMAPI,
  brainAPI,
  memoryAPI,
  personalAPI,
  autonomousAPI,
  groupChatAPI,
  enhancedChatAPI,
  databaseAPI,
  systemOperationsAPI,
  cacheAPI,
  lifecycleAPI,
  universalAPI,
  identityAPI,
  svtAPI,
  hdtAPI,
  worldOSAPI,
  dharmaAPI,
  meshAPI,
  offlineAPI,
  analyticsAPI,
  jobsAPI,
  hybridEconomyAPI,
  reputationAPI,
  taskBusAPI,
  bridgeAPI,
  marketplaceAPI,
  dreamingAPI,
  consensusAPI,
  clonesAPI,
  healingAPI,
  osToolsAPI,
  asimnexusAPI,
  checkBackendHealth,
} from './asimnexus';

// ─── Odysseus Agent/Tool/MCP API (from odysseus.js) ────────────
export {
  agentAPI,
  toolsAPI,
  mcpAPI,
  odysseusAPI,
} from './odysseus';

// ─── WebSocket API (from websocket.js) ─────────────────────────
export {
  wsManager,
  websocketAPI,
} from './websocket';

// ─── Default Axios instance ────────────────────────────────────
export { default as api } from './asimnexus';

// ─── Legacy / Services (backward compat) ───────────────────────
export { default as ApiService } from '../services/api';
export { default as WebSocketService } from '../services/WebSocketService';
export { default as wsService } from '../services/websocket';
