// Each child runs one authoritative YUGA match. The host validates and routes player intent.
import { spawn } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { constants, createReadStream, existsSync } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { WebSocket, WebSocketServer } from 'ws';

const project = fileURLToPath(new URL('../', import.meta.url));
const { values } = parseArgs({ options: {
  host: { type: 'string', default: '127.0.0.1' },
  port: { type: 'string', default: '8787' },
  html: { type: 'string' },
  binary: { type: 'string' },
  wasm: { type: 'string' },
} });
const port = Number(values.port);
if (!/^\d+$/.test(values.port) || !Number.isInteger(port) || port < 0 || port > 65535) {
  throw new Error('Choose a port from 0 through 65535.');
}
const sibling = name => fileURLToPath(new URL(name, import.meta.url));
const packagedPage = sibling('./yuga-rust.html');
const packagedWasm = sibling('./yuga-rust.wasm');
const html = resolve(values.html ?? (existsSync(packagedPage) ? packagedPage : resolve(project, 'dist/yuga-rust.html')));
if (values.binary && values.wasm) throw Error('Choose either --binary or --wasm for the room authority.');
const wasmWorker = sibling('./room-wasm.mjs');
const wasmFile = values.wasm ? resolve(values.wasm) : (!values.binary && existsSync(packagedWasm) ? packagedWasm : null);
const binary = resolve(values.binary ?? resolve(project, 'target/release', process.platform === 'win32' ? 'room.exe' : 'room'));
const childProgram = wasmFile ? process.execPath : binary;
const childArgs = wasmFile ? [wasmWorker, wasmFile] : [];
await Promise.all([access(html, constants.R_OK), ...(wasmFile
  ? [access(wasmFile, constants.R_OK), access(wasmWorker, constants.R_OK)]
  : [access(binary, constants.X_OK)])]);
const page = await stat(html);
if (!page.isFile()) throw new Error('Expected the built HTML file.');

const MAX_ROOMS = 16;
const MAX_CLIENTS = 64;
const MAX_QUEUED = 4;
const MAX_PACKET = 8192;
const MAX_BACKLOG = 2 * 1024 * 1024;
const AUTHORITY_BYTES_PER_SEAT = 1024 * 1024;
const rooms = new Map();
const clients = new Map();

function send(socket, packet) {
  if (socket.readyState !== WebSocket.OPEN) return;
  const body = JSON.stringify(packet);
  if (socket.bufferedAmount + Buffer.byteLength(body) > MAX_BACKLOG) { socket.terminate(); return; }
  socket.send(body);
}
function reject(socket, message) { send(socket, { type: 'error', message }); }
function isRecord(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
function keysAllowed(obj, names) { return isRecord(obj) && Object.keys(obj).every(k => names.includes(k)); }
function point(value, limit) {
  return Array.isArray(value) && value.length === 2 && value.every(x => Number.isFinite(x) && Math.abs(x) <= limit);
}
function validHero(value) { return value === 'hanuman' || value === 'rama'; }
function stopChild(room) {
  const child = room.child;
  room.child = null;
  if (!child) return;
  child.stdin.destroy();
  child.kill();
  const kill = setTimeout(() => { if (child.exitCode === null && child.signalCode === null) child.kill('SIGKILL'); }, 1000);
  kill.unref();
  child.once('close', () => clearTimeout(kill));
}
function closeRoom(room, message) {
  if (rooms.get(room.code) !== room) return;
  rooms.delete(room.code);
  stopChild(room);
  for (const player of room.players) {
    const client = clients.get(player.socket);
    if (client) client.room = null;
    send(player.socket, { type: 'closed', message });
    player.socket.close(1000, message);
  }
}
function seatTeam(seat) { return seat % 2 === 0 ? 'sun' : 'moon'; }
function makePlayer(socket, hero, seat) {
  return { socket, hero, seq: -1, motion: { movement: [0, 0], aim: [0, seatTeam(seat) === 'sun' ? 1 : -1] },
    actions: [], updated: Date.now() };
}
function writeChild(room, command, seqs) {
  room.flight = { since: Date.now(), seqs };
  room.child.stdin.write(JSON.stringify(command) + '\n');
}
function startAuthority(room) {
  const child = spawn(childProgram, childArgs, { stdio: ['pipe', 'pipe', 'ignore'], windowsHide: true });
  room.child = child;
  const died = () => {
    if (room.child === child) closeRoom(room, 'Match authority stopped.');
  };
  child.on('error', died);
  child.once('close', died);
  child.stdin.on('error', died);
  const chunks = [];
  let bufferedBytes = 0;
  child.stdout.setEncoding('utf8');
  child.stdout.on('data', chunk => {
    if (room.child !== child) return;
    bufferedBytes += Buffer.byteLength(chunk);
    if (bufferedBytes > AUTHORITY_BYTES_PER_SEAT * room.capacity) { closeRoom(room, 'Authority frame exceeded its limit.'); return; }
    chunks.push(chunk);
    const newline = chunk.indexOf('\n');
    if (newline === -1) return;
    try {
      if (newline !== chunk.length - 1) throw new Error('Unexpected trailing authority data');
      const frame = JSON.parse(chunks.join(''));
      chunks.length = 0;
      bufferedBytes = 0;
      if (!room.flight || !Array.isArray(frame.states) || frame.states.length !== room.capacity ||
          !frame.states.every(isRecord) || !Array.isArray(frame.accepted) || frame.accepted.length !== room.capacity) {
        throw new Error('Unexpected authority frame');
      }
      const { seqs } = room.flight;
      room.flight = null;
      room.players.forEach(({ socket }, i) => {
        send(socket, { type: 'state', state: frame.states[i], accepted: frame.accepted[i], seq: seqs[i] });
      });
      if (frame.states[0].winner) {
        room.finished = Date.now();
        stopChild(room);
      }
    } catch { closeRoom(room, 'Invalid authority frame.'); }
  });
  const heroes = room.players.map(player => player.hero);
  const roster = room.capacity === 2 ? { sun: heroes[0], moon: heroes[1] } : { heroes };
  writeChild(room, roster, heroes.map(() => null));
}
function beginLobby(socket, client, message) {
  const joining = message.type === 'join';
  if (!keysAllowed(message, joining ? ['type', 'hero', 'code'] : ['type', 'hero', 'teamSize']) || !validHero(message.hero)) {
    reject(socket, 'Choose Hanuman or Rama and supply the requested room fields.'); return;
  }
  if (!joining && message.teamSize !== undefined && ![1, 3].includes(message.teamSize)) {
    reject(socket, 'Choose a team size of one or three.'); return;
  }
  if (client.room) { reject(socket, 'Leave the current room first.'); return; }
  let room;
  if (joining) {
    const code = typeof message.code === 'string' ? message.code.trim().toUpperCase() : '';
    room = rooms.get(code);
    if (!room || room.players.length >= room.capacity) { reject(socket, 'Room is missing or already full.'); return; }
  } else {
    if (rooms.size >= MAX_ROOMS) { reject(socket, 'Room capacity reached.'); return; }
    let code;
    do { code = randomBytes(4).toString('hex').toUpperCase(); } while (rooms.has(code));
    room = { code, capacity: (message.teamSize ?? 1) * 2, created: Date.now(), players: [], child: null, flight: null, finished: 0 };
    rooms.set(code, room);
  }
  const seat = room.players.length;
  client.room = room;
  client.seat = seat;
  room.players.push(makePlayer(socket, message.hero, seat));
  const count = room.players.length;
  room.players.forEach((player, index) => {
    send(player.socket, { type: 'lobby', code: room.code, seat: index,
      team: seatTeam(index), count, capacity: room.capacity });
  });
  if (count === room.capacity) startAuthority(room);
}
function acceptInput(socket, client, msg) {
  const room = client.room;
  if (!room?.child || room.finished) { reject(socket, 'Match is not running.'); return; }
  const player = room.players[client.seat];
  const cast = msg.cast;
  if (!keysAllowed(msg, ['type', 'seq', 'movement', 'aim', 'cast', 'reload']) ||
      !Number.isSafeInteger(msg.seq) || msg.seq < 0 || !point(msg.movement, 1) || !point(msg.aim, 10000) ||
      (msg.reload !== undefined && typeof msg.reload !== 'boolean') ||
      (cast !== undefined && (!keysAllowed(cast, ['slot', 'ground', 'aim']) ||
        !Number.isInteger(cast.slot) || cast.slot < 0 || cast.slot > 4 || !point(cast.ground, 10000) || !point(cast.aim, 10000)))) {
    reject(socket, 'Invalid input fields.'); return;
  }
  if (msg.seq <= player.seq) { reject(socket, 'Input sequence already processed.'); return; }
  if ((cast || msg.reload) && player.actions.length >= MAX_QUEUED) { reject(socket, 'Action queue is full.'); return; }
  player.seq = msg.seq;
  player.updated = Date.now();
  player.motion = { movement: msg.movement, aim: msg.aim };
  if (cast || msg.reload) player.actions.push({ seq: msg.seq, cast, reload: msg.reload === true });
}
const server = createServer((req, res) => {
  const path = (req.url || '').split('?')[0];
  if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405, { Allow: 'GET, HEAD' }).end(); return; }
  if (path === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify({ ok: true, rooms: rooms.size, clients: clients.size,
      running: Array.from(rooms.values()).filter(r => r.child).length }));
  } else if (path === '/' || path === '/yuga-rust.html') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': page.size, 'Cache-Control': 'no-cache' });
    if (req.method === 'HEAD') { res.end(); return; }
    const content = createReadStream(html);
    res.once('close', () => content.destroy());
    content.on('error', () => res.destroy());
    content.pipe(res);
  } else res.writeHead(404).end();
});
const ws = new WebSocketServer({ noServer: true, maxPayload: MAX_PACKET, perMessageDeflate: false });
server.on('upgrade', (req, socket, head) => {
  let originAllowed = true;
  if (req.headers.origin) {
    try { const origin = new URL(req.headers.origin);
      originAllowed = ['http:', 'https:'].includes(origin.protocol) && origin.host === req.headers.host;
    } catch { originAllowed = false; }
  }
  if (req.url !== '/rooms' || clients.size >= MAX_CLIENTS || !originAllowed) {
    socket.destroy(); return;
  }
  ws.handleUpgrade(req, socket, head, client => ws.emit('connection', client));
});
ws.on('connection', socket => {
  const client = { room: null, seat: -1, window: Date.now(), received: 0, alive: true, idle: Date.now() };
  clients.set(socket, client);
  socket.on('pong', () => { client.alive = true; });
  socket.on('error', () => socket.terminate());
  socket.once('close', () => {
    clients.delete(socket);
    if (client.room) closeRoom(client.room, 'A player left the room.');
  });
  socket.on('message', (raw, binaryMessage) => {
    if (socket.readyState !== WebSocket.OPEN) return;
    const now = Date.now();
    if (now - client.window >= 1000) { client.received = 0; client.window = now; }
    if (++client.received > 64) { socket.close(1008, 'Input rate limit.'); return; }
    client.idle = now;
    let msg;
    try { if (!binaryMessage) msg = JSON.parse(raw.toString()); } catch { /* Invalid messages receive a client error. */ }
    if (!isRecord(msg)) { reject(socket, 'Expected a JSON command.'); return; }
    if (msg.type === 'create' || msg.type === 'join') beginLobby(socket, client, msg);
    else if (msg.type === 'input') acceptInput(socket, client, msg);
    else reject(socket, 'Unknown room command.');
  });
});
const tick = setInterval(() => {
  const now = Date.now();
  for (const room of rooms.values()) {
    if (room.finished) {
      if (now - room.finished > 60000) closeRoom(room, 'Match complete.');
      continue;
    }
    if (!room.child) {
      if (now - room.created > 600000) closeRoom(room, 'Waiting room expired.');
      continue;
    }
    if (room.flight) {
      if (now - room.flight.since > 5000) closeRoom(room, 'Match authority timed out.');
      continue;
    }
    const seqs = [];
    const players = room.players.map(player => {
      const action = player.actions.shift();
      seqs.push(action?.seq ?? player.seq);
      const motion = now - player.updated < 1000 ? player.motion : { movement: [0, 0], aim: player.motion.aim };
      return { motion, casts: action?.cast ? [action.cast] : [], ...(action?.reload ? { reload: true } : {}) };
    });
    writeChild(room, { players, ticks: 2 }, seqs);
  }
}, 100);
const heartbeat = setInterval(() => {
  for (const [socket, client] of clients) {
    if (!client.alive || (!client.room && Date.now() - client.idle > 60000)) { socket.terminate(); continue; }
    client.alive = false;
    if (socket.readyState === WebSocket.OPEN) socket.ping();
  }
}, 30000);
function shutdown() {
  clearInterval(tick); clearInterval(heartbeat);
  for (const room of rooms.values()) closeRoom(room, 'Room host stopped.');
  for (const socket of clients.keys()) socket.terminate();
  ws.close(); server.close(); server.closeAllConnections();
}
process.once('SIGINT', shutdown);
process.once('SIGTERM', shutdown);
server.listen(port, values.host, () => {
  const { address, port } = server.address();
  console.log('YUGA room host listening at http://' + (address.includes(':') ? '[' + address + ']' : address) + ':' + port);
});
