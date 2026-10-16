import { createServer } from 'node:http';
import { createReadStream, promises as fs } from 'node:fs';
import { randomBytes, createHash } from 'node:crypto';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { WebSocket, WebSocketServer } from 'ws';
import { HEROES } from '../shared/heroes.js';
import { ArenaSimulation } from '../shared/simulation.js';
import { YUGA_PROTOCOL } from '../shared/types.js';
import type { ArenaCommand, ArenaInput, ArenaJoin, ServerMessage, Team } from '../shared/types.js';
import { ArenaStepClock } from './clock.js';

interface Identity { id: string; heroId: string; team: Team; lastSeen: number }
export interface ArenaRoom { sim: ArenaSimulation; identities: Map<string, Identity>; clients: Map<string, WebSocket>; lastActive: number; finishedAt: number | null }
export interface ArenaServerOptions { port?: number; host?: string; tickMs?: number; idleRoomMs?: number; staticDir?: string; simulation?: { duration?: number; botsPerTeam?: number } }
type ClientMessage = ArenaJoin | ArenaInput | ArenaCommand;
const hash = (token: string) => createHash('sha256').update(token).digest('hex');
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const keys = (value: Record<string, unknown>, allowed: readonly string[]) => Object.keys(value).every(key => allowed.includes(key));
const id = (value: unknown) => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(value);

/** Strict network intent schema: position, health, cooldown and reward claims never enter the engine. */
export function parseArenaMessage(raw: unknown): ClientMessage | null {
  if (!object(raw)) return null;
  if (raw.type === 'join' && keys(raw, ['type', 'protocol', 'room', 'heroId', 'name', 'token']) && raw.protocol === YUGA_PROTOCOL && typeof raw.heroId === 'string' && HEROES.some(hero => hero.id === raw.heroId) && typeof raw.name === 'string' && raw.name.length >= 1 && raw.name.length <= 24 && (raw.room === undefined || typeof raw.room === 'string' && /^[A-Z0-9-]{3,16}$/.test(raw.room)) && (raw.token === undefined || typeof raw.token === 'string' && /^[a-f0-9]{48}$/.test(raw.token))) return raw as unknown as ArenaJoin;
  if (raw.type === 'input' && keys(raw, ['type', 'seq', 'moveX', 'moveZ', 'yaw', 'pitch', 'fire', 'jump']) && Number.isSafeInteger(raw.seq) && Number(raw.seq) >= 0 && ['moveX', 'moveZ', 'yaw', 'pitch'].every(key => typeof raw[key] === 'number' && Number.isFinite(raw[key])) && typeof raw.fire === 'boolean' && typeof raw.jump === 'boolean') return raw as unknown as ArenaInput;
  if (raw.type === 'command' && id(raw.id)) {
    if (raw.action === 'ability' && keys(raw, ['type', 'id', 'action', 'slot']) && [0, 1, 2].includes(raw.slot as number)) return raw as unknown as ArenaCommand;
    if (raw.action === 'upgrade' && keys(raw, ['type', 'id', 'action', 'upgrade']) && ['power', 'vitality', 'tempo'].includes(raw.upgrade as string)) return raw as unknown as ArenaCommand;
  }
  return null;
}

export async function createArenaServer(options: ArenaServerOptions = {}) {
  const rooms = new Map<string, ArenaRoom>();
  const contexts = new Map<WebSocket, { room?: ArenaRoom; id?: string; alive: boolean; windowAt: number; count: number; invalid: number }>();
  const inputTimes = new Map<string, number>();
  const clock = new ArenaStepClock(performance.now());
  let tick = 0;
  const advance = (now: number) => {
    // Wall-clock stale intent must not be replayed across a stalled catch-up batch.
    for (const room of rooms.values()) for (const actor of room.sim.actors.values()) if (actor.connected && now - (inputTimes.get(actor.id) ?? -Infinity) > 350) room.sim.clearInput(actor.id);
    const changed = new Set<ArenaRoom>();
    clock.advance(now, dt => {
      for (const room of rooms.values()) {
        if (!room.clients.size) continue;
        const previousPhase = room.sim.phase; room.sim.step(dt);
        if (room.sim.phase === 'finished' && room.finishedAt === null) room.finishedAt = Date.now();
        if (tick % 2 === 0 || previousPhase !== room.sim.phase) changed.add(room);
      }
      tick++;
    });
    // Coalesce a catch-up batch into its newest scheduled snapshot; no obsolete burst.
    for (const room of changed) { const snapshot = room.sim.snapshot(); for (const socket of room.clients.values()) send(socket, { type: 'snapshot', snapshot }); }
  };
  const idleMs = options.idleRoomMs ?? 120_000;
  const staticDir = path.resolve(options.staticDir ?? path.join(process.cwd(), 'dist/yuga'));
  const mime: Record<string, string> = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2', '.json': 'application/json' };
  const http = createServer((request, response) => {
    void (async () => {
      response.setHeader('X-Content-Type-Options', 'nosniff'); response.setHeader('Referrer-Policy', 'same-origin');
      let pathname: string;
      try { pathname = decodeURIComponent(new URL(request.url ?? '/', 'http://localhost').pathname); } catch { response.writeHead(400); response.end('Invalid path'); return; }
      if (pathname === '/health') { response.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); response.end(JSON.stringify({ ok: true, game: 'yuga', protocol: YUGA_PROTOCOL, rooms: rooms.size, connected: [...rooms.values()].reduce((n, room) => n + room.clients.size, 0), simulationHz: 20, snapshotHz: 10, status: 'bounded-beta' })); return; }
      if (request.method !== 'GET' && request.method !== 'HEAD') { response.writeHead(405); response.end('Method not allowed'); return; }
      const requested = path.resolve(staticDir, `.${pathname}`);
      if (pathname.includes('\0') || requested !== staticDir && !requested.startsWith(staticDir + path.sep)) { response.writeHead(403); response.end('Forbidden'); return; }
      let filename = requested;
      try { const stat = await fs.stat(filename); if (stat.isDirectory()) filename = path.join(filename, 'index.html'); }
      catch { if (path.extname(pathname)) { response.writeHead(404); response.end('Not found'); return; } filename = path.join(staticDir, 'index.html'); }
      let stat;
      try { stat = await fs.stat(filename); } catch { response.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' }); response.end('YUGA arena server is running. Build the client or connect through the YUGA website.'); return; }
      if (!stat.isFile()) { response.writeHead(404); response.end('Not found'); return; }
      response.writeHead(200, { 'Content-Type': mime[path.extname(filename)] ?? 'application/octet-stream', 'Content-Length': stat.size, 'Cache-Control': path.extname(filename) === '.html' ? 'no-cache' : 'public, max-age=3600' });
      if (request.method === 'HEAD') response.end(); else createReadStream(filename).on('error', () => response.destroy()).pipe(response);
    })().catch(() => { if (!response.headersSent) response.writeHead(500); response.end('Server error'); });
  });
  const wss = new WebSocketServer({ server: http, path: '/ws', maxPayload: 2048, perMessageDeflate: false });
  const send = (socket: WebSocket, message: ServerMessage) => { if (socket.readyState === WebSocket.OPEN && socket.bufferedAmount < 750_000) socket.send(JSON.stringify(message)); };
  const fail = (socket: WebSocket, message: string) => send(socket, { type: 'error', message });
  wss.on('connection', socket => {
    if (contexts.size >= 96) { socket.close(1013, 'Arena server capacity reached'); return; }
    const context: { room?: ArenaRoom; id?: string; alive: boolean; windowAt: number; count: number; invalid: number } = { alive: true, windowAt: Date.now(), count: 0, invalid: 0 };
    contexts.set(socket, context);
    const timeout = setTimeout(() => { if (!context.room) socket.close(1008, 'Join a match first'); }, 10_000);
    socket.on('pong', () => { context.alive = true; });
    socket.on('error', () => { /* Close releases only this transport's identity. */ });
    socket.on('message', (data, binary) => {
      const now = Date.now();
      if (now - context.windowAt >= 1000) { context.windowAt = now; context.count = 0; }
      if (++context.count > 100) { socket.close(1008, 'Input rate limit'); return; }
      let message: ClientMessage | null;
      try { message = binary ? null : parseArenaMessage(JSON.parse(data.toString())); } catch { message = null; }
      if (!message) { fail(socket, 'Invalid arena message'); if (++context.invalid >= 5) socket.close(1008, 'Invalid arena messages'); return; }
      if (message.type === 'join') {
        if (context.room) { fail(socket, 'Already joined'); return; }
        if (message.token && !message.room) { fail(socket, 'A reconnect token requires its room code'); return; }
        let room = message.room ? rooms.get(message.room) : undefined;
        if (message.room && !room) { fail(socket, 'Room unavailable. Create a new match.'); return; }
        const existing = message.token && room ? room.identities.get(hash(message.token)) : undefined;
        if (message.token && !existing) { fail(socket, 'Reconnect token does not belong to this room'); return; }
        if (room?.sim.phase === 'finished' && !existing) { fail(socket, 'This match has ended. Create a new match.'); return; }
        if (!room) {
          if (rooms.size >= 32) { fail(socket, 'Arena room limit reached'); return; }
          const code = randomBytes(4).toString('hex').toUpperCase();
          room = { sim: new ArenaSimulation({ room: code, seed: randomBytes(4).readUInt32LE(0), ...options.simulation }), identities: new Map(), clients: new Map(), lastActive: now, finishedAt: null };
          rooms.set(code, room);
        }
        let token = message.token;
        const playerId = existing?.id ?? randomBytes(8).toString('hex');
        let actor;
        try { actor = room.sim.addPlayer(playerId, message.name, existing?.heroId ?? message.heroId, existing?.team); }
        catch (error) { fail(socket, error instanceof Error && ['ROOM_FULL', 'TEAM_FULL'].includes(error.message) ? 'All six player slots are occupied or reserved for reconnecting players' : 'Could not join this match'); return; }
        if (existing) { const previous = room.clients.get(playerId); if (previous) previous.close(4001, 'Reconnected elsewhere'); existing.lastSeen = now; }
        else { token = randomBytes(24).toString('hex'); room.identities.set(hash(token), { id: playerId, heroId: actor.heroId, team: actor.team, lastSeen: now }); }
        room.clients.set(playerId, socket); room.lastActive = now;
        context.room = room; context.id = playerId; clearTimeout(timeout);
        send(socket, { type: 'welcome', protocol: YUGA_PROTOCOL, id: playerId, token: token!, room: room.sim.room, snapshot: room.sim.snapshot() });
        return;
      }
      const room = context.room;
      if (!room || !context.id || room.clients.get(context.id) !== socket) { fail(socket, 'Join a match first'); return; }
      const inputTime = performance.now(); advance(inputTime);
      if (message.type === 'input') { if (room.sim.input(context.id, message)) inputTimes.set(context.id, inputTime); }
      else send(socket, room.sim.command(context.id, message));
    });
    socket.on('close', () => {
      clearTimeout(timeout); contexts.delete(socket);
      if (context.room && context.id && context.room.clients.get(context.id) === socket) {
        const room = context.room; room.clients.delete(context.id); room.sim.removePlayer(context.id); room.lastActive = Date.now(); inputTimes.delete(context.id);
        for (const identity of room.identities.values()) if (identity.id === context.id) identity.lastSeen = Date.now();
      }
    });
  });
  const simulationTimer = setInterval(() => advance(performance.now()), options.tickMs ?? 50);
  const cleanupTimer = setInterval(() => {
    const now = Date.now();
    for (const [socket, context] of contexts) { if (!context.alive) { socket.terminate(); continue; } context.alive = false; socket.ping(); }
    for (const [code, room] of rooms) {
      for (const [digest, identity] of room.identities) if (!room.clients.has(identity.id) && now - identity.lastSeen > idleMs) { room.sim.releasePlayer(identity.id); room.identities.delete(digest); }
      if (!room.clients.size && now - room.lastActive > idleMs || room.finishedAt !== null && now - room.finishedAt > 180_000) { for (const socket of room.clients.values()) socket.close(1000, 'Match archived. Create a new match.'); rooms.delete(code); }
    }
  }, Math.min(15_000, Math.max(100, idleMs)));
  await new Promise<void>((resolve, reject) => { http.once('error', reject); http.listen(options.port ?? 3005, options.host ?? '0.0.0.0', () => { http.off('error', reject); resolve(); }); });
  return {
    http, wss, rooms, address: http.address(),
    async close() {
      clearInterval(simulationTimer); clearInterval(cleanupTimer);
      for (const socket of wss.clients) socket.terminate();
      await new Promise<void>(resolve => wss.close(() => resolve()));
      await new Promise<void>((resolve, reject) => http.close(error => error ? reject(error) : resolve()));
      rooms.clear(); inputTimes.clear();
    },
  };
}
