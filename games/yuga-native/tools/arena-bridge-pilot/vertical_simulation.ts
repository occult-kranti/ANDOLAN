/** Isolated adapter over the existing arena schema/identity/input implementation.
 * Existing Node server owns sockets. Native Godot alone advances physical poses.
 * No planar base step, towers, damage, waves, economy or match outcome is run.
 */
import net from 'node:net';
import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import { ArenaSimulation as ExistingSimulation } from '../../../yuga/shared/simulation.js';
import type { ArenaInput, Actor, ArenaSnapshot, ArenaCommand, CommandResult, Team } from '../../../yuga/shared/types.js';
import type { ArenaAuthorityFactory } from '../../../yuga/server/authority-factory.js';

type Pose = { id: string; x: number; y: number; z: number; yaw: number; pitch: number; bridgeAckSeq: number; bridgeInputTick: number; bridgeSlot: number; bridgeEpoch: number; nativeTick: number; grounded: boolean; support: string; shot: object; velocity: number[] };
type NativeState = { schema: number; nativeTick: number; nativeTime: number; stage: string; stageTime: number; epoch: number; done: boolean; fixtureHash: string; contractHash: string; revision: number; actors: Pose[]; rejectedPackets: number };
let socket: net.Socket;
let latest: NativeState | undefined;
let fixtureHash = '', contractHash = '', revision = 0;
let pending = '';
let activeRoom = '';
const actorSlots = new Map<string, number>();
const contract = JSON.parse(fs.readFileSync(new URL('./bridge-contract.json', import.meta.url), 'utf8')) as { stages: { id: string; seconds: number }[] };
const sent = new Map<number, number>();
export const bridgeStats = { nativePackets: 0, sentPackets: 0, rejectedNativePackets: 0, acceptedInputs: 0, staleInputs: 0, roundTripMilliseconds: [] as number[], nativeClosed: false };

const record = (value: unknown): value is Record<string, any> => !!value && typeof value === 'object' && !Array.isArray(value);
const integer = (value: unknown, minimum = 0) => typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum;
const finite = (value: unknown) => typeof value === 'number' && Number.isFinite(value);
/** Pure evidence-facing predicate: rejects a whole incoherent backend state atomically. */
export function validNativeState(value: unknown, previous: NativeState | undefined, expected: ReadonlyMap<string, number>, fixture: string, contractHashExpected: string): value is NativeState {
  if (!record(value) || value.schema !== 1 || value.fixtureHash !== fixture || value.contractHash !== contractHashExpected || !integer(value.nativeTick, 1) || value.nativeTick <= (previous?.nativeTick ?? -1) || !integer(value.epoch) || value.epoch >= contract.stages.length || value.stage !== contract.stages[value.epoch].id || !finite(value.nativeTime) || value.nativeTime < 0 || value.nativeTime > contract.stages.reduce((sum, stage) => sum + stage.seconds, 0) + .5 || Math.abs(value.nativeTime - value.nativeTick / 60) > .0001 || !finite(value.stageTime) || value.stageTime < 0 || value.stageTime > contract.stages[value.epoch].seconds + .05 || typeof value.done !== 'boolean' || !integer(value.revision) || !integer(value.rejectedPackets) || !Array.isArray(value.actors) || value.actors.length !== 2 || expected.size !== 2) return false;
  // Match the native stage clock, including final-stage clamping. Tiny tolerance
  // admits accumulated 1/60-second rounding at exact stage boundaries only.
  const clockTolerance = 1e-7;
  const start = contract.stages.slice(0, value.epoch).reduce((sum, stage) => sum + stage.seconds, 0);
  const duration = contract.stages[value.epoch].seconds;
  const total = contract.stages.reduce((sum, stage) => sum + stage.seconds, 0);
  const finalStage = value.epoch === contract.stages.length - 1;
  if (value.nativeTime < start - clockTolerance || (!finalStage && value.nativeTime > start + duration + clockTolerance) || Math.abs(value.stageTime - Math.max(0, Math.min(duration, value.nativeTime - start))) > clockTolerance || (value.done && value.nativeTime < total - clockTolerance) || (!value.done && value.nativeTime > total + clockTolerance)) return false;
  if (previous && (value.epoch < previous.epoch || value.epoch > previous.epoch + 1 || value.nativeTime <= previous.nativeTime)) return false;
  const seen = new Set<string>(), slots = new Set<number>();
  for (const a of value.actors) {
    if (!record(a) || typeof a.id !== 'string' || !expected.has(a.id) || seen.has(a.id) || !integer(a.bridgeSlot) || a.bridgeSlot > 1 || a.bridgeSlot !== expected.get(a.id) || slots.has(a.bridgeSlot) || a.nativeTick !== value.nativeTick || a.bridgeEpoch !== value.epoch || !integer(a.bridgeAckSeq, -1) || !integer(a.bridgeInputTick, -1000) || a.bridgeInputTick > value.nativeTick || typeof a.grounded !== 'boolean' || typeof a.support !== 'string' || a.support.length > 64 || !record(a.shot) || !Array.isArray(a.velocity) || a.velocity.length !== 3 || ![a.x,a.y,a.z,a.yaw,a.pitch,...a.velocity].every(finite) || a.velocity.some((v: number) => Math.abs(v) > 100) || Math.abs(a.x) >= 1000 || Math.abs(a.y) >= 100 || Math.abs(a.z) >= 1000 || Math.abs(a.yaw) > Math.PI + .000001 || Math.abs(a.pitch) > 1.35) return false;
    const prior = previous?.actors.find(actor => actor.id === a.id);
    if (prior && value.epoch === previous!.epoch && (a.bridgeAckSeq < prior.bridgeAckSeq || Math.hypot(a.x-prior.x,a.y-prior.y,a.z-prior.z) > 35 * (value.nativeTime-previous!.nativeTime) + .05)) return false;
    if (Object.keys(a.shot).length && (!integer(a.shot.nativeTick) || a.shot.nativeTick > value.nativeTick || !finite(a.shot.pitch) || Math.abs(a.shot.pitch) > 1.35 || typeof a.shot.target !== 'string' || a.shot.target.length > 64 || !Array.isArray(a.shot.origin) || a.shot.origin.length !== 3 || !a.shot.origin.every(finite))) return false;
    seen.add(a.id); slots.add(a.bridgeSlot);
  }
  return true;
}

export async function connectNative(port: number, fixture: string, contract: string): Promise<void> {
  fixtureHash = fixture; contractHash = contract;
  socket = net.createConnection({ port, host: '127.0.0.1' });
  await new Promise<void>((resolve, reject) => { socket.once('connect', resolve); socket.once('error', reject); });
  socket.on('close', () => { bridgeStats.nativeClosed = true; });
  socket.on('error', () => { bridgeStats.nativeClosed = true; });
  socket.on('data', bytes => {
    pending += bytes.toString('utf8');
    if (pending.length > 65536) { bridgeStats.rejectedNativePackets++; socket.destroy(); return; }
    while (pending.includes('\n')) {
      const index = pending.indexOf('\n'), text = pending.slice(0, index); pending = pending.slice(index + 1);
      try {
        const value = JSON.parse(text) as NativeState;
        const valid = validNativeState(value, latest, actorSlots, fixtureHash, contractHash);
        if (!valid) { bridgeStats.rejectedNativePackets++; continue; }
        latest = value; bridgeStats.nativePackets++;
        if (sent.has(value.revision)) bridgeStats.roundTripMilliseconds.push(performance.now() - sent.get(value.revision)!);
        for (const key of sent.keys()) if (key <= value.revision) sent.delete(key);
      } catch { bridgeStats.rejectedNativePackets++; }
    }
  });
}
export function closeNative() { socket?.destroy(); }

/** Explicit trusted server opt-in. The fixture is one native two-slot room,
 * not a general multi-room backend. No adapter is selected from client input. */
export const createNativePilotAuthority: ArenaAuthorityFactory = options => {
  if (!socket?.writable || socket.destroyed || bridgeStats.nativeClosed) throw Error('Native pilot authority must connect before creating a room');
  if (activeRoom && activeRoom !== options.room) throw Error('Native pilot authority supports one room');
  if (options.botsPerTeam !== undefined && options.botsPerTeam !== 0) throw Error('Native pilot authority does not simulate bots');
  return new ArenaSimulation(options);
};

export class ArenaSimulation extends ExistingSimulation {
  private readonly nativeInputs = new Map<string, ArenaInput>();
  private readonly nativeSlots = new Map<string, number>();
  constructor(options: ConstructorParameters<typeof ExistingSimulation>[0]) {
    super({ ...options, botsPerTeam: 0 });
    this.structures = []; this.neutrals = []; this.pickups = [];
  }
  override addPlayer(id: string, name: string, heroId: string, team?: Team): Actor {
    if (activeRoom && activeRoom !== this.room) throw Error('ROOM_FULL');
    if (!this.actors.has(id) && this.nativeSlots.size >= 2) throw Error('ROOM_FULL');
    activeRoom = this.room;
    const actor = super.addPlayer(id, name, heroId, team);
    if (!this.nativeSlots.has(id)) this.nativeSlots.set(id, this.nativeSlots.size);
    actorSlots.set(id, this.nativeSlots.get(id)!);
    if (!latest) Object.assign(actor, { x: 12, y: this.nativeSlots.get(id) === 0 ? 3.21 : 6.21, z: 1 });
    return actor;
  }
  override input(id: string, value: ArenaInput): boolean {
    if (!super.input(id, value)) { bridgeStats.staleInputs++; return false; }
    // Exact existing ArenaSimulation input normalization; shared movement remains world XZ.
    this.nativeInputs.set(id, { ...value, moveX: Math.max(-1, Math.min(1, value.moveX)), moveZ: Math.max(-1, Math.min(1, value.moveZ)), yaw: Math.atan2(Math.sin(value.yaw), Math.cos(value.yaw)), pitch: Math.max(-1.35, Math.min(1.35, value.pitch)) });
    bridgeStats.acceptedInputs++;
    return true;
  }
  override clearInput(id: string) { super.clearInput(id); this.nativeInputs.delete(id); }
  override removePlayer(id: string) { super.removePlayer(id); this.nativeInputs.delete(id); }
  override command(_id: string, command: ArenaCommand): CommandResult { return { type: 'result', id: command.id, ok: false, code: 'PILOT_NO_COMBAT' }; }
  override step(dt: number): void {
    if (!Number.isFinite(dt) || dt <= 0 || dt > .1) return;
    this.tick++; this.time += dt;
    if (latest) for (const pose of latest.actors) {
      const actor = this.actors.get(pose.id);
      if (actor) Object.assign(actor, pose);
    }
    if (!socket?.writable || socket.writableLength > 65536) return;
    const message = { schema: 1, fixtureHash, contractHash, revision: ++revision, actors: [...this.actors.values()].map(actor => ({ id: actor.id, slot: this.nativeSlots.get(actor.id), connected: actor.connected, intent: this.nativeInputs.get(actor.id) ?? null })) };
    sent.set(revision, performance.now());
    while (sent.size > 128) sent.delete(sent.keys().next().value!);
    socket.write(JSON.stringify(message) + '\n');
    bridgeStats.sentPackets++;
  }
  override snapshot(): ArenaSnapshot {
    const snapshot = super.snapshot();
    return Object.assign(snapshot, { bridge: { schema: 1, authority: 'native-3d-pilot-v1', fixtureHash, contractHash, browserPlanarStepDisabled: true, nativeTick: latest?.nativeTick ?? 0, nativeTime: latest?.nativeTime ?? 0, stage: latest?.stage ?? 'waiting', stageTime: latest?.stageTime ?? 0, epoch: latest?.epoch ?? 0, done: latest?.done ?? false, acceptedInputs: bridgeStats.acceptedInputs, staleInputs: bridgeStats.staleInputs } });
  }
}
