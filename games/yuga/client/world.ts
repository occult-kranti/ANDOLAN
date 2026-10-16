import * as pc from 'playcanvas';
import { SOLIDS } from '../shared/map';
import { heroById } from '../shared/heroes';
import type { Actor, ArenaSnapshot, GameEvent, HeroDef, Structure } from '../shared/types';
import { RenderKit, RAD, clamp, mixAngle, type XYZ } from './render-kit';
import { buildSangamCity } from './scenery';
import { HeroModelLibrary, type HeroModel } from './hero-models';
import { CastEffects } from './cast-effects';
import { createOriginalEnvironment } from './environment-light';
import { UnitModelLibrary, type UnitModel, type UnitModelId } from './unit-models';
import { JungleView } from './jungle-view';

export interface ScreenPoint { x: number; y: number; visible: boolean }
export interface ArenaWorld {
  update(snapshot: ArenaSnapshot | null, playerId: string | null, dt: number): void;
  /** Absolute authoritative aim convention: yaw zero is +Z, positive pitch looks up. */
  setCamera(yaw: number, pitch: number): void;
  setQuality(quality: 'low' | 'high'): void;
  setReducedMotion(enabled: boolean): void;
  setOverview(enabled: boolean): void;
  setActive(enabled: boolean): void;
  /** Discard pre-existing transient events after a transport welcome/reconnect. */
  resetEventHistory(): void;
  project(point: XYZ): ScreenPoint;
  reticle(): ScreenPoint | null;
  preloadHeroes(ids: string[], progress?: (done: number, total: number, heroId: string) => void): Promise<void>;
  preloadUnits(progress?: (done: number, total: number, unitId: string) => void): Promise<void>;
  assetDiagnostics(): ReturnType<HeroModelLibrary['diagnostics']> & { fallback: { id: string; heroId: string }[]; casts: ReturnType<CastEffects['diagnostic']>; units: ReturnType<UnitModelLibrary['diagnostics']> & { fallback: { id: string; unitId: string }[] }; jungle: ReturnType<JungleView['diagnostics']> };
  destroy(): void;
}

interface Rig {
  root: pc.Entity; body: pc.Entity; leftArm: pc.Entity; rightArm: pc.Entity; leftLeg: pc.Entity; rightLeg: pc.Entity;
  weapon: pc.Entity; sash: pc.Entity; shadow: pc.Entity; ring: pc.Entity; shield: pc.Entity; hit: pc.Entity;
  health: pc.Entity; hpFrame: pc.Entity; tag: string; phase: number; x: number; z: number; y: number; yaw: number;
  shotUntil: number; castUntil: number; hitUntil: number; deathAt: number; wasAlive: boolean;
  model: HeroModel | UnitModel | null; heroId: string; unitId: UnitModelId | null; shotEvent: number; castEvent: number; castSlot: number; motionSpeed: number;
  lastActor: Actor;
}
interface StructureView { root: pc.Entity; intact: pc.Entity; crystal: pc.Entity; shield: pc.Entity; health: pc.Entity; frame: pc.Entity; shattered: pc.Entity }
interface PooledVisual { root: pc.Entity; key: string }
interface Burst { root: pc.Entity; ring: pc.Entity; sparks: pc.Entity[]; until: number; born: number }

export async function createArenaWorld(canvas: HTMLCanvasElement): Promise<ArenaWorld> {
  const app = new pc.Application(canvas, { graphicsDeviceOptions: { alpha: false, antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true } });
  app.setCanvasFillMode(pc.FILLMODE_NONE); app.setCanvasResolution(pc.RESOLUTION_AUTO);
  app.scene.ambientLight = new pc.Color(.47, .57, .61); app.scene.exposure = 1.05;
  app.scene.fog.type = pc.FOG_LINEAR; app.scene.fog.color = new pc.Color(.72, .75, .69); app.scene.fog.start = 100; app.scene.fog.end = 240;
  const environment = createOriginalEnvironment(app);
  const kit = new RenderKit(app), root = new pc.Entity('SANGAM CITY / original arena'); app.root.addChild(root);
  const heroModels = new HeroModelLibrary(app);
  const unitModels = new UnitModelLibrary(app);
  const castEffects = new CastEffects(kit, root);
  const scenery = buildSangamCity(kit, root);
  const jungle = new JungleView(kit, root, unitModels);
  const camera = new pc.Entity('responsive shoulder camera'); app.root.addChild(camera);
  camera.addComponent('camera', { fov: 64, nearClip: .12, farClip: 450, clearColor: new pc.Color(.64, .75, .77) });
  const sunlight = new pc.Entity('late afternoon sunlight'); app.root.addChild(sunlight);
  sunlight.addComponent('light', { type: 'directional', color: new pc.Color(1, .87, .68), intensity: 1.55, castShadows: true, shadowResolution: 2048, shadowDistance: 85, shadowType: pc.SHADOW_PCF3, normalOffsetBias: .04, shadowBias: .15, numCascades: 2 });
  sunlight.setEulerAngles(48, -36, 0);
  const fill = new pc.Entity('sky bounce'); app.root.addChild(fill);
  fill.addComponent('light', { type: 'directional', color: new pc.Color(.53, .77, .9), intensity: .48, castShadows: false }); fill.setEulerAngles(25, 155, 0);

  const M = {
    ink: kit.material('hero dark undercloth', '#172b3c'), hair: kit.material('hero dark hair', '#252934'),
    skin: kit.material('hero warm bronze skin', '#bd8965'), skinDark: kit.material('hero deep bronze skin', '#90694f'),
    gold: kit.material('hero brass trim', '#eed3a0', .08, .6), light: kit.material('combat white-hot centre', '#fff4d8', 1.4),
    sun: kit.material('sun team orange', '#ffc36c', .6), moon: kit.material('moon team cyan', '#6ce4f4', .6),
    stone: kit.material('objective sandstone', '#b78c70'), dark: kit.material('objective dark metal', '#23434b', 0, .55),
    hp: kit.material('health mint', '#97f5b8', .65), hpBack: kit.material('health dark backing', '#172c37'),
    shield: kit.material('shield filament', '#b0e8ff', .6, .5, .35),
    hit: kit.material('acknowledged hit flash', '#fff7c7', 1, .3, .7),
  };
  const shadowTexture = kit.texture('soft contact shadow', 64, 64, ctx => {
    const gradient = ctx.createRadialGradient(32, 32, 3, 32, 32, 31);
    gradient.addColorStop(0, 'rgba(9,28,34,.5)'); gradient.addColorStop(.5, 'rgba(9,28,34,.3)'); gradient.addColorStop(1, 'rgba(9,28,34,0)');
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, 64, 64);
  });
  const shadowMaterial = kit.material('soft contact shadows', '#0b2029', 0, 0, .6);
  shadowMaterial.opacityMap = shadowTexture; shadowMaterial.opacityMapChannel = 'a'; shadowMaterial.useLighting = false; shadowMaterial.depthWrite = false; shadowMaterial.update();
  const rigs = new Map<string, Rig>(), buildings = new Map<string, StructureView>();
  const corpses: { rig: Rig; until: number; actor: Actor }[] = [];
  const projectileViews = new Map<string, PooledVisual>(), projectilePool: PooledVisual[] = [];
  const zoneViews = new Map<string, PooledVisual>(), zonePool: PooledVisual[] = [];
  const pickupViews = new Map<string, pc.Entity>();
  const bursts: Burst[] = [];
  let yaw = 0, pitch = -.06, elapsed = 0, reducedMotion = false, overview = true;
  let quality: 'low' | 'high' = 'high', lastSnapshot: ArenaSnapshot | null = null, playerId: string | null = null;
  let epoch = '', lastTick = -1, eventId = -1, tracked = '', initialized = false, destroyed = false;
  let active = true, baselineEvents = true;
  let cameraDistance = 6;
  const follow = new pc.Vec3(), cameraForward = new pc.Vec3(0, 0, 1), temp = new pc.Vec3(), screen = new pc.Vec3();

  function group(parent: pc.Entity, name: string, x = 0, y = 0, z = 0) { const e = new pc.Entity(name); parent.addChild(e); e.setLocalPosition(x, y, z); return e; }
  function teamMaterial(team: 'sun' | 'moon') { return team === 'sun' ? M.sun : M.moon; }
  function orb(parent: pc.Entity, m: pc.Material, x: number, y: number, z: number, sx: number, sy: number, sz: number) { return kit.shape(parent, 'sphere', m, x, y, z, sx, sy, sz); }
  function limb(parent: pc.Entity, name: string, x: number, y: number, m: pc.Material, length: number, thickness: number) {
    const pivot = group(parent, name, x, y);
    kit.shape(pivot, 'capsule', m, 0, -length / 2, 0, thickness, length / 2, thickness);
    return pivot;
  }
  function makeWeapon(parent: pc.Entity, hero: HeroDef, color: pc.Material, accent: pc.Material) {
    const weapon = group(parent, hero.weapon, -.02, -.37, .1);
    if (hero.weapon === 'bow') {
      for (let i = 0; i < 8; i++) {
        const a = -1.15 + i / 8 * 2.3, b = -1.15 + (i + 1) / 8 * 2.3;
        kit.line(weapon, accent, { x: 0, y: Math.sin(a) * .85, z: Math.cos(a) * .46 }, { x: 0, y: Math.sin(b) * .85, z: Math.cos(b) * .46 }, .075);
      }
      kit.line(weapon, M.light, { x: 0, y: -.77, z: .19 }, { x: 0, y: .77, z: .19 }, .012);
      kit.line(weapon, M.gold, { x: 0, y: 0, z: -.02 }, { x: 0, y: 0, z: .7 }, .035);
    } else if (hero.weapon === 'chakram') {
      const ring = kit.ring(weapon, accent, .43, .095, 0, 20); ring.setLocalEulerAngles(90, 0, 0);
      for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2; orb(weapon, color, Math.sin(a) * .45, Math.cos(a) * .45, 0, .16, .16, .1); }
    } else {
      const tall = hero.weapon !== 'mace';
      kit.shape(weapon, 'cylinder', M.gold, 0, tall ? .25 : .15, 0, .075, tall ? 2.1 : 1.2, .075);
      if (hero.weapon === 'mace') {
        orb(weapon, accent, 0, .8, 0, hero.id === 'bhima' ? .48 : .55, hero.id === 'bhima' ? .8 : .55, .55);
        kit.shape(weapon, 'cylinder', color, 0, .8, 0, .57, .16, .57);
      } else if (hero.weapon === 'spear') {
        const head = kit.shape(weapon, 'cone', accent, 0, 1.43, 0, .3, .64, .14);
        if (hero.id === 'hidimbi') { head.setLocalScale(.35, .5, .15); for (const side of [-1, 1]) kit.line(weapon, accent, { x: 0, y: 1.1, z: 0 }, { x: side * .26, y: 1.55, z: 0 }, .06); }
        else { const flag = kit.shape(weapon, 'box', color, -.23, 1.02, 0, .46, .35, .025); flag.setLocalEulerAngles(0, 0, -15); }
      } else {
        const crown = orb(weapon, accent, 0, 1.42, 0, .4, .65, .22); crown.setLocalEulerAngles(0, 0, -18);
        orb(weapon, color, 0, 1.4, .08, .22, .35, .14);
        kit.ring(weapon, accent, .25, .035, 1.22, 16);
      }
    }
    return weapon;
  }

  function unitIdentity(actor: Actor): UnitModelId {
    if (actor.unitArchetype === 'summon' || actor.minionRole === 'summon') return actor.heroId === 'hidimbi' ? 'yaksha' : 'soldier';
    return actor.unitArchetype ?? (actor.minionRole === 'siege' ? 'king' : 'soldier');
  }
  function rigTag(actor: Actor) { return `${actor.kind}/${actor.heroId}/${actor.team}/${actor.minionRole ?? ''}/${actor.unitArchetype ?? ''}`; }
  function makeRig(actor: Actor): Rig {
    const hero = heroById(actor.heroId), minion = actor.kind === 'minion', siege = actor.minionRole === 'siege', summon = actor.minionRole === 'summon';
    const color = kit.material(`hero ${hero.id}`, hero.color, .02, .4), accent = kit.material(`hero trim ${hero.id}`, hero.accent, .15, .65);
    const team = teamMaterial(actor.team), r = group(root, `${actor.kind} ${actor.id}`), body = group(r, 'animated body');
    const broad = hero.role === 'Vanguard' ? 1.23 : .97;
    const mantle = kit.shape(body, 'cone', minion ? summon ? color : team : color, 0, .83, -.08, minion ? .56 : .75 * broad, .85, minion ? .4 : .58); mantle.setLocalEulerAngles(180, 0, 0);
    orb(body, minion ? M.dark : color, 0, 1.37, 0, (minion ? .62 : .78) * broad, .75, .43);
    if (!minion) {
      kit.shape(body, 'box', accent, 0, 1.11, .02, .68 * broad, .11, .46);
      orb(body, M.skin, 0, 1.97, .035, .38, .47, .35);
      orb(body, M.hair, 0, 2.09, -.025, .41, .27, .36);
      orb(body, M.skin, 0, 1.95, .19, .18, .16, .1);
      kit.shape(body, 'box', M.ink, 0, 2.01, .204, .25, .035, .012);
      for (const side of [-1, 1]) {
        orb(body, accent, side * .43 * broad, 1.62, -.01, .34, .22, .44);
        orb(body, team, side * .16, 1.53, .212, .1, .1, .035);
      }
      // Original crests give each hero a distinct profile without sacred image textures.
      if (hero.id === 'ravana') {
        for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; const facet = kit.shape(body, 'cone', accent, Math.sin(a) * .26, 2.33 + (i % 2) * .08, Math.cos(a) * .22, .12, .43, .13); facet.setLocalEulerAngles(Math.cos(a) * 24, 0, -Math.sin(a) * 24); }
        orb(body, color, 0, 1.52, -.18, 1.23, .65, .55);
      } else if (hero.id === 'hanuman') {
        orb(body, M.skin, 0, 1.91, .2, .32, .2, .23);
        for (const side of [-1, 1]) orb(body, M.skin, side * .23, 2, .01, .17, .22, .15);
        let prev = { x: 0, y: .77, z: -.28 };
        for (let i = 1; i <= 8; i++) { const a = i / 8 * 3.7; const next = { x: Math.sin(a) * .4, y: .55 + i * .16, z: -.3 - Math.sin(i / 8 * 2.5) * .7 }; kit.line(body, color, prev, next, .09); prev = next; }
      } else if (hero.id === 'karna') {
        for (const side of [-1, 1]) { const disc = kit.shape(body, 'cylinder', accent, side * .5, 1.65, 0, .45, .08, .45); disc.setLocalEulerAngles(0, 0, 90); }
        kit.shape(body, 'cone', accent, 0, 2.37, 0, .32, .46, .23);
      } else if (hero.id === 'hidimbi') {
        for (let i = -2; i <= 2; i++) { const leaf = orb(body, i % 2 ? accent : color, i * .21, 1.6, -.16, .35, .85, .17); leaf.setLocalEulerAngles(0, 0, i * 21); }
        kit.shape(body, 'capsule', M.hair, -.15, 2.28, -.02, .12, .22, .13);
      } else if (hero.id === 'meghnad') {
        for (const side of [-1, 1]) { const crest = kit.shape(body, 'cone', accent, side * .16, 2.35, 0, .17, .55, .17); crest.setLocalEulerAngles(0, 0, -side * 16); }
      } else if (hero.id === 'sita') { const crest = orb(body, accent, 0, 2.35, .05, .19, .46, .1); crest.setLocalEulerAngles(0, 0, -16); }
      else if (hero.id === 'draupadi') {
        for (let i = -2; i <= 2; i++) kit.shape(body, 'cone', accent, i * .095, 2.25 + (.2 - Math.abs(i) * .05), .04, .1, .27, .1);
        orb(body, accent, 0, 1.52, .25, .22, .28, .07);
      } else if (hero.id === 'bhima') {
        for (const side of [-1, 1]) { const strap = kit.shape(body, 'box', accent, side * .16, 1.4, .22, .08, .65, .04); strap.setLocalEulerAngles(0, 0, side * 32); }
      } else if (hero.id === 'duryodhana') {
        kit.shape(body, 'cylinder', accent, 0, 2.18, 0, .43, .16, .39);
        for (const side of [-1, 1]) kit.shape(body, 'box', color, side * .48, 1.62, 0, .35, .24, .46);
      } else if (hero.id === 'subhadra') {
        for (let i = 0; i < 4; i++) orb(body, M.hair, .22 + i * .02, 1.99 - i * .13, -.16, .13, .2, .14);
      } else kit.shape(body, 'cone', accent, 0, 2.3, -.04, .2, .45, .2);
      if (hero.weapon === 'bow') {
        kit.shape(body, 'cylinder', M.ink, -.2, 1.55, -.3, .23, .75, .23);
        for (let i = 0; i < 3; i++) kit.shape(body, 'cylinder', accent, -.27 + i * .065, 1.96, -.3, .025, .5, .025);
      }
    } else {
      orb(body, M.dark, 0, 1.83, 0, .36, .38, .34);
      kit.shape(body, 'box', team, 0, 1.84, .175, .28, .08, .025);
      kit.shape(body, 'cone', team, 0, 2.08, 0, .16, .23, .16);
      if (siege) {
        for (const side of [-1, 1]) {
          orb(body, M.gold, side * .46, 1.46, 0, .35, .4, .46);
          kit.shape(body, 'cylinder', M.dark, side * .35, .35, 0, .46, .2, .46).setLocalEulerAngles(0, 0, 90);
        }
        kit.shape(body, 'cylinder', M.dark, 0, 1.3, .48, .38, 1.05, .38).setLocalEulerAngles(90, 0, 0);
        kit.shape(body, 'cylinder', team, 0, 1.3, 1, .25, .08, .25).setLocalEulerAngles(90, 0, 0);
      }
      if (summon) {
        for (const side of [-1, 1]) { const leaf = orb(body, accent, side * .24, 1.95, -.1, .16, .7, .1); leaf.setLocalEulerAngles(0, 0, -side * 25); }
        kit.ring(body, color, .55, .045, 1.25, 16);
      }
    }
    const leftArm = limb(body, 'left arm', -.43 * broad, 1.58, minion ? M.dark : color, .64, .2);
    const rightArm = limb(body, 'right aim arm', .43 * broad, 1.58, minion ? M.dark : color, .64, .2);
    if (!minion) { orb(leftArm, M.skin, 0, -.61, 0, .19, .2, .19); orb(rightArm, M.skin, 0, -.61, 0, .19, .2, .19); }
    const leftLeg = limb(body, 'left stride', -.19, .86, M.ink, .67, .23), rightLeg = limb(body, 'right stride', .19, .86, M.ink, .67, .23);
    for (const leg of [leftLeg, rightLeg]) kit.shape(leg, 'box', minion ? M.dark : accent, 0, -.61, .08, .25, .18, .38);
    const weapon = minion ? kit.shape(rightArm, 'box', team, 0, -.38, .3, .16, .18, .7) : makeWeapon(rightArm, hero, color, accent);
    const sash = group(body, 'flowing mantle', 0, 1.6, -.24);
    if (!minion) { const cloth = kit.shape(sash, 'box', color, -.11, -.48, -.09, .54, .96, .045); cloth.setLocalEulerAngles(-12, 0, 8); kit.shape(sash, 'box', accent, -.31, -.49, -.1, .045, .95, .055); }
    // Animated body transforms can share GPU draws. Visibility-changing overlays stay separate.
    for (const component of body.findComponents('render')) (component as pc.RenderComponent).batchGroupId = kit.actorGroup;
    const shadow = kit.shape(root, 'plane', shadowMaterial, actor.x, .035, actor.z, minion ? 1.2 : 1.7, 1, minion ? 1.2 : 1.7); shadow.render!.castShadows = false;
    const ring = kit.ring(r, team, minion ? .46 : .72, minion ? .055 : .07, .04, minion ? 12 : 24);
    const shield = kit.ring(r, M.shield, .85, .1, .85, 24); shield.setLocalEulerAngles(65, 0, 0); shield.enabled = false;
    const hit = orb(r, M.hit, 0, 1.1, 0, .95, 1.8, .75); hit.enabled = false; hit.render!.castShadows = false;
    const hpFrame = group(r, 'health strip', 0, minion ? 2.3 : 2.8, 0);
    kit.shape(hpFrame, 'box', M.hpBack, 0, 0, 0, minion ? .65 : 1.1, .075, .025);
    const health = kit.shape(hpFrame, 'box', team, 0, 0, .025, minion ? .6 : 1.05, .04, .025);
    const unitId = minion ? unitIdentity(actor) : null;
    const model = unitId ? unitModels.instantiate(unitId, actor.id, r) : heroModels.instantiate(actor.heroId, actor.id, r);
    if (model) { body.enabled = false; model.setShadows(quality === 'high'); if (minion) model.root.setLocalScale(1 / .68, 1 / .68, 1 / .68); }
    const result: Rig = { root: r, body, leftArm, rightArm, leftLeg, rightLeg, weapon, sash, shadow, ring, shield, hit, health, hpFrame,
      tag: rigTag(actor), phase: 0, x: actor.x, z: actor.z, y: actor.y, yaw: actor.yaw,
      shotUntil: 0, castUntil: 0, hitUntil: 0, deathAt: -10, wasAlive: actor.health > 0,
      model, heroId: actor.heroId, unitId, shotEvent: 0, castEvent: 0, castSlot: 0, motionSpeed: 0, lastActor: actor };
    r.setPosition(actor.x, actor.y, actor.z); return result;
  }

  function makeStructure(s: Structure): StructureView {
    const r = group(root, s.id, s.x, 0, s.z), intact = group(r, 'intact collision silhouette'), team = teamMaterial(s.team), core = s.kind === 'core', radius = core ? 2.7 : 1.7;
    kit.shape(intact, 'cylinder', M.dark, 0, .25, 0, radius * 2, .5, radius * 2);
    kit.shape(intact, 'cylinder', M.stone, 0, 1, 0, radius * 1.6, 1.2, radius * 1.6);
    kit.shape(intact, 'cylinder', M.gold, 0, 1.6, 0, radius * 1.7, .18, radius * 1.7);
    const crystal = group(intact, 'objective heart', 0, core ? 3 : 2.5, 0);
    const lower = kit.shape(crystal, 'cone', team, 0, -.5, 0, core ? 2.5 : 1.4, 1.1, core ? 2.5 : 1.4); lower.setLocalEulerAngles(180, 0, 0);
    kit.shape(crystal, 'cone', team, 0, .5, 0, core ? 2.5 : 1.4, 1.1, core ? 2.5 : 1.4);
    for (let i = 0; i < (core ? 6 : 4); i++) {
      const a = i / (core ? 6 : 4) * Math.PI * 2, x = Math.sin(a) * radius * .78, z = Math.cos(a) * radius * .78;
      kit.shape(intact, 'cylinder', M.gold, x, 2.1, z, .2, 2.8, .2);
      orb(intact, team, x, 3.55, z, .3, .45, .3);
    }
    kit.ring(r, team, radius * .92, .09, .045, 32);
    const shield = group(intact, 'core locked shield');
    for (const tilt of [0, 60, -60]) { const ring = kit.ring(shield, M.shield, radius * .98, .11, 2.6, 40); ring.setLocalEulerAngles(tilt, 20, 0); }
    const frame = group(r, 'structure health', 0, core ? 5 : 4.5, 0);
    kit.shape(frame, 'box', M.hpBack, 0, 0, 0, 2.2, .14, .04);
    const health = kit.shape(frame, 'box', team, 0, 0, .03, 2.1, .08, .035);
    const shattered = group(r, 'destroyed objective rubble');
    for (let i = 0; i < 5; i++) { const a = i * 2.4; const rock = kit.shape(shattered, 'box', M.stone, Math.sin(a) * radius * .6, .05, Math.cos(a) * radius * .6, .6, .1, .6); rock.setLocalEulerAngles(0, a * RAD, 0); }
    shattered.enabled = false;
    return { root: r, intact, crystal, shield, frame, health, shattered };
  }

  function releaseRemoved<T extends PooledVisual>(views: Map<string, T>, live: Set<string>, pool: T[]) {
    for (const [id, visual] of views) if (!live.has(id)) { visual.root.enabled = false; views.delete(id); pool.push(visual); }
  }
  function projectileVisual(key: string): PooledVisual {
    const v = projectilePool.pop() ?? { root: group(root, 'projectile'), key: '' };
    if (v.key !== key) {
      for (const child of [...v.root.children]) child.destroy();
      const [hex, weapon] = key.split('/'), color = kit.material('projectile glow', hex!, 1.2);
      color.cull = pc.CULLFACE_NONE; color.update();
      if (weapon === 'bow' || weapon === 'spear') {
        kit.shape(v.root, 'cylinder', M.light, 0, 0, -.18, .035, .8, .035).setLocalEulerAngles(90, 0, 0);
        kit.shape(v.root, 'cone', color, 0, 0, .3, .13, .28, .08).setLocalEulerAngles(90, 0, 0);
        kit.shape(v.root, 'box', color, 0, 0, -.5, .22, .025, .16);
      } else if (weapon === 'chakram') {
        const hoop = kit.ring(v.root, color, .25, .05, 0, 20); hoop.setLocalEulerAngles(90, 0, 0);
        orb(v.root, M.light, 0, 0, 0, .1, .1, .1);
      } else if (weapon === 'mace') {
        kit.arc(v.root, color, .3, .1, 0, -1.1, 1.1, 16).setLocalEulerAngles(90, 0, 0);
        orb(v.root, M.light, 0, 0, .02, .16, .16, .22);
      } else {
        orb(v.root, color, 0, 0, 0, .28, .28, .35);
        orb(v.root, M.light, 0, 0, .08, .13, .13, .2);
      }
      const trail = kit.shape(v.root, 'cone', color, 0, 0, -.8, .12, 1.2, .12); trail.setLocalEulerAngles(-90, 0, 0);
      v.key = key;
    }
    v.root.enabled = true; return v;
  }
  function zoneVisual(key: string): PooledVisual {
    const v = zonePool.pop() ?? { root: group(root, 'ability footprint'), key: '' };
    if (v.key !== key) {
      for (const child of [...v.root.children]) child.destroy();
      const [color, team, kind, mechanic, relation] = key.split('/'), edge = kit.material('ability boundary', color!, .5);
      const teamColor = team === 'sun' ? M.sun : M.moon;
      const circle = (r: number, width = .018, y = .065) => kit.ring(v.root, edge, r, width, y, 40);
      const mark = (x: number, z: number, sx: number, sz: number, angle = 0) => {
        const e = kit.shape(v.root, 'box', edge, x, .07, z, sx, .015, sz); e.setLocalEulerAngles(0, angle, 0); return e;
      };
      if (kind === 'cone' || kind === 'burst') {
        const half = Math.acos(kind === 'cone' ? .55 : .25);
        kit.arc(v.root, edge, 1, .025, .06, -half, half, 32);
        for (const side of [-1, 1]) kit.line(v.root, teamColor, { x: 0, y: .06, z: 0 }, { x: Math.sin(half) * side, y: .06, z: Math.cos(half) }, .012);
        kit.arc(v.root, edge, .65, .012, .065, -half, half, 24);
      } else {
        circle(1, .025); kit.ring(v.root, teamColor, .95, .012, .066, 40);
        const hostile = relation === 'hostile' && !['heal', 'ward', 'dash', 'leap', 'summon'].includes(kind!);
        for (let i = 0; i < 8; i++) {
          const a = i / 8 * Math.PI * 2;
          if (hostile) { const tip = kit.shape(v.root, 'cone', edge, Math.sin(a) * .9, .07, Math.cos(a) * .9, .07, .12, .02); tip.setLocalEulerAngles(90, a * RAD, 0); }
          else mark(Math.sin(a) * .88, Math.cos(a) * .88, .07, .015, a * RAD);
        }
      }
      if (kind === 'heal') {
        mark(0, 0, .12, .58); mark(0, 0, .58, .12); circle(.55);
      } else if (kind === 'ward') {
        circle(.72, .012);
        for (let i = 0; i < 6; i++) {
          const a = i / 6 * Math.PI * 2, x = Math.sin(a) * .76, z = Math.cos(a) * .76;
          kit.line(v.root, edge, { x, y: .12, z }, { x, y: mechanic === 'mithila-sanctuary' ? 1.7 : .7, z }, .012);
          if (mechanic === 'mithila-sanctuary') {
            const leaf = kit.shape(v.root, 'sphere', edge, x, .07, z, .1, .02, .28); leaf.setLocalEulerAngles(0, a * RAD, 0);
            kit.line(v.root, edge, { x, y: 1.7, z }, { x: x * .6, y: 2.2, z: z * .6 }, .01);
          }
        }
      } else if (kind === 'slow') {
        circle(.52, .016);
        for (let i = 0; i < 6; i++) { const a = i / 6 * Math.PI * 2; mark(Math.sin(a) * .42, Math.cos(a) * .42, .025, .25, a * RAD + 35); }
      } else if (kind === 'pull') {
        circle(.25, .025);
        for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; const arrow = kit.shape(v.root, 'cone', edge, Math.sin(a) * .6, .07, Math.cos(a) * .6, .09, .22, .02); arrow.setLocalEulerAngles(-90, a * RAD, 0); }
      } else if (kind === 'nova') {
        circle(.35, .02); circle(.66, .012);
        for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2; mark(Math.sin(a) * .7, Math.cos(a) * .7, .018, .35, a * RAD); }
      } else if (kind === 'dash' || kind === 'leap') {
        for (let i = -1; i <= 1; i++) { mark(-.13, i * .2, .035, .22, -38); mark(.13, i * .2, .035, .22, 38); }
      } else if (kind === 'summon') {
        for (const side of [-1, 1]) { const standard = new pc.Entity('summon standard'); v.root.addChild(standard); standard.setLocalPosition(side * .35, 0, 0); kit.ring(standard, edge, .19, .025, .07, 16); }
      } else if (kind === 'bolt' || kind === 'line') {
        mark(0, 0, .035, .8); mark(-.12, .25, .025, .25, -45); mark(.12, .25, .025, .25, 45);
      }
      v.key = key;
    }
    v.root.enabled = true; return v;
  }
  function burst(event: GameEvent) {
    if (event.type === 'shot' || event.type === 'upgrade') return;
    let fx = bursts.find(b => b.until <= elapsed);
    if (!fx && bursts.length < 24) {
      const r = group(root, 'server event burst'), ring = kit.ring(r, M.light, 1, .05, .05, 20);
      const sparks = Array.from({ length: 5 }, () => orb(r, M.light, 0, 0, 0, .1, .1, .1));
      fx = { root: r, ring, sparks, until: 0, born: 0 }; bursts.push(fx);
    }
    if (!fx) return;
    fx.root.enabled = true; fx.root.setPosition(event.x, event.type === 'hit' ? .8 : .1, event.z);
    fx.until = elapsed + (reducedMotion ? .16 : .45); fx.born = elapsed;
    const material = kit.material('confirmed combat burst', event.color, .9);
    fx.ring.render!.meshInstances[0]!.material = material;
    for (const s of fx.sparks) s.render!.meshInstances[0]!.material = material;
  }
  function consumeEvents(snapshot: ArenaSnapshot) {
    if (baselineEvents) { eventId = snapshot.events.at(-1)?.id ?? -1; baselineEvents = false; return; }
    for (const event of snapshot.events) {
      if (event.id <= eventId) continue;
      eventId = event.id;
      const age = snapshot.time - event.time;
      const actor = rigs.get(event.actorId), target = event.targetId ? rigs.get(event.targetId) : undefined;
      // A delayed render can still play a recent acknowledged action. Very old menu/reconnect
      // history is discarded, and particles keep the shorter visual freshness window.
      if (age <= 2 && actor && event.type === 'shot') { actor.shotUntil = elapsed + .18; actor.shotEvent = event.id; }
      if (age <= 2 && actor && event.type === 'ability') { actor.castUntil = elapsed + .5; actor.castEvent = event.id; actor.castSlot = Math.max(0, heroById(actor.heroId).abilities.findIndex(ability => event.label.includes(ability.name))); if (actor.unitId) actor.shotEvent = event.id; }
      if (age > .7) continue;
      if (target && event.type === 'hit') target.hitUntil = elapsed + .11;
      burst(event);
    }
  }
  function updateRig(r: Rig, actor: Actor, dt: number, local: boolean) {
    r.lastActor = actor;
    if (!r.model) {
      r.model = r.unitId ? unitModels.instantiate(r.unitId, actor.id, r.root) : heroModels.instantiate(actor.heroId, actor.id, r.root);
      if (r.model) { r.body.enabled = false; r.model.setShadows(quality === 'high'); if (r.unitId) r.model.root.setLocalScale(1 / .68, 1 / .68, 1 / .68); }
    }
    const present = actor.bot || actor.connected;
    const alive = actor.health > 0 && actor.respawn <= 0 && present;
    if (alive !== r.wasAlive) { if (!alive) r.deathAt = elapsed; else { r.x = actor.x; r.z = actor.z; r.y = actor.y; } r.wasAlive = alive; }
    r.root.enabled = alive || present && elapsed - r.deathAt < (r.model ? 1.1 : .45);
    r.shadow.enabled = alive;
    if (!r.root.enabled) return;
    const distance = Math.hypot(actor.x - r.x, actor.z - r.z), k = distance > 8 || local ? 1 : 1 - Math.exp(-16 * dt);
    const oldX = r.x, oldZ = r.z;
    r.x += (actor.x - r.x) * k; r.z += (actor.z - r.z) * k; r.y += (actor.y - r.y) * k;
    r.yaw = local ? actor.cast?.yaw ?? yaw : mixAngle(r.yaw, actor.yaw, 1 - Math.exp(-20 * dt));
    const speed = dt > 0 ? Math.min(9, Math.hypot(r.x - oldX, r.z - oldZ) / dt) : 0;
    r.motionSpeed += (speed - r.motionSpeed) * (1 - Math.exp(-12 * dt));
    r.phase += dt * (2 + r.motionSpeed * 1.5);
    const stride = Math.min(1, r.motionSpeed / 4), swing = Math.sin(r.phase) * stride * 31;
    const shot = clamp((r.shotUntil - elapsed) / .18, 0, 1), cast = clamp((r.castUntil - elapsed) / .5, 0, 1);
    r.root.setPosition(r.x, r.y, r.z); r.root.setEulerAngles(0, r.yaw * RAD, 0);
    const minion = actor.kind === 'minion', scale = minion ? .68 : 1;
    r.root.setLocalScale(scale, scale, scale);
    if (!r.model) {
    r.body.setLocalPosition(0, reducedMotion ? 0 : Math.abs(Math.cos(r.phase)) * stride * .035, 0);
    r.body.setLocalEulerAngles(alive ? -stride * 3 : clamp((elapsed - r.deathAt) * 200, 0, 82), 0, alive ? 0 : 15);
    r.leftLeg.setLocalEulerAngles(actor.y > .1 ? -22 : swing, 0, 0); r.rightLeg.setLocalEulerAngles(actor.y > .1 ? 30 : -swing, 0, 0);
    r.rightArm.setLocalEulerAngles(-72 - (local ? pitch * RAD : 0) - shot * 18 - cast * 35, 0, -8);
    r.leftArm.setLocalEulerAngles(actor.kind === 'hero' && heroById(actor.heroId).weapon === 'bow' ? -82 - (local ? pitch * RAD : 0) : -swing * .65 - cast * 90, 0, cast * 16);
    r.weapon.setLocalEulerAngles(0, shot * 12, 0);
    r.sash.setLocalEulerAngles(reducedMotion ? -6 : -8 - stride * 17 + Math.sin(r.phase * .55) * 4, 0, 0);
    }
    r.shadow.setPosition(r.x, .035, r.z); const ss = (minion ? 1.2 : 1.7) * (1 + actor.y * .12); r.shadow.setLocalScale(ss, 1, ss);
    r.ring.enabled = alive; r.shield.enabled = alive && (actor.shield > 0 || actor.effects.ward > 0);
    if (!reducedMotion) r.shield.setLocalEulerAngles(65, elapsed * 50, 0);
    r.hit.enabled = alive && r.hitUntil > elapsed;
    if (r.model) {
      r.body.enabled = false; r.model.root.enabled = true;
      if ('setAnimated' in r.model) {
        const localActor = lastSnapshot?.actors.find(a => a.id === playerId);
        const near = !localActor || Math.hypot(localActor.x - actor.x, localActor.z - actor.z) < (quality === 'low' ? 38 : 60);
        r.model.setAnimated(near || shot > 0 || !alive);
      }
      const ownedShot = lastSnapshot?.projectiles.find(projectile => projectile.owner === actor.id);
      const aimPitch = actor.cast?.pitch ?? (local ? pitch : ownedShot ? Math.atan2(ownedShot.vy, Math.hypot(ownedShot.vx, ownedShot.vz)) : 0);
      r.model.update({ speed: r.motionSpeed, airborne: actor.y > .1, alive, shot: r.shotEvent, cast: r.castEvent, castSlot: r.castSlot, casting: !!actor.cast, reducedMotion, pitch: aimPitch }, dt);
    }
    r.hpFrame.enabled = alive && !local; r.hpFrame.setEulerAngles(0, yaw * RAD + 180, 0);
    const ratio = clamp(actor.health / actor.maxHealth, 0, 1), width = minion ? .6 : 1.05;
    r.health.setLocalScale(width * Math.max(.001, ratio), .04, .025); r.health.setLocalPosition(-width * (1 - ratio) / 2, 0, .025);
  }

  // Slab segment/AABB intersection, camera-only. Authority owns all character collision.
  function rayBox(origin: XYZ, delta: XYZ, min: XYZ, max: XYZ) {
    let near = 0, far = 1;
    for (const axis of ['x', 'y', 'z'] as const) {
      if (Math.abs(delta[axis]) < .00001) { if (origin[axis] < min[axis] || origin[axis] > max[axis]) return 1; }
      else {
        let a = (min[axis] - origin[axis]) / delta[axis], b = (max[axis] - origin[axis]) / delta[axis];
        if (a > b) [a, b] = [b, a]; near = Math.max(near, a); far = Math.min(far, b); if (near > far) return 1;
      }
    }
    return near >= 0 && near <= 1 ? near : 1;
  }
  function positionCamera(actor: Actor | undefined, dt: number) {
    if (overview || !actor) {
      const angle = reducedMotion ? 0 : Math.sin(elapsed * .025) * .12;
      camera.setPosition(-52 + angle * 25, 31, -74); camera.lookAt(7, 5, 4); cameraForward.copy(camera.forward);
      initialized = false; return;
    }
    const key = `${actor.id}/${actor.respawn > 0}`;
    if (!initialized || key !== tracked || Math.hypot(follow.x - actor.x, follow.z - actor.z) > 10) {
      follow.set(actor.x, actor.y, actor.z); initialized = true; tracked = key; cameraDistance = 6;
    }
    // Current local XZ is immediate; vertical settling avoids a jarring landing camera.
    follow.x = actor.x; follow.z = actor.z; follow.y += (actor.y - follow.y) * (reducedMotion ? 1 : 1 - Math.exp(-18 * dt));
    cameraForward.set(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch));
    const anchor = new pc.Vec3(follow.x, follow.y + 2.25, follow.z);
    const desired = new pc.Vec3(anchor.x - cameraForward.x * 6 - Math.cos(yaw) * .72, Math.max(.4, anchor.y - cameraForward.y * 6), anchor.z - cameraForward.z * 6 + Math.sin(yaw) * .72);
    desired.x = clamp(desired.x, -68.7, 68.7); desired.z = clamp(desired.z, -82.7, 82.7);
    const origin = { x: actor.x, y: actor.y + 1.4, z: actor.z }, delta = { x: desired.x - origin.x, y: desired.y - origin.y, z: desired.z - origin.z };
    let fraction = 1;
    for (const s of SOLIDS) fraction = Math.min(fraction, rayBox(origin, delta, { x: s.x - s.w / 2 - .28, y: -.2, z: s.z - s.d / 2 - .28 }, { x: s.x + s.w / 2 + .28, y: s.height + .28, z: s.z + s.d / 2 + .28 }));
    for (const s of lastSnapshot?.structures ?? []) if (s.health > 0) {
      const radius = (s.kind === 'core' ? 2.8 : 1.8) + .25;
      fraction = Math.min(fraction, rayBox(origin, delta, { x: s.x - radius, y: -.1, z: s.z - radius }, { x: s.x + radius, y: s.kind === 'core' ? 4.4 : 3.9, z: s.z + radius }));
    }
    const length = Math.hypot(delta.x, delta.y, delta.z), targetDistance = Math.max(.2, length * fraction - (fraction < 1 ? .15 : 0));
    cameraDistance = targetDistance < cameraDistance ? targetDistance : cameraDistance + (targetDistance - cameraDistance) * (1 - Math.exp(-8 * dt));
    const t = length ? cameraDistance / length : 0;
    camera.setPosition(origin.x + delta.x * t, Math.max(.25, origin.y + delta.y * t), origin.z + delta.z * t);
    const eye = camera.getPosition(); camera.lookAt(eye.x + cameraForward.x * 25, eye.y + cameraForward.y * 25, eye.z + cameraForward.z * 25);
    const rig = rigs.get(actor.id);
    if (rig?.model) { rig.model.root.enabled = cameraDistance >= 1.4; rig.body.enabled = false; }
    else if (rig) rig.body.enabled = cameraDistance >= 1.4;
  }
  function project(point: XYZ): ScreenPoint {
    const rect = canvas.getBoundingClientRect(), position = camera.getPosition();
    const front = (point.x - position.x) * cameraForward.x + (point.y - position.y) * cameraForward.y + (point.z - position.z) * cameraForward.z;
    camera.camera!.worldToScreen(temp.set(point.x, point.y, point.z), screen);
    return { x: screen.x, y: screen.y, visible: front > .12 && screen.x >= 0 && screen.x <= rect.width && screen.y >= 0 && screen.y <= rect.height };
  }
  const resize = () => { const rect = canvas.getBoundingClientRect(); if (rect.width && rect.height) app.resizeCanvas(rect.width, rect.height); };
  const observer = new ResizeObserver(resize); observer.observe(canvas);
  function setQuality(next: 'low' | 'high') {
    quality = next; app.graphicsDevice.maxPixelRatio = next === 'low' ? .65 : Math.min(window.devicePixelRatio || 1, 1.5);
    sunlight.light!.castShadows = next === 'high'; resize();
    for (const rig of rigs.values()) rig.model?.setShadows(next === 'high');
  }
  setQuality('high'); kit.app.batcher.generate(); app.start();

  return {
    update(snapshot, localId, frameDt) {
      if (destroyed) return;
      const dt = clamp(Number.isFinite(frameDt) ? frameDt : 0, 0, .1); elapsed += dt;
      lastSnapshot = snapshot; playerId = localId;
      if (snapshot) {
        const nextEpoch = `${snapshot.room}/${localId ?? ''}`;
        if (nextEpoch !== epoch || snapshot.tick < lastTick) {
          epoch = nextEpoch; eventId = -1; baselineEvents = true; initialized = false;
          // A replay can reuse actor/effect IDs with fresh event counters and different heroes.
          // Recreate private skeleton state while retaining the shared loaded GLB resources.
          for (const rig of rigs.values()) { rig.model?.destroy(); rig.root.destroy(); rig.shadow.destroy(); }
          rigs.clear();
          for (const { rig } of corpses) { rig.model?.destroy(); rig.root.destroy(); rig.shadow.destroy(); } corpses.length = 0;
          releaseRemoved(projectileViews, new Set(), projectilePool);
          releaseRemoved(zoneViews, new Set(), zonePool);
          castEffects.destroy();
          jungle.reset();
          for (const burst of bursts) { burst.until = 0; burst.root.enabled = false; }
        }
        lastTick = snapshot.tick;
        const aliveIds = new Set(snapshot.actors.map(a => a.id));
        for (const [id, rig] of rigs) if (!aliveIds.has(id)) {
          const defeated = !baselineEvents && rig.unitId && snapshot.events.some(e => e.id > eventId && e.type === 'defeat' && e.targetId === id && snapshot.time - e.time <= .7);
          if (defeated && corpses.length < 24) {
            // A short, untargetable visual remainder; authority has already removed this unit.
            corpses.push({ rig, until: elapsed + 1.1, actor: { ...rig.lastActor, health: 0, respawn: 1 } });
          } else { rig.model?.destroy(); rig.root.destroy(); rig.shadow.destroy(); }
          rigs.delete(id);
        }
        for (const actor of snapshot.actors) {
          let rig = rigs.get(actor.id);
          if (rig && rig.tag !== rigTag(actor)) { rig.model?.destroy(); rig.root.destroy(); rig.shadow.destroy(); rigs.delete(actor.id); rig = undefined; }
          if (!rig) { rig = makeRig(actor); rigs.set(actor.id, rig); }
          updateRig(rig, actor, dt, actor.id === localId);
        }
        consumeEvents(snapshot);
        castEffects.update(snapshot, localId, reducedMotion);
        jungle.update(snapshot, localId, dt, { yaw, reducedMotion, quality, elapsed });
        for (const s of snapshot.structures) {
          let visual = buildings.get(s.id); if (!visual) { visual = makeStructure(s); buildings.set(s.id, visual); }
          visual.intact.enabled = s.health > 0; visual.crystal.enabled = s.health > 0; visual.shield.enabled = s.shielded && s.health > 0; visual.frame.enabled = s.health > 0; visual.shattered.enabled = s.health <= 0;
          visual.root.setPosition(s.x, 0, s.z);
          if (!reducedMotion) { visual.crystal.setLocalEulerAngles(0, elapsed * 24, 0); visual.shield.setLocalEulerAngles(0, -elapsed * 12, 0); }
          visual.frame.setEulerAngles(0, yaw * RAD + 180, 0);
          const ratio = clamp(s.health / s.maxHealth, 0, 1); visual.health.setLocalScale(2.1 * Math.max(.001, ratio), .08, .035); visual.health.setLocalPosition(-2.1 * (1 - ratio) / 2, 0, .03);
        }
        const structureIds = new Set(snapshot.structures.map(s => s.id));
        for (const [id, v] of buildings) if (!structureIds.has(id)) { v.root.destroy(); buildings.delete(id); }
        releaseRemoved(projectileViews, new Set(snapshot.projectiles.map(p => p.id)), projectilePool);
        for (const p of snapshot.projectiles) {
          const owner = snapshot.actors.find(a => a.id === p.owner), weapon = owner?.kind === 'hero' ? heroById(owner.heroId).weapon : owner?.minionRole === 'siege' ? 'mace' : 'staff';
          let v = projectileViews.get(p.id); if (!v) { v = projectileVisual(`${p.color}/${weapon}`); projectileViews.set(p.id, v); }
          v.root.setPosition(p.x, p.y, p.z); v.root.setEulerAngles(-Math.atan2(p.vy, Math.hypot(p.vx, p.vz)) * RAD, Math.atan2(p.vx, p.vz) * RAD, 0);
          const scale = Math.max(.7, Math.min(2, p.radius * 3)); v.root.setLocalScale(scale, scale, scale);
        }
        releaseRemoved(zoneViews, new Set(snapshot.zones.map(z => z.id)), zonePool);
        for (const z of snapshot.zones) {
          const owner = snapshot.actors.find(a => a.id === z.owner), localTeam = snapshot.actors.find(a => a.id === localId)?.team;
          const ability = owner ? heroById(owner.heroId).abilities.find(a => a.kind === z.kind && a.color === z.color) : undefined;
          const radius = ['cone', 'burst'].includes(z.kind) ? ability?.range ?? z.radius : z.radius;
          let v = zoneViews.get(z.id); if (!v) { v = zoneVisual(`${z.color}/${z.team}/${z.kind}/${z.mechanic ?? ''}/${z.team === localTeam ? 'friendly' : 'hostile'}`); zoneViews.set(z.id, v); }
          v.root.setPosition(z.x, 0, z.z); v.root.setLocalScale(radius, 1, radius);
          v.root.setLocalEulerAngles(0, (z.yaw ?? 0) * RAD, 0);
        }
        for (const pickup of snapshot.pickups) {
          let v = pickupViews.get(pickup.id);
          if (!v) {
            v = group(root, `pickup ${pickup.kind}`, pickup.x, 0, pickup.z);
            const color = kit.material(`pickup ${pickup.kind}`, pickup.kind === 'vigor' ? '#a4f1b7' : pickup.kind === 'haste' ? '#ffe098' : '#9ce7ff', .8);
            kit.ring(v, color, .8, .07, .05, 24);
            const crystal = group(v, 'pickup crystal', 0, 1, 0);
            kit.shape(crystal, 'cone', color, 0, .2, 0, .65, .5, .65);
            kit.shape(crystal, 'cone', color, 0, -.3, 0, .65, .5, .65).setLocalEulerAngles(180, 0, 0);
            pickupViews.set(pickup.id, v);
          }
          v.enabled = pickup.readyAt <= snapshot.time;
          v.setPosition(pickup.x, 0, pickup.z);
          const crystal = v.children[1] as pc.Entity;
          crystal.setLocalPosition(0, reducedMotion ? 1 : 1 + Math.sin(elapsed * 2.2) * .13, 0);
          if (!reducedMotion) crystal.setLocalEulerAngles(0, elapsed * 50, 0);
        }
      }
      for (let i = corpses.length - 1; i >= 0; i--) {
        const corpse = corpses[i]!;
        if (elapsed >= corpse.until) { corpse.rig.model?.destroy(); corpse.rig.root.destroy(); corpse.rig.shadow.destroy(); corpses.splice(i, 1); }
        else updateRig(corpse.rig, corpse.actor, dt, false);
      }
      for (const fx of bursts) {
        fx.root.enabled = fx.until > elapsed; if (!fx.root.enabled) continue;
        const age = elapsed - fx.born, radius = reducedMotion ? .45 : .2 + age * 4;
        fx.ring.setLocalScale(radius, 1, radius);
        for (let i = 0; i < fx.sparks.length; i++) { const a = i / fx.sparks.length * Math.PI * 2; fx.sparks[i]!.enabled = !reducedMotion && quality === 'high'; fx.sparks[i]!.setLocalPosition(Math.sin(a) * radius, age * 2, Math.cos(a) * radius); }
      }
      positionCamera(snapshot?.actors.find(a => a.id === localId), dt);
      scenery.sky.setPosition(camera.getPosition());
    },
    setCamera(nextYaw, nextPitch) { if (Number.isFinite(nextYaw)) yaw = nextYaw; if (Number.isFinite(nextPitch)) pitch = clamp(nextPitch, -1.1, 1.1); },
    setQuality,
    setActive(enabled) { if (enabled && !active) { baselineEvents = true; jungle.baselineEvents(); } active = enabled; app.autoRender = enabled; app.renderNextFrame = enabled; heroModels.setActive(enabled); unitModels.setActive(enabled); },
    resetEventHistory() { baselineEvents = true; jungle.baselineEvents(); },
    setReducedMotion(enabled) { reducedMotion = enabled; },
    setOverview(enabled) { if (overview !== enabled) { overview = enabled; initialized = false; } },
    project,
    preloadHeroes: (ids, progress) => heroModels.preload(ids, progress),
    preloadUnits: progress => unitModels.preload(progress),
    assetDiagnostics: () => ({ ...heroModels.diagnostics(), fallback: [...rigs.entries()].filter(([, rig]) => !rig.model && rig.tag.startsWith('hero/')).map(([id, rig]) => ({ id, heroId: rig.heroId })), casts: castEffects.diagnostic(),
      units: { ...unitModels.diagnostics(), fallback: [...[...rigs.entries()].filter(([, rig]) => !rig.model && rig.unitId).map(([id, rig]) => ({ id, unitId: rig.unitId! })), ...jungle.diagnostics().fallback] }, jungle: jungle.diagnostics() }),
    reticle() {
      const actor = lastSnapshot?.actors.find(a => a.id === playerId); if (!actor || overview || actor.health <= 0) return null;
      const aimYaw = actor.cast?.yaw ?? yaw, aimPitch = actor.cast?.pitch ?? pitch;
      return project({ x: actor.x + Math.sin(aimYaw) * Math.cos(aimPitch) * 25, y: actor.y + 1.2 + Math.sin(aimPitch) * 25, z: actor.z + Math.cos(aimYaw) * Math.cos(aimPitch) * 25 });
    },
    destroy() {
      if (destroyed) return; destroyed = true; observer.disconnect();
      // Dispose cached GPU resources while the device is alive; app.destroy clears its GL context.
      castEffects.destroy(); jungle.destroy(); unitModels.destroy(); heroModels.destroy(); root.destroy(); kit.dispose(); environment.destroy(); app.destroy();
    },
  };
}
