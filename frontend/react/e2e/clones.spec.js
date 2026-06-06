/**
 * E2E: Clones Flow — World Clones UI (EconomyHub)
 * Flow: /marketplace → Clones tab → clone list → status display
 */
const { test, expect } = require('@playwright/test');
const { TEST_USER, mockAllAPIs } = require('./helpers');

test.describe('Clones / Economy Hub', () => {
    test.beforeEach(async ({ page }) => {
        // Inject auth token before page loads (addInitScript runs before any JS)
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

    test('should render EconomyHub (marketplace) without crash', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should render at legacy /clones route without crash', async ({ page }) => {
        await page.goto('/clones', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should have tab navigation in EconomyHub', async ({ page }) => {
        await page.goto('/marketplace', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // EconomyHub tabs: Agents, Contracts, MCP Tools, Clones
        const possibleTabs = ['Agents', 'Contracts', 'MCP Tools', 'Clones', 'MCP'];
        const bodyText = await page.locator('body').textContent();
        let foundTab = false;
        for (const tab of possibleTabs) {
            if (bodyText.includes(tab)) {
                foundTab = true;
                console.log(`  ✓ Found tab text: "${tab}"`);
            }
        }
        console.log(`  📊 Economy tabs found in body: ${foundTab ? 'YES' : 'NO'}`);
        expect(foundTab).toBeTruthy();
    });
});
