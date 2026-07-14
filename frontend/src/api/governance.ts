/**
 * ASIMNEXUS Governance API — governance, government, nepal, stakeholder, enterprise, dharma
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const governanceAPI = {
    /** GET /api/governance/balance — Current 51/49 power balance across all sectors */
    getBalance: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/governance/balance'),

    /** GET /api/governance/balance/{sector} — Power balance for a specific sector */
    getSectorBalance: (sector: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/governance/balance/${sector}`),

    /** GET /api/governance/policies — List all government policies */
    getPolicies: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/governance/policies'),

    /** POST /api/governance/policy/approve — Approve a government policy */
    approvePolicy: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/policy/approve', data),

    /** POST /api/governance/veto — Issue a government veto */
    issueVeto: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/veto', data),

    /** POST /api/governance/veto/approve — Approve a pending veto */
    approveVeto: (vetoId: string, approver: string = 'government'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/veto/approve', { veto_id: vetoId, approver }),

    /** POST /api/governance/emergency/declare — Declare a government emergency */
    declareEmergency: (reason: string, initiatedBy: string = 'government'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/emergency/declare', { reason, initiated_by: initiatedBy }),

    /** POST /api/governance/emergency/resolve — Resolve a government emergency */
    resolveEmergency: (initiatedBy: string = 'government'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/emergency/resolve', { initiated_by: initiatedBy }),

    /** GET /api/governance/audit — Get government-layer audit log */
    getAuditLog: (limit: number = 100): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/governance/audit', { params: { limit } }),

    /** GET /api/governance/stats — Get comprehensive governance statistics */
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/governance/stats'),

    /** POST /api/governance/amendment/propose — Propose a constitutional amendment */
    proposeAmendment: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/amendment/propose', data),

    /** POST /api/governance/dharma/check — Check an action against Dharma Veto Engine */
    dharmaCheck: (action: string, agentId: string = 'government', context: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/governance/dharma/check', { action, agent_id: agentId, context }),
};
export const governmentAPI = {
    /** GET /api/government/status — Government integration status */
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/status'),

    /** GET /api/government/identity/countries — Countries with e-ID support */
    getIdentityCountries: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/identity/countries'),

    /** POST /api/government/identity/create — Create digital identity */
    createIdentity: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/government/identity/create', data),

    /** POST /api/government/identity/verify — Verify identity to a level */
    verifyIdentity: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/government/identity/verify', data),

    /** GET /api/government/eresidency/programs — Get available e-Residency programs */
    getEResidencyPrograms: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/eresidency/programs'),

    /** POST /api/government/eresidency/apply — Apply for e-Residency */
    applyEResidency: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/government/eresidency/apply', data),

    /** GET /api/government/tax/countries — Countries with tax filing support */
    getTaxCountries: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/tax/countries'),

    /** POST /api/government/tax/calculate — Calculate tax liability */
    calculateTax: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/government/tax/calculate', data),

    /** POST /api/government/tax/prepare — Prepare tax return */
    prepareTaxReturn: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/government/tax/prepare', data),

    /** GET /api/government/services/{country} — Get government services for a country */
    getServices: (country: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/government/services/${country}`),

    /** GET /api/government/signatures/regions — Get supported signature regions */
    getSignatureRegions: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/signatures/regions'),

    /** GET /api/government/stats — Get comprehensive government stats */
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/government/stats'),
};
export const nepalAPI = {
    /** GET /api/nepal/status — Nepal connector system status */
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/nepal/status'),

    /** GET /api/v1/np/ministries — List Nepal ministries */
    getMinistries: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/ministries'),

    /** GET /api/v1/np/provinces — List Nepal provinces */
    getProvinces: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/provinces'),

    /** GET /api/v1/np/districts — List Nepal districts */
    getDistricts: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/districts'),

    /** GET /api/v1/np/banks — List Nepal banks */
    getBanks: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/banks'),

    /** GET /api/v1/np/isps — List Nepal ISPs */
    getISPs: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/isps'),

    /** GET /api/v1/education/universities — List Nepal universities */
    getUniversities: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/education/universities'),

    /** GET /api/v1/education/schools — List Nepal schools */
    getSchools: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/education/schools'),

    /** GET /api/v1/health/hospitals — List Nepal hospitals */
    getHospitals: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/health/hospitals'),

    /** GET /api/v1/np/palikas — List Nepal palikas */
    getPalikas: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/np/palikas'),

    /** GET /api/v1/tourism/hotels — List Nepal hotels */
    getHotels: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/v1/tourism/hotels'),
};
export const stakeholderAPI = {
    /** GET /api/stakeholder/status — Coordinator system status */
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/stakeholder/status'),

    /** POST /api/stakeholder/action — Propose a new multi-stakeholder action */
    proposeAction: (data: {
        category: string;
        initiated_by: string;
        description: string;
        details?: Record<string, unknown>;
    }): Promise<AxiosResponse<ApiResponse>> => api.post('/api/stakeholder/action', data),

    /** POST /api/stakeholder/action/:id/approve — Approve/reject an action */
    approveAction: (
        actionId: string,
        data: { stakeholder: string; approved?: boolean; reason?: string }
    ): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/stakeholder/action/${actionId}/approve`, data),

    /** GET /api/stakeholder/action/:id — Get action details */
    getAction: (actionId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/stakeholder/action/${actionId}`),

    /** GET /api/stakeholder/actions — List actions (filtered) */
    listActions: (params?: {
        status?: string;
        category?: string;
        limit?: number;
    }): Promise<AxiosResponse<ApiResponse>> => api.get('/api/stakeholder/actions', { params }),

    /** GET /api/stakeholder/consensus — Get consensus decision log */
    getConsensusLog: (params?: {
        limit?: number;
        approved_only?: boolean;
    }): Promise<AxiosResponse<ApiResponse>> => api.get('/api/stakeholder/consensus', { params }),

    /** GET /api/stakeholder/stats — Coordinator statistics */
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/stakeholder/stats'),
};
export const enterpriseAPI = {
    /** GET /api/enterprise/status — Enterprise layer system status */
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/enterprise/status'),

    /** GET /api/enterprise/licenses — List all enterprise licenses */
    getLicenses: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/enterprise/licenses'),

    /** POST /api/enterprise/license/register — Register a new enterprise license */
    registerLicense: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/enterprise/license/register', data),

    /** POST /api/enterprise/license/deactivate — Deactivate an enterprise license */
    deactivateLicense: (licenseId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/enterprise/license/deactivate', { license_id: licenseId }),

    /** POST /api/enterprise/compliance/check — Check compliance for an action */
    checkCompliance: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/enterprise/compliance/check', data),

    /** GET /api/enterprise/compliance/log — Get compliance check history */
    getComplianceLog: (organization?: string, limit: number = 100): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/enterprise/compliance/log', { params: { organization, limit } }),

    /** GET /api/enterprise/stats — Get enterprise layer statistics */
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/enterprise/stats'),
};
export const dharmaAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dharma/status'),
    veto: (reason: string, severity: string = 'warning'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/dharma/veto', { reason, severity }),
    // ── Dharma Veto Evaluation ──
    evaluateVeto: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/dharma/veto/evaluate', data),
    getVetoHistory: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dharma/veto/history'),
    // ── Cultural Sovereignty ──
    getCulturalProfile: (userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/dharma/cultural/profile', { params: { user_id: userId } }),
    compileCultural: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/dharma/cultural/compile', data),
    // ── Delta-T Temporal Engine ──
    getDeltaTStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/dharma/delta-t/status'),
    simulateDeltaT: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/dharma/delta-t/simulate', data),
};
