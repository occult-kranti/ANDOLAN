import { existsSync } from 'node:fs';
import { defineConfig } from '@playwright/test';

const chromium = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/usr/bin/chromium';

export default defineConfig({
  testDir: './games/yuga/tests',
  testMatch: '**/*.e2e.ts',
  fullyParallel: false,
  workers: 1,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  outputDir: 'test-results/yuga',
  reporter: process.env.CI
    ? [['list'], ['github'], ['html', { outputFolder: 'playwright-report/yuga', open: 'never' }]]
    : [['list'], ['html', { outputFolder: 'playwright-report/yuga', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5180',
    viewport: { width: 960, height: 640 },
    actionTimeout: 20_000,
    screenshot: 'only-on-failure',
    trace: { mode: 'retain-on-failure', screenshots: false },
    launchOptions: {
      executablePath: existsSync(chromium) ? chromium : undefined,
      args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
    },
  },
  webServer: {
    command: 'npm run yuga:dev',
    url: 'http://127.0.0.1:5180',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
