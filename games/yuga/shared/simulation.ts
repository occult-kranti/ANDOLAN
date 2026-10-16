import { HEROES, heroById } from './heroes.js';
import { ARENA, GOLD_RULES, JUNGLE_CAMPS, JUNGLE_RULES, LANES, LANE_X, NEUTRAL_STATS, SPAWNS, SOLIDS, blocked, distance, lineClear } from './map.js';
import { YUGA_PROTOCOL } from './types.js';
import type { AbilityDef, Actor, ArenaCommand, ArenaInput, ArenaSnapshot, CombatTeam, CommandResult, GameEvent, GoldShard, Lane, Neutral, Pickup, Projectile, Structure, Team, UnitArchetype, Vec, Zone } from './types.js';

export const UPGRADE_COSTS = { power: 120, vitality: 100, tempo: 140 } as const;
export const MAX_UPGRADE = 3;
export const ARENA_RULES = { heroRadius: .65, towerRadius: 1.8, coreRadius: 2.8, maxActors: 96, maxProjectiles: 192, maxZones: 32, eventHistory: 64, waveSeconds: 18, baseRadius: 15, inputExpiry: .35 } as const;
/** Synchronous notification of a successfully created hero primary projectile.
 * Optional local adapters can observe it without relying on bounded FX history.
 * Observers must not throw or reenter the simulation; this is not an isolated hook. */
export interface PrimaryShotReceipt { readonly actorId: string; readonly projectileId: string; readonly tick: number; readonly time: number }
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const copy = <T>(value: T): T => structuredClone(value);
const validId = (id: unknown): id is string => typeof id === 'string' && /^[a-zA-Z0-9_-]{1,64}$/.test(id);
const aim = (yaw: number, pitch = 0) => ({ x: Math.sin(yaw) * Math.cos(pitch), y: Math.sin(pitch), z: Math.cos(yaw) * Math.cos(pitch) });
const formationOffset = (archetype?: UnitArchetype) => archetype === 'soldier' ? -1.2 : archetype === 'minister' ? 1.2 : 0;
type Target = Actor | Structure | Neutral;
type StoredInput = { value: ArenaInput; time: number };
type Memory = { waypoint: number; velocityY: number; jumping: boolean; expires?: number; attackDamage?: number; supportAt?: number };
type NeutralMemory = { cooldown: number; unseen: number };
export const ESCORT_STATS = {
  soldier: { name: 'Soldier', health: 130, damage: 14, range: 11, stop: 7, interval: 1.05 },
  'city-watch': { name: 'City Watch', health: 90, damage: 10, range: 17, stop: 13, interval: 1.1 },
  minister: { name: 'Minister', health: 100, damage: 7, range: 13, stop: 9, interval: 1.2 },
} as const;

/** Original bounded authoritative arena. Browser practice and WebSocket rooms use these same rules. */
export class ArenaSimulation {
  readonly room: string;
  readonly seed: number;
  readonly duration: number;
  tick = 0;
  time = 0;
  phase: ArenaSnapshot['phase'] = 'playing';
  winner: ArenaSnapshot['winner'] = null;
  reason = '';
  actors = new Map<string, Actor>();
  neutrals: Neutral[] = [];
  goldShards: GoldShard[] = [];
  structures: Structure[] = [];
  projectiles: Projectile[] = [];
  zones: Zone[] = [];
  pickups: Pickup[] = [];
  scores: Record<Team, number> = { sun: 0, moon: 0 };
  private events: GameEvent[] = [];
  private inputs = new Map<string, StoredInput>();
  private memory = new Map<string, Memory>();
  private commands = new Map<string, Map<string, CommandResult>>();
  private towerCooldowns = new Map<string, number>();
  private contributors = new Map<string, Map<string, number>>();
  private neutralMemory = new Map<string, NeutralMemory>();
  private randomState: number;
  private serial = 0;
  private eventSerial = 0;
  private nextWave = 1;
  private waveNumber = 0;
  private readonly teamSize: number;
  private readonly onPrimaryShot?: (receipt: PrimaryShotReceipt) => void;

  constructor(options: { room?: string; seed?: number; duration?: number; botsPerTeam?: number; onPrimaryShot?: (receipt: PrimaryShotReceipt) => void } = {}) {
    this.room = options.room ?? 'PRACTICE';
    this.seed = Number.isSafeInteger(options.seed) ? options.seed! >>> 0 : 7301;
    this.randomState = this.seed || 1;
    this.duration = Number.isFinite(options.duration) ? clamp(options.duration!, 1, 4800) : ARENA.duration;
    this.teamSize = Number.isInteger(options.botsPerTeam) ? clamp(options.botsPerTeam!, 0, 3) : 3;
    this.onPrimaryShot = options.onPrimaryShot;
    for (const team of ['sun', 'moon'] as const) {
      const sign = team === 'sun' ? -1 : 1;
      for (const lane of [0, 1, 2] as const) this.structures.push({ id: `${team}-tower-${lane}`, kind: 'tower', team, lane, x: LANE_X[lane], z: sign * 37, health: 680, maxHealth: 680, shielded: false });
      this.structures.push({ id: `${team}-core`, kind: 'core', team, lane: 1, x: 0, z: sign * 75, health: 1400, maxHealth: 1400, shielded: true });
      this.fillBots(team);
    }
    for (const [index, point] of [{ x: -40, z: -12 }, { x: 40, z: 12 }, { x: 0, z: -18 }, { x: 0, z: 18 }, { x: -40, z: 18 }, { x: 40, z: -18 }].entries()) {
      this.pickups.push({ id: `pickup-${index}`, ...point, kind: (['vigor', 'haste', 'ward'] as const)[index % 3]!, readyAt: 8 });
    }
    for (const camp of JUNGLE_CAMPS) {
      const stats = NEUTRAL_STATS[camp.species], id = `neutral-${camp.id}`;
      this.neutrals.push({ id, kind: 'neutral', team: 'neutral', species: camp.species, campId: camp.id, name: stats.name, x: camp.x, z: camp.z, y: 0, yaw: 0, health: 0, maxHealth: stats.health, state: 'dead', targetId: null, respawnAt: JUNGLE_RULES.firstSpawn, slow: 0 });
      this.neutralMemory.set(id, { cooldown: 0, unseen: 0 });
    }
  }

  private random(): number { this.randomState = (Math.imul(this.randomState, 1664525) + 1013904223) >>> 0; return this.randomState / 0x100000000; }
  private emit(type: GameEvent['type'], actorId: string, team: CombatTeam, point: Vec, label: string, color: string, targetId?: string, details: Pick<GameEvent, 'amount' | 'reward' | 'buff' | 'sharedAwards'> = {}): void {
    this.events.push({ id: ++this.eventSerial, type, actorId, team, x: point.x, z: point.z, label, color, time: this.time, ...(targetId ? { targetId } : {}), ...details });
    if (this.events.length > ARENA_RULES.eventHistory) this.events.splice(0, this.events.length - ARENA_RULES.eventHistory);
  }
  private makeHero(id: string, name: string, heroId: string, team: Team, bot: boolean, lane: Lane): Actor {
    const hero = heroById(heroId), spawn = SPAWNS[team];
    const actor: Actor = { id, name, heroId, team, bot, lane, connected: !bot, kind: 'hero', x: spawn.x + (lane - 1) * 3, z: spawn.z + (team === 'sun' ? 3 : -3), y: 0, yaw: team === 'sun' ? 0 : Math.PI, health: hero.health, maxHealth: hero.health, shield: 0, respawn: 0, cooldowns: [0, 0, 0], fireCooldown: 0, credits: 180, level: 1, kills: 0, deaths: 0, assists: 0, damageDealt: 0, upgrades: { power: 0, vitality: 0, tempo: 0 }, effects: { haste: 0, slow: 0, ward: 0 }, lastInputSeq: -1 };
    this.actors.set(id, actor); this.memory.set(id, { waypoint: 0, velocityY: 0, jumping: false });
    return actor;
  }
  private fillBots(team: Team): void {
    while ([...this.actors.values()].filter(actor => actor.kind === 'hero' && actor.team === team).length < this.teamSize) {
      const used = new Set([...this.actors.values()].filter(actor => actor.kind === 'hero' && actor.team === team).map(actor => actor.lane));
      const lane = ([0, 1, 2] as const).find(value => !used.has(value)) ?? 1;
      const hero = HEROES[Math.floor(this.random() * HEROES.length)]!;
      this.makeHero(`bot-${++this.serial}`, `${hero.name} · AI`, hero.id, team, true, lane);
    }
  }

  addPlayer(id: string, name: string, heroId: string, team?: Team): Actor {
    if (!validId(id) || /^(bot-|minion-|neutral-|gold-)/.test(id) || this.structures.some(value => value.id === id)) throw new Error('INVALID_ID');
    if (!HEROES.some(hero => hero.id === heroId)) throw new Error('UNKNOWN_HERO');
    if (team !== undefined && team !== 'sun' && team !== 'moon') throw new Error('INVALID_TEAM');
    const existing = this.actors.get(id);
    if (existing) { existing.bot = false; existing.connected = true; existing.lastInputSeq = -1; this.inputs.delete(id); return existing; }
    const humans = [...this.actors.values()].filter(actor => actor.kind === 'hero' && !actor.id.startsWith('bot-'));
    if (humans.length >= 6) throw new Error('ROOM_FULL');
    const chosen = team ?? (humans.filter(actor => actor.team === 'sun').length <= humans.filter(actor => actor.team === 'moon').length ? 'sun' : 'moon');
    if (humans.filter(actor => actor.team === chosen).length >= 3) throw new Error('TEAM_FULL');
    const replace = [...this.actors.values()].filter(actor => actor.team === chosen && actor.id.startsWith('bot-')).sort((a, b) => Math.abs(a.lane - 1) - Math.abs(b.lane - 1))[0];
    const lane = replace?.lane ?? ([0, 1, 2] as const).find(value => !humans.some(actor => actor.team === chosen && actor.lane === value)) ?? 1;
    if (replace) { this.actors.delete(replace.id); this.memory.delete(replace.id); }
    const safeName = name.replace(/[^\p{L}\p{N} _.-]/gu, '').trim().slice(0, 24) || 'Player';
    const actor = this.makeHero(id, safeName, heroId, chosen, false, lane);
    this.commands.set(id, new Map());
    return actor;
  }
  /** Preserve the reserved identity and its match progress while AI controls the abandoned lane. */
  removePlayer(id: string): void { const actor = this.actors.get(id); if (actor?.kind === 'hero') { actor.connected = false; actor.bot = true; this.inputs.delete(id); } }
  /** Server-only reservation expiry. Anonymous players can now replace the generic bot. */
  releasePlayer(id: string): void {
    const actor = this.actors.get(id); if (!actor || actor.connected) return;
    this.actors.delete(id); this.memory.delete(id); this.commands.delete(id); this.inputs.delete(id); this.fillBots(actor.team);
  }

  input(id: string, input: ArenaInput): boolean {
    const actor = this.actors.get(id);
    if (this.phase !== 'playing' || !actor?.connected || actor.bot || input.type !== 'input' || !Number.isSafeInteger(input.seq) || input.seq <= actor.lastInputSeq || input.seq < 0 || ![input.moveX, input.moveZ, input.yaw, input.pitch].every(Number.isFinite) || typeof input.fire !== 'boolean' || typeof input.jump !== 'boolean') return false;
    actor.lastInputSeq = input.seq;
    this.inputs.set(id, { time: this.time, value: { ...input, moveX: clamp(input.moveX, -1, 1), moveZ: clamp(input.moveZ, -1, 1), yaw: Math.atan2(Math.sin(input.yaw), Math.cos(input.yaw)), pitch: clamp(input.pitch, -1.35, 1.35) } });
    return true;
  }
  clearInput(id: string): void { this.inputs.delete(id); }
  command(id: string, command: ArenaCommand): CommandResult {
    const cache = this.commands.get(id), prior = cache?.get(command.id);
    if (prior) return copy(prior);
    const result = (ok: boolean, code: string) => {
      const response: CommandResult = { type: 'result', id: command.id, ok, code };
      if (cache && cache.size < 4096 && validId(command.id)) cache.set(command.id, response);
      return response;
    };
    const actor = this.actors.get(id);
    if (!validId(command.id)) return result(false, 'INVALID_COMMAND');
    if (!actor?.connected || actor.bot) return result(false, 'NOT_CONNECTED');
    if (this.phase !== 'playing') return result(false, 'MATCH_FINISHED');
    if (cache && cache.size >= 4096) return result(false, 'COMMAND_LIMIT');
    if (actor.health <= 0) return result(false, 'RESPAWNING');
    if (actor.cast) return result(false, 'CAST_IN_PROGRESS');
    if (command.action === 'upgrade') {
      if (!Object.hasOwn(UPGRADE_COSTS, command.upgrade)) return result(false, 'UNKNOWN_UPGRADE');
      if (distance(actor, SPAWNS[actor.team]) > ARENA_RULES.baseRadius) return result(false, 'RETURN_TO_BASE');
      const rank = actor.upgrades[command.upgrade];
      if (rank >= MAX_UPGRADE) return result(false, 'UPGRADE_MAX');
      const cost = UPGRADE_COSTS[command.upgrade] * (rank + 1);
      if (actor.credits < cost) return result(false, 'INSUFFICIENT_CREDITS');
      actor.credits -= cost; actor.upgrades[command.upgrade]++; actor.level++;
      if (command.upgrade === 'vitality') { actor.maxHealth += 65; actor.health = Math.min(actor.maxHealth, actor.health + 65); }
      this.emit('upgrade', actor.id, actor.team, actor, command.upgrade, heroById(actor.heroId).accent);
      return result(true, 'UPGRADED');
    }
    if (command.action !== 'ability' || ![0, 1, 2].includes(command.slot)) return result(false, 'UNKNOWN_ABILITY');
    if (actor.cooldowns[command.slot]! > 0) return result(false, 'ABILITY_COOLDOWN');
    const intent = this.inputs.get(id);
    if (intent && this.time - intent.time <= ARENA_RULES.inputExpiry) actor.yaw = intent.value.yaw;
    else this.inputs.delete(id);
    this.cast(actor, command.slot); return result(true, 'ABILITY_CAST');
  }

  private blockedAt(x: number, z: number, radius: number = ARENA_RULES.heroRadius): boolean {
    return blocked(x, z, radius) || this.structures.some(structure => structure.health > 0 && Math.hypot(x - structure.x, z - structure.z) < radius + (structure.kind === 'core' ? ARENA_RULES.coreRadius : ARENA_RULES.towerRadius));
  }
  private move(actor: Actor | Neutral, dx: number, dz: number): void {
    const radius = actor.kind === 'hero' ? .65 : actor.kind === 'neutral' ? JUNGLE_RULES.radius : .42;
    const slices = Math.max(1, Math.ceil(Math.hypot(dx, dz) / .35));
    for (let i = 0; i < slices; i++) {
      if (!this.blockedAt(actor.x + dx / slices, actor.z, radius)) actor.x += dx / slices;
      if (!this.blockedAt(actor.x, actor.z + dz / slices, radius)) actor.z += dz / slices;
    }
  }
  private validTargets(team: CombatTeam): Target[] {
    if (team === 'neutral') return [...this.actors.values()].filter(actor => actor.kind === 'hero' && actor.health > 0);
    return [...this.actors.values(), ...this.structures, ...this.neutrals].filter(target => target.team !== team && target.health > 0 && (!('shielded' in target) || !target.shielded));
  }
  private refreshCoreShields(): void { for (const core of this.structures.filter(value => value.kind === 'core')) core.shielded = this.structures.filter(value => value.team === core.team && value.kind === 'tower' && value.health <= 0).length < 2; }
  private award(team: Team, source: string, point: Vec, gold: number): NonNullable<GameEvent['sharedAwards']> {
    const receipts: NonNullable<GameEvent['sharedAwards']> = [];
    for (const actor of this.actors.values()) if (actor.kind === 'hero' && actor.team === team && (actor.id === source || actor.health > 0 && distance(actor, point) <= 26)) {
      const amount = Math.min(gold, 99999 - actor.credits); actor.credits += amount;
      if (amount > 0) receipts.push({ actorId: actor.id, amount });
    }
    return receipts;
  }
  private dropGold(source: Target, value: number, originTeam: Team): void {
    if (this.goldShards.length >= GOLD_RULES.maxShards) this.goldShards.shift();
    this.goldShards.push({ id: `gold-${++this.serial}`, sourceId: source.id, x: source.x, z: source.z, y: GOLD_RULES.height, value, originTeam, createdAt: this.time, expiresAt: this.time + GOLD_RULES.lifetime });
  }
  private secureGold(shard: GoldShard, actor: Actor): boolean {
    if (this.phase !== 'playing' || actor.kind !== 'hero' || actor.health <= 0 || shard.expiresAt <= this.time) return false;
    const index = this.goldShards.indexOf(shard); if (index < 0) return false;
    this.goldShards.splice(index, 1);
    const amount = Math.min(shard.value, 99999 - actor.credits); actor.credits += amount;
    const reward = actor.team === shard.originTeam ? 'secure' : 'steal';
    this.emit('gold', actor.id, actor.team, shard, reward === 'secure' ? 'Gold secured' : 'Gold intercepted', '#ffe28a', shard.id, { amount, reward });
    return true;
  }
  private stepGold(): void {
    this.goldShards = this.goldShards.filter(shard => shard.expiresAt > this.time);
    for (const shard of [...this.goldShards]) {
      if (this.time - shard.createdAt + 1e-7 < GOLD_RULES.pickupDelay) continue;
      const hero = [...this.actors.values()].filter(actor => actor.kind === 'hero' && actor.health > 0 && distance(actor, shard) <= GOLD_RULES.pickupRadius && Math.abs(actor.y + 1.1 - shard.y) <= 1.7 && lineClear(actor, shard)).sort((a, b) => distance(a, shard) - distance(b, shard) || a.id.localeCompare(b.id))[0];
      if (hero) this.secureGold(shard, hero);
    }
  }
  private stepNeutrals(dt: number): void {
    if (this.phase !== 'playing') return;
    for (const neutral of this.neutrals) {
      const camp = JUNGLE_CAMPS.find(value => value.id === neutral.campId)!, stats = NEUTRAL_STATS[neutral.species], memory = this.neutralMemory.get(neutral.id)!;
      memory.cooldown = Math.max(0, memory.cooldown - dt); neutral.slow = Math.max(0, neutral.slow - dt);
      if (neutral.state === 'dead') {
        if (this.time + 1e-7 >= neutral.respawnAt) { neutral.x = camp.x; neutral.z = camp.z; neutral.health = neutral.maxHealth; neutral.state = 'idle'; neutral.targetId = null; neutral.respawnAt = 0; memory.cooldown = .6; memory.unseen = 0; }
        continue;
      }
      if (neutral.state === 'returning') {
        const d = distance(neutral, camp);
        if (d <= .35) { neutral.x = camp.x; neutral.z = camp.z; neutral.health = neutral.maxHealth; neutral.state = 'idle'; memory.unseen = 0; }
        else { neutral.yaw = Math.atan2(camp.x - neutral.x, camp.z - neutral.z); this.move(neutral, (camp.x - neutral.x) / d * Math.min(d, 6 * dt), (camp.z - neutral.z) / d * Math.min(d, 6 * dt)); neutral.health = Math.min(neutral.maxHealth, neutral.health + neutral.maxHealth * .4 * dt); }
        continue;
      }
      let target = neutral.targetId ? this.actors.get(neutral.targetId) : undefined;
      if (!target && neutral.state === 'idle') {
        target = [...this.actors.values()].filter(actor => actor.kind === 'hero' && actor.health > 0 && distance(actor, neutral) <= JUNGLE_RULES.aggro && lineClear(neutral, actor)).sort((a, b) => distance(a, neutral) - distance(b, neutral) || a.id.localeCompare(b.id))[0];
        if (target) { neutral.targetId = target.id; neutral.state = 'aggro'; }
      }
      if (neutral.state === 'idle') { neutral.health = Math.min(neutral.maxHealth, neutral.health + 10 * dt); continue; }
      const visible = target && lineClear(neutral, target);
      memory.unseen = visible ? 0 : memory.unseen + dt;
      if (!target || target.health <= 0 || distance(target, camp) > JUNGLE_RULES.leash || distance(neutral, camp) > JUNGLE_RULES.leash || memory.unseen > 1.5) { neutral.state = 'returning'; neutral.targetId = null; neutral.slow = 0; continue; }
      const d = distance(neutral, target); neutral.yaw = Math.atan2(target.x - neutral.x, target.z - neutral.z);
      if (visible && d <= stats.range && memory.cooldown <= 0 && this.projectiles.length < ARENA_RULES.maxProjectiles) {
        const delta = { x: target.x - neutral.x, y: target.y + 1.1 - JUNGLE_RULES.bodyHeight, z: target.z - neutral.z }, length = Math.max(.001, Math.hypot(delta.x, delta.y, delta.z));
        this.projectiles.push({ id: `projectile-${++this.serial}`, owner: neutral.id, team: 'neutral', x: neutral.x, y: JUNGLE_RULES.bodyHeight, z: neutral.z, vx: delta.x / length * 23, vy: delta.y / length * 23, vz: delta.z / length * 23, damage: stats.damage, radius: .32, life: .6, color: stats.color });
        memory.cooldown = stats.interval; this.emit('shot', neutral.id, 'neutral', neutral, stats.name, stats.color);
      }
      if (d > stats.range * .8) { const amount = Math.min(d, stats.speed * dt * (neutral.slow > 0 ? .55 : 1)); this.move(neutral, (target.x - neutral.x) / Math.max(.001, d) * amount, (target.z - neutral.z) / Math.max(.001, d) * amount); }
    }
  }
  private damage(target: Target, amount: number, owner: string, team: CombatTeam): void {
    if (this.phase !== 'playing' || target.team === team || target.health <= 0 || !Number.isFinite(amount) || amount <= 0) return;
    if ('shielded' in target && target.shielded) return;
    const attacker = this.actors.get(owner);
    if (target.kind === 'neutral' && target.state === 'returning') return;
    let applied = amount;
    if ('shield' in target) { const absorbed = Math.min(target.shield, applied); target.shield -= absorbed; applied -= absorbed; }
    const actual = Math.min(target.health, applied); target.health -= actual;
    if (attacker?.kind === 'hero') attacker.damageDealt += actual;
    if ('heroId' in target && attacker?.kind === 'hero') { const contributors = this.contributors.get(target.id) ?? new Map(); contributors.set(attacker.id, this.time); this.contributors.set(target.id, contributors); }
    this.emit('hit', owner, team, target, String(Math.round(actual)), attacker ? heroById(attacker.heroId).color : '#f9d47d', target.id);
    if (target.kind === 'neutral') {
      const credited = attacker?.kind === 'hero' ? attacker : attacker?.summonerId ? this.actors.get(attacker.summonerId) : undefined;
      if (credited?.kind === 'hero' && credited.health > 0) { target.targetId = credited.id; target.state = 'aggro'; }
      if (target.health > 0) return;
      target.state = 'dead'; target.targetId = null; target.respawnAt = this.time + JUNGLE_RULES.respawn; target.slow = 0;
      if (team !== 'neutral') {
        const sharedAwards = this.award(team, credited?.id ?? owner, target, JUNGLE_RULES.sharedGold);
        this.dropGold(target, JUNGLE_RULES.shardGold, team);
        this.emit('camp', credited?.id ?? owner, team, target, `${target.name} camp cleared`, NEUTRAL_STATS[target.species].color, target.id, { amount: JUNGLE_RULES.sharedGold, sharedAwards });
        if (credited?.kind === 'hero' && credited.health > 0) {
          const buff = NEUTRAL_STATS[target.species].buff;
          credited.effects[buff] = Math.max(credited.effects[buff] ?? 0, JUNGLE_RULES.buffSeconds);
          if (buff === 'ward') credited.shield = Math.max(credited.shield, 60);
          this.emit('buff', credited.id, credited.team, target, `${buff} blessing`, NEUTRAL_STATS[target.species].color, target.id, { buff });
        }
      }
      return;
    }
    if (target.health > 0) return;
    if ('heroId' in target) {
      const hero = target.kind === 'hero';
      let sharedAwards: GameEvent['sharedAwards'];
      if (team !== 'neutral') {
        this.scores[team] += hero ? 5 : target.minionRole === 'summon' ? 0 : 1;
        if (hero) sharedAwards = this.award(team, owner, target, 100);
        else if (target.minionRole !== 'summon') { sharedAwards = this.award(team, owner, target, GOLD_RULES.laneShared); this.dropGold(target, GOLD_RULES.laneShard, team); }
      }
      if (hero) {
        target.deaths++; target.respawn = Math.min(18, 7 + target.deaths * 1.5); target.shield = 0; target.effects = { haste: 0, slow: 0, ward: 0, vigor: 0 };
        delete target.cast; target.y = 0;
        const memory = this.memory.get(target.id); if (memory) memory.velocityY = 0;
        if (attacker?.kind === 'hero') attacker.kills++;
        for (const [id, time] of this.contributors.get(target.id) ?? []) { const helper = this.actors.get(id); if (helper?.kind === 'hero' && id !== owner && this.time - time <= 8) helper.assists++; }
      } else { this.actors.delete(target.id); this.memory.delete(target.id); }
      this.inputs.delete(target.id); this.contributors.delete(target.id);
      this.emit('defeat', owner, team, target, hero ? `${target.name} defeated` : 'Lane unit defeated', '#f0c975', target.id, sharedAwards ? { amount: hero ? 100 : GOLD_RULES.laneShared, sharedAwards } : {});
    } else if (team !== 'neutral') {
      this.scores[team] += target.kind === 'tower' ? 30 : 100;
      for (const actor of this.actors.values()) if (actor.kind === 'hero' && actor.team === team) actor.credits = Math.min(99999, actor.credits + (target.kind === 'tower' ? 140 : 250));
      this.refreshCoreShields();
      this.emit(target.kind, owner, team, target, `${target.kind} destroyed`, '#ffc67a', target.id);
      if (target.kind === 'core') this.finish(team, 'Enemy core destroyed');
    }
  }
  private shoot(actor: Actor, damage: number, speed: number, radius: number, color: string, pitch = 0, yaw = actor.yaw, life = 2): Projectile | undefined {
    if (this.phase !== 'playing' || this.projectiles.length >= ARENA_RULES.maxProjectiles) return;
    const direction = aim(yaw, pitch);
    const projectile: Projectile = { id: `projectile-${++this.serial}`, owner: actor.id, team: actor.team, x: actor.x + direction.x * .8, z: actor.z + direction.z * .8, y: actor.y + (actor.kind === 'hero' ? 1.2 : .7), vx: direction.x * speed, vy: direction.y * speed, vz: direction.z * speed, damage, radius, life, color };
    this.projectiles.push(projectile);
    this.emit('shot', actor.id, actor.team, actor, '', color);
    return projectile;
  }
  private fire(actor: Actor, pitch = 0): void {
    if (actor.cast || actor.fireCooldown > 0 || actor.health <= 0) return;
    const hero = heroById(actor.heroId), minion = actor.kind === 'minion', siege = actor.minionRole === 'siege';
    const escort = actor.unitArchetype && actor.unitArchetype in ESCORT_STATS ? ESCORT_STATS[actor.unitArchetype as keyof typeof ESCORT_STATS] : undefined;
    const damage = siege ? 12 : minion ? this.memory.get(actor.id)?.attackDamage ?? escort?.damage ?? 13 : hero.damage * (1 + actor.upgrades.power * .17);
    const projectile = this.shoot(actor, damage, siege ? 26 : minion ? escort ? 28 : 25 : hero.projectileSpeed, siege ? .45 : minion ? .24 : .32, hero.color, pitch, actor.yaw, siege ? 1.2 : minion ? escort ? .8 : .6 : 1.7);
    if (siege && projectile) projectile.structureDamage = 32;
    if (!minion && projectile) projectile.canSecureGold = true;
    actor.fireCooldown = siege ? 1.6 : minion ? escort?.interval ?? 1.05 : hero.fireInterval / (1 + actor.upgrades.tempo * .12);
    if (!minion && projectile && this.onPrimaryShot) this.onPrimaryShot(Object.freeze({ actorId: actor.id, projectileId: projectile.id, tick: this.tick, time: this.time }));
  }
  private groundAim(actor: Actor, ability: AbilityDef): Vec {
    const input = this.inputs.get(actor.id)?.value, pitch = input?.pitch ?? 0;
    const horizontal = pitch < -.08 ? Math.min(ability.range, (actor.y + 1.2) / -Math.tan(pitch)) : ability.range;
    const direction = aim(actor.yaw); let point = { x: actor.x, z: actor.z };
    for (let d = .5; d <= horizontal; d += .5) { const next = { x: actor.x + direction.x * d, z: actor.z + direction.z * d }; if (blocked(next.x, next.z, 0)) break; point = next; }
    return point;
  }
  private addZone(actor: Actor, ability: AbilityDef, point: Vec, power = 0, life = .7): void {
    if (this.phase !== 'playing') return;
    if (this.zones.length >= ARENA_RULES.maxZones) this.zones.shift();
    this.zones.push({ id: `zone-${++this.serial}`, owner: actor.id, team: actor.team, kind: ability.kind, x: point.x, z: point.z, yaw: actor.yaw, radius: ability.radius, life, duration: life, power, color: ability.color });
  }
  private cast(actor: Actor, slot: 0 | 1 | 2): void {
    const ability = heroById(actor.heroId).abilities[slot];
    actor.cooldowns[slot] = ability.cooldown;
    const power = ability.power * (1 + actor.upgrades.power * .12), point = this.groundAim(actor, ability);
    const enemies = () => this.validTargets(actor.team);
    this.emit('ability', actor.id, actor.team, actor, ability.name, ability.color);
    if (ability.mechanic) {
      const releaseAt = this.time + (ability.windup ?? .8);
      actor.cast = { slot, mechanic: ability.mechanic, phase: 'windup', startedAt: this.time, releaseAt, endsAt: releaseAt + (ability.mechanic === 'mountain-descent' ? .45 : 0), origin: { x: actor.x, z: actor.z }, target: ability.mechanic === 'mithila-sanctuary' ? { x: actor.x, z: actor.z } : point, yaw: actor.yaw, pitch: this.inputs.get(actor.id)?.value.pitch ?? 0 };
      return;
    }
    switch (ability.kind) {
      case 'bolt': case 'line': this.shoot(actor, power, ability.kind === 'line' ? 62 : 38, ability.kind === 'line' ? .5 : .75, ability.color, this.inputs.get(actor.id)?.value.pitch ?? 0, actor.yaw, Math.max(.3, ability.range / (ability.kind === 'line' ? 62 : 38))); break;
      case 'burst': case 'cone':
        for (const target of enemies()) { const angle = Math.atan2(target.x - actor.x, target.z - actor.z) - actor.yaw; if (distance(actor, target) <= ability.range && Math.cos(angle) > (ability.kind === 'cone' ? .55 : .25) && lineClear(actor, target)) this.damage(target, power, actor.id, actor.team); }
        this.addZone(actor, ability, actor); break;
      case 'nova': for (const target of enemies()) if (distance(actor, target) <= ability.radius && lineClear(actor, target)) this.damage(target, power, actor.id, actor.team); this.addZone(actor, ability, actor); break;
      case 'heal': case 'ward':
        for (const ally of this.actors.values()) if (ally.team === actor.team && ally.health > 0 && distance(actor, ally) <= ability.radius && lineClear(actor, ally)) {
          if (ability.kind === 'heal') ally.health = Math.min(ally.maxHealth, ally.health + power);
          else { ally.shield = Math.max(ally.shield, power); ally.effects.ward = Math.max(ally.effects.ward, ability.duration); }
        }
        this.addZone(actor, ability, actor); break;
      case 'dash': case 'leap': {
        const direction = aim(actor.yaw); this.move(actor, direction.x * ability.range, direction.z * ability.range);
        if (ability.kind === 'leap') this.memory.get(actor.id)!.velocityY = 9;
        this.addZone(actor, ability, actor); break;
      }
      case 'slow': this.addZone(actor, ability, point, power / Math.max(1, ability.duration), Math.max(1, ability.duration)); break;
      case 'pull':
        for (const target of enemies()) if (distance(point, target) <= ability.radius && lineClear(actor, target)) {
          this.damage(target, power, actor.id, actor.team);
          if (('heroId' in target || target.kind === 'neutral') && target.health > 0) { const d = distance(point, target); if (d > .1) this.move(target, (point.x - target.x) / d * Math.min(d, 6), (point.z - target.z) / d * Math.min(d, 6)); }
        }
        this.addZone(actor, ability, point); break;
      case 'summon':
        for (const offset of [-1.3, 1.3]) this.spawnMinion(actor.team, actor.lane, { x: actor.x + offset, z: actor.z }, Math.max(6, ability.duration * 3), power, 'summon', actor.id);
        this.addZone(actor, ability, actor); break;
    }
  }

  private stepCast(actor: Actor): boolean {
    const cast = actor.cast; if (!cast) return false;
    const ability = heroById(actor.heroId).abilities[cast.slot], multiplier = 1 + actor.upgrades.power * .12;
    actor.yaw = cast.yaw;
    if (this.time + 1e-7 < cast.releaseAt) return true;
    if (cast.mechanic === 'mountain-descent') {
      cast.phase = 'travel';
      const progress = clamp((this.time - cast.releaseAt) / .45, 0, 1);
      this.move(actor, cast.origin.x + (cast.target.x - cast.origin.x) * progress - actor.x, cast.origin.z + (cast.target.z - cast.origin.z) * progress - actor.z);
      actor.y = Math.sin(Math.PI * progress) * 5;
      this.memory.get(actor.id)!.velocityY = 0;
      if (this.time + 1e-7 < cast.endsAt) return true;
      actor.y = 0;
      for (const target of this.validTargets(actor.team)) if (distance(actor, target) <= ability.radius && lineClear(actor, target)) this.damage(target, ability.power * multiplier, actor.id, actor.team);
      for (const ally of this.actors.values()) if (ally.team === actor.team && ally.health > 0 && distance(actor, ally) <= ability.radius && lineClear(actor, ally)) ally.health = Math.min(ally.maxHealth, ally.health + 45 * multiplier);
      this.addZone(actor, ability, actor);
    } else if (cast.mechanic === 'dawn-volley') {
      for (const offset of [-.12, 0, .12]) this.shoot(actor, ability.power * multiplier, 62, .5, ability.color, cast.pitch, cast.yaw + offset, ability.range / 62);
    } else {
      for (const ally of this.actors.values()) if (ally.team === actor.team && ally.health > 0 && distance(cast.origin, ally) <= ability.radius && lineClear(cast.origin, ally)) { ally.shield = Math.max(ally.shield, ability.power * multiplier); ally.effects.ward = Math.max(ally.effects.ward, ability.duration); }
      this.addZone(actor, ability, cast.origin, 9 * multiplier, ability.duration);
      const zone = this.zones.at(-1); if (zone?.owner === actor.id && zone.kind === 'ward') zone.mechanic = 'mithila-sanctuary';
    }
    delete actor.cast;
    return true;
  }

  private spawnMinion(team: Team, lane: Lane, point?: Vec, expires?: number, attackDamage?: number, role: 'escort' | 'siege' | 'summon' = 'escort', summonerId?: string, archetype: UnitArchetype = role === 'siege' ? 'king' : role === 'summon' ? 'summon' : 'soldier'): void {
    if (this.actors.size >= ARENA_RULES.maxActors) return;
    const spawn = point ?? { x: SPAWNS[team].x + (lane - 1) * 1.3 + formationOffset(archetype), z: SPAWNS[team].z + (team === 'sun' ? 3 : -3) };
    const candidates = [spawn];
    for (const radius of [1.3, 2.6]) for (let index = 0; index < 8; index++) candidates.push({ x: spawn.x + Math.cos(index * Math.PI / 4) * radius, z: spawn.z + Math.sin(index * Math.PI / 4) * radius });
    const placement = candidates.find(candidate => !this.blockedAt(candidate.x, candidate.z, .42));
    if (!placement) return;
    const actor = this.makeHero(`minion-${++this.serial}`, 'Lane sentinel', team === 'sun' ? HEROES[0]!.id : HEROES[1]!.id, team, true, lane);
    const stats = archetype in ESCORT_STATS ? ESCORT_STATS[archetype as keyof typeof ESCORT_STATS] : undefined;
    Object.assign(actor, { kind: 'minion', minionRole: role, unitArchetype: archetype, name: stats?.name ?? (role === 'siege' ? 'King' : 'Summoned sentinel'), health: stats?.health ?? (role === 'siege' ? 240 : 105), maxHealth: stats?.health ?? (role === 'siege' ? 240 : 105), x: placement.x, z: placement.z, credits: 0 });
    if (summonerId) { actor.summonerId = summonerId; actor.heroId = this.actors.get(summonerId)?.heroId ?? actor.heroId; }
    if (expires) actor.expiresAt = this.time + expires;
    const memory = this.memory.get(actor.id)!; if (expires) memory.expires = this.time + expires; if (attackDamage) memory.attackDamage = attackDamage;
    if (point) memory.waypoint = this.nearestWaypoint(actor);
  }
  private path(actor: Actor): Vec[] {
    // Published lane centerlines cross defensive plinths. A parallel route clears
    // those authoritative circles without cutting across the district buildings.
    const points = LANES[actor.lane].map(point => ({ x: point.x + 4.5 + formationOffset(actor.unitArchetype), z: point.z }));
    return actor.team === 'sun' ? points : [...points].reverse();
  }
  private nearestWaypoint(actor: Actor): number {
    const path = this.path(actor); let nearest = 0;
    for (let i = 1; i < path.length; i++) if (distance(actor, path[i]!) < distance(actor, path[nearest]!)) nearest = i;
    return nearest;
  }
  private botInput(actor: Actor, dt: number): void {
    const memory = this.memory.get(actor.id)!, hero = actor.kind === 'hero', siege = actor.minionRole === 'siege';
    const escort = actor.unitArchetype && actor.unitArchetype in ESCORT_STATS ? ESCORT_STATS[actor.unitArchetype as keyof typeof ESCORT_STATS] : undefined;
    if (actor.unitArchetype === 'minister' && this.time >= (memory.supportAt ?? 0)) {
      const allies = [...this.actors.values()].filter(ally => ally.id !== actor.id && ally.kind === 'minion' && ally.team === actor.team && ally.health > 0 && distance(actor, ally) <= 6 && lineClear(actor, ally)).sort((a, b) => a.health / a.maxHealth - b.health / b.maxHealth || a.id.localeCompare(b.id)).slice(0, 3);
      if (allies.length) { for (const ally of allies) { ally.shield = Math.max(ally.shield, 12); ally.effects.ward = Math.max(ally.effects.ward, 3); } this.emit('ability', actor.id, actor.team, actor, 'Lane rally', '#f4d891'); memory.supportAt = this.time + 5; }
    }
    const range = hero ? 27 : siege ? 22 : escort?.range ?? 11;
    const preference = (target: Target) => siege && (target.kind === 'tower' || target.kind === 'core') ? -40 : target.kind === 'hero' ? -4 : 0;
    const target = this.validTargets(actor.team).filter(value => value.kind !== 'neutral' && distance(actor, value) <= range && lineClear(actor, value)).sort((a, b) => preference(a) + distance(actor, a) - preference(b) - distance(actor, b))[0];
    if (target) {
      actor.yaw = Math.atan2(target.x - actor.x, target.z - actor.z);
      const targetHeight = 'y' in target ? target.y + (target.kind === 'hero' ? 1.1 : .7) : target.kind === 'core' ? 3 : 2.2;
      this.fire(actor, Math.atan2(targetHeight - actor.y - (hero ? 1.2 : .7), Math.max(.1, distance(actor, target))));
      if (hero) {
        const kit = heroById(actor.heroId).abilities;
        for (const slot of [0, 1, 2] as const) {
          const ability = kit[slot];
          const useful = ability.kind === 'heal' || ability.kind === 'ward' ? actor.health < actor.maxHealth * .75 : ['nova', 'cone', 'burst', 'dash', 'leap'].includes(ability.kind) ? distance(actor, target) < Math.max(ability.range, ability.radius) : true;
          if (useful && actor.cooldowns[slot]! <= 0 && this.random() < dt * (slot === 2 ? .25 : .8)) { this.cast(actor, slot); break; }
        }
      }
      if (actor.cast || distance(actor, target) < (hero ? 18 : siege ? 14 : escort?.stop ?? 8)) return;
    }
    const path = this.path(actor);
    if (memory.waypoint >= path.length) memory.waypoint = path.length - 1;
    let destination = path[memory.waypoint]!;
    if (distance(actor, destination) < 3 && memory.waypoint < path.length - 1) destination = path[++memory.waypoint]!;
    const remainingTower = this.structures.find(value => value.team !== actor.team && value.kind === 'tower' && value.lane === actor.lane && value.health > 0);
    if (!remainingTower && memory.waypoint >= path.length - 1) destination = this.structures.find(value => value.team !== actor.team && value.kind === 'core')!;
    const d = distance(actor, destination);
    if (d > .1) {
      const yaw = Math.atan2(destination.x - actor.x, destination.z - actor.z); if (!target) actor.yaw = yaw;
      const speed = (hero ? heroById(actor.heroId).speed : siege ? 3.4 : 4.3) * (actor.effects.haste > 0 ? 1.25 : 1) * (actor.effects.slow > 0 ? .55 : 1);
      this.move(actor, (destination.x - actor.x) / d * speed * dt, (destination.z - actor.z) / d * speed * dt);
    }
  }
  private stepProjectiles(dt: number): void {
    const survivors: Projectile[] = [];
    for (const projectile of this.projectiles) {
      projectile.life -= dt; if (projectile.life <= 0 || this.phase !== 'playing') continue;
      const steps = Math.max(1, Math.ceil(Math.hypot(projectile.vx, projectile.vy, projectile.vz) * dt / .35));
      let hit = false;
      for (let i = 0; i < steps; i++) {
        projectile.x += projectile.vx * dt / steps; projectile.z += projectile.vz * dt / steps; projectile.y += projectile.vy * dt / steps;
        if (Math.abs(projectile.x) > 70 || Math.abs(projectile.z) > 84 || projectile.y < .05 || projectile.y > 35 || SOLIDS.some(solid => projectile.y < solid.height && Math.abs(projectile.x - solid.x) < solid.w / 2 + projectile.radius && Math.abs(projectile.z - solid.z) < solid.d / 2 + projectile.radius)) { hit = true; break; }
        const owner = projectile.canSecureGold ? this.actors.get(projectile.owner) : undefined;
        if (owner?.kind === 'hero' && owner.health > 0) {
          const shard = this.goldShards.find(value => value.expiresAt > this.time && Math.hypot(value.x - projectile.x, value.z - projectile.z, value.y - projectile.y) <= GOLD_RULES.radius + projectile.radius);
          if (shard && this.secureGold(shard, owner)) { hit = true; break; }
        }
        for (const target of this.validTargets(projectile.team)) {
          const height = 'y' in target ? target.y + (target.kind === 'neutral' ? JUNGLE_RULES.bodyHeight : target.kind === 'hero' ? 1.1 : .7) : target.kind === 'core' ? 3 : 2.2;
          const radius = target.kind === 'core' ? 2.8 : target.kind === 'tower' ? 1.8 : target.kind === 'hero' ? .95 : target.kind === 'neutral' ? JUNGLE_RULES.radius : .6;
          if (Math.hypot(target.x - projectile.x, target.z - projectile.z, height - projectile.y) <= radius + projectile.radius) { this.damage(target, (target.kind === 'tower' || target.kind === 'core') ? projectile.structureDamage ?? projectile.damage : projectile.damage, projectile.owner, projectile.team); hit = true; break; }
        }
        if (hit) break;
      }
      if (!hit) survivors.push(projectile);
    }
    this.projectiles = this.phase === 'playing' ? survivors : [];
  }
  private stepTowers(dt: number): void {
    for (const structure of this.structures) {
      if (structure.health <= 0 || this.phase !== 'playing') continue;
      const cooldown = Math.max(0, (this.towerCooldowns.get(structure.id) ?? 0) - dt); this.towerCooldowns.set(structure.id, cooldown);
      if (cooldown > 0) continue;
      const target = [...this.actors.values()].filter(actor => actor.team !== structure.team && actor.health > 0 && distance(actor, structure) <= (structure.kind === 'core' ? 18 : 21) && lineClear(actor, structure)).sort((a, b) => (a.kind === 'minion' ? -20 : 0) + distance(a, structure) - ((b.kind === 'minion' ? -20 : 0) + distance(b, structure)))[0];
      if (!target || this.projectiles.length >= ARENA_RULES.maxProjectiles) continue;
      const height = structure.kind === 'core' ? 3 : 2.2;
      const delta = { x: target.x - structure.x, y: target.y + 1 - height, z: target.z - structure.z }, length = Math.hypot(delta.x, delta.y, delta.z);
      this.projectiles.push({ id: `projectile-${++this.serial}`, owner: structure.id, team: structure.team, x: structure.x, z: structure.z, y: height, vx: delta.x / length * 32, vy: delta.y / length * 32, vz: delta.z / length * 32, damage: structure.kind === 'core' ? 32 : 27, radius: .4, life: 1, color: structure.team === 'sun' ? '#ffbb60' : '#a5a2ff' });
      this.towerCooldowns.set(structure.id, .9);
    }
  }
  private finish(winner: Team | 'draw', reason: string): void {
    if (this.phase === 'finished') return;
    this.phase = 'finished'; this.winner = winner; this.reason = reason; this.projectiles = []; this.zones = []; this.goldShards = []; this.inputs.clear();
    for (const actor of this.actors.values()) { delete actor.cast; actor.y = 0; }
    this.emit('victory', '', winner === 'draw' ? 'sun' : winner, { x: 0, z: 0 }, reason, '#f7db96');
  }

  step(dt: number): void {
    if (this.phase !== 'playing' || !Number.isFinite(dt) || dt <= 0) return;
    dt = Math.min(dt, .1, this.duration - this.time); this.time += dt; this.tick++;
    if (this.time >= this.nextWave) {
      this.nextWave += ARENA_RULES.waveSeconds; this.waveNumber++;
      for (const lane of [0, 1, 2] as const) {
        for (const archetype of ['soldier', 'city-watch', 'minister'] as const) if (ARENA_RULES.maxActors - this.actors.size >= 2) for (const team of ['sun', 'moon'] as const) this.spawnMinion(team, lane, undefined, undefined, undefined, 'escort', undefined, archetype);
        if (this.waveNumber % 3 === 0 && ARENA_RULES.maxActors - this.actors.size >= 2) for (const team of ['sun', 'moon'] as const) this.spawnMinion(team, lane, undefined, undefined, undefined, 'siege');
      }
    }
    for (const actor of [...this.actors.values()]) {
      if (this.phase !== 'playing') break;
      // An earlier actor's area cast can remove a minion from this copied list.
      const memory = this.memory.get(actor.id);
      if (!memory || this.actors.get(actor.id) !== actor) continue;
      if (memory.expires !== undefined && this.time >= memory.expires) { this.actors.delete(actor.id); this.memory.delete(actor.id); continue; }
      actor.cooldowns = actor.cooldowns.map(value => Math.max(0, value - dt)); actor.fireCooldown = Math.max(0, actor.fireCooldown - dt);
      for (const effect of ['haste', 'slow', 'ward'] as const) actor.effects[effect] = Math.max(0, actor.effects[effect] - dt);
      const vigorTime = Math.min(dt, actor.effects.vigor ?? 0); actor.effects.vigor = Math.max(0, (actor.effects.vigor ?? 0) - dt);
      if (actor.health > 0 && vigorTime > 0) actor.health = Math.min(actor.maxHealth, actor.health + 5 * vigorTime);
      if (actor.effects.ward <= 0) actor.shield = 0;
      if (actor.health <= 0) {
        actor.respawn = Math.max(0, actor.respawn - dt);
        if (actor.respawn === 0 && actor.kind === 'hero') { actor.health = actor.maxHealth; actor.x = SPAWNS[actor.team].x + (actor.lane - 1) * 3; actor.z = SPAWNS[actor.team].z + (actor.team === 'sun' ? 3 : -3); actor.y = 0; actor.shield = 60; actor.effects.ward = 3; memory.velocityY = 0; memory.waypoint = 0; }
        continue;
      }
      if (this.stepCast(actor)) continue;
      if (actor.kind === 'hero' && distance(actor, SPAWNS[actor.team]) < 12) actor.health = Math.min(actor.maxHealth, actor.health + 18 * dt);
      if (actor.bot) this.botInput(actor, dt);
      else {
        const stored = this.inputs.get(actor.id), input = stored && this.time - stored.time <= ARENA_RULES.inputExpiry ? stored.value : undefined;
        if (input) {
          actor.yaw = input.yaw; const length = Math.max(1, Math.hypot(input.moveX, input.moveZ));
          const speed = heroById(actor.heroId).speed * (actor.effects.haste > 0 ? 1.25 : 1) * (actor.effects.slow > 0 ? .55 : 1);
          this.move(actor, input.moveX / length * speed * dt, input.moveZ / length * speed * dt);
          if (input.fire) this.fire(actor, input.pitch);
          if (input.jump && !memory.jumping && actor.y <= 0) memory.velocityY = 9;
        }
        memory.jumping = input?.jump ?? false;
      }
      if (actor.y > 0 || memory.velocityY > 0) { memory.velocityY -= 18 * dt; actor.y = Math.max(0, actor.y + memory.velocityY * dt); if (actor.y === 0) memory.velocityY = 0; }
      if (actor.kind === 'hero') for (const pickup of this.pickups) if (pickup.readyAt <= this.time && distance(actor, pickup) < 2) {
        if (pickup.kind === 'vigor') actor.health = Math.min(actor.maxHealth, actor.health + 95);
        else if (pickup.kind === 'haste') actor.effects.haste = Math.max(actor.effects.haste, 9);
        else { actor.shield = Math.max(actor.shield, 85); actor.effects.ward = Math.max(actor.effects.ward, 10); }
        pickup.readyAt = this.time + 24; this.emit('pickup', actor.id, actor.team, pickup, pickup.kind, heroById(actor.heroId).accent);
      }
    }
    for (const zone of this.zones) {
      const activeTime = Math.min(dt, zone.life); zone.life -= dt;
      if (zone.mechanic === 'mithila-sanctuary') for (const ally of this.actors.values()) if (ally.team === zone.team && ally.health > 0 && distance(ally, zone) <= zone.radius && lineClear(zone, ally)) ally.health = Math.min(ally.maxHealth, ally.health + zone.power * activeTime);
      if (zone.kind === 'slow' && zone.life > 0) for (const target of this.validTargets(zone.team)) if (distance(target, zone) <= zone.radius && lineClear(zone, target)) { if ('effects' in target) target.effects.slow = Math.max(target.effects.slow, .5); if (target.kind === 'neutral') target.slow = Math.max(target.slow, .5); this.damage(target, zone.power * dt, zone.owner, zone.team); }
    }
    this.zones = this.zones.filter(zone => zone.life > 0);
    this.stepNeutrals(dt); this.stepTowers(dt); this.stepProjectiles(dt); this.stepGold(); this.refreshCoreShields();
    if (this.time >= this.duration && this.phase === 'playing') {
      const sun = this.structures.find(structure => structure.id === 'sun-core')!, moon = this.structures.find(structure => structure.id === 'moon-core')!;
      const scoreDifference = this.scores.sun - this.scores.moon;
      const winner = scoreDifference ? scoreDifference > 0 ? 'sun' : 'moon' : sun.health !== moon.health ? sun.health > moon.health ? 'sun' : 'moon' : 'draw';
      this.finish(winner, scoreDifference ? 'Time limit · higher team score' : sun.health !== moon.health ? 'Time limit · remaining core health' : 'Time limit · equal score and core health');
    }
  }
  snapshot(): ArenaSnapshot { return copy({ protocol: YUGA_PROTOCOL, room: this.room, seed: this.seed, tick: this.tick, time: this.time, duration: this.duration, phase: this.phase, winner: this.winner, reason: this.reason, actors: [...this.actors.values()], neutrals: this.neutrals, goldShards: this.goldShards, structures: this.structures, projectiles: this.projectiles, zones: this.zones, pickups: this.pickups, events: this.events, scores: this.scores }); }
}
