import type { Actor, Team } from '../shared/types.js';

export const CONTROL_RULES = Object.freeze({
  x: 0, z: 0, radius: 8, captureSeconds: 6,
  targetScore: 60, scorePerSecond: 1, duration: 240,
});

export interface ControlPointSnapshot {
  x: number;
  z: number;
  radius: number;
  owner: Team | null;
  capturing: Team | null;
  progress: number;
  contested: boolean;
  occupants: { sun: number; moon: number };
  scores: { sun: number; moon: number };
  targetScore: number;
}

function initialState(): ControlPointSnapshot {
  return {
    x: CONTROL_RULES.x, z: CONTROL_RULES.z, radius: CONTROL_RULES.radius,
    owner: null, capturing: null, progress: 0, contested: false,
    occupants: { sun: 0, moon: 0 }, scores: { sun: 0, moon: 0 },
    targetScore: CONTROL_RULES.targetScore,
  };
}

/** Deterministic control-point rules, independent of the arena's combat rules. */
export class ControlPoint {
  private state = initialState();

  snapshot(): ControlPointSnapshot {
    return {
      ...this.state,
      occupants: { ...this.state.occupants },
      scores: { ...this.state.scores },
    };
  }

  reset(): void {
    this.state = initialState();
  }

  step(actors: readonly Actor[], dt: number): { captured: Team | null; winner: Team | null } {
    const state = this.state;
    const winner = state.scores.sun >= state.targetScore ? 'sun'
      : state.scores.moon >= state.targetScore ? 'moon' : null;
    // A finished objective is terminal. Invalid elapsed times never advance it.
    if (winner || !Number.isFinite(dt) || dt <= 0) return { captured: null, winner };
    const seconds = Math.min(dt, 0.25);
    state.occupants = { sun: 0, moon: 0 };
    for (const actor of actors) {
      if (actor.kind !== 'hero' || !actor.connected || !(actor.health > 0)
        || !(actor.respawn <= 0) || !Number.isFinite(actor.y) || actor.y > 2
        || actor.unitArchetype === 'summon' || actor.minionRole === 'summon') continue;
      const dx = actor.x - state.x;
      const dz = actor.z - state.z;
      if (dx * dx + dz * dz <= state.radius * state.radius) state.occupants[actor.team]++;
    }

    const { sun, moon } = state.occupants;
    state.contested = sun > 0 && moon > 0;
    // Additional heroes change occupancy only; capture and score rates stay fixed.
    if (state.contested) return { captured: null, winner: null };
    const team: Team | null = sun > 0 ? 'sun' : moon > 0 ? 'moon' : null;
    if (!team) {
      state.progress = Math.max(0, state.progress - seconds / CONTROL_RULES.captureSeconds);
      if (state.progress < 1e-9) {
        state.progress = 0;
        state.capturing = null;
      }
      return { captured: null, winner: null };
    }

    if (state.owner === team) {
      // An uncontested owner immediately clears an unfinished hostile capture.
      state.capturing = null;
      state.progress = 0;
      const score = state.scores[team] + seconds * CONTROL_RULES.scorePerSecond;
      state.scores[team] = score >= state.targetScore - 1e-9 ? state.targetScore : score;
      return { captured: null, winner: state.scores[team] >= state.targetScore ? team : null };
    }

    if (state.capturing !== team) {
      state.capturing = team;
      state.progress = 0;
    }
    state.progress = Math.min(1, state.progress + seconds / CONTROL_RULES.captureSeconds);
    // Tolerate accumulated floating-point error at the six-second boundary.
    if (state.progress >= 1 - 1e-9) {
      state.owner = team;
      state.capturing = null;
      state.progress = 0;
      return { captured: team, winner: null };
    }
    return { captured: null, winner: null };
  }
}
