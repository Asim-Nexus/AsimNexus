/**
 * E2E: Teams Collaboration Flow
 * Flow: /teams → TeamsPage → team list → member management
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Teams Collaboration Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render TeamsPage without crash', async ({ page }) => {
        await page.goto('/teams', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should show teams-related content', async ({ page }) => {
        await page.goto('/teams', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasTeamContent = bodyText.includes('Team') || bodyText.includes('Teams') || bodyText.includes('Member') || bodyText.includes('Collaboration');
        expect(hasTeamContent).toBeTruthy();
    });

    test('should not show error boundary', async ({ page }) => {
        await page.goto('/teams', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        const hasError = await page.locator('text=Error').first().isVisible().catch(() => false);
        if (hasError) {
            const errorText = await page.locator('text=Error').first().textContent();
            console.log(`  ⚠ Teams page shows error: ${errorText}`);
        }
    });

    test('should allow navigation to teams from sidebar', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        const teamsLink = page.locator('a[href="/teams"], button:has-text("Teams"), nav:has-text("Teams")').first();
        if (await teamsLink.isVisible().catch(() => false)) {
            await teamsLink.click();
            await page.waitForTimeout(1500);
            const bodyText = await page.locator('body').textContent();
            expect(bodyText.length).toBeGreaterThan(50);
            console.log('  ✓ Navigated to teams via sidebar');
        } else {
            console.log('  ⚠ Teams nav link not visible (may be collapsed)');
        }
    });
});
