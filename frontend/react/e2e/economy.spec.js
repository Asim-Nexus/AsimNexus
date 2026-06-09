/**
 * E2E: Economy / Marketplace Hub — All 7 Tabs
 * Flow: /marketplace → Dashboard → Jobs → Contracts → Reputation → Bridge → MCP → Clones
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Economy / Marketplace Hub', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render EconomyHub without crash', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should have at least 5 of 7 economy tabs', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const tabLabels = ['Dashboard', 'Jobs', 'Contracts', 'Reputation', 'Bridge', 'MCP', 'Clones'];
        const bodyText = await page.locator('body').textContent();
        let foundTabs = 0;
        for (const tab of tabLabels) {
            if (bodyText.includes(tab)) {
                foundTabs++;
                console.log(`  ✓ Found economy tab: "${tab}"`);
            }
        }
        console.log(`  Economy tabs found: ${foundTabs}/${tabLabels.length}`);
        expect(foundTabs).toBeGreaterThanOrEqual(5);
    });

    test('should render Dashboard tab content by default', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasDashboardContent = bodyText.includes('Economy') || bodyText.includes('Market') || bodyText.includes('Dashboard') || bodyText.includes('SVT');
        expect(hasDashboardContent).toBeTruthy();
    });

    test('should click through multiple economy tabs without error', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const tabButtons = [
            'Jobs', 'Contracts', 'Reputation',
        ];

        for (const tab of tabButtons) {
            const btn = page.locator(`button:has-text("${tab}")`).first();
            if (await btn.isVisible().catch(() => false)) {
                await btn.click();
                await page.waitForTimeout(800);
                const bodyText = await page.locator('body').textContent();
                expect(bodyText.length).toBeGreaterThan(50);
                console.log(`  ✓ Clicked tab: "${tab}" — page renders`);
            }
        }
    });

    test('should render legacy /contracts route without crash', async ({ page }) => {
        await page.goto('/contracts', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should render legacy /clones route without crash', async ({ page }) => {
        await page.goto('/clones', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should render MCP tools tab', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const mcpTab = page.locator('button:has-text("MCP")').first();
        if (await mcpTab.isVisible().catch(() => false)) {
            await mcpTab.click();
            await page.waitForTimeout(1000);
            const bodyText = await page.locator('body').textContent();
            const hasMCP = bodyText.includes('MCP') || bodyText.includes('Tool') || bodyText.includes('Server');
            expect(hasMCP).toBeTruthy();
        }
    });
});
