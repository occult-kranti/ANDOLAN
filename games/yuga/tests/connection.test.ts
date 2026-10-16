import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { online, practice, type ArenaConnection, type Callbacks } from '../client/connection';
import { ArenaSimulation } from '../shared/simulation';
import { YUGA_PROTOCOL } from '../shared/types';
import type { ArenaCommand, ArenaInput, ArenaSnapshot } from '../shared/types';

class Socket extends EventTarget {
  static OPEN = 1;
  static all: Socket[] = [];
  readyState = 0;
  sent: unknown[] = [];
  constructor(readonly url: string) { super(); Socket.all.push(this); }
  send(value: string) { this.sent.push(JSON.parse(value)); }
  open() { this.readyState = 1; this.dispatchEvent(new Event('open')); }
  message(value: unknown) { const message = new Event('message'); Object.assign(message, { data: JSON.stringify(value) }); this.dispatchEvent(message); }
  close(code = 1000) { this.readyState = 3; const event = new Event('close'); Object.assign(event, { code }); this.dispatchEvent(event); }
}
let callbacks: Callbacks;
let connections: ArenaConnection[];
let saved: Map<string, string>;
let clock: number;
const snapshot = (): ArenaSnapshot => new ArenaSimulation({ botsPerTeam: 0 }).snapshot();
const intent = (seq: number, moveZ = 0): ArenaInput => ({ type: 'input', seq, moveX: 0, moveZ, yaw: 0, pitch: 0, fire: false, jump: false });
const upgrade: ArenaCommand = { type: 'command', id: 'purchase-1', action: 'upgrade', upgrade: 'power' };
function connect() { const connection = online({ url: 'ws://localhost:3002/ws', heroId: 'rama', name: 'Tester', room: '' }, callbacks); connections.push(connection); return connection; }
function welcome(socket = Socket.all.at(-1)!, room = 'ARENA01', token = 'saved-token') {
  socket.open(); socket.message({ type: 'welcome', protocol: YUGA_PROTOCOL, id: 'human', room, token, snapshot: snapshot() }); return socket;
}
function local() { const connection = practice('rama', 'Tester', callbacks); connections.push(connection); return connection; }
function latest() { return vi.mocked(callbacks.snapshot).mock.calls.at(-1)![0]; }

beforeEach(() => {
  vi.useFakeTimers(); vi.setSystemTime(0); clock = 0; vi.spyOn(performance, 'now').mockImplementation(() => clock);
  Socket.all = []; connections = []; saved = new Map();
  vi.stubGlobal('window', { setInterval: globalThis.setInterval, setTimeout: globalThis.setTimeout });
  vi.stubGlobal('WebSocket', Socket);
  vi.stubGlobal('sessionStorage', { getItem: (key: string) => saved.get(key) ?? null, setItem: (key: string, value: string) => saved.set(key, value) });
  callbacks = { snapshot: vi.fn(), welcome: vi.fn(), status: vi.fn(), result: vi.fn(), error: vi.fn() };
});
afterEach(() => { connections.forEach(connection => connection.close()); vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });

describe('YUGA browser transport lifecycle', () => {
  it('treats replacement close4001 as terminal without reconnecting or retaining timers', async () => {
    const connection = connect(), socket = welcome();
    socket.close(4001);
    expect(callbacks.status).toHaveBeenLastCalledWith('This match is active in another tab', false);
    connection.input(intent(1, 1)); connection.command(upgrade); connection.reconnect!();
    await vi.advanceTimersByTimeAsync(30000);
    expect(Socket.all).toHaveLength(1); expect(vi.getTimerCount()).toBe(0);
    expect(socket.sent.filter(message => (message as { type: string }).type === 'command')).toHaveLength(0);
  });

  it('gates both movement and commands while snapshots are stale, then recovers on a fresh snapshot', async () => {
    const connection = connect(), socket = welcome(); connection.input(intent(1, 1));
    const before = socket.sent.length;
    await vi.advanceTimersByTimeAsync(3000);
    connection.input(intent(2, 1)); connection.command(upgrade);
    expect(socket.sent).toHaveLength(before);
    expect(callbacks.status).toHaveBeenLastCalledWith('Waiting for server · controls paused', false);
    socket.message({ type: 'snapshot', snapshot: snapshot() });
    connection.input(intent(3, 1)); connection.command(upgrade);
    expect(socket.sent.slice(-2)).toEqual([intent(3, 1), upgrade]);
    expect(callbacks.status).toHaveBeenLastCalledWith('Online · ARENA01', true);
  });

  it('retains the room/token and exact command IDs across repeated reconnects without replaying actions', async () => {
    const connection = connect(), first = welcome(); connection.command(upgrade);
    connection.reconnect!(); const second = welcome();
    expect(second.sent).toEqual([{ type: 'join', protocol: YUGA_PROTOCOL, heroId: 'rama', name: 'Tester', room: 'ARENA01', token: 'saved-token' }]);
    connection.command(upgrade); expect(second.sent.at(-1)).toEqual(upgrade);
    first.message({ type: 'result', id: upgrade.id, ok: true, code: 'UPGRADED' });
    expect(callbacks.result).not.toHaveBeenCalled();
    second.message({ type: 'result', id: upgrade.id, ok: true, code: 'UPGRADED' });
    expect(callbacks.result).toHaveBeenCalledExactlyOnceWith({ type: 'result', id: upgrade.id, ok: true, code: 'UPGRADED' });
    second.close(1006); connection.reconnect!(); const third = welcome();
    await vi.advanceTimersByTimeAsync(2000);
    expect(Socket.all).toHaveLength(3); expect(third.sent).toHaveLength(1);
    expect(saved.get('yuga.identity.v1:ws://localhost:3002/ws:ARENA01')).toBe('saved-token');
  });

  it('cleans the freshness timer after a terminal version mismatch', async () => {
    const connection = connect(), socket = Socket.all[0]; socket.open();
    socket.message({ type: 'welcome', protocol: 999, id: 'human', room: 'ARENA01', token: 'token', snapshot: snapshot() });
    await vi.advanceTimersByTimeAsync(10000); connection.reconnect!();
    expect(Socket.all).toHaveLength(1); expect(vi.getTimerCount()).toBe(0);
    expect(callbacks.welcome).not.toHaveBeenCalled(); expect(callbacks.error).toHaveBeenCalledTimes(1);
  });

  it('stops retry/freshness work and ignores stale socket events after explicit close', async () => {
    const connection = connect(), socket = welcome(); socket.close(1006); connection.close();
    const count = vi.mocked(callbacks.snapshot).mock.calls.length;
    socket.message({ type: 'snapshot', snapshot: snapshot() });
    await vi.advanceTimersByTimeAsync(30000);
    expect(Socket.all).toHaveLength(1); expect(vi.getTimerCount()).toBe(0);
    expect(callbacks.snapshot).toHaveBeenCalledTimes(count);
  });
});

describe('YUGA local fixed-step transport', () => {
  it('retains fractional time and caps a delayed callback without an unbounded catch-up loop', async () => {
    local(); clock = 275; await vi.advanceTimersByTimeAsync(50);
    expect(latest().time).toBeCloseTo(.25); expect(latest().tick).toBe(5);
    clock = 300; await vi.advanceTimersByTimeAsync(50);
    expect(latest().time).toBeCloseTo(.3); expect(latest().tick).toBe(6);
    clock = 5300; await vi.advanceTimersByTimeAsync(50);
    expect(latest().time).toBeCloseTo(1.3); expect(latest().tick).toBe(26);
    await vi.advanceTimersByTimeAsync(50); expect(latest().tick).toBe(26);
  });

  it('does not apply a newly pressed movement input retroactively over a delayed frame', async () => {
    const connection = local(); const before = latest().actors.find(actor => actor.id === 'local-player')!;
    clock = 500; connection.input(intent(1, 1)); await vi.advanceTimersByTimeAsync(50);
    const afterStall = latest().actors.find(actor => actor.id === 'local-player')!;
    expect(afterStall.x).toBe(before.x); expect(afterStall.z).toBe(before.z);
    clock = 550; await vi.advanceTimersByTimeAsync(50);
    expect(latest().actors.find(actor => actor.id === 'local-player')!.z).toBeGreaterThan(before.z);
  });

  it('does not catch up paused wall time, blocks paused movement, and supports idempotent forge purchases', async () => {
    const connection = local(); connection.pause(true); const before = latest();
    clock = 5000; connection.input(intent(1, 1)); await vi.advanceTimersByTimeAsync(500);
    expect(latest().time).toBe(before.time);
    connection.command(upgrade); const upgraded = latest().actors.find(actor => actor.id === 'local-player')!;
    connection.command(upgrade); const replayed = latest().actors.find(actor => actor.id === 'local-player')!;
    expect(upgraded.upgrades.power).toBe(1); expect(replayed.credits).toBe(upgraded.credits);
    connection.pause(false); clock += 50; await vi.advanceTimersByTimeAsync(50);
    expect(latest().time).toBeCloseTo(.05); expect(latest().actors.find(actor => actor.id === 'local-player')!.z).toBe(upgraded.z);
    connection.close(); expect(vi.getTimerCount()).toBe(0);
  });
});
