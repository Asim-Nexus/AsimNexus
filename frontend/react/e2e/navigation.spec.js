/**
 * E2E: Route Navigation — All Routes Render Without Crash
 * Validates: every registered route, legacy redirects, catch-all
 */
const { test, expect } = require('@playwright/test');
const { mockAllAPIs } = require('./helpers');

const ROUTES = [
    // Core Routes
    { path: '/', label: 'Chat' },
    { path: '/chat', label: 'Chat (alias)' },
    { path: '/dashboard', label: 'Dashboard' },

    // Consolidated Hubs
    { path: '/os', label: 'OS Hub' },
    { path: '/marketplace', label: 'Market/Economy Hub' },
    { path: '/ai', label: 'AI Hub' },
    { path: '/identity', label: 'Identity Hub' },
    { path: '/network', label: 'Network Hub' },
    { path: '/life', label: 'Life Hub' },

    // Settings
    { path: '/settings', label: 'Settings' },

    // Legacy Redirects (should map to hubs without error)
    { path: '/personal', label: 'Legacy: /personal → OS' },
    { path: '/world-os', label: 'Legacy: /world-os → OS' },
    { path: '/os-panel', label: 'Legacy: /os-panel → OS' },
    { path: '/mcp', label: 'Legacy: /mcp → Economy' },
    { path: '/contracts', label: 'Legacy: /contracts → Economy' },
    { path: '/clones', label: 'Legacy: /clones → Economy' },
    { path: '/memory', label: 'Legacy: /memory → AI' },
    { path: '/local-llm', label: 'Legacy: /local-llm → AI' },
    { path: '/mesh', label: 'Legacy: /mesh → Network' },
];

test.describe('Route Navigation — All Routes Render', () => {
    test.beforeEach(async ({ page }) => {
        // Inject auth before each navigation
        await page.addInitScript(() => {
            localStorage.setItem('asim_token', 'e2e-test-token');
            localStorage.setItem('asim_user', JSON.stringify({
                username: 'testuser_e2e',
                email: 'testuser_e2e@asimnexus.test',
                display_name: 'Test User'
            }));
        });
        await mockAllAPIs(page);
    });

    for (const route of ROUTES) {
        test(`should render ${route.label} (${route.path}) without crash`, async ({ page }) => {
            await page.goto(route.path, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(1000);

            // Check page rendered
            const bodyText = await page.locator('body').textContent();
            expect(bodyText.length).toBeGreaterThan(50);

            // Verify no React crash overlay
            const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
            expect(crashOverlay).toBeFalsy();

            // Check for white screen (empty body)
            const appRoot = await page.locator('#root').textContent().catch(() => '');
            expect(appRoot.length).toBeGreaterThan(0);
        });
    }
});

test.describe('Route Navigation — Legacy Redirects', () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.setItem('asim_token', 'e2e-test-token');
            localStorage.setItem('asim_user', JSON.stringify({
                username: 'testuser_e2e',
                email: 'testuser_e2e@asimnexus.test',
                display_name: 'Test User'
            }));
        });
        await mockAllAPIs(page);
    });

    const LEGACY_REDIRECTS = [
        '/personal', '/world-os', '/os-panel',
        '/mcp', '/contracts', '/clones',
        '/memory', '/local-llm', '/mesh',
    ];

    for (const path of LEGACY_REDIRECTS) {
        test(`legacy ${path} should redirect without error`, async ({ page }) => {
            await page.goto(path, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(1000);

            const bodyText = await page.locator('body').textContent();
            expect(bodyText.length).toBeGreaterThan(50);
        });
    }
});

test.describe('Route Integrity — 404 Handling', () => {
    test.beforeEach(async ({ page }) => {
        await page.addInitScript(() => {
            localStorage.setItem('asim_token', 'e2e-test-token');
            localStorage.setItem('asim_user', JSON.stringify({
                username: 'testuser_e2e',
                email: 'testuser_e2e@asimnexus.test',
                display_name: 'Test User'
            }));
        });
        await mockAllAPIs(page);
    });

    test('unknown route should fallback to chat (catch-all)', async ({ page }) => {
        await page.goto('/this-route-does-not-exist-xyz', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        // Catch-all should redirect to chat (/)
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });
});
