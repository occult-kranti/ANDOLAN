// Black-box multiplayer checks against the shipped WebSocket adapter and native Rust room.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { access, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { setTimeout as delay } from 'node:timers/promises';

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const crate = path.resolve(toolDir, '..');
const { values } = parseArgs({
  options: {
    binary: { type: 'string' },
    wasm: { type: 'string' },
    package: { type: 'string' },
    report: { type: 'string' },
    rooms: { type: 'string', default: '3' },
  },
});
assert.ok([values.binary, values.wasm, values.package].filter(Boolean).length <= 1, 'choose one test authority');
const packaged = values.package ? path.resolve(values.package) : null;
const serverScript = path.join(packaged ?? toolDir, 'serve_rooms.mjs');
const worker = path.join(packaged ?? toolDir, 'room-wasm.mjs');
const wasm = values.wasm ? path.resolve(values.wasm) : (packaged ? path.join(packaged, 'yuga-rust.wasm') : null);
const binary = path.resolve(values.binary ?? path.join(crate, 'target', 'release', process.platform === 'win32' ? 'room.exe' : 'room'));
const authorityArgs = packaged ? [] : (wasm ? ['--wasm', wasm] : ['--binary', binary]);
const roomCount = Number(values.rooms);
const roomCapacity = 16;
assert.ok(Number.isSafeInteger(roomCount) && roomCount >= 2 && roomCount <= roomCapacity, '--rooms must be 2 through 16');
const sockets = new Set();
const servers = new Set();
const nativePids = new Set();
const checks = [];
let messageCount = 0;
let bytesReceived = 0;
const sha = async file => createHash('sha256').update(await readFile(file)).digest('hex');

async function until(label, predicate, timeout = 6000) {
  const deadline = Date.now() + timeout;
  do {
    const value = await predicate();
    if (value) return value;
    await delay(12);
  } while (Date.now() < deadline);
  throw Error('Timed out waiting for ' + label);
}

async function children(pid) {
  if (process.platform !== 'linux') return [];
  const candidates = (await readdir('/proc')).filter(name => /^\d+$/.test(name));
  const found = await Promise.all(candidates.map(async name => {
    try {
      const status = await readFile('/proc/' + name + '/status', 'utf8');
      return Number(/^PPid:\s+(\d+)$/m.exec(status)?.[1]) === pid ? Number(name) : null;
    } catch (error) {
      if (['ENOENT', 'ESRCH', 'EACCES'].includes(error.code)) return null;
      throw error;
    }
  }));
  return found.filter(pid => pid !== null);
}

function alive(pid) {
  try { process.kill(pid, 0); return true; }
  catch (error) { if (error.code === 'ESRCH') return false; throw error; }
}

async function connect(url) {
  const socket = new WebSocket(url);
  sockets.add(socket);
  const messages = [];
  let closeEvent;
  socket.addEventListener('close', event => { closeEvent = event; }, { once: true });
  socket.addEventListener('message', event => {
    messageCount++;
    bytesReceived += Buffer.byteLength(event.data);
    messages.push(JSON.parse(event.data));
  });
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(Error('Timed out opening ' + url)), 4000);
    socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener('error', () => { clearTimeout(timer); reject(Error('WebSocket did not open ' + url)); }, { once: true });
  });
  return {
    socket, messages,
    get closed() { return until('WebSocket close handshake', () => closeEvent); },
    send: value => socket.send(JSON.stringify(value)),
    receive: (predicate, label, after = 0) => until(label, () => messages.slice(after).find(predicate)),
    close: () => socket.close(1000, 'test complete'),
  };
}

function record(name, evidence) {
  checks.push({ name, ...evidence });
}

async function startServer(port = 0) {
  const child = spawn(process.execPath, [serverScript, ...authorityArgs, '--host', '127.0.0.1', '--port', String(port)], {
    cwd: packaged ?? crate, env: packaged ? { ...process.env, NODE_PATH: '' } : process.env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  servers.add(child);
  let log = '';
  child.stdout.on('data', b => { log += b; });
  child.stderr.on('data', b => { log += b; });
  child.on('error', error => { log += error.message; });
  const exited = new Promise(resolve => child.on('exit', (code, signal) => resolve({ code, signal })));
  const actualPort = await until('room server listening', () => {
    if (child.exitCode !== null || child.signalCode) throw Error(log || 'room server exited');
    return Number(/(?:127\.0\.0\.1|localhost):(\d+)/.exec(log)?.[1]);
  });
  const http = 'http://127.0.0.1:' + actualPort;
  const health = async () => {
    const response = await fetch(http + '/health', { signal: AbortSignal.timeout(1800) });
    assert.equal(response.status, 200);
    const state = await response.json();
    assert.equal(state.ok, true);
    return state;
  };
  const initial = await health();
  assert.equal(initial.rooms, 0);
  assert.equal(initial.running, 0);
  assert.equal(initial.clients, 0);
  return { child, exited, health, port: actualPort, ws: 'ws://127.0.0.1:' + actualPort + '/rooms' };
}

async function stopServer(host) {
  host.child.kill('SIGTERM');
  await until('host exit', () => host.child.exitCode !== null || host.child.signalCode);
  const result = await host.exited;
  servers.delete(host.child);
  return result;
}

const snapshot = (client, pred, label, after = 0) =>
  client.receive(m => m.type === 'state' && pred(m.state, m), label, after).then(m => m.state);

async function createPair(host, index) {
  const owner = await connect(host.ws);
  owner.send({ type: 'create', hero: 'hanuman' });
  const invite = await owner.receive(m => m.type === 'lobby', 'Sun lobby');
  assert.equal(invite.seat, 0);
  assert.ok(typeof invite.code === 'string' && invite.code.length > 0);
  const guest = await connect(host.ws);
  guest.send({ type: 'join', code: invite.code, hero: 'rama' });
  const joined = await guest.receive(m => m.type === 'lobby', 'Moon lobby');
  assert.equal(joined.seat, 1);
  assert.equal(joined.code, invite.code);
  const [a,b] = await Promise.all([
    snapshot(owner, () => true, 'Sun native snapshot'), snapshot(guest, () => true, 'Moon native snapshot'),
  ]);
  assert.equal(a.hero, 'hanuman');
  assert.equal(b.hero, 'rama');
  assert.equal(a.actor.team, 'sun');
  assert.equal(b.actor.team, 'moon');
  assert.equal(a.opponent.hero, b.hero);
  assert.equal(b.opponent.hero, a.hero);
  assert.deepEqual(a.opponent.actor.pos, b.actor.pos);
  return { index, code: invite.code, owner, guest, start: [a,b] };
}

const sendInput = (client, seq, movement, aim, cast) =>
  client.send({ type: 'input', seq, movement, aim, ...(cast ? { cast } : {}) });

async function run() {
  await access(wasm ?? binary);
  const host = await startServer();
  if (packaged) {
    const page = await fetch('http://127.0.0.1:' + host.port + '/', { signal: AbortSignal.timeout(15000) });
    assert.equal(page.status, 200);
    const digest = createHash('sha256');
    let byteCount = 0;
    for await (const chunk of page.body) {
      digest.update(chunk);
      byteCount += chunk.length;
    }
    const htmlHash = digest.digest('hex');
    assert.equal(htmlHash, await sha(path.join(packaged, 'yuga-rust.html')));
    record('unpacked host serves the adjacent standalone game', { bytes: byteCount, html_sha256: htmlHash });
  }
  const pairs = await Promise.all(Array.from({ length: roomCount }, (_,i) => createPair(host, i)));
  assert.equal(new Set(pairs.map(p => p.code)).size, roomCount);
  const full = await until('active rooms in health', async () => {
    const h = await host.health();
    return h.running === roomCount && h.rooms === roomCount && h.clients === 2 * roomCount && h;
  });
  const pids = await children(host.child.pid);
  if (process.platform === 'linux') assert.equal(pids.length, roomCount, 'one native process for each playing room');
  for (const pid of pids) nativePids.add(pid);
  record('separate authority processes and opposite heroes', { rooms: full.rooms, active: full.running, sockets: full.clients, observed_authority_children: process.platform === 'linux' ? pids.length : null });

  const pair = pairs[0], other = pairs[1];
  const start = pair.start[1].actor.pos;
  sendInput(pair.guest, 1, [1,0], [0,-1]);
  const seen = await snapshot(pair.owner, s => s.opponent.actor.pos[0] > start[0] + 0.12, 'Moon motion on Sun client');
  const moved = await snapshot(pair.guest, s => s.tick === seen.tick, 'matching motion tick on Moon client');
  assert.deepEqual(seen.opponent.actor.pos, moved.actor.pos);
  sendInput(pair.guest, 2, [0,0], [0,-1]);
  const ready = await snapshot(pair.guest, s => s.tick >= moved.tick + 4, 'neutral movement');
  const aim = [0,-1], cast = { slot: 0, ground: pair.start[0].actor.pos, aim };
  sendInput(pair.guest, 3, [0,0], aim, cast);
  const guestCast = await snapshot(pair.guest,
    s => s.active?.id === 'kodanda' && s.events.some(e => e.kind === 'begin' && e.id === 'kodanda'), 'Rama releases a cast');
  const matchingCast = await snapshot(pair.owner, s => s.tick === guestCast.tick, 'same cast tick on opponent client');
  assert.equal(matchingCast.opponent.active.id, 'kodanda');
  assert.equal(matchingCast.opponent.active.cast_id, guestCast.active.cast_id);
  const castId = guestCast.active.cast_id;
  record('opponent movement and cast mirrored at equal tick', {
    caster: guestCast.hero, observed_by: matchingCast.hero, delta_x_m: moved.actor.pos[0] - start[0],
    movement_tick: moved.tick, cast_tick: guestCast.tick, cast_id: castId,
  });

  const isolated = await snapshot(other.guest, s => s.tick >= other.start[1].tick + (guestCast.tick - pair.start[1].tick),
    'second room advances independently');
  assert.deepEqual(isolated.actor.pos, other.start[1].actor.pos);
  assert.equal(isolated.active, null);
  assert.ok(!other.guest.messages.some(m => m.type === 'state' && m.state.events.some(e => e.kind === 'begin')));
  record('second room saw no motion or cast from first room', { isolated_tick: isolated.tick });

  // Wait past both animation lock and cooldown. A replay here would be a legitimate second
  // action if the transport accidentally forwarded stale input to the native simulator.
  const cool = await snapshot(pair.guest, s => s.tick >= guestCast.tick + 28 &&
    s.active === null && s.abilities[0].cooldown_ticks === 0, 'cast cooldown and recovery finish');
  const marker = pair.guest.messages.length;
  sendInput(pair.guest, 3, [-1,0], aim, cast);
  sendInput(pair.guest, 1, [-1,0], aim, cast);
  const afterStale = await snapshot(pair.guest, s => s.tick >= cool.tick + 8, 'stale commands have passed several server ticks', marker);
  assert.deepEqual(afterStale.actor.pos, cool.actor.pos, 'stale input cannot move the actor');
  const observed = pair.guest.messages.slice(marker).filter(m => m.type === 'state');
  assert.ok(observed.every(m => !m.state.active && !m.state.events.some(e => e.kind === 'begin' && e.cast_id !== castId)));
  assert.ok(ready.tick < guestCast.tick);
  record('duplicate and out-of-order command after cooldown', { rejected_sequences: [3, 1], observation_ticks: afterStale.tick - cool.tick });

  // A fresh connection must be able to correct an invalid game command without mutating a room.
  const invalid = await connect(host.ws);
  invalid.send({ type: 'create', hero: 'invented' });
  await invalid.receive(m => m.type === 'error', 'unknown hero rejected');
  const invalidCount = invalid.messages.length;
  invalid.send({ type: 'join', code: pair.code, hero: 'hanuman' });
  await invalid.receive(m => m.type === 'error', 'full room rejected', invalidCount);
  if (roomCount === roomCapacity) {
    const attemptedAt = invalid.messages.length;
    invalid.send({ type: 'create', hero: 'rama' });
    await invalid.receive(m => m.type === 'error' && /capacity/i.test(m.message), 'maximum room count enforced', attemptedAt);
    const capped = await host.health();
    assert.equal(capped.rooms, roomCapacity);
    assert.equal(capped.running, roomCapacity);
    record('configured room capacity', { active: roomCapacity, additional_room_rejected: true });
  }
  const beforeInvalid = pair.guest.messages.length;
  pair.guest.send({ type: 'input', seq: 4, movement: [0,0], aim, cast: {slot: 99, ground:[0,0], aim} });
  await pair.guest.receive(m => m.type === 'error', 'out-of-range ability slot rejected', beforeInvalid);
  sendInput(pair.guest, 5, [0,0], aim, cast);
  const resumed = await snapshot(pair.guest, s => s.active?.id === 'kodanda' && s.active.cast_id !== castId,
    'valid input still works after bounded invalid field', beforeInvalid);
  invalid.close();
  await invalid.closed;
  const oversized = await connect(host.ws);
  oversized.socket.send(' '.repeat(9 * 1024));
  const payloadClose = await oversized.closed;
  assert.equal(payloadClose.code, 1009, 'oversized message has its own close status');
  record('invalid hero, full room and invalid ability slot', { next_valid_cast_id: resumed.active.cast_id, oversized_payload_bytes: 9 * 1024, payload_close_code: payloadClose.code });

  const clients = pairs.flatMap(p => [p.owner, p.guest]);
  const cursors = clients.map(c => c.messages.length);
  const bursts = 24;
  const seqStart = 100;
  const began = performance.now();
  for (let step = 0; step < bursts; step++) {
    clients.forEach((client, i) => {
      const aim = [0, i % 2 === 0 ? 1 : -1];
      const direction = step < bursts / 2 ? 0.3 : -0.3;
      const action = step === 3 ? { slot: 0, ground: [0,0], aim } : undefined;
      sendInput(client, seqStart + step, step === bursts - 1 ? [0,0] : [direction,0], aim, action);
    });
    await delay(50);
  }
  const lastSeq = seqStart + bursts - 1;
  await Promise.all(clients.map((client, i) => client.receive(
    m => m.type === 'state' && m.seq === lastSeq, 'last load sequence acknowledged', cursors[i],
  )));
  const observedCounts = [], gaps = [];
  clients.forEach((client, i) => {
    const updates = client.messages.slice(cursors[i]).filter(m => m.type === 'state');
    const ticks = updates.map(m => m.state.tick);
    assert.ok(ticks.length >= 2, 'two or more different authority snapshots under concurrent input');
    for (let j = 1; j < ticks.length; j++) {
      assert.ok(ticks[j] > ticks[j-1], 'monotonic room ticks');
      gaps.push(ticks[j] - ticks[j-1]);
    }
    observedCounts.push(ticks.length);
  });
  record('concurrent human-rate movement and casts acknowledged', {
    simultaneous_clients: clients.length, input_frames_sent: clients.length * bursts,
    input_interval_ms: 50, elapsed_ms: Math.round(performance.now() - began),
    final_sequence_each: lastSeq, min_snapshots_per_client: Math.min(...observedCounts),
    max_snapshots_per_client: Math.max(...observedCounts), max_native_tick_gap: Math.max(...gaps),
  });

  pair.guest.close();
  await pair.guest.closed;
  const departure = await pair.owner.receive(m => m.type === 'closed', 'departure notice at remaining peer');
  assert.ok(typeof departure.message === 'string' && departure.message.length > 0);
  await pair.owner.closed;
  const remaining = await until('only departing room removed', async () => {
    const h = await host.health();
    return h.rooms === roomCount - 1 && h.running === roomCount - 1 && h.clients === (roomCount-1)*2 && h;
  });
  const nextOther = other.guest.messages.length;
  await snapshot(other.guest, () => true, 'unrelated native room continues after disconnect', nextOther);
  record('peer departure frees exactly one room', { remaining_rooms: remaining.rooms, notification: departure.message });

  // Stop with active matches to exercise graceful shutdown and native child reaping.
  const port = host.port;
  await stopServer(host);
  await Promise.all(pairs.slice(1).flatMap(p => [p.owner.closed, p.guest.closed]));
  if (process.platform === 'linux') await until('all original native children reaped', () => pids.every(pid => !alive(pid)));
  const restarted = await startServer(port);
  const fresh = await createPair(restarted, -1);
  const freshPid = await children(restarted.child.pid);
  for (const pid of freshPid) nativePids.add(pid);
  assert.equal(fresh.start[0].actor.hp, pair.start[0].actor.hp);
  assert.deepEqual(fresh.start[0].actor.pos, pair.start[0].actor.pos);
  assert.equal(fresh.start[1].active, null);
  fresh.owner.close();
  await fresh.guest.closed;
  const empty = await until('restart releases room, child and sockets', async () => {
    const h = await restarted.health();
    return h.rooms === 0 && h.clients === 0 && h.running === 0 && h;
  });
  await stopServer(restarted);
  if (process.platform === 'linux') await until('restarted native child reaped', () => freshPid.every(pid => !alive(pid)));
  record('active shutdown, child cleanup and fresh same-port restart', {
    original_children_reaped: process.platform === 'linux' ? pids.length : null,
    restarted_children_reaped: process.platform === 'linux' ? freshPid.length : null,
    final: { rooms: empty.rooms, sockets: empty.clients, running: empty.running },
  });
}

try {
  await run();
  const evidence = {
    result: 'pass', scope: 'Real loopback WebSocket clients with one Rust authority per match. Rendering and WAN quality are outside this run.',
    authority: wasm ? 'Rust WebAssembly in a Node worker process' : 'native Rust process', packaged_defaults: Boolean(packaged),
    platform: process.platform, node: process.version, rooms_at_peak: roomCount,
    game_messages_received: messageCount, received_payload_bytes: bytesReceived,
    hashes: { ...(wasm ? { wasm_sha256: await sha(wasm), worker_sha256: await sha(worker) } : { native_binary_sha256: await sha(binary) }),
      adapter_sha256: await sha(serverScript), test_sha256: await sha(fileURLToPath(import.meta.url)) },
    checks,
  };
  if (values.report) {
    const destination = path.resolve(values.report);
    await mkdir(path.dirname(destination), { recursive: true });
    await writeFile(destination, JSON.stringify(evidence, null, 2) + '\n');
  }
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  for (const socket of sockets) {
    if (socket.readyState === WebSocket.OPEN) socket.close();
  }
  for (const server of servers) server.kill('SIGTERM');
  if (servers.size) {
    await delay(500);
    for (const pid of nativePids) if (alive(pid)) process.kill(pid, 'SIGKILL');
    for (const server of servers) if (server.exitCode === null && !server.signalCode) server.kill('SIGKILL');
  }
}
