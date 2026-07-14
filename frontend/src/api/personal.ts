/**
 * ASIMNEXUS Personal API — user profile, teams, personal agents, autonomous mode
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const userProfileAPI = {
    getProfile: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/user/profile'),
    updateProfile: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.put('/api/user/profile', data),
    getPublicProfile: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/user/profiles/${userId}`),
};
export const teamsAPI = {
    list: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/teams'),
    create: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/teams', data),
    get: (teamId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/teams/${teamId}`),
    update: (teamId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.put(`/api/teams/${teamId}`, data),
    inviteMember: (teamId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/teams/${teamId}/members`, data),
    getMembers: (teamId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/teams/${teamId}/members`),
    removeMember: (teamId: string, userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.delete(`/api/teams/${teamId}/members/${userId}`),
    changeMemberRole: (teamId: string, userId: string, role: string): Promise<AxiosResponse<ApiResponse>> =>
        api.put(`/api/teams/${teamId}/members/${userId}/role`, { role }),
    getPermissions: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/permissions'),
};
export const personalAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/personal/status'),
    getClones: (): Promise<AxiosResponse<ApiResponse>> => api.get('/personal/clones'),
    getPersonalStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/personal/status'),
    getUniverse: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/personal/universe'),
    getContracts: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/personal/contracts'),
    agentModeOn: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/agent/mode/on'),
    agentModeOff: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/agent/mode/off'),
    getAgentStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/agent/status'),
    getUniverseStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universe/status'),
    getResourceSharing: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/personal/resource-sharing'),
    setResourceSharing: (enabled: boolean, percentage: number = 2): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/personal/resource-sharing', { enabled, resource_percentage: percentage }),
};
export const autonomousAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/agent/status'),

    getFounders: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('autonomousAPI.getFounders() has no backend endpoint.');
        return api.get('/api/agent/status');
    },

    toggleAutopilot: (enabled: boolean): Promise<AxiosResponse<ApiResponse>> =>
        enabled ? api.post('/api/agent/mode/on') : api.post('/api/agent/mode/off'),

    getKeysStatus: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('autonomousAPI.getKeysStatus() has no backend endpoint.');
        return api.get('/api/agent/status');
    },

    addApiKey: (keyData: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('autonomousAPI.addApiKey() has no backend endpoint.');
        return api.post('/api/keys/update', keyData);
    },

    getTasks: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('autonomousAPI.getTasks() has no backend endpoint.');
        return api.get('/api/agent/status');
    },
};
export const groupChatAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('groupChatAPI.getStatus() — no backend endpoint.');
        return api.get('/status');
    },

    getHistory: (limit: number = 50): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('groupChatAPI.getHistory() — no backend endpoint. Use memoryAPI.getRecent() instead.');
        return api.get('/api/memory/recent', { params: { limit } });
    },

    getFounders: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('groupChatAPI.getFounders() — no backend endpoint.');
        return api.get('/personal/clones');
    },
};
export const enhancedChatAPI = {
    sendMessage: (message: string, userId: number = 1, _conversationId: string | null = null, _modelId: string = 'qwen3-4b'): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('enhancedChatAPI.sendMessage() deprecated. Use brainAPI.process() instead.');
        return api.post('/api/brain/process', { message, user_id: String(userId), mode: 'personal' });
    },

    streamMessage: (message: string, userId: number = 1, _conversationId: string | null = null, _modelId: string = 'qwen3-4b'): EventSource => {
        console.warn('enhancedChatAPI.streamMessage() deprecated. Use brainAPI.stream() instead.');
        return new EventSource(`${BASE}/api/brain/stream?message=${encodeURIComponent(message)}&user_id=${userId}`);
    },

    getHistory: (_conversationId: string, limit: number = 50): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('enhancedChatAPI.getHistory() deprecated. Use memoryAPI.getRecent() instead.');
        return api.get('/api/memory/recent', { params: { limit } });
    },

    clearCache: (_conversationId: string): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('enhancedChatAPI.clearCache() has no backend endpoint.');
        return Promise.resolve({ data: { success: true, message: 'No-op: backend cache clear not available' } } as unknown as AxiosResponse<ApiResponse>);
    },

    testContext: (): Promise<AxiosResponse<ApiResponse>> => {
        console.warn('enhancedChatAPI.testContext() has no backend endpoint.');
        return api.get('/api/memory/stats');
    },
};
