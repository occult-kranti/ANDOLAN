import { describe, expect, it } from 'vitest';
import { ArenaSimulation } from '../shared/simulation.js';
import type { Projectile } from '../shared/types.js';

function fixture() {
  const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 7301 });
  sim.structures = []; sim.neutrals = []; sim.pickups = [];
  const owner = sim.addPlayer('owner', 'Archer', 'rama', 'sun');
  Object.assign(owner, { x: 0, y: 0, z: -5 });
  return { sim, owner };
}

function shot(sim: ArenaSimulation, fields: Partial<Projectile> = {}) {
  const projectile: Projectile = { id: 'lifetime-shot', owner: 'owner', team: 'sun',
    x: 0, y: 1.1, z: 0, vx: 0, vy: 0, vz: 54, damage: 20, radius: .1,
    life: .05, color: '#ffcc66', ...fields };
  sim.projectiles.push(projectile);
  return projectile;
}

function enemy(sim: ArenaSimulation, x = 0, z = 3.6) {
  const actor = sim.addPlayer('enemy', 'Target', 'ravana', 'moon');
  Object.assign(actor, { x, y: 0, z, health: 100, shield: 0 });
  return actor;
}

describe('authoritative projectile lifetime boundary', () => {
  it.each([.05, .1])('resolves the last .05 seconds before expiry when the step is %s', dt => {
    const { sim, owner } = fixture(), target = enemy(sim);
    shot(sim);
    sim.step(dt);
    expect(target.health).toBe(80);
    expect(owner.damageDealt).toBe(20);
    expect(sim.projectiles).toHaveLength(0);
    expect(sim.snapshot().events.filter(event => event.type === 'hit')).toHaveLength(1);
    sim.step(.05);
    expect(target.health).toBe(80);
    expect(sim.snapshot().events.filter(event => event.type === 'hit')).toHaveLength(1);
  });

  it('travels only the remaining lifetime and cannot hit beyond its range plus existing radius', () => {
    const { sim } = fixture(), target = enemy(sim, 0, 3.751);
    const projectile = shot(sim); // Hero .95 + shot .1: nearest surface is 2.701 m.
    sim.step(.1);
    expect(projectile.z).toBeCloseTo(2.7, 10);
    expect(projectile.life).toBe(0);
    expect(target.health).toBe(100);
    expect(sim.projectiles).toHaveLength(0);
  });

  it('preserves total lifetime range across five smaller steps', () => {
    const { sim: whole } = fixture(), { sim: split } = fixture();
    const one = shot(whole), five = shot(split);
    whole.step(.05);
    for (let index = 0; index < 5; index++) split.step(.01);
    expect(one.z).toBeCloseTo(2.7, 10);
    expect(five.z).toBeCloseTo(2.7, 10);
    expect(five.z).toBeCloseTo(one.z, 10);
    expect(whole.projectiles).toHaveLength(0);
    expect(split.projectiles).toHaveLength(0);
  });

  it.each([0, -.01])('does not move or damage with already expired lifetime %s', life => {
    const { sim } = fixture(), target = enemy(sim, 0, 0);
    const projectile = shot(sim, { life });
    sim.step(.1);
    expect(projectile.z).toBe(0);
    expect(target.health).toBe(100);
    expect(sim.projectiles).toHaveLength(0);
  });

  it('still checks shared building cover before a target during the final segment', () => {
    const { sim } = fixture(), target = enemy(sim, 13, -28);
    const projectile = shot(sim, { x: 9.5, z: -28, vx: 54, vz: 0 });
    sim.step(.1);
    expect(projectile.x).toBeGreaterThan(10.9);
    expect(projectile.x).toBeLessThanOrEqual(11.25);
    expect(target.health).toBe(100);
    expect(sim.projectiles).toHaveLength(0);
  });

  it('can intercept one gold shard in the final segment without duplicate credit', () => {
    const { sim, owner } = fixture();
    sim.goldShards.push({ id: 'final-shard', sourceId: 'defeated-minion', originTeam: 'moon',
      x: 0, y: 1.1, z: 3.5, value: 8, createdAt: 0, expiresAt: 12 });
    shot(sim, { canSecureGold: true });
    sim.step(.1);
    expect(owner.credits).toBe(188);
    expect(sim.goldShards).toHaveLength(0);
    expect(sim.snapshot().events.filter(event => event.type === 'gold')).toMatchObject([
      { actorId: owner.id, targetId: 'final-shard', amount: 8, reward: 'steal' },
    ]);
    sim.step(.1);
    expect(owner.credits).toBe(188);
    expect(sim.snapshot().events.filter(event => event.type === 'gold')).toHaveLength(1);
  });

  it('keeps ordinary non-expiring damage and finite 3D trajectory components', () => {
    const { sim } = fixture(), target = enemy(sim);
    shot(sim, { life: .2 });
    sim.step(.05);
    expect(target.health).toBe(80);
    const { sim: rising } = fixture();
    const projectile = shot(rising, { vx: 12, vy: 16, vz: 0 });
    rising.step(.1);
    expect(projectile.x).toBeCloseTo(.6, 10);
    expect(projectile.y).toBeCloseTo(1.9, 10);
    expect(projectile.z).toBe(0);
    expect(rising.projectiles).toHaveLength(0);
  });
});
