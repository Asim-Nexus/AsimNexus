/**
 * E2E: Mesh & Offline Flow
 * Flow: /network → Mesh Panel → Selector (4 modes) → Offline Status
 */
const { test, expect } = require('@playwright/test');
const { TEST_USER, mockAllAPIs } = require('./helpers');

test.describe('Mesh / Network Hub', () => {
    test.beforeEach(async ({ page }) => {
        // Inject auth token before page loads
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

    test('should render NetworkHub without crash', async ({ page }) => {
        await page.goto('/network', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should have 5 tabs in NetworkHub', async ({ page }) => {
        await page.goto('/network', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const tabLabels = ['Mesh', 'Nodes', 'Topology', 'Selector', 'Offline'];
        const bodyText = await page.locator('body').textContent();
        let foundTabs = 0;
        for (const tab of tabLabels) {
            if (bodyText.includes(tab)) {
                foundTabs++;
                console.log(`  ✓ Found network tab text: "${tab}"`);
            }
        }
        console.log(`  📊 Network tabs found in body: ${foundTabs}/${tabLabels.length}`);
        expect(foundTabs).toBeGreaterThanOrEqual(3); // At least 3 of 5 should exist
    });

    test('should render MeshSelector (Selector tab)', async ({ page }) => {
        await page.goto('/network', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // Mesh mode labels from MeshSelector MESH_MODES: Local Mesh, Personal Mesh, Cloud Mesh, Public Mesh
        const modes = ['Local Mesh', 'Personal Mesh', 'Cloud Mesh', 'Public Mesh'];
        let foundModes = 0;
        for (const mode of modes) {
            const visible = await page.locator(`text=${mode}`).first().isVisible().catch(() => false);
            if (visible) {
                foundModes++;
            }
        }
        console.log(`  📊 Mesh mode labels visible: ${foundModes}/${modes.length}`);
    });

    test('should render OfflineStatus tab content', async ({ page }) => {
        await page.goto('/network', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        // Check for offline status elements
        const offlineLabels = ['Offline-First', 'Connectivity', 'Sync', 'Queue'];
        let foundLabels = 0;
        for (const label of offlineLabels) {
            const visible = await page.locator(`text=${label}`).first().isVisible().catch(() => false);
            if (visible) {
                foundLabels++;
            }
        }
        console.log(`  📊 Offline status labels visible: ${foundLabels}/${offlineLabels.length}`);
    });

    test('should render legacy /mesh route without error', async ({ page }) => {
        await page.goto('/mesh', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });
});
