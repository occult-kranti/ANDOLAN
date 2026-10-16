import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { randomBytes, createHash } from 'node:crypto';
import { promises as fs, createReadStream } from 'node:fs';
import path from 'node:path';
import { WebSocketServer, WebSocket } from 'ws';
import { Simulation, type PersistedSimulation } from '../../../packages/sim/src/index.js';
import { parseClientMessage, PROTOCOL_VERSION, type ServerMessage } from '../../../packages/protocol/src/index.js';

interface Identity { id: string; lastSeen: number }
interface SavedRoom { schema: 1; simulation: PersistedSimulation; identities: Record<string, Identity> }
export interface GameRoom { sim: Simulation; identities: Map<string, Identity>; clients: Map<string, WebSocket>; changed: boolean }
interface ClientContext { room?: GameRoom; playerId?: string; joined: boolean; started: number; messages: number; invalid: number; heartbeat: boolean }
export interface ServerOptions { port?: number; host?: string; dataDir?: string; staticDir?: string; checkpointMs?: number; tickMs?: number }
const digest = (token: string) => createHash('sha256').update(token).digest('hex');
const roomCode = () => randomBytes(4).toString('hex').toUpperCase();
const cleanName = (name: string) => name.replace(/[^\p{L}\p{N} _.-]/gu, '').trim().slice(0, 24) || 'Crew member';
const MIME: Record<string, string> = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm' };

export async function createGameServer(options: ServerOptions = {}) {
  const dataDir = path.resolve(options.dataDir ?? path.join(process.cwd(), '.data'));
  const staticDir = path.resolve(options.staticDir ?? path.join(process.cwd(), 'dist/client'));
  const rooms = new Map<string, GameRoom>();
  const contexts = new Map<WebSocket, ClientContext>();
  let closing = false;
  await fs.mkdir(dataDir, { recursive: true, mode: 0o700 });
  for (const filename of await fs.readdir(dataDir)) {
    if (!/^[A-Z0-9-]{3,16}\.json$/.test(filename)) continue;
    try {
      const contents = await fs.readFile(path.join(dataDir, filename), 'utf8');
      if (contents.length > 5_000_000) continue;
      const saved = JSON.parse(contents) as SavedRoom;
      if (saved.schema !== 1 || saved.simulation.mode !== 'private' || saved.simulation.room !== filename.slice(0, -5)) continue;
      if (!saved.identities || typeof saved.identities !== 'object' || Array.isArray(saved.identities) || Object.keys(saved.identities).length > 4096 || !Object.entries(saved.identities).every(([hash, identity]) => /^[a-f0-9]{64}$/.test(hash) && identity && /^[a-f0-9]{16}$/.test(identity.id) && Number.isFinite(identity.lastSeen))) continue;
      const sim = new Simulation(saved.simulation.room, 'private', saved.simulation);
      rooms.set(sim.room, { sim, identities: new Map(Object.entries(saved.identities)), clients: new Map(), changed: false });
    } catch (error) { console.error(`Checkpoint ${filename} could not be loaded: ${error instanceof Error ? error.message : 'invalid data'}`); }
  }

  const http = createServer((req, res) => { void handleHttp(req, res).catch(() => { if (!res.headersSent) res.writeHead(500); res.end('Server error'); }); });
  async function handleHttp(req: IncomingMessage, res: ServerResponse) {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'same-origin');
    let pathname: string;
    try { pathname = decodeURIComponent(new URL(req.url ?? '/', 'http://localhost').pathname); } catch { res.writeHead(400); res.end('Invalid path'); return; }
    if (pathname === '/health' || pathname === '/api/status') {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
      res.end(JSON.stringify({ ok: true, protocol: PROTOCOL_VERSION, rooms: rooms.size, connected: [...rooms.values()].reduce((n, r) => n + r.clients.size, 0), publicStatus: 'development-sandbox', simulationHz: 20, snapshotHz: 10 }));
      return;
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); res.end('Method not allowed'); return; }
    const requested = path.resolve(staticDir, `.${pathname}`);
    if (pathname.includes('\0') || (requested !== staticDir && !requested.startsWith(staticDir + path.sep))) { res.writeHead(403); res.end('Forbidden'); return; }
    let filename = requested;
    let stat;
    try { stat = await fs.stat(filename); if (stat.isDirectory()) { filename = path.join(filename, 'index.html'); stat = await fs.stat(filename); } }
    catch {
      if (path.extname(pathname)) { res.writeHead(404); res.end('Not found'); return; }
      filename = path.join(staticDir, 'index.html');
      try { stat = await fs.stat(filename); } catch { res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' }); res.end('ANDOLAN room service is running. Start the Vite client or run npm run build.'); return; }
    }
    if (!stat.isFile()) { res.writeHead(404); res.end('Not found'); return; }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(filename)] ?? 'application/octet-stream', 'Content-Length': stat.size, 'Cache-Control': path.extname(filename) === '.html' ? 'no-cache' : 'public, max-age=3600' });
    if (req.method === 'HEAD') { res.end(); return; }
    createReadStream(filename).on('error', () => res.destroy()).pipe(res);
  }

  const wss = new WebSocketServer({ server: http, path: '/ws', maxPayload: 4096, perMessageDeflate: false });
  const send = (socket: WebSocket, message: ServerMessage) => {
    if (socket.readyState === WebSocket.OPEN && socket.bufferedAmount < 1_000_000) socket.send(JSON.stringify(message));
  };
  const fail = (socket: WebSocket, code: string, message: string) => send(socket, { type: 'error', code, message });
  wss.on('connection', socket => {
    if (contexts.size >= 64) { socket.close(1013, 'Development server connection limit'); return; }
    const ctx: ClientContext = { joined: false, started: Date.now(), messages: 0, invalid: 0, heartbeat: true };
    contexts.set(socket, ctx);
    const joinTimeout = setTimeout(() => { if (!ctx.joined) socket.close(1008, 'Join required'); }, 10_000);
    socket.on('pong', () => { ctx.heartbeat = true; });
    socket.on('error', () => { /* close handles authoritative cleanup */ });
    socket.on('message', (raw, isBinary) => {
      const now = Date.now();
      if (now - ctx.started > 1000) { ctx.started = now; ctx.messages = 0; }
      if (++ctx.messages > 120) { socket.close(1008, 'Rate limit'); return; }
      let message;
      try { message = isBinary ? null : parseClientMessage(JSON.parse(raw.toString())); } catch { message = null; }
      if (!message) { fail(socket, 'INVALID_MESSAGE', 'Message did not match the protocol.'); if (++ctx.invalid >= 5) socket.close(1008, 'Invalid messages'); return; }
      if (message.type === 'ping') { send(socket, { type: 'pong', time: message.time, serverTime: now }); return; }
      if (message.type === 'join') {
        if (ctx.joined) { fail(socket, 'ALREADY_JOINED', 'One room per connection.'); return; }
        // A bearer token is scoped to its room. Validate before allocating any room state.
        if (message.token && !message.room) { fail(socket, 'ROOM_REQUIRED', 'Use the saved room code to resume this identity.'); return; }
        let room: GameRoom | undefined;
        if (message.room) {
          room = rooms.get(message.room);
          if (!room || room.sim.mode !== message.mode) { fail(socket, 'ROOM_NOT_FOUND', 'That room is unavailable in this mode.'); return; }
        } else if (message.mode === 'public') room = [...rooms.values()].find(r => r.sim.mode === 'public' && !r.sim.mission.complete && r.sim.players.size < 16);
        if (!room) {
          if (rooms.size >= 128) { fail(socket, 'SERVER_FULL', 'The development server has reached its room limit.'); return; }
          const code = message.mode === 'public' ? `CITY-${randomBytes(3).toString('hex').toUpperCase()}` : roomCode();
          room = { sim: new Simulation(code, message.mode), identities: new Map(), clients: new Map(), changed: true };
          rooms.set(code, room);
        }
        let token = message.token;
        const existing = token ? room.identities.get(digest(token)) : undefined;
        if (token && !existing) { fail(socket, 'INVALID_TOKEN', 'This saved identity does not belong to the room.'); return; }
        let playerId: string;
        if (existing) {
          playerId = existing.id;
          const previous = room.clients.get(playerId);
          if (previous) { previous.close(4001, 'Reconnected elsewhere'); room.clients.delete(playerId); }
          if (room.sim.players.has(playerId)) room.sim.connectPlayer(playerId);
          else {
            try { room.sim.addPlayer(playerId, cleanName(message.name)); }
            catch { fail(socket, 'ROOM_FULL', 'All seats in this room are occupied.'); return; }
          }
          existing.lastSeen = now;
        } else {
          token = randomBytes(24).toString('hex');
          playerId = randomBytes(8).toString('hex');
          try { room.sim.addPlayer(playerId, cleanName(message.name)); }
          catch { fail(socket, 'ROOM_FULL', 'All seats in this room are occupied.'); return; }
          room.identities.set(digest(token), { id: playerId, lastSeen: now });
        }
        ctx.room = room; ctx.playerId = playerId; ctx.joined = true;
        clearTimeout(joinTimeout);
        room.clients.set(playerId, socket); room.changed = true;
        send(socket, { type: 'welcome', protocol: PROTOCOL_VERSION, playerId, token: token!, room: room.sim.room, mode: room.sim.mode, snapshot: room.sim.snapshot() });
        return;
      }
      if (!ctx.joined || !ctx.room || !ctx.playerId || ctx.room.clients.get(ctx.playerId) !== socket) { fail(socket, 'JOIN_REQUIRED', 'Join a room before sending game input.'); return; }
      if (message.type === 'input') ctx.room.sim.input(ctx.playerId, message);
      else if (message.type === 'command') { send(socket, ctx.room.sim.command(ctx.playerId, message)); ctx.room.changed = true; }
    });
    socket.on('close', () => {
      clearTimeout(joinTimeout); contexts.delete(socket);
      if (ctx.room && ctx.playerId && ctx.room.clients.get(ctx.playerId) === socket) {
        ctx.room.clients.delete(ctx.playerId); ctx.room.sim.disconnectPlayer(ctx.playerId, !closing); ctx.room.changed = true;
        for (const identity of ctx.room.identities.values()) if (identity.id === ctx.playerId) identity.lastSeen = Date.now();
      }
    });
  });

  let writeQueue = Promise.resolve();
  function checkpoint() {
    const saves = [...rooms.values()].filter(r => r.sim.mode === 'private' && r.changed).map(r => {
      r.changed = false;
      return { room: r, file: path.join(dataDir, `${r.sim.room}.json`), contents: JSON.stringify({ schema: 1, simulation: r.sim.serialize(), identities: Object.fromEntries(r.identities) } satisfies SavedRoom) };
    });
    writeQueue = writeQueue.then(async () => {
      for (const save of saves) {
        try { await fs.writeFile(`${save.file}.tmp`, save.contents, { mode: 0o600 }); await fs.rename(`${save.file}.tmp`, save.file); }
        catch (error) { save.room.changed = true; console.error('Checkpoint write failed:', error instanceof Error ? error.message : 'unknown error'); }
      }
    });
    return writeQueue;
  }
  let tick = 0;
  const simulationTimer = setInterval(() => {
    for (const room of rooms.values()) {
      if (!room.clients.size) continue;
      const revision = room.sim.mission.revision;
      room.sim.step(0.05);
      // Checkpoint positions as well as mission changes during the regular atomic-save cycle.
      room.changed = true;
      if (tick % 2 === 0 || revision !== room.sim.mission.revision) {
        const snapshot = room.sim.snapshot();
        for (const socket of room.clients.values()) send(socket, snapshot);
      }
    }
    tick++;
  }, options.tickMs ?? 50);
  const checkpointTimer = setInterval(() => { void checkpoint(); }, options.checkpointMs ?? 5000);
  const heartbeatTimer = setInterval(() => {
    for (const [socket, ctx] of contexts) {
      if (!ctx.heartbeat) { socket.terminate(); continue; }
      ctx.heartbeat = false; socket.ping();
    }
    for (const room of rooms.values()) {
      // Reserve disconnected seats for two minutes, retaining authenticated identity for later recovery.
      for (const identity of room.identities.values()) if (!room.clients.has(identity.id) && room.sim.players.has(identity.id) && Date.now() - identity.lastSeen > 120_000) { room.sim.removePlayer(identity.id); room.changed = true; }
      if (room.sim.mode === 'public' && !room.clients.size && room.sim.players.size === 0) rooms.delete(room.sim.room);
    }
  }, 15_000);
  await new Promise<void>((resolve, reject) => { http.once('error', reject); http.listen(options.port ?? 3001, options.host ?? '0.0.0.0', () => { http.off('error', reject); resolve(); }); });
  return {
    http, wss, rooms, checkpoint,
    address: http.address(),
    async close() {
      closing = true;
      clearInterval(simulationTimer); clearInterval(checkpointTimer); clearInterval(heartbeatTimer);
      for (const socket of wss.clients) socket.terminate();
      await new Promise<void>(resolve => wss.close(() => resolve()));
      for (const room of rooms.values()) { for (const player of room.sim.players.values()) room.sim.disconnectPlayer(player.id, false); room.changed = true; }
      await checkpoint();
      await new Promise<void>((resolve, reject) => http.close(error => error ? reject(error) : resolve()));
    },
  };
}
