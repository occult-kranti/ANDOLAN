// Compare native and Wasm authorities through one ordinary six-seat vault knockout.
// Run from the repository root after building the optimized room binary and Wasm library.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';

const crate = path.resolve('games/yuga-rust');
const binary = path.join(crate, 'target/release/room');
const wasm = path.join(crate, 'target/wasm32-unknown-unknown/release/yuga_rust.wasm');
const worker = path.join(crate, 'tools/room-wasm.mjs');
const output = path.resolve('games/yuga-native/docs/research/physics-panel-2026/vault-parity.json');
const seats = [0, 1, 2, 3, 4, 5];
const court = [[10, -1], [10, 1], [9, -1], [9, 1], [11, -1], [11, 1]];
const neutral = () => seats.map(() => ({}));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const transcript = createHash('sha256');
let frames = 0;
let maxDifference = 0;

function compare(native, portable, field = '$') {
  if (typeof native === 'number') {
    assert.equal(typeof portable, 'number', field);
    assert.ok(Number.isFinite(native) && Number.isFinite(portable), field);
    const delta = Math.abs(native - portable);
    maxDifference = Math.max(maxDifference, delta);
    if (Number.isInteger(native) && Number.isInteger(portable)) assert.equal(native, portable, field);
    else assert.ok(delta <= 0.0001, field + ' differs by ' + delta);
  } else if (native !== null && typeof native === 'object') {
    assert.ok(portable !== null && typeof portable === 'object', field);
    assert.equal(Array.isArray(native), Array.isArray(portable), field);
    assert.deepEqual(Object.keys(native).sort(), Object.keys(portable).sort(), field);
    for (const key of Object.keys(native)) compare(native[key], portable[key], field + '.' + key);
  } else {
    assert.equal(native, portable, field);
  }
}

function peer(command, args) {
  const child = spawn(command, args, { stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '';
  child.stderr.on('data', data => { stderr += data; });
  const exit = once(child, 'exit');
  const lines = createInterface({ input: child.stdout })[Symbol.asyncIterator]();
  return {
    async send(input) {
      const watchdog = setTimeout(() => child.kill('SIGKILL'), 15000);
      try {
        if (!child.stdin.write(JSON.stringify(input) + '\n')) await once(child.stdin, 'drain');
        const row = await lines.next();
        assert.ok(!row.done, 'Authority stopped: ' + stderr);
        return JSON.parse(row.value);
      } finally {
        clearTimeout(watchdog);
      }
    },
    async close() {
      child.stdin.end();
      const [status] = await exit;
      assert.equal(status, 0, stderr);
    },
    abort() { child.kill(); },
  };
}

const peers = [peer(binary, []), peer(process.execPath, [worker, wasm])];
let packet;
async function exchange(input) {
  const [native, portable] = await Promise.all(peers.map(p => p.send(input)));
  compare(native, portable);
  assert.equal(native.states.length, 6);
  for (const viewer of native.states) {
    for (const remote of viewer.roster) {
      assert.deepEqual(remote.actor, native.states[remote.seat].actor);
    }
  }
  transcript.update(JSON.stringify(input) + '\n' + JSON.stringify(native) + '\n');
  frames++;
  packet = native;
  return packet;
}
async function advance(ticks, players = neutral()) {
  while (ticks > 0) {
    const n = Math.min(4, ticks);
    await exchange({ players, ticks: n });
    ticks -= n;
  }
}
function cast(slot, origin, target) {
  const dx = target[0] - origin[0];
  const dz = target[1] - origin[1];
  const length = Math.hypot(dx, dz);
  return { casts: [{ slot, ground: target, aim: [dx / length, dz / length] }] };
}

try {
  await exchange({ heroes: seats.map(() => 'hanuman') });
  const start = packet.states.map(s => s.actor.pos);
  const delta = court.map((point, i) => point.map((value, j) => value - start[i][j]));
  const walkingTicks = Math.max(...delta.map(d => Math.ceil(Math.hypot(...d) / 0.25)));
  const walking = delta.map((d, i) => ({
    motion: {
      movement: d.map(v => v / (0.25 * walkingTicks)),
      aim: [0, i % 2 === 0 ? 1 : -1],
    },
  }));
  await advance(walkingTicks, walking);
  for (const i of seats) {
    assert.ok(Math.hypot(...packet.states[i].actor.pos.map((v, j) => v - court[i][j])) < 0.005);
  }

  for (const attackers of [[1, 3, 5], [1, 3, 5], [1, 3]]) {
    const players = neutral();
    for (const seat of attackers) players[seat] = cast(0, court[seat], court[0]);
    await exchange({ players, ticks: 1 });
    for (const seat of attackers) assert.equal(packet.accepted[seat], true);
    await advance(11);
  }
  assert.equal(packet.states[0].actor.hp, 28);

  const vault = neutral();
  vault[0] = { casts: [{ slot: 2, ground: court[0], aim: [1, 0] }] };
  await exchange({ players: vault, ticks: 1 });
  assert.equal(packet.accepted[0], true);
  await advance(1);
  const attack = neutral();
  attack[1] = cast(0, court[1], [court[0][0] + 8.5 / 3, court[0][1]]);
  await exchange({ players: attack, ticks: 1 });
  assert.equal(packet.accepted[1], true);
  await advance(3);
  const airborne = packet.states[0].actor.y;
  assert.ok(airborne > 0.35);
  await advance(1);
  const knockoutTick = packet.states[0].tick;
  assert.equal(packet.states[0].actor.alive, false);
  assert.equal(packet.states[0].actor.y, 0);
  assert.equal(packet.states[0].respawn_ticks, 60);
  await advance(60);
  assert.equal(packet.states[0].actor.alive, true);
  assert.equal(packet.states[0].actor.y, 0);
  assert.equal(packet.states[0].respawn_ticks, 0);

  const at = packet.states[0].actor.pos;
  const after = neutral();
  after[0] = cast(0, at, [at[0], at[1] + 1]);
  await exchange({ players: after, ticks: 1 });
  assert.equal(packet.accepted[0], true);
  const result = {
    scope: 'Same public six-seat input trace on native and Wasm room authorities; each snapshot includes all five remote actors.',
    frames_compared: frames,
    seat_snapshots_compared: frames * 6,
    float_tolerance: 0.0001,
    max_numeric_difference: maxDifference,
    airborne_height_before_knockout_m: airborne,
    knockout_tick: knockoutTick,
    grounded_immediately: true,
    grounded_after_60_tick_respawn: true,
    post_respawn_cast_accepted: true,
    trace_sha256: transcript.digest('hex'),
    native_sha256: digest(await readFile(binary)),
    wasm_sha256: digest(await readFile(wasm)),
    worker_sha256: digest(await readFile(worker)),
    test_sha256: digest(await readFile(fileURLToPath(import.meta.url))),
  };
  await Promise.all(peers.map(p => p.close()));
  await writeFile(output, JSON.stringify(result, null, 2) + '\n');
  process.stdout.write(JSON.stringify(result, null, 2) + '\n');
} finally {
  for (const p of peers) p.abort();
}
