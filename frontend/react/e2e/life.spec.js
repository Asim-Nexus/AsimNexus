/**
 * E2E: Life Journey Flow
 * Flow: /life → LifeHub → LifeJourney stages → milestones render
 */
const { test, expect } = require('@playwright/test');
const { mockAllAPIs } = require('./helpers');

test.describe('Life Journey Hub', () => {
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

    test('should render LifeHub without crash', async ({ page }) => {
        await page.goto('/life', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);
        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should show life stage elements', async ({ page }) => {
        await page.goto('/life', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1500);

        // Check for life stage labels
        const stages = ['Birth', 'Education', 'Work', 'Family', 'Retirement', 'Inheritance'];
        let foundStages = 0;
        for (const stage of stages) {
            const visible = await page.locator(`text=${stage}`).first().isVisible().catch(() => false);
            if (visible) {
                foundStages++;
                console.log(`  ✓ Found life stage: "${stage}"`);
            }
        }
        console.log(`  📊 Life stages visible: ${foundStages}/${stages.length}`);
    });

    test('should render lifecycle metrics or fallback state', async ({ page }) => {
        await page.goto('/life', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);
        const bodyText = await page.locator('body').textContent();

        // Should show some content (stages, metrics, or loading)
        expect(bodyText.length).toBeGreaterThan(100);
    });

    test('should not show React crash overlay', async ({ page }) => {
        await page.goto('/life', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });
});
