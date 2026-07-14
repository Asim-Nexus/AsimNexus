/**
 * ASIMNEXUS Social API — clones, healing, OS tools, sandbox, jobs, AR/VR, analytics
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const clonesAPI = {
    getSpecs: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/clones/specs'),
    getSpec: (cloneId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/clones/${cloneId}/spec`),
    route: (query: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/clones/route', { query }),
};
export const healingAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/healing/status'),
    getBalance: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/healing/balance'),
    heal: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/healing/heal'),
};
export const osToolsAPI = {
    listTools: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/tools'),
    execute: (toolName: string, params: Record<string, unknown> = {}, agentName: string = 'AutoModeAgent'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/os/execute', { tool_name: toolName, parameters: params, agent_name: agentName }),
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/status'),
    getMetrics: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/metrics'),
    getPending: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/pending'),
    approve: (callId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/os/approve/${callId}`),
    reject: (callId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/os/reject/${callId}`),
    getAudit: (limit: number = 30): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/audit', { params: { limit } }),
    getClipboardStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/os/clipboard/status'),
};
export const sandboxAPI = {
    execute: (toolId: string, parameters: Record<string, unknown>, userId: string = 'default', context: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/v1/sandbox/execute', { tool_id: toolId, parameters, user_id: userId, context }),
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/sandbox/status'),
};
export const jobsAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/jobs/stats'),
    list: (status: string = 'open', category: string | null = null): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/jobs/list', { params: { status, category } }),
    post: (jobData: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/jobs/post', jobData),
    apply: (jobId: string, coverNote: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/jobs/${jobId}/apply`, { cover_note: coverNote }),
};
export const arvrAPI = {
    /** GET /api/arvr/status — Get AR/VR interface status */
    getStatus: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/arvr/status'),

    /** GET /api/arvr/scene — Get current spatial scene */
    getScene: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/arvr/scene'),

    /** POST /api/arvr/mode — Set AR/VR interface mode (ar/vr/mr) */
    setMode: (mode: 'ar' | 'vr' | 'mr'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/arvr/mode', { mode }),

    /** POST /api/arvr/element — Create a spatial element in AR/VR space */
    createElement: (data: {
        position: Record<string, number>;
        content: string;
        rotation?: Record<string, number>;
        scale?: Record<string, number>;
        interactive?: boolean;
    }): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/arvr/element', data),

    /** POST /api/arvr/element/{element_id}/position — Update a spatial element's position */
    updateElementPosition: (elementId: string, position: Record<string, number>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/arvr/element/${elementId}/position`, { position }),

    /** DELETE /api/arvr/element/{element_id} — Remove a spatial element */
    removeElement: (elementId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.delete(`/api/arvr/element/${elementId}`),

    /** POST /api/arvr/gesture — Register a gesture command */
    registerGesture: (data: {
        gesture_type: string;
        target_element?: string;
        parameters?: Record<string, unknown>;
    }): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/arvr/gesture', data),

    /** POST /api/arvr/haptic — Trigger haptic feedback */
    triggerHaptic: (data: {
        intensity: number;
        duration_ms: number;
        pattern?: string;
    }): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/arvr/haptic', data),

    /** GET /api/arvr/gestures — Get recent gesture history */
    getGestureHistory: (limit: number = 10): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/arvr/gestures', { params: { limit } }),
};
export const analyticsAPI = {
    getOverview: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/analytics/overview'),
    getActivity: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/analytics/activity'),

    // ── Phase 4 — DePIN Network Map ──
    getDepinMap: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/analytics/depin/map'),
    getDepinCoverage: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/analytics/depin/coverage'),

    // ── Phase 4 — Clone Agents Live Feed ──
    getCloneAgentsFeed: (limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/analytics/clone-agents/feed', { params: { limit } }),
    getCloneAgentsStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/analytics/clone-agents/stats'),
};
export const consensusV1API = {
    vote: (topic: string, description: string = '', level: string = 'high'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/consensus/vote', { topic, description, level }),
    override: (roundId: string, approved: boolean = true, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/consensus/${roundId}/override`, { approved, reason }),
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/consensus/stats'),
    getPending: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/consensus/pending'),
    getList: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/consensus/list'),
};
export const consensusAPI = {
    vote: (title: string, description: string, sector: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/v1/consensus/vote', { title, description, sector }),
    weightedVote: (title: string, description: string, sector: string, govBenefit: string, privateBenefit: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/v1/consensus/weighted-vote', {
            title, description, sector, gov_benefit: govBenefit, private_benefit: privateBenefit
        }),
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/consensus/status'),
};
