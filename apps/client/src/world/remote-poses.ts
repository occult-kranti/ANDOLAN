import type { Snapshot } from '../../../../packages/protocol/src/index';

export interface Pose { x: number; z: number; heading: number }
export interface RemotePoses { players: Map<string, Pose>; vehicles: Map<string, Pose> }
type TrackedPose = Pose & { continuity: string };
type Frame = { tick: number; time: number; received: number; players: Map<string, TrackedPose>; vehicles: Map<string, TrackedPose> };
const fields = ['players', 'vehicles'] as const;
const pose = ({ x, z, heading }: Pose): Pose => ({ x, z, heading });
const finite = (p: Pose) => [p.x, p.z, p.heading].every(Number.isFinite);

/** Original presentation-only history. Never modifies authoritative snapshots or local controls. */
export class RemotePoseBuffer {
  private frames: Frame[] = [];
  private identity = '';
  private clockOffset = 0;
  private playhead = -Infinity;

  constructor(private delayMs = 100, private capacity = 12, private snapDistance = 8) {
    if (!Number.isFinite(delayMs) || delayMs < 0 || !Number.isInteger(capacity) || capacity < 2 || capacity > 120 || !Number.isFinite(snapDistance) || snapDistance <= 0) {
      throw new RangeError('Invalid remote pose history settings');
    }
  }

  get size(): number { return this.frames.length; }

  /** Call on every welcome/reconnect, even when the room and player identity are unchanged. */
  reset(): void { this.frames = []; this.identity = ''; this.clockOffset = 0; this.playhead = -Infinity; }

  push(snapshot: Snapshot, receivedAtMs: number, localPlayerId: string | null): boolean {
    const time = snapshot.time * 1000;
    if (!Number.isFinite(time) || !Number.isFinite(receivedAtMs) || !Number.isSafeInteger(snapshot.tick) || snapshot.tick < 0 || time < 0) return false;
    const identity = JSON.stringify([snapshot.room, snapshot.mode, snapshot.gameplay, localPlayerId]);
    if (identity !== this.identity) this.reset();
    let previous = this.frames.at(-1);
    // Lower ticks are old packets, not evidence of a new session. Reconnect calls reset explicitly.
    if (previous && snapshot.tick <= previous.tick) return false;
    if (previous && (time <= previous.time || receivedAtMs < previous.received)) {
      this.reset(); previous = undefined;
    }
    this.identity = identity;
    if (!previous) this.clockOffset = time - receivedAtMs;

    const localVehicle = snapshot.players.find(player => player.id === localPlayerId)?.vehicleId;
    const frame: Frame = { tick: snapshot.tick, time, received: receivedAtMs, players: new Map(), vehicles: new Map() };
    for (const player of snapshot.players) {
      if (player.id === localPlayerId || !player.connected || !finite(player)) continue;
      frame.players.set(player.id, { ...pose(player), continuity: JSON.stringify([player.vehicleId, player.seat]) });
    }
    for (const vehicle of snapshot.vehicles) {
      if (vehicle.id === localVehicle || !finite(vehicle)) continue;
      frame.vehicles.set(vehicle.id, { ...pose(vehicle), continuity: JSON.stringify(vehicle.occupants) });
    }

    for (const field of fields) for (const [id, current] of frame[field]) {
      const old = previous?.[field].get(id);
      if (!old || old.continuity !== current.continuity || Math.hypot(current.x - old.x, current.z - old.z) > this.snapDistance) {
        // Do not draw a path across a seat transition, respawn, teleport or newly visible entity.
        for (const stored of this.frames) stored[field].delete(id);
      }
    }
    this.frames.push(frame);
    if (this.frames.length > this.capacity) this.frames.splice(0, this.frames.length - this.capacity);
    return true;
  }

  sample(nowMs: number): RemotePoses {
    const result: RemotePoses = { players: new Map(), vehicles: new Map() };
    const latest = this.frames.at(-1);
    if (!latest) return result;
    const desired = Number.isFinite(nowMs) ? nowMs + this.clockOffset - this.delayMs : latest.time;
    const time = Math.min(latest.time, Math.max(this.frames[0]!.time, this.playhead, desired));
    this.playhead = time;
    const newer = this.frames.find(frame => frame.time >= time) ?? latest;
    const index = this.frames.indexOf(newer);
    const older = this.frames[Math.max(0, index - 1)]!;
    const fraction = newer.time === older.time ? 1 : Math.max(0, Math.min(1, (time - older.time) / (newer.time - older.time)));

    // The newest frame determines existence and role; only continuous numeric poses interpolate.
    for (const field of fields) for (const [id, current] of latest[field]) {
      const a = older[field].get(id), b = newer[field].get(id);
      if (!a || !b) { result[field].set(id, pose(current)); continue; }
      result[field].set(id, {
        x: a.x + (b.x - a.x) * fraction,
        z: a.z + (b.z - a.z) * fraction,
        heading: a.heading + Math.atan2(Math.sin(b.heading - a.heading), Math.cos(b.heading - a.heading)) * fraction,
      });
    }
    return result;
  }
}
