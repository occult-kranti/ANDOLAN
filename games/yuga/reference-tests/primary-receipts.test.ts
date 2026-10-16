import { describe, expect, it, vi } from 'vitest';
import { ReferenceLab } from '../reference/controller.js';
import { ARENA_RULES, ArenaSimulation, type PrimaryShotReceipt } from '../shared/simulation.js';
import type { ArenaInput } from '../shared/types.js';

const input = (seq = 1, fire = true): ArenaInput => ({ type: 'input', seq, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire, jump: false });

/** Explicit deterministic capacity fixture, not an encounter a browser earned. */
function fillProjectiles(simulation: ArenaSimulation) {
  for (let index = 0; index < ARENA_RULES.maxProjectiles; index++) simulation.projectiles.push({
    id: `capacity-fixture-${index}`, owner: 'capacity-fixture', team: 'moon',
    x: 100, z: 100, y: 20, vx: 0, vy: 0, vz: 0,
    damage: 1, radius: .1, life: 10, color: '#ffffff',
  });
}

/** Seventy stationary target fixtures receive real zone damage after the hero
 * fires, evicting that earlier shot from the64-event presentation history. */
function fillDamageTargets(simulation: ArenaSimulation, ownerId: string) {
  const owner = simulation.actors.get(ownerId)!;
  Object.assign(owner, { x: 0, z: -6 });
  for (let index = 0; index < 70; index++) {
    const target = { ...structuredClone(owner), id: `pressure-fixture-${index}`, kind: 'minion' as const,
      team: 'moon' as const, connected: false, bot: true, x: 0, z: 0, health: 100, maxHealth: 100 };
    simulation.actors.set(target.id, target);
  }
  simulation.zones.push({ id: 'pressure-zone-fixture', owner: ownerId, team: 'sun', kind: 'slow', x: 0, z: 0, radius: 10, life: 2, duration: 2, power: 1, color: '#ffffff' });
}

describe('primary-shot observer — labelled capacity/history fixtures', () => {
  it('leaves identical seeded arena snapshots unchanged when an observer is installed', () => {
    let observed = 0;
    const plain = new ArenaSimulation({ botsPerTeam: 0, seed: 512 });
    const watched = new ArenaSimulation({ botsPerTeam: 0, seed: 512, onPrimaryShot: () => { observed++; } });
    plain.addPlayer('same-player', 'Same', 'rama', 'sun');
    watched.addPlayer('same-player', 'Same', 'rama', 'sun');
    for (let step = 0; step < 80; step++) {
      const intent = { ...input(step + 1), moveX: step < 20 ? 1 : 0, jump: step === 30, pitch: .5 };
      plain.input('same-player', intent); watched.input('same-player', intent);
      plain.step(.05); watched.step(.05);
      expect(watched.snapshot()).toEqual(plain.snapshot());
    }
    expect(observed).toBeGreaterThan(0);
  });

  it('delivers one immutable receipt for a real primary projectile and none for a capacity-rejected attempt', () => {
    const receipts: Readonly<PrimaryShotReceipt>[] = [];
    const simulation = new ArenaSimulation({ botsPerTeam: 0, onPrimaryShot: receipt => receipts.push(receipt) });
    const actor = simulation.addPlayer('observer-player', 'Observer', 'rama', 'sun');
    simulation.input(actor.id, input()); simulation.step(.05);
    expect(receipts).toHaveLength(1);
    expect(receipts[0]).toMatchObject({ actorId: actor.id, tick: 1, time: .05 });
    expect(Object.isFrozen(receipts[0])).toBe(true);
    expect(simulation.snapshot().projectiles.some(projectile => projectile.id === receipts[0]!.projectileId)).toBe(true);

    const rejected: Readonly<PrimaryShotReceipt>[] = [];
    const capped = new ArenaSimulation({ botsPerTeam: 0, onPrimaryShot: receipt => rejected.push(receipt) });
    const cappedActor = capped.addPlayer('capped-player', 'Capped', 'rama', 'sun');
    fillProjectiles(capped); capped.input(cappedActor.id, input()); capped.step(.05);
    expect(cappedActor.fireCooldown).toBeGreaterThan(0); // The attempt ran; cooldown alone would be false evidence.
    expect(rejected).toEqual([]);
    expect(capped.snapshot().events.some(event => event.type === 'shot' && event.actorId === cappedActor.id)).toBe(false);
  });

  it('retains the authoritative receipt when actual later damage evicts its shot event in the same tick', () => {
    const receipts: Readonly<PrimaryShotReceipt>[] = [];
    const simulation = new ArenaSimulation({ botsPerTeam: 0, onPrimaryShot: receipt => receipts.push(receipt) });
    const actor = simulation.addPlayer('pressure-player', 'Pressure', 'rama', 'sun');
    fillDamageTargets(simulation, actor.id);
    simulation.input(actor.id, input()); simulation.step(.05);
    const state = simulation.snapshot();
    expect(receipts).toHaveLength(1);
    expect(state.events).toHaveLength(ARENA_RULES.eventHistory);
    expect(state.events.every(event => event.type === 'hit')).toBe(true);
    expect(state.events.some(event => event.type === 'shot' && event.actorId === actor.id)).toBe(false);
    expect(state.actors.filter(value => value.id.startsWith('pressure-fixture-') && value.health < 100)).toHaveLength(70);
    expect(receipts[0]).toMatchObject({ actorId: actor.id, tick: state.tick, time: state.time });
  });

  it('excludes immediate and delayed ability projectiles and genuine minion fire', () => {
    const receipts: Readonly<PrimaryShotReceipt>[] = [];
    const simulation = new ArenaSimulation({ botsPerTeam: 0, onPrimaryShot: receipt => receipts.push(receipt) });
    const hero = simulation.addPlayer('ability-player', 'Ability', 'rama', 'sun');
    simulation.input(hero.id, input(1, false));
    expect(simulation.command(hero.id, { type: 'command', id: 'ability-q', action: 'ability', slot: 0 }).ok).toBe(true);
    expect(simulation.command(hero.id, { type: 'command', id: 'ability-r', action: 'ability', slot: 2 }).ok).toBe(true);
    for (let step = 0; step < 35; step++) simulation.step(.05);
    expect(simulation.snapshot().events.filter(event => event.actorId === hero.id && event.type === 'shot').length).toBeGreaterThan(1);
    expect(receipts).toEqual([]);

    const target = simulation.addPlayer('human-target', 'Target', 'rama', 'moon');
    Object.assign(target, { x: 0, z: 0 });
    const minion = [...simulation.actors.values()].find(actor => actor.team === 'sun' && actor.kind === 'minion')!;
    Object.assign(minion, { x: 0, z: -6, fireCooldown: 0 });
    for (let step = 0; step < 10; step++) simulation.step(.05);
    expect(simulation.snapshot().events.some(event => event.actorId === minion.id && event.type === 'shot')).toBe(true);
    expect(receipts).toEqual([]);
  });

  it.each(['capacity rejection', 'history eviction'] as const)('keeps lab ammunition correct under%s', scenario => {
    const realStep = ArenaSimulation.prototype.step;
    let installed = false;
    const observer = vi.spyOn(ArenaSimulation.prototype, 'step').mockImplementation(function (this: ArenaSimulation, elapsed: number) {
      if (!installed) {
        installed = true;
        if (scenario === 'capacity rejection') fillProjectiles(this);
        else fillDamageTargets(this, 'reference-player');
      }
      realStep.call(this, elapsed);
    });
    const lab = new ReferenceLab({ experiment: 'lane-economy', heroId: 'rama', seed: 4 });
    try {
      lab.input(input(), lab.epoch); lab.step(.05);
      const state = lab.snapshot();
      expect(installed).toBe(true);
      expect(state.weapons[lab.localId]!.ammo).toBe(scenario === 'capacity rejection' ? 12 : 11);
      expect(state.arena.actors.find(actor => actor.id === lab.localId)!.fireCooldown).toBeGreaterThan(0);
      expect(state.arena.events.some(event => event.actorId === lab.localId && event.type === 'shot')).toBe(false);
      if (scenario === 'history eviction') expect(state.arena.events).toHaveLength(64);
    } finally {
      lab.dispose(); observer.mockRestore();
    }
  });
});
