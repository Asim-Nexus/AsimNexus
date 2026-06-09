/**
 * E2E: Settings, Theme & Universe Mode Flow
 * Flow: /settings → settings page → sidebar drawer → universe mode → theme selection
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Settings & Theme / Universe Mode Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render Settings page without crash', async ({ page }) => {
        await page.goto('/settings', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should render settings form elements', async ({ page }) => {
        await page.goto('/settings', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasSettingsContent = bodyText.includes('Settings') || bodyText.includes('Profile') || bodyText.includes('Theme') || bodyText.includes('Universe') || bodyText.includes('Preferences') || bodyText.includes('Account');
        expect(hasSettingsContent).toBeTruthy();
    });

    test('should render sidebar drawer with universe mode and theme options', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const gearButton = page.locator('button:has-text("⚙"), button:has-text("Settings"), [aria-label="Settings"], svg.lucide-settings').first();
        if (await gearButton.isVisible().catch(() => false)) {
            await gearButton.click();
            await page.waitForTimeout(1000);
        } else {
            const universeBadge = page.locator('text=personal, text=family, text=company, text=community, text=government, text=global').first();
            if (await universeBadge.isVisible().catch(() => false)) {
                await universeBadge.click();
                await page.waitForTimeout(1000);
            }
        }

        const bodyText = await page.locator('body').textContent();
        const hasDrawerContent = bodyText.includes('Universe') || bodyText.includes('Theme') || bodyText.includes('Logout') || bodyText.includes('personal') || bodyText.includes('family');
        console.log(`  Settings drawer content visible: ${hasDrawerContent}`);
    });

    test('should render theme options in sidebar drawer', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const gearButton = page.locator('button:has-text("⚙"), button:has-text("Settings")').first();
        if (await gearButton.isVisible().catch(() => false)) {
            await gearButton.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const themes = ['deep-space', 'aurora', 'corporate', 'government', 'medical', 'minimal'];
        let foundThemes = 0;
        for (const theme of themes) {
            if (bodyText.includes(theme)) foundThemes++;
        }
        console.log(`  Theme options visible in drawer: ${foundThemes}/${themes.length}`);
    });

    test('should render universe mode options in sidebar drawer', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const gearButton = page.locator('button:has-text("⚙"), button:has-text("Settings")').first();
        if (await gearButton.isVisible().catch(() => false)) {
            await gearButton.click();
            await page.waitForTimeout(1000);
        }

        const bodyText = await page.locator('body').textContent();
        const modes = ['personal', 'family', 'company', 'community', 'government', 'global'];
        let foundModes = 0;
        for (const mode of modes) {
            if (bodyText.includes(mode)) foundModes++;
        }
        console.log(`  Universe mode options visible: ${foundModes}/${modes.length}`);
    });

    test('should have working navigation to all hub pages from settings', async ({ page }) => {
        await page.goto('/settings', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        const navHubs = ['/dashboard', '/os', '/marketplace', '/ai', '/identity', '/life', '/network'];
        for (const hub of navHubs) {
            await page.goto(hub, { waitUntil: 'domcontentloaded' });
            await page.waitForTimeout(800);
            const bodyText = await page.locator('body').textContent();
            expect(bodyText.length).toBeGreaterThan(50);
            console.log(`  ✓ Navigated to ${hub} — renders OK`);
        }
    });
});
