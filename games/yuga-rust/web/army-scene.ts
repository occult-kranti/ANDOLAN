import * as pc from 'playcanvas';
import { RenderKit, RAD, clamp, mixAngle } from '../../yuga/client/render-kit';

type Point = [number, number];
type Unit = {
  id: number;
  team: 'sun' | 'moon';
  role: string;
  lane: number;
  xz: Point;
  yaw_rad: number;
  hp: number;
  max_hp: number;
  radius: number;
  height: number;
  state: string;
  alive: boolean;
  death_tick: number | null;
  attack_until: number;
  attack_duration_ticks: number;
  windup_ticks: number;
};
type Attack = {
  kind: string;
  role: string;
  source: number;
  target?: number;
  team: 'sun' | 'moon';
  origin: [number, number, number];
  point: Point;
  start_tick: number;
  due_tick: number;
  radius?: number;
};
type Army = { units: Unit[]; attacks: Attack[]; cores: { sun: number; moon: number }; tick: number };
const blend = (a: number, b: number, t: number) => a + (b - a) * t;
const distance = (a: Point, b: Point) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2;
// Every authoritative unit gets its donor mesh. The closest sixteen get GPU
// morphs, shadows and health bars; more distant units keep their role silhouette.
const TROOP_CAP = 96,
  NEAR_CAP = 16,
  ATTACK_CAP = 72;
const roles = ['spearman', 'bow_guard', 'commander', 'cannon_cart', 'royal_chariot'];

export function setMaterial(entity: pc.Entity, material: pc.Material) {
  const mesh = entity.render!.meshInstances[0];
  if (mesh.material !== material) mesh.material = material;
}

function poseWeight(morph: pc.MorphInstance, index: number, value: number) {
  if (morph.getWeight(index) !== value) morph.setWeight(index, value);
}

export function makeArmyScene(kit: RenderKit, map: any, library?: pc.ContainerResource) {
  const app = kit.app;
  const layer = new pc.Entity('Army and core objectives', app);
  app.root.addChild(layer);
  const colors = {
    sun: kit.material('Sun army gold', '#f3b568', 0.55),
    moon: kit.material('Moon army azure', '#74d4ef', 0.55)
  };
  const backing = kit.material('army health backing', '#232d2c');
  const plinth = kit.material('objective sandstone', '#887963');
  const templates = new Map<string, pc.MeshInstance>();
  if (library) {
    const native = library.instantiateRenderEntity();
    for (const type of roles)
      for (const team of ['sun', 'moon']) {
        const key = team + '_' + type;
        const node = native.findByName(key) as pc.Entity;
        const source = node?.render?.meshInstances[0];
        if (!source?.mesh?.morph || source.mesh.morph.targets.length !== 4)
          throw new Error('Missing native army poses for ' + key);
        templates.set(key, source);
        const distant = (native.findByName(key + '_lod') as pc.Entity)?.render?.meshInstances[0];
        if (!distant) throw new Error('Missing distant mesh for ' + key);
        templates.set(key + '_lod', distant);
      }
    // Templates hold their mesh references while individual troop slots recycle.
  }

  const cores = new Map<string, { health: pc.Entity; beacon: pc.Entity }>();
  for (const objective of map.objectives) {
    const node = new pc.Entity(objective.id, app);
    layer.addChild(node);
    node.setLocalPosition(...(objective.position as [number, number, number]));
    const core = objective.kind === 'core',
      team = objective.team as 'sun' | 'moon',
      mat = colors[team];
    // Reuse the native confluence_world objective silhouette and dimensions.
    kit.shape(node, 'cylinder', plinth, 0, 0.1, 0, objective.radius * 2, 0.2, objective.radius * 2);
    kit.shape(
      node,
      'cylinder',
      plinth,
      0,
      core ? 1.6 : 1.2,
      0,
      core ? 1.05 : 0.6,
      core ? 2.8 : 2,
      core ? 1.05 : 0.6
    );
    const radius = core ? 0.65 : 0.38;
    const beacon = kit.shape(
      node,
      'sphere',
      mat,
      0,
      core ? 3.2 : 2.4,
      0,
      radius * 2,
      radius * 2,
      radius * 2
    );
    kit.ring(node, mat, objective.radius * 0.82, 0.105, 0.215);
    if (core) {
      kit.shape(node, 'box', backing, 0, 4.17, 0, 2.84, 0.22, 0.065);
      const health = kit.shape(node, 'box', mat, 0, 4.17, 0, 2.7, 0.13, 0.08);
      cores.set(team, { health, beacon });
    }
  }
  function makeSlot(near: boolean, source: pc.MeshInstance) {
    const root = new pc.Entity('Lane unit', app);
    layer.addChild(root);
    const visual = new pc.Entity('Authored native body', app);
    root.addChild(visual);
    const instance = new pc.MeshInstance(source.mesh, source.material);
    visual.addComponent('render', {
      meshInstances: [instance],
      castShadows: near,
      receiveShadows: near
    });
    const bar = near ? kit.shape(root, 'box', backing, 0, 2, 0, 0.75, 0.09, 0.06) : null;
    const hp = near ? kit.shape(root, 'box', colors.sun, 0, 2, 0, 0.7, 0.045, 0.075) : null;
    const foot = near ? kit.ring(root, colors.sun, 0.48, 0.055, 0.027, 20) : null;
    if (bar && hp) bar.render!.castShadows = hp.render!.castShadows = false;
    return { root, visual, instance, near, bar, hp, foot, key: '', id: -1 };
  }
  type Slot = ReturnType<typeof makeSlot>;
  const slots: Slot[] = [];
  let active = 0,
    nearCount = 0,
    troopTypes: string[] = [];
  const objectiveHP = { sun: 100, moon: 100 };
  const nearById = new Map<number, Slot>(),
    farById = new Map<number, Slot>();
  function showUnits(
    units: Unit[],
    prior: Map<number, Unit>,
    alpha: number,
    tick: number,
    actor: Point
  ) {
    const groups = [...units]
      .sort((a, b) => distance(a.xz, actor) - distance(b.xz, actor))
      .slice(0, TROOP_CAP);
    const near = groups.slice(0, NEAR_CAP);
    nearCount = 0;
    const assignments = [
      { map: nearById, near: true, units: near },
      { map: farById, near: false, units: groups.slice(NEAR_CAP) }
    ];
    // Reclaim departed IDs before assigning new ones. Waves reuse slots rather
    // than retaining nodes for every unit that has ever spawned.
    for (const batch of assignments) {
      const ids = new Set(batch.units.map((u) => u.id));
      for (const [id, slot] of batch.map)
        if (!ids.has(id)) {
          slot.root.enabled = false;
          slot.id = -1;
          batch.map.delete(id);
        }
    }
    for (const batch of assignments)
      for (const u of batch.units) {
        const detailed = batch.near && distance(u.xz, actor) < 36 * 36;
        const key = u.team + '_' + u.role + (detailed ? '' : '_lod'),
          source = templates.get(key);
        if (!source) throw new Error('Unknown army role ' + key);
        let slot = batch.map.get(u.id);
        if (!slot) {
          slot = slots.find((s) => s.id === -1 && s.near === batch.near);
          if (!slot) {
            slot = makeSlot(batch.near, source);
            slots.push(slot);
          }
          slot.id = u.id;
          batch.map.set(u.id, slot);
        }
        slot.root.enabled = true;
        if (slot.key !== key) {
          slot.key = key;
          slot.visual.render!.castShadows = detailed;
          if (slot.bar && slot.hp && slot.foot)
            slot.bar.enabled = slot.hp.enabled = slot.foot.enabled = detailed;
          slot.instance.mesh = source.mesh;
          slot.instance.material = source.material;
          slot.instance.morphInstance = detailed ? new pc.MorphInstance(source.mesh.morph!) : null;
          if (slot.hp && slot.foot) {
            setMaterial(slot.hp, colors[u.team]);
            setMaterial(slot.foot, colors[u.team]);
          }
        }
        const b = prior.get(u.id) ?? u;
        const dead = u.alive ? 0 : clamp((tick - (u.death_tick ?? tick)) / 13, 0, 1);
        slot.root.setLocalPosition(blend(b.xz[0], u.xz[0], alpha), 0, blend(b.xz[1], u.xz[1], alpha));
        slot.visual.setLocalEulerAngles(
          0,
          mixAngle(b.yaw_rad, u.yaw_rad, alpha) * RAD,
          dead * (u.role === 'cannon_cart' || u.role === 'royal_chariot' ? 6 : 84)
        );
        slot.visual.setLocalPosition(0, -dead * 0.12, 0);
        if (!detailed) continue;
        nearCount++;
        const gait = u.alive && u.state === 'walk' ? Math.sin(tick * 0.05 * 8.8 + u.id * 0.12) : 0;
        const windup = u.windup_ticks,
          duration = u.attack_duration_ticks;
        const elapsed = duration - (u.attack_until - tick);
        const swinging = u.alive && u.attack_until > tick && elapsed >= 0;
        const preparing = swinging
          ? clamp(elapsed / windup, 0, 1) * clamp((windup + 2 - elapsed) / 2, 0, 1)
          : 0;
        const follow = swinging
          ? clamp((elapsed - windup) / 2, 0, 1) * clamp((duration - elapsed) / (duration - windup), 0, 1)
          : 0;
        const morph = slot.instance.morphInstance!;
        poseWeight(morph, 0, Math.max(0, gait));
        poseWeight(morph, 1, Math.max(0, -gait));
        poseWeight(morph, 2, preparing);
        poseWeight(morph, 3, follow);
        const ratio = clamp(u.hp / u.max_hp, 0, 1);
        slot.bar!.enabled = slot.hp!.enabled = slot.foot!.enabled = u.alive;
        slot.bar!.setLocalPosition(0, u.height + 0.19, 0);
        slot.hp!.setLocalPosition(0.35 * (1 - ratio), u.height + 0.19, 0);
        slot.hp!.setLocalScale(0.7 * ratio, 0.045, 0.075);
        slot.foot!.setLocalScale(u.radius / 0.39, 1, u.radius / 0.39);
      }
    active = groups.length;
    troopTypes = [...new Set(groups.map((u) => u.role))];
  }

  function makeStrike() {
    const root = new pc.Entity('Army attack', app);
    layer.addChild(root);
    const shot = kit.shape(root, 'sphere', colors.sun, 0, 0, 0, 0.12, 0.12, 0.6);
    shot.render!.castShadows = false;
    const ring = kit.ring(root, colors.sun, 1, 0.045, 0.035, 36);
    return { root, shot, ring };
  }
  const strikes: ReturnType<typeof makeStrike>[] = [];
  let visibleAttacks = 0;
  function update(army: Army | null, previous: Army | null, alpha: number, actor: Point) {
    layer.enabled = !!army;
    if (!army) {
      active = nearCount = visibleAttacks = 0;
      troopTypes = [];
      return;
    }
    const prior = new Map((previous?.units ?? []).map((u) => [u.id, u]));
    const tick = blend(previous?.tick ?? army.tick, army.tick, alpha);
    showUnits(army.units, prior, alpha, tick, actor);
    for (const [name, objects] of cores) {
      const team = name as 'sun' | 'moon',
        hp = army.cores[team];
      objectiveHP[team] = hp;
      const fraction = clamp(hp / 100, 0, 1);
      objects.health.setLocalScale(2.7 * fraction, 0.13, 0.08);
      objects.health.setLocalPosition(1.35 * (1 - fraction), 4.17, 0);
      objects.beacon.enabled = hp > 0;
    }
    visibleAttacks = 0;
    for (const strike of army.attacks) {
      if (strike.kind !== 'siege' && strike.role !== 'bow_guard') continue;
      if (distance(actor, strike.point) > 55 * 55 || visibleAttacks >= ATTACK_CAP) continue;
      const siege = strike.kind === 'siege',
        progress = clamp(
          (tick - strike.start_tick) / Math.max(1, strike.due_tick - strike.start_tick),
          0,
          1
        );
      const q = clamp((progress - (siege ? 0.55 : 0.42)) / (siege ? 0.45 : 0.58), 0, 1);
      let s = strikes[visibleAttacks++];
      if (!s) {
        s = makeStrike();
        strikes.push(s);
      }
      s.root.enabled = true;
      s.ring.enabled = siege;
      s.shot.enabled = q > 0;
      const [x, sourceY, z] = strike.origin,
        [tx, tz] = strike.point;
      if (siege) {
        const radius = strike.radius!;
        s.ring.setLocalScale(radius, 1, radius);
        s.ring.setLocalPosition(tx, 0.045, tz);
        setMaterial(s.ring, colors[strike.team]);
      }
      const isBall = strike.role === 'cannon_cart';
      s.shot.setLocalScale(isBall ? 0.26 : 0.09, isBall ? 0.26 : 0.09, isBall ? 0.26 : 0.74);
      s.shot.setLocalPosition(
        blend(x, tx, q),
        blend(siege ? sourceY : 1.22, siege ? 0.15 : 1.05, q) +
          (isBall ? 2.4 * Math.sin(q * Math.PI) : 0),
        blend(z, tz, q)
      );
      s.shot.setLocalEulerAngles(0, Math.atan2(tx - x, tz - z) * RAD, 0);
      setMaterial(s.shot, colors[strike.team]);
    }
    for (let i = visibleAttacks; i < strikes.length; i++) strikes[i].root.enabled = false;
  }
  return {
    update,
    diagnostics: () => ({
      armyVisible: active,
      armyNear: nearCount,
      armyPool: slots.length,
      armyRoles: troopTypes,
      armyAttacks: visibleAttacks,
      objectiveCount: layer.enabled ? map.objectives.length : 0,
      coreHp: { ...objectiveHP }
    })
  };
}
