import { describe, expect, it } from 'vitest';
import { ArenaStepClock } from '../server/clock.js';
import { ArenaSimulation } from '../shared/simulation.js';

describe('arena fixed-step server clock', () => {
  it('advances four actual 20 Hz steps through a 200 ms scheduler delay', () => {
    const clock = new ArenaStepClock(100), sim = new ArenaSimulation({ seed: 9 });
    expect(clock.advance(300, dt => sim.step(dt))).toBe(4);
    expect(sim.tick).toBe(4); expect(sim.time).toBeCloseTo(.2);
    expect(clock.advance(325, dt => sim.step(dt))).toBe(0);
    expect(clock.advance(350, dt => sim.step(dt))).toBe(1);
    expect(sim.time).toBeCloseTo(.25);
  });

  it('produces the same state with regular and delayed callbacks', () => {
    const regular = new ArenaSimulation({ seed: 9 }), delayed = new ArenaSimulation({ seed: 9 });
    const a = new ArenaStepClock(0), b = new ArenaStepClock(0);
    for (let now = 50; now <= 2000; now += 50) a.advance(now, dt => regular.step(dt));
    for (let now = 200; now <= 2000; now += 200) b.advance(now, dt => delayed.step(dt));
    expect(delayed.snapshot()).toEqual(regular.snapshot());
  });

  it('caps a long suspend at one second without accumulating obsolete backlog', () => {
    const clock = new ArenaStepClock(0), steps: number[] = [];
    expect(clock.advance(25, dt => steps.push(dt))).toBe(0);
    expect(clock.advance(5025, dt => steps.push(dt))).toBe(20);
    expect(clock.advance(5050, dt => steps.push(dt))).toBe(1);
    expect(clock.advance(5050, dt => steps.push(dt))).toBe(0);
    expect(clock.advance(NaN, dt => steps.push(dt))).toBe(0);
    expect(steps).toHaveLength(21); expect(steps.every(dt => dt === .05)).toBe(true);
  });
});
