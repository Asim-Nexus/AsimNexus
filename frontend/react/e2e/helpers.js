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
};

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
 * Login via auth page
 */
async function login(page) {
    await page.goto('/');
    // Check if already logged in by looking for chat interface
    const chatVisible = await page.locator('text=AsimNexus').first().isVisible().catch(() => false);
    if (chatVisible) return;

    // Fill login form
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
                body: JSON.stringify(responseData),
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
        user: { id: 'user-e2e-001', username: TEST_USER.username, email: TEST_USER.email }
    });

    // Personal / Status
    await mockAPI(page, 'GET', '**/api/personal/status', {
        status: 'active', mode: 'personal',
        created_at: '2025-01-01T00:00:00Z',
    });

    // Clones
    await mockAPI(page, 'GET', '**/personal/clones', [
        { id: 1, name: 'Clone Alpha', status: 'active', specialty: 'research' },
        { id: 2, name: 'Clone Beta', status: 'idle', specialty: 'development' },
    ]);

    // Lifecycle
    await mockAPI(page, 'GET', '**/api/universe/*/lifecycle', {
        user_id: 'user-e2e-001', current_state: 'active',
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
}

module.exports = {
    TEST_USER,
    NAV_LINKS,
    login,
    navigateTo,
    mockAPI,
    mockAllAPIs,
};
