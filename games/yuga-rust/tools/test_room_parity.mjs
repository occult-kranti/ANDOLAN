// Send identical NDJSON frames to the native and WebAssembly Rust room authorities.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';

const here = path.dirname(fileURLToPath(import.meta.url));
const crate = path.resolve(here, '..');
const { values } = parseArgs({ options: {
  binary: { type: 'string', default: path.join(crate, 'target/release', process.platform === 'win32' ? 'room.exe' : 'room') },
  wasm: { type: 'string', default: path.join(crate, 'target/wasm32-unknown-unknown/release/yuga_rust.wasm') },
  report: { type: 'string' },
} });
const worker = path.join(here, 'room-wasm.mjs');
const digest = async file => createHash('sha256').update(await readFile(file)).digest('hex');
const retreat = { motion: { movement: [-0.5, 0.5], aim: [0, -1] } };
const aimAt = (slot, z) => ({ slot, aim: [0, Math.sign(z)], ground: [0, z] });
const frames = [
  { players: [{}, {}], ticks: 1 },
  { players: [{ motion: { movement: [0.25, 0.5], aim: [0, 1] } }, retreat], ticks: 3 },
  { players: [{ casts: [aimAt(0, 5)] }, { casts: [aimAt(0, -5)] }], ticks: 2 },
  { players: [{ casts: [aimAt(0, 5), aimAt(99, 5)] }, { reload: true }], ticks: 4 },
  ...Array.from({ length: 7 }, () => ({ players: [{}, {}], ticks: 4 })),
  { players: [{ casts: [aimAt(1, 5)] }, { casts: [aimAt(2, -5)] }], ticks: 2 },
  ...Array.from({ length: 8 }, () => ({ players: [{}, {}], ticks: 4 })),
  { players: [{ casts: [aimAt(3, 5)] }, { casts: [aimAt(4, -5)] }], ticks: 1 },
  { players: [{ motion: { aim: [1, 0] } }, { reload: true }], ticks: 4 },
];
const commands = [{ cmd: path.resolve(values.binary), args: [] }, { cmd: process.execPath, args: [worker, path.resolve(values.wasm)] }];
function invoke({cmd, args}, trace) {
  return spawnSync(cmd, args, { encoding: 'utf8', timeout: 15000, maxBuffer: 32 * 1024 * 1024,
    input: trace.map(v => JSON.stringify(v)).join('\n') + '\n' });
}
const counters = { values_compared: 0, numeric_fields_compared: 0, max_absolute_numeric_error: 0 };
function compare(a, b, field = '$') {
  counters.values_compared++;
  if (typeof a === 'number') {
    assert.ok(typeof b === 'number' && Number.isFinite(a) && Number.isFinite(b), field);
    counters.numeric_fields_compared++;
    const err = Math.abs(a-b);
    counters.max_absolute_numeric_error = Math.max(counters.max_absolute_numeric_error, err);
    if (Number.isInteger(a) && Number.isInteger(b)) assert.equal(a, b, field);
    else assert.ok(err <= 0.0001, field + ': native=' + a + ' wasm=' + b);
  } else if (a !== null && typeof a === 'object') {
    assert.ok(b !== null && typeof b === 'object' && Array.isArray(a) === Array.isArray(b), field);
    assert.deepEqual(Object.keys(a).sort(), Object.keys(b).sort(), field);
    for (const k of Object.keys(a)) compare(a[k], b[k], field + '.' + k);
  } else assert.equal(a, b, field);
}
const results = [];
for (const [sun, moon] of [['hanuman', 'rama'], ['rama', 'hanuman']]) {
  const trace = [{ sun, moon }, ...frames];
  const [native, portable] = commands.map(c => {
    const result = invoke(c, trace);
    assert.equal(result.status, 0, result.stderr || result.error?.message);
    return result.stdout.trimEnd().split('\n').map(line => JSON.parse(line));
  });
  assert.equal(native.length, trace.length);
  assert.equal(portable.length, trace.length);
  const accepts = new Set();
  native.forEach((frame, i) => {
    compare(frame, portable[i], sun + '/frame[' + i + ']');
    for (const accepted of frame.accepted) accepts.add(accepted);
  });
  assert.ok(accepts.has(true) && accepts.has(false), 'cast success and explicit rejection traced');
  results.push({ sun, moon, frames_compared: native.length, ticks_advanced: native.at(-1).states[0].tick - native[0].states[0].tick });
}
const roster = { sun: 'hanuman', moon: 'rama' };
const invalid = [
  [{ sun: 'absent', moon: 'rama' }],
  [roster, { players: [{},{}], ticks: 0 }],
  [roster, { players: [{},{}], ticks: 5 }],
  [roster, { players: [{}, { casts: Array(5).fill(aimAt(0,-5)) }], ticks: 2 }],
  [roster, { players: [{}, { motion: { movement: [0, 'wrong'] } }], ticks: 2 }],
];
for (const trace of invalid) {
  for (const c of commands) {
    const proc = invoke(c, trace);
    assert.ok(Number.isInteger(proc.status) && proc.status !== 0, 'invalid trace rejected');
    assert.equal(proc.stdout.split('\n').filter(Boolean).length, trace.length - 1, 'no invalid frame published');
  }
}
const evidence = { scope: 'Full decoded authority snapshots and action receipts from the same ordered trace; integer fields exact, float tolerance 0.0001.',
  node: process.version, rosters: results, ...counters, invalid_traces_rejected_by_both: invalid.length,
  hashes: { native_sha256: await digest(values.binary), wasm_sha256: await digest(values.wasm), worker_sha256: await digest(worker), test_sha256: await digest(fileURLToPath(import.meta.url)) } };
const summary = JSON.stringify(evidence, null, 2) + '\n';
if (values.report) await writeFile(values.report, summary);
process.stdout.write(summary);
