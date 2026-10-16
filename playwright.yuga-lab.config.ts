import { existsSync } from 'node:fs';
import { defineConfig } from '@playwright/test';

const chromium = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium';

export default defineConfig({
  testDir: './games/yuga/reference-tests', testMatch: '**/*.e2e.ts',
  fullyParallel: false, workers: 1, timeout: 120_000,
  expect: { timeout: 15_000 }, outputDir: 'test-results/yuga-lab',
  reporter: process.env.CI
    ? [['list'], ['github'], ['html', { outputFolder: 'playwright-report/yuga-lab', open: 'never' }]]
    : [['list'], ['html', { outputFolder: 'playwright-report/yuga-lab', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5181', viewport: { width: 960, height: 640 },
    actionTimeout: 20_000, screenshot: 'only-on-failure',
    trace: { mode: 'retain-on-failure', screenshots: false },
    launchOptions: { executablePath: existsSync(chromium) ? chromium : undefined,
      args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'] },
  },
  webServer: {
    // Exercise the shared combined client; focused builds have a separate production smoke.
    env: { YUGA_LAB_TRACK: 'all' },
    command: 'npm run yuga:lab:dev', url: 'http://127.0.0.1:5181',
    reuseExistingServer: !process.env.CI, timeout: 120_000,
  },
});
