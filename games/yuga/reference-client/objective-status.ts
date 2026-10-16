import type { Team } from '../shared/types';
import type { ControlPointSnapshot } from '../reference/objective';

/** Presentation only: never advances or predicts the controller's objective. */
export function objectiveStatus(point: ControlPointSnapshot, localTeam: Team): { state: 'contested' | 'capturing' | 'scoring' | 'absent' | 'unclaimed'; text: string } {
  const team = (value: Team) => value === localTeam ? 'Your team' : 'Rivals';
  if (point.contested) return { state: 'contested', text: 'CONTESTED · Capture & scoring paused' };
  if (point.capturing && point.occupants[point.capturing] > 0) return { state: 'capturing', text: `${team(point.capturing)} capturing · ${Math.round(point.progress * 100)}%` };
  if (point.owner && point.occupants[point.owner] > 0) return { state: 'scoring', text: `${team(point.owner)} scoring · 1 point per second` };
  if (point.owner) return { state: 'absent', text: 'Owner absent · No points earned' };
  return { state: 'unclaimed', text: point.progress > 0 ? 'Court empty · Capture progress receding' : 'Enter and stay inside the marked court' };
}
