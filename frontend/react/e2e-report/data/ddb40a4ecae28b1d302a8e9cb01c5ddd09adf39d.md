# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.js >> Route Navigation — All Routes Render >> should render Legacy: /memory → AI (/memory) without crash
- Location: e2e\navigation.spec.js:52:9

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/memory
Call log:
  - navigating to "http://localhost:3000/memory", waiting until "domcontentloaded"

```

# Test source

```ts
  1   | /**
  2   |  * E2E: Route Navigation — All Routes Render Without Crash
  3   |  * Validates: every registered route, legacy redirects, catch-all
  4   |  */
  5   | const { test, expect } = require('@playwright/test');
  6   | const { mockAllAPIs } = require('./helpers');
  7   | 
  8   | const ROUTES = [
  9   |     // Core Routes
  10  |     { path: '/', label: 'Chat' },
  11  |     { path: '/chat', label: 'Chat (alias)' },
  12  |     { path: '/dashboard', label: 'Dashboard' },
  13  | 
  14  |     // Consolidated Hubs
  15  |     { path: '/os', label: 'OS Hub' },
  16  |     { path: '/marketplace', label: 'Market/Economy Hub' },
  17  |     { path: '/ai', label: 'AI Hub' },
  18  |     { path: '/identity', label: 'Identity Hub' },
  19  |     { path: '/network', label: 'Network Hub' },
  20  |     { path: '/life', label: 'Life Hub' },
  21  | 
  22  |     // Settings
  23  |     { path: '/settings', label: 'Settings' },
  24  | 
  25  |     // Legacy Redirects (should map to hubs without error)
  26  |     { path: '/personal', label: 'Legacy: /personal → OS' },
  27  |     { path: '/world-os', label: 'Legacy: /world-os → OS' },
  28  |     { path: '/os-panel', label: 'Legacy: /os-panel → OS' },
  29  |     { path: '/mcp', label: 'Legacy: /mcp → Economy' },
  30  |     { path: '/contracts', label: 'Legacy: /contracts → Economy' },
  31  |     { path: '/clones', label: 'Legacy: /clones → Economy' },
  32  |     { path: '/memory', label: 'Legacy: /memory → AI' },
  33  |     { path: '/local-llm', label: 'Legacy: /local-llm → AI' },
  34  |     { path: '/mesh', label: 'Legacy: /mesh → Network' },
  35  | ];
  36  | 
  37  | test.describe('Route Navigation — All Routes Render', () => {
  38  |     test.beforeEach(async ({ page }) => {
  39  |         // Inject auth before each navigation
  40  |         await page.addInitScript(() => {
  41  |             localStorage.setItem('token', 'e2e-test-token');
  42  |             localStorage.setItem('user', JSON.stringify({
  43  |                 username: 'testuser_e2e',
  44  |                 email: 'testuser_e2e@asimnexus.test',
  45  |                 display_name: 'Test User'
  46  |             }));
  47  |         });
  48  |         await mockAllAPIs(page);
  49  |     });
  50  | 
  51  |     for (const route of ROUTES) {
  52  |         test(`should render ${route.label} (${route.path}) without crash`, async ({ page }) => {
> 53  |             await page.goto(route.path, { waitUntil: 'domcontentloaded' });
      |                        ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/memory
  54  |             await page.waitForTimeout(1000);
  55  | 
  56  |             // Check page rendered
  57  |             const bodyText = await page.locator('body').textContent();
  58  |             expect(bodyText.length).toBeGreaterThan(50);
  59  | 
  60  |             // Verify no React crash overlay
  61  |             const crashOverlay = await page.locator('iframe[title="React error overlay"]').isVisible().catch(() => false);
  62  |             expect(crashOverlay).toBeFalsy();
  63  | 
  64  |             // Check for white screen (empty body)
  65  |             const appRoot = await page.locator('#root').textContent().catch(() => '');
  66  |             expect(appRoot.length).toBeGreaterThan(0);
  67  |         });
  68  |     }
  69  | });
  70  | 
  71  | test.describe('Route Navigation — Legacy Redirects', () => {
  72  |     test.beforeEach(async ({ page }) => {
  73  |         await page.addInitScript(() => {
  74  |             localStorage.setItem('token', 'e2e-test-token');
  75  |             localStorage.setItem('user', JSON.stringify({
  76  |                 username: 'testuser_e2e',
  77  |                 email: 'testuser_e2e@asimnexus.test',
  78  |                 display_name: 'Test User'
  79  |             }));
  80  |         });
  81  |         await mockAllAPIs(page);
  82  |     });
  83  | 
  84  |     const LEGACY_REDIRECTS = [
  85  |         '/personal', '/world-os', '/os-panel',
  86  |         '/mcp', '/contracts', '/clones',
  87  |         '/memory', '/local-llm', '/mesh',
  88  |     ];
  89  | 
  90  |     for (const path of LEGACY_REDIRECTS) {
  91  |         test(`legacy ${path} should redirect without error`, async ({ page }) => {
  92  |             await page.goto(path, { waitUntil: 'domcontentloaded' });
  93  |             await page.waitForTimeout(1000);
  94  | 
  95  |             const bodyText = await page.locator('body').textContent();
  96  |             expect(bodyText.length).toBeGreaterThan(50);
  97  |         });
  98  |     }
  99  | });
  100 | 
  101 | test.describe('Route Integrity — 404 Handling', () => {
  102 |     test.beforeEach(async ({ page }) => {
  103 |         await page.addInitScript(() => {
  104 |             localStorage.setItem('token', 'e2e-test-token');
  105 |             localStorage.setItem('user', JSON.stringify({
  106 |                 username: 'testuser_e2e',
  107 |                 email: 'testuser_e2e@asimnexus.test',
  108 |                 display_name: 'Test User'
  109 |             }));
  110 |         });
  111 |         await mockAllAPIs(page);
  112 |     });
  113 | 
  114 |     test('unknown route should fallback to chat (catch-all)', async ({ page }) => {
  115 |         await page.goto('/this-route-does-not-exist-xyz', { waitUntil: 'domcontentloaded' });
  116 |         await page.waitForTimeout(1000);
  117 | 
  118 |         // Catch-all should redirect to chat (/)
  119 |         const bodyText = await page.locator('body').textContent();
  120 |         expect(bodyText.length).toBeGreaterThan(50);
  121 |     });
  122 | });
  123 | 
```