import * as pc from 'playcanvas';
import { GOLD_RULES, JUNGLE_CAMPS, JUNGLE_RULES, NEUTRAL_STATS } from '../shared/map';
import type { ArenaSnapshot, BuffKind, Neutral } from '../shared/types';
import { RenderKit, clamp, mixAngle, RAD } from './render-kit';
import { UnitModelLibrary, type UnitModel } from './unit-models';

interface CampView { root: pc.Entity; boundary: pc.Entity; progress: pc.Entity; label: pc.Entity; danger: pc.Entity; returning: pc.Entity }
interface NeutralView { root: pc.Entity; model: UnitModel | null; marker: pc.Entity; frame: pc.Entity; health: pc.Entity; x: number; z: number; yaw: number; wasAlive: boolean; deathAt: number; shot: number; speed: number }
interface GoldView { root: pc.Entity; crystal: pc.Entity; remaining: pc.Entity; ready: pc.Entity }
interface Options { yaw: number; reducedMotion: boolean; quality: 'low' | 'high'; elapsed: number }

/** Flat camp artwork and server-owned units/rewards; this view introduces no collision geometry. */
export class JungleView {
  private readonly camps = new Map<string, CampView>();
  private readonly neutrals = new Map<string, NeutralView>();
  private readonly gold = new Map<string, GoldView>();
  private readonly goldPool: GoldView[] = [];
  private readonly buffs = new Map<string, pc.Entity>();
  private eventId = -1;
  private needsBaseline = true;
  private latest: ArenaSnapshot | null = null;
  constructor(private readonly kit: RenderKit, private readonly parent: pc.Entity, private readonly models: UnitModelLibrary) {
    for (const camp of JUNGLE_CAMPS) this.camps.set(camp.id, this.buildCamp(camp));
  }
  private group(name: string, parent = this.parent) { const node = new pc.Entity(name, this.kit.app); parent.addChild(node); return node; }
  private dashedBoundary(parent: pc.Entity, material: pc.Material) {
    const positions: number[] = [], normals: number[] = [], indices: number[] = [];
    for (let dash = 0; dash < 24; dash++) {
      const offset = positions.length / 3;
      for (let step = 0; step <= 3; step++) {
        const angle = dash / 24 * Math.PI * 2 + step / 3 * .11;
        for (const radius of [JUNGLE_RULES.aggro - .025, JUNGLE_RULES.aggro + .025]) { positions.push(Math.sin(angle) * radius, .042, Math.cos(angle) * radius); normals.push(0, 1, 0); }
        if (step < 3) { const n = offset + step * 2; indices.push(n, n + 1, n + 2, n + 1, n + 3, n + 2); }
      }
    }
    parent.addComponent('render', { meshInstances: [new pc.MeshInstance(pc.createMesh(this.kit.app.graphicsDevice, positions, { normals, indices }), material)], castShadows: false });
  }
  private glyph(root: pc.Entity, kind: BuffKind, material: pc.Material, radius = 1) {
    if (kind === 'ward') {
      this.kit.ring(root, material, radius, .055, .05, 6);
      this.kit.ring(root, material, radius * .7, .025, .055, 6);
    } else if (kind === 'vigor') {
      for (const side of [-1, 1]) this.kit.shape(root, 'sphere', material, side * radius * .28, .06, 0, radius * .42, .025, radius * .9).setLocalEulerAngles(0, side * 35, 0);
      this.kit.shape(root, 'box', material, 0, .06, -.3 * radius, .035, .025, radius * .7);
    } else {
      for (const z of [-.2, .2]) for (const side of [-1, 1]) this.kit.shape(root, 'box', material, side * radius * .23, .06, z * radius, .06, .025, radius * .6).setLocalEulerAngles(0, side * 38, 0);
    }
  }
  private buildCamp(camp: typeof JUNGLE_CAMPS[number]): CampView {
    const root = this.group(`neutral court ${camp.id}`); root.setPosition(camp.x, 0, camp.z);
    const stats = NEUTRAL_STATS[camp.species];
    const accent = this.kit.material(`camp ${camp.species}`, stats.color, .25);
    const stone = this.kit.material(`camp ${camp.x < 0 ? 'carved sandstone' : 'metro mosaic'}`, camp.x < 0 ? '#b79a75' : '#648c8a', 0, .4);
    if (!stone.diffuseMap) {
      const texture = this.kit.texture(`original ${camp.x < 0 ? 'carved court' : 'metro court'} tile`, 256, 256, ctx => {
        ctx.fillStyle = camp.x < 0 ? '#cbb798' : '#a8c6be'; ctx.fillRect(0, 0, 256, 256);
        ctx.strokeStyle = camp.x < 0 ? '#967c59' : '#56817e'; ctx.lineWidth = 2;
        for (let row = 0; row < 8; row++) for (let col = -1; col < 9; col++) ctx.strokeRect(col * 32 + row % 2 * 16, row * 32, 32, 32);
        ctx.strokeStyle = '#e7d9b0'; ctx.lineWidth = 4; ctx.strokeRect(9, 9, 238, 238);
        for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.arc(128, 128, 28 + i * 23, 0, Math.PI * 2); ctx.stroke(); }
      });
      stone.diffuseMap = texture; stone.update();
    }
    // A shallow mosaic is visibly walkable. Tall props stay in the existing city solids.
    this.kit.shape(root, 'plane', stone, 0, .035, 0, 9.6, 1, 9.6, true);
    this.kit.ring(root, accent, 4.5, .12, .045, 40, true);
    const crest = this.group('neutral diamond court seal', root); crest.setLocalEulerAngles(0, 45, 0);
    this.kit.ring(crest, accent, 1.2, .08, .06, 4, true);
    this.glyph(root, stats.buff, accent, .8);
    const boundary = this.group('exact camp aggro boundary', root);
    const muted = this.kit.material('neutral territory ivory', '#d8cfae', .1);
    this.dashedBoundary(boundary, muted);
    const danger = this.group('camp engaged warning', root), warning = this.kit.material('neutral aggro coral', '#ff9673', .7);
    // Triangular danger teeth and diamond identity survive team-colour ambiguity.
    for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; this.kit.shape(danger, 'cone', warning, Math.sin(a) * 4.65, .075, Math.cos(a) * 4.65, .26, .5, .025).setLocalEulerAngles(90, a * RAD, 0); }
    const returning = this.group('neutral disengaging inward marks', root);
    for (const side of [-1, 1]) this.kit.shape(returning, 'cone', accent, side * 2, .08, 0, .35, .7, .025).setLocalEulerAngles(90, side * 90, 0);
    const progress = this.kit.ring(root, accent, 1.65, .065, .07, 32);
    const label = this.group('neutral court label', root); label.setLocalPosition(0, 2.9, 0);
    const texture = this.kit.texture(`label ${camp.id}`, 512, 128, ctx => {
      ctx.fillStyle = '#112b32e8'; ctx.fillRect(0, 0, 512, 128); ctx.strokeStyle = stats.color; ctx.lineWidth = 4; ctx.strokeRect(3, 3, 506, 122);
      ctx.textAlign = 'center'; ctx.fillStyle = '#fff2d0'; ctx.font = '600 34px sans-serif'; ctx.fillText(stats.name.toUpperCase(), 256, 50);
      ctx.fillStyle = stats.color; ctx.font = '22px sans-serif'; ctx.fillText(`NEUTRAL  ·  ${stats.buff.toUpperCase()}`, 256, 94);
    });
    const textMaterial = this.kit.material(`label ${camp.id}`, '#ffffff', .2); textMaterial.diffuseMap = texture; textMaterial.emissiveMap = texture; textMaterial.update();
    this.kit.shape(label, 'plane', textMaterial, 0, 0, 0, 3.5, 1, .875).setLocalEulerAngles(90, 180, 0);
    danger.enabled = false; returning.enabled = false;
    return { root, boundary, progress, label, danger, returning };
  }
  private makeNeutral(n: Neutral): NeutralView {
    const root = this.group(`neutral ${n.id}`), accent = this.kit.material(`neutral body marker ${n.species}`, NEUTRAL_STATS[n.species].color, .4);
    const model = this.models.instantiate(n.species, n.id, root);
    const marker = this.kit.ring(root, accent, .95, .075, .055, 4); marker.setLocalEulerAngles(0, 45, 0);
    const frame = this.group('neutral health', root); frame.setLocalPosition(0, 2.35, 0);
    this.kit.shape(frame, 'box', this.kit.material('neutral health backing', '#153237'), 0, 0, 0, 1.4, .09, .03);
    const health = this.kit.shape(frame, 'box', accent, 0, 0, .025, 1.3, .055, .02);
    return { root, model, marker, frame, health, x: n.x, z: n.z, yaw: n.yaw, wasAlive: n.health > 0, deathAt: -10, shot: 0, speed: 0 };
  }
  private makeGold(): GoldView {
    const root = this.group('contestable gold shard'), metal = this.kit.material('contestable gold crystal', '#ffd66d', .8, .7);
    const crystal = this.kit.shape(root, 'box', metal, 0, 0, 0, .34, .64, .34); crystal.setLocalEulerAngles(25, 45, 20);
    const pale = this.kit.material('gold expiry ivory', '#fff3c7', .55);
    this.kit.ring(root, pale, GOLD_RULES.radius, .035, -GOLD_RULES.height + .065, 16);
    const ready = this.kit.ring(root, metal, .5, .045, -GOLD_RULES.height + .07, 4);
    const remaining = this.kit.shape(root, 'box', pale, 0, -.55, 0, .65, .04, .04);
    return { root, crystal, remaining, ready };
  }
  update(snapshot: ArenaSnapshot, localId: string | null, dt: number, options: Options) {
    this.latest = snapshot;
    if (this.needsBaseline) { this.eventId = snapshot.events.at(-1)?.id ?? -1; this.needsBaseline = false; }
    const local = snapshot.actors.find(a => a.id === localId);
    for (const event of snapshot.events) {
      if (event.id <= this.eventId) continue; this.eventId = event.id;
      if (snapshot.time - event.time > 2) continue;
      if (event.type === 'shot') { const view = this.neutrals.get(event.actorId); if (view) view.shot = event.id; }
    }
    const live = new Set(snapshot.neutrals.map(n => n.id));
    for (const [id, v] of this.neutrals) if (!live.has(id)) { v.model?.destroy(); v.root.destroy(); this.neutrals.delete(id); }
    for (const n of snapshot.neutrals) {
      let v = this.neutrals.get(n.id); if (!v) { v = this.makeNeutral(n); this.neutrals.set(n.id, v); }
      if (!v.model) v.model = this.models.instantiate(n.species, n.id, v.root);
      const alive = n.health > 0 && n.state !== 'dead';
      if (alive !== v.wasAlive) { if (!alive) v.deathAt = options.elapsed; else { v.x = n.x; v.z = n.z; } v.wasAlive = alive; }
      v.root.enabled = alive || options.elapsed - v.deathAt < 1.1;
      const dx = n.x - v.x, dz = n.z - v.z, blend = Math.hypot(dx, dz) > 8 ? 1 : 1 - Math.exp(-16 * dt);
      v.x += dx * blend; v.z += dz * blend; v.yaw = mixAngle(v.yaw, n.yaw, 1 - Math.exp(-18 * dt));
      const speed = dt ? Math.min(9, Math.hypot(dx, dz) * blend / dt) : 0; v.speed += (speed - v.speed) * (1 - Math.exp(-12 * dt));
      v.root.setPosition(v.x, n.y, v.z); v.root.setEulerAngles(0, v.yaw * RAD, 0);
      v.frame.setEulerAngles(0, options.yaw * RAD + 180, 0); v.frame.enabled = alive; v.marker.enabled = alive;
      const ratio = clamp(n.health / n.maxHealth, 0, 1); v.health.setLocalScale(Math.max(.001, ratio) * 1.3, .055, .02); v.health.setLocalPosition((ratio - 1) * .65, 0, .025);
      if (v.model) {
        v.model.setShadows(options.quality === 'high');
        v.model.setAnimated(v.root.enabled && (!local || Math.hypot(local.x - n.x, local.z - n.z) < 45 || n.state === 'aggro'));
        v.model.update({ speed: v.speed, alive, airborne: false, shot: v.shot, cast: 0, castSlot: 0, casting: false, reducedMotion: options.reducedMotion }, dt);
      }
      const camp = this.camps.get(n.campId);
      if (camp) {
        const nearby = !local || Math.hypot(local.x - camp.root.getPosition().x, local.z - camp.root.getPosition().z) < 29;
        camp.boundary.enabled = nearby && alive; camp.label.enabled = nearby; camp.label.setEulerAngles(0, options.yaw * RAD, 0);
        camp.danger.enabled = n.state === 'aggro'; camp.returning.enabled = n.state === 'returning';
        camp.progress.enabled = !alive;
        const duration = n.respawnAt <= JUNGLE_RULES.firstSpawn ? JUNGLE_RULES.firstSpawn : JUNGLE_RULES.respawn;
        const fraction = clamp(1 - (n.respawnAt - snapshot.time) / duration, 0, 1), size = .12 + .88 * fraction;
        camp.progress.setLocalScale(size, 1, size);
      }
    }
    const goldIds = new Set(snapshot.goldShards.map(g => g.id));
    for (const [id, v] of this.gold) if (!goldIds.has(id)) { v.root.enabled = false; this.gold.delete(id); this.goldPool.push(v); }
    for (const shard of snapshot.goldShards) {
      let v = this.gold.get(shard.id); if (!v) { v = this.goldPool.pop() ?? this.makeGold(); v.root.enabled = true; this.gold.set(shard.id, v); }
      v.root.setPosition(shard.x, shard.y, shard.z);
      v.crystal.setLocalPosition(0, options.reducedMotion ? 0 : Math.sin(options.elapsed * 2.5 + shard.x) * .07, 0);
      if (!options.reducedMotion) v.crystal.setLocalEulerAngles(25, options.elapsed * 35, 20);
      const fraction = clamp((shard.expiresAt - snapshot.time) / Math.max(.1, shard.expiresAt - shard.createdAt), 0, 1);
      v.remaining.setLocalScale(.65 * fraction, .04, .04); v.remaining.setEulerAngles(0, options.yaw * RAD, 0);
      // The footprint becomes solid after the shared walking-pickup delay; shots can secure immediately.
      v.ready.enabled = snapshot.time >= shard.createdAt + GOLD_RULES.pickupDelay;
    }
    const buffIds = new Set<string>();
    for (const actor of snapshot.actors) if (actor.kind === 'hero' && actor.health > 0) for (const buff of ['ward', 'vigor', 'haste'] as const) {
      const seconds = actor.effects[buff] ?? 0; if (seconds <= 0) continue;
      const id = `${actor.id}/${buff}`; buffIds.add(id); let v = this.buffs.get(id);
      if (!v) { v = this.group(`active ${buff} aura`); this.glyph(v, buff, this.kit.material(`buff ${buff}`, buff === 'ward' ? '#8de6d4' : buff === 'vigor' ? '#b9e69e' : '#d4b5ff', .6), .85); this.buffs.set(id, v); }
      v.setPosition(actor.x, actor.y + .04, actor.z); v.setEulerAngles(0, actor.yaw * RAD, 0);
      const strength = .65 + .35 * Math.min(1, seconds / 2); v.setLocalScale(strength, 1, strength);
    }
    for (const [id, v] of this.buffs) if (!buffIds.has(id)) { v.destroy(); this.buffs.delete(id); }
  }
  diagnostics() {
    return {
      camps: this.latest?.neutrals.map(n => ({ id: n.campId, species: n.species, state: n.state, respawnAt: n.respawnAt })) ?? [],
      shards: this.latest?.goldShards.map(g => ({ id: g.id, originTeam: g.originTeam, expiresAt: g.expiresAt, contestable: true })) ?? [],
      fallback: [...this.neutrals].filter(([, v]) => !v.model).map(([id]) => ({ id, unitId: this.latest?.neutrals.find(n => n.id === id)?.species ?? 'unknown' })),
    };
  }
  baselineEvents() { this.needsBaseline = true; }
  reset() {
    for (const v of this.neutrals.values()) { v.model?.destroy(); v.root.destroy(); } this.neutrals.clear();
    for (const v of this.gold.values()) { v.root.enabled = false; this.goldPool.push(v); } this.gold.clear();
    for (const v of this.buffs.values()) v.destroy(); this.buffs.clear(); this.eventId = -1; this.needsBaseline = true; this.latest = null;
  }
  destroy() { this.reset(); for (const v of this.goldPool) v.root.destroy(); this.goldPool.length = 0; for (const v of this.camps.values()) v.root.destroy(); this.camps.clear(); }
}
