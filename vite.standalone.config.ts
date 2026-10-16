import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
export default defineConfig({
  root: 'apps/client',
  base: './',
  plugins: [viteSingleFile()],
  build: { outDir: '../../dist/standalone', emptyOutDir: true, target: 'es2022', chunkSizeWarningLimit: 3000 },
});
