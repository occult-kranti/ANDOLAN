import { describe, expect, it } from 'vitest';
import { ARENA_RULES, ArenaSimulation, UPGRADE_COSTS } from '../shared/simulation.js';
import { HEROES } from '../shared/heroes.js';
import { blocked, SPAWNS } from '../shared/map.js';
import type { ArenaInput, Team } from '../shared/types.js';

const input = (seq: number, fields: Partial<ArenaInput> = {}): ArenaInput => ({ type: 'input', seq, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: false, jump: false, ...fields });
function duel() { const sim = new ArenaSimulation({ botsPerTeam: 0, seed: 12 }); const a = sim.addPlayer('a', 'Aadi', HEROES[0]!.id, 'sun'), b = sim.addPlayer('b', 'Noor', HEROES[1]!.id, 'moon'); a.x = b.x = 0; a.z = -6; b.z = 6; return { sim, a, b }; }

describe('authoritative arena rules', () => {
  it('fills six hero slots, reserves a disconnected identity and preserves its progress on resume', () => {
    const sim = new ArenaSimulation({ seed: 1 });
    const a = sim.addPlayer('a', 'Aadi', HEROES[0]!.id);
    a.credits = 777; a.upgrades.power = 2; a.kills = 3;
    for (let i = 1; i < 6; i++) sim.addPlayer(`p${i}`, `Player ${i}`, HEROES[i]!.id);
    expect(sim.snapshot().actors.filter(actor => actor.kind === 'hero')).toHaveLength(6);
    expect(sim.snapshot().actors.filter(actor => actor.team === 'sun')).toHaveLength(3);
    expect(() => sim.addPlayer('overflow', 'Extra', HEROES[0]!.id)).toThrow('ROOM_FULL');
    sim.removePlayer('a'); expect(a).toMatchObject({ bot: true, connected: false });
    expect(() => sim.addPlayer('steal-slot', 'Extra', HEROES[0]!.id)).toThrow('ROOM_FULL');
    const resumed = sim.addPlayer('a', 'Aadi', HEROES[0]!.id);
    expect(resumed).toBe(a); expect(resumed).toMatchObject({ credits: 777, kills: 3, upgrades: { power: 2 }, bot: false, connected: true });
    sim.removePlayer('a'); sim.releasePlayer('a'); sim.addPlayer('replacement', 'New', HEROES[2]!.id);
    expect(sim.snapshot().actors.filter(actor => actor.kind === 'hero')).toHaveLength(6);
  });

  it('rejects invalid identities and non-finite input, normalizes movement and expires stale controls', () => {
    const { sim, a } = duel();
    expect(() => sim.addPlayer('bad', 'Bad', 'invented')).toThrow('UNKNOWN_HERO');
    expect(() => sim.addPlayer('bot-1', 'Bad', HEROES[0]!.id)).toThrow('INVALID_ID');
    expect(sim.input(a.id, input(1, { moveX: Infinity }))).toBe(false);
    expect(sim.input(a.id, input(1, { yaw: NaN }))).toBe(false);
    expect(sim.input(a.id, input(1, { moveX: 100, moveZ: 100, yaw: 1000, pitch: 100 }))).toBe(true);
    const before = { x: a.x, z: a.z }; sim.step(.05);
    expect(Math.hypot(a.x - before.x, a.z - before.z)).toBeCloseTo(HEROES[0]!.speed * .05);
    expect(sim.input(a.id, input(1, { moveX: -1 }))).toBe(false);
    for (let i = 0; i < 12; i++) sim.step(.05);
    const stopped = { x: a.x, z: a.z }; sim.step(.1); expect({ x: a.x, z: a.z }).toEqual(stopped);
  });

  it('collides with shared buildings and live structures, and a held jump does not auto-repeat', () => {
    const { sim, a } = duel(); a.x = 9; a.z = -28;
    for (let i = 0; i < 40; i++) { sim.input(a.id, input(i + 1, { moveX: 1 })); sim.step(.05); }
    expect(a.x).toBeLessThanOrEqual(10.35); expect(blocked(a.x, a.z)).toBe(false);
    a.x = 0; a.z = -42;
    for (let i = 0; i < 30; i++) { sim.input(a.id, input(i + 50, { moveZ: 1 })); sim.step(.05); }
    expect(a.z).toBeLessThan(-39.4);
    a.x = 0; a.z = 0; let highest = 0;
    for (let i = 0; i < 35; i++) { sim.input(a.id, input(i + 100, { jump: true })); sim.step(.05); highest = Math.max(highest, a.y); }
    expect(highest).toBeGreaterThan(1.5); expect(a.y).toBe(0);
    sim.input(a.id, input(200, { jump: false })); sim.step(.05); sim.input(a.id, input(201, { jump: true })); sim.step(.05); expect(a.y).toBeGreaterThan(0);
  });

  it('charges upgrades only at the base, deduplicates purchases and enforces rank and funds', () => {
    const sim = new ArenaSimulation({ botsPerTeam: 0 }); const a = sim.addPlayer('a', 'Aadi', HEROES[0]!.id);
    const purchase = { type: 'command', id: 'purchase', action: 'upgrade', upgrade: 'power' } as const;
    const result = sim.command(a.id, purchase); expect(result.code).toBe('UPGRADED');
    expect(a.credits).toBe(180 - UPGRADE_COSTS.power); expect(a.upgrades.power).toBe(1);
    expect(sim.command(a.id, purchase)).toEqual(result); expect(a.upgrades.power).toBe(1);
    expect(sim.command(a.id, { ...purchase, id: 'no-funds' }).code).toBe('INSUFFICIENT_CREDITS');
    a.credits = 2000; a.x = 0; a.z = 0;
    expect(sim.command(a.id, { ...purchase, id: 'remote' }).code).toBe('RETURN_TO_BASE');
    Object.assign(a, SPAWNS.sun);
    sim.command(a.id, { ...purchase, id: 'rank2' }); sim.command(a.id, { ...purchase, id: 'rank3' });
    expect(sim.command(a.id, { ...purchase, id: 'max' }).code).toBe('UPGRADE_MAX');
    expect(a.upgrades.power).toBe(3);
  });

  it('owns projectile deaths, respawn, KDA and nearby teammate rewards without friendly fire', () => {
    const { sim, a, b } = duel(), helper = sim.addPlayer('helper', 'Helper', HEROES[2]!.id, 'sun');
    helper.x = 0; helper.z = 0; b.health = 10;
    sim.input(a.id, input(1, { fire: true }));
    for (let i = 0; i < 15; i++) sim.step(.05);
    expect(b.health).toBe(0); expect(b.deaths).toBe(1); expect(b.respawn).toBeGreaterThan(0);
    expect(a.kills).toBe(1); expect(a.credits).toBe(280); expect(helper.credits).toBe(280); expect(helper.health).toBe(helper.maxHealth);
    expect(sim.command(b.id, { type: 'command', id: 'dead-cast', action: 'ability', slot: 0 }).code).toBe('RESPAWNING');
    for (let i = 0; i < 190; i++) sim.step(.05);
    expect(b.health).toBe(b.maxHealth); expect(b.z).toBe(SPAWNS.moon.z - 3); expect(b.deaths).toBe(1);
  });

  it('keeps the core shield until two towers fall, then finishes once from actual projectile damage', () => {
    const sim = new ArenaSimulation({ botsPerTeam: 0 }); const a = sim.addPlayer('a', 'Aadi', HEROES[0]!.id, 'sun'); a.health = a.maxHealth = 10000;
    const core = sim.structures.find(value => value.id === 'moon-core')!;
    a.x = 0; a.z = 68;
    sim.input(a.id, input(1, { fire: true, pitch: Math.atan2(1.8, 7) }));
    for (let i = 0; i < 10; i++) sim.step(.05);
    expect(core.health).toBe(core.maxHealth); expect(core.shielded).toBe(true);
    for (const lane of [0, 1]) {
      const tower = sim.structures.find(value => value.id === `moon-tower-${lane}`)!;
      tower.health = 1; a.x = tower.x; a.z = tower.z - 7; a.fireCooldown = 0;
      sim.input(a.id, input(10 + lane, { fire: true, pitch: Math.atan2(1, 7) }));
      for (let i = 0; i < 10; i++) sim.step(.05);
      expect(tower.health).toBe(0); expect(core.shielded).toBe(lane === 0);
    }
    a.x = 0; a.z = 68; a.fireCooldown = 0; core.health = 1;
    sim.input(a.id, input(20, { fire: true, pitch: Math.atan2(1.8, 7) }));
    for (let i = 0; i < 10; i++) sim.step(.05);
    expect(sim.phase).toBe('finished'); expect(sim.winner).toBe('sun');
    expect(sim.snapshot().projectiles).toHaveLength(0); expect(sim.snapshot().zones).toHaveLength(0);
    expect(sim.snapshot().events.filter(event => event.type === 'victory')).toHaveLength(1);
    const finished = sim.snapshot(); sim.step(1); expect(sim.snapshot()).toEqual(finished);
    expect(sim.command(a.id, { type: 'command', id: 'post-match', action: 'ability', slot: 0 }).code).toBe('MATCH_FINISHED');
  });

  it('collects neutral pickups once with an authoritative cooldown', () => {
    const { sim, a, b } = duel(); const pickup = sim.pickups[0]!; pickup.readyAt = 0; a.x = b.x = pickup.x; a.z = b.z = pickup.z; a.health = b.health = 100;
    sim.step(.05); expect(a.health).toBe(195); expect(b.health).toBe(100); expect(pickup.readyAt).toBeGreaterThan(24);
    sim.step(.05); expect(a.health).toBe(195);
    expect(sim.snapshot().events.filter(event => event.type === 'pickup')).toHaveLength(1);
  });

  it('casts along the newest validated aim without waiting for a movement tick', () => {
    const { sim, a } = duel();
    sim.input(a.id, input(1, { yaw: Math.PI / 2 }));
    expect(sim.command(a.id, { type: 'command', id: 'new-aim', action: 'ability', slot: 0 }).ok).toBe(true);
    const projectile = sim.snapshot().projectiles.find(value => value.owner === a.id)!;
    expect(projectile.vx).toBeGreaterThan(30); expect(Math.abs(projectile.vz)).toBeLessThan(.001);
  });

  it('routes heroes and minion waves through all three lanes past friendly towers', () => {
    const sim = new ArenaSimulation({ seed: 77, duration: 40 });
    const progress = new Set<string>();
    // The outer route is about60m at4.3m/s plus its1s wave lead;20s
    // covers that actual distance while retaining the same all-lanes gate.
    for (let i = 0; i < 400; i++) {
      sim.step(.05);
      for (const actor of sim.actors.values()) if (Math.abs(actor.z) < 34 && actor.health > 0) progress.add(`${actor.team}:${actor.kind}:${actor.lane}`);
    }
    for (const team of ['sun', 'moon']) for (const lane of [0, 1, 2]) {
      expect(progress.has(`${team}:hero:${lane}`), `${team} hero lane ${lane}`).toBe(true);
      expect(progress.has(`${team}:minion:${lane}`), `${team} minion lane ${lane}`).toBe(true);
    }
    expect(sim.snapshot().events.some(event => event.type === 'shot' || event.type === 'hit')).toBe(true);
  });

  it('uses deterministic seeds, bounded snapshots and a finite timer with an honest tiebreak', () => {
    const first = new ArenaSimulation({ seed: 42, duration: 2 }), second = new ArenaSimulation({ seed: 42, duration: 2 });
    for (let i = 0; i < 45; i++) { first.step(.05); second.step(.05); }
    expect(first.snapshot()).toEqual(second.snapshot()); expect(first.phase).toBe('finished'); expect(first.winner).toBe('draw');
    for (const winner of ['sun', 'moon'] as Team[]) {
      const sim = new ArenaSimulation({ botsPerTeam: 0, duration: 1 }); sim.scores[winner] = 1;
      for (let i = 0; i < 20; i++) sim.step(.05);
      expect(sim.winner).toBe(winner); expect(sim.reason).toContain('higher team score');
    }
    const snapshot = first.snapshot(); expect(snapshot.actors.length).toBeLessThanOrEqual(ARENA_RULES.maxActors); expect(snapshot.events.length).toBeLessThanOrEqual(ARENA_RULES.eventHistory);
    snapshot.actors[0]!.health = -999; expect(first.snapshot().actors[0]!.health).toBeGreaterThan(0);
    const replay = new ArenaSimulation({ seed: 42 }); expect(replay.phase).toBe('playing'); expect(replay.time).toBe(0); expect(replay.scores).toEqual({ sun: 0, moon: 0 });
  });

  it('finishes a real bot match when an area cast removes a later actor during the same tick', () => {
    // Seed7 previously crashed at tick1223: Converging Volley removed minion-294
    // before the copied actor-update list reached that now-deleted entity.
    const sim = new ArenaSimulation({ seed: 7 });
    for (let i = 0; i < 9601 && sim.phase === 'playing'; i++) sim.step(.05);
    expect(sim.tick).toBeGreaterThan(1223); expect(sim.phase).toBe('finished');
    expect(sim.time).toBeLessThanOrEqual(480); expect(sim.winner).not.toBeNull();
    expect(sim.snapshot().events.filter(event => event.type === 'victory')).toHaveLength(1);
    expect(sim.snapshot().projectiles).toHaveLength(0); expect(sim.snapshot().zones).toHaveLength(0);
    expect(sim.actors.size).toBeLessThanOrEqual(ARENA_RULES.maxActors);
  });
});
