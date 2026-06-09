/**
 * ASIMNEXUS Desktop Application - Preload Script
 * Exposes safe APIs to renderer process via contextBridge
 * All network calls are handled in main.js IPC handlers
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('asimnexusAPI', {
    // ─── App Info ─────────────────────────────────────────────────
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),

    // ─── Settings ─────────────────────────────────────────────────
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),

    // ─── Window Controls ──────────────────────────────────────────
    minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
    maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
    closeWindow: () => ipcRenderer.invoke('close-window'),

    // ─── External Links ───────────────────────────────────────────
    openExternal: (url) => ipcRenderer.invoke('open-external', url),

    // ─── System Info ──────────────────────────────────────────────
    platform: process.platform,
    arch: process.arch,

    // ─── Health / Ping ────────────────────────────────────────────
    health: () => ipcRenderer.invoke('asim:health'),

    // ─── Chat ─────────────────────────────────────────────────────
    chat: (message, useWorldOS) => ipcRenderer.invoke('asim:chat', message, useWorldOS),

    // ─── World OS ─────────────────────────────────────────────────
    getWorldOSStatus: () => ipcRenderer.invoke('asim:world_os_status'),
    getWorldOSAgents: () => ipcRenderer.invoke('asim:world_os_agents'),

    // ─── Analytics & Security ─────────────────────────────────────
    getAnalytics: () => ipcRenderer.invoke('asim:analytics'),
    getSecurity: () => ipcRenderer.invoke('asim:security'),
    getAgents: () => ipcRenderer.invoke('asim:agents'),
    getFounders: () => ipcRenderer.invoke('asim:founders'),

    // ═══════════════════════════════════════════════════════════════
    // ECONOMY API
    // ═══════════════════════════════════════════════════════════════

    // ─── Wallet ───────────────────────────────────────────────────
    createWallet: (ownerId, ownerType) => ipcRenderer.invoke('economy:wallet:create', ownerId, ownerType),
    getWallet: (walletId) => ipcRenderer.invoke('economy:wallet:get', walletId),
    getWalletByOwner: (ownerId) => ipcRenderer.invoke('economy:wallet:byOwner', ownerId),
    getBalance: (walletId, tokenType) => ipcRenderer.invoke('economy:wallet:balance', walletId, tokenType),
    deposit: (walletId, amount, tokenType) => ipcRenderer.invoke('economy:wallet:deposit', walletId, amount, tokenType),
    withdraw: (walletId, amount, tokenType) => ipcRenderer.invoke('economy:wallet:withdraw', walletId, amount, tokenType),
    transfer: (fromWalletId, toWalletId, amount, tokenType) => ipcRenderer.invoke('economy:wallet:transfer', fromWalletId, toWalletId, amount, tokenType),
    freezeWallet: (walletId, reason) => ipcRenderer.invoke('economy:wallet:freeze', walletId, reason),
    closeWallet: (walletId) => ipcRenderer.invoke('economy:wallet:close', walletId),
    listTransactions: (walletId, limit) => ipcRenderer.invoke('economy:wallet:transactions', walletId, limit),
    getTotalSupply: (tokenType) => ipcRenderer.invoke('economy:wallet:supply', tokenType),
    getWalletStats: () => ipcRenderer.invoke('economy:wallet:stats'),

    // ─── Tokens ───────────────────────────────────────────────────
    registerToken: (name, symbol, standard, ownerId, totalSupply, decimals) =>
        ipcRenderer.invoke('economy:tokens:register', name, symbol, standard, ownerId, totalSupply, decimals),
    getToken: (tokenId) => ipcRenderer.invoke('economy:tokens:get', tokenId),
    getTokenBySymbol: (symbol) => ipcRenderer.invoke('economy:tokens:bySymbol', symbol),
    listTokens: (standard) => ipcRenderer.invoke('economy:tokens:list', standard),
    mint: (tokenId, ownerId, amount) => ipcRenderer.invoke('economy:tokens:mint', tokenId, ownerId, amount),
    burn: (tokenId, ownerId, amount) => ipcRenderer.invoke('economy:tokens:burn', tokenId, ownerId, amount),
    lockTokens: (tokenId, ownerId, amount) => ipcRenderer.invoke('economy:tokens:lock', tokenId, ownerId, amount),
    unlockTokens: (tokenId, ownerId, amount) => ipcRenderer.invoke('economy:tokens:unlock', tokenId, ownerId, amount),
    getOwnerHoldings: (ownerId) => ipcRenderer.invoke('economy:tokens:holdings', ownerId),
    getHolding: (ownerId, tokenId) => ipcRenderer.invoke('economy:tokens:holding', ownerId, tokenId),
    getTokenStats: () => ipcRenderer.invoke('economy:tokens:stats'),

    // ─── Escrow ───────────────────────────────────────────────────
    createEscrow: (buyerId, sellerId, amount, tokenType) =>
        ipcRenderer.invoke('economy:escrow:create', buyerId, sellerId, amount, tokenType),
    getEscrow: (escrowId) => ipcRenderer.invoke('economy:escrow:get', escrowId),
    fundEscrow: (escrowId) => ipcRenderer.invoke('economy:escrow:fund', escrowId),
    releaseToSeller: (escrowId) => ipcRenderer.invoke('economy:escrow:release', escrowId),
    refundToBuyer: (escrowId) => ipcRenderer.invoke('economy:escrow:refund', escrowId),
    raiseDispute: (escrowId, raisedBy, reason) => ipcRenderer.invoke('economy:escrow:dispute', escrowId, raisedBy, reason),
    resolveDispute: (escrowId, resolution, resolvedBy) =>
        ipcRenderer.invoke('economy:escrow:resolveDispute', escrowId, resolution, resolvedBy),
    getEscrowsForUser: (userId) => ipcRenderer.invoke('economy:escrow:userEscrows', userId),
    getEscrowDisputes: (escrowId) => ipcRenderer.invoke('economy:escrow:disputes', escrowId),
    getEscrowStats: () => ipcRenderer.invoke('economy:escrow:stats'),

    // ─── Marketplace ──────────────────────────────────────────────
    createListing: (sellerId, title, description, price, category, tokenType) =>
        ipcRenderer.invoke('economy:marketplace:createListing', sellerId, title, description, price, category, tokenType),
    getListing: (listingId) => ipcRenderer.invoke('economy:marketplace:getListing', listingId),
    searchListings: (query, category, minPrice, maxPrice, status) =>
        ipcRenderer.invoke('economy:marketplace:search', query, category, minPrice, maxPrice, status),
    cancelListing: (listingId, sellerId) => ipcRenderer.invoke('economy:marketplace:cancelListing', listingId, sellerId),
    createOrder: (listingId, buyerId, quantity) => ipcRenderer.invoke('economy:marketplace:createOrder', listingId, buyerId, quantity),
    getOrdersForUser: (userId, role) => ipcRenderer.invoke('economy:marketplace:userOrders', userId, role),
    submitReview: (orderId, reviewerId, rating, comment) =>
        ipcRenderer.invoke('economy:marketplace:submitReview', orderId, reviewerId, rating, comment),
    getUserReputation: (userId) => ipcRenderer.invoke('economy:marketplace:reputation', userId),
    getMarketplaceStats: () => ipcRenderer.invoke('economy:marketplace:stats'),

    // ─── Staking ──────────────────────────────────────────────────
    stake: (stakerId, validatorId, amount, tokenType) =>
        ipcRenderer.invoke('economy:staking:stake', stakerId, validatorId, amount, tokenType),
    unstake: (stakeId, stakerId) => ipcRenderer.invoke('economy:staking:unstake', stakeId, stakerId),
    claimUnstaked: (stakeId, stakerId) => ipcRenderer.invoke('economy:staking:claim', stakeId, stakerId),
    getStake: (stakeId) => ipcRenderer.invoke('economy:staking:getStake', stakeId),
    getStakesForUser: (stakerId) => ipcRenderer.invoke('economy:staking:userStakes', stakerId),
    getTotalStaked: (tokenType) => ipcRenderer.invoke('economy:staking:totalStaked', tokenType),
    registerValidator: (name, owner, commission, description) =>
        ipcRenderer.invoke('economy:staking:registerValidator', name, owner, commission, description),
    getValidator: (validatorId) => ipcRenderer.invoke('economy:staking:getValidator', validatorId),
    listValidators: (status) => ipcRenderer.invoke('economy:staking:listValidators', status),
    jailValidator: (validatorId, reason) => ipcRenderer.invoke('economy:staking:jailValidator', validatorId, reason),
    unjailValidator: (validatorId) => ipcRenderer.invoke('economy:staking:unjailValidator', validatorId),
    slashValidator: (validatorId, amount, reason) => ipcRenderer.invoke('economy:staking:slashValidator', validatorId, amount, reason),
    distributeRewards: () => ipcRenderer.invoke('economy:staking:distributeRewards'),
    getRewardsHistory: (stakerId, limit) => ipcRenderer.invoke('economy:staking:rewardsHistory', stakerId, limit),
    unlockMaturedStakes: () => ipcRenderer.invoke('economy:staking:unlockMatured'),
    getStakingStats: () => ipcRenderer.invoke('economy:staking:stats'),

    // ═══════════════════════════════════════════════════════════════
    // GOVERNANCE API
    // ═══════════════════════════════════════════════════════════════

    // ─── Health ──────────────────────────────────────────────────
    governanceHealth: () => ipcRenderer.invoke('gov:health'),

    // ─── Proposals ───────────────────────────────────────────────
    createProposal: (title, description, proposer, vetoPower, urgency, sector) =>
        ipcRenderer.invoke('gov:proposals:create', title, description, proposer, vetoPower, urgency, sector),
    listProposals: (state, proposer, limit) =>
        ipcRenderer.invoke('gov:proposals:list', state, proposer, limit),
    getProposal: (proposalId) =>
        ipcRenderer.invoke('gov:proposals:get', proposalId),
    activateProposal: (proposalId) =>
        ipcRenderer.invoke('gov:proposals:activate', proposalId),
    finalizeProposal: (proposalId) =>
        ipcRenderer.invoke('gov:proposals:finalize', proposalId),

    // ─── Voting ─────────────────────────────────────────────────
    castVote: (proposalId, voterAddress, decision, weight, rationale) =>
        ipcRenderer.invoke('gov:vote:cast', proposalId, voterAddress, decision, weight, rationale),
    getTally: (proposalId) =>
        ipcRenderer.invoke('gov:vote:tally', proposalId),

    // ─── Veto ───────────────────────────────────────────────────
    exerciseVeto: (exercisedBy, reason, actionVetoed, proposalId) =>
        ipcRenderer.invoke('gov:veto:exercise', exercisedBy, reason, actionVetoed, proposalId),
    getVetoStatus: () => ipcRenderer.invoke('gov:veto:status'),

    // ─── Constitution ───────────────────────────────────────────
    sealConstitution: (constitutionHash, sealedBy, jurisdiction, metadata) =>
        ipcRenderer.invoke('gov:constitution:seal', constitutionHash, sealedBy, jurisdiction, metadata),
    verifyConstitution: (constitutionHash) =>
        ipcRenderer.invoke('gov:constitution:verify', constitutionHash),
    getLatestConstitution: () => ipcRenderer.invoke('gov:constitution:latest'),
    getConstitutionStats: () => ipcRenderer.invoke('gov:constitution:stats'),

    // ─── Audit ──────────────────────────────────────────────────
    queryAudit: (query) => ipcRenderer.invoke('gov:audit:query', query),
    verifyAuditChain: () => ipcRenderer.invoke('gov:audit:verify'),
    getAuditStats: () => ipcRenderer.invoke('gov:audit:stats'),

    // ─── Council ────────────────────────────────────────────────
    getCouncilStatus: () => ipcRenderer.invoke('gov:council:status'),
    addCouncilMember: (name, memberType, country, expertise) =>
        ipcRenderer.invoke('gov:council:addMember', name, memberType, country, expertise),

    // ─── Bridge ─────────────────────────────────────────────────
    bridgeDecision: (title, description, source, sector, urgency, context, autoVote, escalate) =>
        ipcRenderer.invoke('gov:bridge:decide', title, description, source, sector, urgency, context, autoVote, escalate),
    getBridgeHistory: (limit) =>
        ipcRenderer.invoke('gov:bridge:history', limit),

    // ─── Founders ───────────────────────────────────────────────
    listFounders: () => ipcRenderer.invoke('gov:founders:list'),

    // ─── Stats ──────────────────────────────────────────────────
    getGovernanceStats: () => ipcRenderer.invoke('gov:stats'),
});

/**
 * Expose node versions
 */
contextBridge.exposeInMainWorld('nodeVersions', {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
});
