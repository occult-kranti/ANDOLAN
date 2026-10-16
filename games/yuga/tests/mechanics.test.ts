import { describe, expect, it } from 'vitest';
import { ArenaSimulation } from '../shared/simulation.js';
import { blocked } from '../shared/map.js';
import { heroById } from '../shared/heroes.js';
import type { Actor } from '../shared/types.js';

function setup(heroId: string) {
  const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 7 });
  const caster = sim.addPlayer('caster', 'Caster', heroId, 'sun');
  Object.assign(caster, { x: 0, z: 0, yaw: 0 });
  return { sim, caster };
}
function advance(sim: ArenaSimulation, seconds: number) { for (let remaining = seconds; remaining > 1e-8; remaining -= .05) sim.step(Math.min(.05, remaining)); }
function input(sim: ArenaSimulation, actor: Actor, fields: { yaw?: number; fire?: boolean; moveX?: number; jump?: boolean } = {}) { sim.input(actor.id, { type: 'input', seq: actor.lastInputSeq + 1, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: false, jump: false, ...fields }); }
const ultimate = { type: 'command', id: 'ultimate', action: 'ability', slot: 2 } as const;

describe('telegraphed mythic abilities', () => {
  it('locks Rama windup position and aim, announces the cast, then releases exactly three bounded arrows once', () => {
    const { sim, caster } = setup('rama'); input(sim, caster);
    expect(sim.command(caster.id, ultimate).code).toBe('ABILITY_CAST');
    expect(caster.cast).toMatchObject({ mechanic: 'dawn-volley', phase: 'windup', releaseAt: 1, yaw: 0 });
    const before = sim.snapshot(); expect(sim.command(caster.id, ultimate).ok).toBe(true); expect(sim.snapshot()).toEqual(before);
    expect(sim.command(caster.id, { ...ultimate, id: 'second' }).code).toBe('CAST_IN_PROGRESS');
    input(sim, caster, { yaw: Math.PI / 2, fire: true, moveX: 1, jump: true }); advance(sim, .95);
    expect(caster).toMatchObject({ x: 0, z: 0, y: 0, yaw: 0 }); expect(sim.projectiles.filter(p => p.owner === caster.id)).toHaveLength(0);
    sim.step(.05); const arrows = sim.projectiles.filter(p => p.owner === caster.id);
    expect(caster.cast).toBeUndefined(); expect(arrows).toHaveLength(3);
    expect(arrows.map(p => Math.sign(p.vx))).toEqual([-1, 0, 1]);
    expect(arrows.reduce((sum, arrow) => sum + arrow.damage, 0)).toBeLessThanOrEqual(100);
    expect(sim.command(caster.id, ultimate).ok).toBe(true); expect(sim.projectiles.filter(p => p.owner === caster.id)).toHaveLength(3);
  });

  it('keeps all three Rama arrows behind physical building cover', () => {
    const { sim, caster } = setup('rama'), enemy = sim.addPlayer('enemy', 'Enemy', 'bhima', 'moon');
    for (const structure of sim.structures) if (structure.kind === 'tower') structure.health = 0;
    Object.assign(caster, { x: -32, z: -28 }); Object.assign(enemy, { x: -8, z: -28 }); input(sim, caster, { yaw: Math.PI / 2 });
    sim.command(caster.id, ultimate); advance(sim, 1.6);
    expect(enemy.health).toBe(enemy.maxHealth); expect(sim.projectiles.some(p => p.owner === caster.id)).toBe(false);
  });

  it('allows movement out of the warned lane before Rama releases', () => {
    const { sim, caster } = setup('rama'), enemy = sim.addPlayer('enemy', 'Enemy', 'bhima', 'moon');
    Object.assign(enemy, { x: 0, z: 12 }); input(sim, caster); sim.command(caster.id, ultimate);
    for (let i = 0; i < 30; i++) { input(sim, enemy, { moveX: 1 }); sim.step(.05); }
    expect(enemy.x).toBeGreaterThan(8); expect(enemy.health).toBe(enemy.maxHealth);
  });

  it.each(['rama', 'hanuman', 'sita'])('%s loses a pending cast on actual projectile death without refund', heroId => {
    const { sim, caster } = setup(heroId), enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon');
    caster.health = 1; Object.assign(enemy, { x: 0, z: -6, yaw: 0 }); input(sim, caster); sim.command(caster.id, ultimate); input(sim, enemy, { fire: true }); advance(sim, 1.5);
    expect(caster.health).toBe(0); expect(caster.cast).toBeUndefined(); expect(caster.cooldowns[2]).toBeGreaterThan(35);
    expect(sim.projectiles.some(p => p.owner === caster.id)).toBe(false); expect(sim.zones.some(z => z.owner === caster.id)).toBe(false);
  });

  it('preserves a pending cast through disconnect and resumes the same cooldown and identity', () => {
    const { sim, caster } = setup('rama'); input(sim, caster); sim.command(caster.id, ultimate); advance(sim, .2); sim.removePlayer(caster.id);
    expect(caster.cast?.mechanic).toBe('dawn-volley'); advance(sim, .8);
    expect(sim.projectiles.filter(p => p.owner === caster.id)).toHaveLength(3);
    const actor = sim.addPlayer(caster.id, 'Caster', 'rama'); expect(actor).toBe(caster); expect(actor.cooldowns[2]).toBeCloseTo(heroById('rama').abilities[2].cooldown - 1);
    expect(sim.command(actor.id, ultimate).ok).toBe(true); expect(sim.projectiles.filter(p => p.owner === actor.id)).toHaveLength(3);
  });

  it('does not interrupt a declared windup from nonfatal damage', () => {
    const { sim, caster } = setup('sita'), enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon');
    caster.health = 200; Object.assign(enemy, { x: 0, z: -6 }); input(sim, caster); sim.command(caster.id, ultimate); input(sim, enemy, { fire: true });
    advance(sim, .3); expect(caster.health).toBeLessThan(200); expect(caster.health).toBeGreaterThan(0); expect(caster.cast?.phase).toBe('windup');
    advance(sim, .5); expect(caster.cast).toBeUndefined(); expect(sim.zones.some(zone => zone.mechanic === 'mithila-sanctuary')).toBe(true);
  });

  it('moves Hanuman through a timed arc and applies landing damage and ally healing only at the end', () => {
    const { sim, caster } = setup('hanuman'), ally = sim.addPlayer('ally', 'Ally', 'sita', 'sun'), enemy = sim.addPlayer('enemy', 'Enemy', 'bhima', 'moon');
    Object.assign(ally, { x: 2, z: 14, health: 100 }); Object.assign(enemy, { x: 0, z: 15 }); input(sim, caster); sim.command(caster.id, ultimate);
    advance(sim, .65); expect(caster.z).toBe(0); expect(enemy.health).toBe(enemy.maxHealth); expect(ally.health).toBe(100);
    advance(sim, .25); expect(caster.cast?.phase).toBe('travel'); expect(caster.z).toBeGreaterThan(5); expect(caster.z).toBeLessThan(14); expect(caster.y).toBeGreaterThan(4); expect(enemy.health).toBe(enemy.maxHealth);
    advance(sim, .25); expect(caster.cast).toBeUndefined(); expect(caster.z).toBeCloseTo(14); expect(caster.y).toBe(0);
    expect(enemy.health).toBe(enemy.maxHealth - 65); expect(ally.health).toBe(145);
  });

  it('stops Hanuman at a building and never lands through it or damages someone behind it', () => {
    const { sim, caster } = setup('hanuman'), enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon');
    for (const structure of sim.structures) if (structure.kind === 'tower') structure.health = 0;
    Object.assign(caster, { x: -20, z: -45 }); Object.assign(enemy, { x: -20, z: -25 }); input(sim, caster); sim.command(caster.id, ultimate); advance(sim, 1.2);
    expect(caster.z).toBeGreaterThan(-45); expect(caster.z).toBeLessThan(-37.6); expect(blocked(caster.x, caster.z)).toBe(false); expect(caster.y).toBe(0); expect(enemy.health).toBe(enemy.maxHealth);
  });

  it('cancels Hanuman landing payload if he is defeated during the actual travel phase', () => {
    const { sim, caster } = setup('hanuman'), ally = sim.addPlayer('ally', 'Ally', 'sita', 'sun'), enemy = sim.addPlayer('enemy', 'Enemy', 'arjuna', 'moon');
    Object.assign(ally, { x: 6, z: 14, health: 100 }); Object.assign(enemy, { x: 6, z: 6 }); caster.health = 1;
    input(sim, caster); sim.command(caster.id, ultimate); advance(sim, .9); expect(caster.cast?.phase).toBe('travel'); expect(caster.y).toBeGreaterThan(4);
    input(sim, enemy, { yaw: -Math.PI / 2 }); sim.command(enemy.id, { ...ultimate, id: 'intercept', slot: 0 });
    expect(caster.health).toBe(0); expect(caster.cast).toBeUndefined(); expect(caster.y).toBe(0);
    advance(sim, .4); expect(ally.health).toBe(100); expect(enemy.health).toBe(enemy.maxHealth); expect(sim.zones.some(zone => zone.owner === caster.id)).toBe(false);
  });

  it('creates a fixed Sita sanctuary with initial allied shields, bounded healing and no enemy benefit', () => {
    const { sim, caster } = setup('sita'), ally = sim.addPlayer('ally', 'Ally', 'rama', 'sun'), enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon');
    Object.assign(ally, { x: 2, z: 0, health: 100 }); Object.assign(enemy, { x: -2, z: 0, health: 100 }); caster.health = 100;
    input(sim, caster); sim.command(caster.id, ultimate); advance(sim, .75); expect(ally.shield).toBe(0); expect(ally.health).toBe(100);
    sim.step(.05); expect(ally.shield).toBe(70); expect(enemy.shield).toBe(0); expect(enemy.health).toBe(100);
    const zone = sim.zones.find(z => z.mechanic === 'mithila-sanctuary')!; expect(zone).toMatchObject({ x: 0, z: 0, radius: 8, power: 9, team: 'sun' });
    const afterRelease = ally.health; advance(sim, 1); expect(ally.health - afterRelease).toBeCloseTo(9);
    ally.x = 10; const outside = ally.health; caster.x = 10; advance(sim, 1); expect(ally.health).toBe(outside); expect(zone.x).toBe(0);
    advance(sim, 4.1); expect(sim.zones.some(z => z.id === zone.id)).toBe(false); expect(ally.shield).toBe(0);
  });

  it('keeps a completed sanctuary for its remaining duration after the caster is defeated', () => {
    const { sim, caster } = setup('sita'), ally = sim.addPlayer('ally', 'Ally', 'rama', 'sun'), enemy = sim.addPlayer('enemy', 'Enemy', 'ravana', 'moon');
    Object.assign(ally, { x: 0, z: 7.5, health: 100 }); Object.assign(enemy, { x: 0, z: 0 }); caster.health = 1;
    input(sim, caster); sim.command(caster.id, ultimate); advance(sim, .8);
    sim.command(enemy.id, { ...ultimate, id: 'defeat-caster' }); expect(caster.health).toBe(0);
    const before = ally.health; advance(sim, 1); expect(ally.health - before).toBeCloseTo(9); expect(sim.zones.some(zone => zone.mechanic === 'mithila-sanctuary')).toBe(true);
  });
});

describe('purposeful lane units', () => {
  it('spawns two escorts per lane every wave, adds siege every third wave, and routes all six siege lanes forward', () => {
    const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 2 }); advance(sim, 1.05);
    expect([...sim.actors.values()].filter(a => a.minionRole === 'escort')).toHaveLength(12); expect([...sim.actors.values()].some(a => a.minionRole === 'siege')).toBe(false);
    advance(sim, 36); const siege = [...sim.actors.values()].filter(a => a.minionRole === 'siege'); expect(siege).toHaveLength(6);
    expect(siege.every(a => a.maxHealth === 240)).toBe(true); const progress = new Set<string>();
    for (let i = 0; i < 500; i++) { sim.step(.05); for (const actor of siege) if (Math.abs(actor.z) < 34) progress.add(`${actor.team}:${actor.lane}`); }
    expect(progress.size).toBe(6);
  });

  it('makes a siege unit prioritize a visible enemy tower over a closer hero', () => {
    const sim = new ArenaSimulation({ botsPerTeam: 0 }); advance(sim, 37.05);
    const siege = [...sim.actors.values()].find(a => a.minionRole === 'siege' && a.team === 'sun' && a.lane === 1)!;
    Object.assign(siege, { x: 4.5, z: 22, fireCooldown: 0 }); const enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon'); Object.assign(enemy, { x: 8, z: 24 });
    const tower = sim.structures.find(s => s.id === 'moon-tower-1')!; tower.health = tower.maxHealth;
    sim.step(.05); const projectile = sim.projectiles.find(p => p.owner === siege.id)!; expect(projectile.damage).toBe(12); expect(projectile.structureDamage).toBe(32); expect(projectile.vx).toBeLessThan(0); expect(projectile.vz).toBeGreaterThan(0);
  });

  it('exposes summon identity and authoritative expiry without guessing from team colour', () => {
    const { sim, caster } = setup('subhadra'); sim.command(caster.id, ultimate);
    const summons = sim.snapshot().actors.filter(a => a.minionRole === 'summon'); expect(summons).toHaveLength(2);
    expect(summons.every(a => a.summonerId === caster.id && a.heroId === 'subhadra' && a.expiresAt === 9)).toBe(true);
    advance(sim, 9.05); expect(summons.some(a => sim.actors.has(a.id))).toBe(false);
  });

  it.each(['subhadra', 'hidimbi'])('%s places both summons clear of nearby buildings and arena edges', heroId => {
    for (const position of [{ x: 10.3, z: -28 }, { x: 67.2, z: 0 }]) {
      const { sim, caster } = setup(heroId); Object.assign(caster, position); sim.command(caster.id, ultimate);
      const summons = sim.snapshot().actors.filter(actor => actor.minionRole === 'summon'); expect(summons).toHaveLength(2);
      expect(summons.every(actor => !blocked(actor.x, actor.z, .42))).toBe(true);
      expect(summons.every(actor => Math.hypot(actor.x - caster.x, actor.z - caster.z) <= 3.5)).toBe(true);
    }
  });

  it('lets a hero intercept a siege round without taking its anti-structure damage bonus', () => {
    const sim = new ArenaSimulation({ botsPerTeam: 0 }); advance(sim, 37.05);
    const siege = [...sim.actors.values()].find(a => a.minionRole === 'siege' && a.team === 'sun' && a.lane === 1)!;
    Object.assign(siege, { x: 4.5, z: 22, fireCooldown: 0 }); sim.projectiles = [];
    const enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon'); Object.assign(enemy, { x: 4.5, z: 24 });
    sim.step(.05); expect(enemy.health).toBe(enemy.maxHealth - 12);
  });

  it('emits unique directional zone metadata without leaking or overwriting it with actor fields', () => {
    const { sim, caster } = setup('arjuna'); input(sim, caster, { yaw: .8 }); sim.command(caster.id, { ...ultimate, slot: 0 });
    const zone = sim.snapshot().zones[0]!;
    expect(zone.id).toMatch(/^zone-/); expect(zone.kind).toBe('burst'); expect(zone.yaw).toBe(.8);
    expect(zone).not.toHaveProperty('health'); expect(zone).not.toHaveProperty('heroId');
  });
});
