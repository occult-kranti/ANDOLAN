import { describe, expect, it } from 'vitest';
import { acknowledgedHeroAction, lockedCastPlayback, type LockedCastFrame } from '../client/hero-cast-playback';
import { ArenaSimulation } from '../shared/simulation';
import { HEROES, heroById } from '../shared/heroes';
import type { Actor } from '../shared/types';

const ultimate = { type: 'command', action: 'ability', id: 'ultimate', slot: 2 } as const;
function fixture(hero: string, duration = 480) {
  const sim = new ArenaSimulation({ botsPerTeam: 0, duration });
  const actor = sim.addPlayer('caster', 'Caster', hero, 'sun');
  Object.assign(actor, { x: 0, z: 0, yaw: 0 });
  expect(sim.command(actor.id, ultimate).ok).toBe(true);
  return { sim, actor };
}
function advance(sim: ArenaSimulation, seconds: number) {
  for (let remaining = seconds; remaining > 1e-8; remaining -= .05) sim.step(Math.min(.05, remaining));
}
function frame(sim: ArenaSimulation, actor: Actor): LockedCastFrame {
  const snapshot = sim.snapshot(), value = snapshot.actors.find(item => item.id === actor.id)!;
  return { alive: value.health > 0, casting: !!value.cast, castSlot: value.cast?.slot ?? 0,
    castStartedAt: value.cast?.startedAt, castElapsed: value.cast ? snapshot.time - value.cast.startedAt : undefined };
}

describe('authoritative full-body cast playback', () => {
  it.each(['rama', 'hanuman', 'sita'])('%s selects its R pose from snapshot state without needing the start event', hero => {
    const { sim, actor } = fixture(hero); advance(sim, .25);
    // A newly joined renderer has no event-derived animation state.
    const first = lockedCastPlayback(frame(sim, actor), null, 1.6)!;
    expect(first.clip).toBe('cast3'); expect(first.seekSeconds).toBeCloseTo(.25);
    advance(sim, .1);
    expect(lockedCastPlayback(frame(sim, actor), first.key, 1.6)).toMatchObject({ clip: 'cast3', key: first.key, seekSeconds: null });
  });

  it('keeps Hanuman’s same full-body cast during real airborne travel and ends it on landing', () => {
    const { sim, actor } = fixture('hanuman');
    const first = lockedCastPlayback(frame(sim, actor), null, 1.3667)!;
    advance(sim, .9); expect(actor.cast?.phase).toBe('travel'); expect(actor.y).toBeGreaterThan(4);
    expect(lockedCastPlayback(frame(sim, actor), first.key, 1.3667)).toMatchObject({ clip: 'cast3', seekSeconds: null });
    const rejoined = lockedCastPlayback(frame(sim, actor), null, 1.3667)!;
    expect(rejoined.seekSeconds).toBeCloseTo(.9);
    advance(sim, .3); expect(actor.y).toBe(0); expect(lockedCastPlayback(frame(sim, actor), first.key, 1.3667)).toBeNull();
  });

  it('releases full-body selection on actual lethal damage and cannot override defeat', () => {
    const { sim, actor } = fixture('rama'); actor.health = 1;
    const enemy = sim.addPlayer('enemy', 'Enemy', 'arjuna', 'moon'); Object.assign(enemy, { x: 0, z: -5, yaw: 0 });
    const first = lockedCastPlayback(frame(sim, actor), null, 1.6)!;
    expect(sim.command(enemy.id, { ...ultimate, id: 'defeat', slot: 0 }).ok).toBe(true);
    expect(actor.health).toBe(0); expect(lockedCastPlayback(frame(sim, actor), first.key, 1.6)).toBeNull();
    expect(lockedCastPlayback({ alive: false, casting: true, castSlot: 2, castElapsed: .5 }, first.key, 1.6)).toBeNull();
  });

  it('releases a pending pose when the actual match ends before Hanuman lands', () => {
    const { sim, actor } = fixture('hanuman', 1);
    const first = lockedCastPlayback(frame(sim, actor), null, 1.3667)!;
    advance(sim, 1); expect(sim.phase).toBe('finished'); expect(actor.cast).toBeUndefined();
    expect(lockedCastPlayback(frame(sim, actor), first.key, 1.3667)).toBeNull();
  });

  it('distinguishes a later same-slot cast and clamps the one-time rejoin seek to the clip', () => {
    const initial = { alive: true, casting: true, castSlot: 2, castStartedAt: 5, castElapsed: .6 };
    const first = lockedCastPlayback(initial, null, 1.4)!;
    const later = lockedCastPlayback({ ...initial, castStartedAt: 50, castElapsed: 3 }, first.key, 1.4)!;
    expect(later.key).not.toBe(first.key); expect(later.seekSeconds).toBeCloseTo(1.399);
    expect(lockedCastPlayback({ ...initial, castElapsed: Number.NaN }, null, 1.4)?.seekSeconds).toBe(0);
    expect(lockedCastPlayback({ ...initial, casting: false }, first.key, 1.4)).toBeNull();
  });

  it.each(['rama', 'hanuman', 'sita'])('%s does not replay a delayed accepted R receipt after the real cast finishes', hero => {
    const { sim, actor } = fixture(hero);
    const started = lockedCastPlayback(frame(sim, actor), null, 1.7)!;
    const receipt = sim.snapshot().events.find(event => event.type === 'ability' && event.actorId === actor.id)!;
    const ability = heroById(hero).abilities[2];
    // Model updates can precede world.consumeEvents, delaying the receipt even
    // after the last snapshot of the cast has been presented.
    advance(sim, 1.3); expect(actor.cast).toBeUndefined();
    expect(lockedCastPlayback(frame(sim, actor), started.key, 1.7)).toBeNull();
    expect(acknowledgedHeroAction({ cast: receipt.id, shot: 0 }, 0, 0, ability)).toBeNull();
    expect(acknowledgedHeroAction({ cast: receipt.id, shot: 0 }, receipt.id, 0, ability)).toBeNull();
    // The same rule applies when a whole cast elapsed between renders: there is
    // no prior full-body key to identify the receipt as already animated.
    expect(lockedCastPlayback(frame(sim, actor), null, 1.7)).toBeNull();
    expect(acknowledgedHeroAction({ cast: receipt.id, shot: 0 }, -1, -1, ability)).toBeNull();
  });

  it('keeps all 39 untimed ability slots and new primary shots event-driven', () => {
    const ordinary = HEROES.flatMap(hero => hero.abilities).filter(ability => !ability.mechanic);
    expect(ordinary).toHaveLength(39);
    for (const ability of ordinary) {
      expect(acknowledgedHeroAction({ cast: 7, shot: 3 }, 6, 3, ability)).toBe('cast');
      expect(acknowledgedHeroAction({ cast: 7, shot: 3 }, 7, 3, ability)).toBeNull();
    }
    const timed = heroById('rama').abilities[2];
    expect(acknowledgedHeroAction({ cast: 7, shot: 8 }, 6, 3, timed)).toBe('fire');
    expect(acknowledgedHeroAction({ cast: 7, shot: 8 }, 7, 8, timed)).toBeNull();
  });
});
