/**
 * ASIMNEXUS Desktop Application - Main Process
 * Electron main process for desktop app
 */

const { app, BrowserWindow, ipcMain, Menu, shell } = require('electron');
const path = require('path');
const axios = require('axios');
const Store = require('electron-store');

const store = new Store();
let mainWindow;

// ASIMNEXUS Backend API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Economy API Client for Main Process
const economyAPI = {
    // ─── Wallet ──────────────────────────────────────────────────────
    async createWallet(ownerId, ownerType = 'user') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/create`, { owner_id: ownerId, owner_type: ownerType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getWallet(walletId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/${walletId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getWalletByOwner(ownerId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/by-owner/${ownerId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getBalance(walletId, tokenType = 'nexus') {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/${walletId}/balance`, { params: { token_type: tokenType } }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async deposit(walletId, amount, tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/deposit`, { wallet_id: walletId, amount, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async withdraw(walletId, amount, tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/withdraw`, { wallet_id: walletId, amount, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async transfer(fromWalletId, toWalletId, amount, tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/transfer`, { from_wallet_id: fromWalletId, to_wallet_id: toWalletId, amount, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async freezeWallet(walletId, reason = '') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/freeze`, { wallet_id: walletId, reason }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async closeWallet(walletId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/wallet/${walletId}/close`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async listTransactions(walletId, limit = 50) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/${walletId}/transactions`, { params: { limit } }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getTotalSupply(tokenType = 'nexus') {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/supply/${tokenType}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getWalletStats() {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/wallet/stats`); return r.data; }
        catch (e) { return { error: e.message }; }
    },

    // ─── Tokens ──────────────────────────────────────────────────────
    async registerToken(name, symbol, standard = 'NRC-20', ownerId = '', totalSupply = 0, decimals = 18) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/tokens/register`, { name, symbol, standard, owner_id: ownerId, total_supply: totalSupply, decimals }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getToken(tokenId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/tokens/${tokenId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getTokenBySymbol(symbol) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/tokens/by-symbol/${symbol}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async listTokens(standard = null) {
        try { const params = standard ? { standard } : {}; const r = await axios.get(`${API_BASE_URL}/api/economy/tokens`, { params }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async mint(tokenId, ownerId, amount) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/tokens/${tokenId}/mint`, { owner_id: ownerId, amount }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async burn(tokenId, ownerId, amount) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/tokens/${tokenId}/burn`, { owner_id: ownerId, amount }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async lockTokens(tokenId, ownerId, amount) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/tokens/${tokenId}/lock`, { owner_id: ownerId, amount }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async unlockTokens(tokenId, ownerId, amount) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/tokens/${tokenId}/unlock`, { owner_id: ownerId, amount }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getOwnerHoldings(ownerId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/tokens/holdings/${ownerId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getHolding(ownerId, tokenId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/tokens/holdings/${ownerId}/${tokenId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getTokenStats() {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/tokens/stats`); return r.data; }
        catch (e) { return { error: e.message }; }
    },

    // ─── Escrow ──────────────────────────────────────────────────────
    async createEscrow(buyerId, sellerId, amount, tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/create`, { buyer_id: buyerId, seller_id: sellerId, amount, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getEscrow(escrowId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/escrow/${escrowId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async fundEscrow(escrowId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/fund`, { escrow_id: escrowId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async releaseToSeller(escrowId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/release`, { escrow_id: escrowId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async refundToBuyer(escrowId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/refund`, { escrow_id: escrowId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async raiseDispute(escrowId, raisedBy, reason = 'other') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/dispute`, { escrow_id: escrowId, raised_by: raisedBy, reason }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async resolveDispute(escrowId, resolution, resolvedBy) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/escrow/dispute/resolve`, { escrow_id: escrowId, resolution, resolved_by: resolvedBy }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getEscrowsForUser(userId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/escrow/user/${userId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getEscrowDisputes(escrowId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/escrow/${escrowId}/disputes`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getEscrowStats() {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/escrow/stats`); return r.data; }
        catch (e) { return { error: e.message }; }
    },

    // ─── Marketplace ─────────────────────────────────────────────────
    async createListing(sellerId, title, description, price, category = 'other', tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/marketplace/listings`, { seller_id: sellerId, title, description, price, category, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getListing(listingId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/marketplace/listings/${listingId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async searchListings(query, category = null, minPrice = null, maxPrice = null, status = 'active') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/marketplace/listings/search`, { query, category, min_price: minPrice, max_price: maxPrice, status }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async cancelListing(listingId, sellerId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/marketplace/listings/${listingId}/cancel?seller_id=${sellerId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async createOrder(listingId, buyerId, quantity = 1) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/marketplace/orders`, { listing_id: listingId, buyer_id: buyerId, quantity }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getOrdersForUser(userId, role = null) {
        try { const params = role ? { role } : {}; const r = await axios.get(`${API_BASE_URL}/api/economy/marketplace/orders/user/${userId}`, { params }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async submitReview(orderId, reviewerId, rating, comment) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/marketplace/reviews`, { order_id: orderId, reviewer_id: reviewerId, rating, comment }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getUserReputation(userId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/marketplace/reputation/${userId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getMarketplaceStats() {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/marketplace/stats`); return r.data; }
        catch (e) { return { error: e.message }; }
    },

    // ─── Staking ─────────────────────────────────────────────────────
    async stake(stakerId, validatorId, amount, tokenType = 'nexus') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/stake`, { staker_id: stakerId, validator_id: validatorId, amount, token_type: tokenType }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async unstake(stakeId, stakerId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/unstake`, { stake_id: stakeId, staker_id: stakerId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async claimUnstaked(stakeId, stakerId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/claim`, { stake_id: stakeId, staker_id: stakerId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getStake(stakeId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/positions/${stakeId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getStakesForUser(stakerId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/positions`, { params: { staker_id: stakerId } }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getTotalStaked(tokenType = 'nexus') {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/total-staked`, { params: { token_type: tokenType } }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async registerValidator(name, owner, commission = 10, description = '') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/validators`, { name, owner, commission, description }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getValidator(validatorId) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/validators/${validatorId}`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async listValidators(status = null) {
        try { const params = status ? { status } : {}; const r = await axios.get(`${API_BASE_URL}/api/economy/staking/validators`, { params }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async jailValidator(validatorId, reason = '') {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/validators/jail`, { validator_id: validatorId, reason }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async unjailValidator(validatorId) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/validators/unjail`, { validator_id: validatorId }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async slashValidator(validatorId, amount, reason) {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/slash`, { validator_id: validatorId, amount, reason }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async distributeRewards() {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/distribute-rewards`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getRewardsHistory(stakerId, limit = 50) {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/rewards/${stakerId}`, { params: { limit } }); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async unlockMaturedStakes() {
        try { const r = await axios.post(`${API_BASE_URL}/api/economy/staking/unlock-matured`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
    async getStakingStats() {
        try { const r = await axios.get(`${API_BASE_URL}/api/economy/staking/stats`); return r.data; }
        catch (e) { return { error: e.message }; }
    },
};

/**
 * Create main application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            enableRemoteModule: false,
            nodeIntegration: false
        },
        icon: path.join(__dirname, 'assets', 'icon.png'),
        titleBarStyle: 'default',
        backgroundColor: '#1a1a2e'
    });

    // Load the app
    mainWindow.loadFile(path.join(__dirname, 'electron', 'index.html'));

    // Open DevTools in development
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/**
 * Create application menu
 */
function createMenu() {
    const template = [
        {
            label: 'ASIMNEXUS',
            submenu: [
                {
                    label: 'About ASIMNEXUS',
                    click: () => {
                        shell.openExternal('https://asimnexus.ai');
                    }
                },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Window',
            submenu: [
                { role: 'minimize' },
                { role: 'close' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: () => {
                        shell.openExternal('https://docs.asimnexus.ai');
                    }
                },
                {
                    label: 'Report Issue',
                    click: () => {
                        shell.openExternal('https://github.com/asimnexus/asimnexus/issues');
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

/**
 * IPC handlers
 */
function setupIpcHandlers() {
    // ─── App & System ──────────────────────────────────────────────
    ipcMain.handle('get-app-version', () => app.getVersion());

    // Settings (persisted via electron-store)
    ipcMain.handle('get-settings', () => store.get('settings', {}));
    ipcMain.handle('save-settings', (_e, settings) => { store.set('settings', settings); return true; });

    // Window controls
    ipcMain.handle('minimize-window', () => { if (mainWindow) mainWindow.minimize(); return true; });
    ipcMain.handle('maximize-window', () => {
        if (!mainWindow) return true;
        mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
        return true;
    });
    ipcMain.handle('close-window', () => { if (mainWindow) mainWindow.close(); return true; });

    // External links
    ipcMain.handle('open-external', (_e, url) => { shell.openExternal(url); return true; });

    // ─── Health / Ping ─────────────────────────────────────────────
    ipcMain.handle('asim:health', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/health`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── Chat ──────────────────────────────────────────────────────
    ipcMain.handle('asim:chat', async (_e, message, useWorldOS = true) => {
        try { const r = await axios.post(`${API_BASE_URL}/api/chat`, { message, use_world_os: useWorldOS }); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── World OS ──────────────────────────────────────────────────
    ipcMain.handle('asim:world_os_status', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/world_os/status`); return r.data; }
        catch (e) { return { error: e.message }; }
    });
    ipcMain.handle('asim:world_os_agents', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/world_os/agents`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── Analytics ─────────────────────────────────────────────────
    ipcMain.handle('asim:analytics', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/analytics/overview`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── Security ──────────────────────────────────────────────────
    ipcMain.handle('asim:security', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/security/status`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── Agents ────────────────────────────────────────────────────
    ipcMain.handle('asim:agents', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/agents`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ─── Founders ──────────────────────────────────────────────────
    ipcMain.handle('asim:founders', async () => {
        try { const r = await axios.get(`${API_BASE_URL}/api/founders`); return r.data; }
        catch (e) { return { error: e.message }; }
    });

    // ════════════════════════════════════════════════════════════════
    // ECONOMY IPC HANDLERS
    // ════════════════════════════════════════════════════════════════

    // ─── Wallet ────────────────────────────────────────────────────
    ipcMain.handle('economy:wallet:create', async (_e, ownerId, ownerType) => economyAPI.createWallet(ownerId, ownerType));
    ipcMain.handle('economy:wallet:get', async (_e, walletId) => economyAPI.getWallet(walletId));
    ipcMain.handle('economy:wallet:byOwner', async (_e, ownerId) => economyAPI.getWalletByOwner(ownerId));
    ipcMain.handle('economy:wallet:balance', async (_e, walletId, tokenType) => economyAPI.getBalance(walletId, tokenType));
    ipcMain.handle('economy:wallet:deposit', async (_e, walletId, amount, tokenType) => economyAPI.deposit(walletId, amount, tokenType));
    ipcMain.handle('economy:wallet:withdraw', async (_e, walletId, amount, tokenType) => economyAPI.withdraw(walletId, amount, tokenType));
    ipcMain.handle('economy:wallet:transfer', async (_e, fromWalletId, toWalletId, amount, tokenType) => economyAPI.transfer(fromWalletId, toWalletId, amount, tokenType));
    ipcMain.handle('economy:wallet:freeze', async (_e, walletId, reason) => economyAPI.freezeWallet(walletId, reason));
    ipcMain.handle('economy:wallet:close', async (_e, walletId) => economyAPI.closeWallet(walletId));
    ipcMain.handle('economy:wallet:transactions', async (_e, walletId, limit) => economyAPI.listTransactions(walletId, limit));
    ipcMain.handle('economy:wallet:supply', async (_e, tokenType) => economyAPI.getTotalSupply(tokenType));
    ipcMain.handle('economy:wallet:stats', async () => economyAPI.getWalletStats());

    // ─── Tokens ────────────────────────────────────────────────────
    ipcMain.handle('economy:tokens:register', async (_e, name, symbol, standard, ownerId, totalSupply, decimals) => economyAPI.registerToken(name, symbol, standard, ownerId, totalSupply, decimals));
    ipcMain.handle('economy:tokens:get', async (_e, tokenId) => economyAPI.getToken(tokenId));
    ipcMain.handle('economy:tokens:bySymbol', async (_e, symbol) => economyAPI.getTokenBySymbol(symbol));
    ipcMain.handle('economy:tokens:list', async (_e, standard) => economyAPI.listTokens(standard));
    ipcMain.handle('economy:tokens:mint', async (_e, tokenId, ownerId, amount) => economyAPI.mint(tokenId, ownerId, amount));
    ipcMain.handle('economy:tokens:burn', async (_e, tokenId, ownerId, amount) => economyAPI.burn(tokenId, ownerId, amount));
    ipcMain.handle('economy:tokens:lock', async (_e, tokenId, ownerId, amount) => economyAPI.lockTokens(tokenId, ownerId, amount));
    ipcMain.handle('economy:tokens:unlock', async (_e, tokenId, ownerId, amount) => economyAPI.unlockTokens(tokenId, ownerId, amount));
    ipcMain.handle('economy:tokens:holdings', async (_e, ownerId) => economyAPI.getOwnerHoldings(ownerId));
    ipcMain.handle('economy:tokens:holding', async (_e, ownerId, tokenId) => economyAPI.getHolding(ownerId, tokenId));
    ipcMain.handle('economy:tokens:stats', async () => economyAPI.getTokenStats());

    // ─── Escrow ────────────────────────────────────────────────────
    ipcMain.handle('economy:escrow:create', async (_e, buyerId, sellerId, amount, tokenType) => economyAPI.createEscrow(buyerId, sellerId, amount, tokenType));
    ipcMain.handle('economy:escrow:get', async (_e, escrowId) => economyAPI.getEscrow(escrowId));
    ipcMain.handle('economy:escrow:fund', async (_e, escrowId) => economyAPI.fundEscrow(escrowId));
    ipcMain.handle('economy:escrow:release', async (_e, escrowId) => economyAPI.releaseToSeller(escrowId));
    ipcMain.handle('economy:escrow:refund', async (_e, escrowId) => economyAPI.refundToBuyer(escrowId));
    ipcMain.handle('economy:escrow:dispute', async (_e, escrowId, raisedBy, reason) => economyAPI.raiseDispute(escrowId, raisedBy, reason));
    ipcMain.handle('economy:escrow:resolveDispute', async (_e, escrowId, resolution, resolvedBy) => economyAPI.resolveDispute(escrowId, resolution, resolvedBy));
    ipcMain.handle('economy:escrow:userEscrows', async (_e, userId) => economyAPI.getEscrowsForUser(userId));
    ipcMain.handle('economy:escrow:disputes', async (_e, escrowId) => economyAPI.getEscrowDisputes(escrowId));
    ipcMain.handle('economy:escrow:stats', async () => economyAPI.getEscrowStats());

    // ─── Marketplace ───────────────────────────────────────────────
    ipcMain.handle('economy:marketplace:createListing', async (_e, sellerId, title, description, price, category, tokenType) => economyAPI.createListing(sellerId, title, description, price, category, tokenType));
    ipcMain.handle('economy:marketplace:getListing', async (_e, listingId) => economyAPI.getListing(listingId));
    ipcMain.handle('economy:marketplace:search', async (_e, query, category, minPrice, maxPrice, status) => economyAPI.searchListings(query, category, minPrice, maxPrice, status));
    ipcMain.handle('economy:marketplace:cancelListing', async (_e, listingId, sellerId) => economyAPI.cancelListing(listingId, sellerId));
    ipcMain.handle('economy:marketplace:createOrder', async (_e, listingId, buyerId, quantity) => economyAPI.createOrder(listingId, buyerId, quantity));
    ipcMain.handle('economy:marketplace:userOrders', async (_e, userId, role) => economyAPI.getOrdersForUser(userId, role));
    ipcMain.handle('economy:marketplace:submitReview', async (_e, orderId, reviewerId, rating, comment) => economyAPI.submitReview(orderId, reviewerId, rating, comment));
    ipcMain.handle('economy:marketplace:reputation', async (_e, userId) => economyAPI.getUserReputation(userId));
    ipcMain.handle('economy:marketplace:stats', async () => economyAPI.getMarketplaceStats());

    // ─── Staking ───────────────────────────────────────────────────
    ipcMain.handle('economy:staking:stake', async (_e, stakerId, validatorId, amount, tokenType) => economyAPI.stake(stakerId, validatorId, amount, tokenType));
    ipcMain.handle('economy:staking:unstake', async (_e, stakeId, stakerId) => economyAPI.unstake(stakeId, stakerId));
    ipcMain.handle('economy:staking:claim', async (_e, stakeId, stakerId) => economyAPI.claimUnstaked(stakeId, stakerId));
    ipcMain.handle('economy:staking:getStake', async (_e, stakeId) => economyAPI.getStake(stakeId));
    ipcMain.handle('economy:staking:userStakes', async (_e, stakerId) => economyAPI.getStakesForUser(stakerId));
    ipcMain.handle('economy:staking:totalStaked', async (_e, tokenType) => economyAPI.getTotalStaked(tokenType));
    ipcMain.handle('economy:staking:registerValidator', async (_e, name, owner, commission, description) => economyAPI.registerValidator(name, owner, commission, description));
    ipcMain.handle('economy:staking:getValidator', async (_e, validatorId) => economyAPI.getValidator(validatorId));
    ipcMain.handle('economy:staking:listValidators', async (_e, status) => economyAPI.listValidators(status));
    ipcMain.handle('economy:staking:jailValidator', async (_e, validatorId, reason) => economyAPI.jailValidator(validatorId, reason));
    ipcMain.handle('economy:staking:unjailValidator', async (_e, validatorId) => economyAPI.unjailValidator(validatorId));
    ipcMain.handle('economy:staking:slashValidator', async (_e, validatorId, amount, reason) => economyAPI.slashValidator(validatorId, amount, reason));
    ipcMain.handle('economy:staking:distributeRewards', async () => economyAPI.distributeRewards());
    ipcMain.handle('economy:staking:rewardsHistory', async (_e, stakerId, limit) => economyAPI.getRewardsHistory(stakerId, limit));
    ipcMain.handle('economy:staking:unlockMatured', async () => economyAPI.unlockMaturedStakes());
    ipcMain.handle('economy:staking:stats', async () => economyAPI.getStakingStats());

    // ════════════════════════════════════════════════════════════════
    // GOVERNANCE IPC HANDLERS
    // ════════════════════════════════════════════════════════════════

    const govAPI = {
        // Health
        health: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/health`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Proposals
        createProposal: async (title, description, proposer, vetoPower, urgency, sector) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/proposals`, { title, description, proposer, veto_power: vetoPower, urgency, sector }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        listProposals: async (state, proposer, limit) => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/proposals`, { params: { state, proposer, limit } }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getProposal: async (proposalId) => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/proposals/${proposalId}`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        activateProposal: async (proposalId) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/proposals/${proposalId}/activate`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        finalizeProposal: async (proposalId) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/proposals/${proposalId}/finalize`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Voting
        castVote: async (proposalId, voterAddress, decision, weight, rationale) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/vote`, { proposal_id: proposalId, voter_address: voterAddress, decision, weight, rationale }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getTally: async (proposalId) => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/proposals/${proposalId}/tally`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Veto
        exerciseVeto: async (exercisedBy, reason, actionVetoed, proposalId) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/veto`, { exercised_by: exercisedBy, reason, action_vetoed: actionVetoed, proposal_id: proposalId }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getVetoStatus: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/veto/status`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Constitution
        sealConstitution: async (constitutionHash, sealedBy, jurisdiction, metadata) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/constitution/seal`, { constitution_hash: constitutionHash, sealed_by: sealedBy, jurisdiction, metadata }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        verifyConstitution: async (constitutionHash) => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/constitution/verify`, { params: { constitution_hash: constitutionHash } }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getLatestConstitution: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/constitution/latest`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getConstitutionStats: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/constitution/stats`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Audit
        queryAudit: async (query) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/audit/query`, query); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        verifyAuditChain: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/audit/verify-chain`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getAuditStats: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/audit/stats`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Council
        getCouncilStatus: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/council/status`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        addCouncilMember: async (name, memberType, country, expertise) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/council/members`, { name, member_type: memberType, country, expertise }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Bridge
        bridgeDecision: async (title, description, source, sector, urgency, context, autoVote, escalate) => {
            try { const r = await axios.post(`${API_BASE_URL}/api/governance/bridge/decide`, { title, description, source, sector, urgency, context, auto_vote: autoVote, escalate_grey_zone: escalate }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        getBridgeHistory: async (limit) => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/bridge/history`, { params: { limit } }); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Founders
        listFounders: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/founders`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
        // Stats
        getGovernanceStats: async () => {
            try { const r = await axios.get(`${API_BASE_URL}/api/governance/stats`); return r.data; }
            catch (e) { return { error: e.message }; }
        },
    };

    // ─── Governance: Health ──────────────────────────────────────
    ipcMain.handle('gov:health', async () => govAPI.health());

    // ─── Governance: Proposals ───────────────────────────────────
    ipcMain.handle('gov:proposals:create', async (_e, title, description, proposer, vetoPower, urgency, sector) =>
        govAPI.createProposal(title, description, proposer, vetoPower, urgency, sector));
    ipcMain.handle('gov:proposals:list', async (_e, state, proposer, limit) =>
        govAPI.listProposals(state, proposer, limit));
    ipcMain.handle('gov:proposals:get', async (_e, proposalId) =>
        govAPI.getProposal(proposalId));
    ipcMain.handle('gov:proposals:activate', async (_e, proposalId) =>
        govAPI.activateProposal(proposalId));
    ipcMain.handle('gov:proposals:finalize', async (_e, proposalId) =>
        govAPI.finalizeProposal(proposalId));

    // ─── Governance: Voting ──────────────────────────────────────
    ipcMain.handle('gov:vote:cast', async (_e, proposalId, voterAddress, decision, weight, rationale) =>
        govAPI.castVote(proposalId, voterAddress, decision, weight, rationale));
    ipcMain.handle('gov:vote:tally', async (_e, proposalId) =>
        govAPI.getTally(proposalId));

    // ─── Governance: Veto ────────────────────────────────────────
    ipcMain.handle('gov:veto:exercise', async (_e, exercisedBy, reason, actionVetoed, proposalId) =>
        govAPI.exerciseVeto(exercisedBy, reason, actionVetoed, proposalId));
    ipcMain.handle('gov:veto:status', async () => govAPI.getVetoStatus());

    // ─── Governance: Constitution ────────────────────────────────
    ipcMain.handle('gov:constitution:seal', async (_e, constitutionHash, sealedBy, jurisdiction, metadata) =>
        govAPI.sealConstitution(constitutionHash, sealedBy, jurisdiction, metadata));
    ipcMain.handle('gov:constitution:verify', async (_e, constitutionHash) =>
        govAPI.verifyConstitution(constitutionHash));
    ipcMain.handle('gov:constitution:latest', async () => govAPI.getLatestConstitution());
    ipcMain.handle('gov:constitution:stats', async () => govAPI.getConstitutionStats());

    // ─── Governance: Audit ───────────────────────────────────────
    ipcMain.handle('gov:audit:query', async (_e, query) =>
        govAPI.queryAudit(query));
    ipcMain.handle('gov:audit:verify', async () => govAPI.verifyAuditChain());
    ipcMain.handle('gov:audit:stats', async () => govAPI.getAuditStats());

    // ─── Governance: Council ─────────────────────────────────────
    ipcMain.handle('gov:council:status', async () => govAPI.getCouncilStatus());
    ipcMain.handle('gov:council:addMember', async (_e, name, memberType, country, expertise) =>
        govAPI.addCouncilMember(name, memberType, country, expertise));

    // ─── Governance: Bridge ──────────────────────────────────────
    ipcMain.handle('gov:bridge:decide', async (_e, title, description, source, sector, urgency, context, autoVote, escalate) =>
        govAPI.bridgeDecision(title, description, source, sector, urgency, context, autoVote, escalate));
    ipcMain.handle('gov:bridge:history', async (_e, limit) =>
        govAPI.getBridgeHistory(limit));

    // ─── Governance: Founders ────────────────────────────────────
    ipcMain.handle('gov:founders:list', async () => govAPI.listFounders());

    // ─── Governance: Stats ───────────────────────────────────────
    ipcMain.handle('gov:stats', async () => govAPI.getGovernanceStats());
}

/**
 * App event handlers
 */
app.whenReady().then(() => {
    createWindow();
    createMenu();
    setupIpcHandlers();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    // Cleanup before quit
    console.log('ASIMNEXUS Desktop shutting down...');
});
