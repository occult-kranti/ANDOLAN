// Cost-based CI groups. Every current/future *.e2e.ts file belongs to exactly
// one group; each runner keeps the ordinary Playwright config and assertions.
import assert from 'node:assert/strict';
import { readdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const tests = 'games/yuga/tests';
async function discover(directory) {
  const files = [];
  for (const entry of await readdir(path.join(root, directory), { withFileTypes: true })) {
    const filename = `${directory}/${entry.name}`;
    if (entry.isDirectory()) files.push(...await discover(filename));
    else if (entry.isFile() && entry.name.endsWith('.e2e.ts')) files.push(filename);
  }
  return files.sort();
}
const files = await discover(tests);
const special = { 'hero-assets': `${tests}/hero-assets.e2e.ts`, arena: `${tests}/arena.e2e.ts` };
for (const filename of Object.values(special)) assert.ok(files.includes(filename), `Required browser group file is missing: ${filename}`);
const groups = {
  'hero-assets': [special['hero-assets']],
  arena: [special.arena],
  remaining: files.filter(filename => !Object.values(special).includes(filename)),
};
const partition = Object.values(groups).flat();
assert.equal(new Set(partition).size, partition.length, 'Browser groups overlap.');
assert.deepEqual([...partition].sort(), files, 'Browser groups omit a discovered test file.');
for (const [name, group] of Object.entries(groups)) assert.ok(group.length, `Browser group is empty: ${name}`);

const [group, ...args] = process.argv.slice(2);
if (group === '--verify') {
  console.log(JSON.stringify({ files, groups, disjoint: true, exhaustive: true }, null, 2));
} else {
  assert.ok(Object.hasOwn(groups, group ?? ''), 'Choose hero-assets, arena, remaining, or --verify.');
  // Playwright treats positional filters as regexes: escape and anchor each
  // exact file, so e.g. a future nested arena.e2e.ts stays in remaining only.
  const filters = groups[group].map(filename => `${filename.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`);
  const result = spawnSync(process.execPath, [path.join(root, 'node_modules/@playwright/test/cli.js'), 'test', '--config', 'playwright.yuga.config.ts', ...filters, ...args], { cwd: root, env: process.env, stdio: 'inherit' });
  if (result.error) throw result.error;
  process.exitCode = result.status ?? 1;
}
