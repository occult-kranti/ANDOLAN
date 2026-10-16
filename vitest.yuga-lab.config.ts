import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: { include: ['games/yuga/reference-tests/**/*.test.ts'], testTimeout: 20000, maxWorkers: 2 },
});
