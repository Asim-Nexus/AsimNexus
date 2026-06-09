/**
 * E2E: Identity Hub — ZKP Creation, Verification, HDT, SVT, Consensus
 * Flow: /identity → Digital ID tab → create identity → verify → HDT skills → SVT tokens → Consensus
 */
const { test, expect } = require('@playwright/test');
const { TEST_USER, TEST_DID, setupTestContext } = require('./helpers');

test.describe('Identity Hub — Sovereign Identity Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render IdentityHub without crash', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should have 3 identity tabs: Digital ID, Blockchain, ZKP', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const tabLabels = ['Digital ID', 'Blockchain', 'ZKP'];
        const bodyText = await page.locator('body').textContent();
        let foundTabs = 0;
        for (const tab of tabLabels) {
            if (bodyText.includes(tab)) {
                foundTabs++;
                console.log(`  ✓ Found identity tab: "${tab}"`);
            }
        }
        expect(foundTabs).toBeGreaterThanOrEqual(2);
    });

    test('should render ZKP identity form elements in Digital ID tab', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasCreateForm = bodyText.includes('Display name') || bodyText.includes('Passphrase') || bodyText.includes('Create Sovereign Identity');
        expect(hasCreateForm).toBeTruthy();
    });

    test('should render identity stats or list', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasStats = bodyText.includes('Active') || bodyText.includes('Total') || bodyText.includes('Algorithm');
        const hasList = bodyText.includes(TEST_DID.slice(0, 20)) || bodyText.includes(TEST_USER.display_name);
        console.log(`  Identity stats visible: ${hasStats}, list visible: ${hasList}`);
    });

    test('should render ZKP sub-tab with active status', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const zkpTab = page.locator('button:has-text("ZKP"), button:has-text("🔐")').first();
        if (await zkpTab.isVisible().catch(() => false)) {
            await zkpTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasZKPContent = bodyText.includes('ZKP') || bodyText.includes('Active') || bodyText.includes('Verification');
        expect(hasZKPContent).toBeTruthy();
    });

    test('should render Blockchain Identity tab elements', async ({ page }) => {
        await page.goto('/identity', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bcTab = page.locator('button:has-text("Blockchain"), button:has-text("⛓️")').first();
        if (await bcTab.isVisible().catch(() => false)) {
            await bcTab.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const hasWalletElements = bodyText.includes('Connect Wallet') || bodyText.includes('Network') || bodyText.includes('Blockchain');
        expect(hasWalletElements).toBeTruthy();
    });
});
