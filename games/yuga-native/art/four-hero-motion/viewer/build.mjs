import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';
import { copyFileSync, existsSync } from 'node:fs';
const directory = fileURLToPath(new URL('.', import.meta.url));
const shared = new URL('../../../../yuga/client/environment-light.ts', import.meta.url);
if (existsSync(shared)) copyFileSync(shared, new URL('./src/environment-light.ts', import.meta.url));
await build({absWorkingDir: directory, entryPoints: ['src/app.js'], outfile: 'app.min.js', bundle: true,
    format: 'iife', target: ['es2022'], minify: true, legalComments: 'eof',
    banner: { js: '/*! YUGA rig inspector includes PlayCanvas 2.23.3, MIT. Full text in notices/PlayCanvas-MIT.txt. */' }});
