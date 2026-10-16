import { describe, expect, it } from 'vitest';
import { DEFAULT_BINDINGS, actionHeld, bindingProblem, driveThrottle, restoreBindings } from '../apps/client/src/controls';

describe('keyboard, touch and driving controls', () => {
  it('rejects duplicate/reserved keys and restores only a valid complete mapping', () => {
    expect(bindingProblem('KeyF', DEFAULT_BINDINGS, 'forward')).toContain('vehicle');
    for (const code of ['KeyJ', 'KeyH', 'KeyC', 'Escape', 'Space', 'Tab']) expect(bindingProblem(code, DEFAULT_BINDINGS, 'forward')).not.toBeNull();
    expect(restoreBindings({ forward: 'KeyF' })).toEqual(DEFAULT_BINDINGS);
    const swapped = { ...DEFAULT_BINDINGS, forward: 'KeyS', back: 'KeyW' };
    expect(restoreBindings(swapped)).toEqual(swapped);
  });
  it('keeps touch actions working after keyboard remapping', () => {
    const rebound = { ...DEFAULT_BINDINGS, forward: 'KeyI' };
    expect(actionHeld('forward', rebound, new Set(), new Set(['forward']))).toBe(true);
    expect(actionHeld('forward', rebound, new Set(['KeyI']), new Set())).toBe(true);
    expect(actionHeld('forward', rebound, new Set(['KeyW']), new Set())).toBe(false);
  });
  it('preserves full forward and reverse braking with assistance enabled', () => {
    expect(driveThrottle(-1, 12, true)).toBe(-1);
    expect(driveThrottle(1, -8, true)).toBe(1);
    expect(driveThrottle(1, 12, true)).toBe(.55);
    expect(driveThrottle(-1, -8, true)).toBe(-.55);
    expect(driveThrottle(1, 0, true)).toBe(.55);
  });
});
