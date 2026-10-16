import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { connectSolo, type Connection } from '../apps/client/src/connection';
import type { Snapshot } from '../packages/protocol/src/index';

class Visibility extends EventTarget { hidden = false; }
let now = 0, documentState: Visibility;
const connections: Connection[] = [];
const storage = new Map<string, string>();
const writes = vi.fn((key: string, value: string) => { storage.set(key, value); });

beforeEach(() => {
  vi.useFakeTimers(); now = 0; storage.clear(); writes.mockClear();
  vi.spyOn(performance, 'now').mockImplementation(() => now);
  documentState = new Visibility();
  vi.stubGlobal('document', documentState); vi.stubGlobal('window', new EventTarget());
  vi.stubGlobal('localStorage', { getItem: (key: string) => storage.get(key) ?? null, setItem: writes });
});
afterEach(() => {
  for (const connection of connections.splice(0)) connection.close();
  vi.clearAllTimers(); vi.restoreAllMocks(); vi.useRealTimers(); vi.unstubAllGlobals();
});
function start() {
  const interval = vi.spyOn(globalThis, 'setInterval');
  const callbacks = { snapshot: vi.fn<(snapshot: Snapshot) => void>(), welcome: vi.fn(), status: vi.fn(), error: vi.fn() };
  const connection = connectSolo('Aadi', callbacks, true); connections.push(connection);
  const timer = interval.mock.calls.at(-1)![0] as () => void;
  const state = () => callbacks.snapshot.mock.calls.at(-1)![0];
  const tick = (ms: number) => { now += ms; timer(); };
  const input = (seq: number, moveX = 0, forward = 0) => connection.input({ type: 'input', seq, moveX, moveZ: 0, forward, turn: 0 });
  return { connection, callbacks, state, tick, input };
}
const normal = Array<number>(20).fill(50), delayed = Array<number>(5).fill(200);

function walk(schedule: number[]) {
  const game = start(); let seq = 0; game.input(seq++, 1);
  for (const elapsed of schedule) { game.tick(elapsed); game.input(seq++, 1); }
  const state = game.state(); game.connection.close(); return state;
}
function driveAndCoast(schedule: number[]) {
  const game = start(); let seq = 0;
  game.connection.command({ type: 'command', id: 'enter-car', action: 'enter', target: 'compact-01' });
  expect(game.state().players[0]!.seat).toBe(0);
  game.input(seq++, 0, 1);
  for (const elapsed of schedule) { game.tick(elapsed); game.input(seq++, 0, 1); }
  const accelerating = game.state().vehicles[0]!.speed;
  game.input(seq++);
  for (const elapsed of schedule) { game.tick(elapsed); game.input(seq++); }
  const state = game.state(); game.connection.close(); return { state, accelerating };
}

describe('solo fixed-step wall clock', () => {
  it('walks the same distance in one second with ordinary or delayed callbacks', () => {
    const a = walk(normal), b = walk(delayed);
    expect(a.tick).toBe(20); expect(b.tick).toBe(20);
    expect(a.time).toBeCloseTo(1); expect(b.time).toBeCloseTo(1);
    expect(b.players[0]!.x).toBeCloseTo(a.players[0]!.x, 10);
    expect(b.players[0]!.x).toBeCloseTo(-55 + 3.8, 8);
  });
  it('preserves acceleration and coasting in wall time despite delayed callbacks', () => {
    const a = driveAndCoast(normal), b = driveAndCoast(delayed);
    expect(a.accelerating).toBeGreaterThan(5);
    expect(b.accelerating).toBeCloseTo(a.accelerating, 10);
    expect(b.state.tick).toBe(40);
    expect(b.state.vehicles[0]!.speed).toBeCloseTo(a.state.vehicles[0]!.speed, 10);
    expect(b.state.vehicles[0]!.speed).toBeLessThan(b.accelerating / 10);
    expect(b.state.vehicles[0]!.x).toBeCloseTo(a.state.vehicles[0]!.x, 10);
  });
  it('finishes elapsed time before accepting fresh input rather than backdating it', () => {
    const game = start(); const before = game.state().players[0]!.x;
    now += 200; game.input(1, 1);
    expect(game.state().tick).toBe(4);
    expect(game.state().players[0]!.x).toBe(before);
    game.tick(50);
    expect(game.state().players[0]!.x).toBeCloseTo(before + .19, 10);
  });
  it('caps a long stall to five steps, expires old intent and discards excess debt', () => {
    const game = start(); const before = game.state().players[0]!.x;
    game.input(10, 1); game.tick(5000);
    expect(game.state().tick).toBe(5); expect(game.state().time).toBeCloseTo(.25);
    expect(game.state().players[0]!.x).toBe(before);
    game.tick(0); expect(game.state().tick).toBe(5);
    game.input(9, 1); game.tick(50);
    expect(game.state().players[0]!.x).toBe(before);
    expect(game.state().players[0]!.lastInputSeq).toBe(10);
    game.input(11, 1); game.tick(50);
    expect(game.state().players[0]!.x).toBeGreaterThan(before);
  });
  it('coasts rather than accelerating on throttle older than 350ms after a 500ms stall', () => {
    const game = start();
    game.connection.command({ type: 'command', id: 'enter-stall', action: 'enter', target: 'compact-01' });
    game.input(1, 0, 1); game.tick(200);
    const before = game.state().vehicles[0]!.speed, tickBefore = game.state().tick;
    expect(before).toBeGreaterThan(0);
    game.tick(500);
    expect(game.state().tick).toBe(tickBefore + 5);
    expect(game.state().vehicles[0]!.speed).toBeCloseTo(before * Math.exp(-3.5 * .25), 10);
    expect(game.state().players[0]!.lastInputSeq).toBe(1);
  });
  it('pauses hidden time and clears held intent on both hide and resume', () => {
    const game = start(); game.input(1, 1); game.tick(50);
    const before = game.state();
    documentState.hidden = true; documentState.dispatchEvent(new Event('visibilitychange'));
    game.tick(60_000); game.input(2, 1);
    expect(game.state()).toBe(before);
    documentState.hidden = false; documentState.dispatchEvent(new Event('visibilitychange'));
    game.tick(50);
    expect(game.state().tick).toBe(before.tick + 1);
    expect(game.state().players[0]!.x).toBe(before.players[0]!.x);
    game.input(3, 1); game.tick(50);
    expect(game.state().players[0]!.x).toBeGreaterThan(before.players[0]!.x);
  });
  it('clears held movement on focus loss without resetting the accepted sequence', () => {
    const game = start(); game.input(7, 1); game.tick(50);
    const before = game.state().players[0]!.x;
    window.dispatchEvent(new Event('blur')); game.tick(50);
    expect(game.state().players[0]!.x).toBe(before);
    expect(game.state().players[0]!.lastInputSeq).toBe(7);
  });
  it('saves by wall time under load and writes at most once after a long gap', () => {
    const game = start();
    for (let i = 0; i < 5; i++) game.tick(1000);
    expect(writes).toHaveBeenCalledTimes(1);
    expect(JSON.parse(writes.mock.calls[0]![1]).tick).toBe(25);
    game.tick(20_000); expect(writes).toHaveBeenCalledTimes(2);
  });
  it('close is idempotent and removes timers, listeners and action eligibility', () => {
    const game = start(); game.connection.close();
    const writesBefore = writes.mock.calls.length, snapshotsBefore = game.callbacks.snapshot.mock.calls.length;
    expect(vi.getTimerCount()).toBe(0);
    game.connection.close(); game.input(1, 1);
    game.connection.command({ type: 'command', id: 'after-close', action: 'signal', value: 'ready' });
    documentState.hidden = true; documentState.dispatchEvent(new Event('visibilitychange'));
    window.dispatchEvent(new Event('blur')); game.tick(5000);
    expect(writes).toHaveBeenCalledTimes(writesBefore);
    expect(game.callbacks.snapshot).toHaveBeenCalledTimes(snapshotsBefore);
  });
});
