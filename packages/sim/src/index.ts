import { CAMPAIGN, CONTENT_VERSION, EVIDENCE, chooseEnding, getStageDialogue } from '../../content/src/index.js';
import { PROTOCOL_VERSION, type CommandMessage, type InputMessage, type MissionSnapshot, type Mode, type PlayerSnapshot, type ResultMessage, type Snapshot, type VehicleSnapshot } from '../../protocol/src/index.js';
import { WORLD, isBlocked, landmark } from './world.js';
export { WORLD, isBlocked, landmark } from './world.js';

interface StoredInput { message: InputMessage; time: number }
export interface PersistedSimulation {
  schema: 1; contentVersion: string; room: string; mode: Mode; tick: number; time: number;
  players: PlayerSnapshot[]; vehicles: VehicleSnapshot[]; mission: MissionSnapshot;
  commands: Record<string, Record<string, ResultMessage>>;
}
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const distance = (a: { x: number; z: number }, b: { x: number; z: number }) => Math.hypot(a.x - b.x, a.z - b.z);
const clamp = (n: number, low: number, high: number) => Math.min(high, Math.max(low, n));
const SIGNALS = new Set(['follow', 'wait', 'ready', 'thanks', 'help']);
const validId = (value: unknown) => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(value);
const validName = (value: unknown) => typeof value === 'string' && /^[\p{L}\p{N} _.-]{1,24}$/u.test(value);
const validObject = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);

function validCheckpoint(saved: PersistedSimulation, room: string, mode: Mode): boolean {
  const position = (p: { x: number; z: number; heading: number }) => [p.x, p.z, p.heading].every(Number.isFinite) && Math.abs(p.x) <= WORLD.bounds && Math.abs(p.z) <= WORLD.bounds && Math.abs(p.heading) < 1e6;
  if (!validObject(saved) || saved.schema !== 1 || saved.contentVersion !== CONTENT_VERSION || saved.room !== room || saved.mode !== mode || !Number.isSafeInteger(saved.tick) || saved.tick < 0 || !Number.isFinite(saved.time) || saved.time < 0) return false;
  if (!Array.isArray(saved.players) || saved.players.length > (mode === 'private' ? 4 : 16) || !saved.players.every(p => validObject(p) && position(p) && validId(p.id) && validName(p.name) && Number.isSafeInteger(p.lastInputSeq) && p.lastInputSeq >= -1)) return false;
  if (new Set(saved.players.map(p => p.id)).size !== saved.players.length) return false;
  if (!Array.isArray(saved.vehicles) || saved.vehicles.length !== 2 || !saved.vehicles.every(v => validObject(v) && position(v) && ['compact-01', 'van-01'].includes(v.id) && ['car', 'van'].includes(v.kind) && Number.isFinite(v.speed) && Math.abs(v.speed) <= 21 && Array.isArray(v.occupants) && v.occupants.length === 4 && v.occupants.every(id => id === null || saved.players.some(p => p.id === id)))) return false;
  if (new Set(saved.vehicles.map(v => v.id)).size !== 2) return false;
  if (!validObject(saved.commands) || !Object.entries(saved.commands).every(([id, entries]) => validId(id) && validObject(entries) && Object.keys(entries).length <= 4096 && Object.entries(entries).every(([commandId, result]) => validId(commandId) && validObject(result) && result.type === 'result' && result.commandId === commandId && typeof result.ok === 'boolean' && typeof result.code === 'string' && result.code.length <= 64))) return false;
  const mission = saved.mission;
  if (!validObject(mission) || !validObject(mission.metrics) || !(['trust', 'care', 'accountability'] as const).every(k => Number.isFinite(mission.metrics[k]) && mission.metrics[k] >= 0 && mission.metrics[k] <= 100) || !Number.isSafeInteger(mission.revision) || mission.revision < 0 || typeof mission.complete !== 'boolean') return false;
  if (!Array.isArray(mission.evidence) || mission.evidence.length > Object.keys(EVIDENCE).length || !mission.evidence.every(id => typeof id === 'string' && Object.hasOwn(EVIDENCE, id)) || new Set(mission.evidence).size !== mission.evidence.length) return false;
  if (!Array.isArray(mission.history) || mission.history.length > 64 || !mission.history.every(entry => validObject(entry) && CAMPAIGN.find(c => c.id === entry.chapterId)?.stages.find(s => s.id === entry.stageId)?.choices?.some(c => c.id === entry.choiceId))) return false;
  if (new Set(mission.history.map(entry => `${entry.chapterId}/${entry.stageId}`)).size !== mission.history.length) return false;
  if (!Number.isInteger(mission.chapterIndex) || !Number.isInteger(mission.stageIndex)) return false;
  if (mission.complete) return mission.chapterIndex === CAMPAIGN.length && mission.stageIndex === 0;
  return !!CAMPAIGN[mission.chapterIndex]?.stages[mission.stageIndex];
}

/** Original bounded arcade simulation. The browser sends intent; only this simulation moves entities. */
export class Simulation {
  readonly room: string;
  readonly mode: Mode;
  tick = 0;
  time = 0;
  players = new Map<string, PlayerSnapshot>();
  vehicles = new Map<string, VehicleSnapshot>();
  mission: MissionSnapshot;
  private inputs = new Map<string, StoredInput>();
  private commands = new Map<string, Map<string, ResultMessage>>();

  constructor(room: string, mode: Mode = 'private', restored?: PersistedSimulation) {
    this.room = room;
    this.mode = mode;
    this.vehicles.set('compact-01', { id: 'compact-01', kind: 'car', x: -52, z: 48, heading: Math.PI / 2, speed: 0, occupants: [null, null, null, null] });
    this.vehicles.set('van-01', { id: 'van-01', kind: 'van', x: 48, z: 40, heading: Math.PI, speed: 0, occupants: [null, null, null, null] });
    this.mission = this.initialMission();
    if (restored) this.restore(restored);
  }

  private initialMission(): MissionSnapshot {
    const chapter = CAMPAIGN[0]!;
    const stage = chapter.stages[0]!;
    return { chapterIndex: 0, chapterId: chapter.id, title: chapter.title, stageIndex: 0, stage: stage.id, objective: stage.objective, targetId: stage.targetId, trigger: stage.trigger, dialogue: clone(getStageDialogue(stage, [])), documents: [...(stage.documents ?? [])], choices: (stage.choices ?? []).map(({ id, label, description }) => ({ id, label, description })), votes: {}, evidence: [], metrics: { trust: 50, care: 50, accountability: 50 }, history: [], revision: 0, complete: false, ending: null };
  }

  addPlayer(id: string, name: string): PlayerSnapshot {
    const existing = this.players.get(id);
    if (existing) { this.connectPlayer(id); return existing; }
    const max = this.mode === 'private' ? 4 : 16;
    if (this.players.size >= max) throw new Error('ROOM_FULL');
    if (!validId(id)) throw new Error('INVALID_PLAYER_ID');
    const safeName = name.replace(/[^\p{L}\p{N} _.-]/gu, '').trim().slice(0, 24) || 'Crew member';
    const player: PlayerSnapshot = { id, name: safeName, x: WORLD.spawn.x - 3, z: WORLD.spawn.z + (this.players.size % 4) * 1.2 + 2, heading: Math.PI / 2, vehicleId: null, seat: null, connected: true, color: this.players.size % 4, signal: null, signalUntil: 0, lastInputSeq: -1 };
    this.players.set(id, player);
    if (!this.commands.has(id)) this.commands.set(id, new Map());
    return player;
  }

  connectPlayer(id: string): boolean {
    const player = this.players.get(id);
    if (!player) return false;
    player.connected = true;
    // Sequence belongs to one transport session; authenticated reconnect replaces the old transport.
    player.lastInputSeq = -1;
    this.inputs.delete(id);
    return true;
  }

  disconnectPlayer(id: string, resolveVotes = true): void {
    const player = this.players.get(id);
    if (!player) return;
    const wasConnected = player.connected;
    if (player.vehicleId && !this.leaveVehicle(player)) {
      const vehicle = this.vehicles.get(player.vehicleId);
      if (vehicle) { vehicle.occupants = vehicle.occupants.map(p => p === id ? null : p); if (player.seat === 0) vehicle.speed = 0; }
      player.vehicleId = null; player.seat = null;
      player.x = WORLD.spawn.x; player.z = WORLD.spawn.z;
    }
    player.connected = false;
    this.inputs.delete(id);
    delete this.mission.votes[id];
    if (wasConnected && resolveVotes && Object.keys(this.mission.votes).length && !this.resolveVote()) this.mission.revision++;
  }

  removePlayer(id: string): void {
    this.disconnectPlayer(id);
    this.players.delete(id);
    // Keep accepted command IDs for the persistent bearer identity even after its seat expires.
  }

  input(playerId: string, message: InputMessage): boolean {
    const player = this.players.get(playerId);
    if (!player?.connected || message.seq <= player.lastInputSeq || !Number.isSafeInteger(message.seq) || ![message.moveX, message.moveZ, message.forward, message.turn].every(n => Number.isFinite(n) && Math.abs(n) <= 1)) return false;
    player.lastInputSeq = message.seq;
    this.inputs.set(playerId, { message, time: this.time });
    return true;
  }

  clearInput(playerId: string): void { this.inputs.delete(playerId); }

  command(playerId: string, command: CommandMessage): ResultMessage {
    const cache = this.commands.get(playerId);
    const previous = cache?.get(command.id);
    if (previous) return clone(previous);
    const player = this.players.get(playerId);
    const result = (ok: boolean, code: string): ResultMessage => {
      const response: ResultMessage = { type: 'result', commandId: command.id, ok, code };
      if (cache && cache.size < 4096) cache.set(command.id, response);
      return response;
    };
    if (!player?.connected) return result(false, 'NOT_CONNECTED');
    // Preserve replay protection for the whole checkpoint instead of evicting old command IDs.
    if (cache && cache.size >= 4096) return result(false, 'COMMAND_LIMIT');
    if (command.action === 'enter') {
      if (player.vehicleId) return result(false, 'ALREADY_SEATED');
      const vehicle = command.target ? this.vehicles.get(command.target) : [...this.vehicles.values()].sort((a, b) => distance(player, a) - distance(player, b))[0];
      if (!vehicle || distance(player, vehicle) > 5.8) return result(false, 'TOO_FAR');
      if (Math.abs(vehicle.speed) > 1.5) return result(false, 'VEHICLE_MOVING');
      const seat = vehicle.occupants.findIndex(id => id === null);
      if (seat < 0) return result(false, 'VEHICLE_FULL');
      vehicle.occupants[seat] = player.id;
      player.vehicleId = vehicle.id;
      player.seat = seat;
      player.x = vehicle.x; player.z = vehicle.z; player.heading = vehicle.heading;
      this.inputs.delete(player.id);
      this.maybeAutomaticProgress();
      return result(true, 'ENTERED');
    }
    if (command.action === 'exit') {
      if (!player.vehicleId) return result(false, 'NOT_SEATED');
      const vehicle = this.vehicles.get(player.vehicleId)!;
      if (Math.abs(vehicle.speed) > 3) return result(false, 'VEHICLE_MOVING');
      if (!this.leaveVehicle(player)) return result(false, 'EXIT_BLOCKED');
      return result(true, 'EXITED');
    }
    if (command.action === 'take_wheel') {
      if (!player.vehicleId || player.seat === null) return result(false, 'NOT_SEATED');
      const vehicle = this.vehicles.get(player.vehicleId)!;
      if (player.seat === 0) return result(false, 'ALREADY_DRIVER');
      if (vehicle.occupants[0] !== null) return result(false, 'DRIVER_OCCUPIED');
      if (Math.abs(vehicle.speed) > 1.5) return result(false, 'VEHICLE_MOVING');
      vehicle.occupants[player.seat] = null;
      vehicle.occupants[0] = player.id;
      player.seat = 0; vehicle.speed = 0;
      this.inputs.delete(player.id);
      return result(true, 'DRIVER_CLAIMED');
    }
    if (command.action === 'signal') {
      if (!SIGNALS.has(command.value ?? '')) return result(false, 'UNKNOWN_SIGNAL');
      player.signal = command.value!;
      player.signalUntil = this.time + 5;
      return result(true, 'SIGNAL_SENT');
    }
    if (command.action === 'replay') {
      if (!this.mission.complete || command.value !== 'confirm' || this.mode !== 'private' || [...this.players.values()].filter(p => p.connected).length !== 1) return result(false, 'REPLAY_UNAVAILABLE');
      this.mission = this.initialMission();
      return result(true, 'REPLAY_STARTED');
    }
    if (this.mission.complete) return result(false, 'CAMPAIGN_COMPLETE');
    const chapter = CAMPAIGN[this.mission.chapterIndex]!;
    const stage = chapter.stages[this.mission.stageIndex]!;
    const place = landmark(stage.targetId);
    if (!place || distance(player, place) > place.radius) return result(false, 'TOO_FAR');
    if (command.action === 'interact') {
      if (command.target && command.target !== stage.targetId) return result(false, 'WRONG_TARGET');
      if (stage.trigger !== 'interact') return result(false, stage.trigger === 'choice' ? 'CHOICE_REQUIRED' : 'WRONG_ACTION');
      if (player.vehicleId) return result(false, 'EXIT_VEHICLE_FIRST');
      this.advance();
      return result(true, 'STAGE_COMPLETE');
    }
    if (command.action === 'choice') {
      if (stage.trigger !== 'choice') return result(false, 'CHOICE_UNAVAILABLE');
      if (player.vehicleId) return result(false, 'EXIT_VEHICLE_FIRST');
      const choice = stage.choices?.find(c => c.id === command.value);
      if (!choice) return result(false, 'UNKNOWN_CHOICE');
      this.mission.votes[playerId] = choice.id;
      if (this.resolveVote()) return result(true, 'CHOICE_ACCEPTED');
      this.mission.revision++; return result(true, 'VOTE_RECORDED');
    }
    return result(false, 'UNKNOWN_ACTION');
  }

  /** Private choices use a majority of the currently connected crew; public contracts resolve one vote. */
  private resolveVote(): boolean {
    if (this.mission.complete) return false;
    const chapter = CAMPAIGN[this.mission.chapterIndex]!, stage = chapter.stages[this.mission.stageIndex]!;
    if (stage.trigger !== 'choice') return false;
    const connected = [...this.players.values()].filter(p => p.connected);
    if (!connected.length) return false;
    const required = this.mode === 'private' ? Math.floor(connected.length / 2) + 1 : 1;
    const choice = stage.choices?.find(option => connected.filter(p => this.mission.votes[p.id] === option.id).length >= required);
    if (!choice) return false;
    this.mission.history.push({ chapterId: chapter.id, stageId: stage.id, choiceId: choice.id, label: choice.label });
    for (const key of ['trust', 'care', 'accountability'] as const) this.mission.metrics[key] = clamp(this.mission.metrics[key] + (choice.effects?.[key] ?? 0), 0, 100);
    this.mission.evidence = [...new Set([...this.mission.evidence, ...(choice.evidence ?? [])])];
    this.advance();
    return true;
  }

  private leaveVehicle(player: PlayerSnapshot): boolean {
    const vehicle = this.vehicles.get(player.vehicleId ?? '');
    if (!vehicle) { player.vehicleId = null; player.seat = null; return true; }
    const offsets = [[-3, 0], [3, 0], [0, -4], [0, 4], [-4, -4], [4, 4]];
    const offset = offsets.find(([x, z]) => !isBlocked(vehicle.x + x!, vehicle.z + z!));
    if (!offset) return false;
    vehicle.occupants = vehicle.occupants.map(id => id === player.id ? null : id);
    if (player.seat === 0) vehicle.speed = 0;
    player.x = vehicle.x + offset[0]!; player.z = vehicle.z + offset[1]!;
    player.vehicleId = null; player.seat = null;
    this.inputs.delete(player.id);
    return true;
  }

  private advance(): void {
    const chapter = CAMPAIGN[this.mission.chapterIndex]!;
    const stage = chapter.stages[this.mission.stageIndex]!;
    this.mission.evidence = [...new Set([...this.mission.evidence, ...(stage.evidence ?? [])])];
    this.mission.stageIndex++;
    if (this.mission.stageIndex >= chapter.stages.length) { this.mission.chapterIndex++; this.mission.stageIndex = 0; }
    this.mission.votes = {};
    this.mission.revision++;
    const nextChapter = CAMPAIGN[this.mission.chapterIndex];
    if (!nextChapter) {
      this.mission.complete = true; this.mission.stage = 'complete';
      this.mission.objective = 'The hearing has ended. Read the city’s response.';
      this.mission.targetId = null; this.mission.trigger = 'complete'; this.mission.choices = []; this.mission.documents = [];
      this.mission.ending = chooseEnding(this.mission.metrics, this.mission.history);
      return;
    }
    const next = nextChapter.stages[this.mission.stageIndex]!;
    Object.assign(this.mission, { chapterId: nextChapter.id, title: nextChapter.title, stage: next.id, objective: next.objective, targetId: next.targetId, trigger: next.trigger, dialogue: clone(getStageDialogue(next, this.mission.history)), documents: [...(next.documents ?? [])], choices: (next.choices ?? []).map(({ id, label, description }) => ({ id, label, description })) });
  }

  private maybeAutomaticProgress(): void {
    if (this.mission.complete) return;
    const stage = CAMPAIGN[this.mission.chapterIndex]!.stages[this.mission.stageIndex]!;
    if (stage.trigger !== 'arrive' && stage.trigger !== 'enter_vehicle') return;
    const place = landmark(stage.targetId);
    if (place && [...this.players.values()].some(p => p.connected && distance(p, place) <= place.radius && (stage.trigger !== 'enter_vehicle' || p.vehicleId))) this.advance();
  }

  step(dt = 0.05): void {
    if (!Number.isFinite(dt) || dt <= 0) return;
    dt = Math.min(dt, 0.1);
    this.tick++; this.time += dt;
    for (const player of this.players.values()) {
      if (player.signal && this.time > player.signalUntil) player.signal = null;
      if (!player.connected || player.vehicleId) continue;
      const input = this.inputs.get(player.id);
      if (!input || this.time - input.time > 0.35) continue;
      const { moveX, moveZ, sprint } = input.message;
      const magnitude = Math.max(1, Math.hypot(moveX, moveZ));
      const speed = sprint ? 6.2 : 3.8;
      const dx = moveX / magnitude * speed * dt, dz = moveZ / magnitude * speed * dt;
      if (Math.abs(dx) + Math.abs(dz) > 0.001) player.heading = Math.atan2(moveX, moveZ);
      if (!isBlocked(player.x + dx, player.z)) player.x += dx;
      if (!isBlocked(player.x, player.z + dz)) player.z += dz;
    }
    for (const vehicle of this.vehicles.values()) {
      const driverId = vehicle.occupants[0];
      const stored = driverId ? this.inputs.get(driverId) : undefined;
      const active = stored && this.time - stored.time <= 0.35;
      const forward = active ? stored.message.forward : 0;
      const turn = active ? stored.message.turn : 0;
      if (Math.abs(forward) > 0.01) vehicle.speed = clamp(vehicle.speed + forward * (vehicle.speed * forward < 0 ? 24 : 12) * dt, -7, vehicle.kind === 'van' ? 16 : 21);
      else vehicle.speed *= Math.exp(-3.5 * dt);
      if (Math.abs(vehicle.speed) < 0.02) vehicle.speed = 0;
      if (Math.abs(vehicle.speed) > 0.1) vehicle.heading += turn * 1.8 * Math.min(1, Math.abs(vehicle.speed) / 4) * Math.sign(vehicle.speed) * dt;
      const dx = Math.sin(vehicle.heading) * vehicle.speed * dt, dz = Math.cos(vehicle.heading) * vehicle.speed * dt;
      const slices = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.45));
      for (let i = 0; i < slices; i++) {
        if (isBlocked(vehicle.x + dx / slices, vehicle.z + dz / slices, 1.3)) { vehicle.speed = 0; break; }
        vehicle.x += dx / slices; vehicle.z += dz / slices;
      }
      for (const id of vehicle.occupants) {
        const player = id ? this.players.get(id) : undefined;
        if (player) { player.x = vehicle.x; player.z = vehicle.z; player.heading = vehicle.heading; }
      }
    }
    this.maybeAutomaticProgress();
  }

  snapshot(): Snapshot { return clone({ type: 'snapshot', protocol: PROTOCOL_VERSION, tick: this.tick, time: this.time, room: this.room, mode: this.mode, players: [...this.players.values()], vehicles: [...this.vehicles.values()], mission: this.mission }); }
  serialize(): PersistedSimulation { return { schema: 1, contentVersion: CONTENT_VERSION, ...this.snapshot(), commands: Object.fromEntries([...this.commands].map(([id, commands]) => [id, Object.fromEntries(commands)])) }; }

  private restore(saved: PersistedSimulation): void {
    if (!validCheckpoint(saved, this.room, this.mode)) throw new Error('INVALID_CHECKPOINT');
    this.tick = saved.tick; this.time = saved.time; this.mission = clone(saved.mission); this.mission.votes = {};
    // Presentation comes from pinned content, never arbitrary strings in a checkpoint.
    if (this.mission.complete) {
      this.mission.ending = chooseEnding(this.mission.metrics, this.mission.history);
      const chapter = CAMPAIGN.at(-1)!, stage = chapter.stages.at(-1)!;
      Object.assign(this.mission, { chapterId: chapter.id, title: chapter.title, stage: 'complete', objective: 'The hearing has ended. Read the city’s response.', dialogue: clone(getStageDialogue(stage, this.mission.history)), documents: [], choices: [], targetId: null, trigger: 'complete' });
    } else {
      const chapter = CAMPAIGN[this.mission.chapterIndex]!, stage = chapter.stages[this.mission.stageIndex]!;
      Object.assign(this.mission, { chapterId: chapter.id, title: chapter.title, stage: stage.id, objective: stage.objective, targetId: stage.targetId, trigger: stage.trigger, dialogue: clone(getStageDialogue(stage, this.mission.history)), documents: [...(stage.documents ?? [])], choices: (stage.choices ?? []).map(({ id, label, description }) => ({ id, label, description })), ending: null });
    }
    this.mission.history = this.mission.history.map(entry => ({ ...entry, label: CAMPAIGN.find(c => c.id === entry.chapterId)!.stages.find(s => s.id === entry.stageId)!.choices!.find(c => c.id === entry.choiceId)!.label }));
    this.players = new Map(saved.players.map((p, index) => [p.id, { ...p, connected: false, color: index % 4, signal: null, signalUntil: 0 }]));
    this.vehicles = new Map(saved.vehicles.map(v => [v.id, clone(v)]));
    this.commands = new Map(Object.entries(saved.commands).map(([id, commands]) => [id, new Map(Object.entries(commands))]));
    for (const player of this.players.values()) if (!this.commands.has(player.id)) this.commands.set(player.id, new Map());
    for (const player of this.players.values()) this.disconnectPlayer(player.id, false);
    for (const vehicle of this.vehicles.values()) { vehicle.occupants.fill(null); vehicle.speed = 0; }
  }
}
