/**
 * Playwright E2E Configuration — AsimNexus
 * Tests cover: Auth → Dashboard → Clones → Life → Mesh/Offline → Navigation
 */
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
    testDir: './e2e',
    fullyParallel: false,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : 1,
    reporter: [
        ['html', { outputFolder: 'e2e-report' }],
        ['list'],
    ],

    use: {
        baseURL: process.env.BASE_URL || 'http://localhost:3000',
        trace: 'on-first-retry',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        headless: true,
        viewport: { width: 1280, height: 800 },
        ignoreHTTPSErrors: true,
    },

    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] },
        },
        {
            name: 'firefox',
            use: { ...devices['Desktop Firefox'] },
        },
        {
            name: 'webkit',
            use: { ...devices['Desktop Safari'] },
        },
    ],

    webServer: {
        command: 'npm start',
        port: 3000,
        timeout: 120 * 1000,
        reuseExistingServer: true,
        cwd: './',
    },
});
