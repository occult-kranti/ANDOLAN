import { CAMPAIGN, CONTENT_VERSION, EVIDENCE, chooseEnding, getStageDialogue } from '../../content/src/index.js';
import { CITY_EXPOSE_JOB_ID, CITY_OUTCOMES, CONTRACTS, getEffectiveJobReward, type JobDefinition, type JobStage } from '../../content/src/contracts.js';
import { PROTOCOL_VERSION, type ActiveContract, type CityReformSnapshot, type CityRoute, type CitySector, type CommandMessage, type ContractsSnapshot, type Gameplay, type InputMessage, type MissionSnapshot, type Mode, type PlayerSnapshot, type ResultMessage, type Snapshot, type VehicleSnapshot } from '../../protocol/src/index.js';
import { WORLD, isBlocked, landmark } from './world.js';
export { WORLD, isBlocked, landmark } from './world.js';

interface StoredInput { message: InputMessage; time: number }
export interface PersistedSimulation {
  schema: 1 | 2 | 3; contentVersion: string; room: string; mode: Mode; gameplay?: Gameplay; tick: number; time: number;
  players: PlayerSnapshot[]; vehicles: VehicleSnapshot[]; mission: MissionSnapshot;
  contracts?: ContractsSnapshot;
  city?: CityReformSnapshot;
  commands: Record<string, Record<string, ResultMessage>>;
}
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const distance = (a: { x: number; z: number }, b: { x: number; z: number }) => Math.hypot(a.x - b.x, a.z - b.z);
const clamp = (n: number, low: number, high: number) => Math.min(high, Math.max(low, n));
const SIGNALS = new Set(['follow', 'wait', 'ready', 'thanks', 'help', 'horn']);
const validId = (value: unknown) => typeof value === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(value);
const validName = (value: unknown) => typeof value === 'string' && /^[\p{L}\p{N} _.-]{1,24}$/u.test(value);
const validObject = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const emptyContracts = (): ContractsSnapshot => ({ active: null, progression: { credits: 0, reputation: 0, completed: 0, project: 0 }, cooldowns: {}, recent: [], nextInstance: 1, revision: 0 });
const CITY_SECTORS: readonly CitySector[] = ['energy', 'welfare', 'resources', 'procurement'];
const emptyCity = (): CityReformSnapshot => ({ completedJobs: [], sectors: { energy: 0, welfare: 0, resources: 0, procurement: 0 }, votes: {}, decision: null, outcome: null, revision: 0 });
const contractDefinition = (id: string) => CONTRACTS.find(job => job.id === id);
const cityReady = (city: CityReformSnapshot): boolean => city.completedJobs.includes(CITY_EXPOSE_JOB_ID) && CITY_SECTORS.every(sector => city.sectors[sector] >= 1);

function validCity(city: CityReformSnapshot, saved: PersistedSimulation): boolean {
  if (!validObject(city) || !Array.isArray(city.completedJobs) || city.completedJobs.length > CONTRACTS.filter(job => job.once).length || new Set(city.completedJobs).size !== city.completedJobs.length || !Number.isSafeInteger(city.revision) || city.revision < 0) return false;
  if (!city.completedJobs.every((id, index) => {
    const job = contractDefinition(id);
    return job?.once && (job.requiresJobs ?? []).every(required => city.completedJobs.slice(0, index).includes(required));
  })) return false;
  if (!validObject(city.sectors) || Object.keys(city.sectors).length !== CITY_SECTORS.length || !CITY_SECTORS.every(sector => Number.isSafeInteger(city.sectors[sector]) && city.sectors[sector] === city.completedJobs.filter(id => contractDefinition(id)?.sector === sector).length)) return false;
  if (!validObject(city.votes) || !Object.entries(city.votes).every(([id, route]) => (route === 'reform' || route === 'capture') && saved.players.some(player => player.id === id && player.connected))) return false;
  if (city.completedJobs.length > (saved.contracts?.progression.completed ?? 0)) return false;
  if (Object.keys(city.votes).length && (!cityReady(city) || saved.contracts?.active || city.decision !== null)) return false;
  if (city.decision !== null) {
    if (!validObject(city.decision) || !['reform', 'capture'].includes(city.decision.route) || !Number.isFinite(city.decision.decidedAt) || city.decision.decidedAt < 0 || city.decision.decidedAt > saved.time || !cityReady(city) || !validObject(city.outcome)) return false;
  } else if (city.outcome !== null) return false;
  const active = saved.contracts?.active;
  if (active) {
    const job = contractDefinition(active.jobId)!;
    if ((job.once && city.completedJobs.includes(job.id)) || (job.requiresJobs ?? []).some(required => !city.completedJobs.includes(required))) return false;
  }
  if (saved.contracts?.recent.some(outcome => outcome.status === 'completed' && contractDefinition(outcome.jobId)?.once && !city.completedJobs.includes(outcome.jobId))) return false;
  return true;
}

function validContracts(state: ContractsSnapshot, time: number): boolean {
  const sequence = (id: unknown): number => typeof id === 'string' && /^job-[1-9]\d*$/.test(id) && Number.isSafeInteger(Number(id.slice(4))) ? Number(id.slice(4)) : -1;
  if (!validObject(state) || !validObject(state.progression) || !(['credits', 'reputation', 'completed', 'project'] as const).every(key => Number.isSafeInteger(state.progression[key]) && state.progression[key] >= 0 && state.progression[key] <= 1e9) || !Number.isSafeInteger(state.nextInstance) || state.nextInstance < 1 || !Number.isSafeInteger(state.revision) || state.revision < 0) return false;
  if (!validObject(state.cooldowns) || !Object.entries(state.cooldowns).every(([id, until]) => contractDefinition(id) && Number.isFinite(until) && until >= 0)) return false;
  if (!Array.isArray(state.recent) || state.recent.length > 20 || !state.recent.every(outcome => validObject(outcome) && validId(outcome.instanceId) && contractDefinition(outcome.jobId) && ['completed', 'failed', 'cancelled'].includes(outcome.status) && Number.isFinite(outcome.finishedAt) && ['credits', 'reputation', 'project'].every(key => Number.isSafeInteger(outcome[key as 'credits']) && outcome[key as 'credits'] >= 0) && Array.isArray(outcome.participants) && outcome.participants.length <= 256 && outcome.participants.every(validId))) return false;
  if (new Set(state.recent.map(outcome => outcome.instanceId)).size !== state.recent.length) return false;
  if (state.recent.some(outcome => sequence(outcome.instanceId) < 1 || sequence(outcome.instanceId) >= state.nextInstance || outcome.finishedAt < 0 || outcome.finishedAt > time)) return false;
  const active = state.active;
  if (active === null) return true;
  if (!validObject(active) || !validId(active.instanceId) || !validId(active.startedBy) || !contractDefinition(active.jobId)?.stages[active.stageIndex] || !Number.isInteger(active.stageIndex) || ![active.startedAt, active.stageStartedAt].every(n => Number.isFinite(n) && n >= 0) || !(active.deadlineAt === null || Number.isFinite(active.deadlineAt)) || !(active.orphanedAt === null || Number.isFinite(active.orphanedAt)) || typeof active.cargo !== 'boolean' || !(active.vehicleId === null || ['compact-01', 'van-01'].includes(active.vehicleId)) || !Array.isArray(active.participants) || active.participants.length > 256 || !active.participants.every(validId)) return false;
  if (sequence(active.instanceId) < 1 || sequence(active.instanceId) >= state.nextInstance || active.startedAt > time || active.stageStartedAt < active.startedAt || active.stageStartedAt > time || (active.orphanedAt !== null && (active.orphanedAt < 0 || active.orphanedAt > time)) || new Set(active.participants).size !== active.participants.length) return false;
  const job = contractDefinition(active.jobId)!;
  if (job.timeLimitSeconds === undefined ? active.deadlineAt !== null : active.deadlineAt === null || Math.abs(active.deadlineAt - active.startedAt - job.timeLimitSeconds) > 1e-6 || active.deadlineAt <= time) return false;
  let cargo = false, bound = false, exactVehicle: string | null = null;
  let vehicleKind: 'car' | 'van' | null = null;
  for (const stage of job.stages.slice(0, active.stageIndex)) {
    if (stage.grantCargo) cargo = true;
    if (stage.consumeCargo) cargo = false;
    if (stage.targetVehicleId) { bound = true; exactVehicle = stage.targetVehicleId; }
    if (stage.vehicle && stage.vehicle !== 'none') bound = true;
    if (stage.vehicle === 'car' || stage.vehicle === 'van') vehicleKind = stage.vehicle;
  }
  if (active.cargo !== cargo || (active.vehicleId !== null) !== bound || (exactVehicle && active.vehicleId !== exactVehicle) || (vehicleKind === 'car' && active.vehicleId !== 'compact-01') || (vehicleKind === 'van' && active.vehicleId !== 'van-01')) return false;
  return !state.recent.some(outcome => outcome.instanceId === active.instanceId);
}

function validCheckpoint(saved: PersistedSimulation, room: string, mode: Mode, gameplay: Gameplay): boolean {
  const position = (p: { x: number; z: number; heading: number }) => [p.x, p.z, p.heading].every(Number.isFinite) && Math.abs(p.x) <= WORLD.bounds && Math.abs(p.z) <= WORLD.bounds && Math.abs(p.heading) < 1e6;
  if (!validObject(saved) || ![1, 2, 3].includes(saved.schema) || ![CONTENT_VERSION, '0.4.0'].includes(saved.contentVersion) || saved.room !== room || saved.mode !== mode || (saved.gameplay ?? 'story') !== gameplay || !Number.isSafeInteger(saved.tick) || saved.tick < 0 || !Number.isFinite(saved.time) || saved.time < 0) return false;
  if (!['private', 'public'].includes(mode) || !['story', 'freeroam'].includes(gameplay) || (saved.schema >= 2 && !['story', 'freeroam'].includes(saved.gameplay ?? '')) || (saved.schema === 1 && gameplay !== 'story')) return false;
  if ((saved.schema >= 2 && !saved.contracts) || (saved.contracts && !validContracts(saved.contracts, saved.time))) return false;
  if (gameplay === 'story' && saved.contracts && (saved.contracts.active || Object.values(saved.contracts.progression).some(value => value !== 0) || saved.contracts.recent.length || Object.keys(saved.contracts.cooldowns).length || saved.contracts.nextInstance !== 1 || saved.contracts.revision !== 0)) return false;
  if (!Array.isArray(saved.players) || saved.players.length > (mode === 'private' ? 4 : 16) || !saved.players.every(p => validObject(p) && position(p) && validId(p.id) && validName(p.name) && Number.isSafeInteger(p.lastInputSeq) && p.lastInputSeq >= -1)) return false;
  if (new Set(saved.players.map(p => p.id)).size !== saved.players.length) return false;
  if ((saved.schema === 3 && !saved.city) || !validCity(saved.city ?? emptyCity(), saved)) return false;
  if ((saved.schema < 3 || gameplay === 'story') && saved.city && (saved.city.completedJobs.length || Object.values(saved.city.sectors).some(Boolean) || Object.keys(saved.city.votes).length || saved.city.decision || saved.city.outcome || saved.city.revision)) return false;
  if (!Array.isArray(saved.vehicles) || saved.vehicles.length !== 2 || !saved.vehicles.every(v => validObject(v) && position(v) && ['compact-01', 'van-01'].includes(v.id) && v.kind === (v.id === 'compact-01' ? 'car' : 'van') && Number.isFinite(v.speed) && Math.abs(v.speed) <= 21 && Array.isArray(v.occupants) && v.occupants.length === 4 && v.occupants.every(id => id === null || saved.players.some(p => p.id === id)))) return false;
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
  readonly gameplay: Gameplay;
  tick = 0;
  time = 0;
  players = new Map<string, PlayerSnapshot>();
  vehicles = new Map<string, VehicleSnapshot>();
  mission: MissionSnapshot;
  contracts: ContractsSnapshot = emptyContracts();
  city: CityReformSnapshot = emptyCity();
  private inputs = new Map<string, StoredInput>();
  private commands = new Map<string, Map<string, ResultMessage>>();

  constructor(room: string, mode: Mode = 'private', restored?: PersistedSimulation, gameplay?: Gameplay) {
    this.room = room;
    this.mode = mode;
    this.gameplay = gameplay ?? restored?.gameplay ?? 'story';
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
    // A disconnected voter loses their pending city ballot; only a new, valid vote can decide the mandate.
    if (Object.hasOwn(this.city.votes, id)) { delete this.city.votes[id]; this.city.revision++; }
  }

  removePlayer(id: string): void {
    this.disconnectPlayer(id);
    this.players.delete(id);
    // Keep accepted command IDs for the persistent bearer identity even after its seat expires.
  }

  input(playerId: string, message: InputMessage): boolean {
    const player = this.players.get(playerId);
    if (!player?.connected || message.seq <= player.lastInputSeq || !Number.isSafeInteger(message.seq) || ![message.moveX, message.moveZ, message.forward, message.turn].every(n => Number.isFinite(n) && Math.abs(n) <= 1) || (message.brake !== undefined && typeof message.brake !== 'boolean')) return false;
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
    if (command.action === 'city_choice') {
      const code = this.handleCityChoice(player, command);
      return result(code === 'CITY_VOTE_RECORDED' || code === 'CITY_DECIDED', code);
    }
    if (command.action.startsWith('job_')) {
      if (this.gameplay !== 'freeroam') return result(false, 'FREEROAM_REQUIRED');
      const code = this.handleContractCommand(player, command);
      return result(['JOB_STARTED', 'JOB_STAGE_COMPLETE', 'JOB_COMPLETE', 'JOB_CANCELLED'].includes(code), code);
    }
    if (this.gameplay === 'freeroam') return result(false, 'STORY_REQUIRED');
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

  private contractStage(): { active: ActiveContract; job: JobDefinition; stage: JobStage } | null {
    const active = this.contracts.active;
    if (!active) return null;
    const job = contractDefinition(active.jobId)!;
    return { active, job, stage: job.stages[active.stageIndex]! };
  }

  private handleCityChoice(player: PlayerSnapshot, command: CommandMessage): string {
    if (this.gameplay !== 'freeroam') return 'FREEROAM_REQUIRED';
    if (command.target !== 'city-mandate') return 'WRONG_TARGET';
    if (command.value !== 'reform' && command.value !== 'capture') return 'CITY_INVALID_CHOICE';
    if (this.city.decision) return 'CITY_ALREADY_DECIDED';
    if (!cityReady(this.city)) return 'CITY_LOCKED';
    if (this.contracts.active) return 'CITY_JOB_ACTIVE';
    const hall = landmark('civic')!;
    if (distance(player, hall) > hall.radius) return 'TOO_FAR';
    if (player.vehicleId) return 'EXIT_VEHICLE_FIRST';
    this.city.votes[player.id] = command.value;
    this.city.revision++;
    const connected = [...this.players.values()].filter(actor => actor.connected);
    const required = Math.floor(connected.length / 2) + 1;
    const route: CityRoute = command.value;
    if (connected.filter(actor => this.city.votes[actor.id] === route).length < required) return 'CITY_VOTE_RECORDED';
    this.city.decision = { route, decidedAt: this.time };
    this.city.outcome = clone(CITY_OUTCOMES[route]);
    this.city.votes = {};
    return 'CITY_DECIDED';
  }

  private refreshContractPresentation(): void {
    const current = this.contractStage();
    if (!current) return;
    const { active, stage } = current;
    const point = stage.targetVehicleId ? this.vehicles.get(stage.targetVehicleId)! : landmark(stage.targetId)!;
    Object.assign(active, { stageId: stage.id, objective: stage.objective, targetId: stage.targetId, targetPosition: { x: point.x, z: point.z }, action: stage.action, vehicle: stage.vehicle ?? 'none', targetVehicleId: stage.targetVehicleId ?? null });
  }

  private handleContractCommand(player: PlayerSnapshot, command: CommandMessage): string {
    if (command.action === 'job_start') {
      if (this.contracts.active) return 'JOB_ALREADY_ACTIVE';
      const job = contractDefinition(command.target ?? '');
      if (!job) return 'UNKNOWN_JOB';
      if (job.once && this.city.completedJobs.includes(job.id)) return 'JOB_ALREADY_COMPLETED';
      if ((job.requiresJobs ?? []).some(id => !this.city.completedJobs.includes(id))) return 'JOB_PREREQUISITE';
      if (this.contracts.progression.reputation < (job.minReputation ?? 0)) return 'JOB_LOCKED';
      if ((this.contracts.cooldowns[job.id] ?? 0) > this.time) return 'JOB_COOLDOWN';
      // Starting new work interrupts a pending hearing; later votes must be submitted again in person.
      if (Object.keys(this.city.votes).length) { this.city.votes = {}; this.city.revision++; }
      const stage = job.stages[0]!;
      const instanceId = `job-${this.contracts.nextInstance++}`;
      this.contracts.active = { instanceId, jobId: job.id, stageIndex: 0, stageId: stage.id, objective: stage.objective, targetId: stage.targetId, targetPosition: { x: 0, z: 0 }, action: stage.action, vehicle: stage.vehicle ?? 'none', targetVehicleId: stage.targetVehicleId ?? null, startedBy: player.id, startedAt: this.time, stageStartedAt: this.time, deadlineAt: job.timeLimitSeconds ? this.time + job.timeLimitSeconds : null, vehicleId: null, cargo: false, participants: [], orphanedAt: null };
      this.contracts.revision++; this.refreshContractPresentation();
      return 'JOB_STARTED';
    }
    const current = this.contractStage();
    if (!current) return 'NO_ACTIVE_JOB';
    const { active, stage } = current;
    if (command.target !== active.instanceId) return 'STALE_JOB';
    if (active.deadlineAt !== null && this.time >= active.deadlineAt) { this.finishContract('failed'); return 'JOB_EXPIRED'; }
    if (command.action === 'job_cancel') {
      const ownerConnected = this.players.get(active.startedBy)?.connected ?? false;
      const canRecover = !ownerConnected && (active.participants.includes(player.id) || (active.orphanedAt !== null && this.time - active.orphanedAt >= 30));
      if (player.id !== active.startedBy && !canRecover) return 'JOB_OWNER_REQUIRED';
      this.finishContract('cancelled'); return 'JOB_CANCELLED';
    }
    if (command.action !== 'job_interact') return 'UNKNOWN_ACTION';
    if (command.value !== stage.id) return 'STALE_JOB_STAGE';
    if (stage.action !== 'interact') return 'CHECKPOINT_REQUIRED';
    const checked = this.validateContractStage(player, active, stage);
    if (checked !== 'OK') return checked;
    this.advanceContract(player);
    return this.contracts.active ? 'JOB_STAGE_COMPLETE' : 'JOB_COMPLETE';
  }

  private validateContractStage(player: PlayerSnapshot, active: ActiveContract, stage: JobStage): string {
    if (!player.connected) return 'NOT_CONNECTED';
    if (this.time - active.stageStartedAt < (stage.minimumSeconds ?? 0)) return 'JOB_WAIT';
    const targetVehicle = stage.targetVehicleId ? this.vehicles.get(stage.targetVehicleId) : undefined;
    const place = targetVehicle ?? landmark(stage.targetId);
    if (!place) return 'UNKNOWN_TARGET';
    const radius = targetVehicle ? 5.8 : landmark(stage.targetId)!.radius;
    if (distance(player, place) > radius) return 'TOO_FAR';
    const maximumSpeed = stage.maxSpeed ?? (stage.action === 'interact' ? 1.5 : Infinity);
    if (targetVehicle && (Math.abs(targetVehicle.speed) > maximumSpeed || targetVehicle.occupants.some(Boolean))) return 'RECOVERY_VEHICLE_OCCUPIED';
    const required = stage.vehicle ?? 'none';
    const vehicle = player.vehicleId ? this.vehicles.get(player.vehicleId) : undefined;
    if (required === 'none') {
      if (vehicle) return 'EXIT_VEHICLE_FIRST';
    } else {
      if (!vehicle || player.seat !== 0) return 'DRIVER_REQUIRED';
      if (required !== 'any' && vehicle.kind !== required) return 'WRONG_VEHICLE';
      if (active.vehicleId && vehicle.id !== active.vehicleId) return 'BOUND_VEHICLE_REQUIRED';
      if (Math.abs(vehicle.speed) > maximumSpeed) return 'VEHICLE_MOVING';
    }
    if (stage.grantCargo && (!vehicle || player.seat !== 0)) return 'DRIVER_REQUIRED';
    if (stage.grantCargo && active.cargo) return 'CARGO_ALREADY_LOADED';
    if (stage.requiresCargo || stage.consumeCargo) {
      if (!active.cargo || !active.vehicleId) return 'CARGO_REQUIRED';
      const carrier = this.vehicles.get(active.vehicleId)!;
      if (distance(carrier, place) > radius) return 'CARGO_TOO_FAR';
      if (Math.abs(carrier.speed) > maximumSpeed) return 'VEHICLE_MOVING';
    }
    return 'OK';
  }

  private advanceContract(player: PlayerSnapshot): void {
    const { active, job, stage } = this.contractStage()!;
    if (!active.vehicleId) active.vehicleId = stage.targetVehicleId ?? (stage.vehicle && stage.vehicle !== 'none' ? player.vehicleId : null);
    if (stage.grantCargo) active.cargo = true;
    if (stage.consumeCargo) active.cargo = false;
    if (!active.participants.includes(player.id) && active.participants.length < 256) active.participants.push(player.id);
    active.stageIndex++;
    if (active.stageIndex >= job.stages.length) { this.finishContract('completed'); return; }
    active.stageStartedAt = this.time;
    this.contracts.revision++; this.refreshContractPresentation();
  }

  private finishContract(status: 'completed' | 'failed' | 'cancelled'): void {
    const current = this.contractStage();
    if (!current) return;
    const { active, job } = current;
    // The active instance is consumed in the same transaction as its one room-wide reward.
    if (this.contracts.recent.some(outcome => outcome.instanceId === active.instanceId)) { this.contracts.active = null; return; }
    const reward = status === 'completed' ? getEffectiveJobReward(job.reward, this.city.decision?.route ?? null) : { credits: 0, reputation: 0, project: 0 };
    for (const key of ['credits', 'reputation', 'project'] as const) this.contracts.progression[key] = Math.min(1e9, this.contracts.progression[key] + reward[key]);
    if (status === 'completed') {
      this.contracts.progression.completed = Math.min(1e9, this.contracts.progression.completed + 1);
      if (job.once && !this.city.completedJobs.includes(job.id)) {
        this.city.completedJobs.push(job.id);
        if (job.sector) this.city.sectors[job.sector]++;
        this.city.revision++;
      }
    }
    this.contracts.recent.unshift({ instanceId: active.instanceId, jobId: job.id, status, finishedAt: this.time, ...reward, participants: [...active.participants] });
    this.contracts.recent = this.contracts.recent.slice(0, 20);
    this.contracts.cooldowns[job.id] = this.time + (status === 'completed' ? job.cooldownSeconds : 5);
    this.contracts.active = null; this.contracts.revision++;
  }

  private stepContracts(): void {
    const current = this.contractStage();
    if (!current) return;
    const { active, stage } = current;
    if (this.players.get(active.startedBy)?.connected) active.orphanedAt = null;
    else if (active.orphanedAt === null) active.orphanedAt = this.time;
    if (active.deadlineAt !== null && this.time >= active.deadlineAt) { this.finishContract('failed'); return; }
    this.refreshContractPresentation();
    if (stage.action !== 'checkpoint') return;
    const player = [...this.players.values()].find(actor => this.validateContractStage(actor, active, stage) === 'OK');
    if (player) this.advanceContract(player);
  }

  /** Private choices use a majority of the currently connected crew; public contracts resolve one vote. */
  private resolveVote(): boolean {
    if (this.gameplay !== 'story' || this.mission.complete) return false;
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
    if (this.gameplay !== 'story' || this.mission.complete) return;
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
      const braking = active && stored.message.brake === true;
      if (braking) vehicle.speed = Math.sign(vehicle.speed) * Math.max(0, Math.abs(vehicle.speed) - 24 * dt);
      else if (Math.abs(forward) > 0.01) vehicle.speed = clamp(vehicle.speed + forward * (vehicle.speed * forward < 0 ? 24 : 12) * dt, -7, vehicle.kind === 'van' ? 16 : 21);
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
    if (this.gameplay === 'freeroam') this.stepContracts();
  }

  snapshot(): Snapshot { return clone({ type: 'snapshot', protocol: PROTOCOL_VERSION, tick: this.tick, time: this.time, room: this.room, mode: this.mode, gameplay: this.gameplay, players: [...this.players.values()], vehicles: [...this.vehicles.values()], mission: this.mission, contracts: this.contracts, city: this.city }); }
  serialize(): PersistedSimulation { return { schema: 3, contentVersion: CONTENT_VERSION, ...this.snapshot(), commands: Object.fromEntries([...this.commands].map(([id, commands]) => [id, Object.fromEntries(commands)])) }; }

  private restore(saved: PersistedSimulation): void {
    if (!validCheckpoint(saved, this.room, this.mode, this.gameplay)) throw new Error('INVALID_CHECKPOINT');
    this.tick = saved.tick; this.time = saved.time; this.mission = clone(saved.mission); this.mission.votes = {};
    this.contracts = saved.contracts ? clone(saved.contracts) : emptyContracts();
    this.city = saved.city ? clone(saved.city) : emptyCity();
    this.city.votes = {};
    this.city.outcome = this.city.decision ? clone(CITY_OUTCOMES[this.city.decision.route]) : null;
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
    this.refreshContractPresentation();
  }
}
