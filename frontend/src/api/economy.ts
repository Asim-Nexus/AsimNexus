/**
 * ASIMNEXUS Economy API — marketplace, hybrid economy, reputation, task bus, bridge, finance
 * ========================================
 * Extracted from monolithic asimnexus.ts during M5 refactoring.
 * Import via the barrel index: `import { ... } from '../../api';`
 */

import api from './asimnexus';
import { AxiosResponse } from 'axios';
import type { ApiResponse, User, HealthStatus } from '../types';

export const hybridEconomyAPI = {
    getSummary: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/hybrid-economy/summary'),
    setMode: (mode: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/hybrid-economy/mode', { mode }),
    createAccount: (ownerId: string, ownerType: string, initialBalance: number = 0): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/account', { owner_id: ownerId, owner_type: ownerType, initial_balance: initialBalance }),
    getAccount: (ownerId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/hybrid-economy/account/${ownerId}`),
    listAccounts: (ownerType?: string): Promise<AxiosResponse<ApiResponse>> => api.get('/api/hybrid-economy/accounts', { params: { owner_type: ownerType } }),
    deposit: (ownerId: string, amount: number, memo: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/deposit', { owner_id: ownerId, amount, memo }),
    withdraw: (ownerId: string, amount: number, memo: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/withdraw', { owner_id: ownerId, amount, memo }),
    transfer: (fromId: string, toId: string, amount: number, memo: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/transfer', { from_id: fromId, to_id: toId, amount, memo }),
    createTask: (description: string, requesterId: string, reward: number, category: string = 'general'): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/task', { description, requester_id: requesterId, reward, category }),
    assignTask: (taskId: string, executorId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/hybrid-economy/task/assign', { task_id: taskId, executor_id: executorId }),
    listTasks: (params: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> => api.get('/api/hybrid-economy/tasks', { params }),
};
export const reputationAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/reputation/stats'),
    getLeaderboard: (limit: number = 10): Promise<AxiosResponse<ApiResponse>> => api.get('/api/reputation/leaderboard', { params: { limit } }),
    register: (entityId: string, initialScore: number = 0): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/reputation/register', { entity_id: entityId, initial_score: initialScore }),
    get: (entityId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/reputation/${entityId}`),
    getEvents: (entityId: string, limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/reputation/${entityId}/events`, { params: { limit } }),
    add: (entityId: string, amount: number, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/reputation/add', { entity_id: entityId, amount, reason }),
    remove: (entityId: string, amount: number, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/reputation/remove', { entity_id: entityId, amount, reason }),
    stake: (entityId: string, amount: number, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/reputation/stake', { entity_id: entityId, amount, reason }),
    unstake: (stakeId: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/reputation/unstake', { stake_id: stakeId }),
    slash: (stakeId: string, penaltyPct: number = 1.0, reason: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/reputation/slash', { stake_id: stakeId, penalty_pct: penaltyPct, reason }),
};
export const taskBusAPI = {
    getStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/task-bus/status'),
    registerAgent: (agentId: string, capabilities: string[] = [], displayName: string = '', maxConcurrent: number = 5): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/task-bus/agent/register', { agent_id: agentId, capabilities, display_name: displayName, max_concurrent: maxConcurrent }),
    unregisterAgent: (agentId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/task-bus/agent/${agentId}/unregister`),
    listAgents: (onlineOnly: boolean = false): Promise<AxiosResponse<ApiResponse>> => api.get('/api/task-bus/agents', { params: { online_only: onlineOnly } }),
    submitTask: (taskType: string, payload: Record<string, unknown> = {}, priority: string = 'medium', maxRetries: number = 3): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/task-bus/task/submit', { task_type: taskType, payload, priority, max_retries: maxRetries }),
    assignNext: (agentId: string): Promise<AxiosResponse<ApiResponse>> => api.post('/api/task-bus/task/assign-next', { agent_id: agentId }),
    listTasks: (params: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> => api.get('/api/task-bus/tasks', { params }),
    getTask: (taskId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/task-bus/task/${taskId}`),
    startTask: (taskId: string, agentId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/task-bus/task/${taskId}/start`, null, { params: { agent_id: agentId } }),
    completeTask: (taskId: string, agentId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/task-bus/task/${taskId}/complete`, { task_id: taskId, agent_id: agentId }),
    failTask: (taskId: string, agentId: string, error: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/task-bus/task/${taskId}/fail`, { task_id: taskId, agent_id: agentId, error }),
    cancelTask: (taskId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/task-bus/task/${taskId}/cancel`),
    heartbeat: (agentId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/task-bus/agent/${agentId}/heartbeat`),
};
export const bridgeAPI = {
    getStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/bridge/stats'),
    createPool: (chain: string, tokenSymbol: string, initialBalance: number = 0): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/bridge/pool/create', { chain, token_symbol: tokenSymbol, initial_balance: initialBalance }),
    listPools: (chain?: string): Promise<AxiosResponse<ApiResponse>> => api.get('/api/bridge/pools', { params: { chain } }),
    addLiquidity: (poolId: string, amount: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/bridge/pool/add-liquidity', { pool_id: poolId, amount }),
    removeLiquidity: (poolId: string, amount: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/bridge/pool/remove-liquidity', { pool_id: poolId, amount }),
    initiate: (fromChain: string, toChain: string, asset: string, amount: number, sender: string, recipient: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/bridge/initiate', { from_chain: fromChain, to_chain: toChain, asset, amount, sender, recipient }),
    getTransaction: (txId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/bridge/tx/${txId}`),
    listTransactions: (params: Record<string, unknown> = {}): Promise<AxiosResponse<ApiResponse>> => api.get('/api/bridge/transactions', { params }),
    calculateFee: (fromChain: string, amount: number): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/bridge/fee', { params: { from_chain: fromChain, amount } }),
};
export const marketplaceAPI = {
    getGlobalStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/marketplace/global-stats'),
    search: (q: string, module: string | null = null, limit: number = 10): Promise<AxiosResponse<ApiResponse>> =>
        api.get('/api/marketplace/search', { params: { q, module, limit } }),

    // ── Listings ──
    createListing: (data: Record<string, unknown>, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/marketplace/listings', data, { params: { seller_id: sellerId } }),
    listListings: (params: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.get('/api/marketplace/listings', { params }),
    getListing: (id: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/marketplace/listings/${id}`),
    updateListing: (id: string, data: Record<string, unknown>, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.put(`/api/marketplace/listings/${id}`, data, { params: { seller_id: sellerId } }),
    pauseListing: (id: string, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/listings/${id}/pause`, {}, { params: { seller_id: sellerId } }),
    activateListing: (id: string, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/listings/${id}/activate`, {}, { params: { seller_id: sellerId } }),
    cancelListing: (id: string, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/listings/${id}/cancel`, {}, { params: { seller_id: sellerId } }),

    // ── Cart ──
    getCart: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/marketplace/cart/${userId}`),
    addToCart: (userId: string, listingId: string, quantity: number = 1): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/cart/${userId}/add`, { listing_id: listingId, quantity }),
    removeFromCart: (userId: string, listingId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/cart/${userId}/remove`, {}, { params: { listing_id: listingId } }),
    updateCartItem: (userId: string, listingId: string, quantity: number): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/cart/${userId}/update`, { listing_id: listingId, quantity }),
    clearCart: (userId: string): Promise<AxiosResponse<ApiResponse>> => api.post(`/api/marketplace/cart/${userId}/clear`),
    checkout: (userId: string, data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/cart/${userId}/checkout`, data),

    // ── Orders ──
    listOrders: (params: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.get('/api/marketplace/orders', { params }),
    getOrder: (id: string): Promise<AxiosResponse<ApiResponse>> => api.get(`/api/marketplace/orders/${id}`),
    payOrder: (id: string, paymentTxId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/pay`, { payment_tx_id: paymentTxId }),
    fulfillOrder: (id: string, sellerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/fulfill`, {}, { params: { seller_id: sellerId } }),
    completeOrder: (id: string, buyerId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/complete`, {}, { params: { buyer_id: buyerId } }),
    cancelOrder: (id: string, userId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/cancel`, {}, { params: { user_id: userId } }),
    disputeOrder: (id: string, userId: string, reason: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/dispute`, { reason }, { params: { user_id: userId } }),
    refundOrder: (id: string, resolverId: string): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${id}/refund`, {}, { params: { resolver_id: resolverId } }),

    // ── Reviews ──
    addReview: (orderId: string, reviewerId: string, rating: number, title: string = '', body: string = ''): Promise<AxiosResponse<ApiResponse>> =>
        api.post(`/api/marketplace/orders/${orderId}/review`, { rating, title, body }, { params: { reviewer_id: reviewerId } }),
    listReviews: (params: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> => api.get('/api/marketplace/reviews', { params }),

    // ── Stats ──
    getEngineStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/marketplace/stats'),
};
export const financeAPI = {
    // ── Ledger Engine (Double-Entry) ──
    getLedgerBalance: (account: string, currency: string = 'NCR'): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/finance/ledger/balance/${account}`, { params: { currency } }),
    getUserLedgerBalance: (userId: string, currency: string = 'NCR'): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/finance/ledger/user/${userId}`, { params: { currency } }),
    verifyLedger: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/finance/ledger/verify'),
    getLedgerTransactions: (userId: string, limit: number = 50): Promise<AxiosResponse<ApiResponse>> =>
        api.get(`/api/finance/ledger/transactions/${userId}`, { params: { limit } }),
    getLedgerStats: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/finance/ledger/stats'),

    // ── Nepal Banking Integration ──
    getNepalProviders: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/finance/nepal/providers'),
    initiateNepalPayment: (data: Record<string, unknown>): Promise<AxiosResponse<ApiResponse>> =>
        api.post('/api/finance/nepal/payment/initiate', data),
    getNepalTaxBreakdown: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/finance/nepal/tax-breakdown'),
    getNepalBankingStatus: (): Promise<AxiosResponse<ApiResponse>> => api.get('/api/finance/nepal/status'),
};
