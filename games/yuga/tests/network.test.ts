import { afterEach, describe, expect, it } from 'vitest';
import { WebSocket } from 'ws';
import { createArenaServer, parseArenaMessage } from '../server/server.js';
import type { ArenaJoin, ServerMessage } from '../shared/types.js';
import { YUGA_PROTOCOL } from '../shared/types.js';
import { ArenaSimulation } from '../shared/simulation.js';

type Server = Awaited<ReturnType<typeof createArenaServer>>;
type Welcome = Extract<ServerMessage, { type: 'welcome' }>;
const servers: Server[] = [];
const sockets: WebSocket[] = [];
const join: ArenaJoin = { type: 'join', protocol: YUGA_PROTOCOL, name: 'Aadi', heroId: 'rama' };
const intent = { type: 'input', seq: 1, moveX: 1, moveZ: 0, yaw: Math.PI / 2, pitch: 0, fire: false, jump: false };
async function start(options: Parameters<typeof createArenaServer>[0] = {}) {
  const server = await createArenaServer({ port: 0, host: '127.0.0.1', ...options }); servers.push(server);
  const address = server.address; if (!address || typeof address === 'string') throw new Error('Missing listener');
  return { server, url: `ws://127.0.0.1:${address.port}/ws`, http: `http://127.0.0.1:${address.port}` };
}
async function client(url: string) {
  const socket = new WebSocket(url); sockets.push(socket);
  const queue: ServerMessage[] = [];
  const listeners = new Set<() => void>();
  socket.on('message', data => { queue.push(JSON.parse(data.toString()) as ServerMessage); for (const listener of listeners) listener(); });
  const closed = new Promise<number>(resolve => socket.once('close', code => resolve(code)));
  await new Promise<void>((resolve, reject) => { socket.once('open', resolve); socket.once('error', reject); });
  function next<T extends ServerMessage>(predicate: (message: ServerMessage) => message is T): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => { listeners.delete(check); reject(new Error('Expected arena frame did not arrive')); }, 4000);
      function check() { const index = queue.findIndex(predicate); if (index < 0) return; const message = queue.splice(index, 1)[0] as T; clearTimeout(timeout); listeners.delete(check); resolve(message); }
      listeners.add(check); check();
    });
  }
  return { socket, closed, next, send(value: unknown) { socket.send(JSON.stringify(value)); }, welcome: () => next((message): message is Welcome => message.type === 'welcome') };
}
afterEach(async () => { for (const socket of sockets.splice(0)) socket.terminate(); await Promise.all(servers.splice(0).map(server => server.close())); });

describe('real arena WebSocket authority', () => {
  it('synchronizes one physical gold claim and preserves it through token resume without trusting old snapshots', async () => {
    const { url, server } = await start(); const host = await client(url); host.send(join); const welcome = await host.welcome();
    const guest = await client(url); guest.send({ ...join, name: 'Noor', room: welcome.room }); const peer = await guest.welcome();
    expect(peer.snapshot.neutrals).toHaveLength(4); expect(peer.snapshot.goldShards).toEqual([]); expect(peer.protocol).toBe(YUGA_PROTOCOL);
    const sim = server.rooms.get(welcome.room)!.sim, actor = sim.actors.get(welcome.id)!; Object.assign(actor, { x: 0, z: -6 });
    if (!(sim instanceof ArenaSimulation)) throw new Error('Default arena authority must remain the planar simulation');
    sim.goldShards.push({ id: 'gold-network', sourceId: 'fixture-lane', x: 0, z: 0, y: 1.2, value: 8, originTeam: actor.team, createdAt: sim.time, expiresAt: sim.time + 12 });
    host.send({ ...intent, moveX: 0, yaw: 0, fire: true });
    const claimed = await guest.next((message): message is Extract<ServerMessage, { type: 'snapshot' }> => message.type === 'snapshot' && message.snapshot.events.some(event => event.type === 'gold' && event.targetId === 'gold-network'));
    expect(claimed.snapshot.actors.find(a => a.id === welcome.id)!.credits).toBe(188); expect(claimed.snapshot.goldShards).toEqual([]);
    claimed.snapshot.actors.find(a => a.id === welcome.id)!.credits = 99999;
    host.send({ ...intent, moveX: 0, yaw: 0, fire: true }); host.send({ type: 'command', id: 'steal-claim', action: 'reward', amount: 99999 });
    await host.next((message): message is Extract<ServerMessage, { type: 'error' }> => message.type === 'error');
    host.socket.close(); await host.closed;
    const resumed = await client(url); resumed.send({ ...join, room: welcome.room, token: welcome.token }); const back = await resumed.welcome();
    expect(back.id).toBe(welcome.id); expect(back.snapshot.actors.find(a => a.id === welcome.id)!.credits).toBe(188); expect(back.snapshot.events.filter(event => event.type === 'gold' && event.targetId === 'gold-network')).toHaveLength(1);
  });
  it('parses finite intent only and rejects forged coordinates, rewards and unknown actions', () => {
    expect(parseArenaMessage(join)).toEqual(join); expect(parseArenaMessage(intent)).toEqual(intent);
    for (const invalid of [{ ...intent, x: 80 }, { ...intent, credits: 9999 }, { ...intent, moveX: Infinity }, { ...intent, pitch: NaN }, { ...intent, seq: 1.5 }, { ...join, heroId: 'unknown' }, { ...join, protocol: YUGA_PROTOCOL - 1 }, { type: 'command', id: 'x', action: 'ability', slot: 9 }, { type: 'command', id: 'x', action: 'reward', amount: 999 }]) expect(parseArenaMessage(invalid)).toBeNull();
  });

  it('shares authoritative movement and charges an idempotent upgrade once across two sockets', async () => {
    const { url, http } = await start(); const host = await client(url); host.send(join); const welcome = await host.welcome();
    const guest = await client(url); guest.send({ ...join, name: 'Noor', room: welcome.room }); const other = await guest.welcome();
    expect(other.id).not.toBe(welcome.id); expect(other.snapshot.actors.filter(actor => actor.kind === 'hero')).toHaveLength(6);
    const purchase = { type: 'command', id: 'power-once', action: 'upgrade', upgrade: 'power' };
    host.send(purchase); expect(await host.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result' && message.id === purchase.id)).toMatchObject({ ok: true, code: 'UPGRADED' });
    host.send(purchase); await host.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result' && message.id === purchase.id);
    host.send(intent);
    const moved = await guest.next((message): message is Extract<ServerMessage, { type: 'snapshot' }> => message.type === 'snapshot' && message.snapshot.actors.some(actor => actor.id === welcome.id && actor.lastInputSeq === 1 && actor.x > .1));
    expect(moved.snapshot.actors.find(actor => actor.id === welcome.id)).toMatchObject({ credits: 60, upgrades: { power: 1 } });
    expect(await (await fetch(`${http}/health`)).json()).toMatchObject({ game: 'yuga', protocol: 2, connected: 2, simulationHz: 20, snapshotHz: 10 });
  });

  it('resumes only the token owner, preserves progress and displaces an old transport without a reconnect race', async () => {
    const { server, url } = await start(); const first = await client(url); first.send(join); const welcome = await first.welcome();
    first.send({ type: 'command', id: 'purchase', action: 'upgrade', upgrade: 'vitality' }); await first.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result');
    const replacement = await client(url); replacement.send({ ...join, heroId: 'ravana', room: welcome.room, token: welcome.token }); const resumed = await replacement.welcome();
    expect(await first.closed).toBe(4001); expect(resumed.id).toBe(welcome.id);
    expect(resumed.snapshot.actors.find(actor => actor.id === welcome.id)).toMatchObject({ heroId: 'rama', credits: 80, upgrades: { vitality: 1 }, connected: true, bot: false });
    replacement.send({ ...intent, seq: 0 });
    await replacement.next((message): message is Extract<ServerMessage, { type: 'snapshot' }> => message.type === 'snapshot' && message.snapshot.actors.some(actor => actor.id === welcome.id && actor.lastInputSeq === 0 && actor.connected));
    replacement.socket.close(); await replacement.closed;
    expect(server.rooms.get(welcome.room)!.sim.actors.get(welcome.id)).toMatchObject({ connected: false, bot: true, upgrades: { vitality: 1 } });
    const third = await client(url); third.send({ ...join, room: welcome.room, token: welcome.token }); const restored = await third.welcome(); expect(restored.id).toBe(welcome.id);
    expect(restored.snapshot.actors.find(actor => actor.id === welcome.id)?.upgrades.vitality).toBe(1);
  });

  it('rejects orphan and foreign tokens before allocation, and caps each room at six human identities', async () => {
    const { server, url } = await start(); const invalid = await client(url); invalid.send({ ...join, token: 'a'.repeat(48) });
    await invalid.next((message): message is Extract<ServerMessage, { type: 'error' }> => message.type === 'error'); expect(server.rooms.size).toBe(0);
    const host = await client(url); host.send(join); const welcome = await host.welcome();
    invalid.send({ ...join, room: welcome.room, token: 'b'.repeat(48) }); await invalid.next((message): message is Extract<ServerMessage, { type: 'error' }> => message.type === 'error');
    expect(server.rooms.get(welcome.room)!.identities.size).toBe(1);
    for (let i = 1; i < 6; i++) { const peer = await client(url); peer.send({ ...join, room: welcome.room }); await peer.welcome(); }
    const extra = await client(url); extra.send({ ...join, room: welcome.room });
    expect(await extra.next((message): message is Extract<ServerMessage, { type: 'error' }> => message.type === 'error')).toMatchObject({ message: expect.stringContaining('six player slots') });
    expect(server.rooms.get(welcome.room)!.sim.snapshot().actors.filter(actor => actor.kind === 'hero')).toHaveLength(6);
    expect(server.rooms.get(welcome.room)!.identities.size).toBe(6);
  });

  it('resumes a real pending telegraph with one release and the original command receipt', async () => {
    const { url } = await start(); const host = await client(url); host.send(join); const welcome = await host.welcome();
    const command = { type: 'command', id: 'resumed-ultimate', action: 'ability', slot: 2 };
    host.send(command); await host.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result' && message.id === command.id);
    host.socket.close(); await host.closed;
    const resumed = await client(url); resumed.send({ ...join, room: welcome.room, token: welcome.token }); const ready = await resumed.welcome();
    expect(ready.id).toBe(welcome.id); expect(ready.snapshot.actors.find(actor => actor.id === welcome.id)?.cast?.mechanic).toBe('dawn-volley');
    resumed.send(command); expect(await resumed.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result' && message.id === command.id)).toMatchObject({ ok: true, code: 'ABILITY_CAST' });
    const released = await resumed.next((message): message is Extract<ServerMessage, { type: 'snapshot' }> => message.type === 'snapshot' && message.snapshot.events.filter(event => event.actorId === welcome.id && event.type === 'shot').length === 3);
    expect(released.snapshot.actors.find(actor => actor.id === welcome.id)?.cast).toBeUndefined();
    expect(released.snapshot.actors.find(actor => actor.id === welcome.id)?.cooldowns[2]).toBeGreaterThan(40);
  });

  it('bounds invalid messages, packet size and per-socket input rate', async () => {
    const { url } = await start();
    const malformed = await client(url); for (let i = 0; i < 5; i++) malformed.send({ ...intent, health: 999 }); expect(await malformed.closed).toBe(1008);
    const oversized = await client(url); oversized.socket.send('x'.repeat(3000)); expect(await oversized.closed).toBe(1009);
    const flooding = await client(url); for (let i = 0; i < 101; i++) flooding.send({ ...intent, seq: i }); expect(await flooding.closed).toBe(1008);
  });

  it('expires abandoned rooms and reconnect reservations without retaining leaked identities', async () => {
    const { server, url } = await start({ idleRoomMs: 100 }); const host = await client(url); host.send(join); const welcome = await host.welcome(); host.socket.close(); await host.closed;
    await new Promise(resolve => setTimeout(resolve, 350)); expect(server.rooms.has(welcome.room)).toBe(false);
    const old = await client(url); old.send({ ...join, room: welcome.room, token: welcome.token });
    expect(await old.next((message): message is Extract<ServerMessage, { type: 'error' }> => message.type === 'error')).toMatchObject({ message: expect.stringContaining('Room unavailable') });
  });

  it('publishes a finite final result and makes replay a fresh independent match', async () => {
    const { url } = await start({ simulation: { duration: 1 } }); const host = await client(url); host.send(join); const welcome = await host.welcome();
    const result = await host.next((message): message is Extract<ServerMessage, { type: 'snapshot' }> => message.type === 'snapshot' && message.snapshot.phase === 'finished');
    expect(result.snapshot.time).toBe(1); expect(result.snapshot.winner).toBe('draw');
    host.send({ type: 'command', id: 'after-end', action: 'ability', slot: 0 });
    expect(await host.next((message): message is Extract<ServerMessage, { type: 'result' }> => message.type === 'result')).toMatchObject({ ok: false, code: 'MATCH_FINISHED' });
    const replay = await client(url); replay.send(join); const next = await replay.welcome(); expect(next.room).not.toBe(welcome.room); expect(next.snapshot.time).toBe(0); expect(next.snapshot.phase).toBe('playing');
  });
});
