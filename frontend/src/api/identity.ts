/**
 * ASIMNEXUS Identity API — identity, SVT, HDT, blockchain identity, soul key
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const identityAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/identity/stats'),
    getList: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/identity/list'),
    create: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.post('/api/identity/create', data),
    verify: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.post('/api/identity/verify', data),
};
export const svtAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/svt/stats'),
    createWallet: (did: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/svt/wallet', { did }),
    mint: (did: string, amount: number, memo: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/svt/mint', { did, amount, memo }),
    getWallet: (did: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/svt/wallet/${did}`),
};
export const hdtAPI = {
    create: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.post('/api/hdt/create', data),
    getStatus: (did: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/hdt/${did}/status`),
    addSkill: (did: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/hdt/${did}/skill`, data),
    announce: (did: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/hdt/${did}/announce`, {}),
};
export const blockchainIdentityAPI = {
    // ── DID (Decentralized Identifiers) ──
    createDID: (publicKey: string, network: string = 'ASIM_CHAIN'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/blockchain/did', { public_key: publicKey, network }),
    getDID: (did: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/blockchain/did/${did}`),
    listDIDs: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/blockchain/dids'),

    // ── Verifiable Credentials ──
    issueCredential: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/blockchain/credentials', data),
    listCredentials: (subjectDid: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/blockchain/credentials', { params: { subject_did: subjectDid } }),
    verifyCredential: (vcId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/blockchain/credentials/${vcId}`),
    revokeCredential: (vcId: string, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/blockchain/credentials/${vcId}/revoke`, { reason }),

    // ── Soulbound Tokens ──
    issueSBT: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/blockchain/sbt', data),
    listSBTs: (ownerDid: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/blockchain/sbt', { params: { owner_did: ownerDid } }),

    // ── Zero-Knowledge Proofs ──
    createZKP: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/blockchain/zkp', data),
    verifyZKP: (proofId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/blockchain/zkp/${proofId}`),

    // ── Stats ──
    getStats: (): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/blockchain/stats'),
};
export const soulKeyAPI = {
    create: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/soul-key/create', data),
    getSoulKey: (citizenId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/soul-key/${citizenId}`),
    addEvent: (citizenId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/soul-key/${citizenId}/events`, data),
    listEvents: (citizenId: string, limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/soul-key/${citizenId}/events`, { params: { limit } }),
    verify: (citizenId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/soul-key/${citizenId}/verify`),
    attest: (citizenId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/soul-key/${citizenId}/attest`, data),
    triggerLockout: (citizenId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/soul-key/${citizenId}/lockout`, data),
    getLockoutHistory: (citizenId: string, limit: number = 10): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/soul-key/${citizenId}/lockout-history`, { params: { limit } }),
    resolveLockout: (recordId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/soul-key/lockout/${recordId}/resolve`),
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/soul-key/stats'),
};
export const founderClonesAPI = {
    list: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/founder-clones/list'),
    spawn: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/founder-clones/spawn', data),
    getStatus: (cloneId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/founder-clones/${cloneId}/status`),
    assignTask: (cloneId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/founder-clones/${cloneId}/assign-task`, data),
    terminate: (cloneId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/founder-clones/${cloneId}/terminate`),
};
