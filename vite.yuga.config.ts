import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
export default defineConfig({
  root: 'games/yuga', base: './', plugins: [viteSingleFile({ useRecommendedBuildConfig: false })],
  // The script is inlined into index.html, so GLBs resolve from the document,
  // not the emitted JS chunk's former assets/ directory.
  experimental: { renderBuiltUrl(filename, context) {
    if (context.hostType === 'js' && /\.glb$/i.test(filename)) return { runtime: `new URL(${JSON.stringify(filename)}, document.baseURI).href` };
  } },
  server: { host: '0.0.0.0', port: 5180, strictPort: true, proxy: { '/ws': { target: 'ws://127.0.0.1:3005', ws: true }, '/health': 'http://127.0.0.1:3005' } },
  build: { outDir: '../../dist/yuga', emptyOutDir: true, target: 'es2022', assetsInlineLimit: (path) => !/\.glb$/i.test(path), chunkSizeWarningLimit: 5000 },
});
