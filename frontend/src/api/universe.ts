/**
 * ASIMNEXUS Universe API — universe, world OS, lifecycle, universal
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const universeAPI = {
    create: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/create', data),
    getStatus: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/status', { params: { user_id: userId } }),
    getLifecycle: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/lifecycle', { params: { user_id: userId } }),
    activateLayer: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/layer/activate', data),
    updateState: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/state/update', data),
    recordActivity: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/activity/record', data),
    addConnection: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/connection/add', data),
    migrate: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/migrate', data),
    archive: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/archive', data),
    reactivate: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/reactivate', data),
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universe/stats'),
    getPrivacyScore: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/privacy-score', { params: { user_id: userId } }),
};
export const worldOSAPI = {
    getQuadStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/quad/status'),
    getBugStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/bugs/stats'),
    getDHTStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dht/status'),
    getFirewallStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/firewall/status'),
};
export const lifecycleAPI = {
    getLifecycle: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/lifecycle', { params: { user_id: userId } }),

    getStatus: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/status', { params: { user_id: userId } }),

    activateLayer: (userId: string, layerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/universe/layer/activate', { user_id: userId, layer_id: layerId }),

    getStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/universe/stats'),
};
export const universalAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universal/status'),
    getCountries: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universal/countries'),
    getCurrencies: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universal/currencies'),
    getLanguages: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universal/languages'),
    getTimezones: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/universal/timezones'),
};
