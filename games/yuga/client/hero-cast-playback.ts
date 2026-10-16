import type { AbilityDef } from '../shared/types';

export interface LockedCastFrame {
  alive: boolean; casting: boolean; castSlot: number;
  castElapsed?: number; castStartedAt?: number;
}
export interface LockedCastPlayback {
  key: string; clip: 'cast1' | 'cast2' | 'cast3'; seekSeconds: number | null;
}

/** Timed ability events are receipts, not a second animation clock. A delayed
 * event must not restart an ultimate after its authoritative cast disappeared.
 */
export function acknowledgedHeroAction(
  frame: { cast: number; shot: number }, previousCast: number, previousShot: number,
  ability: Pick<AbilityDef, 'mechanic'> | undefined,
): 'cast' | 'fire' | null {
  if (frame.cast > previousCast && frame.cast > 0 && !ability?.mechanic) return 'cast';
  if (frame.shot > previousShot && frame.shot > 0) return 'fire';
  return null;
}

/** A server-owned cast is movement-locked, so its authored pose owns the whole body.
 * Seek once when entering/rejoining a cast; repeated snapshots never restart it.
 */
export function lockedCastPlayback(frame: LockedCastFrame, previousKey: string | null, duration: number): LockedCastPlayback | null {
  if (!frame.alive || !frame.casting) return null;
  const slot = Number.isInteger(frame.castSlot) && frame.castSlot >= 0 && frame.castSlot <= 2 ? frame.castSlot : 0;
  const startedAt = Number.isFinite(frame.castStartedAt) ? frame.castStartedAt! : 0;
  const key = `${slot}:${startedAt}`, clip = `cast${slot + 1}` as LockedCastPlayback['clip'];
  const limit = Number.isFinite(duration) ? Math.max(0, duration - .001) : 0;
  const elapsed = Number.isFinite(frame.castElapsed) ? Math.max(0, frame.castElapsed!) : 0;
  return { key, clip, seekSeconds: key === previousKey ? null : Math.min(limit, elapsed) };
}
