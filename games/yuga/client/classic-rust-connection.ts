import wasmUrl from './assets/classic-roster.wasm?url';
import { heroById } from '../shared/heroes';
import { YUGA_PROTOCOL } from '../shared/types';
import type {
  AbilityMechanic, Actor, ArenaInput, ArenaSnapshot, CastState, GameEvent,
  Projectile, Team, Zone,
} from '../shared/types';
import type { ArenaConnection, Callbacks } from './connection';

const ROOM = 'RUST-SPARRING';
const LOCAL = 'self';
const STEP_MS = 50;
const utf8 = new TextEncoder();
const decoder = new TextDecoder();
type Slot = 0 | 1 | 2;
type Point = [number, number];

interface RustCast {
  slot: Slot; mechanic: AbilityMechanic; phase: CastState['phase']; release: number;
  end: number; origin: Point; target: Point; yaw: number; pitch: number;
}
interface RustActor {
  id: string; kind: Actor['kind']; hero: string; team: Team; pos: Point; y: number; yaw: number;
  hp: number; max_hp: number; shield: number; ward: number; slow: number; fire_cd: number;
  cds: number[]; respawn: number; deaths: number; expires_at: number | null; cast: RustCast | null;
}
interface RustShot extends Omit<Projectile, 'id' | 'color' | 'team'> {
  id: number; team: Team; slot?: Slot | null;
}
interface RustZone extends Omit<Zone, 'id' | 'color' | 'mechanic'> {
  id: number; slot: Slot; mechanic?: AbilityMechanic | null;
}
interface RustEvent {
  id: number; kind: 'shot' | 'hit' | 'defeat' | 'ability'; actor: string; team: Team; target?: string | null;
  slot?: Slot | null; amount?: number | null; x: number; z: number; time: number;
}
interface RustState {
  tick: number; time: number; units: RustActor[]; projectiles: RustShot[]; zones: RustZone[];
  events: RustEvent[]; accepted: boolean | null;
}
interface Engine {
  memory: WebAssembly.Memory;
  roster_input_ptr(): number; roster_input_capacity(): number;
  roster_reset(length: number): number; roster_command(length: number): number;
  roster_snapshot_ptr(): number; roster_snapshot_len(): number;
  roster_error_ptr(): number; roster_error_len(): number;
}
async function loadEngine(signal?: AbortSignal) {
  const response = await fetch(wasmUrl, { signal });
  if (!response.ok) throw new Error(`Could not load the Rust sparring engine (HTTP ${response.status})`);
  const { instance } = await WebAssembly.instantiate(await response.arrayBuffer(), {});
  signal?.throwIfAborted();
  const engine = instance.exports as unknown as Engine;
  function read(pointer: number, length: number) {
    return decoder.decode(new Uint8Array(engine.memory.buffer, pointer, length));
  }
  return (op: 'roster_reset' | 'roster_command', text: string): RustState => {
    const bytes = utf8.encode(text);
    if (bytes.length > engine.roster_input_capacity()) throw new Error('Rust sparring input exceeds its buffer');
    new Uint8Array(engine.memory.buffer, engine.roster_input_ptr(), bytes.length).set(bytes);
    if (!engine[op](bytes.length)) throw new Error(read(engine.roster_error_ptr(), engine.roster_error_len()));
    // The allocator can grow linear memory during reset and simulation.
    return JSON.parse(read(engine.roster_snapshot_ptr(), engine.roster_snapshot_len())) as RustState;
  };
}

function actorView(unit: RustActor, name: string, seq: number, kills: number, dealt: number): Actor {
  const hero = heroById(unit.hero);
  const c = unit.cast;
  return {
    id: unit.id, kind: unit.kind, team: unit.team, heroId: unit.hero,
    name: unit.id === LOCAL ? name : unit.kind === 'minion' ? 'Summoned sentinel' : hero.name,
    bot: unit.id !== LOCAL, connected: unit.id === LOCAL, lane: 1, x: unit.pos[0], z: unit.pos[1],
    y: unit.y, yaw: unit.yaw, health: unit.hp, maxHealth: unit.max_hp, shield: unit.shield,
    respawn: unit.respawn, cooldowns: unit.cds, fireCooldown: unit.fire_cd,
    effects: { haste: 0, ward: unit.ward, slow: unit.slow },
    kills, deaths: unit.deaths, assists: 0, damageDealt: dealt, credits: 0, level: 1,
    upgrades: { power: 0, vitality: 0, tempo: 0 }, lastInputSeq: unit.id === LOCAL ? seq : 0,
    ...(c ? { cast: {
      slot: c.slot, mechanic: c.mechanic, phase: c.phase, yaw: c.yaw, pitch: c.pitch,
      startedAt: c.release - (hero.abilities[c.slot].windup ?? .8), releaseAt: c.release, endsAt: c.end,
      origin: { x: c.origin[0], z: c.origin[1] }, target: { x: c.target[0], z: c.target[1] },
    } } : {}),
    ...(unit.kind === 'minion' ? { unitArchetype: 'summon', minionRole: 'summon', expiresAt: unit.expires_at ?? undefined } : {}),
  };
}

class Presentation {
  private lastReceipt = 0;
  private stats = new Map<string, { kills: number; damage: number }>();

  snapshot(state: RustState, name: string, seq: number): ArenaSnapshot {
    const sources = new Map(state.units.map(unit => [unit.id, unit]));
    const palette = (team: Team) => team === 'sun' ? '#ffcf79' : '#a5dfef';
    function color(owner: string, team: Team, slot?: Slot | null) {
      const unit = sources.get(owner);
      if (!unit) return palette(team);
      const hero = heroById(unit.hero);
      return slot == null ? hero.accent : hero.abilities[slot].color;
    }

    const events: GameEvent[] = [];
    for (const e of state.events) {
      const source = sources.get(e.actor), target = e.target ? sources.get(e.target) : undefined;
      if (e.id > this.lastReceipt) {
        if (source?.kind === 'hero') {
          const tally = this.stats.get(e.actor) ?? { kills: 0, damage: 0 };
          if (e.kind === 'hit') tally.damage += e.amount ?? 0;
          if (e.kind === 'defeat' && target?.kind === 'hero') tally.kills++;
          this.stats.set(e.actor, tally);
        }
        this.lastReceipt = e.id;
      }
      // A heal/ward can touch several allies. Only the activation starts the rig and its cue.
      // Per-target health and shield outcomes are already authoritative actor fields.
      if (e.kind === 'ability' && e.target) continue;
      const hero = source ? heroById(source.hero) : undefined;
      const ability = e.slot != null ? hero?.abilities[e.slot] : undefined;
      const label = e.kind === 'ability' ? ability?.name ?? 'Ability'
        : e.kind === 'defeat' ? `${hero?.name ?? 'Sentinel'} defeated ${target ? heroById(target.hero).name : 'a target'}`
        : e.kind === 'shot' ? 'Primary fire' : 'Hit';
      events.push({ id: e.id, type: e.kind, actorId: e.actor, targetId: e.target ?? undefined, amount: e.amount ?? undefined,
        team: e.team, x: e.x, z: e.z, time: e.time, label, color: color(e.actor, e.team, e.slot) });
    }

    const actors = state.units.map(unit => {
      const tally = this.stats.get(unit.id);
      return actorView(unit, name, seq, tally?.kills ?? 0, tally?.damage ?? 0);
    });
    const scores = { sun: 0, moon: 0 };
    for (const actor of actors) if (actor.kind === 'hero') scores[actor.team === 'sun' ? 'moon' : 'sun'] += actor.deaths;
    return {
      protocol: YUGA_PROTOCOL, room: ROOM, tick: state.tick, time: state.time, duration: 0, phase: 'playing',
      winner: null, reason: '', scores, seed: 0, actors, events,
      projectiles: state.projectiles.map(p => ({ ...p, id: String(p.id), color: color(p.owner, p.team, p.slot) })),
      zones: state.zones.map(z => ({ ...z, id: String(z.id), mechanic: z.mechanic ?? undefined, color: color(z.owner, z.team, z.slot) })),
      neutrals: [], goldShards: [], structures: [], pickups: [],
    };
  }
}

export async function classicRustPractice(heroId: string, name: string, callbacks: Callbacks, initiallyPaused = false, signal?: AbortSignal): Promise<ArenaConnection> {
  const execute = await loadEngine(signal);
  signal?.throwIfAborted();
  let state = execute('roster_reset', heroId);
  const view = new Presentation();
  let paused = initiallyPaused, closed = false, timer: number | undefined;
  let last = performance.now(), carry = 0, seq = 0, pressedJump = false, pressedFire = false;
  let input: ArenaInput = { type: 'input', seq: 0, moveX: 0, moveZ: 0, yaw: 0, pitch: 0, fire: false, jump: false };
  const publish = () => callbacks.snapshot(view.snapshot(state, name, seq));
  function close() {
    closed = true;
    window.clearInterval(timer);
    signal?.removeEventListener('abort', close);
  }
  function advance() {
    const now = performance.now();
    carry = Math.min(1000, carry + Math.max(0, now - last));
    last = now;
    if (closed || paused) { carry = 0; return; }
    const ticks = Math.floor(carry / STEP_MS);
    if (!ticks) return;
    carry -= ticks * STEP_MS;
    const command = { ticks, movement: [input.moveX, input.moveZ], yaw: input.yaw, pitch: input.pitch, fire: input.fire, jump: input.jump };
    if ((pressedJump && !input.jump) || (pressedFire && !input.fire)) {
      // Preserve a complete down/up between steps without repeating the transient on catch-up ticks.
      state = execute('roster_command', JSON.stringify({ ...command, ticks: 1, jump: pressedJump || input.jump, fire: pressedFire || input.fire }));
      command.ticks--;
    }
    if (command.ticks) state = execute('roster_command', JSON.stringify(command));
    seq = input.seq;
    pressedJump = pressedFire = false;
    publish();
  }
  function stopWithError(error: unknown) {
    close();
    callbacks.status('Rust sparring stopped', false);
    callbacks.error(error instanceof Error ? error.message : 'Sparring engine stopped');
  }
  function guardedAdvance() {
    if (closed) return;
    try { advance(); }
    catch (error) { stopWithError(error); }
  }
  signal?.addEventListener('abort', close, { once: true });
  try {
    callbacks.welcome(LOCAL, ROOM, false);
    callbacks.status('Rust sparring · Sangam City', true);
    publish();
    signal?.throwIfAborted();
    timer = window.setInterval(guardedAdvance, STEP_MS);
  } catch (error) {
    close();
    throw error;
  }
  return {
    input(next) {
      if (paused || closed || next.seq <= input.seq) return;
      guardedAdvance();
      pressedJump ||= next.jump && !input.jump;
      pressedFire ||= next.fire && !input.fire;
      input = next;
    },
    command(cmd) {
      if (closed) return;
      if (cmd.action !== 'ability' || paused) {
        callbacks.result({ type: 'result', id: cmd.id, ok: false, code: paused ? 'SPARRING_PAUSED' : 'NO_FORGE_IN_SPARRING' });
        return;
      }
      guardedAdvance();
      if (closed) return;
      try {
        state = execute('roster_command', JSON.stringify({ cast: cmd.slot, yaw: input.yaw, pitch: input.pitch }));
      } catch (error) {
        callbacks.result({ type: 'result', id: cmd.id, ok: false, code: 'SPARRING_ENGINE_STOPPED' });
        stopWithError(error);
        return;
      }
      const self = state.units.find(u => u.id === LOCAL)!;
      const ok = state.accepted === true;
      callbacks.result({ type: 'result', id: cmd.id, ok, code: ok ? 'OK' : self.hp <= 0 ? 'RESPAWNING' : self.cast ? 'CAST_IN_PROGRESS' : 'ABILITY_COOLDOWN' });
      publish();
    },
    pause(next) {
      if (closed || next === paused) return;
      guardedAdvance();
      paused = next;
      pressedJump = pressedFire = false;
      input = { ...input, moveX: 0, moveZ: 0, jump: false, fire: false };
      carry = 0; last = performance.now();
    },
    close,
  };
}
