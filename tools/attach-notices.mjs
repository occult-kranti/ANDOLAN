import { readFile, writeFile } from 'node:fs/promises';

const target = process.argv[2];
if (!['client', 'standalone'].includes(target)) throw new Error('Choose client or standalone');
const notices = await readFile(new URL('../THIRD_PARTY_NOTICES.md', import.meta.url), 'utf8');
const output = new URL(`../dist/${target}/`, import.meta.url);
if (target === 'standalone') {
  const path = new URL('index.html', output);
  const html = await readFile(path, 'utf8');
  if (!html.includes('</body>')) throw new Error('Missing HTML body');
  const embedded = notices.replace(/<\/script/gi, '<\\/script');
  await writeFile(path, html.replace('</body>', `<script type="text/plain" id="andolan-third-party-notices">${embedded}</script></body>`));
} else {
  await writeFile(new URL('THIRD_PARTY_NOTICES.txt', output), notices);
}
