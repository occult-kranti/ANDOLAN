import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { existsSync, readFileSync } from 'node:fs';

const trackFile = new URL('./reference-track/track.json', import.meta.url);
const configuredTrack: unknown = process.env.YUGA_LAB_TRACK ?? (existsSync(trackFile) ? JSON.parse(readFileSync(trackFile, 'utf8')).id : 'all');
if (!['all', 'lane', 'control'].includes(String(configuredTrack))) throw new Error('Unknown YUGA lab track');
const track = String(configuredTrack);
const output = process.env.YUGA_LAB_FLAVOR_OUTPUT === '1' && track !== 'all' ? `yuga-${track}-lab` : 'yuga-lab';

export default defineConfig({
  root: 'games/yuga/reference-client',
  base: './',
  define: { 'import.meta.env.VITE_YUGA_LAB_TRACK': JSON.stringify(track) },
  plugins: [viteSingleFile({ useRecommendedBuildConfig: false })],
  experimental: { renderBuiltUrl(filename, context) {
    if (context.hostType === 'js' && /\.glb$/i.test(filename)) return { runtime: `new URL(${JSON.stringify(filename)}, document.baseURI).href` };
  } },
  server: { host: '0.0.0.0', port: 5181, strictPort: true },
  build: {
    outDir: `../../../dist/${output}`, emptyOutDir: true, target: 'es2022',
    assetsInlineLimit: (filename) => !/\.glb$/i.test(filename), chunkSizeWarningLimit: 5000,
  },
});
