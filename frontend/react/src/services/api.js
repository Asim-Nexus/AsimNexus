/**
 * ASIMNEXUS API Service
 * Frontend connection to Backend
 * All API calls centralized here
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this.token = localStorage.getItem('token') || null;
  }

  // Helper: Make API call
  async fetch(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // GET request
  get(endpoint) {
    return this.fetch(endpoint, { method: 'GET' });
  }

  // POST request
  post(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ==========================================
  // AUTH & USER
  // ==========================================

  async login(email, password) {
    const result = await this.post('/api/auth/login', { email, password });
    if (result.token) {
      this.token = result.token;
      localStorage.setItem('token', result.token);
    }
    return result;
  }

  async register(email, password, displayName) {
    return this.post('/api/auth/register', { email, password, display_name: displayName });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('token');
  }

  // ==========================================
  // SYSTEM STATUS
  // ==========================================

  async getSystemStatus() {
    return this.get('/api/system/complete');
  }

  async getSystemInfo() {
    return this.get('/api/system/info');
  }

  // ==========================================
  // DHARMA / ΔT ENGINE
  // ==========================================

  async getDharmaStatus() {
    return this.get('/api/dharma/status');
  }

  async submitVeto(reason, severity = 'warning') {
    return this.post('/api/dharma/veto', { reason, severity });
  }

  // ==========================================
  // PERSONAL OS
  // ==========================================

  async getPersonalStatus() {
    return this.get('/api/personal/status');
  }

  async getPersonalUniverse() {
    return this.get('/api/personal/universe');
  }

  async getContracts() {
    return this.get('/api/personal/contracts');
  }

  // ==========================================
  // AGENT MODE
  // ==========================================

  async activateAgent(skills, maxDays = 15) {
    return this.post('/api/agent/mode/on', { skills, max_contract_days: maxDays });
  }

  async deactivateAgent() {
    return this.post('/api/agent/mode/off', {});
  }

  async getAgentStatus() {
    return this.get('/api/agent/status');
  }

  // ==========================================
  // FINANCIAL
  // ==========================================

  async getFinanceStatus() {
    return this.get('/api/finance/status');
  }

  async getCurrencies() {
    return this.get('/api/finance/currencies');
  }

  async getExchangeRates(base = 'USD') {
    return this.get(`/api/finance/exchange-rates?base=${base}`);
  }

  async createWallet(demoMode = true) {
    // Need user_id from context
    const userId = localStorage.getItem('user_id') || 'anonymous';
    return this.post('/api/finance/wallet/create', {
      user_id: userId,
      demo_mode: demoMode
    });
  }

  async getWallet(userId) {
    return this.get(`/api/finance/wallet/${userId}`);
  }

  // ==========================================
  // GOVERNMENT
  // ==========================================

  async getGovernmentStatus() {
    return this.get('/api/government/status');
  }

  async getIdentityCountries() {
    return this.get('/api/government/identity/countries');
  }

  async getEResidencyPrograms() {
    return this.get('/api/government/eresidency/programs');
  }

  async getTaxCountries() {
    return this.get('/api/government/tax/countries');
  }

  // ==========================================
  // MESH NETWORK
  // ==========================================

  async getMeshStatus() {
    return this.get('/api/mesh/status');
  }

  async getMeshStats() {
    return this.get('/api/mesh/stats');
  }

  async discoverMeshNodes() {
    return this.get('/api/mesh/nodes/discover');
  }

  async initMeshNode(nodeType, name, country) {
    return this.post('/api/mesh/node/init', {
      node_type: nodeType,
      name,
      country
    });
  }

  async getFederationMap() {
    return this.get('/api/mesh/federation/map');
  }

  async joinFederation(nodeId, level = 'full') {
    return this.post('/api/mesh/federation/join', {
      node_id: nodeId,
      level
    });
  }

  // ==========================================
  // CLONE SYNC
  // ==========================================

  async getCloneStatus(userId) {
    return this.get(`/api/mesh/clone/status/${userId}`);
  }

  async syncClone(userId, priority = 'normal', direction = 'bidirectional', data = {}) {
    return this.post('/api/mesh/clone/sync', {
      user_id: userId,
      priority,
      direction,
      data
    });
  }

  // ==========================================
  // OFFLINE SYNC
  // ==========================================

  async getOfflineStatus(userId) {
    return this.get(`/api/mesh/offline/status/${userId}`);
  }

  async getOfflineCapabilities() {
    return this.get('/api/mesh/offline/capabilities');
  }

  async createOfflineOperation(userId, nodeId, operation, target, data) {
    return this.post('/api/mesh/offline/operation', {
      user_id: userId,
      node_id: nodeId,
      operation,
      target,
      data
    });
  }

  // ==========================================
  // SOVEREIGNTY (AIR-GAP)
  // ==========================================

  async getAirGapStatus() {
    return this.get('/api/sovereignty/airgap/status');
  }

  async getAirGapHistory() {
    return this.get('/api/sovereignty/airgap/history');
  }

  async activateAirGap(mode = 'partial', reason = 'User requested') {
    const userId = localStorage.getItem('user_id') || 'anonymous';
    return this.post('/api/sovereignty/airgap/activate', {
      mode,
      reason,
      user_id: userId
    });
  }

  async restoreConnection(verifyIntegrity = true) {
    const userId = localStorage.getItem('user_id') || 'anonymous';
    return this.post('/api/sovereignty/airgap/restore', {
      user_id: userId,
      verify_integrity: verifyIntegrity
    });
  }

  // ==========================================
  // UNIVERSAL
  // ==========================================

  async getUniversalCurrencies() {
    return this.get('/api/universal/currencies');
  }

  async getUniversalCountries() {
    return this.get('/api/universal/countries');
  }

  async getUniversalLanguages() {
    return this.get('/api/universal/languages');
  }

  // ==========================================
  // ACCESSIBILITY
  // ==========================================

  async getAccessibilityStatus() {
    return this.get('/api/accessibility/status');
  }

  async getAccessibilityWCAG() {
    return this.get('/api/accessibility/wcag-compliance');
  }

  // ==========================================
  // PERFORMANCE
  // ==========================================

  async getPerformanceStatus() {
    return this.get('/api/performance/status');
  }

  async optimizePerformance(connectionType) {
    return this.post('/api/performance/optimize', {
      connection_type: connectionType
    });
  }

  // ==========================================
  // SECURITY
  // ==========================================

  async getSecurityStatus() {
    return this.get('/api/security/status');
  }

  async getEncryptionAlgorithms() {
    return this.get('/api/security/encryption-algorithms');
  }

  // ==========================================
  // OS CONTROL (Tool Execution)
  // ==========================================

  async getOsTools() {
    return this.get('/api/os/tools');
  }

  async executeOsTool(toolName, parameters = {}, agentName = 'AutoModeAgent') {
    return this.post('/api/os/execute', {
      tool_name: toolName,
      parameters,
      agent_name: agentName,
    });
  }

  async getOsPending() {
    return this.get('/api/os/pending');
  }

  async approveOsCall(callId) {
    return this.post(`/api/os/approve/${callId}`, {});
  }

  async rejectOsCall(callId) {
    return this.post(`/api/os/reject/${callId}`, {});
  }

  async getOsAudit(limit = 30) {
    return this.get(`/api/os/audit?limit=${limit}`);
  }

  async getOsStatus() {
    return this.get('/api/os/status');
  }

  async getOsMetrics() {
    return this.get('/api/os/metrics');
  }

  async getKernelStatus() {
    return this.get('/api/os/kernel');
  }
}

// Export singleton
export const api = new ApiService();

// Hook for React components
export function useApi() {
  return api;
}

export default api;
