/**
 * E2E Test Helpers — AsimNexus
 * Shared utilities, test user, API mocks, navigation helpers
 */
const { expect } = require('@playwright/test');

// ── Test User ──
const TEST_USER = {
    username: 'testuser_e2e',
    email: 'testuser_e2e@asimnexus.test',
    password: 'TestPass123!',
    display_name: 'Test User',
    id: 'user-e2e-001',
};

const TEST_DID = 'did:asim:test:zkp:abc123def456';

// ── Navigation ──
const NAV_LINKS = {
    Chat: '/',
    Dashboard: '/dashboard',
    OS: '/os',
    Market: '/marketplace',
    AI: '/ai',
    Identity: '/identity',
    Life: '/life',
    Network: '/network',
    Settings: '/settings',
};

/**
 * Inject auth state into page
 */
async function injectAuth(page) {
    await page.addInitScript(() => {
        localStorage.setItem('asimnexus_token', 'e2e-test-token');
        localStorage.setItem('asimnexus_user', JSON.stringify({
            id: 'user-e2e-001',
            username: 'testuser_e2e',
            email: 'testuser_e2e@asimnexus.test',
            display_name: 'Test User'
        }));
    });
}

/**
 * Login via auth page
 */
async function login(page) {
    await page.goto('/');
    const chatVisible = await page.locator('text=AsimNexus').first().isVisible().catch(() => false);
    if (chatVisible) return;

    await page.fill('input[type="text"], input[name="username"], input[placeholder*="user"]', TEST_USER.username);
    await page.fill('input[type="password"], input[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
    await page.waitForTimeout(2000);
}

/**
 * Navigate to a page via URL
 */
async function navigateTo(page, path) {
    await page.goto(path);
    await page.waitForTimeout(1000);
}

/**
 * Mock an API endpoint
 */
async function mockAPI(page, method, urlPattern, responseData) {
    await page.route(urlPattern, async (route) => {
        if (route.request().method() === method) {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: typeof responseData === 'string' ? responseData : JSON.stringify(responseData),
            });
        } else {
            await route.continue();
        }
    });
}

/**
 * Mock all common API endpoints for test isolation
 */
async function mockAllAPIs(page) {
    // Auth
    await mockAPI(page, 'POST', '**/auth/login', {
        success: true, token: 'test-token-e2e',
        user: { id: TEST_USER.id, username: TEST_USER.username, email: TEST_USER.email }
    });
    await mockAPI(page, 'GET', '**/auth/me', {
        id: TEST_USER.id, username: TEST_USER.username,
        email: TEST_USER.email, display_name: 'Test User',
        country_code: 'NP', created_at: '2025-01-01T00:00:00Z'
    });

    // Personal / Status
    await mockAPI(page, 'GET', '**/api/personal/status', {
        status: 'active', mode: 'personal',
        created_at: '2025-01-01T00:00:00Z',
        theme: 'deep-space',
        message_count: 42,
        active_clones: 2,
        active_contracts: 1,
        cpu_usage: 23,
        ram_usage: 45,
        dharma_score: 92,
    });
    await mockAPI(page, 'GET', '**/api/personal/universe', {
        mode: 'personal',
        layers: ['personal', 'family', 'community'],
        active_layer: 'personal',
    });
    await mockAPI(page, 'GET', '**/api/personal/resource-sharing', {
        enabled: true, percentage: 3,
    });

    // Clones
    await mockAPI(page, 'GET', '**/personal/clones', [
        { id: 1, name: 'Clone Alpha', status: 'active', specialty: 'research' },
        { id: 2, name: 'Clone Beta', status: 'idle', specialty: 'development' },
        { id: 3, name: 'Tech Architect', status: 'active', specialty: 'engineering' },
        { id: 4, name: 'Health Sage', status: 'idle', specialty: 'healthcare' },
        { id: 5, name: 'Financial Oracle', status: 'active', specialty: 'finance' },
    ]);

    // Chat / LLM
    await mockAPI(page, 'POST', '**/api/chat', {
        response: 'Hello! I am AsimNexus AI. How can I assist you today?',
        clone_used: 'Auto',
        intent: 'general',
        model: 'local-gguf',
        processing_time_ms: 450,
    });
    await mockAPI(page, 'POST', '**/llm/chat', {
        response: 'Greetings from the AsimNexus neural network.',
        model: 'local-gguf',
    });
    await mockAPI(page, 'POST', '**/chat', {
        response: 'Chat response via legacy endpoint.',
        clone_used: 'Auto',
    });

    // Memory
    await mockAPI(page, 'GET', '**/api/memory/stats', {
        total_messages: 42, unique_days: 15,
        average_per_day: 2.8, top_clone: 'Tech Architect',
    });
    await mockAPI(page, 'GET', '**/api/memory/recent', [
        { id: 'm1', role: 'user', content: 'Hello', timestamp: new Date().toISOString() },
        { id: 'm2', role: 'assistant', content: 'Hi there!', clone_used: 'Auto', timestamp: new Date().toISOString() },
    ]);
    await mockAPI(page, 'GET', '**/api/memory/search?q=*', []);
    await mockAPI(page, 'GET', '**/api/db/conversations/**', []);

    // Lifecycle
    await mockAPI(page, 'GET', '**/api/universe/*/lifecycle', {
        user_id: TEST_USER.id, current_state: 'active',
        created_at: '2025-01-01T00:00:00Z', age_days: 365,
        active_layers: 3, total_layers: 7,
        mesh_nodes: 2, activity_count: 150,
        last_activity: new Date().toISOString(), privacy_score: 85,
    });

    // Mesh
    await mockAPI(page, 'GET', '**/api/mesh/status', {
        status: 'connected', air_gap: { level: 0, label: 'Normal' },
        discovery: { running: true, local_ip: '192.168.1.100' },
        p2p: { running: true }, peers: [],
        uptime: 3600,
    });
    await mockAPI(page, 'GET', '**/api/mesh/peers', {
        peers: [
            { id: 'p1', name: 'Device Alpha', status: 'online', type: 'personal', latency: 5 },
            { id: 'p2', name: 'Mobile Phone', status: 'online', type: 'companion', latency: 12 },
        ]
    });
    await mockAPI(page, 'POST', '**/api/mesh/node/init', {
        success: true, node_id: 'n1', message: 'Node initialized'
    });
    await mockAPI(page, 'POST', '**/api/mesh/discover/start', {
        success: true, message: 'Discovery started'
    });
    await mockAPI(page, 'POST', '**/api/mesh/air-gap/engage', {
        success: true, message: 'Air-gap engaged', isolation_level: 1,
    });

    // Sync
    await mockAPI(page, 'GET', '**/api/sync/status', {
        status: 'active', last_sync: new Date().toISOString(),
        pending: 0, total_synced: 250,
    });
    await mockAPI(page, 'GET', '**/api/sync/queue', {
        queue: [], items: [], count: 0,
    });
    await mockAPI(page, 'GET', '**/api/mesh/offline/capabilities', {
        local_storage: true, indexed_db: true,
        service_worker: 'registered', background_sync: 'available',
        air_gap_mode: 'supported',
    });

    // Health
    await mockAPI(page, 'GET', '**/health', {
        status: 'healthy', uptime: 86400, version: '2.0.0',
    });
    await mockAPI(page, 'GET', '**/api/healing/connection', {
        status: 'connected', latency_ms: 25,
    });
    await mockAPI(page, 'GET', '**/api/system/info', {
        version: '2.0.0', mode: 'personal', local_llm: 'Qwen3-4B',
    });
    await mockAPI(page, 'GET', '**/api/local-llm/health', {
        status: 'loaded', model: 'Qwen3-4B-Q4_K_M',
    });

    // Agent
    await mockAPI(page, 'GET', '**/api/agent/sessions', [
        {
            session_id: 'ses-active-001', mode: 'AUTO', status: 'running',
            steps: 3, duration_seconds: 45,
            created_at: new Date(Date.now() - 60000).toISOString(),
            user_input: 'Check system health',
        },
        {
            session_id: 'ses-complete-002', mode: 'GUIDE', status: 'completed',
            steps: 7, duration_seconds: 120,
            created_at: new Date(Date.now() - 300000).toISOString(),
            user_input: 'Deploy contract',
            result: 'Contract deployed successfully',
        },
    ]);
    await mockAPI(page, 'GET', '**/api/agent/stats', {
        total_sessions: 15, active_sessions: 1, completed_sessions: 10,
        cancelled_sessions: 2, error_sessions: 2, avg_duration: 65,
    });
    await mockAPI(page, 'POST', '**/api/agent/run', {
        success: true, session_id: 'ses-new-003',
        message: 'Agent session started',
        status: 'running',
    });
    await mockAPI(page, 'POST', '**/api/agent/cancel', {
        success: true, message: 'Session cancelled',
    });
    await mockAPI(page, 'GET', '**/api/agent/status/*', {
        session_id: 'ses-active-001', status: 'running',
        steps: [{ step: 1, action: 'analyze', status: 'done' }],
        current_step: 2, total_steps: 5,
    });

    // Tools
    await mockAPI(page, 'GET', '**/api/tools/list', [
        { id: 't1', name: 'hw.cpu', category: 'hardware', risk: 'low' },
        { id: 't2', name: 'hw.memory', category: 'hardware', risk: 'low' },
        { id: 't3', name: 'fs.read', category: 'filesystem', risk: 'medium' },
        { id: 't4', name: 'network.scan', category: 'network', risk: 'high' },
        { id: 't5', name: 'os.execute', category: 'system', risk: 'dangerous' },
    ]);
    await mockAPI(page, 'POST', '**/api/tools/execute', {
        success: true, execution_id: 'exec-001',
        status: 'approved', result: { data: 'Tool executed successfully' },
    });
    await mockAPI(page, 'GET', '**/api/tools/pending', []);
    await mockAPI(page, 'POST', '**/api/tools/approve', { success: true });
    await mockAPI(page, 'POST', '**/api/tools/reject', { success: true });
    await mockAPI(page, 'GET', '**/api/tools/audit', [
        {
            execution_id: 'exec-001', tool_name: 'hw.cpu',
            user: 'testuser_e2e', status: 'completed', duration_ms: 150,
            timestamp: new Date().toISOString(),
            arguments: { core: 0 }, result: { usage: 23 },
        },
        {
            execution_id: 'exec-002', tool_name: 'fs.read',
            user: 'testuser_e2e', status: 'rejected', duration_ms: 0,
            timestamp: new Date().toISOString(),
            arguments: { path: '/etc/config' }, error: 'Rejected by user',
        },
    ]);

    // MCP
    await mockAPI(page, 'GET', '**/api/mcp/status', {
        servers: [
            { name: 'asim-memory', status: 'connected', tools_count: 5 },
            { name: 'asim-mesh', status: 'connected', tools_count: 3 },
            { name: 'asim-files', status: 'disconnected', tools_count: 4 },
        ]
    });
    await mockAPI(page, 'GET', '**/api/mcp/tools', [
        { name: 'memory_search', description: 'Search memory', parameters: { query: 'string' } },
        { name: 'mesh_status', description: 'Get mesh status', parameters: {} },
    ]);
    await mockAPI(page, 'POST', '**/api/mcp/call', {
        success: true, result: { data: 'MCP tool executed' }
    });
    await mockAPI(page, 'GET', '**/api/mcp/pending', []);
    await mockAPI(page, 'GET', '**/api/mcp/audit', []);

    // Identity
    await mockAPI(page, 'GET', '**/api/identity/stats', {
        total_identities: 1, active_identities: 1, algorithm: 'zkp-bls-384',
    });
    await mockAPI(page, 'GET', '**/api/identity/list', [
        { did: TEST_DID, display_name: 'Test User', universe: 'personal', active: true, created_at: '2025-01-01T00:00:00Z' },
    ]);
    await mockAPI(page, 'POST', '**/api/identity/create', {
        success: true, did: TEST_DID,
        message: 'Sovereign identity created successfully',
    });
    await mockAPI(page, 'POST', '**/api/identity/verify', {
        success: true, verified: true, message: 'Identity verified (ZKP)',
    });

    // HDT
    await mockAPI(page, 'POST', '**/api/hdt/create', {
        success: true, did: TEST_DID, message: 'HDT created',
    });
    await mockAPI(page, 'GET', '**/api/hdt/*', {
        did: TEST_DID, display_name: 'Test User',
        skills: ['python', 'farming'], verified_skills: 1,
        reputation: 85, dharma_score: 92,
        autonomy_level: 3, contracts_done: 5,
    });
    await mockAPI(page, 'POST', '**/api/hdt/*/skill', {
        success: true, message: 'Skill added',
    });
    await mockAPI(page, 'POST', '**/api/hdt/*/announce', {
        success: true, message: 'Skills announced to mesh',
    });

    // SVT
    await mockAPI(page, 'GET', '**/api/svt/stats', {
        total_supply: 1000000, burned: 50000, gini: 0.42,
        wallets: 150, burn_rate: 0.05, cap: 21000000,
    });
    await mockAPI(page, 'POST', '**/api/svt/wallet', {
        success: true, did: TEST_DID, address: 'svt:test:addr001',
        message: 'Wallet created',
    });
    await mockAPI(page, 'POST', '**/api/svt/mint', {
        success: true, amount: 100, new_balance: 10100,
        message: 'Minted 100 SVT',
    });
    await mockAPI(page, 'GET', '**/api/svt/wallet/*', {
        balance: 10000, earned_total: 5000, staked: 2000,
        percent_of_supply: 0.01, transactions: 25,
    });

    // Dharma
    await mockAPI(page, 'GET', '**/api/dharma/status', {
        status: 'active', verdict: 'BALANCED',
        symmetry: 0.85, gini: 0.42, l_max: 0.65,
        veto_active: false, nodes_count: 15,
    });
    await mockAPI(page, 'POST', '**/api/dharma/veto-check', {
        veto: false, reason: 'No ethical violation detected',
    });

    // Consensus
    await mockAPI(page, 'GET', '**/api/consensus/stats', {
        total_rounds: 50, approved: 35, rejected: 10,
        pending_human: 2, clone_count: 15,
        thresholds: { high: 9, critical: 12, sovereignty: 15 },
    });
    await mockAPI(page, 'GET', '**/api/consensus/pending', [
        { round_id: 'r1', topic: 'Upgrade protocol', level: 'HIGH', votes_for: 10, votes_against: 2 },
    ]);
    await mockAPI(page, 'GET', '**/api/consensus/list', [
        { round_id: 'r1', topic: 'Upgrade protocol', outcome: 'approved', level: 'HIGH', date: '2025-06-01' },
        { round_id: 'r2', topic: 'Adjust tax rate', outcome: 'rejected', level: 'CRITICAL', date: '2025-05-30' },
    ]);
    await mockAPI(page, 'POST', '**/api/consensus/vote', {
        success: true, round_id: 'r3', message: 'Vote started',
    });
    await mockAPI(page, 'POST', '**/api/consensus/*/override', {
        success: true, message: 'Override applied',
    });

    // Economy / Jobs
    await mockAPI(page, 'GET', '**/api/jobs/list', {
        jobs: [
            { id: 'j1', title: 'Build dApp', budget: 5000, skills: ['solidity', 'react'], status: 'open', poster: 'alice' },
            { id: 'j2', title: 'Design UI', budget: 2000, skills: ['figma', 'ui/ux'], status: 'open', poster: 'bob' },
        ],
        total: 2,
    });
    await mockAPI(page, 'POST', '**/api/jobs/post', {
        success: true, job_id: 'j3', message: 'Job posted',
    });
    await mockAPI(page, 'POST', '**/api/jobs/*/apply', {
        success: true, message: 'Application submitted',
    });

    // Contracts
    await mockAPI(page, 'GET', '**/api/contracts/**', [
        { id: 'c1', title: 'Development Contract', status: 'active', parties: ['alice', 'bob'], value: 5000 },
    ]);
    await mockAPI(page, 'POST', '**/api/contracts/propose', {
        success: true, contract_id: 'c2', message: 'Contract proposed',
    });
    await mockAPI(page, 'POST', '**/api/contracts/*/sign', {
        success: true, message: 'Contract signed',
    });

    // Reputation
    await mockAPI(page, 'GET', '**/api/reputation/**', {
        score: 85, level: 'trusted',
        ratings: 12, history: [],
    });

    // Bridge
    await mockAPI(page, 'GET', '**/api/bridge/**', {
        pools: [
            { name: 'SVT-USDC', liquidity: 50000, apy: 12.5 },
            { name: 'SVT-ETH', liquidity: 25000, apy: 8.3 },
        ],
        total_locked: 75000,
    });

    // World OS
    await mockAPI(page, 'GET', '**/api/quad/status', {
        citizen: 10, corporate: 3, government: 1, community: 5,
    });
    await mockAPI(page, 'GET', '**/api/bugs/stats', {
        total: 25, critical: 3, high: 7, applied: 15, pending: 10, auto_rate: 0.6,
    });
    await mockAPI(page, 'GET', '**/api/dht/status', {
        node_id: 'dht-node-001', nodes: 42, stored_keys: 150, buckets: 8,
    });
    await mockAPI(page, 'GET', '**/api/firewall/status', {
        patterns: 120, bias_types: ['gender', 'cultural'], sensitivity: 0.85,
    });
    await mockAPI(page, 'POST', '**/api/os/execute', {
        success: true, result: { data: 'OS command executed' },
    });

    // Deploy
    await mockAPI(page, 'GET', '**/api/deploy/status', {
        current_version: '2.0.0', target: 'linux-x64',
        checksum: 'abc123', published: '2025-06-01',
    });
    await mockAPI(page, 'GET', '**/api/deploy/targets', ['linux-x64', 'win-x64', 'mac-arm64']);
    await mockAPI(page, 'GET', '**/api/release/current', {
        version: '2.0.0', target: 'linux-x64', checksum: 'abc123',
        published: '2025-06-01', artifacts: ['asimnexus-linux-x64.tar.gz'],
    });
    await mockAPI(page, 'GET', '**/api/deploy/releases', [
        { version: '2.0.0', target: 'linux-x64', checksum: 'abc123', size_mb: 45, active: true },
        { version: '1.9.0', target: 'linux-x64', checksum: 'def456', size_mb: 42, active: false },
    ]);
    await mockAPI(page, 'POST', '**/api/deploy/build', {
        success: true, version: '2.1.0', message: 'Build triggered',
    });
    await mockAPI(page, 'POST', '**/api/deploy/release', {
        success: true, message: 'Release published',
    });
    await mockAPI(page, 'POST', '**/api/deploy/rollback', {
        success: true, message: 'Rollback initiated',
    });

    // Finance / Universal
    await mockAPI(page, 'GET', '**/api/universal/countries', [
        { code: 'NP', name: 'Nepal' },
        { code: 'US', name: 'United States' },
    ]);
    await mockAPI(page, 'GET', '**/api/universal/currencies', [
        { code: 'NPR', name: 'Nepalese Rupee', symbol: 'रू' },
        { code: 'USD', name: 'US Dollar', symbol: '$' },
    ]);
}

/**
 * Create a fresh mock context: inject auth + mock APIs
 */
async function setupTestContext(page) {
    await injectAuth(page);
    await mockAllAPIs(page);
}

/**
 * Wait for loading spinners to disappear
 */
async function waitForLoad(page, timeout = 5000) {
    try {
        await page.waitForFunction(() => {
            const loading = document.body.textContent;
            return !loading.includes('Loading') || loading.includes('Loading done');
        }, { timeout });
    } catch {
        // Continue even if timeout — content may have rendered without "Loading" disappearing
    }
}

module.exports = {
    TEST_USER,
    TEST_DID,
    NAV_LINKS,
    injectAuth,
    login,
    navigateTo,
    mockAPI,
    mockAllAPIs,
    setupTestContext,
    waitForLoad,
};
