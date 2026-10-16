import { ARENA, SOLIDS } from '../shared/map.js';
import type { Actor, ArenaSnapshot, Neutral, Structure, Team } from '../shared/types.js';

type Target = Actor | Structure | Neutral;
type Point = { x: number; y: number; z: number };
export interface TargetAim extends Point { yaw: number; pitch: number; label: string }
const RANGE = 32, CONE_COS = Math.cos(20 * Math.PI / 180), EPSILON = 1e-9;
const SHOT_RADIUS = .32;
const finite = (...values: number[]) => values.every(Number.isFinite);

function shooter(snapshot: ArenaSnapshot, playerId: string): Actor | undefined {
  if (snapshot.phase !== 'playing') return;
  const actor = snapshot.actors.find(candidate => candidate.id === playerId);
  if (actor?.kind !== 'hero' || !actor.connected || actor.bot || actor.health <= 0 || actor.respawn > 0 || !finite(actor.x, actor.y, actor.z, actor.health, actor.respawn)) return;
  return actor;
}

function eligible(target: Target, team: Team): boolean {
  if (target.team === team || target.health <= 0 || !finite(target.x, target.z, target.health)) return false;
  if (target.kind === 'neutral') return target.state !== 'dead' && target.state !== 'returning' && finite(target.y);
  if ('heroId' in target) return finite(target.y, target.respawn) && target.respawn <= 0 && (target.connected || target.bot);
  return !target.shielded;
}

function center(target: Target): Point {
  return { x: target.x, z: target.z, y: 'y' in target ? target.y + (target.kind === 'minion' ? .7 : 1.1) : target.kind === 'tower' ? 2.2 : 3 };
}

/** Slab intersection includes building height and a basic projectile's width. */
function boxBlocks(origin: Point, end: Point, min: Point, max: Point): boolean {
  let enter = 0, leave = 1;
  for (const axis of ['x', 'y', 'z'] as const) {
    const delta = end[axis] - origin[axis];
    if (Math.abs(delta) < EPSILON) { if (origin[axis] < min[axis] || origin[axis] > max[axis]) return false; continue; }
    const first = (min[axis] - origin[axis]) / delta, second = (max[axis] - origin[axis]) / delta;
    enter = Math.max(enter, Math.min(first, second)); leave = Math.min(leave, Math.max(first, second));
    if (enter > leave) return false;
  }
  return leave >= 0 && enter <= 1;
}

/** Live enemy plinths occlude the ray; friendly shots pass through allied structures. */
function structureBlocks(origin: Point, end: Point, structure: Structure): boolean {
  const radius = (structure.kind === 'tower' ? 1.8 : 2.8) + SHOT_RADIUS, height = structure.kind === 'tower' ? 4.5 : 6.5;
  const dx = end.x - origin.x, dz = end.z - origin.z, ox = origin.x - structure.x, oz = origin.z - structure.z;
  const a = dx * dx + dz * dz, b = 2 * (ox * dx + oz * dz), c = ox * ox + oz * oz - radius * radius;
  let enter = 0, leave = 1;
  if (a < EPSILON) { if (c > 0) return false; }
  else {
    const discriminant = b * b - 4 * a * c; if (discriminant < 0) return false;
    const root = Math.sqrt(discriminant);
    enter = Math.max(enter, (-b - root) / (2 * a)); leave = Math.min(leave, (-b + root) / (2 * a));
  }
  const dy = end.y - origin.y;
  if (Math.abs(dy) < EPSILON) { if (origin.y < 0 || origin.y > height) return false; }
  else { const first = -origin.y / dy, second = (height - origin.y) / dy; enter = Math.max(enter, Math.min(first, second)); leave = Math.min(leave, Math.max(first, second)); }
  return enter <= leave && leave >= 0 && enter <= 1;
}

function visible(snapshot: ArenaSnapshot, actor: Actor, target: Target, origin: Point, end: Point): boolean {
  for (const solid of SOLIDS) if (boxBlocks(origin, end,
    { x: solid.x - solid.w / 2 - SHOT_RADIUS, y: 0, z: solid.z - solid.d / 2 - SHOT_RADIUS },
    { x: solid.x + solid.w / 2 + SHOT_RADIUS, y: solid.height, z: solid.z + solid.d / 2 + SHOT_RADIUS })) return false;
  return !snapshot.structures.some(structure => structure.id !== target.id && structure.team !== actor.team && structure.health > 0 && finite(structure.x, structure.z, structure.health) && structureBlocks(origin, end, structure));
}

function solution(snapshot: ArenaSnapshot, actor: Actor, target: Target): (TargetAim & { distance: number }) | null {
  if (!eligible(target, actor.team)) return null;
  const origin = { x: actor.x, y: actor.y + 1.2, z: actor.z }, point = center(target);
  const dx = point.x - origin.x, dy = point.y - origin.y, dz = point.z - origin.z, distance = Math.hypot(dx, dy, dz);
  if (!Number.isFinite(distance) || distance < EPSILON || distance > RANGE + EPSILON || !visible(snapshot, actor, target, origin, point)) return null;
  const label = target.kind === 'neutral' ? target.name : 'heroId' in target ? target.kind === 'hero' || target.unitArchetype ? target.name : target.minionRole === 'siege' ? 'Siege sentinel' : target.minionRole === 'summon' ? 'Summoned sentinel' : 'Lane sentinel' : target.kind === 'core' ? 'Enemy core' : `${ARENA.lanes[target.lane]} tower`;
  return { ...point, yaw: Math.atan2(dx, dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)), label, distance };
}

/** Client aim assistance only. Never modifies the snapshot or authorizes a hit. */
export function acquireTarget(snapshot: ArenaSnapshot, playerId: string, yaw: number, pitch: number): string | null {
  if (!finite(yaw, pitch) || Math.abs(pitch) > Math.PI / 2) return null;
  const actor = shooter(snapshot, playerId); if (!actor) return null;
  const forward = { x: Math.sin(yaw) * Math.cos(pitch), y: Math.sin(pitch), z: Math.cos(yaw) * Math.cos(pitch) };
  let best: { id: string; error: number; hero: boolean; distance: number } | undefined;
  for (const target of [...snapshot.actors, ...snapshot.structures, ...snapshot.neutrals]) {
    const aim = solution(snapshot, actor, target); if (!aim) continue;
    const dot = (forward.x * (aim.x - actor.x) + forward.y * (aim.y - actor.y - 1.2) + forward.z * (aim.z - actor.z)) / aim.distance;
    if (dot + EPSILON < CONE_COS) continue;
    const candidate = { id: target.id, error: 1 - dot, hero: target.kind === 'hero', distance: aim.distance };
    if (!best || candidate.error < best.error - EPSILON || Math.abs(candidate.error - best.error) <= EPSILON && (Number(candidate.hero) > Number(best.hero) || candidate.hero === best.hero && (candidate.distance < best.distance - EPSILON || Math.abs(candidate.distance - best.distance) <= EPSILON && candidate.id < best.id))) best = candidate;
  }
  return best?.id ?? null;
}

/** Revalidates an existing lock every frame; the acquisition cone does not restrict retention. */
export function targetAim(snapshot: ArenaSnapshot, playerId: string, targetId: string): TargetAim | null {
  const actor = shooter(snapshot, playerId); if (!actor) return null;
  const target = snapshot.actors.find(candidate => candidate.id === targetId) ?? snapshot.structures.find(candidate => candidate.id === targetId) ?? snapshot.neutrals.find(candidate => candidate.id === targetId);
  if (!target) return null;
  const aim = solution(snapshot, actor, target); if (!aim) return null;
  return { yaw: aim.yaw, pitch: aim.pitch, x: aim.x, y: aim.y, z: aim.z, label: aim.label };
}
