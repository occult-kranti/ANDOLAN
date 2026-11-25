// Compare the native room and packaged Wasm worker through their real line protocol.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import path from 'node:path';

const [native, folder, reportFile] = process.argv.slice(2);
if (!native || !folder || !reportFile) throw Error('Usage: node test_5v5_parity.mjs native-room extracted-folder report.json');
const root = path.resolve(folder), wasm = path.join(root, 'yuga-rust.wasm');
const nativePath = path.resolve(native);
function start(program, args) {
  const child = spawn(program, args, { stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '';
  child.stderr.on('data', chunk => { stderr = (stderr + chunk).slice(-3000); });
  const lines = createInterface({ input: child.stdout })[Symbol.asyncIterator]();
  return {
    child,
    async send(value) {
      child.stdin.write(JSON.stringify(value) + '\n');
      let timer;
      try {
        const line = await Promise.race([
          lines.next(),
          new Promise((_, reject) => { timer = setTimeout(() => reject(Error('Authority timed out: ' + stderr)), 15000); }),
        ]);
        if (line.done) throw Error('Authority exited: ' + stderr);
        return JSON.parse(line.value);
      } finally { clearTimeout(timer); }
    },
  };
}
const peers = [start(nativePath, []), start(process.execPath, [path.join(root, 'room-wasm.mjs'), wasm])];
let numericFields = 0, maxError = 0, comparedFrames = 0, acceptedCasts = 0, lowestHp = 300;
function compare(a, b, at = 'frame') {
  if (typeof a === 'number' && typeof b === 'number') {
    const error = Math.abs(a - b);
    maxError = Math.max(maxError, error); numericFields++;
    assert.ok(error <= 0.0001, `${at}: ${a} differs from ${b}`);
  } else if (Array.isArray(a)) {
    assert.ok(Array.isArray(b), at); assert.equal(a.length, b.length, at);
    a.forEach((v, i) => compare(v, b[i], at + '[' + i + ']'));
  } else if (a && typeof a === 'object') {
    assert.ok(b && typeof b === 'object' && !Array.isArray(b), at);
    assert.deepEqual(Object.keys(a).sort(), Object.keys(b).sort(), at);
    for (const k of Object.keys(a)) compare(a[k], b[k], at + '.' + k);
  } else assert.deepEqual(a, b, at);
}
async function exchange(command) {
  const [a, b] = await Promise.all(peers.map(p => p.send(command)));
  compare(a, b);
  assert.equal(a.states.length, 10);
  for (let i = 0; i < 10; i++) {
    const s = a.states[i];
    assert.equal(s.seat, i); assert.equal(s.army.units.length, 0);
    assert.equal(s.ruleset, 'hero_skirmish'); assert.equal(s.roster.length, 9);
    lowestHp = Math.min(lowestHp, s.actor.hp);
  }
  acceptedCasts += a.accepted.filter(Boolean).length;
  comparedFrames++;
  return a;
}
try {
  let packet = await exchange({ heroes: Array.from({ length: 10 }, (_, i) => i % 2 ? 'rama' : 'hanuman') });
  for (let frame = 0; frame < 90; frame++) {
    const players = packet.states.map((s, i) => {
      const sign = i % 2 ? -1 : 1;
      const target = packet.states[i ^ 1].actor.pos;
      const dx = target[0] - s.actor.pos[0], dz = target[1] - s.actor.pos[1];
      const length = Math.hypot(dx, dz) || 1;
      const aim = [dx / length, dz / length];
      return { motion: { movement: [0, frame < 32 ? sign * 0.5 : 0], aim },
        casts: frame >= 24 && frame % 2 === 0 ? [{ slot: 0, ground: target, aim }] : [] };
    });
    packet = await exchange({ players, ticks: 4 });
  }
  assert.ok(acceptedCasts > 0, 'ordinary cast inputs were accepted');
  assert.ok(lowestHp < 300, 'ordinary attacks damaged a hero');
  const report = { result: 'pass', scope: 'native room versus packaged Wasm authority, ten seats, no rendered clients',
    compared_frames: comparedFrames, compared_seat_snapshots: comparedFrames * 10,
    numeric_fields: numericFields, max_absolute_error: maxError, accepted_casts: acceptedCasts, lowest_hero_hp: lowestHp,
    native_sha256: createHash('sha256').update(await readFile(nativePath)).digest('hex'),
    wasm_sha256: createHash('sha256').update(await readFile(wasm)).digest('hex') };
  await writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  for (const p of peers) { p.child.stdin.end(); p.child.kill(); }
}
