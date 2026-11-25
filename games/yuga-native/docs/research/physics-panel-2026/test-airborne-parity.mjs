// Compare vertical-hit behavior in six-seat native and Wasm room authorities.
// Build the optimized room and Wasm library, then run from the repository root.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const crate = path.resolve('games/yuga-rust');
const binary = path.join(crate, 'target/release/room');
const wasm = path.join(crate, 'target/wasm32-unknown-unknown/release/yuga_rust.wasm');
const worker = path.join(crate, 'tools/room-wasm.mjs');
const report = path.resolve('games/yuga-native/docs/research/physics-panel-2026/airborne-parity.json');
const commands = [[binary], [process.execPath, worker, wasm]];
const heroes = Array(6).fill('hanuman');
const neutral = () => Array.from({ length: 6 }, () => ({}));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const transcript = createHash('sha256');
let maxDifference = 0;
let comparedFrames = 0;

function compare(native, portable, field = '$') {
  if (typeof native === 'number') {
    assert.equal(typeof portable, 'number', field);
    assert.ok(Number.isFinite(native) && Number.isFinite(portable), field);
    const difference = Math.abs(native - portable);
    maxDifference = Math.max(maxDifference, difference);
    if (Number.isInteger(native) && Number.isInteger(portable)) assert.equal(native, portable, field);
    else assert.ok(difference <= 0.0001, field + ' differs by ' + difference);
  } else if (native !== null && typeof native === 'object') {
    assert.ok(portable !== null && typeof portable === 'object', field);
    assert.equal(Array.isArray(native), Array.isArray(portable), field);
    assert.deepEqual(Object.keys(native).sort(), Object.keys(portable).sort(), field);
    for (const key of Object.keys(native)) compare(native[key], portable[key], field + '.' + key);
  } else {
    assert.equal(native, portable, field);
  }
}

function invoke(command, trace) {
  const result = spawnSync(command[0], command.slice(1), {
    input: trace.map(line => JSON.stringify(line)).join('\n') + '\n',
    encoding: 'utf8',
    timeout: 30000,
    maxBuffer: 128 * 1024 * 1024,
  });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  return result.stdout.trimEnd().split('\n').map(line => JSON.parse(line));
}

const initial = invoke(commands[0], [{ heroes }])[0];
const start = initial.states.map(state => state.actor.pos);
const results = [];
for (const jumper of [0, 1]) {
  for (const [attackAge, expectedHit] of [[2, true], [4, false]]) {
    const attacker = 1 - jumper;
    const court = [[8, -4], [8, 4], [30, -2], [30, 2], [34, -3], [34, 3]];
    court[jumper] = [11, jumper === 0 ? -1 : 1];
    court[attacker] = [15, -court[jumper][1]];
    const delta = court.map((point, i) => point.map((value, j) => value - start[i][j]));
    const walkingTicks = Math.max(...delta.map(d => Math.ceil(Math.hypot(...d) / 0.25)));
    const walking = delta.map((d, i) => ({
      motion: {
        movement: d.map(value => value / (0.25 * walkingTicks)),
        aim: [0, i % 2 === 0 ? 1 : -1],
      },
    }));
    const trace = [{ heroes }];
    function advance(ticks, players = neutral()) {
      while (ticks > 0) {
        const n = Math.min(4, ticks);
        trace.push({ players, ticks: n });
        ticks -= n;
      }
    }
    advance(walkingTicks, walking);
    const vault = neutral();
    vault[jumper] = { casts: [{ slot: 2, ground: court[jumper], aim: [1, 0] }] };
    trace.push({ players: vault, ticks: 1 });
    const vaultIndex = trace.length - 1;
    advance(attackAge - 1);
    const target = [court[jumper][0] + 8.5 * attackAge / 9, court[jumper][1]];
    const vector = target.map((v, i) => v - court[attacker][i]);
    const length = Math.hypot(...vector);
    const attack = neutral();
    attack[attacker] = { casts: [{ slot: 0, ground: target, aim: vector.map(v => v / length) }] };
    trace.push({ players: attack, ticks: 1 });
    const attackIndex = trace.length - 1;
    advance(3);
    const beforeIndex = trace.length - 1;
    advance(1);
    const impactIndex = trace.length - 1;

    const [native, portable] = commands.map(command => invoke(command, trace));
    assert.equal(native.length, trace.length);
    assert.equal(portable.length, trace.length);
    native.forEach((frame, index) => {
      compare(frame, portable[index]);
      assert.equal(frame.states.length, 6);
      for (const viewer of frame.states) {
        for (const remote of viewer.roster) assert.deepEqual(remote.actor, frame.states[remote.seat].actor);
      }
      transcript.update(JSON.stringify(trace[index]) + '\n' + JSON.stringify(frame) + '\n');
      comparedFrames++;
    });
    assert.equal(native[vaultIndex].accepted[jumper], true);
    assert.equal(native[attackIndex].accepted[attacker], true);
    const before = native[beforeIndex].states[jumper];
    const after = native[impactIndex].states[jumper];
    assert.equal(before.actor.hp, 300);
    assert.equal(before.actor.y <= 1.4, expectedHit);
    assert.equal(after.actor.hp, expectedHit ? 266 : 300);
    const impact = native[impactIndex].states[attacker].events.find(event =>
      event.kind === 'impact' && event.id === 'vajra_gada' && event.tick === after.tick
    );
    assert.ok(impact, 'Gada impact event missing');
    const receipt = impact.receipts.find(r => r.unit === after.actor.id);
    assert.equal(Boolean(receipt), expectedHit);
    if (receipt) assert.equal(receipt.damage, 34);
    results.push({
      jumper_seat: jumper,
      attacker_seat: attacker,
      sampled_feet_height_m: before.actor.y,
      hit_expected: expectedHit,
      hp_before: before.actor.hp,
      hp_after: after.actor.hp,
      victim_receipt: receipt ?? null,
      snapshots_compared: trace.length * 6,
    });
  }
}

const evidence = {
  scope: 'Identical public six-seat movement, vault and attack inputs in native and Wasm room authorities.',
  float_tolerance: 0.0001,
  max_numeric_difference: maxDifference,
  compared_frames: comparedFrames,
  seat_snapshots_compared: comparedFrames * 6,
  cases: results,
  trace_sha256: transcript.digest('hex'),
  native_sha256: digest(await readFile(binary)),
  wasm_sha256: digest(await readFile(wasm)),
  worker_sha256: digest(await readFile(worker)),
  test_sha256: digest(await readFile(fileURLToPath(import.meta.url))),
};
await writeFile(report, JSON.stringify(evidence, null, 2) + '\n');
process.stdout.write(JSON.stringify(evidence, null, 2) + '\n');
