import tseslint from 'typescript-eslint';
export default tseslint.config(
  { ignores: ['node_modules/**', '.npm-cache/**', 'dist/**', 'release/**', 'test-results/**', '.data/**', 'playwright-report/**'] },
  ...tseslint.configs.recommended,
  { rules: { '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }] } }
);
