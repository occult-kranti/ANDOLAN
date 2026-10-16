import { describe, expect, it } from 'vitest';
import { ArenaSimulation } from '../shared/simulation.js';
import { GOLD_RULES, JUNGLE_CAMPS, JUNGLE_RULES, NEUTRAL_STATS, blocked } from '../shared/map.js';
import type { Actor, GoldShard, NeutralSpecies } from '../shared/types.js';

// Positioned authority fixtures: all damage, rewards, timers and actions use the real engine.
function advance(sim: ArenaSimulation, seconds: number) { for (let left = seconds; left > 1e-7; left -= .05) sim.step(Math.min(.05, left)); }
function intent(sim: ArenaSimulation, actor: Actor, yaw = 0, fire = true, pitch = 0) { return sim.input(actor.id, { type: 'input', seq: actor.lastInputSeq + 1, moveX: 0, moveZ: 0, yaw, pitch, fire, jump: false }); }
function arena() { const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 7 }); const hero = sim.addPlayer('hero', 'Hero', 'rama', 'sun'); Object.assign(hero, { x: 0, z: -6 }); return { sim, hero }; }
function shard(sim: ArenaSimulation, overrides: Partial<GoldShard> = {}) { const value: GoldShard = { id: 'gold-fixture', sourceId: 'lane-fixture', x: 0, z: 0, y: 1.2, value: 8, originTeam: 'sun', createdAt: sim.time, expiresAt: sim.time + 12, ...overrides }; sim.goldShards.push(value); return value; }
function camp(species: NeutralSpecies) {
  const { sim, hero } = arena(); sim.time = JUNGLE_RULES.firstSpawn - .05; sim.step(.05);
  const neutral = sim.neutrals.find(value => value.species === species)!;
  Object.assign(hero, { x: neutral.x, z: neutral.z - 6, health: 1000, maxHealth: 1000 });
  return { sim, hero, neutral };
}
function defeatCamp(species: NeutralSpecies) { const setup = camp(species); setup.neutral.health = 1; intent(setup.sim, setup.hero); advance(setup.sim, .25); expect(setup.neutral.state).toBe('dead'); return setup; }

describe('contested gold authority', () => {
  it('lets either team secure a shard with an actual primary shot and never subtracts banked gold', () => {
    const { sim, hero } = arena(), rival = sim.addPlayer('rival', 'Rival', 'rama', 'moon');
    Object.assign(hero, { x: 10 }); Object.assign(rival, { x: 0, z: -6 }); shard(sim); intent(sim, rival); advance(sim, .25);
    expect(rival.credits).toBe(188); expect(hero.credits).toBe(180); expect(sim.goldShards).toHaveLength(0);
    expect(sim.snapshot().events.find(event => event.type === 'gold')).toMatchObject({ actorId: rival.id, targetId: 'gold-fixture', amount: 8, reward: 'steal' });
    advance(sim, .25); expect(rival.credits).toBe(188);
  });
  it('settles two simultaneous primary shots once and consumes the winning projectile', () => {
    const { sim, hero } = arena(), rival = sim.addPlayer('rival', 'Rival', 'rama', 'moon'); Object.assign(rival, { x: 0, z: 6 });
    shard(sim); intent(sim, hero); intent(sim, rival, Math.PI); advance(sim, .25);
    expect(hero.credits + rival.credits).toBe(368); expect(sim.snapshot().events.filter(event => event.type === 'gold')).toHaveLength(1);
    expect(sim.projectiles.filter(value => value.owner === hero.id)).toHaveLength(0);
  });
  it('does not let ability projectiles, stale inputs or forged reward commands claim gold', () => {
    const { sim, hero } = arena(); shard(sim); intent(sim, hero, 0, false);
    sim.command(hero.id, { type: 'command', id: 'bolt', action: 'ability', slot: 0 }); advance(sim, .25);
    expect(sim.goldShards).toHaveLength(1); expect(hero.credits).toBe(180);
    expect(sim.input(hero.id, { type: 'input', seq: hero.lastInputSeq, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: true, jump: false })).toBe(false);
    advance(sim, .25); expect(hero.credits).toBe(180);
    expect(sim.command(hero.id, { type: 'command', id: 'forged', action: 'reward' } as never).code).toBe('UNKNOWN_ABILITY');
  });
  it('stops a primary shot at actual cover before it can secure the shard behind it', () => {
    const { sim, hero } = arena(); Object.assign(hero, { x: -32, z: -28 }); shard(sim, { x: -8, z: -28 }); intent(sim, hero, Math.PI / 2); advance(sim, .8);
    expect(sim.goldShards).toHaveLength(1); expect(hero.credits).toBe(180);
  });
  it('delays physical fallback for one second and chooses exactly one living nearby hero', () => {
    const { sim, hero } = arena(), rival = sim.addPlayer('rival', 'Rival', 'rama', 'moon'); Object.assign(hero, { x: 1, z: 0 }); Object.assign(rival, { x: -.5, z: 0 }); shard(sim);
    advance(sim, .95); expect(sim.goldShards).toHaveLength(1); sim.step(.05);
    expect(sim.goldShards).toHaveLength(0); expect(hero.credits).toBe(180); expect(rival.credits).toBe(188);
  });
  it('expires an unclaimed shard without payout and returns a detached snapshot', () => {
    const { sim, hero } = arena(); shard(sim); const snapshot = sim.snapshot(); snapshot.goldShards[0]!.value = 99999;
    advance(sim, 12.1); expect(sim.goldShards).toHaveLength(0); expect(hero.credits).toBe(180); expect(sim.snapshot().events.some(event => event.type === 'gold')).toBe(false);
  });
  it('splits a lane defeat into shared10 and one contested8, and never rewards summoned deaths', () => {
    const { sim, hero } = arena(); advance(sim, 1.05);
    const minion = [...sim.actors.values()].find(actor => actor.team === 'moon' && actor.minionRole === 'escort')!;
    Object.assign(minion, { x: 0, z: 0, health: 1, shield: 0 }); intent(sim, hero); advance(sim, .25);
    expect(sim.actors.has(minion.id)).toBe(false); expect(hero.credits).toBe(190); expect(sim.scores.sun).toBe(1); expect(sim.goldShards).toHaveLength(1); expect(sim.goldShards[0]!.value).toBe(8);
    const enemy = sim.addPlayer('summoner', 'Summoner', 'subhadra', 'moon'); Object.assign(enemy, { x: 20, z: 0 });
    sim.command(enemy.id, { type: 'command', id: 'summon', action: 'ability', slot: 2 });
    const summon = [...sim.actors.values()].find(actor => actor.minionRole === 'summon')!;
    Object.assign(summon, { x: 5, z: 0, health: 1, shield: 0 }); Object.assign(hero, { x: 5, z: -6, fireCooldown: 0 }); intent(sim, hero); advance(sim, .25);
    expect(sim.actors.has(summon.id)).toBe(false); expect(hero.credits).toBe(190); expect(sim.scores.sun).toBe(1); expect(sim.goldShards).toHaveLength(1);
  });
  it('bounds shard count and keeps unique IDs after more than48 genuine lane deaths', () => {
    const { sim, hero } = arena(); advance(sim, 1.05); hero.heroId = 'ravana';
    const template = [...sim.actors.values()].find(actor => actor.team === 'moon' && actor.kind === 'minion')!;
    for (let i = 0; i < 55; i++) sim.actors.set(`fixture-${i}`, { ...structuredClone(template), id: `fixture-${i}`, x: 0, z: 0, health: 1, shield: 0 });
    hero.x = 0; hero.z = 0; sim.command(hero.id, { type: 'command', id: 'nova', action: 'ability', slot: 2 });
    expect(sim.goldShards).toHaveLength(GOLD_RULES.maxShards); expect(new Set(sim.goldShards.map(value => value.id)).size).toBe(GOLD_RULES.maxShards);
  });
});

describe('neutral camps and temporary rewards', () => {
  it('spawns exactly four neutral slots at30seconds on walkable, mirrored camp points', () => {
    const { sim } = arena(); expect(sim.neutrals).toHaveLength(4); expect(sim.neutrals.every(value => value.state === 'dead' && value.respawnAt === 30)).toBe(true);
    expect(JUNGLE_CAMPS.every(value => !blocked(value.x, value.z, .8))).toBe(true); sim.time = 29.95; sim.step(.05);
    expect(sim.neutrals.every(value => value.state === 'idle' && value.health === value.maxHealth)).toBe(true);
  });
  it('aggros a nearby hero and damages it with real neutral projectiles', () => {
    const { sim, hero, neutral } = camp('naga'); advance(sim, 1.1);
    expect(neutral.state).toBe('aggro'); expect(neutral.targetId).toBe(hero.id); expect(hero.health).toBeLessThan(1000);
    expect(sim.snapshot().events.some(event => event.type === 'shot' && event.actorId === neutral.id && event.team === 'neutral')).toBe(true);
  });
  it('does not aggro or fire through a building corner despite a hero inside the aggro radius', () => {
    const { sim, hero, neutral } = camp('naga'); Object.assign(neutral, { x: -10, z: -22 }); Object.assign(hero, { x: -13, z: -18 });
    advance(sim, 1); expect(neutral.state).toBe('idle'); expect(hero.health).toBe(1000); expect(sim.snapshot().events.some(event => event.actorId === neutral.id && event.type === 'shot')).toBe(false);
  });
  it('records only eligible shared recipients and reports actual capped wallet deltas', () => {
    const { sim, hero, neutral } = camp('naga'), near = sim.addPlayer('near', 'Near', 'rama', 'sun'), far = sim.addPlayer('far', 'Far', 'rama', 'sun'), rival = sim.addPlayer('rival', 'Rival', 'rama', 'moon');
    Object.assign(near, { x: neutral.x + 2, z: neutral.z, credits: 99990 }); Object.assign(rival, { x: neutral.x + 4, z: neutral.z });
    neutral.health = 1; intent(sim, hero); advance(sim, .25);
    expect(near.credits).toBe(99999); expect(far.credits).toBe(180); expect(rival.credits).toBe(180);
    expect(sim.snapshot().events.find(event => event.type === 'camp')!.sharedAwards).toEqual([{ actorId: hero.id, amount: 30 }, { actorId: near.id, amount: 9 }]);
    hero.credits = 99998; hero.fireCooldown = 0; intent(sim, hero); advance(sim, .25);
    expect(hero.credits).toBe(99999); expect(sim.snapshot().events.find(event => event.type === 'gold')).toMatchObject({ actorId: hero.id, amount: 1 });
  });
  it('leashes home, rejects damage during reset and grants no reward until an actual later defeat', () => {
    const { sim, hero, neutral } = camp('naga'); neutral.health = 120; advance(sim, .2); hero.z = -20; sim.step(.05); expect(neutral.state).toBe('returning');
    const before = neutral.health; hero.z = -6; intent(sim, hero); advance(sim, .15); expect(neutral.health).toBeGreaterThanOrEqual(before);
    hero.z = -25; advance(sim, 3); expect(neutral.state).toBe('idle'); expect(neutral.health).toBe(neutral.maxHealth); expect(hero.credits).toBe(180); expect(sim.goldShards).toHaveLength(0);
  });
  it.each(['naga', 'yaksha', 'sky-sentinel'] as const)('%s defeat grants one shared30, one contested30 and a bounded twelve-second buff', species => {
    const { sim, hero, neutral } = defeatCamp(species); const buff = NEUTRAL_STATS[species].buff;
    expect(hero.credits).toBe(210); expect(sim.goldShards).toHaveLength(1); expect(sim.goldShards[0]!.value).toBe(30); expect(hero.effects[buff]).toBeGreaterThan(11.8); expect(hero.effects[buff]).toBeLessThanOrEqual(12);
    if (buff === 'ward') expect(hero.shield).toBe(60);
    expect(sim.snapshot().events.filter(event => event.type === 'camp' && event.targetId === neutral.id)).toHaveLength(1);
    expect(sim.snapshot().events.find(event => event.type === 'buff')).toMatchObject({ actorId: hero.id, targetId: neutral.id, buff });
    hero.x = 0; hero.z = -60; advance(sim, 12.1); expect(hero.effects[buff]).toBe(0); expect(hero.credits).toBe(210);
    advance(sim, 28); expect(neutral.state).toBe('idle'); expect(neutral.health).toBe(neutral.maxHealth);
  });
  it('vigor heals at5HP/s only for remaining duration and death clears every camp buff', () => {
    const { sim, hero } = defeatCamp('yaksha'); hero.x = 0; hero.z = 0; hero.health = 100; const before = hero.health; advance(sim, 2); expect(hero.health - before).toBeCloseTo(10);
    const enemy = sim.addPlayer('enemy', 'Enemy', 'rama', 'moon'); Object.assign(enemy, { x: 0, z: -5 }); hero.health = 1; intent(sim, enemy); advance(sim, .3);
    expect(hero.health).toBe(0); expect(hero.effects).toEqual({ haste: 0, slow: 0, ward: 0, vigor: 0 });
  });
  it('does not add or shorten stronger wards and matching legacy pickups preserve camp durations', () => {
    const { sim, hero, neutral } = camp('naga'); hero.shield = 100; hero.effects.ward = 20; neutral.health = 1; intent(sim, hero); advance(sim, .25);
    expect(hero.shield).toBe(100); expect(hero.effects.ward).toBeCloseTo(19.75);
    const ward = sim.pickups.find(value => value.kind === 'ward')!; ward.readyAt = 0; Object.assign(hero, { x: ward.x, z: ward.z }); sim.step(.05); expect(hero.effects.ward).toBeCloseTo(19.7);
    const haste = sim.pickups.find(value => value.kind === 'haste')!; haste.readyAt = 0; hero.effects.haste = 12; Object.assign(hero, { x: haste.x, z: haste.z }); sim.step(.05); expect(hero.effects.haste).toBeCloseTo(11.95);
  });
  it('preserves gold, buffs and independent neutral state across disconnect/rejoin while snapshots cannot mutate them', () => {
    const { sim, hero, neutral } = defeatCamp('naga'); const snapshot = sim.snapshot(); snapshot.neutrals[0]!.health = 99999; snapshot.goldShards[0]!.value = 99999;
    sim.removePlayer(hero.id); const resumed = sim.addPlayer(hero.id, 'Hero', 'rama'); expect(resumed).toBe(hero); expect(resumed.credits).toBe(210); expect(resumed.effects.ward).toBeGreaterThan(11); expect(neutral.health).toBe(0); expect(sim.goldShards[0]!.value).toBe(30);
  });
});
