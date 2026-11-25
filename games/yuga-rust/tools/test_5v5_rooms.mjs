// Test ten real WebSocket peers against the extracted portable room host.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { WebSocket } from 'ws';

const [folder, reportFile] = process.argv.slice(2);
if (!folder || !reportFile) throw Error('Usage: node test_5v5_rooms.mjs /path/to/extracted /path/to/report.json');
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
  const p = { socket, messages: [], latest: null, frames: 0, closed: false };
  peers.push(p);
  socket.on('message', data => {
    const m = JSON.parse(data.toString());
    if (m.type === 'state') { p.latest = m.state; p.frames++; }
    else p.messages.push(m);
  });
  socket.on('close', () => { p.closed = true; });
  socket.on('error', () => {});
  await until('socket open', () => socket.readyState === WebSocket.OPEN);
  return p;
}
const send = (peer, message) => peer.socket.send(JSON.stringify(message));

try {
  const port = await until('host start', () => Number(/127\.0\.0\.1:(\d+)/.exec(log)?.[1]));
  const first = await connect(port);
  send(first, { type: 'create', hero: 'hanuman', teamSize: 5 });
  const lobby = await until('5v5 lobby', () => first.messages.find(m => m.type === 'lobby'));
  assert.equal(lobby.capacity, 10);
  for (let seat = 1; seat < 10; seat++) {
    const peer = await connect(port);
    send(peer, { type: 'join', hero: seat % 2 ? 'rama' : 'hanuman', code: lobby.code });
    const joined = await until('seat ' + seat, () => peer.messages.find(m => m.type === 'lobby'));
    assert.equal(joined.seat, seat);
    assert.equal(joined.team, seat % 2 ? 'moon' : 'sun');
    assert.equal(joined.capacity, 10);
  }
  await until('ten live states', () => peers.every(p => p.latest?.tick >= 2));
  const starts = peers.map(p => p.latest.actor.pos.slice());
  const ids = peers.map(p => p.latest.actor.id);
  assert.equal(new Set(ids).size, 10);
  for (let seat = 0; seat < 10; seat++) {
    const state = peers[seat].latest;
    assert.equal(state.seat, seat);
    assert.equal(state.ruleset, 'hero_skirmish');
    assert.equal(state.army.waves_enabled, false);
    assert.equal(state.army.units.length, 0);
    assert.equal(state.army.wave, 0);
    assert.equal(state.roster.length, 9);
    assert.deepEqual(state.score, { sun: 0, moon: 0, target: 25 });
    send(peers[seat], { type: 'input', seq: 1, movement: [0, seat % 2 ? -1 : 1], aim: [0, seat % 2 ? -1 : 1] });
  }
  await until('both teams move', () => [0, 9].every(i =>
    Math.hypot(...peers[i].latest.actor.pos.map((v, j) => v - starts[i][j])) > 0.05));
  const ticks = peers.map(p => p.latest.tick);
  assert.ok(Math.max(...ticks) - Math.min(...ticks) <= 2, 'client snapshots should be closely synchronized');
  for (let i = 0; i < 10; i++) send(peers[i], { type: 'input', seq: 2, movement: [0, 0], aim: [0, i % 2 ? -1 : 1] });
  const report = {
    scope: 'ten WebSocket peers and the extracted local Wasm room host; no browser rendering or public network',
    result: 'pass', seats: 10, teams: { sun: 5, moon: 5 }, unique_ids: ids.length,
    zero_wave_units: true, each_peer_remote_heroes: 9, target_score: 25,
    sample_ticks: ticks, sample_frames: peers.map(p => p.frames),
    wasm_sha256: createHash('sha256').update(await readFile(path.join(root, 'yuga-rust.wasm'))).digest('hex'),
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
