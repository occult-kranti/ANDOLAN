import { describe, expect, it } from 'vitest';
import { acquireTarget, targetAim } from '../client/targeting.js';
import { ArenaSimulation } from '../shared/simulation.js';
import type { Actor, ArenaSnapshot, Structure } from '../shared/types.js';

function fixture() {
  const sim = new ArenaSimulation({ botsPerTeam: 0 });
  sim.addPlayer('self', 'Local', 'rama', 'sun'); sim.addPlayer('enemy', 'Rival', 'ravana', 'moon');
  const snapshot = sim.snapshot(); snapshot.structures = [];
  const self = snapshot.actors.find(actor => actor.id === 'self')!, enemy = snapshot.actors.find(actor => actor.id === 'enemy')!;
  Object.assign(self, { x: 0, y: 0, z: 0 }); Object.assign(enemy, { x: 0, y: .1, z: 20 });
  return { snapshot, self, enemy };
}
function minion(enemy: Actor): Actor { return { ...structuredClone(enemy), id: 'minion-1', kind: 'minion', name: 'Lane sentinel', bot: true, connected: false, y: .5, minionRole: 'escort' }; }
function tower(fields: Partial<Structure> = {}): Structure { return { id: 'moon-tower-1', kind: 'tower', team: 'moon', lane: 1, x: 0, z: 10, health: 680, maxHealth: 680, shielded: false, ...fields }; }
function deepFreeze(value: object): void { Object.freeze(value); for (const entry of Object.values(value)) if (entry && typeof entry === 'object') deepFreeze(entry); }

describe('client lock-on acquisition', () => {
  it('returns the authoritative body-center solution without predicting velocity or writing state', () => {
    const { snapshot, self, enemy } = fixture(); Object.assign(self, { y: 2 }); Object.assign(enemy, { x: 3, y: 4, z: 12 });
    const before = structuredClone(snapshot); deepFreeze(snapshot);
    const aim = targetAim(snapshot, self.id, enemy.id)!;
    expect(aim).toMatchObject({ x: 3, y: 5.1, z: 12, label: 'Rival' });
    expect(aim.yaw).toBeCloseTo(Math.atan2(3, 12)); expect(aim.pitch).toBeCloseTo(Math.atan2(1.9, Math.hypot(3, 12)));
    expect(acquireTarget(snapshot, self.id, aim.yaw, aim.pitch)).toBe(enemy.id);
    aim.x = 999; expect(snapshot).toEqual(before);
  });

  it('uses an inclusive32-metre3D range rather than horizontal distance alone', () => {
    const { snapshot, enemy } = fixture(); enemy.z = 32;
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(enemy.id);
    enemy.z = 32.001; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
    enemy.z = 31.9; enemy.y = 4; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
  });

  it('uses a20-degree cone in both yaw and pitch and handles angle wrapping', () => {
    const { snapshot, enemy } = fixture(), boundary = 20 * Math.PI / 180;
    Object.assign(enemy, { x: Math.sin(boundary) * 20, z: Math.cos(boundary) * 20 });
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(enemy.id);
    Object.assign(enemy, { x: Math.sin(boundary + .001) * 20, z: Math.cos(boundary + .001) * 20 });
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull();
    Object.assign(enemy, { x: 0, y: .1 + Math.sin(boundary) * 20, z: Math.cos(boundary) * 20 });
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(enemy.id);
    enemy.y += .05; expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull();
    Object.assign(enemy, { x: Math.sin(-Math.PI + .01) * 20, y: .1, z: Math.cos(-Math.PI + .01) * 20 });
    expect(acquireTarget(snapshot, 'self', Math.PI - .01, 0)).toBe(enemy.id);
    expect(acquireTarget(snapshot, 'self', Math.PI - .01 + 8 * Math.PI, 0)).toBe(enemy.id);
  });

  it('prioritizes aim error, then a hero on an exact tie, then distance deterministically', () => {
    const { snapshot, enemy } = fixture(), sentinel = minion(enemy); snapshot.actors.push(sentinel);
    enemy.x = 1; expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(sentinel.id);
    enemy.x = 0; expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(enemy.id);
    const nearer = { ...structuredClone(enemy), id: 'nearer', z: 10 }; snapshot.actors.push(nearer);
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(nearer.id);
    const tied = { ...structuredClone(nearer), id: 'aaa' }; snapshot.actors.unshift(tied);
    expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(tied.id);
    snapshot.actors.reverse(); expect(acquireTarget(snapshot, 'self', 0, 0)).toBe(tied.id);
  });

  it('rejects friends, dead or respawning enemies, shielded cores and unknown target IDs', () => {
    const { snapshot, enemy } = fixture(); enemy.team = 'sun'; expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull();
    enemy.team = 'moon'; enemy.health = 0; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
    enemy.health = 100; enemy.respawn = 1; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
    snapshot.actors = snapshot.actors.filter(actor => actor.id === 'self');
    const core = tower({ id: 'moon-core', kind: 'core', z: 20, shielded: true }); snapshot.structures = [core];
    expect(targetAim(snapshot, 'self', core.id)).toBeNull(); expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull();
    core.shielded = false; expect(targetAim(snapshot, 'self', core.id)).toMatchObject({ y: 3, label: 'Enemy core' });
    expect(targetAim(snapshot, 'self', 'missing')).toBeNull();
  });

  it('uses the minion center and keeps built-in bots and disconnected AI takeovers eligible', () => {
    const { snapshot, enemy } = fixture(); enemy.connected = false; enemy.bot = false;
    expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
    enemy.bot = true; expect(targetAim(snapshot, 'self', enemy.id)).not.toBeNull();
    const sentinel = minion(enemy); sentinel.y = 0; sentinel.minionRole = 'siege'; snapshot.actors.push(sentinel);
    expect(targetAim(snapshot, 'self', sentinel.id)).toMatchObject({ y: .7, label: 'Siege sentinel' });
    sentinel.minionRole = 'summon'; expect(targetAim(snapshot, 'self', sentinel.id)?.label).toBe('Summoned sentinel');
  });

  it('releases locks when the local player disconnects, dies or the match ends', () => {
    const { snapshot, self, enemy } = fixture(); self.connected = false; self.bot = true;
    expect(acquireTarget(snapshot, self.id, 0, 0)).toBeNull(); expect(targetAim(snapshot, self.id, enemy.id)).toBeNull();
    self.connected = true; self.bot = false; self.health = 0; expect(targetAim(snapshot, self.id, enemy.id)).toBeNull();
    self.health = 100; snapshot.phase = 'finished'; expect(targetAim(snapshot, self.id, enemy.id)).toBeNull();
  });

  it('rejects non-finite pose, health and aim data instead of producing invalid angles', () => {
    const { snapshot, enemy } = fixture();
    for (const value of [NaN, Infinity, -Infinity]) {
      expect(acquireTarget(snapshot, 'self', value, 0)).toBeNull(); expect(acquireTarget(snapshot, 'self', 0, value)).toBeNull();
      for (const key of ['x', 'y', 'z', 'health', 'respawn'] as const) { const previous = enemy[key]; enemy[key] = value; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull(); enemy[key] = previous; }
    }
    enemy.x = Number.MAX_VALUE; expect(targetAim(snapshot, 'self', enemy.id)).toBeNull();
    expect(acquireTarget(snapshot, 'missing', 0, 0)).toBeNull(); expect(acquireTarget(snapshot, 'self', 0, Math.PI)).toBeNull();
  });
});

describe('lock-on cover and retention', () => {
  it('uses actual SOLIDS building footprints and height for line of sight', () => {
    const { snapshot, self, enemy } = fixture(); Object.assign(self, { x: -32, z: -28 }); Object.assign(enemy, { x: -8, z: -28 });
    expect(targetAim(snapshot, self.id, enemy.id)).toBeNull(); expect(acquireTarget(snapshot, self.id, Math.PI / 2, 0)).toBeNull();
    self.z = enemy.z = -45; expect(targetAim(snapshot, self.id, enemy.id)).not.toBeNull();
    self.z = enemy.z = -28; self.y = 11; enemy.y = 11.1;
    expect(acquireTarget(snapshot, self.id, Math.PI / 2, 0)).toBe(enemy.id);
  });

  it('counts projectile width at the edge of a building rather than promising a blocked shot', () => {
    const { snapshot, self, enemy } = fixture(); Object.assign(self, { x: -32, z: -37.1 }); Object.assign(enemy, { x: -8, z: -37.1 });
    expect(targetAim(snapshot, self.id, enemy.id)).toBeNull();
    self.z = enemy.z = -37.4; expect(targetAim(snapshot, self.id, enemy.id)).not.toBeNull();
  });

  it('blocks a target behind a living enemy tower but can acquire that tower itself', () => {
    const { snapshot, self, enemy } = fixture(), blocker = tower(); snapshot.structures.push(blocker);
    expect(targetAim(snapshot, self.id, enemy.id)).toBeNull(); expect(acquireTarget(snapshot, self.id, 0, 0)).toBe(blocker.id);
    expect(targetAim(snapshot, self.id, blocker.id)).toMatchObject({ x: 0, y: 2.2, z: 10, label: 'Temple avenue tower' });
    blocker.team = 'sun'; expect(targetAim(snapshot, self.id, enemy.id)).not.toBeNull();
    blocker.team = 'moon'; blocker.health = 0; expect(targetAim(snapshot, self.id, enemy.id)).not.toBeNull();
  });

  it('releases an existing lock behind a shielded enemy core and restores it when cover is removed', () => {
    const { snapshot, enemy } = fixture(), blocker = tower({ id: 'moon-core', kind: 'core', shielded: true });
    const id = acquireTarget(snapshot, 'self', 0, 0)!; expect(id).toBe(enemy.id);
    snapshot.structures.push(blocker); expect(targetAim(snapshot, 'self', id)).toBeNull(); expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull();
    blocker.health = 0; expect(targetAim(snapshot, 'self', id)).not.toBeNull();
  });

  it('retains a visible target outside the initial cone but immediately releases it on range or team change', () => {
    const { snapshot, enemy } = fixture(), id = acquireTarget(snapshot, 'self', 0, 0)!;
    enemy.x = 15; enemy.z = 0; expect(acquireTarget(snapshot, 'self', 0, 0)).toBeNull(); expect(targetAim(snapshot, 'self', id)?.yaw).toBeCloseTo(Math.PI / 2);
    enemy.x = 33; expect(targetAim(snapshot, 'self', id)).toBeNull();
    enemy.x = 15; enemy.team = 'sun'; expect(targetAim(snapshot, 'self', id)).toBeNull();
  });

  it('does not use an old snapshot position when the next authoritative frame moves a target', () => {
    const { snapshot, enemy } = fixture(), before = targetAim(snapshot, 'self', enemy.id)!;
    const next: ArenaSnapshot = structuredClone(snapshot); next.actors.find(actor => actor.id === enemy.id)!.x = 3;
    const after = targetAim(next, 'self', enemy.id)!;
    expect(after.x).toBe(3); expect(before.x).toBe(0); expect(snapshot.actors.find(actor => actor.id === enemy.id)!.x).toBe(0);
  });
});
