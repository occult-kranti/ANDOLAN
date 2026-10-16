import type { Actor, ArenaSnapshot, GameEvent } from '../shared/types.js';

/** Optional feedback only. This module never sends commands or changes match rewards. */
export const PRACTICE_GOALS = [
  { id: 'move', title: 'Find your footing', instruction: 'Reach a point 12 metres from your start. Respawning begins a new movement attempt.', completion: 'You moved 12 metres from your starting point.', target: 12 },
  { id: 'hit', title: 'Land a hit', instruction: 'Hit an enemy, structure or neutral with your weapon or a damaging ability.', completion: 'Your hit was confirmed.', target: 1 },
  { id: 'ability', title: 'Try an ability', instruction: 'Use a ready Q, E or R ability. Starting a windup counts, even if it is later interrupted.', completion: 'Your ability started.', target: 1 },
  { id: 'upgrade', title: 'Buy an upgrade', instruction: 'Visit your base forge and spend your credits on one upgrade.', completion: 'Your upgrade rank increased.', target: 1 },
  { id: 'camp', title: 'Earn a camp reward', instruction: 'Earn shared credits or a blessing when a jungle camp is defeated. Camps first appear at 30 seconds.', completion: 'You earned a camp reward.', target: 1 },
] as const;

export type PracticeGoalId = typeof PRACTICE_GOALS[number]['id'];
export interface PracticeGoalState {
  readonly sessionId: string;
  readonly playerId: string;
  readonly goalId: PracticeGoalId;
  readonly room: string;
  readonly seed: number;
  readonly heroId: string;
  readonly team: Actor['team'];
  readonly startedAt: number;
  readonly lastTick: number;
  readonly lastTime: number;
  readonly lastEventId: number;
  readonly origin: Readonly<{ x: number; z: number }> | null;
  readonly deaths: number;
  readonly initialDamage: number;
  readonly initialUpgradeRanks: number;
  readonly current: number;
}
export interface PracticeGoalProgress {
  readonly id: PracticeGoalId;
  readonly title: string;
  readonly instruction: string;
  readonly current: number;
  readonly target: number;
  readonly complete: boolean;
  readonly progressText: string;
  readonly completionText: string;
}

function localActor(snapshot: ArenaSnapshot, playerId: string): Actor | undefined {
  return snapshot.actors.find(actor => actor.id === playerId && actor.kind === 'hero' && actor.connected && !actor.bot);
}
function validSnapshot(snapshot: ArenaSnapshot): boolean {
  return Number.isSafeInteger(snapshot.tick) && snapshot.tick >= 0 && Number.isFinite(snapshot.time) && snapshot.time >= 0;
}
function validEvent(event: GameEvent, time: number): boolean {
  return Number.isSafeInteger(event.id) && event.id > 0 && Number.isFinite(event.time) && event.time >= 0 && event.time <= time;
}
function eventWatermark(snapshot: ArenaSnapshot): number {
  return snapshot.events.reduce((max, event) => validEvent(event, snapshot.time) ? Math.max(max, event.id) : max, 0);
}
function ranks(actor: Actor): number { return actor.upgrades.power + actor.upgrades.vitality + actor.upgrades.tempo; }
function validActor(actor: Actor): boolean {
  return [actor.x, actor.z, actor.health, actor.respawn, actor.deaths, actor.damageDealt, ...Object.values(actor.upgrades)].every(Number.isFinite);
}
function living(actor: Actor): boolean { return actor.health > 0 && actor.respawn <= 0; }

/**
 * Start only after the player chooses a goal. Free play has a null tracker.
 * Keep this state across pause/settings. Leave, replay and an explicit goal change
 * require a new sessionId and a new baseline; do not reuse a saved tracker.
 */
export function startPracticeGoal(snapshot: ArenaSnapshot, playerId: string, goalId: PracticeGoalId, sessionId: string): PracticeGoalState | null {
  const actor = localActor(snapshot, playerId);
  if (!sessionId || !actor || !validActor(actor) || !validSnapshot(snapshot) || snapshot.phase !== 'playing' || !PRACTICE_GOALS.some(goal => goal.id === goalId)) return null;
  return {
    sessionId, playerId, goalId, room: snapshot.room, seed: snapshot.seed, heroId: actor.heroId, team: actor.team,
    startedAt: snapshot.time, lastTick: snapshot.tick, lastTime: snapshot.time, lastEventId: eventWatermark(snapshot),
    origin: living(actor) ? { x: actor.x, z: actor.z } : null, deaths: actor.deaths,
    initialDamage: actor.damageDealt, initialUpgradeRanks: ranks(actor), current: 0,
  };
}

/** Read fresh authoritative observations. Old frames and rolling event repeats grant nothing. */
export function updatePracticeGoal(state: PracticeGoalState | null, snapshot: ArenaSnapshot, sessionId: string): PracticeGoalState | null {
  if (!state || state.sessionId !== sessionId || snapshot.room !== state.room || snapshot.seed !== state.seed) return null;
  if (!validSnapshot(snapshot) || snapshot.tick < state.lastTick || snapshot.time < state.lastTime) return state;
  const actor = localActor(snapshot, state.playerId);
  if (!actor || actor.heroId !== state.heroId || actor.team !== state.team) return null;
  if (!validActor(actor)) return state;
  const events = snapshot.events.filter(event => validEvent(event, snapshot.time) && event.id > state.lastEventId && event.time >= state.startedAt);
  const ownEvents = events.filter(event => event.actorId === state.playerId && event.team === state.team);
  let current = state.current, origin = state.origin;
  if (state.goalId === 'move' && current < 12) {
    // A death/respawn relocates the hero; that is not movement practice.
    if (!living(actor) || actor.deaths !== state.deaths) { origin = living(actor) ? { x: actor.x, z: actor.z } : null; current = 0; }
    else if (!origin) origin = { x: actor.x, z: actor.z };
    else { const distance = Math.hypot(actor.x - origin.x, actor.z - origin.z); if (Number.isFinite(distance)) current = Math.min(12, Math.max(current, distance)); }
  } else if (state.goalId === 'hit' && (actor.damageDealt > state.initialDamage || ownEvents.some(event => event.type === 'hit' && event.targetId && event.targetId !== state.playerId))) current = 1;
  else if (state.goalId === 'ability' && ownEvents.some(event => event.type === 'ability')) current = 1;
  else if (state.goalId === 'upgrade' && ranks(actor) > state.initialUpgradeRanks) current = 1;
  else if (state.goalId === 'camp' && events.some(event =>
    event.team === state.team && (
      (event.type === 'camp' && event.sharedAwards?.some(award => award.actorId === state.playerId && Number.isFinite(award.amount) && award.amount > 0)) ||
      (event.type === 'buff' && event.actorId === state.playerId && (event.buff === 'ward' || event.buff === 'vigor' || event.buff === 'haste'))
    ))) current = 1;
  return { ...state, current, origin, deaths: actor.deaths, lastTick: snapshot.tick, lastTime: snapshot.time, lastEventId: Math.max(state.lastEventId, eventWatermark(snapshot)) };
}

export function practiceGoalProgress(state: PracticeGoalState | null): PracticeGoalProgress | null {
  if (!state) return null;
  const goal = PRACTICE_GOALS.find(definition => definition.id === state.goalId)!;
  const complete = state.current >= goal.target;
  return {
    id: goal.id, title: goal.title, instruction: goal.instruction, current: state.current, target: goal.target, complete,
    progressText: complete ? goal.completion : goal.id === 'move' ? `${Math.floor(state.current)} / 12 metres from your start` : 'Waiting for your next action',
    completionText: goal.completion,
  };
}
