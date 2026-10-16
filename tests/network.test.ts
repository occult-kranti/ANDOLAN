import { afterEach, describe, expect, it } from 'vitest';
import { promises as fs } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { WebSocket } from 'ws';
import { createGameServer } from '../apps/server/src/server.js';
import type { ServerMessage, WelcomeMessage, Snapshot, ResultMessage } from '../packages/protocol/src/index.js';

type RunningServer = Awaited<ReturnType<typeof createGameServer>>;
const servers: RunningServer[] = [];
const sockets: WebSocket[] = [];
const dirs: string[] = [];

async function start(dataDir?: string) {
  const dir = dataDir ?? await fs.mkdtemp(path.join(tmpdir(), 'andolan-network-'));
  if (!dirs.includes(dir)) dirs.push(dir);
  const server = await createGameServer({ port: 0, host: '127.0.0.1', dataDir: dir, checkpointMs: 100_000 });
  servers.push(server);
  const address = server.address;
  if (!address || typeof address === 'string') throw new Error('No server address');
  return { server, dataDir: dir, url: `ws://127.0.0.1:${address.port}/ws`, http: `http://127.0.0.1:${address.port}` };
}

async function peer(url: string) {
  const ws = new WebSocket(url); sockets.push(ws);
  const queue: ServerMessage[] = [];
  const listeners = new Set<() => void>();
  ws.on('message', raw => { queue.push(JSON.parse(raw.toString()) as ServerMessage); for (const notify of listeners) notify(); });
  await new Promise<void>((resolve, reject) => { ws.once('open', resolve); ws.once('error', reject); });
  return {
    ws, send: (value: unknown) => ws.send(JSON.stringify(value)),
    next<T extends ServerMessage>(predicate: (m: ServerMessage) => boolean, timeout = 3000): Promise<T> {
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => { listeners.delete(check); reject(new Error('Timed out waiting for server message')); }, timeout);
        function check() {
          const index = queue.findIndex(predicate);
          if (index >= 0) { clearTimeout(timer); listeners.delete(check); resolve(queue.splice(index, 1)[0] as T); }
        }
        listeners.add(check); check();
      });
    },
  };
}

afterEach(async () => {
  for (const ws of sockets.splice(0)) ws.terminate();
  for (const server of servers.splice(0)) await server.close();
  for (const dir of dirs.splice(0)) await fs.rm(dir, { recursive: true, force: true });
});

describe('real WebSocket room service', () => {
  it('synchronizes two independent clients and serializes concurrent vehicle seats', async () => {
    const running = await start(), a = await peer(running.url), b = await peer(running.url);
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const wa = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    b.send({ type: 'join', mode: 'private', room: wa.room, name: 'Noor' });
    const wb = await b.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(wb.room).toBe(wa.room); expect(wb.playerId).not.toBe(wa.playerId);
    a.send({ type: 'command', id: 'enter-a', action: 'enter', target: 'compact-01' });
    b.send({ type: 'command', id: 'enter-b', action: 'enter', target: 'compact-01' });
    expect((await a.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    expect((await b.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    const snapshotA = await a.next<Snapshot>(m => m.type === 'snapshot' && m.vehicles[0]!.occupants.filter(Boolean).length === 2);
    const snapshotB = await b.next<Snapshot>(m => m.type === 'snapshot' && m.tick === snapshotA.tick);
    expect(snapshotB).toEqual(snapshotA);
    expect(snapshotA.vehicles[0]!.occupants[0]).toBe(wa.playerId);
    expect(snapshotA.vehicles[0]!.occupants[1]).toBe(wb.playerId);
    a.send({ type: 'input', seq: 2, moveX: 0, moveZ: 0, forward: 1, turn: 0 });
    const moved = await b.next<Snapshot>(m => m.type === 'snapshot' && m.vehicles[0]!.speed > 0);
    expect(moved.vehicles[0]!.x).toBeGreaterThan(-52);
    expect(JSON.stringify(moved)).not.toContain(wa.token);
    a.ws.close();
    await b.next<Snapshot>(m => m.type === 'snapshot' && m.vehicles[0]!.occupants[0] === null && m.vehicles[0]!.occupants[1] === wb.playerId);
    b.send({ type: 'command', id: 'take-wheel', action: 'take_wheel' });
    expect((await b.next<ResultMessage>(m => m.type === 'result' && m.commandId === 'take-wheel')).code).toBe('DRIVER_CLAIMED');
    const transferred = await b.next<Snapshot>(m => m.type === 'snapshot' && m.vehicles[0]!.occupants[0] === wb.playerId);
    expect(transferred.vehicles[0]!.speed).toBe(0);
  });

  it('rejects forged coordinates, duplicate command effects and unauthenticated control', async () => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'command', id: 'unjoined', action: 'interact' });
    expect((await a.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('JOIN_REQUIRED');
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const welcome = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    a.send({ type: 'input', seq: 1, moveX: 0, moveZ: 0, forward: 0, turn: 0, x: 90 });
    expect((await a.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('INVALID_MESSAGE');
    const enter = { type: 'command', id: 'same-id', action: 'enter', target: 'compact-01' };
    a.send(enter); const first = await a.next<ResultMessage>(m => m.type === 'result');
    a.send({ ...enter, action: 'exit' }); const repeated = await a.next<ResultMessage>(m => m.type === 'result');
    expect(first).toEqual(repeated);
    expect(running.server.rooms.get(welcome.room)!.sim.players.get(welcome.playerId)!.vehicleId).toBe('compact-01');
  });

  it('reconnects with a bearer token, releases seats, and rejects cross-room tokens', async () => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const welcome = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    a.send({ type: 'command', id: 'seat', action: 'enter' }); await a.next(m => m.type === 'result');
    a.ws.close(); await new Promise<void>(resolve => a.ws.once('close', () => resolve()));
    const b = await peer(running.url);
    b.send({ type: 'join', mode: 'private', name: 'Aadi', room: welcome.room, token: welcome.token });
    const resumed = await b.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(welcome.playerId); expect(resumed.token).toBe(welcome.token);
    expect(resumed.snapshot.players).toHaveLength(1);
    expect(resumed.snapshot.vehicles[0]!.occupants).toEqual([null, null, null, null]);
    const stranger = await peer(running.url);
    stranger.send({ type: 'join', mode: 'private', name: 'Stranger', room: welcome.room, token: 'a'.repeat(48) });
    expect((await stranger.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('INVALID_TOKEN');
  });

  it('rejects roomless resume tokens without allocating orphan rooms and accepts a corrected join', async () => {
    const running = await start(), a = await peer(running.url);
    for (let i = 0; i < 12; i++) {
      a.send({ type: 'join', mode: i % 2 === 0 ? 'private' : 'public', name: 'Resume', token: 'a'.repeat(48) });
      expect((await a.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('ROOM_REQUIRED');
      expect(running.server.rooms.size).toBe(0);
    }
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const welcome = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(welcome.snapshot.players).toHaveLength(1);
    expect(running.server.rooms.size).toBe(1);
  });

  it('automatically matches newcomers to unfinished public districts while preserving explicit friend joins', async () => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'join', mode: 'public', name: 'First crew' });
    const first = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    running.server.rooms.get(first.room)!.sim.mission.complete = true;
    const newcomer = await peer(running.url);
    newcomer.send({ type: 'join', mode: 'public', name: 'New arrival' });
    const fresh = await newcomer.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(fresh.room).not.toBe(first.room); expect(fresh.snapshot.mission.complete).toBe(false);
    const friend = await peer(running.url);
    friend.send({ type: 'join', mode: 'public', room: first.room, name: 'Invited friend' });
    const joined = await friend.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(joined.room).toBe(first.room); expect(joined.snapshot.mission.complete).toBe(true);
  });

  it('persists canonical progress atomically and restores after an actual server restart', async () => {
    const running = await start(), a = await peer(running.url);
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const welcome = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    a.send({ type: 'command', id: 'keys', action: 'interact', target: 'garage' });
    expect((await a.next<ResultMessage>(m => m.type === 'result')).ok).toBe(true);
    await running.server.checkpoint();
    const saved = await fs.readFile(path.join(running.dataDir, `${welcome.room}.json`), 'utf8');
    expect(saved).not.toContain(welcome.token);
    expect((await fs.readdir(running.dataDir)).some(name => name.endsWith('.tmp'))).toBe(false);
    servers.splice(servers.indexOf(running.server), 1); await running.server.close();
    const restarted = await start(running.dataDir), b = await peer(restarted.url);
    b.send({ type: 'join', mode: 'private', name: 'Aadi', room: welcome.room, token: welcome.token });
    const resumed = await b.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(resumed.playerId).toBe(welcome.playerId); expect(resumed.snapshot.mission.stage).toBe('car');
    b.send({ type: 'command', id: 'keys', action: 'interact', target: 'garage' });
    expect((await b.next<ResultMessage>(m => m.type === 'result')).code).toBe('STAGE_COMPLETE');
    expect(restarted.server.rooms.get(welcome.room)!.sim.mission.revision).toBe(1);
  });

  it('enforces private capacity, separates public state and serves health without secrets', async () => {
    const running = await start(); let code = '';
    for (let i = 0; i < 5; i++) {
      const p = await peer(running.url); p.send({ type: 'join', mode: 'private', name: `Player ${i}`, ...(code ? { room: code } : {}) });
      if (i < 4) { const w = await p.next<WelcomeMessage>(m => m.type === 'welcome'); code = w.room; }
      else expect((await p.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('ROOM_FULL');
    }
    const p = await peer(running.url);
    p.send({ type: 'join', mode: 'public', room: code, name: 'Public' });
    expect((await p.next<Extract<ServerMessage, { type: 'error' }>>(m => m.type === 'error')).code).toBe('ROOM_NOT_FOUND');
    p.send({ type: 'join', mode: 'public', name: 'Public' });
    const w = await p.next<WelcomeMessage>(m => m.type === 'welcome');
    expect(w.room).not.toBe(code); expect(w.mode).toBe('public');
    const health = await fetch(`${running.http}/health`).then(r => r.json());
    expect(health).toMatchObject({ ok: true, connected: 5, publicStatus: 'development-sandbox' });
  });

  it('does not commit a pending ballot during an actual graceful server shutdown', async () => {
    const running = await start(), a = await peer(running.url), b = await peer(running.url);
    a.send({ type: 'join', mode: 'private', name: 'Aadi' });
    const wa = await a.next<WelcomeMessage>(m => m.type === 'welcome');
    b.send({ type: 'join', mode: 'private', name: 'Noor', room: wa.room });
    await b.next<WelcomeMessage>(m => m.type === 'welcome');
    const sim = running.server.rooms.get(wa.room)!.sim;
    sim.command(wa.playerId, { type: 'command', id: 'keys', action: 'interact' });
    sim.command(wa.playerId, { type: 'command', id: 'car', action: 'enter' });
    const car = sim.vehicles.get('compact-01')!; car.x = 52; car.z = -48; sim.step();
    sim.command(wa.playerId, { type: 'command', id: 'exit', action: 'exit' });
    a.send({ type: 'command', id: 'ballot', action: 'choice', value: 'copy' });
    expect((await a.next<ResultMessage>(m => m.type === 'result' && m.commandId === 'ballot')).code).toBe('VOTE_RECORDED');
    servers.splice(servers.indexOf(running.server), 1); await running.server.close();
    const save = JSON.parse(await fs.readFile(path.join(running.dataDir, `${wa.room}.json`), 'utf8'));
    expect(save.simulation.mission.history).toHaveLength(0);
    expect(save.simulation.mission.stage).toBe('receipt');
  });

  it('holds sixteen real public WebSocket clients in one sandbox with authoritative snapshots', async () => {
    const running = await start();
    const peers = await Promise.all(Array.from({ length: 16 }, () => peer(running.url)));
    for (let i = 0; i < peers.length; i++) peers[i]!.send({ type: 'join', mode: 'public', name: `Test ${i}` });
    const welcomes = await Promise.all(peers.map(p => p.next<WelcomeMessage>(m => m.type === 'welcome')));
    expect(new Set(welcomes.map(w => w.room)).size).toBe(1);
    const snapshots = await Promise.all(peers.map(p => p.next<Snapshot>(m => m.type === 'snapshot' && m.players.length === 16)));
    expect(snapshots.every(s => s.players.filter(p => p.connected).length === 16)).toBe(true);
    expect(snapshots.every(s => JSON.stringify(s).length < 16_000)).toBe(true);
    const room = running.server.rooms.get(welcomes[0]!.room)!;
    expect(room.clients.size).toBe(16);
    const extra = await peer(running.url); extra.send({ type: 'join', mode: 'public', name: 'Next district' });
    expect((await extra.next<WelcomeMessage>(m => m.type === 'welcome')).room).not.toBe(welcomes[0]!.room);
  });
});
