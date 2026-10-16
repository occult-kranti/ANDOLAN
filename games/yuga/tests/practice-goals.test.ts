import { describe, expect, it } from 'vitest';
import { PRACTICE_GOALS, practiceGoalProgress, startPracticeGoal, updatePracticeGoal, type PracticeGoalId, type PracticeGoalState } from '../client/practice-goals.js';
import { ArenaSimulation } from '../shared/simulation.js';
import type { ArenaSnapshot, GameEvent } from '../shared/types.js';

function fixture() {
  const sim = new ArenaSimulation({ room: 'PRACTICE', seed: 7, botsPerTeam: 0 });
  sim.addPlayer('self', 'Practice player', 'rama', 'sun');
  return { sim, snapshot: sim.snapshot() };
}
function begin(snapshot: ArenaSnapshot, goal: PracticeGoalId): PracticeGoalState { return startPracticeGoal(snapshot, 'self', goal, 'session-1')!; }
function advance(state: PracticeGoalState, snapshot: ArenaSnapshot): PracticeGoalState { return updatePracticeGoal(state, snapshot, 'session-1')!; }
function event(fields: Partial<GameEvent> = {}): GameEvent { return { id: 1, type: 'hit', time: 1, actorId: 'self', team: 'sun', x: 0, z: 0, label: '22', color: '#fff', targetId: 'enemy', ...fields }; }
function next(snapshot: ArenaSnapshot, events: GameEvent[] = []): ArenaSnapshot { return { ...structuredClone(snapshot), tick: snapshot.tick + 1, time: snapshot.time + 1, events }; }
function freeze(value: object): void { Object.freeze(value); for (const entry of Object.values(value)) if (entry && typeof entry === 'object') freeze(entry); }

describe('optional practice-goal feedback', () => {
  it('keeps free play empty and offers only optional goals with honest, specific copy', () => {
    const { snapshot } = fixture();
    expect(updatePracticeGoal(null, snapshot, 'session-1')).toBeNull(); expect(practiceGoalProgress(null)).toBeNull();
    expect(new Set(PRACTICE_GOALS.map(goal => goal.id)).size).toBe(5);
    expect(PRACTICE_GOALS.find(goal => goal.id === 'hit')?.instruction).toContain('damaging ability');
    expect(PRACTICE_GOALS.find(goal => goal.id === 'ability')?.instruction).toContain('interrupted');
    expect(PRACTICE_GOALS.find(goal => goal.id === 'camp')?.instruction).toContain('30 seconds');
  });

  it('baselines existing receipts, damage and upgrade ranks instead of awarding past actions', () => {
    const { snapshot } = fixture(); snapshot.tick = 20; snapshot.time = 1;
    Object.assign(snapshot.actors[0]!, { damageDealt: 100, upgrades: { power: 1, vitality: 1, tempo: 0 } });
    snapshot.events = [event(), event({ id: 2, type: 'ability' }), event({ id: 3, type: 'upgrade' }), event({ id: 4, type: 'camp', sharedAwards: [{ actorId: 'self', amount: 30 }] })];
    for (const goal of PRACTICE_GOALS) expect(practiceGoalProgress(advance(begin(snapshot, goal.id), next(snapshot, snapshot.events)))?.complete).toBe(false);
  });

  it('tracks actual authoritative movement to twelve metres without changing the simulation or wallet', () => {
    const { sim } = fixture(); let state = begin(sim.snapshot(), 'move');
    for (let tick = 0; tick < 100 && state.current < 12; tick++) {
      sim.input('self', { type: 'input', seq: tick, moveX: 0, moveZ: 1, yaw: 0, pitch: 0, fire: false, jump: false }); sim.step(.05);
      const snapshot = sim.snapshot(), before = structuredClone(snapshot); freeze(snapshot);
      state = advance(state, snapshot); expect(snapshot).toEqual(before); expect(sim.snapshot()).toEqual(before);
    }
    expect(practiceGoalProgress(state)).toMatchObject({ id: 'move', complete: true, current: 12, target: 12 });
    expect(sim.actors.get('self')!.credits).toBe(180);
  });

  it('preserves earned progress across pause/settings, repeated frames and walking back', () => {
    const { snapshot } = fixture(); let state = begin(snapshot, 'move'); const moved = next(snapshot); moved.actors[0]!.z += 7.6;
    state = advance(state, moved); expect(practiceGoalProgress(state)?.progressText).toBe('7 / 12 metres from your start');
    const pausedState = state; freeze(pausedState);
    state = advance(pausedState, moved); expect(state.current).toBeCloseTo(7.6);
    const back = next(moved); back.actors[0]!.z = snapshot.actors[0]!.z;
    expect(advance(state, back).current).toBeCloseTo(7.6);
  });

  it('does not count death or respawn relocation as movement and preserves already-completed goals', () => {
    const { snapshot } = fixture(); let state = begin(snapshot, 'move');
    const dead = next(snapshot); Object.assign(dead.actors[0]!, { x: 50, health: 0, deaths: 1, respawn: 8 });
    state = advance(state, dead); expect(state.current).toBe(0); expect(state.origin).toBeNull();
    const respawn = next(dead); Object.assign(respawn.actors[0]!, { x: 0, health: 300, respawn: 0 });
    state = advance(state, respawn); expect(state.current).toBe(0);
    const moved = next(respawn); moved.actors[0]!.z += 12;
    state = advance(state, moved); expect(state.current).toBe(12);
    const deadAgain = next(moved); Object.assign(deadAgain.actors[0]!, { health: 0, deaths: 2, respawn: 8 });
    expect(advance(state, deadAgain).current).toBe(12);
    // A snapshot gap may contain the entire death/respawn; the deaths counter catches it.
    const skipped = next(snapshot); Object.assign(skipped.actors[0]!, { x: 50, deaths: 1 });
    expect(advance(begin(snapshot, 'move'), skipped).current).toBe(0);
  });

  it('waits for an actual hit, rather than treating a primary shot as a hit', () => {
    const { sim } = fixture(); sim.addPlayer('enemy', 'Target', 'ravana', 'moon');
    // Controlled unit-test positions; all subsequent hit resolution uses real projectiles.
    Object.assign(sim.actors.get('self')!, { x: 0, z: 0 }); Object.assign(sim.actors.get('enemy')!, { x: 0, z: 8 });
    let state = begin(sim.snapshot(), 'hit');
    sim.input('self', { type: 'input', seq: 1, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: true, jump: false }); sim.step(.05);
    state = advance(state, sim.snapshot()); expect(state.current).toBe(0);
    for (let tick = 0; tick < 10; tick++) { sim.step(.05); state = advance(state, sim.snapshot()); }
    expect(state.current).toBe(1); expect(sim.actors.get('enemy')!.health).toBeLessThan(sim.actors.get('enemy')!.maxHealth);
  });

  it('accepts shield-hit receipts and durable damage totals when a hit event has rolled out', () => {
    const { snapshot } = fixture(), state = begin(snapshot, 'hit');
    expect(advance(state, next(snapshot, [event({ label: '0' })])).current).toBe(1);
    const evicted = next(snapshot); evicted.actors[0]!.damageDealt += 24;
    expect(advance(state, evicted).current).toBe(1);
    expect(advance(state, next(snapshot, [event({ actorId: 'ally' }), event({ id: 2, actorId: 'enemy', team: 'moon' })])).current).toBe(0);
  });

  it('counts an accepted real ability, including same-tick snapshots, but not a rejected cast', () => {
    const { sim } = fixture(); let state = begin(sim.snapshot(), 'ability');
    expect(sim.command('self', { type: 'command', id: 'cast-1', action: 'ability', slot: 0 }).ok).toBe(true);
    state = advance(state, sim.snapshot()); expect(state.current).toBe(1);
    const restarted = startPracticeGoal(sim.snapshot(), 'self', 'ability', 'new-goal')!;
    expect(sim.command('self', { type: 'command', id: 'cast-2', action: 'ability', slot: 0 }).ok).toBe(false);
    expect(updatePracticeGoal(restarted, sim.snapshot(), 'new-goal')!.current).toBe(0);
    sim.command('self', { type: 'command', id: 'cast-1', action: 'ability', slot: 0 });
    expect(updatePracticeGoal(restarted, sim.snapshot(), 'new-goal')!.current).toBe(0);
  });

  it('requires an authoritative upgrade rank increase, not wallet changes or rejected purchases', () => {
    const { sim } = fixture(); const state = begin(sim.snapshot(), 'upgrade');
    expect(sim.command('self', { type: 'command', id: 'upgrade-1', action: 'upgrade', upgrade: 'power' }).ok).toBe(true);
    const bought = sim.snapshot(); expect(advance(state, bought).current).toBe(1);
    const restarted = begin(bought, 'upgrade');
    expect(sim.command('self', { type: 'command', id: 'upgrade-2', action: 'upgrade', upgrade: 'power' }).ok).toBe(false);
    expect(advance(restarted, sim.snapshot()).current).toBe(0);
    const creditOnly = next(bought); creditOnly.actors[0]!.credits += 30; expect(advance(restarted, creditOnly).current).toBe(0);
  });

  it('requires a positive local camp-credit or blessing receipt, not someone else clearing a camp', () => {
    const { snapshot } = fixture(), state = begin(snapshot, 'camp');
    for (const receipt of [event({ type: 'camp' }), event({ type: 'camp', sharedAwards: [{ actorId: 'ally', amount: 30 }] }), event({ type: 'camp', sharedAwards: [{ actorId: 'self', amount: 0 }] }), event({ type: 'gold', amount: 30, reward: 'secure' }), event({ type: 'pickup', buff: 'ward' })]) {
      expect(advance(state, next(snapshot, [receipt])).current).toBe(0);
    }
    expect(advance(state, next(snapshot, [event({ type: 'camp', actorId: 'ally', sharedAwards: [{ actorId: 'self', amount: 2 }] })])).current).toBe(1);
    expect(advance(state, next(snapshot, [event({ type: 'buff', buff: 'ward' })])).current).toBe(1);
    expect(advance(state, next(snapshot, [event({ type: 'buff', actorId: 'ally', buff: 'ward' })])).current).toBe(0);
  });

  it('ignores stale frames, repeated or pre-session events and non-finite future event watermarks', () => {
    const { snapshot } = fixture(); snapshot.tick = 20; snapshot.time = 1; snapshot.events = [event({ type: 'shot', id: 10 })];
    let state = begin(snapshot, 'ability');
    const old = { ...next(snapshot, [event({ id: 11, type: 'ability' })]), tick: 19 }; expect(advance(state, old)).toBe(state);
    state = advance(state, next(snapshot, [event({ id: 10, type: 'ability' }), event({ id: 11, time: .5, type: 'ability' }), event({ id: Number.MAX_SAFE_INTEGER, time: Infinity, type: 'ability' })]));
    expect(state.current).toBe(0); expect(state.lastEventId).toBe(11);
    const fresh = next(snapshot, [event({ id: 12, time: 2, type: 'ability' })]); state = advance(state, fresh); expect(state.current).toBe(1);
    expect(advance(state, fresh).current).toBe(1);
  });

  it('resets by explicit session identity for leave/replay/goal changes and stops on identity loss', () => {
    const { snapshot } = fixture(), state = begin(snapshot, 'hit');
    expect(updatePracticeGoal(state, snapshot, 'replay-2')).toBeNull();
    expect(advance(state, { ...snapshot, room: 'OTHER' })).toBeNull(); expect(advance(state, { ...snapshot, seed: 99 })).toBeNull();
    const disconnected = next(snapshot); disconnected.actors[0]!.connected = false; expect(advance(state, disconnected)).toBeNull();
    expect(advance(state, { ...snapshot, actors: [] })).toBeNull();
    const withOldHit = next(snapshot, [event()]); const replay = startPracticeGoal(withOldHit, 'self', 'hit', 'replay-2')!;
    expect(updatePracticeGoal(replay, withOldHit, 'replay-2')!.current).toBe(0);
  });

  it('handles a dead selection, final-frame receipts and invalid observations without false completion', () => {
    const { snapshot } = fixture(); const dead = structuredClone(snapshot); Object.assign(dead.actors[0]!, { health: 0, respawn: 5 });
    expect(begin(dead, 'move').origin).toBeNull();
    const state = begin(snapshot, 'move'), invalid = next(snapshot); invalid.actors[0]!.x = Infinity;
    expect(advance(state, invalid)).toBe(state);
    expect(advance(state, { ...snapshot, time: NaN })).toBe(state);
    const finished: ArenaSnapshot = { ...next(snapshot, [event()]), phase: 'finished' };
    expect(advance(begin(snapshot, 'hit'), finished).current).toBe(1); expect(startPracticeGoal(finished, 'self', 'hit', 'new')).toBeNull();
  });

  it('does not mutate frozen snapshots or states, and returns detached presentation data', () => {
    const { snapshot } = fixture(); const before = structuredClone(snapshot); freeze(snapshot);
    const state = begin(snapshot, 'ability'); freeze(state);
    const changed = next(snapshot, [event({ type: 'ability' })]); freeze(changed);
    const updated = advance(state, changed), progress = practiceGoalProgress(updated)!;
    expect(updated).not.toBe(state); expect(state.current).toBe(0); expect(snapshot).toEqual(before);
    Object.assign(progress, { current: 999 }); expect(updated.current).toBe(1);
  });
});
