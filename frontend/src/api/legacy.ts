/**
 * ASIMNEXUS Legacy API (backward compatibility)
 * ==============================================
 * The monolithic asimnexusAPI object kept for components that still use it.
 * New code should import from the domain-specific modules via '../../api'.
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse } from '../types';

import {
    chatAPI, healthAPI, brainAPI, memoryAPI, localLLMAPI,
    databaseAPI, systemOperationsAPI, cacheAPI,
} from './core';
import { authAPI } from './auth';
import {
    personalAPI, autonomousAPI, groupChatAPI, enhancedChatAPI,
} from './personal';
import {
    hybridEconomyAPI, reputationAPI, taskBusAPI, bridgeAPI,
    marketplaceAPI,
} from './economy';
import {
    analyticsAPI, clonesAPI, healingAPI, osToolsAPI,
    jobsAPI, arvrAPI, consensusAPI,
} from './social';
import { identityAPI, svtAPI, hdtAPI, blockchainIdentityAPI } from './identity';
import { meshAPI, offlineAPI, depinAPI, rbeAPI } from './mesh';
import { universeAPI, worldOSAPI, lifecycleAPI, universalAPI } from './universe';
import { dreamingAPI } from './mirror';
import { dharmaAPI, governmentAPI, nepalAPI } from './governance';

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

    // ── AR/VR Immersive Interface ──
    ...arvrAPI,

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

    // ── RBE (Resource-Based Economy) ──
    ...rbeAPI,

    // ── DePIN (Decentralized Physical Infrastructure) ──
    ...depinAPI,

    // ── Blockchain Identity (DID / VC / SBT / ZKP) ──
    ...blockchainIdentityAPI,

    // ── Government (e-Residency, Tax, Digital Identity) ──
    ...governmentAPI,

    // ── Nepal Connectors (Ministries, Provinces, Districts) ──
    ...nepalAPI,

    // ═════════════════════════════════════════════════════════════════
    // LEGACY ROUTES — No backend equivalent exists for these paths.
    // ═════════════════════════════════════════════════════════════════

    /** @deprecated — No GET /founders in backend. Use personalAPI.getClones() */
    getFounders: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getFounders() — no backend route. Use personalAPI.getClones()');
        return api.get('/personal/clones');
    },

    /** @deprecated — No GET /founders/{id} in backend */
    getFounder: (_id: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getFounder() — no backend route.');
        return api.get('/personal/clones');
    },

    /** @deprecated — No POST /founders in backend */
    createFounder: (_data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.createFounder() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No PUT /founders/{id} in backend */
    updateFounder: (_id: string, _data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.updateFounder() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No GET /agents in backend */
    getAgents: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getAgents() — no backend route.');
        return api.get('/api/agent/status');
    },

    /** @deprecated — No GET /agents/{id} in backend */
    getAgent: (_id: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getAgent() — no backend route.');
        return api.get('/api/agent/status');
    },

    /** @deprecated — No POST /agents in backend */
    createAgent: (_data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.createAgent() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No PUT /agents/{id} in backend */
    updateAgent: (_id: string, _data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.updateAgent() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No DELETE /agents/{id} in backend */
    deleteAgent: (_id: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.deleteAgent() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No GET /security/events in backend */
    getSecurityEvents: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getSecurityEvents() — no backend route.');
        return api.get('/api/firewall/status');
    },

    /** @deprecated — No GET /security/metrics in backend */
    getSecurityMetrics: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getSecurityMetrics() — no backend route.');
        return api.get('/api/firewall/status');
    },

    /** @deprecated — No GET /virtual-office/rooms in backend */
    getVirtualRooms: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getVirtualRooms() — no backend route.');
        return Promise.resolve({ data: { rooms: [], message: 'Virtual office not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No POST /virtual-office/rooms in backend */
    createVirtualRoom: (_data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.createVirtualRoom() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No POST /virtual-office/rooms/{id}/join in backend */
    joinVirtualRoom: (_roomId: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.joinVirtualRoom() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No GET /vr/avatars in backend */
    getVRAvatars: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getVRAvatars() — no backend route.');
        return Promise.resolve({ data: { avatars: [], message: 'VR not available in backend' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No POST /vr/avatars in backend */
    createVRAvatar: (_data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.createVRAvatar() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No PUT /vr/avatars/{id}/position in backend */
    updateAvatarPosition: (_id: string, _data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.updateAvatarPosition() — no backend route.');
        return Promise.resolve({ data: { success: false, message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No GET /analytics in backend. Use analyticsAPI.getOverview() */
    getAnalytics: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getAnalytics() deprecated. Use analyticsAPI.getOverview()');
        return api.get('/api/analytics/overview');
    },

    /** @deprecated — No GET /analytics/predictions in backend */
    getPredictions: (_target: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getPredictions() — no backend route.');
        return Promise.resolve({ data: { predictions: [], message: 'Not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    /** @deprecated — No GET /system/metrics in backend */
    getSystemMetrics: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getSystemMetrics() — no backend route. Use healthAPI.check()');
        return api.get('/health');
    },

    /** @deprecated — No GET /system/status in backend. Use chatAPI.getStatus() */
    getSystemStatus: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('asimnexusAPI.getSystemStatus() deprecated. Use chatAPI.getStatus()');
        return api.get('/status');
    },
};

/**
 * Simple backend health check — returns true if the server responds.
 * Defined here for backward compatibility.
 */
export async function checkBackendHealth(): Promise<boolean> {
    try {
        const res = await api.get('/health');
        return res.status === 200;
    } catch {
        return false;
    }
}
