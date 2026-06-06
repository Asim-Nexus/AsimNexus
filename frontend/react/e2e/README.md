# E2E Tests — ASIMNEXUS Frontend

## Overview

46 Playwright tests across 5 spec files covering auth, navigation, EconomyHub, LifeHub, and NetworkHub.

## Quick Start

```bash
cd frontend/react
npm install                    # Install deps (if not done)
npx playwright install         # Install browser binaries (first time)
npm run test:e2e               # Run all tests (Chromium)
npm run test:e2e:ui            # Run with Playwright UI mode
npm run test:e2e:report        # View HTML report
```

## Test Structure

| Spec File | Tests | Coverage |
|-----------|-------|----------|
| [`auth.spec.js`](auth.spec.js) | 5 | Login page, nav rail, chat interface, dashboard, settings |
| [`navigation.spec.js`](navigation.spec.js) | 23 | 12 core routes + 9 legacy redirects + 404 handling |
| [`clones.spec.js`](clones.spec.js) | 3 | EconomyHub render, legacy /clones route, tab navigation |
| [`life.spec.js`](life.spec.js) | 4 | LifeHub render, life stages, lifecycle metrics, crash overlay |
| [`mesh-offline.spec.js`](mesh-offline.spec.js) | 5 | NetworkHub render, 5 tabs, MeshSelector, OfflineStatus, legacy /mesh |

## Auth Contract (⚠️ Critical)

The frontend reads authentication state from **`localStorage`** using specific key names defined in [`unified_api.js`](../../src/api/unified_api.js):

| Key | Value | Source |
|-----|-------|--------|
| `asim_token` | JWT token string | [`getStoredToken()`](../../src/api/unified_api.js#L65) |
| `asim_user` | JSON-serialized user object | [`getStoredUser()`](../../src/api/unified_api.js#L66) |

All tests use [`page.addInitScript()`](https://playwright.dev/docs/api/class-page#page-add-init-script) to inject these **before** any page JS runs:

```js
await page.addInitScript(() => {
    localStorage.setItem('asim_token', 'e2e-test-token');
    localStorage.setItem('asim_user', JSON.stringify({
        username: 'testuser_e2e',
        email: 'testuser_e2e@asimnexus.test',
        display_name: 'Test User'
    }));
});
```

> **⚠️ DO NOT change these key names** without updating both [`App.js`](../../src/App.js#L324) and [`unified_api.js`](../../src/api/unified_api.js#L65). Tests will silently render the login page instead of the authenticated app.

## Route Map

The app uses React Router with routes defined in [`App.js`](../../src/App.js).

### Core Routes (12)

| Route | Component | Hub |
|-------|-----------|-----|
| `/` or `/chat` | UnifiedChat | Chat |
| `/dashboard` | Dashboard | Dashboard |
| `/os` | OSHub | Personal OS |
| `/marketplace` | EconomyHub | Economy |
| `/ai` | AI Hub | AI |
| `/identity` | Identity | Identity |
| `/network` | NetworkHub | Network |
| `/life` | LifeHub | Life |
| `/settings` | Settings | Settings |
| `/personal` | → OSHub | (redirect) |

### Legacy Redirects (9)

`/personal`, `/world-os`, `/os-panel`, `/mcp`, `/contracts`, `/clones`, `/memory`, `/local-llm`, `/mesh` — all redirect to their modern equivalents.

## Helper: [`mockAllAPIs()`](helpers.js)

Intercepts all backend API calls with realistic mock data so tests run without a backend server. Currently mocks:

- `POST /auth/login` → token response
- `GET /api/personal/status` → user status
- `GET /personal/clones` → clone list
- `GET /api/universe/*/lifecycle` → lifecycle metrics
- `GET /api/mesh/status` → mesh status
- `GET /api/mesh/peers` → peer list
- `GET /api/sync/status` → sync status
- `GET /api/mesh/offline/capabilities` → offline capabilities

## Config

Tests run via [`playwright.config.js`](../playwright.config.js). Currently configured for Chromium only. To enable Firefox/WebKit:

```js
projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
]
```

## CI Integration

```bash
# Run and generate report
npx playwright test --reporter=html
npx playwright show-report
```
