import { describe, expect, it } from 'vitest';
import { ControlPoint } from '../reference/objective.js';
import { ArenaSimulation } from '../shared/simulation.js';
import type { Actor, Team } from '../shared/types.js';

/** These are explicit actor-placement fixtures for the original objective rules,
 * not evidence of a browser player travelling to or winning the point. */
function occupant(id: string, team: Team, fields: Partial<Actor> = {}): Actor {
  const simulation = new ArenaSimulation({ botsPerTeam: 0, seed: 31 });
  return { ...simulation.addPlayer(id, id, 'rama', team), x: 0, z: 0, ...fields };
}

function advance(point: ControlPoint, actors: Actor[], seconds: number) {
  const results: ReturnType<ControlPoint['step']>[] = [];
  for (let step = 0; step < Math.round(seconds / .05); step++) results.push(point.step(actors, .05));
  return results;
}

describe('original hybrid control point — labelled deterministic placement fixtures', () => {
  it('counts only living, connected, grounded heroes inside the inclusive radius', () => {
    const point = new ControlPoint();
    const eligible = occupant('edge', 'sun', { x: 8, y: 2 });
    const excluded = [
      occupant('outside', 'moon', { x: 8.001 }),
      occupant('airborne', 'moon', { y: 2.001 }),
      occupant('dead', 'moon', { health: 0 }),
      occupant('respawning', 'moon', { respawn: .05 }),
      occupant('disconnected', 'moon', { connected: false }),
      occupant('lane-unit', 'moon', { kind: 'minion' }),
      occupant('summon', 'moon', { unitArchetype: 'summon' }),
      occupant('nonfinite-position', 'moon', { x: NaN }),
    ];
    point.step([eligible, ...excluded], .05);
    expect(point.snapshot()).toMatchObject({ occupants: { sun: 1, moon: 0 }, contested: false, capturing: 'sun' });
  });

  it('takes six uncontested seconds regardless of friendly headcount and does not score on the capture tick', () => {
    const first = new ControlPoint(), crowded = new ControlPoint();
    const sun = occupant('sun-one', 'sun'), helper = occupant('sun-two', 'sun');
    advance(first, [sun], 5.95); advance(crowded, [sun, helper], 5.95);
    expect(first.snapshot().owner).toBeNull();
    expect(crowded.snapshot().progress).toBeCloseTo(first.snapshot().progress, 10);
    expect(first.step([sun], .05)).toEqual({ captured: 'sun', winner: null });
    expect(crowded.step([sun, helper], .05)).toEqual({ captured: 'sun', winner: null });
    expect(first.snapshot().scores).toEqual({ sun: 0, moon: 0 });
    expect(crowded.snapshot().scores).toEqual({ sun: 0, moon: 0 });
    advance(first, [sun], 1); advance(crowded, [sun, helper], 1);
    expect(first.snapshot().scores.sun).toBeCloseTo(1, 10);
    expect(crowded.snapshot().scores.sun).toBeCloseTo(1, 10);
  });

  it('freezes both unfinished capture and owned scoring while opponents contest', () => {
    const point = new ControlPoint(), sun = occupant('sun', 'sun'), moon = occupant('moon', 'moon');
    advance(point, [sun], 3);
    const progress = point.snapshot().progress;
    advance(point, [sun, moon], 4);
    expect(point.snapshot()).toMatchObject({ contested: true, owner: null, scores: { sun: 0, moon: 0 } });
    expect(point.snapshot().progress).toBeCloseTo(progress, 10);
    advance(point, [sun], 3); advance(point, [sun], 2);
    expect(point.snapshot().scores.sun).toBeCloseTo(2, 10);
    advance(point, [sun, moon], 4);
    expect(point.snapshot()).toMatchObject({ owner: 'sun', contested: true });
    expect(point.snapshot().scores.sun).toBeCloseTo(2, 10);
  });

  it('keeps an empty owner without income, decays partial capture and lets the returning owner clear hostile progress', () => {
    const point = new ControlPoint(), sun = occupant('sun', 'sun'), moon = occupant('moon', 'moon');
    advance(point, [sun], 6);
    advance(point, [], 4);
    expect(point.snapshot()).toMatchObject({ owner: 'sun', scores: { sun: 0, moon: 0 } });
    advance(point, [moon], 3);
    expect(point.snapshot().progress).toBeCloseTo(.5, 10);
    advance(point, [], 1.5);
    expect(point.snapshot()).toMatchObject({ owner: 'sun', capturing: 'moon' });
    expect(point.snapshot().progress).toBeCloseTo(.25, 10);
    point.step([sun], .05);
    expect(point.snapshot()).toMatchObject({ owner: 'sun', capturing: null, progress: 0 });
    advance(point, [moon], 6);
    expect(point.snapshot()).toMatchObject({ owner: 'moon', scores: { moon: 0 } });
  });

  it('bounds one delayed call to250ms and ignores invalid elapsed values', () => {
    const point = new ControlPoint(), sun = occupant('sun', 'sun');
    const initial = point.snapshot();
    for (const elapsed of [0, -.05, NaN, Infinity]) point.step([sun], elapsed);
    expect(point.snapshot()).toEqual(initial);
    point.step([sun], 10);
    expect(point.snapshot().progress).toBeCloseTo(.25 / 6, 10);
    expect(point.snapshot().owner).toBeNull();
  });

  it('finishes at60 points, then leaves the completed state unchanged until reset', () => {
    const point = new ControlPoint(), sun = occupant('sun', 'sun'), moon = occupant('moon', 'moon');
    const captureEvents = advance(point, [sun], 6).filter(result => result.captured !== null);
    expect(captureEvents).toEqual([{ captured: 'sun', winner: null }]);
    advance(point, [sun], 59.95);
    expect(point.snapshot().scores.sun).toBeLessThan(60);
    expect(point.step([sun], .05)).toEqual({ captured: null, winner: 'sun' });
    const finished = point.snapshot();
    advance(point, [moon], 10);
    expect(point.snapshot()).toEqual(finished);
    point.reset();
    expect(point.snapshot()).toMatchObject({ owner: null, capturing: null, progress: 0, contested: false, occupants: { sun: 0, moon: 0 }, scores: { sun: 0, moon: 0 } });
  });

  it('returns independent snapshots that cannot mutate objective ownership or score', () => {
    const point = new ControlPoint();
    const external = point.snapshot();
    external.owner = 'moon'; external.scores.moon = 60; external.occupants.moon = 8;
    expect(point.snapshot()).toMatchObject({ owner: null, scores: { moon: 0 }, occupants: { moon: 0 } });
  });
});
