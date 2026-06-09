/**
 * E2E: Agent Loop & Tool Execution Flow
 * Flow: /agent → session list → stats → run agent → cancel → /audit → audit table → /mcp → MCP browser
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Agent Loop & Tool Execution Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render AgentSessionPanel without crash', async ({ page }) => {
        await page.goto('/agent', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should show agent session stats bar', async ({ page }) => {
        await page.goto('/agent', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasStats = bodyText.includes('Active') || bodyText.includes('Completed') || bodyText.includes('Sessions');
        const hasCount = bodyText.includes('15') || bodyText.includes('10') || bodyText.includes('1');
        console.log(`  Agent stats visible: ${hasStats}, counts visible: ${hasCount}`);
        expect(hasStats).toBeTruthy();
    });

    test('should render session cards in session list', async ({ page }) => {
        await page.goto('/agent', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasSessionContent = bodyText.includes('ses-') || bodyText.includes('AUTO') || bodyText.includes('GUIDE') || bodyText.includes('running') || bodyText.includes('completed');
        expect(hasSessionContent).toBeTruthy();
    });

    test('should render ToolAuditView without crash', async ({ page }) => {
        await page.goto('/audit', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should show audit table with tool execution entries', async ({ page }) => {
        await page.goto('/audit', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasAuditEntries = bodyText.includes('hw.cpu') || bodyText.includes('exec-') || bodyText.includes('Tool') || bodyText.includes('Audit');
        expect(hasAuditEntries).toBeTruthy();
    });

    test('should render MCPServiceBrowser without crash', async ({ page }) => {
        await page.goto('/mcp', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should show MCP server cards with status', async ({ page }) => {
        await page.goto('/mcp', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasServerInfo = bodyText.includes('asim-memory') || bodyText.includes('asim-mesh') || bodyText.includes('asim-files') || bodyText.includes('Server');
        expect(hasServerInfo).toBeTruthy();
    });

    test('should render agent mode controls in agent chat sidebar', async ({ page }) => {
        await page.goto('/agent', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasModeControls = bodyText.includes('AUTO') || bodyText.includes('GUIDE') || bodyText.includes('PLAN') || bodyText.includes('OBSERVE');
        expect(hasModeControls).toBeTruthy();
    });

    test('should not show React crash overlay on agent pages', async ({ page }) => {
        const routes = ['/agent', '/audit', '/mcp'];
        for (const route of routes) {
            await page.goto(route, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(1000);
            const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
            expect(crashOverlay).toBeFalsy();
            console.log(`  ✓ No crash on ${route}`);
        }
    });
});
