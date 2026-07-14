/**
 * ASIMNEXUS Mesh API — mesh networking, offline, depin, RBE, security
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const meshAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/mesh/status'),
    getPeers: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/mesh/peers'),
    getNodes: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/mesh/nodes'),
    discoverStart: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/mesh/discover/start'),
    addPeer: (ip: string, port: number = 8765): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/mesh/discover/add-peer', { ip, port }),
    airGapEngage: (level: number = 1, reason: string = 'Human-initiated'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/mesh/air-gap/engage', { level, reason }),
    airGapDisengage: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/mesh/air-gap/disengage'),
    checkConnectivity: (host: string = '8.8.8.8'): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/mesh/air-gap/check', { params: { host } }),
    initNode: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/mesh/node/init'),
};
export const offlineAPI = {
    getSyncStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/sync/status'),
    getQueue: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/sync/queue'),
    enqueue: (opType: string, entityType: string, entityId: string, payload: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/sync/enqueue', { op_type: opType, entity_type: entityType, entity_id: entityId, payload }),
    flushQueue: (): Promise<AxiosResponse<ApiResponse>> => api.post('/api/sync/flush'),
    getUserOfflineStatus: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/mesh/offline/status/${userId}`),
    getCapabilities: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/mesh/offline/capabilities'),
    createOperation: (operationType: string, payload: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/mesh/offline/operation', { operation_type: operationType, ...payload }),
};
export const depinAPI = {
    // ── Uplink (Decentralized Wireless) ──
    uplinkConnect: (apiKey: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/uplink/connect', { api_key: apiKey }),
    uplinkDisconnect: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/uplink/disconnect'),
    uplinkRegisterNode: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/uplink/nodes', data),
    uplinkOffload: (nodeId: string, amountMbps: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/uplink/nodes/${nodeId}/offload`, { amount_mbps: amountMbps }),
    uplinkRelease: (nodeId: string, amountMbps: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/uplink/nodes/${nodeId}/release`, { amount_mbps: amountMbps }),
    uplinkClaimRewards: (nodeId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/uplink/nodes/${nodeId}/rewards`),
    uplinkStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/depin/uplink/stats'),

    // ── Daylight (Decentralized Energy) ──
    daylightConnect: (apiKey: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/daylight/connect', { api_key: apiKey }),
    daylightDisconnect: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/daylight/disconnect'),
    daylightRegisterDevice: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/daylight/devices', data),
    daylightUpdateOutput: (deviceId: string, outputKwh: number, state: string = 'idle'): Promise<AxiosResponse<ApiResponse>> =>
        api.put(`/api/depin/daylight/devices/${deviceId}/output`, { output_kwh: outputKwh, state }),
    daylightSellEnergy: (deviceId: string, amountKwh: number, pricePerKwh: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/daylight/devices/${deviceId}/sell`, { amount_kwh: amountKwh, price_per_kwh: pricePerKwh }),
    daylightBuyEnergy: (amountKwh: number, maxPricePerKwh: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/daylight/buy', { amount_kwh: amountKwh, max_price_per_kwh: maxPricePerKwh }),
    daylightClaimCarbonCredits: (deviceId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/daylight/devices/${deviceId}/carbon-credits`),
    daylightStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/depin/daylight/stats'),

    // ── DIMO (Decentralized Vehicles) ──
    dimoConnect: (apiKey: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/dimo/connect', { api_key: apiKey }),
    dimoDisconnect: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/dimo/disconnect'),
    dimoRegisterVehicle: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/depin/dimo/vehicles', data),
    dimoUpdateTelemetry: (vehicleId: string, dataType: string, value: number): Promise<AxiosResponse<ApiResponse>> =>
        api.put(`/api/depin/dimo/vehicles/${vehicleId}/telemetry`, { data_type: dataType, value }),
    dimoShareData: (vehicleId: string, dataTypes: string[], durationMinutes: number = 60): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/dimo/vehicles/${vehicleId}/share`, { data_types: dataTypes, duration_minutes: durationMinutes }),
    dimoGrantPermission: (vehicleId: string, dataType: string, grantee: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/dimo/vehicles/${vehicleId}/permissions`, { data_type: dataType, grantee }),
    dimoRevokePermission: (vehicleId: string, dataType: string, grantee: string): Promise<AxiosResponse<ApiResponse>> =>
        api.delete(`/api/depin/dimo/vehicles/${vehicleId}/permissions`, { data: { data_type: dataType, grantee } }),
    dimoClaimRewards: (vehicleId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/depin/dimo/vehicles/${vehicleId}/rewards`),
    dimoStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/depin/dimo/stats'),

    // ── Aggregate Status ──
    getStatus: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/depin/status'),
};
export const rbeAPI = {
    // ── Resources ──
    addResource: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/rbe/resources', data),

    // ── Demand ──
    submitDemand: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/rbe/demand', data),

    // ── Allocation ──
    allocate: (requestId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/rbe/allocate', { request_id: requestId }),
    allocateAll: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/rbe/allocate-all'),

    // ── Status ──
    getStatus: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/rbe/status'),
    getEquilibrium: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/rbe/equilibrium'),

    // ── Regeneration ──
    regenerate: (): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/rbe/regenerate'),
};
export const securityAPI = {
    // ── TPM Hardware Key Status ──
    getTPMStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/security/tpm/status'),
    getTPMKeys: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/security/tpm/keys'),
    generateTPMKey: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/security/tpm/key/generate', data),

    // ── Level-3 with TPM Hardware Key ──
    verifyLevel3TPM: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/confirm/level3/tpm/verify', data),
    getLevel3TPMKeyStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/confirm/level3/tpm/key-status'),
};
