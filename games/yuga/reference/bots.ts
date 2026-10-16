import { HEROES, heroById } from '../shared/heroes.js';
import { blocked, distance, LANES, lineClear, SPAWNS } from '../shared/map.js';
import { UPGRADE_COSTS } from '../shared/simulation.js';
import type { Actor, ArenaSnapshot, Vec } from '../shared/types.js';
import type { ReferenceCommand, ReferenceExperiment, WeaponSnapshot } from './types.js';

interface BotMemory { waypoint: number; deaths: number; nextAction: number; serial: number }
export interface BotIntent { moveX: number; moveZ: number; yaw: number; pitch: number; fire: boolean; jump: boolean; command?: ReferenceCommand }

/** An original deterministic policy. Bots submit the same intents and commands
 * as the local player; they cannot assign health, position, rewards or cooldowns. */
export class ReferenceBots {
  private readonly memory = new Map<string, BotMemory>();
  constructor(private readonly experiment: ReferenceExperiment, private readonly seed: number) {}

  intent(state: ArenaSnapshot, actor: Actor, weapon: WeaponSnapshot): BotIntent {
    let memory = this.memory.get(actor.id);
    if (!memory) { memory = { waypoint: 0, deaths: actor.deaths, nextAction: 1 + actor.lane * .4, serial: 0 }; this.memory.set(actor.id, memory); }
    if (actor.deaths !== memory.deaths) { memory.deaths = actor.deaths; memory.waypoint = 0; }
    const neutral: BotIntent = { moveX: 0, moveZ: 0, yaw: actor.yaw, pitch: 0, fire: false, jump: false };
    if (actor.health <= 0 || actor.respawn > 0) return neutral;
    const direction = actor.team === 'sun' ? 1 : -1;
    const approachX = actor.lane === 0 ? -6 : 6;
    const controlPath = [{ x: approachX, z: -direction * 48 }, { x: approachX, z: -direction * 18 }, { x: (actor.lane - 1) * 3, z: -direction * 2 }];
    const lanePath = LANES[actor.lane].map(point => ({ x: point.x + 4.5, z: point.z }));
    const path = this.experiment === 'control-point' ? controlPath : actor.team === 'sun' ? lanePath : lanePath.reverse();
    while (memory.waypoint < path.length - 1 && distance(actor, path[memory.waypoint]!) < 2) memory.waypoint++;
    let destination: Vec = path[Math.min(memory.waypoint, path.length - 1)]!;
    const targets = [
      ...state.actors.filter(target => target.team !== actor.team && target.health > 0 && (target.bot || target.connected)),
      ...state.structures.filter(target => target.team !== actor.team && target.health > 0 && !target.shielded),
    ].filter(target => distance(actor, target) < 27 && lineClear(actor, target));
    targets.sort((a, b) => (a.kind === 'hero' ? -4 : 0) + distance(actor, a) - (b.kind === 'hero' ? -4 : 0) - distance(actor, b) || a.id.localeCompare(b.id));
    const target = targets[0];
    if (this.experiment === 'lane-economy' && target && distance(actor, target) < 18) destination = actor;
    if (this.experiment === 'lane-economy' && memory.waypoint === path.length - 1) {
      const core = state.structures.find(value => value.kind === 'core' && value.team !== actor.team && value.health > 0);
      if (core && !target) destination = core;
    }
    const remaining = distance(actor, destination), intent = { ...neutral };
    if (remaining > .65 && !actor.cast) {
      const heading = Math.atan2(destination.x - actor.x, destination.z - actor.z);
      // Short deterministic steering probes use the same solid/structure radii.
      // The authored waypoints keep routes clear of the central defensive plinth.
      for (const offset of [0, .45, -.45, .9, -.9, 1.35, -1.35]) {
        const x = actor.x + Math.sin(heading + offset) * 1.1, z = actor.z + Math.cos(heading + offset) * 1.1;
        if (blocked(x, z, .65) || state.structures.some(s => s.health > 0 && Math.hypot(s.x - x, s.z - z) < .65 + (s.kind === 'core' ? 2.8 : 1.8))) continue;
        intent.moveX = Math.sin(heading + offset); intent.moveZ = Math.cos(heading + offset); break;
      }
      intent.yaw = heading;
    }
    if (target) {
      intent.yaw = Math.atan2(target.x - actor.x, target.z - actor.z);
      const height = 'y' in target ? target.y + (target.kind === 'hero' ? 1.1 : .7) : target.kind === 'core' ? 3 : 2.2;
      intent.pitch = Math.atan2(height - actor.y - 1.2, Math.max(.1, distance(actor, target))); intent.fire = true;
    }
    if (actor.cast || state.time < memory.nextAction) return intent;
    memory.nextAction = state.time + .75;
    const id = `ai-${actor.id}-${++memory.serial}`;
    if (weapon.ammo === 0 && weapon.reloadRemaining === 0) intent.command = { type: 'command', id, action: 'reload' };
    else if (distance(actor, SPAWNS[actor.team]) <= 15) {
      const order = ['power', 'vitality', 'tempo'] as const;
      const upgrade = order.find(key => actor.upgrades[key] < 3 && actor.credits >= UPGRADE_COSTS[key] * (actor.upgrades[key] + 1));
      if (upgrade) intent.command = { type: 'command', id, action: 'upgrade', upgrade };
    } else {
      const hero = heroById(actor.heroId), offset = (Math.floor(state.time) + actor.lane + this.seed) % 3;
      for (let index = 0; index < 3; index++) {
        const slot = (offset + index) % 3 as 0 | 1 | 2, ability = hero.abilities[slot];
        const support = ability.kind === 'heal' || ability.kind === 'ward';
        const useful = support ? state.actors.some(ally => ally.team === actor.team && ally.health > 0 && ally.health < ally.maxHealth * .8 && distance(actor, ally) <= ability.radius) : !!target && distance(actor, target) <= Math.max(ability.range, ability.radius);
        // Keep movement abilities on their authored collision path; no special teleport policy.
        if (useful && actor.cooldowns[slot]! <= 0 && ability.kind !== 'dash' && ability.kind !== 'leap') { intent.command = { type: 'command', id, action: 'ability', slot }; break; }
      }
    }
    return intent;
  }
}

export function referenceBotHero(seed: number, index: number): string { return HEROES[((seed >>> 0) + index * 5) % HEROES.length]!.id; }
