import { HEROES } from '../shared/heroes.js';
import { ArenaSimulation, ARENA_RULES } from '../shared/simulation.js';
import type { ArenaInput, CommandResult } from '../shared/types.js';
import { ControlPoint, CONTROL_RULES } from './objective.js';
import { ReferenceBots, referenceBotHero } from './bots.js';
import type { EconomyReceipt, ReferenceCommand, ReferenceOptions, ReferenceSnapshot, WalletSnapshot, WeaponSnapshot } from './types.js';
export type * from './types.js';
export { CONTROL_RULES } from './objective.js';

export const REFERENCE_RULES = Object.freeze({ fixedStep: .05, maxElapsed: .25, magazine: 12, reloadSeconds: 1.6, laneDuration: 480, controlDuration: 240, maxReceipts: 128, maxCommands: 4096 });
export const REFERENCE_EXPERIMENTS = [
  { id: 'lane-economy', title: 'Three-lane economy', description: 'Original lane waves, contested shards, jungle powers and upgrades. Push two towers, then their core; the eight-minute arena result applies.' },
  { id: 'control-point', title: 'Hybrid team control', description: 'Original six-second capture and occupied hold scoring added to the same lane arena. Towers, waves and camps remain active. An arena victory takes precedence, then 60 control points, then the four-minute point tally.' },
] as const;
const validCommandId = (id: unknown): id is string => typeof id === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(id);
const copy = <T>(value: T): T => structuredClone(value);

/** Offline original mechanics lab. All combat, wallet changes and collision are
 * delegated to the arena's public API with unchanged combat rules and an optional
 * shot receipt observer. Input gating, objective accounting and terminal
 * precedence belong to this separate controller. */
export class ReferenceLab {
  readonly localId = 'reference-player';
  private epochCounter = 0;
  get epoch(): number { return this.epochCounter; }
  private options: Required<ReferenceOptions>;
  private arena!: ArenaSimulation;
  private bots!: ReferenceBots;
  private point = new ControlPoint();
  private botIds: string[] = [];
  private weapons = new Map<string, WeaponSnapshot>();
  private wallets: Record<string, WalletSnapshot> = {};
  private receipts: EconomyReceipt[] = [];
  private receiptSerial = 0;
  private commands = new Map<string, Map<string, CommandResult>>();
  private sequences = new Map<string, number>();
  private lastLocalSequence = -1;
  private localInput: { value: ArenaInput; at: number } | null = null;
  private accumulator = 0;
  private paused = false;
  private disposed = false;
  private phase: ReferenceSnapshot['phase'] = 'playing';
  private winner: ReferenceSnapshot['winner'] = null;
  private reason = '';

  constructor(options: ReferenceOptions) { this.options = this.validate(options); this.reset(); }
  private validate(options: ReferenceOptions): Required<ReferenceOptions> {
    if (!REFERENCE_EXPERIMENTS.some(value => value.id === options.experiment)) throw new Error('UNKNOWN_EXPERIMENT');
    if (!HEROES.some(hero => hero.id === options.heroId)) throw new Error('UNKNOWN_HERO');
    const seed = options.seed ?? 7301;
    if (!Number.isSafeInteger(seed) || seed < 0 || seed > 0xffffffff) throw new Error('INVALID_SEED');
    return { ...options, seed };
  }
  reset(options: Partial<ReferenceOptions> = {}): ReferenceSnapshot {
    if (this.disposed) throw new Error('LAB_DISPOSED');
    this.options = this.validate({ ...this.options, ...options }); this.epochCounter++;
    this.arena = new ArenaSimulation({ room: `REFERENCE-${this.epoch}`, seed: this.options.seed, botsPerTeam: 0, duration: REFERENCE_RULES.laneDuration,
      onPrimaryShot: receipt => {
        const weapon = this.weapons.get(receipt.actorId);
        if (weapon) weapon.ammo = Math.max(0, weapon.ammo - 1);
      } });
    this.arena.addPlayer(this.localId, 'You', this.options.heroId, 'sun');
    this.botIds = [];
    for (let index = 0; index < 5; index++) {
      const id = `reference-ai-${index}`, hero = referenceBotHero(this.options.seed, index);
      this.arena.addPlayer(id, `${HEROES.find(value => value.id === hero)!.name} · AI`, hero, index < 2 ? 'sun' : 'moon'); this.botIds.push(id);
    }
    this.bots = new ReferenceBots(this.options.experiment, this.options.seed); this.point.reset();
    this.weapons.clear(); this.wallets = {}; this.commands.clear(); this.sequences.clear();
    for (const actor of this.arena.actors.values()) {
      this.weapons.set(actor.id, { ammo: REFERENCE_RULES.magazine, capacity: REFERENCE_RULES.magazine, reloadRemaining: 0, reloadSeconds: REFERENCE_RULES.reloadSeconds });
      this.wallets[actor.id] = { balance: actor.credits, earned: 0, spent: 0 }; this.commands.set(actor.id, new Map()); this.sequences.set(actor.id, 0);
    }
    this.receipts = []; this.receiptSerial = 0; this.lastLocalSequence = -1; this.localInput = null;
    this.accumulator = 0; this.paused = false; this.phase = 'playing'; this.winner = null; this.reason = '';
    return this.snapshot();
  }
  input(input: ArenaInput, epoch: number): boolean {
    if (this.disposed || this.paused || this.phase !== 'playing' || epoch !== this.epoch || !input || input.type !== 'input' || !Number.isSafeInteger(input.seq) || input.seq <= this.lastLocalSequence || input.seq < 0 || ![input.moveX, input.moveZ, input.yaw, input.pitch].every(Number.isFinite) || typeof input.fire !== 'boolean' || typeof input.jump !== 'boolean') return false;
    this.lastLocalSequence = input.seq; this.localInput = { value: copy(input), at: this.arena.time }; return true;
  }
  command(command: ReferenceCommand, epoch: number): CommandResult {
    if (!command || command.type !== 'command' || !validCommandId(command.id)) return { type: 'result', id: typeof command?.id === 'string' ? command.id : 'invalid', ok: false, code: 'INVALID_COMMAND' };
    if (epoch !== this.epoch) return { type: 'result', id: command.id, ok: false, code: 'STALE_EPOCH' };
    return this.dispatch(this.localId, command);
  }
  private dispatch(id: string, command: ReferenceCommand): CommandResult {
    const cache = this.commands.get(id), prior = cache?.get(command.id); if (prior) return copy(prior);
    const result = (ok: boolean, code: string): CommandResult => {
      const response: CommandResult = { type: 'result', id: command.id, ok, code };
      if (validCommandId(command.id) && cache && cache.size < REFERENCE_RULES.maxCommands) cache.set(command.id, response);
      return copy(response);
    };
    if (!validCommandId(command.id)) return result(false, 'INVALID_COMMAND');
    if (this.disposed) return result(false, 'LAB_DISPOSED');
    if (this.phase !== 'playing') return result(false, 'MATCH_FINISHED');
    // A deliberate forge purchase may use the paused menu; combat and reload
    // remain stopped, and the arena still validates location, cost and level.
    if (this.paused && command.action !== 'upgrade') return result(false, 'PAUSED');
    if (!cache || cache.size >= REFERENCE_RULES.maxCommands) return result(false, 'COMMAND_LIMIT');
    const actor = this.arena.actors.get(id), weapon = this.weapons.get(id);
    if (!actor || actor.health <= 0 || actor.respawn > 0) return result(false, 'RESPAWNING');
    if (command.action === 'reload') {
      if (actor.cast) return result(false, 'CAST_IN_PROGRESS');
      if (weapon!.reloadRemaining > 0) return result(false, 'RELOADING');
      if (weapon!.ammo === weapon!.capacity) return result(false, 'MAGAZINE_FULL');
      weapon!.reloadRemaining = weapon!.reloadSeconds; this.arena.clearInput(id); return result(true, 'RELOAD_STARTED');
    }
    // Apply the latest accepted local aim before immediate abilities, without
    // advancing time or fabricating a movement/fire acknowledgement.
    if (id === this.localId) this.forwardLocal();
    const response = this.arena.command(id, command); cache.set(command.id, response); this.recordEconomy(); return copy(response);
  }
  private forward(id: string, value: Omit<ArenaInput, 'type' | 'seq'>): void {
    const weapon = this.weapons.get(id)!;
    this.arena.input(id, { ...value, type: 'input', seq: (this.sequences.get(id) ?? 0) + 1, fire: value.fire && weapon.ammo > 0 && weapon.reloadRemaining <= 0 });
    this.sequences.set(id, (this.sequences.get(id) ?? 0) + 1);
  }
  private forwardLocal(): void {
    if (this.localInput && this.arena.time - this.localInput.at <= ARENA_RULES.inputExpiry) this.forward(this.localId, this.localInput.value);
    else this.arena.clearInput(this.localId);
  }
  pause(value: boolean): void {
    if (this.disposed || this.paused === value) return;
    this.paused = value; this.accumulator = 0; this.localInput = null;
    for (const id of this.weapons.keys()) this.arena.clearInput(id);
  }
  step(elapsedSeconds: number): void {
    if (this.disposed || this.paused || this.phase !== 'playing' || !Number.isFinite(elapsedSeconds) || elapsedSeconds <= 0) return;
    this.accumulator += Math.min(elapsedSeconds, REFERENCE_RULES.maxElapsed);
    const count = Math.min(5, Math.floor((this.accumulator + 1e-9) / REFERENCE_RULES.fixedStep));
    this.accumulator = Math.max(0, this.accumulator - count * REFERENCE_RULES.fixedStep);
    for (let index = 0; index < count && this.phase === 'playing'; index++) this.fixedStep();
  }
  private fixedStep(): void {
    const dt = REFERENCE_RULES.fixedStep, before = this.arena.snapshot();
    for (const actor of before.actors) {
      const weapon = this.weapons.get(actor.id); if (!weapon) continue;
      if (actor.health <= 0) { weapon.reloadRemaining = 0; weapon.ammo = weapon.capacity; }
      else if (weapon.reloadRemaining > 0) { weapon.reloadRemaining = Math.max(0, weapon.reloadRemaining - dt); if (weapon.reloadRemaining < 1e-9) { weapon.reloadRemaining = 0; weapon.ammo = weapon.capacity; } }
    }
    for (const id of this.botIds) {
      const actor = before.actors.find(value => value.id === id)!;
      const intent = this.bots.intent(before, actor, this.weapons.get(id)!);
      this.forward(id, intent); if (intent.command) this.dispatch(id, intent.command);
    }
    this.forwardLocal();
    // The synchronous creation receipt debits only accepted primary shots,
    // including shots whose visual event is evicted within this same tick.
    this.arena.step(dt);
    const after = this.arena.snapshot();
    this.recordEconomy();
    if (after.phase === 'finished') { this.finish(after.winner!, `Arena result: ${after.reason}`); return; }
    if (this.options.experiment === 'control-point') {
      const result = this.point.step(after.actors, dt);
      if (result.winner) this.finish(result.winner, 'Control target reached: 60 occupied hold points');
      else if (after.time + 1e-9 >= CONTROL_RULES.duration) {
        const scores = this.point.snapshot().scores;
        this.finish(scores.sun === scores.moon ? 'draw' : scores.sun > scores.moon ? 'sun' : 'moon', 'Control time limit: higher control score; equal scores draw');
      }
    }
  }
  private recordEconomy(): void {
    for (const actor of this.arena.actors.values()) {
      const wallet = this.wallets[actor.id]; if (!wallet) continue;
      const delta = actor.credits - wallet.balance; if (!delta) continue;
      if (delta > 0) wallet.earned += delta; else wallet.spent -= delta; wallet.balance = actor.credits;
      this.receipts.push({ id: ++this.receiptSerial, epoch: this.epoch, time: this.arena.time, actorId: actor.id, amount: Math.abs(delta), kind: delta > 0 ? 'income' : 'spend', balance: actor.credits });
    }
    if (this.receipts.length > REFERENCE_RULES.maxReceipts) this.receipts.splice(0, this.receipts.length - REFERENCE_RULES.maxReceipts);
  }
  private finish(winner: NonNullable<ReferenceSnapshot['winner']>, reason: string): void {
    this.phase = 'finished'; this.winner = winner; this.reason = reason; this.accumulator = 0; this.localInput = null;
    for (const id of this.weapons.keys()) this.arena.clearInput(id);
  }
  snapshot(): ReferenceSnapshot {
    return { epoch: this.epoch, experiment: this.options.experiment, localId: this.localId, paused: this.paused, phase: this.phase, winner: this.winner, reason: this.reason,
      timeLeft: Math.max(0, (this.options.experiment === 'control-point' ? CONTROL_RULES.duration : REFERENCE_RULES.laneDuration) - this.arena.time),
      arena: this.arena.snapshot(), objective: this.options.experiment === 'control-point' ? this.point.snapshot() : null, weapons: Object.fromEntries([...this.weapons].map(([id, weapon]) => [id, { ...weapon }])), botIds: [...this.botIds], economy: { wallets: copy(this.wallets), receipts: copy(this.receipts) } };
  }
  dispose(): void { this.pause(true); this.disposed = true; this.localInput = null; this.commands.clear(); }
}
