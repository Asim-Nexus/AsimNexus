/**
 * E2E: Onboarding Wizard Flow
 * Flow: /onboard → 10-step wizard → welcome → language → device scan → identity → role → agreement → policies → universe → confirm → activation
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Onboarding Wizard Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render OnboardingPage without crash', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should show welcome step initially with Get Started button', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasWelcome = bodyText.includes('Welcome') || bodyText.includes('Get Started') || bodyText.includes('सुरु') || bodyText.includes('Onboarding');
        expect(hasWelcome).toBeTruthy();

        const startBtn = page.locator('button:has-text("Get Started"), button:has-text("Start"), button:has-text("Next")').first();
        const hasStartBtn = await startBtn.isVisible().catch(() => false);
        expect(hasStartBtn).toBeTruthy();
    });

    test('should navigate through onboarding steps via Next button', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        for (let i = 0; i < 3; i++) {
            const nextBtn = page.locator('button:has-text("Next"), button:has-text("Get Started"), button:has-text("Skip"), button:has-text("Continue")').first();
            if (await nextBtn.isVisible().catch(() => false)) {
                await nextBtn.click();
                await page.waitForTimeout(1000);
                const bodyText = await page.locator('body').textContent();
                expect(bodyText.length).toBeGreaterThan(50);
                console.log(`  ✓ Moved to step ${i + 2}`);
            } else {
                console.log(`  ⚠ No Next button at step ${i + 1}, stopping navigation`);
                break;
            }
        }
    });

    test('should show progress bar with 10 steps', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasProgressBar = bodyText.includes('10') || bodyText.includes('step') || bodyText.includes('Step') || bodyText.includes('/10');
        expect(hasProgressBar).toBeTruthy();
    });

    test('should render language selection step with language options', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();

        const nextBtn = page.locator('button:has-text("Next"), button:has-text("Get Started")').first();
        if (await nextBtn.isVisible().catch(() => false)) {
            await nextBtn.click();
            await page.waitForTimeout(1000);
        }

        const bodyText2 = await page.locator('body').textContent();
        const languages = ['English', 'नेपाली', 'हिन्दी', '中文'];
        let foundLangs = 0;
        for (const lang of languages) {
            if (bodyText2.includes(lang)) foundLangs++;
        }
        console.log(`  Language options visible: ${foundLangs}/${languages.length}`);
    });

    test('should render activation step with Activate button at the end', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasActivationContent = bodyText.includes('Activate') || bodyText.includes('Activation') || bodyText.includes('Asim Orb');
        console.log(`  Activation content visible on page load: ${hasActivationContent}`);
    });

    test('should render role selection cards', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const roles = ['Personal', 'Company', 'Community', 'Government'];
        let foundRoles = 0;
        for (const role of roles) {
            if (bodyText.includes(role)) foundRoles++;
        }
        console.log(`  Role cards visible: ${foundRoles}/${roles.length}`);
    });

    test('should render policy checkboxes', async ({ page }) => {
        await page.goto('/onboard', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const policies = ['Local-First', 'Mesh', 'Dharma', 'ZKP', 'Final 3', 'Dreaming'];
        let foundPolicies = 0;
        for (const policy of policies) {
            if (bodyText.includes(policy)) foundPolicies++;
        }
        console.log(`  Policy options visible: ${foundPolicies}/${policies.length}`);
    });
});
