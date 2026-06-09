/**
 * ASIMNEXUS Desktop App - Renderer Process
 * Uses window.asimnexusAPI exposed via preload.js contextBridge
 * Handles page navigation, economy forms, chat, and settings
 */

const API = window.asimnexusAPI;

// ─── Page Navigation ───────────────────────────────────────────────────────

function navigateTo(pageId) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  // Deactivate all nav items
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  // Activate target
  const page = document.getElementById('page-' + pageId);
  if (page) page.classList.add('active');
  const nav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
  if (nav) nav.classList.add('active');
  // Load page content on first visit
  switch (pageId) {
    case 'dashboard': updateDashboard(); break;
    case 'founders': loadFounders(); break;
    case 'agents': loadAgents(); break;
    case 'security': loadSecurity(); break;
    case 'economy': loadEconomyStats(); break;
    case 'governance': loadGovernanceDashboard(); break;
    case 'settings': loadSettings(); break;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Sidebar navigation
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    el.addEventListener('click', () => navigateTo(el.dataset.page));
  });

  // Economy sub-navigation
  document.querySelectorAll('.sub-nav-item[data-sub]').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.sub-nav-item').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.sub-page').forEach(s => s.classList.remove('active'));
      el.classList.add('active');
      const sub = document.getElementById('econ-' + el.dataset.sub);
      if (sub) sub.classList.add('active');
    });
  });

  // Governance sub-navigation
  document.querySelectorAll('#gov-sub-nav .sub-nav-item[data-sub]').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('#gov-sub-nav .sub-nav-item').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('#page-governance .sub-page').forEach(s => s.classList.remove('active'));
      el.classList.add('active');
      const sub = document.getElementById('gov-' + el.dataset.sub);
      if (sub) sub.classList.add('active');
      // Load data when tab is clicked
      const tab = el.dataset.sub;
      if (tab === 'overview') loadGovernanceDashboard();
      if (tab === 'proposals') govListProposals();
      if (tab === 'veto') govRefreshVetoStatus();
      if (tab === 'constitution') govLatestConstitution();
      if (tab === 'audit') govGetAuditStats();
      if (tab === 'council') govGetCouncilStatus();
      if (tab === 'bridge') govBridgeHistory();
    });
  });

  // Initial load
  updateDashboard();
  loadSettings();

  // Periodic refresh every 5 seconds (dashboard only)
  setInterval(() => {
    const dashPage = document.getElementById('page-dashboard');
    if (dashPage && dashPage.classList.contains('active')) {
      updateDashboard();
    }
  }, 5000);
});

// ─── Utility ───────────────────────────────────────────────────────────────

function $(id) { return document.getElementById(id); }

function showError(msg) {
  const banner = $('error-banner');
  if (banner) { banner.textContent = '⚠ ' + msg; banner.style.display = 'block'; }
  const status = $('connection-status');
  if (status) { status.textContent = 'Disconnected'; status.className = 'status-error'; }
}

function clearError() {
  const banner = $('error-banner');
  if (banner) banner.style.display = 'none';
  const status = $('connection-status');
  if (status) { status.textContent = 'Connected'; status.className = 'status-ok'; }
}

function formatVal(v, suffix = '') {
  if (v === null || v === undefined || v === '—') return '—';
  return String(v) + suffix;
}

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════

function setMetricValue(cls, val) {
  const el = document.querySelector(`.metric-card.${cls} .metric-value`);
  if (el) el.textContent = val;
}
function setMetricError(cls) {
  const el = document.querySelector(`.metric-card.${cls} .metric-value`);
  if (el) { el.textContent = '—'; el.style.color = '#ef4444'; }
}

async function updateDashboard() {
  try {
    clearError();
    try {
      const analytics = await API.getAnalytics();
      if (analytics && !analytics.error) {
        setMetricValue('cpu', formatVal(analytics.cpu_usage, '%'));
        setMetricValue('memory', formatVal(analytics.ram_usage, '%'));
        setMetricValue('network', analytics.network_usage || analytics.status || '—');
        setMetricValue('storage', formatVal(analytics.disk_usage, '%'));
      } else {
        const health = await API.health();
        if (health && !health.error) {
          setMetricValue('cpu', '—');
          setMetricValue('memory', '—');
          setMetricValue('network', health.status || '—');
          setMetricValue('storage', '—');
        } else {
          throw new Error(health?.error || 'No data');
        }
      }
    } catch (e) {
      setMetricError('cpu'); setMetricError('memory');
      setMetricError('network'); setMetricError('storage');
      throw e;
    }

    const wos = await API.getWorldOSStatus();
    const wosEl = $('worldos-status');
    if (wosEl) {
      wosEl.textContent = wos?.status || 'Active';
      wosEl.className = 'status-ok';
    }
  } catch (err) {
    console.error('Dashboard error:', err);
    showError('Backend unavailable: ' + (err.message || 'connection failed'));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// FOUNDERS
// ═══════════════════════════════════════════════════════════════════════════

async function loadFounders() {
  const container = $('founders-content');
  container.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await API.getFounders();
    if (!data || data.error) {
      container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${data?.error || 'No data'}</p></div>`;
      return;
    }
    const list = data.founders || data.data || (Array.isArray(data) ? data : [data]);
    if (!Array.isArray(list) || list.length === 0) {
      container.innerHTML = '<div class="section-card"><p>No founders found.</p></div>';
      return;
    }
    let html = '<div class="card-grid">';
    list.forEach(f => {
      const status = f.status || 'active';
      const statusClass = status === 'active' ? 'active' : 'inactive';
      html += `<div class="person-card">
        <div class="name">${f.name || f.id || 'Unknown'}</div>
        <div class="role">${f.role || f.title || ''}</div>
        <div class="status"><span class="status-badge ${statusClass}">${status}</span></div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${err.message}</p></div>`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// AGENTS
// ═══════════════════════════════════════════════════════════════════════════

async function loadAgents() {
  const container = $('agents-content');
  container.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await API.getAgents();
    if (!data || data.error) {
      container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${data?.error || 'No data'}</p></div>`;
      return;
    }
    const list = data.agents || data.data || (Array.isArray(data) ? data : [data]);
    if (!Array.isArray(list) || list.length === 0) {
      container.innerHTML = '<div class="section-card"><p>No agents found.</p></div>';
      return;
    }
    let html = '<div class="card-grid">';
    list.forEach(a => {
      const status = a.status || 'active';
      const statusClass = status === 'active' ? 'active' : 'inactive';
      html += `<div class="person-card">
        <div class="name">${a.name || a.id || 'Unknown'}</div>
        <div class="role">${a.type || a.agent_type || ''}</div>
        <div class="status"><span class="status-badge ${statusClass}">${status}</span></div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${err.message}</p></div>`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// SECURITY
// ═══════════════════════════════════════════════════════════════════════════

async function loadSecurity() {
  const container = $('security-content');
  container.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await API.getSecurity();
    if (!data || data.error) {
      container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${data?.error || 'No data'}</p></div>`;
      return;
    }
    let html = '<div class="section-card"><h3>🔒 Security Status</h3>';
    if (data.status) html += `<div class="info-row"><span class="info-label">Status</span><span class="info-value">${data.status}</span></div>`;
    if (data.level) html += `<div class="info-row"><span class="info-label">Level</span><span class="info-value">${data.level}</span></div>`;
    if (data.encryption) html += `<div class="info-row"><span class="info-label">Encryption</span><span class="info-value">${data.encryption}</span></div>`;
    if (data.last_scan) html += `<div class="info-row"><span class="info-label">Last Scan</span><span class="info-value">${data.last_scan}</span></div>`;
    html += '</div>';

    const events = data.events || data.recent_events || [];
    if (Array.isArray(events) && events.length > 0) {
      html += '<div class="section-card"><h3>📋 Recent Events</h3>';
      events.slice(0, 20).forEach(ev => {
        html += `<div class="info-row"><span class="info-label">${ev.type || ev.event_type || 'Event'}</span><span class="info-value">${ev.description || ev.message || ''} ${ev.timestamp ? '— ' + ev.timestamp : ''}</span></div>`;
      });
      html += '</div>';
    }
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="section-card"><p style="color:#ef4444">Error: ${err.message}</p></div>`;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// ECONOMY - Load Stats
// ═══════════════════════════════════════════════════════════════════════════

async function loadEconomyStats() {
  // Wallet stats
  try {
    const ws = await API.getWalletStats();
    const el = $('wallet-stats-display');
    if (el && ws && !ws.error) {
      el.innerHTML = Object.entries(ws).map(([k, v]) =>
        `<span class="info-label">${k.replace(/_/g, ' ')}</span><span class="info-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span>`
      ).join('') || '<span class="info-label">No stats available</span>';
    }
  } catch (e) { /* ignore */ }

  // Token stats
  try {
    const ts = await API.getTokenStats();
    const el = $('token-stats-display');
    if (el && ts && !ts.error) {
      el.innerHTML = Object.entries(ts).map(([k, v]) =>
        `<span class="info-label">${k.replace(/_/g, ' ')}</span><span class="info-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span>`
      ).join('') || '<span class="info-label">No stats available</span>';
    }
  } catch (e) { /* ignore */ }

  // Escrow stats
  try {
    const es = await API.getEscrowStats();
    const el = $('escrow-stats-display');
    if (el && es && !es.error) {
      el.innerHTML = Object.entries(es).map(([k, v]) =>
        `<span class="info-label">${k.replace(/_/g, ' ')}</span><span class="info-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span>`
      ).join('') || '<span class="info-label">No stats available</span>';
    }
  } catch (e) { /* ignore */ }

  // Marketplace stats
  try {
    const ms = await API.getMarketplaceStats();
    const el = $('mp-stats-display');
    if (el && ms && !ms.error) {
      el.innerHTML = Object.entries(ms).map(([k, v]) =>
        `<span class="info-label">${k.replace(/_/g, ' ')}</span><span class="info-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span>`
      ).join('') || '<span class="info-label">No stats available</span>';
    }
  } catch (e) { /* ignore */ }

  // Staking stats
  try {
    const ss = await API.getStakingStats();
    const el = $('staking-stats-display');
    if (el && ss && !ss.error) {
      el.innerHTML = Object.entries(ss).map(([k, v]) =>
        `<span class="info-label">${k.replace(/_/g, ' ')}</span><span class="info-value">${typeof v === 'object' ? JSON.stringify(v) : v}</span>`
      ).join('') || '<span class="info-label">No stats available</span>';
    }
  } catch (e) { /* ignore */ }
}

// ═══════════════════════════════════════════════════════════════════════════
// WALLET ACTIONS
// ═══════════════════════════════════════════════════════════════════════════

async function walletCreate() {
  const owner = $('wallet-create-owner').value.trim();
  const type = $('wallet-create-type').value;
  if (!owner) { $('wallet-create-result').textContent = '⚠ Please enter an Owner ID'; return; }
  const r = await API.createWallet(owner, type);
  $('wallet-create-result').textContent = JSON.stringify(r, null, 2);
}

async function walletLookup() {
  const id = $('wallet-lookup-id').value.trim();
  if (!id) { $('wallet-lookup-result').textContent = '⚠ Please enter a Wallet ID'; return; }
  const r = await API.getWallet(id);
  $('wallet-lookup-result').textContent = JSON.stringify(r, null, 2);
}

async function walletLookupByOwner() {
  const id = $('wallet-lookup-id').value.trim();
  if (!id) { $('wallet-lookup-result').textContent = '⚠ Please enter an Owner ID'; return; }
  const r = await API.getWalletByOwner(id);
  $('wallet-lookup-result').textContent = JSON.stringify(r, null, 2);
}

async function walletDeposit() {
  const wid = $('wallet-tx-id').value.trim();
  const amt = parseFloat($('wallet-tx-amount').value);
  const type = $('wallet-tx-type').value;
  if (!wid || isNaN(amt)) { $('wallet-tx-result').textContent = '⚠ Enter wallet ID and amount'; return; }
  const r = await API.deposit(wid, amt, type);
  $('wallet-tx-result').textContent = JSON.stringify(r, null, 2);
}

async function walletWithdraw() {
  const wid = $('wallet-tx-id').value.trim();
  const amt = parseFloat($('wallet-tx-amount').value);
  const type = $('wallet-tx-type').value;
  if (!wid || isNaN(amt)) { $('wallet-tx-result').textContent = '⚠ Enter wallet ID and amount'; return; }
  const r = await API.withdraw(wid, amt, type);
  $('wallet-tx-result').textContent = JSON.stringify(r, null, 2);
}

async function walletTransfer() {
  const from = $('wallet-tx-id').value.trim();
  const to = $('wallet-transfer-to').value.trim();
  const amt = parseFloat($('wallet-tx-amount').value);
  const type = $('wallet-tx-type').value;
  if (!from || !to || isNaN(amt)) { $('wallet-tx-result').textContent = '⚠ Enter from, to wallet IDs and amount'; return; }
  const r = await API.transfer(from, to, amt, type);
  $('wallet-tx-result').textContent = JSON.stringify(r, null, 2);
}

// ═══════════════════════════════════════════════════════════════════════════
// TOKEN ACTIONS
// ═══════════════════════════════════════════════════════════════════════════

async function tokenRegister() {
  const name = $('token-reg-name').value.trim();
  const symbol = $('token-reg-symbol').value.trim();
  const supply = parseFloat($('token-reg-supply').value) || 0;
  const owner = $('token-reg-owner').value.trim();
  if (!name || !symbol) { $('token-reg-result').textContent = '⚠ Enter token name and symbol'; return; }
  const r = await API.registerToken(name, symbol, 'NRC-20', owner, supply, 18);
  $('token-reg-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenGet() {
  const id = $('token-action-id').value.trim();
  if (!id) { $('token-action-result').textContent = '⚠ Enter Token ID'; return; }
  const r = await API.getToken(id);
  $('token-action-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenMint() {
  const id = $('token-action-id').value.trim();
  const owner = $('token-action-owner').value.trim();
  const amt = parseFloat($('token-action-amount').value);
  if (!id || !owner || isNaN(amt)) { $('token-action-result').textContent = '⚠ Enter token ID, owner ID, and amount'; return; }
  const r = await API.mint(id, owner, amt);
  $('token-action-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenBurn() {
  const id = $('token-action-id').value.trim();
  const owner = $('token-action-owner').value.trim();
  const amt = parseFloat($('token-action-amount').value);
  if (!id || !owner || isNaN(amt)) { $('token-action-result').textContent = '⚠ Enter token ID, owner ID, and amount'; return; }
  const r = await API.burn(id, owner, amt);
  $('token-action-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenLock() {
  const id = $('token-action-id').value.trim();
  const owner = $('token-action-owner').value.trim();
  const amt = parseFloat($('token-action-amount').value);
  if (!id || !owner || isNaN(amt)) { $('token-action-result').textContent = '⚠ Enter token ID, owner ID, and amount'; return; }
  const r = await API.lockTokens(id, owner, amt);
  $('token-action-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenUnlock() {
  const id = $('token-action-id').value.trim();
  const owner = $('token-action-owner').value.trim();
  const amt = parseFloat($('token-action-amount').value);
  if (!id || !owner || isNaN(amt)) { $('token-action-result').textContent = '⚠ Enter token ID, owner ID, and amount'; return; }
  const r = await API.unlockTokens(id, owner, amt);
  $('token-action-result').textContent = JSON.stringify(r, null, 2);
}

async function tokenList() {
  const r = await API.listTokens();
  $('token-list-result').textContent = JSON.stringify(r, null, 2);
}

// ═══════════════════════════════════════════════════════════════════════════
// ESCROW ACTIONS
// ═══════════════════════════════════════════════════════════════════════════

async function escrowCreate() {
  const buyer = $('escrow-buyer').value.trim();
  const seller = $('escrow-seller').value.trim();
  const amt = parseFloat($('escrow-amount').value);
  const type = $('escrow-token-type').value;
  if (!buyer || !seller || isNaN(amt)) { $('escrow-create-result').textContent = '⚠ Enter buyer, seller, and amount'; return; }
  const r = await API.createEscrow(buyer, seller, amt, type);
  $('escrow-create-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowGet() {
  const id = $('escrow-id').value.trim();
  if (!id) { $('escrow-action-result').textContent = '⚠ Enter Escrow ID'; return; }
  const r = await API.getEscrow(id);
  $('escrow-action-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowFund() {
  const id = $('escrow-id').value.trim();
  if (!id) { $('escrow-action-result').textContent = '⚠ Enter Escrow ID'; return; }
  const r = await API.fundEscrow(id);
  $('escrow-action-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowRelease() {
  const id = $('escrow-id').value.trim();
  if (!id) { $('escrow-action-result').textContent = '⚠ Enter Escrow ID'; return; }
  const r = await API.releaseToSeller(id);
  $('escrow-action-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowRefund() {
  const id = $('escrow-id').value.trim();
  if (!id) { $('escrow-action-result').textContent = '⚠ Enter Escrow ID'; return; }
  const r = await API.refundToBuyer(id);
  $('escrow-action-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowDispute() {
  const id = $('escrow-id').value.trim();
  if (!id) { $('escrow-action-result').textContent = '⚠ Enter Escrow ID'; return; }
  const reason = prompt('Dispute reason (optional):') || 'other';
  const r = await API.raiseDispute(id, 'user', reason);
  $('escrow-action-result').textContent = JSON.stringify(r, null, 2);
}

async function escrowUserLookup() {
  const uid = $('escrow-user-id').value.trim();
  if (!uid) { $('escrow-user-result').textContent = '⚠ Enter User ID'; return; }
  const r = await API.getEscrowsForUser(uid);
  $('escrow-user-result').textContent = JSON.stringify(r, null, 2);
}

// ═══════════════════════════════════════════════════════════════════════════
// MARKETPLACE ACTIONS
// ═══════════════════════════════════════════════════════════════════════════

async function mpCreateListing() {
  const seller = $('mp-seller-id').value.trim();
  const title = $('mp-title').value.trim();
  const desc = $('mp-description').value.trim();
  const price = parseFloat($('mp-price').value);
  const cat = $('mp-category').value;
  if (!seller || !title || isNaN(price)) { $('mp-create-result').textContent = '⚠ Enter seller, title, and price'; return; }
  const r = await API.createListing(seller, title, desc, price, cat, 'nexus');
  $('mp-create-result').textContent = JSON.stringify(r, null, 2);
}

async function mpSearch() {
  const q = $('mp-search-query').value.trim();
  if (!q) { $('mp-search-result').textContent = '⚠ Enter a search query'; return; }
  const r = await API.searchListings(q, null, null, null, 'active');
  $('mp-search-result').textContent = JSON.stringify(r, null, 2);
}

async function mpGetListing() {
  const id = $('mp-search-query').value.trim();
  if (!id) { $('mp-search-result').textContent = '⚠ Enter a Listing ID'; return; }
  const r = await API.getListing(id);
  $('mp-search-result').textContent = JSON.stringify(r, null, 2);
}

async function mpCreateOrder() {
  const listing = $('mp-order-listing').value.trim();
  const buyer = $('mp-order-buyer').value.trim();
  if (!listing || !buyer) { $('mp-order-result').textContent = '⚠ Enter listing and buyer ID'; return; }
  const r = await API.createOrder(listing, buyer, 1);
  $('mp-order-result').textContent = JSON.stringify(r, null, 2);
}

// ═══════════════════════════════════════════════════════════════════════════
// STAKING ACTIONS
// ═══════════════════════════════════════════════════════════════════════════

async function stakeAction(action) {
  const staker = $('stake-staker').value.trim();
  const validator = $('stake-validator').value.trim();
  const amt = parseFloat($('stake-amount').value);
  const type = $('stake-token-type').value;

  if (action === 'stake') {
    if (!staker || !validator || isNaN(amt)) { $('stake-action-result').textContent = '⚠ Enter staker, validator, and amount'; return; }
    const r = await API.stake(staker, validator, amt, type);
    $('stake-action-result').textContent = JSON.stringify(r, null, 2);
  } else if (action === 'unstake') {
    if (!staker) { $('stake-action-result').textContent = '⚠ Enter stake ID in the Staker ID field'; return; }
    const r = await API.unstake(staker, staker);
    $('stake-action-result').textContent = JSON.stringify(r, null, 2);
  } else if (action === 'claim') {
    if (!staker) { $('stake-action-result').textContent = '⚠ Enter stake ID in the Staker ID field'; return; }
    const r = await API.claimUnstaked(staker, staker);
    $('stake-action-result').textContent = JSON.stringify(r, null, 2);
  }
}

async function valRegister() {
  const name = $('val-name').value.trim();
  const owner = $('val-owner').value.trim();
  const comm = parseFloat($('val-commission').value) || 10;
  const desc = $('val-desc').value.trim();
  if (!name || !owner) { $('val-result').textContent = '⚠ Enter name and owner'; return; }
  const r = await API.registerValidator(name, owner, comm, desc);
  $('val-result').textContent = JSON.stringify(r, null, 2);
}

async function valList() {
  const r = await API.listValidators();
  $('val-result').textContent = JSON.stringify(r, null, 2);
}

async function rewardsHistory() {
  const staker = $('rewards-staker').value.trim();
  if (!staker) { $('rewards-result').textContent = '⚠ Enter staker ID'; return; }
  const r = await API.getRewardsHistory(staker, 50);
  $('rewards-result').textContent = JSON.stringify(r, null, 2);
}

async function distributeRewards() {
  const r = await API.distributeRewards();
  $('rewards-result').textContent = JSON.stringify(r, null, 2);
}

async function unlockMatured() {
  const r = await API.unlockMaturedStakes();
  $('rewards-result').textContent = JSON.stringify(r, null, 2);
}

// ═══════════════════════════════════════════════════════════════════════════
// CHAT
// ═══════════════════════════════════════════════════════════════════════════

let chatUseWorldOS = true;
let chatHistory = [];

function toggleChatOS() {
  chatUseWorldOS = !chatUseWorldOS;
  const btn = $('chat-os-toggle');
  if (btn) btn.textContent = chatUseWorldOS ? '🌐 World OS: ON' : '💻 Local: ON';
}

function addChatMessage(role, text) {
  const container = $('chat-messages');
  const empty = container.querySelector('.chat-empty');
  if (empty) empty.remove();

  const div = document.createElement('div');
  div.className = 'chat-message ' + role;
  const time = new Date().toLocaleTimeString();
  div.innerHTML = text.replace(/\n/g, '<br>') + `<div class="msg-time">${time}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;

  chatHistory.push({ role, text, time });
  if (chatHistory.length > 100) chatHistory.shift();
}

async function sendChat() {
  const input = $('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  addChatMessage('user', msg);
  try {
    const r = await API.chat(msg, chatUseWorldOS);
    const reply = r?.response || r?.message || r?.reply || JSON.stringify(r);
    addChatMessage('bot', reply);
  } catch (err) {
    addChatMessage('bot', '⚠ Error: ' + err.message);
  }
}

function clearChat() {
  const container = $('chat-messages');
  container.innerHTML = '<div class="chat-empty">Send a message to start chatting with ASIMNEXUS</div>';
  chatHistory = [];
}

// ═══════════════════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════════════════

let autoRefreshEnabled = true;

async function loadSettings() {
  // About info
  try {
    const ver = await API.getAppVersion();
    const el = $('about-version');
    if (el) el.textContent = ver || '1.0.0';
  } catch (e) { /* ignore */ }
  const plat = $('about-platform');
  if (plat) plat.textContent = API.platform + ' ' + API.arch;
  const nv = $('about-node');
  if (nv && window.nodeVersions) nv.textContent = window.nodeVersions.node;
  const cv = $('about-chrome');
  if (cv && window.nodeVersions) cv.textContent = window.nodeVersions.chrome;
  const ev = $('about-electron');
  if (ev && window.nodeVersions) ev.textContent = window.nodeVersions.electron;

  // Load saved settings
  try {
    const settings = await API.getSettings();
    if (settings) {
      if (settings.apiUrl) $('settings-api-url').value = settings.apiUrl;
      if (settings.autoRefresh !== undefined) {
        autoRefreshEnabled = settings.autoRefresh;
        const sw = $('settings-autorefresh');
        if (sw) sw.classList.toggle('active', autoRefreshEnabled);
      }
    }
  } catch (e) { /* ignore */ }
}

async function testConnection() {
  const url = $('settings-api-url').value.trim();
  if (!url) { $('settings-connection-result').textContent = '⚠ Enter a URL'; return; }
  $('settings-connection-result').textContent = 'Testing connection...';
  try {
    const r = await API.health();
    if (r && !r.error) {
      $('settings-connection-result').textContent = '✅ Connected! Response: ' + JSON.stringify(r);
      // Save API URL
      await API.saveSettings({ apiUrl: url, autoRefresh: autoRefreshEnabled });
    } else {
      $('settings-connection-result').textContent = '❌ Error: ' + (r?.error || 'No response');
    }
  } catch (err) {
    $('settings-connection-result').textContent = '❌ Connection failed: ' + err.message;
  }
}

function toggleAutoRefresh() {
  const sw = $('settings-autorefresh');
  autoRefreshEnabled = !autoRefreshEnabled;
  sw.classList.toggle('active', autoRefreshEnabled);
  API.saveSettings({ autoRefresh: autoRefreshEnabled, apiUrl: $('settings-api-url').value.trim() });
}

// ═════════════════════════════════════════════════════════════════════════════
// GOVERNANCE HANDLERS
// ═════════════════════════════════════════════════════════════════════════════

const $g = (id) => document.getElementById(id);

// ─── Dashboard ──────────────────────────────────────────────────────────────
async function loadGovernanceDashboard() {
  // Health
  const health = await API.governanceHealth();
  if (health && !health.error) {
    $g('gov-health-status').textContent = health.status || 'unknown';
    $g('gov-health-status').className = health.status === 'healthy' ? 'status-ok' : 'status-error';
    $g('gov-health-modules').textContent = (health.modules || []).join(', ') || 'none';
  } else {
    $g('gov-health-status').textContent = '❌ ' + (health?.error || 'unavailable');
    $g('gov-health-status').className = 'status-error';
  }

  // Stats
  const stats = await API.getGovernanceStats();
  if (stats && !stats.error) {
    $g('gov-stat-proposals').textContent = stats.proposals?.total ?? '—';
    $g('gov-stat-active').textContent = stats.proposals?.active ?? '—';
    $g('gov-stat-audit').textContent = stats.audit?.total_entries ?? '—';
    $g('gov-stat-council').textContent = stats.council?.total_members ?? '—';
    $g('gov-stat-anchors').textContent = stats.constitution?.anchors_count ?? '—';
    $g('gov-stat-bridge').textContent = stats.bridge?.total_decisions ?? '—';
    $g('gov-stat-veto').textContent = stats.veto?.active ? '✅ Active' : '❌ Inactive';
  }
}

// ─── Proposals ──────────────────────────────────────────────────────────────
async function govCreateProposal() {
  const title = $g('gov-prop-title').value.trim();
  const desc = $g('gov-prop-desc').value.trim();
  const proposer = $g('gov-prop-proposer').value.trim() || 'anonymous';
  const urgency = $g('gov-prop-urgency').value;
  const sector = $g('gov-prop-sector').value;

  if (!title) { $g('gov-prop-result').textContent = '❌ Title is required'; return; }

  $g('gov-prop-result').textContent = '⏳ Creating proposal...';
  const r = await API.createProposal(title, desc, proposer, null, urgency, sector);
  $g('gov-prop-result').textContent = r?.error ? '❌ ' + r.error : '✅ Created: ' + JSON.stringify(r, null, 2);
  govListProposals();
}

async function govListProposals() {
  const r = await API.listProposals(null, null, 50);
  const list = $g('gov-proposals-list');
  if (r?.error) { list.innerHTML = '<p class="error-text">❌ ' + r.error + '</p>'; return; }

  const proposals = r?.proposals || [];
  if (proposals.length === 0) {
    list.innerHTML = '<p class="help-text">No proposals found.</p>';
    return;
  }
  list.innerHTML = proposals.map((p, i) =>
    `<div class="list-item">
      <strong>#${i + 1}</strong> <span>${p.title || 'Untitled'}</span>
      <span class="badge badge-${p.state === 'active' ? 'success' : 'secondary'}">${p.state || 'draft'}</span>
      <br><small>ID: ${p.proposal_id} | Proposer: ${p.proposer}</small>
    </div>`
  ).join('');
}

// ─── Voting ─────────────────────────────────────────────────────────────────
async function govCastVote() {
  const proposalId = $g('gov-vote-prop-id').value.trim();
  const voter = $g('gov-vote-voter').value.trim();
  const decision = $g('gov-vote-decision').value;
  const weight = parseFloat($g('gov-vote-weight').value) || 1;
  const rationale = $g('gov-vote-rationale').value.trim();

  if (!proposalId || !voter) { $g('gov-vote-result').textContent = '❌ Proposal ID and Voter are required'; return; }

  $g('gov-vote-result').textContent = '⏳ Casting vote...';
  const r = await API.castVote(proposalId, voter, decision, weight, rationale);
  $g('gov-vote-result').textContent = r?.error ? '❌ ' + r.error : '✅ Vote cast: ' + JSON.stringify(r, null, 2);
}

async function govGetTally() {
  const proposalId = $g('gov-vote-prop-id').value.trim() || prompt('Enter Proposal ID:');
  if (!proposalId) return;

  $g('gov-vote-result').textContent = '⏳ Fetching tally...';
  const r = await API.getTally(proposalId);
  if (r?.error) { $g('gov-vote-result').textContent = '❌ ' + r.error; return; }

  $g('gov-tally-for').textContent = r?.for ?? r?.votes_for ?? '—';
  $g('gov-tally-against').textContent = r?.against ?? r?.votes_against ?? '—';
  $g('gov-tally-abstain').textContent = r?.abstain ?? '—';
  $g('gov-tally-pct').textContent = r?.approval_pct != null ? (r.approval_pct * 100).toFixed(1) + '%' : '—';
  $g('gov-vote-result').textContent = '✅ Tally updated';
}

// ─── Veto ───────────────────────────────────────────────────────────────────
async function govExerciseVeto() {
  const exercisedBy = $g('gov-veto-by').value.trim();
  const reason = $g('gov-veto-reason').value.trim();
  const actionVetoed = $g('gov-veto-action').value.trim();
  const proposalId = $g('gov-veto-prop-id').value.trim();

  if (!exercisedBy || !reason || !actionVetoed) {
    $g('gov-veto-result').textContent = '❌ All fields except Proposal ID are required'; return;
  }

  $g('gov-veto-result').textContent = '⏳ Exercising veto...';
  const r = await API.exerciseVeto(exercisedBy, reason, actionVetoed, proposalId);
  $g('gov-veto-result').textContent = r?.error ? '❌ ' + r.error : '✅ Veto recorded: ' + JSON.stringify(r, null, 2);
  govRefreshVetoStatus();
}

async function govRefreshVetoStatus() {
  const r = await API.getVetoStatus();
  const list = $g('gov-veto-records');
  if (r?.error) { list.innerHTML = '<p class="error-text">❌ ' + r.error + '</p>'; return; }

  const records = r?.veto_records || [];
  list.innerHTML =
    '<div class="metric-row"><span>Veto Power Active</span><span>' + (r?.veto_power_active ? '✅ Yes' : '❌ No') + '</span></div>' +
    '<div class="metric-row"><span>Recent Vetoes</span><span>' + (r?.recent_vetoes ?? 0) + '</span></div>' +
    (records.length === 0 ? '<p class="help-text">No veto records.</p>' :
      records.map(v => `<div class="list-item"><small>${v.exercised_by}: ${v.reason} (${v.action_vetoed}) ${v.abuse_detected ? '⚠️ ABUSE' : ''}</small></div>`).join(''));
}

// ─── Constitution ───────────────────────────────────────────────────────────
async function govSealConstitution() {
  const hash = $g('gov-const-hash').value.trim();
  const sealer = $g('gov-const-sealer').value.trim() || 'system';
  const jurisdiction = $g('gov-const-jurisdiction').value.trim() || 'global';

  if (!hash) { $g('gov-const-result').textContent = '❌ Constitution hash is required'; return; }

  $g('gov-const-result').textContent = '⏳ Sealing constitution...';
  const r = await API.sealConstitution(hash, sealer, jurisdiction, {});
  $g('gov-const-result').textContent = r?.error ? '❌ ' + r.error : '✅ Sealed: ' + JSON.stringify(r, null, 2);
  govLatestConstitution();
}

async function govVerifyConstitution() {
  const hash = $g('gov-const-hash').value.trim();
  if (!hash) { $g('gov-const-result').textContent = '❌ Constitution hash is required'; return; }

  $g('gov-const-result').textContent = '⏳ Verifying...';
  const r = await API.verifyConstitution(hash);
  $g('gov-const-result').textContent = r?.error ? '❌ ' + r.error :
    (r?.verified ? '✅ Verified on chain' : '❌ Not found on chain');
}

async function govLatestConstitution() {
  const r = await API.getLatestConstitution();
  if (r?.error) { $g('gov-const-result').textContent = '❌ ' + r.error; return; }

  // Also load stats
  const stats = await API.getConstitutionStats();
  if (stats && !stats.error) {
    $g('gov-const-count').textContent = stats.anchors_count ?? stats.anchorsCount ?? '—';
    $g('gov-const-latest').textContent = stats.latest_hash ?? stats.latestHash ?? '—';
    $g('gov-const-integrity').textContent = stats.chain_integrity ?? stats.chainIntegrity ?? '—';
  }
  $g('gov-const-result').textContent = r?.latest_anchor ? '✅ Latest: ' + JSON.stringify(r.latest_anchor).slice(0, 200) : 'ℹ️ No anchors yet';
}

// ─── Audit ──────────────────────────────────────────────────────────────────
async function govQueryAudit() {
  const action = $g('gov-audit-action').value.trim() || undefined;
  const actor = $g('gov-audit-actor').value.trim() || undefined;
  const limit = parseInt($g('gov-audit-limit').value) || 20;

  $g('gov-audit-result').textContent = '⏳ Querying audit...';
  const r = await API.queryAudit({ action, actor, limit });
  const entries = r?.entries || [];
  const list = $g('gov-audit-entries');

  if (r?.error) { list.innerHTML = '<p class="error-text">❌ ' + r.error + '</p>'; return; }
  if (entries.length === 0) { list.innerHTML = '<p class="help-text">No audit entries found.</p>'; return; }

  list.innerHTML = entries.map(e =>
    `<div class="list-item">
      <strong>${e.action}</strong> by ${e.actor} on ${e.resource || '—'}
      <br><small>${e.severity} | ${new Date((e.timestamp || 0) * 1000).toLocaleString()}</small>
    </div>`
  ).join('');
  $g('gov-audit-result').textContent = `✅ Found ${entries.length} entries`;
}

async function govVerifyAuditChain() {
  $g('gov-audit-result').textContent = '⏳ Verifying chain...';
  const r = await API.verifyAuditChain();
  $g('gov-audit-result').textContent = r?.error ? '❌ ' + r.error :
    `🔗 Chain: ${r.status} (${r.total_entries} entries, ${(r.broken_links || []).length} broken)`;
}

async function govGetAuditStats() {
  const r = await API.getAuditStats();
  if (r?.error) { $g('gov-audit-result').textContent = '❌ ' + r.error; return; }

  const entries = $g('gov-audit-entries');
  entries.innerHTML =
    '<div class="metric-row"><span>Total Entries</span><span>' + (r.total_entries ?? '—') + '</span></div>' +
    '<div class="metric-row"><span>Unique Actions</span><span>' + (r.unique_actions ?? '—') + '</span></div>' +
    '<div class="metric-row"><span>Unique Actors</span><span>' + (r.unique_actors ?? '—') + '</span></div>' +
    '<div class="metric-row"><span>Chain Integrity</span><span>' + (r.chain_integrity ?? '—') + '</span></div>';
  $g('gov-audit-result').textContent = '✅ Stats loaded';
}

// ─── Council ────────────────────────────────────────────────────────────────
async function govGetCouncilStatus() {
  $g('gov-council-result').textContent = '⏳ Loading council...';
  const r = await API.getCouncilStatus();
  const display = $g('gov-council-result');
  if (r?.error) { display.textContent = '❌ ' + r.error; return; }

  const members = r?.council_members || [];
  let html =
    '<div class="metric-row"><span>Total Members</span><span>' + (r.total_council_members ?? members.length) + '</span></div>' +
    '<div class="metric-row"><span>Active</span><span>' + (r.active_members ?? '—') + '</span></div>' +
    '<div class="metric-row"><span>Veto Active</span><span>' + (r.veto_power_active ? '✅' : '❌') + '</span></div>' +
    '<div class="metric-row"><span>Auto-refactor</span><span>' + (r.auto_refactor_enabled ? '✅' : '❌') + '</span></div>' +
    '<hr>';

  if (members.length > 0) {
    html += members.map(m =>
      `<div class="list-item">
        <strong>${m.name}</strong> (${m.member_type}) — ${m.country}
        <br><small>Expertise: ${(m.expertise || []).join(', ')}</small>
      </div>`
    ).join('');
  } else {
    html += '<p class="help-text">No council members loaded.</p>';
  }
  display.innerHTML = html;
}

async function govAddCouncilMember() {
  const name = $g('gov-council-name').value.trim();
  const type = $g('gov-council-type').value;
  const country = $g('gov-council-country').value.trim() || 'global';
  const expertiseStr = $g('gov-council-expertise').value.trim();

  if (!name) { $g('gov-council-add-result').textContent = '❌ Name is required'; return; }
  const expertise = expertiseStr ? expertiseStr.split(',').map(s => s.trim()) : [];

  $g('gov-council-add-result').textContent = '⏳ Adding member...';
  const r = await API.addCouncilMember(name, type, country, expertise);
  $g('gov-council-add-result').textContent = r?.error ? '❌ ' + r.error : '✅ Added: ' + JSON.stringify(r, null, 2);
  govGetCouncilStatus();
}

// ─── Bridge ─────────────────────────────────────────────────────────────────
async function govBridgeDecide() {
  const title = $g('gov-bridge-title').value.trim();
  const desc = $g('gov-bridge-desc').value.trim();
  const sector = $g('gov-bridge-sector').value;
  const urgency = $g('gov-bridge-urgency').value;
  const source = $g('gov-bridge-source').value.trim() || 'governance/api';

  if (!title || !desc) { $g('gov-bridge-result').textContent = '❌ Title and Description are required'; return; }

  $g('gov-bridge-result').textContent = '⏳ Submitting to bridge...';
  const r = await API.bridgeDecision(title, desc, source, sector, urgency, {}, true, true);
  $g('gov-bridge-result').textContent = r?.error ? '❌ ' + r.error : '✅ Result: ' + JSON.stringify(r, null, 2);
  govBridgeHistory();
}

async function govBridgeHistory() {
  const r = await API.getBridgeHistory(20);
  const list = $g('gov-bridge-history-list');
  if (r?.error) { list.innerHTML = '<p class="error-text">❌ ' + r.error + '</p>'; return; }

  const history = r?.history || [];
  if (history.length === 0) {
    list.innerHTML = '<p class="help-text">No bridge decisions yet.</p>';
    return;
  }
  list.innerHTML = history.map(h =>
    `<div class="list-item">
      <strong>${h.title || 'Untitled'}</strong>
      <span class="badge badge-${h.approved ? 'success' : 'danger'}">${h.approved ? '✅' : '❌'}</span>
      <br><small>Confidence: ${(h.confidence * 100).toFixed(1)}% | Escalated: ${h.escalated_to_human ? '⚠️ Yes' : 'No'}</small>
    </div>`
  ).join('');
}

console.log('ASIMNEXUS Desktop App renderer loaded');
