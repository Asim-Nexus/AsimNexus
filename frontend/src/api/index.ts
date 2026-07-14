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
 * All modules map to routes in app.py (FastAPI backend, 224+ routes).
 * See docs/API_CONTRACT.md for the canonical route map.
 *
 * Auth storage key: localStorage('asimnexus_token')
 * Env var: REACT_APP_API_URL (default: http://localhost:8000)
 */

// ─── Shared Axios instance & auth helpers ──────────────────────
export {
    default as api,
    getStoredToken,
    getStoredUser,
    setAuth,
    clearAuth,
} from './asimnexus';

// ─── Domain API Modules ────────────────────────────────────────
export {
    authAPI,
} from './auth';

export {
    healthAPI,
    chatAPI,
    localLLMAPI,
    brainAPI,
    memoryAPI,
    databaseAPI,
    systemOperationsAPI,
    cacheAPI,
} from './core';

export {
    userProfileAPI,
    teamsAPI,
    personalAPI,
    autonomousAPI,
    groupChatAPI,
    enhancedChatAPI,
} from './personal';

export {
    hybridEconomyAPI,
    reputationAPI,
    taskBusAPI,
    bridgeAPI,
    marketplaceAPI,
    financeAPI,
} from './economy';

export {
    governanceAPI,
    governmentAPI,
    nepalAPI,
    stakeholderAPI,
    enterpriseAPI,
    dharmaAPI,
} from './governance';

export {
    identityAPI,
    svtAPI,
    hdtAPI,
    blockchainIdentityAPI,
    soulKeyAPI,
    founderClonesAPI,
} from './identity';

export {
    meshAPI,
    offlineAPI,
    depinAPI,
    rbeAPI,
    securityAPI,
} from './mesh';

export {
    universeAPI,
    worldOSAPI,
    lifecycleAPI,
    universalAPI,
} from './universe';

export {
    mirrorAPI,
    evolutionAPI,
    dreamingAPI,
    selfAwarenessAPI,
} from './mirror';

export {
    clonesAPI,
    healingAPI,
    osToolsAPI,
    sandboxAPI,
    jobsAPI,
    arvrAPI,
    analyticsAPI,
    consensusV1API,
    consensusAPI,
} from './social';

// ─── Legacy API (backward compat — asimnexusAPI) ───────────────
export {
    asimnexusAPI,
    checkBackendHealth,
} from './legacy';

// ─── Odysseus Agent/Tool/MCP API (from odysseus.js) ────────────
export {
    agentAPI,
    toolsAPI,
    mcpAPI,
    odysseusAPI,
} from './odysseus';

// ─── WebSocket API (from consolidated WebSocketService) ────────
export {
    wsService,
    websocketAPI,
} from '../services/WebSocketService';

// ─── Legacy / Services (backward compat) ───────────────────────
export { default as ApiService } from '../services/api';
