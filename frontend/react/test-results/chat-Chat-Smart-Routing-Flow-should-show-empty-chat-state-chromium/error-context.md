# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.js >> Chat / Smart Routing Flow >> should show empty chat state
- Location: e2e\chat.spec.js:96:5

# Error details

```
Error: expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- iframe [ref=e3]:
  - generic [ref=f1e2]:
    - generic [ref=f1e3]: "Compiled with problems:"
    - button "Dismiss" [ref=f1e4] [cursor=pointer]: ×
    - generic [ref=f1e5]:
      - generic [ref=f1e6]:
        - generic [ref=f1e7] [cursor=pointer]: ERROR in ./src/services/websocket.js
        - generic [ref=f1e8]:
          - text: "Module build failed (from ./node_modules/babel-loader/lib/index.js): SyntaxError: C:\\AsimNexus\\frontend\\react\\src\\services\\websocket.js: Identifier 'wsService' has already been declared. (13:13)"
          - generic [ref=f1e9]:
            - text: 11 | 12 | // Re-export the singleton instance
            - generic [ref=f1e10]: ">"
            - text: 13 | export const wsService = wsService; |
            - generic [ref=f1e11]: ^
            - text: 14 | export default wsService; 15 |
          - text: at constructor (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:365:19) at FlowParserMixin.raise (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:6599:19) at FlowScopeHandler.checkRedeclarationInScope (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:1619:19) at FlowScopeHandler.declareName (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:1585:12) at FlowScopeHandler.declareName (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:1686:11) at FlowParserMixin.declareNameFromIdentifier (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:7567:16) at FlowParserMixin.checkIdentifier (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:7563:12) at FlowParserMixin.checkLVal (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:7500:12) at FlowParserMixin.parseVarId (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13412:10) at FlowParserMixin.parseVarId (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:3474:11) at FlowParserMixin.parseVar (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13383:12) at FlowParserMixin.parseVarStatement (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13230:10) at FlowParserMixin.parseStatementContent (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12851:23) at FlowParserMixin.parseStatementLike (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12767:17) at FlowParserMixin.parseStatementLike (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:2918:24) at FlowParserMixin.parseStatementListItem (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12747:17) at FlowParserMixin.parseExportDeclaration (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13934:17) at FlowParserMixin.parseExportDeclaration (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:3120:20) at FlowParserMixin.maybeParseExportDeclaration (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13893:31) at FlowParserMixin.parseExport (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13812:29) at FlowParserMixin.parseStatementContent (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12878:27) at FlowParserMixin.parseStatementLike (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12767:17) at FlowParserMixin.parseStatementLike (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:2918:24) at FlowParserMixin.parseModuleItem (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12744:17) at FlowParserMixin.parseBlockOrModuleBlockBody (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13316:36) at FlowParserMixin.parseBlockBody (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:13309:10) at FlowParserMixin.parseProgram (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12622:10) at FlowParserMixin.parseTopLevel (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:12612:25) at FlowParserMixin.parseTopLevel (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:3685:28) at FlowParserMixin.parse (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:14488:25) at parse (C:\AsimNexus\frontend\react\node_modules\@babel\parser\lib\index.js:14522:38) at parser (C:\AsimNexus\frontend\react\node_modules\@babel\core\lib\parser\index.js:41:34) at parser.next (<anonymous>) at normalizeFile (C:\AsimNexus\frontend\react\node_modules\@babel\core\lib\transformation\normalize-file.js:64:37) at normalizeFile.next (<anonymous>) at run (C:\AsimNexus\frontend\react\node_modules\@babel\core\lib\transformation\index.js:22:50) at run.next (<anonymous>) at transform (C:\AsimNexus\frontend\react\node_modules\@babel\core\lib\transform.js:22:33) at transform.next (<anonymous>) at step (C:\AsimNexus\frontend\react\node_modules\gensync\index.js:261:32) at C:\AsimNexus\frontend\react\node_modules\gensync\index.js:273:13 at async.call.result.err.err (C:\AsimNexus\frontend\react\node_modules\gensync\index.js:223:11)
      - generic [ref=f1e12]:
        - generic [ref=f1e13]: ERROR
        - generic [ref=f1e14]:
          - text: "[eslint] src\\components\\odysseus\\AgentChat.jsx Line 229:9: Definition for rule 'react-hooks/exhaustive-deps' was not found"
          - generic [ref=f1e15]: react-hooks/exhaustive-deps
          - text: "src\\services\\websocket.js Line 13:13: Parsing error: Identifier 'wsService' has already been declared. (13:13) Search for the"
          - generic [ref=f1e16]: keywords
          - text: to learn more about each error.
```

# Test source

```ts
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
  14  |         await page.goto('/', { waitUntil: 'domcontentloaded' });
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
> 102 |         expect(hasEmptyState).toBeTruthy();
      |                               ^ Error: expect(received).toBeTruthy()
  103 |     });
  104 | });
  105 | 
```