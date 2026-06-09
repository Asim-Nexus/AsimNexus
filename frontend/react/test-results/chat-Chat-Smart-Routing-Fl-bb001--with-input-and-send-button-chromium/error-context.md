# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.js >> Chat / Smart Routing Flow >> should render AgentChat at / with input and send button
- Location: e2e\chat.spec.js:13:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "http://localhost:3000/", waiting until "domcontentloaded"

```

# Test source

```ts
  1   | /**
  2   |  * E2E: Chat & Smart Routing Flow
  3   |  * Flow: / → send message → see thinking → receive response → clone routing
  4   |  */
  5   | const { test, expect } = require('@playwright/test');
  6   | const { setupTestContext } = require('./helpers');
  7   | 
  8   | test.describe('Chat / Smart Routing Flow', () => {
  9   |     test.beforeEach(async ({ page }) => {
  10  |         await setupTestContext(page);
  11  |     });
  12  | 
  13  |     test('should render AgentChat at / with input and send button', async ({ page }) => {
> 14  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
      |                    ^ Error: page.goto: Test timeout of 30000ms exceeded.
  15  |         await page.waitForTimeout(2000);
  16  | 
  17  |         const textarea = page.locator('textarea, input[type="text"]').first();
  18  |         await expect(textarea).toBeVisible({ timeout: 5000 });
  19  | 
  20  |         const hasSend = await page.locator('button:has-text("Send"), button:has-text("➤"), svg.lucide-send').first().isVisible().catch(() => false);
  21  |         expect(hasSend).toBeTruthy();
  22  |     });
  23  | 
  24  |     test('should type a message and send it', async ({ page }) => {
  25  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
  26  |         await page.waitForTimeout(2000);
  27  | 
  28  |         const textarea = page.locator('textarea.odysseus-input-field, textarea, input[type="text"]').first();
  29  |         await textarea.fill('Hello AsimNexus');
  30  |         await page.waitForTimeout(500);
  31  | 
  32  |         const sendBtn = page.locator('button.odysseus-send-btn, button:has-text("Send"), button:has-text("➤")').first();
  33  |         if (await sendBtn.isVisible().catch(() => false)) {
  34  |             await sendBtn.click();
  35  |         } else {
  36  |             await textarea.press('Enter');
  37  |         }
  38  |         await page.waitForTimeout(2000);
  39  | 
  40  |         const bodyText = await page.locator('body').textContent();
  41  |         expect(bodyText.length).toBeGreaterThan(50);
  42  |     });
  43  | 
  44  |     test('should show mode selector dropdown', async ({ page }) => {
  45  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
  46  |         await page.waitForTimeout(2000);
  47  | 
  48  |         const modeOptions = ['Auto', 'Guide', 'Plan', 'Observe'];
  49  |         let foundMode = false;
  50  |         for (const mode of modeOptions) {
  51  |             const visible = await page.locator(`text=${mode}`).first().isVisible().catch(() => false);
  52  |             if (visible) { foundMode = true; break; }
  53  |         }
  54  | 
  55  |         const modeBtn = page.locator('button.odysseus-mode-btn, button:has-text("Auto"), button:has-text("Guide")').first();
  56  |         const hasModeBtn = await modeBtn.isVisible().catch(() => false);
  57  |         expect(foundMode || hasModeBtn).toBeTruthy();
  58  |     });
  59  | 
  60  |     test('should render quick action buttons in chat', async ({ page }) => {
  61  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
  62  |         await page.waitForTimeout(2000);
  63  | 
  64  |         const quickActions = ['Health', 'Work', 'Mesh', 'Hire', 'Code'];
  65  |         let foundActions = 0;
  66  |         for (const action of quickActions) {
  67  |             const visible = await page.locator(`text=${action}`).first().isVisible().catch(() => false);
  68  |             if (visible) foundActions++;
  69  |         }
  70  |         console.log(`  Quick actions visible: ${foundActions}/${quickActions.length}`);
  71  |     });
  72  | 
  73  |     test('should navigate to /chat and render UniversalChat', async ({ page }) => {
  74  |         await page.goto('/chat', { waitUntil: 'domcontentloaded' });
  75  |         await page.waitForTimeout(2000);
  76  | 
  77  |         const bodyText = await page.locator('body').textContent();
  78  |         expect(bodyText.length).toBeGreaterThan(50);
  79  | 
  80  |         const inputVisible = await page.locator('textarea, input[type="text"]').first().isVisible().catch(() => false);
  81  |         expect(inputVisible).toBeTruthy();
  82  |     });
  83  | 
  84  |     test('should not show React crash overlay on chat pages', async ({ page }) => {
  85  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
  86  |         await page.waitForTimeout(1000);
  87  |         let crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
  88  |         expect(crashOverlay).toBeFalsy();
  89  | 
  90  |         await page.goto('/chat', { waitUntil: 'domcontentloaded' });
  91  |         await page.waitForTimeout(1000);
  92  |         crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
  93  |         expect(crashOverlay).toBeFalsy();
  94  |     });
  95  | 
  96  |     test('should show empty chat state', async ({ page }) => {
  97  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
  98  |         await page.waitForTimeout(2000);
  99  | 
  100 |         const bodyText = await page.locator('body').textContent();
  101 |         const hasEmptyState = bodyText.includes('Ask Asim') || bodyText.includes('Type your message');
  102 |         expect(hasEmptyState).toBeTruthy();
  103 |     });
  104 | });
  105 | 
```