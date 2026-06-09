/**
 * ASIMNEXUS Economy API Service for React Native
 * Covers all /api/economy/* endpoints: Wallet, Tokens, Escrow, Marketplace, Staking
 */

import axios from 'axios';
import { API_BASE_URL } from '../config';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
});

// ─── Wallet API ───────────────────────────────────────────────────────────────

const walletAPI = {
    async createWallet(ownerId, ownerType = 'user') {
        const res = await api.post('/api/economy/wallet/create', { owner_id: ownerId, owner_type: ownerType });
        return res.data;
    },

    async getWallet(walletId) {
        const res = await api.get(`/api/economy/wallet/${walletId}`);
        return res.data;
    },

    async getWalletByOwner(ownerId) {
        const res = await api.get(`/api/economy/wallet/by-owner/${ownerId}`);
        return res.data;
    },

    async getBalance(walletId, tokenType = 'nexus') {
        const res = await api.get(`/api/economy/wallet/${walletId}/balance`, { params: { token_type: tokenType } });
        return res.data;
    },

    async deposit(walletId, amount, tokenType = 'nexus') {
        const res = await api.post('/api/economy/wallet/deposit', { wallet_id: walletId, amount, token_type: tokenType });
        return res.data;
    },

    async withdraw(walletId, amount, tokenType = 'nexus') {
        const res = await api.post('/api/economy/wallet/withdraw', { wallet_id: walletId, amount, token_type: tokenType });
        return res.data;
    },

    async transfer(fromWalletId, toWalletId, amount, tokenType = 'nexus') {
        const res = await api.post('/api/economy/wallet/transfer', {
            from_wallet_id: fromWalletId, to_wallet_id: toWalletId, amount, token_type: tokenType,
        });
        return res.data;
    },

    async freezeWallet(walletId, reason = '') {
        const res = await api.post('/api/economy/wallet/freeze', { wallet_id: walletId, reason });
        return res.data;
    },

    async closeWallet(walletId) {
        const res = await api.post(`/api/economy/wallet/${walletId}/close`);
        return res.data;
    },

    async listTransactions(walletId, limit = 50) {
        const res = await api.get(`/api/economy/wallet/${walletId}/transactions`, { params: { limit } });
        return res.data;
    },

    async getTransaction(walletId, txId) {
        const res = await api.get(`/api/economy/wallet/${walletId}/transactions/${txId}`);
        return res.data;
    },

    async getTotalSupply(tokenType = 'nexus') {
        const res = await api.get(`/api/economy/wallet/supply/${tokenType}`);
        return res.data;
    },

    async getWalletStats() {
        const res = await api.get('/api/economy/wallet/stats');
        return res.data;
    },
};

// ─── Tokens API ───────────────────────────────────────────────────────────────

const tokenAPI = {
    async registerToken(name, symbol, standard = 'NRC-20', ownerId = '', totalSupply = 0, decimals = 18) {
        const res = await api.post('/api/economy/tokens/register', {
            name, symbol, standard, owner_id: ownerId, total_supply: totalSupply, decimals,
        });
        return res.data;
    },

    async getToken(tokenId) {
        const res = await api.get(`/api/economy/tokens/${tokenId}`);
        return res.data;
    },

    async getTokenBySymbol(symbol) {
        const res = await api.get(`/api/economy/tokens/by-symbol/${symbol}`);
        return res.data;
    },

    async listTokens(standard = null) {
        const params = standard ? { standard } : {};
        const res = await api.get('/api/economy/tokens', { params });
        return res.data;
    },

    async mint(tokenId, toOwnerId, amount) {
        const res = await api.post(`/api/economy/tokens/${tokenId}/mint`, { to_owner_id: toOwnerId, amount });
        return res.data;
    },

    async burn(tokenId, fromOwnerId, amount) {
        const res = await api.post(`/api/economy/tokens/${tokenId}/burn`, { from_owner_id: fromOwnerId, amount });
        return res.data;
    },

    async lockTokens(tokenId, ownerId, amount) {
        const res = await api.post(`/api/economy/tokens/${tokenId}/lock`, { owner_id: ownerId, amount });
        return res.data;
    },

    async unlockTokens(tokenId, ownerId, amount) {
        const res = await api.post(`/api/economy/tokens/${tokenId}/unlock`, { owner_id: ownerId, amount });
        return res.data;
    },

    async getOwnerHoldings(ownerId) {
        const res = await api.get(`/api/economy/tokens/holdings/${ownerId}`);
        return res.data;
    },

    async getHolding(ownerId, tokenId) {
        const res = await api.get(`/api/economy/tokens/holdings/${ownerId}/${tokenId}`);
        return res.data;
    },

    async getOwnerBalance(ownerId, tokenId) {
        const res = await api.get(`/api/economy/tokens/balance/${ownerId}/${tokenId}`);
        return res.data;
    },

    async getTokenStats() {
        const res = await api.get('/api/economy/tokens/stats');
        return res.data;
    },
};

// ─── Escrow API ───────────────────────────────────────────────────────────────

const escrowAPI = {
    async createEscrow(buyerId, sellerId, amount, tokenType = 'nexus', expiresIn = 86400) {
        const res = await api.post('/api/economy/escrow/create', {
            buyer_id: buyerId, seller_id: sellerId, amount, token_type: tokenType, expires_in: expiresIn,
        });
        return res.data;
    },

    async getEscrow(escrowId) {
        const res = await api.get(`/api/economy/escrow/${escrowId}`);
        return res.data;
    },

    async fundEscrow(escrowId, fundedBy) {
        const res = await api.post('/api/economy/escrow/fund', { escrow_id: escrowId, funded_by: fundedBy });
        return res.data;
    },

    async releaseToSeller(escrowId, releasedBy) {
        const res = await api.post('/api/economy/escrow/release', { escrow_id: escrowId, released_by: releasedBy });
        return res.data;
    },

    async refundToBuyer(escrowId, refundedBy) {
        const res = await api.post('/api/economy/escrow/refund', { escrow_id: escrowId, refunded_by: refundedBy });
        return res.data;
    },

    async raiseDispute(escrowId, raisedBy, reason = '') {
        const res = await api.post('/api/economy/escrow/dispute', { escrow_id: escrowId, raised_by: raisedBy, reason });
        return res.data;
    },

    async resolveDispute(escrowId, resolvedBy, resolution = 'release') {
        const res = await api.post('/api/economy/escrow/dispute/resolve', {
            escrow_id: escrowId, resolved_by: resolvedBy, resolution,
        });
        return res.data;
    },

    async getEscrowsForUser(userId) {
        const res = await api.get(`/api/economy/escrow/user/${userId}`);
        return res.data;
    },

    async getEscrowDisputes(escrowId) {
        const res = await api.get(`/api/economy/escrow/${escrowId}/disputes`);
        return res.data;
    },

    async getEscrowStats() {
        const res = await api.get('/api/economy/escrow/stats');
        return res.data;
    },
};

// ─── Marketplace API ──────────────────────────────────────────────────────────

const marketplaceAPI = {
    async createListing(sellerId, title, description, price, category = 'general', tokenType = 'nexus', quantity = 1) {
        const res = await api.post('/api/economy/marketplace/listings', {
            seller_id: sellerId, title, description, price, category, token_type: tokenType, quantity,
        });
        return res.data;
    },

    async getListing(listingId) {
        const res = await api.get(`/api/economy/marketplace/listings/${listingId}`);
        return res.data;
    },

    async searchListings(query = '', category = null, minPrice = null, maxPrice = null, status = 'active') {
        const res = await api.post('/api/economy/marketplace/listings/search', {
            query, category, min_price: minPrice, max_price: maxPrice, status,
        });
        return res.data;
    },

    async cancelListing(listingId, sellerId) {
        const res = await api.post(`/api/economy/marketplace/listings/${listingId}/cancel`, null, {
            params: { seller_id: sellerId },
        });
        return res.data;
    },

    async createOrder(listingId, buyerId, quantity = 1) {
        const res = await api.post('/api/economy/marketplace/orders', {
            listing_id: listingId, buyer_id: buyerId, quantity,
        });
        return res.data;
    },

    async updateOrderStatus(orderId, status, actorId) {
        const res = await api.post('/api/economy/marketplace/orders/status', {
            order_id: orderId, status, actor_id: actorId,
        });
        return res.data;
    },

    async getOrdersForUser(userId, role = null) {
        const params = role ? { role } : {};
        const res = await api.get(`/api/economy/marketplace/orders/user/${userId}`, { params });
        return res.data;
    },

    async submitReview(orderId, reviewerId, rating, comment = '') {
        const res = await api.post('/api/economy/marketplace/reviews', {
            order_id: orderId, reviewer_id: reviewerId, rating, comment,
        });
        return res.data;
    },

    async getUserReputation(userId) {
        const res = await api.get(`/api/economy/marketplace/reputation/${userId}`);
        return res.data;
    },

    async getMarketplaceStats() {
        const res = await api.get('/api/economy/marketplace/stats');
        return res.data;
    },
};

// ─── Staking API ──────────────────────────────────────────────────────────────

const stakingAPI = {
    async stake(stakerId, amount, validatorId, tokenType = 'nexus', lockDays = 30) {
        const res = await api.post('/api/economy/staking/stake', {
            staker_id: stakerId, amount, validator_id: validatorId, token_type: tokenType, lock_days: lockDays,
        });
        return res.data;
    },

    async unstake(stakeId, stakerId) {
        const res = await api.post('/api/economy/staking/unstake', { stake_id: stakeId, staker_id: stakerId });
        return res.data;
    },

    async claimUnstaked(stakeId, stakerId) {
        const res = await api.post('/api/economy/staking/claim', { stake_id: stakeId, staker_id: stakerId });
        return res.data;
    },

    async getStake(stakeId) {
        const res = await api.get(`/api/economy/staking/positions/${stakeId}`);
        return res.data;
    },

    async getStakesForUser(stakerId) {
        const res = await api.get('/api/economy/staking/positions', { params: { staker_id: stakerId } });
        return res.data;
    },

    async getTotalStaked(tokenType = 'nexus') {
        const res = await api.get('/api/economy/staking/total-staked', { params: { token_type: tokenType } });
        return res.data;
    },

    async registerValidator(name, ownerId, description = '', commission = 0.1) {
        const res = await api.post('/api/economy/staking/validators', {
            name, owner_id: ownerId, description, commission,
        });
        return res.data;
    },

    async getValidator(validatorId) {
        const res = await api.get(`/api/economy/staking/validators/${validatorId}`);
        return res.data;
    },

    async listValidators(status = null) {
        const params = status ? { status } : {};
        const res = await api.get('/api/economy/staking/validators', { params });
        return res.data;
    },

    async jailValidator(validatorId, reason = '') {
        const res = await api.post('/api/economy/staking/validators/jail', { validator_id: validatorId, reason });
        return res.data;
    },

    async unjailValidator(validatorId) {
        const res = await api.post('/api/economy/staking/validators/unjail', { validator_id: validatorId });
        return res.data;
    },

    async slashValidator(validatorId, amount, reason = '') {
        const res = await api.post('/api/economy/staking/slash', { validator_id: validatorId, amount, reason });
        return res.data;
    },

    async distributeRewards() {
        const res = await api.post('/api/economy/staking/distribute-rewards');
        return res.data;
    },

    async getRewardsHistory(stakerId, limit = 50) {
        const res = await api.get(`/api/economy/staking/rewards/${stakerId}`, { params: { limit } });
        return res.data;
    },

    async unlockMaturedStakes() {
        const res = await api.post('/api/economy/staking/unlock-matured');
        return res.data;
    },

    async getStakingStats() {
        const res = await api.get('/api/economy/staking/stats');
        return res.data;
    },
};

export { walletAPI, tokenAPI, escrowAPI, marketplaceAPI, stakingAPI };
export default { walletAPI, tokenAPI, escrowAPI, marketplaceAPI, stakingAPI };
