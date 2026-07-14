/**
 * ASIMNEXUS Mirror API — mirror, evolution, dreaming, self-awareness
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const mirrorAPI = {
    reflect: (userId: string, action: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/v1/mirror/reflect', { user_id: userId, action }),
    getDaily: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/v1/mirror/daily/${userId}`),
    dream: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/v1/mirror/dream', { user_id: userId }),
    fineTune: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/v1/mirror/fine-tune', { user_id: userId }),
    getState: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/v1/mirror/state/${userId}`),
};
export const evolutionAPI = {
    getSuggestions: (category?: string, status?: string, limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/evolution/suggestions', { params: { category, status, limit } }),
    getPendingReview: (limit: number = 20): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/evolution/suggestions/pending-review', { params: { limit } }),
    getSuggestion: (suggestionId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/evolution/suggestions/${suggestionId}`),
    approveSuggestion: (suggestionId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/evolution/suggestions/${suggestionId}/approve`),
    rejectSuggestion: (suggestionId: string, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/evolution/suggestions/${suggestionId}/reject`, { reason }),
    getEvents: (limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/evolution/events', { params: { limit } }),
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/evolution/stats'),
    getHistory: (limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/evolution/history', { params: { limit } }),
};
export const dreamingAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dreaming/status'),
    getBriefing: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dreaming/briefing'),
    trigger: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/dreaming/trigger'),
};
export const selfAwarenessAPI = {
    /** GET /api/self/knowledge/summary — Get knowledge summary */
    getSummary: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/knowledge/summary'),

    /** GET /api/self/knowledge/modules — Get all modules */
    getModules: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/knowledge/modules'),

    /** GET /api/self/knowledge/routes — Get all routes */
    getRoutes: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/knowledge/routes'),

    /** GET /api/self/knowledge/issues — Get all issues */
    getIssues: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/knowledge/issues'),

    /** GET /api/self/builder/history — Get build action history */
    getBuildHistory: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/builder/history'),

    /** GET /api/self/builder/stats — Get builder statistics */
    getBuildStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/builder/stats'),

    /** POST /api/self/scan — Trigger a codebase scan */
    triggerScan: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/self/scan'),

    /** GET /api/self/bridge/stats — Get evolution bridge stats */
    getBridgeStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/self/bridge/stats'),
};
