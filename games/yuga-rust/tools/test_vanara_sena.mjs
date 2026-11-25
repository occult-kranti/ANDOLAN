// Exercise Hanuman's sixth action across ten real loopback WebSocket peers.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { WebSocket } from 'ws';

const [folder, reportFile] = process.argv.slice(2);
if (!folder || !reportFile) throw Error('Usage: node test_vanara_sena.mjs /path/to/extracted /path/to/report.json');
const root = path.resolve(folder);
const host = spawn(process.execPath, [path.join(root, 'serve_rooms.mjs'), '--port', '0'],
  { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
let log = '';
for (const stream of [host.stdout, host.stderr]) stream.on('data', c => { log += c; });
const peers = [];
async function until(label, fn, timeout = 30000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const result = fn();
    if (result) return result;
    if (host.exitCode !== null) throw Error(label + ': host exited: ' + log.slice(-1000));
    await delay(20);
  }
  throw Error('Timeout waiting for ' + label + ': ' + log.slice(-1000));
}
async function connect(port) {
  const socket = new WebSocket(`ws://127.0.0.1:${port}/rooms`);
  const p = { socket, messages: [], latest: null, replies: [], seq: 0, closed: false };
  peers.push(p);
  socket.on('message', data => {
    const m = JSON.parse(data.toString());
    if (m.type === 'state') {
      p.latest = m.state;
      // Keep only non-null acknowledgements for the requested command checks.
      if (m.accepted !== null) p.replies.push({seq: m.seq, accepted: m.accepted, state: m.state});
    } else p.messages.push(m);
  });
  socket.on('close', () => { p.closed = true; });
  socket.on('error', () => {});
  await until('socket open', () => socket.readyState === WebSocket.OPEN);
  return p;
}
const send = (peer, message) => peer.socket.send(JSON.stringify(message));
const action = (peer, movement, aim, cast) => {
  const seq = ++peer.seq;
  send(peer, { type: 'input', seq, movement, aim, ...(cast ? { cast } : {}) });
  return seq;
};
const remote = (peer, seat) => peer.latest?.roster?.find(p => p.seat === seat);
const near = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

try {
  const port = await until('host start', () => Number(/127\.0\.0\.1:(\d+)/.exec(log)?.[1]));
  const owner = await connect(port);
  send(owner, { type: 'create', hero: 'hanuman', teamSize: 5 });
  const lobby = await until('5v5 lobby', () => owner.messages.find(m => m.type === 'lobby'));
  assert.equal(lobby.capacity, 10);
  for (let seat = 1; seat < 10; seat++) {
    const p = await connect(port);
    send(p, { type: 'join', hero: seat % 2 ? 'rama' : 'hanuman', code: lobby.code });
    const joined = await until('seat ' + seat, () => p.messages.find(m => m.type === 'lobby'));
    assert.equal(joined.seat, seat);
  }
  await until('ten live states', () => peers.every(p => p.latest?.tick >= 2));
  const defender = peers[1];
  assert.equal(owner.latest.abilities[5].id, 'vanara_sena');
  assert.equal(defender.latest.abilities.length, 5);

  // Walk both selected players into range using normal sequenced inputs. Re-send
  // movement while the server's stale-input timer is active.
  let mover = setInterval(() => {
    action(owner, [0, 1], [0, 1]);
    action(defender, [0, -1], [0, -1]);
  }, 250);
  try {
    await until('heroes in cast range', () => near(owner.latest.actor.pos, defender.latest.actor.pos) < 7, 20000);
  } finally { clearInterval(mover); }
  action(owner, [0, 0], [0, 1]);
  action(defender, [0, 0], [0, -1]);
  const stopTick = owner.latest.tick;
  await until('neutral input advances', () => owner.latest.tick >= stopTick + 4 && defender.latest.tick >= stopTick + 4);

  const invalidAim = [-1, 0], defenderAim = [0, -1], defenderPos = defender.latest.actor.pos.slice();
  const ramaSeq = action(defender, [0, 0], defenderAim,
    { slot: 5, ground: defenderPos, aim: invalidAim });
  const rejected = await until('Rama sixth slot rejected', () => defender.replies.find(r => r.seq === ramaSeq));
  assert.equal(rejected.accepted, false);
  assert.deepEqual(rejected.state.actor.aim, defenderAim);
  assert.equal(rejected.state.abilities.length, 5);

  const target = defender.latest.actor.pos.slice();
  const beforeHp = defender.latest.actor.hp;
  const cast = { slot: 5, ground: target, aim: [0, 1] };
  const castSeq = action(owner, [0, 0], [0, 1], cast);
  // The room must reject the repeated sequence before it can schedule a second cast.
  send(owner, { type: 'input', seq: castSeq, movement: [0, 0], aim: [0, 1], cast });
  const accepted = await until('Hanuman Sena accepted', () => owner.replies.find(r => r.seq === castSeq));
  assert.equal(accepted.accepted, true);
  await until('duplicate sequence rejected', () => owner.messages.find(m => m.type === 'error' && /sequence/i.test(m.message)));
  const act = accepted.state.casts.find(c => c.id === 'vanara_sena');
  assert.ok(act);
  assert.ok(near(act.target, target) < 0.001);
  assert.equal(act.release_tick, 12);
  assert.equal(act.impact_tick, 12);
  assert.equal(act.end_tick, 52);
  await until('all nine remote views see the cast', () => peers.slice(1).every(p =>
    remote(p, 0)?.casts?.some(c => c.id === 'vanara_sena' && c.cast_id === act.cast_id && near(c.target, target) < .001)));
  const impact = await until('defender receives impact', () => {
    const event = remote(defender, 0)?.events?.find(e => e.id === 'vanara_sena' && e.kind === 'impact' && e.cast_id === act.cast_id);
    return event && defender.latest.actor.hp < beforeHp ? event : null;
  });
  assert.equal(impact.tick - (accepted.state.tick - act.age_ticks), 12);
  await until('field expiry and full damage', () => !remote(defender, 0)?.casts?.some(c => c.id === 'vanara_sena') &&
    Math.abs(defender.latest.actor.hp - (beforeHp - 28)) < 1e-4);
  for (const p of peers) {
    assert.equal(p.latest.army.waves_enabled, false);
    assert.equal(p.latest.army.units.length, 0);
  }
  const report = {
    result: 'pass', scope: 'ten loopback WebSocket peers against the extracted Wasm host; no rendered browsers or WAN',
    seats: peers.length, hero: 'hanuman', ability: 'vanara_sena', slot: 5,
    target, release_ticks: act.release_tick, end_ticks: act.end_tick, damage: beforeHp - defender.latest.actor.hp,
    all_nine_remote_views_received_cast: true, rama_slot_rejected_without_aim_change: true,
    duplicate_sequence_rejected: true, no_wave_units: true,
    wasm_sha256: createHash('sha256').update(await readFile(path.join(root, 'yuga-rust.wasm'))).digest('hex'),
    html_sha256: createHash('sha256').update(await readFile(path.join(root, 'yuga-rust.html'))).digest('hex'),
    host_sha256: createHash('sha256').update(await readFile(path.join(root, 'serve_rooms.mjs'))).digest('hex'),
    worker_sha256: createHash('sha256').update(await readFile(path.join(root, 'room-wasm.mjs'))).digest('hex'),
    test_sha256: createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex'),
  };
  peers[9].socket.close();
  await until('disconnect closes the remaining room', () => peers.slice(0, 9).every(p => p.closed));
  report.disconnect_closes_room = true;
  await writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  for (const peer of peers) peer.socket.terminate();
  host.kill('SIGTERM');
}
