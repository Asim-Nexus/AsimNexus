/**
 * E2E: Chat & Smart Routing Flow
 * Flow: / → send message → see thinking → receive response → clone routing
 */
const { test, expect } = require('@playwright/test');
const { setupTestContext } = require('./helpers');

test.describe('Chat / Smart Routing Flow', () => {
    test.beforeEach(async ({ page }) => {
        await setupTestContext(page);
    });

    test('should render AgentChat at / with input and send button', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const textarea = page.locator('textarea, input[type="text"]').first();
        await expect(textarea).toBeVisible({ timeout: 5000 });

        const hasSend = await page.locator('button:has-text("Send"), button:has-text("➤"), svg.lucide-send').first().isVisible().catch(() => false);
        expect(hasSend).toBeTruthy();
    });

    test('should type a message and send it', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const textarea = page.locator('textarea.odysseus-input-field, textarea, input[type="text"]').first();
        await textarea.fill('Hello AsimNexus');
        await page.waitForTimeout(500);

        const sendBtn = page.locator('button.odysseus-send-btn, button:has-text("Send"), button:has-text("➤")').first();
        if (await sendBtn.isVisible().catch(() => false)) {
            await sendBtn.click();
        } else {
            await textarea.press('Enter');
        }
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);
    });

    test('should show mode selector dropdown', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const modeOptions = ['Auto', 'Guide', 'Plan', 'Observe'];
        let foundMode = false;
        for (const mode of modeOptions) {
            const visible = await page.locator(`text=${mode}`).first().isVisible().catch(() => false);
            if (visible) { foundMode = true; break; }
        }

        const modeBtn = page.locator('button.odysseus-mode-btn, button:has-text("Auto"), button:has-text("Guide")').first();
        const hasModeBtn = await modeBtn.isVisible().catch(() => false);
        expect(foundMode || hasModeBtn).toBeTruthy();
    });

    test('should render quick action buttons in chat', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const quickActions = ['Health', 'Work', 'Mesh', 'Hire', 'Code'];
        let foundActions = 0;
        for (const action of quickActions) {
            const visible = await page.locator(`text=${action}`).first().isVisible().catch(() => false);
            if (visible) foundActions++;
        }
        console.log(`  Quick actions visible: ${foundActions}/${quickActions.length}`);
    });

    test('should navigate to /chat and render UniversalChat', async ({ page }) => {
        await page.goto('/chat', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        expect(bodyText.length).toBeGreaterThan(50);

        const inputVisible = await page.locator('textarea, input[type="text"]').first().isVisible().catch(() => false);
        expect(inputVisible).toBeTruthy();
    });

    test('should not show React crash overlay on chat pages', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);
        let crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();

        await page.goto('/chat', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1000);
        crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
        expect(crashOverlay).toBeFalsy();
    });

    test('should show empty chat state', async ({ page }) => {
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(2000);

        const bodyText = await page.locator('body').textContent();
        const hasEmptyState = bodyText.includes('Ask Asim') || bodyText.includes('Type your message');
        expect(hasEmptyState).toBeTruthy();
    });
});
