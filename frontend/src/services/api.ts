/**
 * ASIMNEXUS API Service
 * ======================
 * Legacy fetch-based API service.
 *
 * @deprecated Use the axios-based API modules in api/asimnexus.ts instead.
 *   Import from '../../api' for the canonical API client.
 *
 * This file now delegates all calls to the canonical asimnexus.ts API client.
 * Kept for backward compatibility — all new code should import from '../../api'.
 */

import axiosApi, {
    authAPI,
    personalAPI,
    dharmaAPI,
    meshAPI,
    offlineAPI,
    universalAPI,
    osToolsAPI,
    clonesAPI,
} from '../api/asimnexus';

interface FetchOptions {
    method?: string;
    body?: string;
    [key: string]: unknown;
}

interface LegacyResponse {
    status?: string;
    message?: string;
    success?: boolean;
    [key: string]: unknown;
}

/**
 * Legacy ApiService — delegates to the canonical axios-based API client.
 * @deprecated Import from '../../api' instead.
 */
class ApiService {
    // ── Generic HTTP methods (delegate to axios) ──────────────────

    async fetch(endpoint: string, options: FetchOptions = {}): Promise<unknown> {
        const method = (options.method || 'GET').toLowerCase();
        try {
            const config: Record<string, unknown> = { ...options };
            delete config.method;
            if (config.body) {
                config.data = JSON.parse(config.body as string);
                delete config.body;
            }
            const response = await (axiosApi as unknown as Record<string, Function>)[method](endpoint, config);
            return response.data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    get(endpoint: string): Promise<unknown> {
        return this.fetch(endpoint, { method: 'GET' });
    }

    post(endpoint: string, data: unknown): Promise<unknown> {
        return this.fetch(endpoint, { method: 'POST', body: JSON.stringify(data) });
    }

    // ── Auth ──────────────────────────────────────────────────────

    async login(email: string, password: string): Promise<unknown> {
        const response = await authAPI.login(email, password);
        const data = response.data as unknown as Record<string, unknown>;
        return data;
    }

    async register(email: string, password: string, displayName: string): Promise<unknown> {
        return authAPI.register(displayName, email, password);
    }

    logout(): void {
        localStorage.removeItem('asimnexus_token');
        localStorage.removeItem('asimnexus_user');
    }

    // ── System Status ─────────────────────────────────────────────

    async getSystemStatus(): Promise<unknown> {
        return (await axiosApi.get('/api/system/complete')).data;
    }

    async getSystemInfo(): Promise<unknown> {
        return (await axiosApi.get('/api/system/info')).data;
    }

    // ── Dharma / ΔT Engine ───────────────────────────────────────

    async getDharmaStatus(): Promise<unknown> {
        return (await dharmaAPI.getStatus()).data;
    }

    async submitVeto(reason: string, severity: string = 'warning'): Promise<unknown> {
        return (await dharmaAPI.veto(reason, severity)).data;
    }

    // ── Personal OS ───────────────────────────────────────────────

    async getPersonalStatus(): Promise<unknown> {
        return (await personalAPI.getPersonalStatus()).data;
    }

    async getPersonalUniverse(): Promise<unknown> {
        return (await personalAPI.getUniverse()).data;
    }

    async getContracts(): Promise<unknown> {
        return (await personalAPI.getContracts()).data;
    }

    // ── Agent Mode ────────────────────────────────────────────────

    async activateAgent(_skills: string, _maxDays: number = 15): Promise<unknown> {
        return (await personalAPI.agentModeOn()).data;
    }

    async deactivateAgent(): Promise<unknown> {
        return (await personalAPI.agentModeOff()).data;
    }

    async getAgentStatus(): Promise<unknown> {
        return (await personalAPI.getAgentStatus()).data;
    }

    // ── Financial (legacy routes — may not exist in backend) ──────

    async getFinanceStatus(): Promise<LegacyResponse> {
        console.warn('ApiService.getFinanceStatus() — legacy route. Use hybridEconomyAPI instead.');
        return { status: 'legacy', message: 'Use hybridEconomyAPI' };
    }

    async getCurrencies(): Promise<unknown> {
        return (await universalAPI.getCurrencies()).data;
    }

    async getExchangeRates(base: string = 'USD'): Promise<LegacyResponse> {
        console.warn('ApiService.getExchangeRates() — legacy route.');
        return { base, rates: {} };
    }

    async createWallet(_demoMode: boolean = true): Promise<LegacyResponse> {
        console.warn('ApiService.createWallet() — legacy route. Use hybridEconomyAPI instead.');
        return { success: false, message: 'Use hybridEconomyAPI' };
    }

    async getWallet(_userId: string): Promise<LegacyResponse> {
        console.warn('ApiService.getWallet() — legacy route. Use hybridEconomyAPI instead.');
        return { success: false, message: 'Use hybridEconomyAPI' };
    }

    // ── Government (legacy routes) ────────────────────────────────

    async getGovernmentStatus(): Promise<LegacyResponse> {
        console.warn('ApiService.getGovernmentStatus() — legacy route.');
        return { status: 'legacy' };
    }

    async getIdentityCountries(): Promise<unknown[]> {
        console.warn('ApiService.getIdentityCountries() — legacy route.');
        return [];
    }

    async getEResidencyPrograms(): Promise<unknown[]> {
        console.warn('ApiService.getEResidencyPrograms() — legacy route.');
        return [];
    }

    async getTaxCountries(): Promise<unknown[]> {
        console.warn('ApiService.getTaxCountries() — legacy route.');
        return [];
    }

    // ── Mesh Network ──────────────────────────────────────────────

    async getMeshStatus(): Promise<unknown> {
        return (await meshAPI.getStatus()).data;
    }

    async getMeshStats(): Promise<unknown> {
        return (await meshAPI.getStatus()).data;
    }

    async discoverMeshNodes(): Promise<unknown> {
        return (await meshAPI.discoverStart()).data;
    }

    async initMeshNode(_nodeType: string, _name: string, _country: string): Promise<unknown> {
        return (await meshAPI.initNode()).data;
    }

    async getFederationMap(): Promise<LegacyResponse> {
        console.warn('ApiService.getFederationMap() — legacy route.');
        return { nodes: [] };
    }

    async joinFederation(_nodeId: string, _level: string = 'full'): Promise<LegacyResponse> {
        console.warn('ApiService.joinFederation() — legacy route.');
        return { success: false };
    }

    // ── Clone Sync ────────────────────────────────────────────────

    async getCloneStatus(_userId: string): Promise<unknown> {
        console.warn('ApiService.getCloneStatus() — legacy route.');
        return (await clonesAPI.getSpecs()).data;
    }

    async syncClone(_userId: string, _priority: string = 'normal', _direction: string = 'bidirectional', _data: Record<string, unknown> = {}): Promise<LegacyResponse> {
        console.warn('ApiService.syncClone() — legacy route.');
        return { success: false };
    }

    // ── Offline Sync ──────────────────────────────────────────────

    async getOfflineStatus(userId: string): Promise<unknown> {
        return (await offlineAPI.getUserOfflineStatus(userId)).data;
    }

    async getOfflineCapabilities(): Promise<unknown> {
        return (await offlineAPI.getCapabilities()).data;
    }

    async createOfflineOperation(userId: string, nodeId: string, operation: string, target: string, data: Record<string, unknown>): Promise<unknown> {
        return (await offlineAPI.createOperation(operation, { user_id: userId, node_id: nodeId, target, ...data })).data;
    }

    // ── Sovereignty (Air-Gap) ─────────────────────────────────────

    async getAirGapStatus(): Promise<unknown> {
        return (await meshAPI.checkConnectivity()).data;
    }

    async getAirGapHistory(): Promise<unknown[]> {
        console.warn('ApiService.getAirGapHistory() — legacy route.');
        return [];
    }

    async activateAirGap(mode: string = 'partial', reason: string = 'User requested'): Promise<unknown> {
        return (await meshAPI.airGapEngage(mode === 'full' ? 2 : 1, reason)).data;
    }

    async restoreConnection(_verifyIntegrity: boolean = true): Promise<unknown> {
        return (await meshAPI.airGapDisengage()).data;
    }

    // ── Universal ─────────────────────────────────────────────────

    async getUniversalCurrencies(): Promise<unknown> {
        return (await universalAPI.getCurrencies()).data;
    }

    async getUniversalCountries(): Promise<unknown> {
        return (await universalAPI.getCountries()).data;
    }

    async getUniversalLanguages(): Promise<unknown> {
        return (await universalAPI.getLanguages()).data;
    }

    // ── Accessibility (legacy) ────────────────────────────────────

    async getAccessibilityStatus(): Promise<LegacyResponse> {
        console.warn('ApiService.getAccessibilityStatus() — legacy route.');
        return { status: 'unknown' };
    }

    async getAccessibilityWCAG(): Promise<LegacyResponse> {
        console.warn('ApiService.getAccessibilityWCAG() — legacy route.');
        return { compliance: 'unknown' };
    }

    // ── Performance (legacy) ──────────────────────────────────────

    async getPerformanceStatus(): Promise<LegacyResponse> {
        console.warn('ApiService.getPerformanceStatus() — legacy route.');
        return { status: 'unknown' };
    }

    async optimizePerformance(_connectionType: string): Promise<LegacyResponse> {
        console.warn('ApiService.optimizePerformance() — legacy route.');
        return { success: false };
    }

    // ── Security (legacy) ─────────────────────────────────────────

    async getSecurityStatus(): Promise<LegacyResponse> {
        console.warn('ApiService.getSecurityStatus() — legacy route.');
        return { status: 'unknown' };
    }

    async getEncryptionAlgorithms(): Promise<unknown[]> {
        console.warn('ApiService.getEncryptionAlgorithms() — legacy route.');
        return [];
    }

    // ── OS Control ────────────────────────────────────────────────

    async getOsTools(): Promise<unknown> {
        return (await osToolsAPI.listTools()).data;
    }

    async executeOsTool(toolName: string, parameters: Record<string, unknown> = {}, agentName: string = 'AutoModeAgent'): Promise<unknown> {
        return (await osToolsAPI.execute(toolName, parameters, agentName)).data;
    }

    async getOsPending(): Promise<unknown> {
        return (await osToolsAPI.getPending()).data;
    }

    async approveOsCall(callId: string): Promise<unknown> {
        return (await osToolsAPI.approve(callId)).data;
    }

    async rejectOsCall(callId: string): Promise<unknown> {
        return (await osToolsAPI.reject(callId)).data;
    }

    async getOsAudit(limit: number = 30): Promise<unknown> {
        return (await osToolsAPI.getAudit(limit)).data;
    }

    async getOsStatus(): Promise<unknown> {
        return (await osToolsAPI.getStatus()).data;
    }

    async getOsMetrics(): Promise<unknown> {
        return (await osToolsAPI.getMetrics()).data;
    }

    async getKernelStatus(): Promise<unknown> {
        console.warn('ApiService.getKernelStatus() — legacy route.');
        return (await osToolsAPI.getStatus()).data;
    }
}

// Export singleton
export const api = new ApiService();

// Hook for React components
export function useApi(): ApiService {
    return api;
}

export default api;
