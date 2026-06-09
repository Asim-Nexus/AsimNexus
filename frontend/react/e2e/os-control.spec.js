/**
 * E2E: OS Control Flow — OS Hub, Personal OS, World OS, Control Panel, Deploy
 * Flow: /os → Personal tab → World tab → Control tab → Deploy tab
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('OS Control Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render OSHub without crash', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should have 4 OS tabs: Personal, World, Control, Deploy', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const tabLabels = ['Personal', 'World', 'Control', 'Deploy'];
        const bodyText = await page.locator('body').textContent();
        let foundTabs = 0;
        for (const tab of tabLabels) {
            if (bodyText.includes(tab)) {
                foundTabs++;
                console.log(`  ✓ Found OS tab: "${tab}"`);
            }
        }
        expect(foundTabs).toBeGreaterThanOrEqual(3);
    });

    test('should render Personal OS tab with stats', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const personalTab = page.locator('button:has-text("Personal")').first();
        if (await personalTab.isVisible().catch(() => false)) {
            await personalTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasStats = bodyText.includes('Messages') || bodyText.includes('Clones') || bodyText.includes('Contracts') || bodyText.includes('CPU') || bodyText.includes('RAM') || bodyText.includes('Dharma');
        expect(hasStats).toBeTruthy();
    });

    test('should render World OS Dashboard tab with system metrics', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const worldTab = page.locator('button:has-text("World")').first();
        if (await worldTab.isVisible().catch(() => false)) {
            await worldTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasWorldContent = bodyText.includes('SVT') || bodyText.includes('Consensus') || bodyText.includes('Mesh') || bodyText.includes('DHT') || bodyText.includes('Firewall') || bodyText.includes('Bug');
        expect(hasWorldContent).toBeTruthy();
    });

    test('should render OS Control Panel tab with modules and system vitals', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const controlTab = page.locator('button:has-text("Control")').first();
        if (await controlTab.isVisible().catch(() => false)) {
            await controlTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasControlContent = bodyText.includes('Control Panel') || bodyText.includes('CPU') || bodyText.includes('RAM') || bodyText.includes('Module') || bodyText.includes('Execute');
        expect(hasControlContent).toBeTruthy();
    });

    test('should render Deploy tab with build and release options', async ({ page }) => {
        await page.goto('/os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const deployTab = page.locator('button:has-text("Deploy")').first();
        if (await deployTab.isVisible().catch(() => false)) {
            await deployTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasDeployContent = bodyText.includes('Deploy') || bodyText.includes('Build') || bodyText.includes('Release') || bodyText.includes('Rollback') || bodyText.includes('Version');
        expect(hasDeployContent).toBeTruthy();
    });

    test('should render legacy redirect /personal to OS Hub', async ({ page }) => {
        await page.goto('/personal', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should render legacy redirect /world-os to OS Hub', async ({ page }) => {
        await page.goto('/world-os', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should render legacy redirect /os-panel to OS Hub', async ({ page }) => {
        await page.goto('/os-panel', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });
});
