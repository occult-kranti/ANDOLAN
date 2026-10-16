import { describe, expect, it } from 'vitest';
import { RemotePoseBuffer } from '../apps/client/src/world/remote-poses';
import { Simulation } from '../packages/sim/src/index';
import type { Snapshot } from '../packages/protocol/src/index';

function frame(tick: number, time: number, x = 0): Snapshot {
  const sim = new Simulation('POSE-ROOM', 'private');
  sim.addPlayer('local', 'Local'); sim.addPlayer('remote', 'Remote');
  const snapshot = sim.snapshot(); snapshot.tick = tick; snapshot.time = time;
  for (const player of snapshot.players) { player.x = player.id === 'remote' ? x : 50; player.z = 0; player.heading = 0; }
  for (const vehicle of snapshot.vehicles) { vehicle.x = x; vehicle.z = 0; vehicle.heading = 0; }
  return snapshot;
}
function pair(buffer = new RemotePoseBuffer()) {
  const a = frame(1, 1, 0), b = frame(3, 1.1, 4);
  a.players[1]!.heading = 350 * Math.PI / 180; b.players[1]!.heading = 10 * Math.PI / 180;
  buffer.push(a, 1000, 'local'); buffer.push(b, 1100, 'local');
  return buffer;
}

describe('remote presentation pose history', () => {
  it('interpolates timestamp midpoints and crosses angle zero by the shortest arc', () => {
    const sampled = pair().sample(1150);
    expect(sampled.players.get('remote')!.x).toBeCloseTo(2);
    expect(sampled.vehicles.get('compact-01')!.x).toBeCloseTo(2);
    expect(Math.sin(sampled.players.get('remote')!.heading)).toBeCloseTo(0, 10);
    expect(Math.cos(sampled.players.get('remote')!.heading)).toBeCloseTo(1, 10);
  });

  it('uses elapsed timestamps rather than the number of render calls', () => {
    const frequent = pair(), sparse = pair();
    for (let now = 1100; now < 1150; now += 5) frequent.sample(now);
    sparse.sample(1100);
    expect(frequent.sample(1150)).toEqual(sparse.sample(1150));
  });

  it('rejects duplicate and out-of-order packets without rewinding state', () => {
    const buffer = pair();
    expect(buffer.push(frame(3, 1.1, 90), 1110, 'local')).toBe(false);
    expect(buffer.push(frame(2, 1.05, -90), 1120, 'local')).toBe(false);
    expect(buffer.size).toBe(2);
    expect(buffer.sample(1200).players.get('remote')!.x).toBe(4);
  });

  it('holds endpoints when history is missing or a network gap exceeds the buffer', () => {
    const buffer = new RemotePoseBuffer();
    expect(buffer.sample(1000).players.size).toBe(0);
    buffer.push(frame(1, 1, 3), 1000, 'local');
    expect(buffer.sample(900).players.get('remote')!.x).toBe(3);
    expect(buffer.sample(50_000).players.get('remote')!.x).toBe(3);
    buffer.push(frame(3, 1.1, 4), 50_001, 'local');
    expect(buffer.sample(50_002).players.get('remote')!.x).toBe(4);
  });

  it('never adds interpolation delay to the local player or their driver/passenger vehicle', () => {
    for (const seat of [0, 1]) {
      const buffer = new RemotePoseBuffer(), state = frame(1, 1);
      state.players[0]!.vehicleId = 'compact-01'; state.players[0]!.seat = seat;
      state.vehicles[0]!.occupants[seat] = 'local';
      buffer.push(state, 1000, 'local'); const sampled = buffer.sample(1000);
      expect(sampled.players.has('local')).toBe(false);
      expect(sampled.vehicles.has('compact-01')).toBe(false);
      expect(sampled.vehicles.has('van-01')).toBe(true);
    }
  });

  it('snaps seat changes and vehicle occupancy changes instead of drawing a transition path', () => {
    const buffer = new RemotePoseBuffer(), a = frame(1, 1), b = frame(3, 1.1, 4);
    b.players[1]!.vehicleId = 'compact-01'; b.players[1]!.seat = 0;
    b.vehicles[0]!.occupants[0] = 'remote';
    buffer.push(a, 1000, 'local'); buffer.push(b, 1100, 'local');
    const sampled = buffer.sample(1100);
    expect(sampled.players.get('remote')!.x).toBe(4);
    expect(sampled.vehicles.get('compact-01')!.x).toBe(4);
    expect(sampled.vehicles.get('van-01')!.x).toBe(0);
  });

  it('snaps a large positional discontinuity and resumes interpolation from the new location', () => {
    const buffer = new RemotePoseBuffer();
    buffer.push(frame(1, 1), 1000, 'local'); buffer.push(frame(3, 1.1, 30), 1100, 'local');
    expect(buffer.sample(1100).players.get('remote')!.x).toBe(30);
    buffer.push(frame(5, 1.2, 34), 1200, 'local');
    expect(buffer.sample(1250).players.get('remote')!.x).toBeCloseTo(32);
  });

  it('removes absent/disconnected entities immediately and does not bridge their return', () => {
    const buffer = pair(), missing = frame(5, 1.2, 5);
    missing.players[1]!.connected = false; missing.vehicles = missing.vehicles.filter(v => v.id !== 'van-01');
    buffer.push(missing, 1200, 'local');
    expect(buffer.sample(1200).players.has('remote')).toBe(false);
    expect(buffer.sample(1200).vehicles.has('van-01')).toBe(false);
    buffer.push(frame(7, 1.3, 6), 1300, 'local');
    expect(buffer.sample(1300).players.get('remote')!.x).toBe(6);
  });

  it('caps history and clamps a requested time older than retained data', () => {
    const buffer = new RemotePoseBuffer(100, 3);
    for (let i = 0; i < 10; i++) buffer.push(frame(i, i / 10, i), i * 100, 'local');
    expect(buffer.size).toBe(3);
    expect(buffer.sample(0).players.get('remote')!.x).toBe(7);
  });

  it('resets for a new room, gameplay or local identity rather than joining their histories', () => {
    for (const changed of ['room', 'gameplay', 'identity']) {
      const buffer = pair(), state = frame(1, .1, 40);
      if (changed === 'room') state.room = 'OTHER-ROOM';
      if (changed === 'gameplay') state.gameplay = 'freeroam';
      expect(buffer.push(state, 2000, changed === 'identity' ? 'different-local' : 'local')).toBe(true);
      expect(buffer.size).toBe(1);
      expect(buffer.sample(2000).players.get('remote')!.x).toBe(40);
    }
  });

  it('requires explicit reconnect reset for lower ticks and accepts the restarted clock afterward', () => {
    const buffer = pair();
    expect(buffer.push(frame(0, 0, 20), 2000, 'local')).toBe(false);
    buffer.reset(); expect(buffer.size).toBe(0);
    expect(buffer.push(frame(0, 0, 20), 2000, 'local')).toBe(true);
    expect(buffer.sample(2000).players.get('remote')!.x).toBe(20);
  });

  it('resets an advancing tick with a regressed server time or receipt clock', () => {
    for (const receipt of [1200, 900]) {
      const buffer = pair();
      expect(buffer.push(frame(5, receipt === 1200 ? .5 : 1.2, 6), receipt, 'local')).toBe(true);
      expect(buffer.size).toBe(1);
      expect(buffer.sample(receipt).players.get('remote')!.x).toBe(6);
    }
  });

  it('does not mutate snapshots, expose internal pose objects or move its playhead backward', () => {
    const buffer = new RemotePoseBuffer(), a = frame(1, 1), b = frame(3, 1.1, 4);
    const before = structuredClone([a, b]);
    buffer.push(a, 1000, 'local'); buffer.push(b, 1100, 'local');
    const visual = buffer.sample(1150); visual.players.get('remote')!.x = 999;
    expect(buffer.sample(1100).players.get('remote')!.x).toBe(2);
    expect([a, b]).toEqual(before);
  });

  it('rejects invalid clocks/settings and omits non-finite entity poses', () => {
    expect(() => new RemotePoseBuffer(-1)).toThrow(RangeError);
    expect(() => new RemotePoseBuffer(100, 1)).toThrow(RangeError);
    const buffer = new RemotePoseBuffer(), state = frame(1, 1);
    expect(buffer.push(state, NaN, 'local')).toBe(false);
    expect(buffer.push({ ...state, time: Infinity }, 1000, 'local')).toBe(false);
    state.players[1]!.x = NaN;
    expect(buffer.push(state, 1000, 'local')).toBe(true);
    expect(buffer.sample(1000).players.has('remote')).toBe(false);
  });
});
