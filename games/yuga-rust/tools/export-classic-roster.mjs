// Execute the actual typed definitions, including ability() calls and object spreads.
import { tsImport } from 'tsx/esm/api';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const shared = new URL('../../yuga/shared/', import.meta.url);
const target = new URL('../assets/classic-roster.json', import.meta.url);
const files = ['heroes.ts', 'map.ts', 'simulation.ts'];
const modules = await Promise.all(files.map(name=>tsImport(new URL(name, shared).href, import.meta.url)));
const sourceHashes = Object.fromEntries(await Promise.all(files.map(async name=>[name,
  createHash('sha256').update(await readFile(new URL(name,shared))).digest('hex')])));
const heroes = modules[0].HEROES;
if (heroes.length !== new Set(heroes.map(h=>h.id)).size || !heroes.every(h=>h.abilities.length===3))
  throw new Error('Expected unique heroes with three classic ability slots');
const content = JSON.stringify({schema:1, sourceHashes, heroes, solids:modules[1].SOLIDS,
  rules:modules[2].ARENA_RULES},null,2)+'\n';
if (process.argv.length === 2) await writeFile(target,content);
else if (process.argv.length===3 && process.argv[2]==='--check') {
  if(await readFile(target,'utf8')!==content) throw new Error('Stale classic roster. Run the exporter, then repeat parity tests.');
} else throw new Error('Usage: node export-classic-roster.mjs [--check]');
console.log('Validated '+heroes.length+' heroes and '+heroes.length*3+' abilities.');
