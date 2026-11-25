import * as pc from 'playcanvas';
import { RenderKit, RAD, clamp, mixAngle } from '../../yuga/client/render-kit';
import { makeArmyScene, setMaterial } from './army-scene';
import { GROOM_MATERIAL, groomVisible, projectedHanumanHeight, verticalFocalPixels } from './groom-detail';
import { cameraObstaclesFromMap, resolveChaseCamera } from './camera-clearance';
import { createOriginalEnvironment } from '../../yuga/client/environment-light';

type Assets = {
  hero: string;
  rama?: string;
  vehicles?: string;
  soldier: string;
  architecture: string;
  nature: string;
  mountain?: string;
};
type Point = [number, number];
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const angle = (p: Point) => Math.atan2(p[0], p[1]);

function loadGlb(app: pc.Application, url: string, name: string): Promise<pc.ContainerResource> {
  return new Promise((resolve, reject) => {
    app.assets.loadFromUrlAndFilename(url, name + '.glb', 'container', (err, asset) => {
      if (err || !asset?.resource) reject(new Error(name + ': ' + (err || 'missing GLB')));
      else resolve(asset.resource);
    });
  });
}

function figure(container: pc.ContainerResource, parent: pc.Entity, findGroom = false) {
  const model = container.instantiateRenderEntity({ castShadows: true, receiveShadows: true });
  parent.addChild(model);
  model.addComponent('anim', { activate: true });
  const anim = model.anim!;
  const tracks = new Map<string, pc.AnimTrack>();
  for (const asset of container.animations) {
    const track = asset.resource;
    if (!(track instanceof pc.AnimTrack)) continue;
    const name = track.name
      .split('|')
      .at(-1)!
      .replace(/\.\d+$/, '')
      .toLowerCase();
    tracks.set(name, track);
    anim.assignAnimation(name, track, undefined, 1, name === 'idle' || name === 'run');
  }
  const skinned = (model.findComponents('render') as pc.RenderComponent[])
    .flatMap((part) => part.meshInstances)
    .filter((mesh) => mesh.skinInstance);
  const bones = new Set(skinned.flatMap((mesh) => mesh.skinInstance!.bones));
  if (!bones.size || !tracks.has('idle')) throw new Error('Rig or idle clip missing from ' + model.name);
  const layer = anim.baseLayer;
  if (!layer) throw new Error('Missing animation layer on ' + model.name);
  layer.play('idle');
  const groom = findGroom ? skinned.find((mesh) => mesh.material?.name === GROOM_MATERIAL) : undefined;
  return { model, anim, layer, tracks, bones, groom, surfaces: skinned.length, clip: 'idle' };
}

function buildMap(
  app: pc.Application,
  kit: RenderKit,
  map: any,
  architecture: pc.ContainerResource,
  nature: pc.ContainerResource
) {
  const world = new pc.Entity('Confluence', app);
  app.root.addChild(world);
  const stone = kit.material('sandstone', '#9f8768'),
    brass = kit.material('inlay brass', '#c7a05d', 0.16);
  const ink = kit.material('basalt', '#536665'),
    water = kit.material('water', '#376960', 0, 0.8);
  const tileTexture = kit.texture('cut sandstone pavers', 256, 256, (ctx) => {
    ctx.fillStyle = '#807765';
    ctx.fillRect(0, 0, 256, 256);
    for (let row = 0; row < 4; row++)
      for (let col = -1; col < 3; col++) {
        const x = col * 128 + (row % 2) * 64,
          z = row * 64;
        const tone = (row * 7 + ((col + 2) % 2) * 3) % 13;
        ctx.fillStyle = 'rgb(' + [176 + tone, 163 + tone, 140 + tone].join(',') + ')';
        ctx.fillRect(x + 1, z + 1, 126, 62);
        ctx.fillStyle = '#c4b9a2';
        ctx.fillRect(x + 1, z + 1, 125, 1);
      }
  });
  const ground = kit.material('packed earth', '#9d9481');
  const [x0, x1, z0, z1] = map.bounds.nominal_xz;
  kit.shape(world, 'plane', ground, (x0 + x1) / 2, -0.012, (z0 + z1) / 2, x1 - x0, 1, z1 - z0, true);
  function ribbon(a: number[], b: number[], width: number) {
    const dx = b[0] - a[0],
      dz = b[2] - a[2],
      length = Math.hypot(dx, dz),
      yaw = Math.atan2(dx, dz);
    const paving = kit.material('paved avenue ' + width + '/' + length, '#ffffff');
    paving.diffuseMap = tileTexture;
    paving.diffuseMapTiling.set(width / 3, length / 3);
    paving.update();
    const x = (a[0] + b[0]) / 2,
      z = (a[2] + b[2]) / 2;
    kit
      .shape(world, 'plane', paving, x, 0.002, z, width, 1, length, true)
      .setEulerAngles(0, yaw * RAD, 0);
    for (const side of [-1, 1]) {
      const offset = side * (width / 2 - 0.12);
      kit
        .shape(
          world,
          'plane',
          brass,
          x + Math.cos(yaw) * offset,
          0.005,
          z - Math.sin(yaw) * offset,
          0.085,
          1,
          length,
          true
        )
        .setEulerAngles(0, yaw * RAD, 0);
    }
  }
  for (const lane of map.lanes)
    for (let i = 1; i < lane.points.length; i++)
      ribbon(lane.points[i - 1], lane.points[i], 2 * lane.clear_half_width);
  for (const w of map.waters)
    kit.shape(
      world,
      'plane',
      water,
      w.position[0],
      w.position[1],
      w.position[2],
      w.size_xz[0],
      1,
      w.size_xz[1],
      true
    );

  const kits = [architecture, nature].map((c) => c.instantiateRenderEntity());
  const solidIds: string[] = [];
  for (const p of map.props) {
    const [x, y, z] = p.position,
      [sx, sy, sz] = p.scale;
    if (p.kit === 'ground_inlay') {
      const root = new pc.Entity(p.id, app);
      world.addChild(root);
      root.setLocalPosition(x, y, z);
      root.setLocalEulerAngles(0, p.yaw_degrees, 0);
      const radius = sx * 0.46;
      const material = p.preset === 'moon_lotus' || p.preset === 'ghat_wave' ? ink : brass;
      kit.ring(root, material, radius, 0.09, 0, 44, true);
      kit.ring(root, material, radius * 0.77, 0.045, 0, 44, true);
      for (let i = 0; i < 8; i++) {
        const theta = (i * Math.PI) / 4;
        const mark = kit.shape(
          root,
          'plane',
          material,
          Math.sin(theta) * radius * 0.43,
          0.002,
          Math.cos(theta) * radius * 0.43,
          0.095,
          1,
          radius * 0.56,
          true
        );
        mark.setLocalEulerAngles(0, theta * RAD + (p.preset === 'ghat_wave' ? 28 : 0), 0);
      }
    } else {
      const source = kits.map((root) => root.findByName(p.preset)).find(Boolean) as
        | pc.Entity
        | undefined;
      if (!source) throw new Error('Map prefab missing: ' + p.preset);
      const instance = source.clone();
      world.addChild(instance);
      instance.name = p.id;
      instance.setLocalPosition(x, y, z);
      instance.setLocalEulerAngles(0, p.yaw_degrees, 0);
      instance.setLocalScale(sx, sy, sz);
      for (const component of instance.findComponents('render') as pc.RenderComponent[])
        component.batchGroupId = kit.staticGroup;
    }
    if (p.authority_collision_id) solidIds.push(p.authority_collision_id);
  }
  kits.forEach((root) => root.destroy());
  for (const deck of map.traversal.native_collision_boxes) {
    const [x, y, z] = deck.position,
      [w, h, d] = deck.size;
    kit.shape(world, 'box', stone, x, y + h / 2, z, w, h, d, true);
    kit.shape(world, 'box', ink, x, y + h - 0.32, z, w + 0.012, 0.48, d + 0.012, true);
    kit.shape(world, 'box', brass, x, y + h - 0.08, z, w + 0.02, 0.08, d + 0.02, true);
    kit
      .ring(world, brass, Math.min(w, d) * 0.32, 0.09, 0.025, 30, true)
      .setPosition(x, y + h + 0.015, z);
    solidIds.push(deck.id);
  }
  return solidIds;
}

// A deliberately spectral, painted effect card, shared by every active cast in
// this scene. It is presentation only: the server resolves the disk's damage.
const senaTexture = new WeakMap<RenderKit, pc.Texture>();
function guardianTexture(kit: RenderKit) {
  const cached = senaTexture.get(kit);
  if (cached) return cached;
  const texture = kit.texture('Vanara Sena · painted spirit', 256, 384, (ctx) => {
    ctx.clearRect(0, 0, 256, 384);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const gold = ctx.createLinearGradient(0, 25, 0, 370);
    gold.addColorStop(0, '#ffda91'); gold.addColorStop(.45, '#db792f'); gold.addColorStop(1, '#a44716');
    ctx.strokeStyle = gold; ctx.fillStyle = gold; ctx.shadowColor = '#ffba54'; ctx.shadowBlur = 9;
    const outline = 'rgba(112,43,11,.86)';
    function outlinedFill() {
      ctx.save(); ctx.shadowBlur = 0; ctx.strokeStyle = outline; ctx.lineWidth = 5; ctx.stroke(); ctx.restore();
      ctx.fill();
    }
    function outlinedStroke(width: number) {
      ctx.save(); ctx.shadowBlur = 0; ctx.strokeStyle = outline; ctx.lineWidth = width + 5; ctx.stroke(); ctx.restore();
      ctx.lineWidth = width; ctx.stroke();
    }
    // Curved tail and a small gada remain recognizable at the game camera.
    ctx.lineWidth = 9;
    ctx.beginPath(); ctx.moveTo(104, 226); ctx.bezierCurveTo(51, 250, 32, 210, 48, 181);
    ctx.bezierCurveTo(58, 163, 74, 166, 76, 182); outlinedStroke(9);
    ctx.lineWidth = 8;
    ctx.beginPath(); ctx.moveTo(177, 143); ctx.lineTo(207, 75); outlinedStroke(8);
    ctx.beginPath(); ctx.ellipse(210, 67, 13, 18, .3, 0, Math.PI * 2); outlinedFill();
    // Crown, head and muzzle form a single soft outline, rather than a box figure.
    ctx.beginPath(); ctx.moveTo(98, 72); ctx.bezierCurveTo(93, 47, 104, 29, 128, 30);
    ctx.bezierCurveTo(150, 29, 161, 45, 158, 65); ctx.bezierCurveTo(169, 70, 168, 82, 156, 86);
    ctx.bezierCurveTo(147, 103, 110, 104, 100, 85); ctx.closePath(); outlinedFill();
    ctx.beginPath(); ctx.ellipse(96, 74, 9, 13, -.3, 0, Math.PI * 2); outlinedFill();
    ctx.beginPath(); ctx.ellipse(160, 74, 9, 13, .3, 0, Math.PI * 2); outlinedFill();
    // One flowing silhouette for shoulders, arms, waist, legs and feet.
    ctx.beginPath(); ctx.moveTo(113, 101); ctx.bezierCurveTo(92, 102, 79, 112, 73, 131);
    ctx.lineTo(58, 178); ctx.quadraticCurveTo(55, 190, 65, 193); ctx.quadraticCurveTo(75, 194, 79, 181);
    ctx.lineTo(94, 147); ctx.lineTo(100, 209); ctx.lineTo(92, 244); ctx.lineTo(101, 279);
    ctx.lineTo(91, 335); ctx.quadraticCurveTo(88, 348, 100, 349); ctx.quadraticCurveTo(113, 349, 116, 338);
    ctx.lineTo(128, 287); ctx.lineTo(139, 338); ctx.quadraticCurveTo(143, 349, 156, 349);
    ctx.quadraticCurveTo(168, 348, 165, 335); ctx.lineTo(155, 279); ctx.lineTo(164, 244);
    ctx.lineTo(155, 209); ctx.lineTo(162, 147); ctx.lineTo(176, 162);
    ctx.quadraticCurveTo(184, 170, 191, 162); ctx.quadraticCurveTo(196, 155, 188, 147);
    ctx.lineTo(173, 122); ctx.quadraticCurveTo(160, 104, 143, 101); ctx.closePath(); outlinedFill();
    ctx.shadowBlur = 0;
    // Fine dark-gold edges separate face, armor and dhoti inside the luminous outline.
    ctx.strokeStyle = 'rgba(118,52,18,.78)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(108, 77); ctx.quadraticCurveTo(128, 70, 148, 77);
    ctx.moveTo(115, 90); ctx.quadraticCurveTo(128, 93, 141, 90);
    ctx.moveTo(104, 133); ctx.quadraticCurveTo(128, 143, 153, 133);
    ctx.moveTo(101, 205); ctx.quadraticCurveTo(128, 216, 155, 205);
    ctx.moveTo(108, 231); ctx.lineTo(129, 252); ctx.lineTo(149, 231); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,245,210,.8)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(128, 48); ctx.lineTo(128, 65); ctx.stroke();
  });
  senaTexture.set(kit, texture);
  return texture;
}

// One static mesh replaces the twelve independently rendered disk tick marks.
function makeSenaMarks(kit: RenderKit, root: pc.Entity, material: pc.Material, radius: number) {
  const positions: number[] = [], normals: number[] = [], indices: number[] = [];
  for (let i = 0; i < 12; i++) {
    const theta = i * Math.PI / 6, s = Math.sin(theta), c = Math.cos(theta);
    const x = s * (radius - .28), z = c * (radius - .28), first = positions.length / 3;
    for (const [side, forward] of [[-.06, -.26], [.06, -.26], [.06, .26], [-.06, .26]]) {
      positions.push(x + c * side + s * forward, .034, z - s * side + c * forward);
      normals.push(0, 1, 0);
    }
    indices.push(first, first + 2, first + 1, first, first + 3, first + 2);
  }
  const mesh = pc.createMesh(kit.app.graphicsDevice, positions, { normals, indices });
  const marks = new pc.Entity('Vanara Sena · radial markers', kit.app);
  root.addChild(marks);
  marks.addComponent('render', { meshInstances: [new pc.MeshInstance(mesh, material)],
    castShadows: false, receiveShadows: true });
}

function makeTelegraph(kit: RenderKit, rule: any, seat: string, mountainSource: pc.Entity) {
  const root = new pc.Entity(rule.id, kit.app);
  kit.app.root.addChild(root);
  // Double-sided ribbons remain visible for oblique cameras and both winding orders.
  const material = kit.material(seat + rule.id, '#' + rule.color, 0.75, 0.25, 0.82);
  material.cull = pc.CULLFACE_NONE;
  material.update();
  const g = rule.geometry,
    radius = g.range_m ?? g.radius_m ?? 0.65;
  const half = g.kind === 'sector' ? Math.acos(g.half_angle_cos) : Math.PI;
  let outline: pc.StandardMaterial | null = null;
  if (rule.id === 'vanara_sena') {
    // A narrow dark underlay separates the golden danger boundary from pale ground.
    outline = kit.material(seat + ' sena boundary', '#873a12', 0.08, 0.25, 0.86);
    outline.cull = pc.CULLFACE_NONE;
    outline.update();
    kit.arc(root, outline, radius, 0.25, 0.027, -half, half, 56);
  }
  kit.arc(root, material, radius, 0.095, 0.032, -half, half, 56);
  const wave = kit.arc(root, material, radius, 0.135, 0.042, -half, half, 48);
  if (g.kind === 'sector')
    for (const side of [-1, 1]) {
      const a = half * side;
      const edge = kit.shape(
        root,
        'plane',
        material,
        Math.sin(a) * radius * 0.5,
        0.031,
        Math.cos(a) * radius * 0.5,
        0.056,
        1,
        radius
      );
      edge.setLocalEulerAngles(0, a * RAD, 0);
    }
  if (g.kind === 'disk' && rule.id === 'vanara_sena') {
    makeSenaMarks(kit, root, material, radius);
  } else if (g.kind === 'disk')
    for (let i = 0; i < 12; i++) {
      const a = (i * Math.PI) / 6;
      kit
        .shape(
          root,
          'plane',
          material,
          Math.sin(a) * (radius - 0.28),
          0.034,
          Math.cos(a) * (radius - 0.28),
          0.12,
          1,
          0.52
        )
        .setLocalEulerAngles(0, a * RAD, 0);
    }
  const trail =
    g.kind === 'movement' ? kit.shape(root, 'plane', material, 0, 0.04, 0, 0.13, 1, 1) : null;
  let mote: pc.Entity | null = null;
  const impactSparks: pc.Entity[] = [];
  const senaSpirits: pc.Entity[] = [];
  if (rule.id === 'mountain_pulse') {
    // Reuse the bundled rock for the visual projectile, without a physics body.
    mote = mountainSource.clone();
    mote.name = 'Mountain Pulse · airborne rock';
    root.addChild(mote);
    mote.setLocalScale(0.72, 0.65, 0.72);
    for (const part of mote.findComponents('render') as pc.RenderComponent[])
      part.castShadows = false;
    kit.ring(mote, material, 0.65, 0.055, 0.18, 32);
    mote.enabled = false;
    for (let i = 0; i < 6; i++) {
      const spark = kit.shape(root, 'sphere', material, 0, 0, 0, 0.12, 0.12, 0.12);
      spark.name = 'Mountain Pulse · impact spark ' + (i + 1);
      spark.render!.castShadows = false;
      spark.enabled = false;
      impactSparks.push(spark);
    }
  }
  if (rule.id === 'vanara_sena') {
    const texture = guardianTexture(kit);
    const spirit = kit.material(seat + ' sena spirit', '#ffffff', 0.45, 0.15, 0.72);
    spirit.diffuseMap = texture;
    spirit.emissiveMap = texture;
    spirit.opacityMap = texture;
    spirit.opacityMapChannel = 'a';
    spirit.useLighting = false;
    spirit.cull = pc.CULLFACE_NONE;
    spirit.update();
    for (let i = 0; i < 5; i++) {
      const guardian = kit.shape(root, 'plane', spirit, 0, 0, 0, .84, 1, 1.28);
      guardian.name = 'Vanara Sena · spectral guardian ' + (i + 1);
      guardian.render!.castShadows = false;
      guardian.render!.receiveShadows = false;
      guardian.enabled = false;
      senaSpirits.push(guardian);
    }
  }
  root.enabled = false;
  return { root, wave, material, outline, trail, mote, impactSparks, senaSpirits, geometry: g };
}

export async function makeScene(
  canvas: HTMLCanvasElement,
  assets: Assets,
  map: any,
  rules: any,
  ramaKit?: any
) {
  const app = new pc.Application(canvas, {
    graphicsDeviceOptions: { alpha: false, antialias: true, powerPreference: 'high-performance' }
  });
  app.graphicsDevice.maxPixelRatio = Math.min(window.devicePixelRatio || 1, 1.4);
  app.setCanvasResolution(pc.RESOLUTION_AUTO);
  const resize = () => {
    app.updateCanvasSize();
    app.graphicsDevice.updateClientRect();
  };
  resize();
  const [hanuman, soldier, architecture, nature, rama, vehicles, mountain] = await Promise.all([
    loadGlb(app, assets.hero, 'hanuman'),
    loadGlb(app, assets.soldier, 'soldier'),
    loadGlb(app, assets.architecture, 'architecture'),
    loadGlb(app, assets.nature, 'nature'),
    assets.rama ? loadGlb(app, assets.rama, 'rama') : undefined,
    assets.vehicles ? loadGlb(app, assets.vehicles, 'native-army') : undefined,
    assets.mountain ? loadGlb(app, assets.mountain, 'mountain-rock') : undefined
  ]);
  const mountainCatalog = (mountain ?? nature).instantiateRenderEntity();
  app.root.addChild(mountainCatalog);
  mountainCatalog.enabled = false;
  const mountainCandidate = mountainCatalog.findByName(
    mountain ? 'rock_face_01_compact' : 'rock_island'
  ) as pc.Entity | null;
  if (!mountainCandidate) throw new Error('Mountain visual is missing its rock prefab');
  const mountainSource: pc.Entity = mountainCandidate;
  const kit = new RenderKit(app);
  const cameraObstacles = cameraObstaclesFromMap(map);
  createOriginalEnvironment(app);
  app.scene.ambientLight = new pc.Color(0.48, 0.45, 0.42);
  const camera = new pc.Entity('Trial camera', app);
  app.root.addChild(camera);
  camera.addComponent('camera', {
    fov: 48,
    nearClip: 0.12,
    farClip: 250,
    clearColor: new pc.Color(0.71, 0.73, 0.7)
  });
  const sun = new pc.Entity('Courtyard sunlight', app);
  app.root.addChild(sun);
  sun.addComponent('light', {
    type: 'directional',
    color: new pc.Color(1, 0.91, 0.78),
    intensity: 1.38,
    castShadows: true,
    shadowResolution: 1024,
    shadowDistance: 34,
    shadowBias: 0.12,
    normalOffsetBias: 0.03
  });
  sun.setEulerAngles(49, 138, 0);
  const fill = new pc.Entity('Sky bounce', app);
  app.root.addChild(fill);
  fill.addComponent('light', {
    type: 'directional',
    color: new pc.Color(0.65, 0.81, 0.99),
    intensity: 0.56
  });
  fill.setEulerAngles(38, -35, 0);

  const visualSolidIds = buildMap(app, kit, map, architecture, nature);
  const armyView = makeArmyScene(kit, map, vehicles);
  const resources: { [key: string]: pc.ContainerResource | undefined } = { hanuman, rama };
  const localRigs = new Map<string, ReturnType<typeof makeRig>>();
  const teamColors = { sun: '#f3b568', moon: '#74d4ef' };
  const sunMarker = kit.material('Sun hero', teamColors.sun, 0.48),
    moonMarker = kit.material('Moon hero', teamColors.moon, 0.58),
    vitalsBacking = kit.material('Hero vitals', '#142522');
  const localRing = kit.ring(app.root, sunMarker, 0.66, 0.065, 0.03, 32);
  localRing.enabled = false;
  const mountainRule = rules.abilities.find((rule: any) => rule.id === 'mountain_pulse');
  const aimFootprint = new pc.Entity('Mountain Pulse targeting', app);
  app.root.addChild(aimFootprint);
  const eligible = kit.material('Clear pulse aim', '#ffe5a1', 0.8);
  const rejected = kit.material('Blocked pulse aim', '#ff8475', 0.8);
  const area = kit.arc(aimFootprint, eligible, mountainRule.geometry.radius_m, 0.09, 0.065, -Math.PI, Math.PI, 64);
  const center = kit.ring(aimFootprint, eligible, 0.24, 0.07, 0.067, 24);
  const cross = new pc.Entity('Unavailable ground', app);
  aimFootprint.addChild(cross);
  for (const angle of [-45, 45])
    kit.shape(cross, 'plane', rejected, 0, 0.07, 0, 0.12, 1, 0.84).setLocalEulerAngles(0, angle, 0);
  aimFootprint.enabled = false;
  let targeting: { position: Point; clear: boolean; radius: number } | null = null;

  function showGroundAim(at: Point | null, clear = false, radius = mountainRule.geometry.radius_m) {
    aimFootprint.enabled = at !== null;
    if (!at) { targeting = null; return; }
    aimFootprint.setPosition(at[0], 0, at[1]);
    radius = Number.isFinite(radius) && radius > 0 ? radius : mountainRule.geometry.radius_m;
    targeting = { position: [at[0], at[1]], clear, radius };
    const footprintScale = radius / mountainRule.geometry.radius_m;
    area.setLocalScale(footprintScale, 1, footprintScale);
    center.enabled = clear;
    cross.enabled = !clear;
    setMaterial(area, clear ? eligible : rejected);
  }
  function makeRig(id: string, remote = false) {
    const resource = resources[id];
    if (!resource) throw new Error('Unbundled hero: ' + id);
    const holder = new pc.Entity(id + ' feet', app);
    app.root.addChild(holder);
    const rig = figure(resource, holder, remote && id === 'hanuman');
    const nodes = [
      'spine03',
      'upperarm01.R',
      'lowerarm01.R',
      'wrist.R',
      'upperleg01.L',
      'tail_02',
      'bowstring'
    ]
      .map((n) => rig.model.findByName(n))
      .filter((n): n is pc.GraphNode => !!n);
    return {
      ...rig,
      holder,
      nodes,
      id,
      yaw: 0,
      phase: 0,
      bowstring: rig.model.findByName('bowstring'),
      grip: rig.model.findByName('wrist.R')
    };
  }
  function selectRig(rigs: typeof localRigs, id: string) {
    let chosen = rigs.get(id);
    if (!chosen) {
      chosen = makeRig(id);
      rigs.set(id, chosen);
    }
    for (const r of rigs.values()) r.holder.enabled = r === chosen;
    return chosen;
  }
  let hero = selectRig(localRigs, 'hanuman');
  let cameraFraction = 1;
  let cameraFov = 48;
  let cameraClearance: ReturnType<typeof resolveChaseCamera> | null = null;
  for (const rule of rules.abilities)
    if (!hero.tracks.has(rule.motion)) throw new Error('Missing Hanuman stage ' + rule.motion);
  function poseRig(
    rig: ReturnType<typeof makeRig>,
    state: any,
    prev: any,
    t: number,
    dt: number,
    reset: boolean
  ) {
    const a = state.actor,
      b = prev.actor;
    const x = lerp(b.pos[0], a.pos[0], t),
      y = lerp(b.y ?? 0, a.y ?? 0, t),
      z = lerp(b.pos[1], a.pos[1], t);
    const active = state.active,
      moving = (a.pos[0] - b.pos[0]) ** 2 + (a.pos[1] - b.pos[1]) ** 2 > 1e-8;
    const clip = a.hp <= 0 ? 'defeat' : (active?.motion ?? (moving ? 'run' : 'idle'));
    if (!rig.tracks.has(clip)) throw new Error('Missing ' + rig.id + ' animation ' + clip);
    if (clip !== rig.clip || reset) {
      rig.layer.play(clip);
      rig.clip = clip;
    }
    if (active && a.hp > 0) {
      const current = active.motion_phase_normalized;
      const old =
        prev.active?.cast_id === active.cast_id && prev.active.motion === active.motion
          ? prev.active.motion_phase_normalized
          : current;
      rig.phase = lerp(old, current, t);
      rig.anim.speed = 0;
      rig.layer.activeStateCurrentTime = rig.phase * rig.tracks.get(clip)!.duration;
    } else rig.anim.speed = 1;
    const targetYaw = angle(active?.aim ?? a.aim);
    rig.yaw = reset ? targetYaw : mixAngle(rig.yaw, targetYaw, Math.min(1, Math.max(dt, 0) * 18));
    rig.holder.setLocalPosition(x, y, z);
    rig.holder.setLocalEulerAngles(0, rig.yaw * RAD, 0);
    return { x, y, z };
  }
  const friendly = kit.material('sun jade', '#6ee7be', 0.45),
    hostile = kit.material('moon vermilion', '#f27b62', 0.45);
  const backing = kit.material('status backing', '#293534');
  const soldierActors = new Map<number, ReturnType<typeof makeSoldier>>();
  function makeSoldier(unit: any) {
    const root = new pc.Entity('Soldier ' + unit.id, app);
    app.root.addChild(root);
    const skin = figure(soldier, root);
    const material = unit.team === 'sun' ? friendly : hostile;
    kit.ring(root, material, 0.49, 0.057, 0.024, 30);
    const bar = kit.shape(root, 'box', backing, 0, 2.12, 0, 0.82, 0.1, 0.042);
    const hp = kit.shape(root, 'box', material, 0, 2.122, -0.025, 0.77, 0.057, 0.018);
    bar.render!.castShadows = hp.render!.castShadows = false;
    return { root, skin, hp, bar };
  }
  const groundRules = new Map<string, any>(rules.abilities.map((r: any) => [r.id, r]));
  for (const r of ramaKit?.abilities ?? []) {
    if (r.id === 'guardian_circle')
      groundRules.set(r.id, { ...r, geometry: { kind: 'disk', radius_m: r.radius_m } });
    if (r.id === 'measured_step')
      groundRules.set(r.id, { ...r, geometry: { kind: 'movement', target_range_m: r.range_m } });
  }
  function prepareSena(effects: { seat: string; areas: Map<string, ReturnType<typeof makeTelegraph>> }) {
    const sena = groundRules.get('vanara_sena');
    if (sena && !effects.areas.has(sena.id))
      effects.areas.set(sena.id, makeTelegraph(kit, sena, effects.seat, mountainSource));
  }
  function makeHeroEffects(seat: string, prepare = false) {
    const effects = {
      seat,
      areas: new Map<string, ReturnType<typeof makeTelegraph>>(),
      shafts: [] as pc.Entity[],
      nock: undefined as pc.Entity | undefined,
      projectiles: 0,
      casts: [] as string[]
    };
    // Build the bounded Sena geometry and its shared painted texture before an
    // invocation begins. Lazy fallback below still covers a later hero change.
    if (prepare) prepareSena(effects);
    return effects;
  }
  const localFx = makeHeroEffects('local', true);
  function makeRemote(seat: number, id: string) {
    const markers = new pc.Entity('Seat ' + (seat + 1) + ' vitals', app);
    app.root.addChild(markers);
    const ring = kit.ring(markers, sunMarker, 0.7, 0.09, 0.032, 32);
    const bar = kit.shape(markers, 'box', vitalsBacking, 0, 0, 0, 1.1, 0.13, 0.07);
    const hp = kit.shape(markers, 'box', sunMarker, 0, 0, 0, 1, 0.074, 0.09);
    bar.render!.castShadows = hp.render!.castShadows = false;
    return { seat, rig: makeRig(id, true), fx: makeHeroEffects('seat' + seat, id === 'hanuman'), markers, ring, bar, hp, state: null as any };
  }
  const remotes = new Map<number, ReturnType<typeof makeRemote>>();
  function remoteStates(state: any): any[] {
    return state.roster ?? (state.opponent ? [state.opponent] : []);
  }
  function seatOf(remote: any): number {
    return remote.seat ?? (remote.actor.team === 'sun' ? 0 : 1);
  }
  const arrowColors = new Map<string, pc.Material>();
  for (const r of ramaKit?.abilities ?? [])
    arrowColors.set(r.id, kit.material('arrow ' + r.id, '#' + r.color, 0.9));
  const screen = new pc.Vec3(),
    point = new pc.Vec3();
  let frames = 0,
    lastState: any,
    generation = -1,
    lastMode = '';
  function render(state: any, previous: any, alpha: number, dt: number) {
    if (!state?.actor) return;
    const id = state.hero ?? state.hero_id ?? 'hanuman',
      mode = state.mode ?? 'drill';
    const reset = generation !== state.generation || id !== hero.id || mode !== lastMode;
    generation = state.generation;
    lastMode = mode;
    const prev = !reset && previous?.generation === generation ? previous : state;
    const t = clamp(alpha, 0, 1),
      a = state.actor;
    hero = selectRig(localRigs, id);
    const { x, y, z } = poseRig(hero, state, prev, t, dt, reset);
    const sign = a.team === 'moon' ? -1 : 1;
    cameraClearance = resolveChaseCamera({
      look: { x: x + sign * 0.15, y: 0.85 + Math.min(y, 0.8) * 0.5, z: z + sign * 0.2 },
      desired: { x: x + sign * 1.35, y: 4.4 + Math.min(y, 0.8) * 0.5, z: z - sign * 8.4 },
      feet: { x, y, z },
      height: 2.1,
      obstacles: cameraObstacles,
      nearClip: camera.camera!.nearClip,
      aspect: Math.max(1, canvas.clientWidth) / Math.max(1, canvas.clientHeight),
      previousFraction: reset ? 1 : cameraFraction,
      previousFov: reset ? 48 : cameraFov,
      dt
    });
    cameraFraction = cameraClearance.fraction;
    cameraFov = cameraClearance.fov;
    camera.camera!.fov = cameraFov;
    camera.setPosition(cameraClearance.position.x, cameraClearance.position.y, cameraClearance.position.z);
    camera.lookAt(cameraClearance.look.x, cameraClearance.look.y, cameraClearance.look.z);
    localRing.enabled = !!state.army;
    if (localRing.enabled) {
      localRing.setPosition(x, 0.03, z);
      setMaterial(localRing, sign === 1 ? sunMarker : moonMarker);
    }
    const roster = remoteStates(state), oldRoster = remoteStates(prev);
    const focal = roster.length ? verticalFocalPixels(canvas.clientHeight, camera.camera!.fov) : 0;
    for (const remote of roster) {
      const seat = seatOf(remote), heroId = remote.hero ?? remote.hero_id;
      let view = remotes.get(seat);
      if (!view) {
        view = makeRemote(seat, heroId);
        remotes.set(seat, view);
      }
      const prior = oldRoster.find((r) => seatOf(r) === seat);
      const newPose = reset || !view.state || !prior || prior.actor.id !== remote.actor.id ||
        prior.generation !== remote.generation || view.rig.id !== heroId;
      if (view.rig.id !== heroId) {
        view.rig.holder.destroy();
        view.rig = makeRig(heroId, true);
        if (heroId === 'hanuman') prepareSena(view.fx);
      }
      view.state = remote;
      view.rig.holder.enabled = view.markers.enabled = true;
      const from = newPose ? remote : prior;
      const p = poseRig(view.rig, remote, from, t, dt, newPose);
      const groom = view.rig.groom;
      if (groom) {
        const pixels = projectedHanumanHeight(p, camera.getPosition(), camera.forward, camera.up, focal);
        groom.visible = groomVisible(groom.visible, pixels);
      }
      const hp = clamp(remote.actor.hp / remote.actor.max_hp, 0, 1);
      const marker = remote.actor.team === 'sun' ? sunMarker : moonMarker;
      view.ring.setPosition(p.x, 0.032, p.z);
      view.bar.setPosition(p.x, p.y + 2.46, p.z);
      view.hp.setPosition(p.x + sign * (1 - hp) * 0.5, p.y + 2.46, p.z);
      view.hp.setLocalScale(hp, 0.074, 0.09);
      setMaterial(view.ring, marker);
      setMaterial(view.hp, marker);
      updateEffects(view.fx, remote, from, t);
    }
    for (const view of remotes.values()) {
      if (!view.state || roster.includes(view.state)) continue;
      view.rig.holder.enabled = view.markers.enabled = false;
      view.state = null;
      updateEffects(view.fx, null, null, 1);
      updateNock(view.fx, null, null);
    }
    const showArmy = state.ruleset !== 'hero_skirmish';
    armyView.update(showArmy ? state.army ?? null : null, showArmy ? prev.army ?? null : null, t, [x, z]);
    for (const body of soldierActors.values()) body.root.enabled = !state.army;
    for (const unit of state.army ? [] : (state.targets ?? [])) {
      let body = soldierActors.get(unit.id);
      if (!body) {
        body = makeSoldier(unit);
        soldierActors.set(unit.id, body);
      }
      body.root.setLocalPosition(unit.pos[0], 0, unit.pos[1]);
      const soldierClip = unit.alive ? 'idle' : 'defeat';
      if (soldierClip !== body.skin.clip || reset) {
        body.skin.layer.play(soldierClip);
        body.skin.clip = soldierClip;
      }
      body.skin.model.setLocalEulerAngles(0, Math.atan2(x - unit.pos[0], z - unit.pos[1]) * RAD, 0);
      body.bar.enabled = body.hp.enabled = unit.alive;
      const ratio = clamp(unit.hp / unit.max_hp, 0, 1);
      body.hp.setLocalScale(0.77 * ratio, 0.057, 0.018);
      body.hp.setLocalPosition((1 - ratio) * 0.385, 2.122, -0.025);
    }
    updateEffects(localFx, state, prev, t);
    app.update(clamp(dt, 0, 0.2));
    updateNock(localFx, state, hero);
    for (const view of remotes.values())
      if (view.state) updateNock(view.fx, view.state, view.rig);
    app.render();
    frames++;
    lastState = state;
    if (!state.active) hero.phase = hero.layer.activeStateProgress % 1;
  }
  function updateEffects(fx: typeof localFx, state: any, prev: any, t: number) {
    for (const e of fx.areas.values()) e.root.enabled = false;
    fx.casts.length = 0;
    for (const cast of state?.casts ?? []) {
      if (cast.field_end_tick != null && cast.age_ticks >= cast.field_end_tick) continue;
      fx.casts.push(cast.id);
      let e = fx.areas.get(cast.id);
      if (!e) {
        const rule = groundRules.get(cast.id);
        if (!rule) continue;
        e = makeTelegraph(kit, rule, fx.seat, mountainSource);
        fx.areas.set(cast.id, e);
      }
      e.root.enabled = true;
      const aimed = e.geometry.kind !== 'sector',
        base = aimed ? cast.target : cast.origin;
      const heading: Point =
        e.geometry.kind === 'movement'
          ? [cast.target[0] - cast.origin[0], cast.target[1] - cast.origin[1]]
          : cast.aim;
      const direction = angle(heading) + (e.geometry.direction === 'rear' ? Math.PI : 0);
      e.root.setLocalPosition(base[0], 0, base[1]);
      e.root.setLocalEulerAngles(0, direction * RAD, 0);
      const prior = prev?.casts?.find((v: any) => v.cast_id === cast.cast_id);
      const age = lerp(prior?.age_ticks ?? cast.age_ticks, cast.age_ticks, t);
      const progress = clamp(age / Math.max(1, cast.end_tick), 0, 1);
      const pulse =
        age < cast.impact_tick
          ? clamp(age / Math.max(1, cast.impact_tick), 0, 1)
          : clamp((age - cast.impact_tick) / Math.max(1, cast.end_tick - cast.impact_tick), 0, 1);
      const size = 0.22 + 0.78 * pulse;
      e.wave.setLocalScale(size, 1, size);
      e.material.opacity = (0.94 - 0.44 * progress) * clamp((cast.end_tick - age) / 3, 0.14, 1);
      e.material.update();
      if (e.outline) {
        e.outline.opacity = e.material.opacity * 0.86;
        e.outline.update();
      }
      if (e.trail) {
        const length = Math.hypot(cast.target[0] - cast.origin[0], cast.target[1] - cast.origin[1]);
        e.trail.setLocalScale(0.13, 1, length);
        e.trail.setLocalPosition(0, 0.035, -length * 0.5);
      }
      if (e.senaSpirits.length) {
        // Five flat, painted guardian silhouettes form a short-lived crescent.
        // Their motion follows the replicated cast clock; they have no hitboxes,
        // independent AI, target selection, or authority over damage.
        const elapsed = age - cast.release_tick;
        const life = Math.max(1, cast.end_tick - cast.release_tick);
        const time = clamp(elapsed / life, 0, 1);
        const arrival = clamp(elapsed / 4, 0, 1);
        const departure = clamp((cast.end_tick - age) / 5, 0, 1);
        const scale = Math.min(arrival, departure);
        const radius = (e.geometry.radius_m ?? 3) * (0.73 - 0.14 * Math.sin(Math.PI * time));
        for (let i = 0; i < e.senaSpirits.length; i++) {
          const guardian = e.senaSpirits[i];
          const theta = -Math.PI * .62 + (i / 4) * Math.PI * 1.24;
          guardian.enabled = elapsed >= 0 && age < cast.end_tick && scale > 0.01;
          guardian.setLocalPosition(Math.sin(theta) * radius,
            .68 + .12 * Math.sin(Math.PI * time * 3 + i * .7), Math.cos(theta) * radius);
          guardian.setLocalScale(.84 * scale, 1, 1.28 * scale);
          const position = guardian.getPosition(), eye = camera.getPosition();
          guardian.setEulerAngles(90, Math.atan2(eye.x - position.x, eye.z - position.z) * RAD, 0);
        }
      }
      if (e.mote) {
        const q = clamp(
          (age - cast.release_tick) / Math.max(1, cast.impact_tick - cast.release_tick),
          0,
          1
        );
        e.mote.enabled = age >= cast.release_tick && age < cast.impact_tick;
        e.mote.setPosition(
          lerp(cast.origin[0], cast.target[0], q),
          2.4 * (1 - q) + 2.2 * Math.sin(Math.PI * q) + 0.1,
          lerp(cast.origin[1], cast.target[1], q)
        );
        e.mote.setLocalEulerAngles(0, q * 70, 0);
        const impactAge = age - cast.impact_tick;
        const sparkProgress = clamp(impactAge / 6, 0, 1);
        for (let i = 0; i < e.impactSparks.length; i++) {
          const spark = e.impactSparks[i];
          const theta = i * Math.PI * 2 / e.impactSparks.length;
          const spread = 0.3 + sparkProgress * 1.35;
          const size = 0.16 * (1 - sparkProgress);
          spark.enabled = impactAge >= 0 && impactAge < 6;
          spark.setLocalPosition(
            Math.sin(theta) * spread,
            0.12 + Math.sin(Math.PI * sparkProgress) * 0.48,
            Math.cos(theta) * spread
          );
          spark.setLocalScale(size, size, size);
        }
      }
    }

    const arrows = state?.projectiles ?? [];
    fx.projectiles = Math.min(arrows.length, 36);
    for (let i = 0; i < fx.projectiles; i++) {
      const shot = arrows[i],
        mat = arrowColors.get(shot.id);
      if (!mat) throw new Error('Unknown Rama projectile ' + shot.id);
      let shaft = fx.shafts[i];
      if (!shaft) {
        shaft = kit.shape(app.root, 'sphere', mat, 0, 0, 0, 0.06, 0.06, 0.86);
        shaft.render!.castShadows = false;
        fx.shafts.push(shaft);
      }
      shaft.enabled = true;
      setMaterial(shaft, mat);
      const old = (prev?.projectiles ?? []).find(
        (r: any) => r.cast_id === shot.cast_id && r.index === shot.index
      );
      const from = old?.pos ?? shot.origin;
      shaft.setPosition(lerp(from[0], shot.pos[0], t), shot.y, lerp(from[1], shot.pos[1], t));
      shaft.setEulerAngles(0, angle(shot.forward) * RAD, 0);
    }
    for (let i = fx.projectiles; i < fx.shafts.length; i++) fx.shafts[i].enabled = false;
  }
  function updateNock(fx: typeof localFx, state: any, rig: ReturnType<typeof makeRig> | null) {
    const active = state?.active,
      mat = active && arrowColors.get(active.id);
    const show =
      rig?.id === 'rama' &&
      mat &&
      ['kodanda', 'piercing_dawn', 'dawn_volley'].includes(active.id) &&
      active.phase === 'windup' &&
      rig.bowstring &&
      rig.grip;
    if (!show) {
      if (fx.nock) fx.nock.enabled = false;
      return;
    }
    if (!fx.nock) {
      fx.nock = kit.shape(app.root, 'sphere', mat, 0, 0, 0, 0.033, 0.033, 0.67);
      fx.nock.render!.castShadows = false;
    }
    const start = rig.bowstring!.getPosition(),
      end = rig.grip!.getPosition();
    const dx = end.x - start.x,
      dy = end.y - start.y,
      dz = end.z - start.z,
      len = Math.hypot(dx, dy, dz) || 1;
    fx.nock.enabled = true;
    setMaterial(fx.nock, mat);
    fx.nock.setPosition(
      start.x + (dx * 0.335) / len,
      start.y + (dy * 0.335) / len,
      start.z + (dz * 0.335) / len
    );
    fx.nock.lookAt(start.x + dx, start.y + dy, start.z + dz);
  }
  const near = new pc.Vec3(),
    far = new pc.Vec3();
  function ground(clientX: number, clientY: number): Point | null {
    const rect = canvas.getBoundingClientRect(),
      x = clientX - rect.left,
      y = clientY - rect.top;
    if (!rect.width || !rect.height || !Number.isFinite(x + y)) return null;
    camera.camera!.screenToWorld(x, y, 0.12, near);
    camera.camera!.screenToWorld(x, y, 250, far);
    const dy = far.y - near.y;
    if (Math.abs(dy) < 1e-5) return null;
    const t = -near.y / dy;
    if (t < 0 || t > 1) return null;
    return [lerp(near.x, far.x, t), lerp(near.z, far.z, t)];
  }
  function diagnostics() {
    const rect = canvas.getBoundingClientRect();
    const mountainEffect = localFx.areas.get('mountain_pulse');
    const senaEffect = localFx.areas.get('vanara_sena');
    const mountainVisible = !!mountainEffect?.root.enabled;
    const activeRemotes = [...remotes.values()].filter((v) => v.state).sort((a, b) => a.seat - b.seat);
    const opponent = activeRemotes.find((v) => v.state.actor.team !== lastState.actor.team);
    const remoteHeroes = activeRemotes.map(({ seat, rig, state, fx }) => {
      const { actor } = state, p = rig.holder.getPosition();
      return { seat, id: actor.id, team: actor.team, color: actor.team === 'sun' ? teamColors.sun : teamColors.moon,
        hero: rig.id, skinnedSurfaces: rig.surfaces, groomVisible: rig.groom?.visible ?? false, pos: [p.x, p.z], hp: actor.hp, maxHp: actor.max_hp, clip: rig.clip,
        casts: [...fx.casts], projectiles: fx.projectiles, nocked: !!fx.nock?.enabled,
        senaSpirits: fx.areas.get('vanara_sena')?.root.enabled
          ? fx.areas.get('vanara_sena')!.senaSpirits.filter((s) => s.enabled).length : 0 };
    });
    return {
      frames,
      mapProps: map.props.length,
      lanes: map.lanes.length,
      waters: map.waters.length,
      decks: map.traversal.native_collision_boxes.length,
      visualSolidIds: [...visualSolidIds],
      heroClips: [...hero.tracks.keys()],
      heroBones: hero.bones.size,
      heroSkinnedSurfaces: hero.surfaces,
      activeClip: hero.clip,
      heroId: hero.id,
      posePhase: hero.phase,
      poseTime: hero.layer.activeStateCurrentTime,
      heroPose: hero.nodes.flatMap((bone) => {
        const q = bone.getLocalRotation();
        return [q.x, q.y, q.z, q.w];
      }),
      soldierCount: lastState?.army ? 0 : soldierActors.size,
      visibleCasts: [...localFx.casts],
      groundTargeting: targeting,
      mountainCue: mountainEffect ? {
        inFlight: mountainVisible && !!mountainEffect.mote?.enabled,
        renderSurfaces: mountainEffect.mote
          ? (mountainEffect.mote.findComponents('render') as pc.RenderComponent[])
              .reduce((count, part) => count + part.meshInstances.length, 0)
          : 0,
        impactSparks: mountainVisible
          ? mountainEffect.impactSparks.filter((spark) => spark.enabled).length
          : 0
      } : null,
      senaCue: senaEffect ? {
        visibleSpirits: senaEffect.root.enabled ? senaEffect.senaSpirits.filter((s) => s.enabled).length : 0,
        casts: localFx.casts.filter((id) => id === 'vanara_sena').length
      } : null,
      cameraClearance,
      projectiles: localFx.projectiles,
      nocked: !!localFx.nock?.enabled,
      remoteHeroes,
      opponentHero: opponent?.rig.id ?? null,
      opponentClip: opponent?.rig.clip ?? null,
      opponentCasts: opponent ? [...opponent.fx.casts] : [],
      opponentProjectiles: opponent?.fx.projectiles ?? 0,
      cameraForward: lastState?.actor?.team === 'moon' ? -1 : 1,
      ...armyView.diagnostics(),
      targetScreens: (lastState?.army
        ? [
            ...lastState.army.units.map((u: any) => ({ ...u, pos: u.xz })),
            ...activeRemotes.map(({ state, rig, seat }) => {
              const p = rig.holder.getPosition();
              return { ...state.actor, seat, pos: [p.x, p.z], alive: state.actor.hp > 0 };
            })
          ]
        : (lastState?.targets ?? [])
      ).map((u: any) => {
        camera.camera!.worldToScreen(point.set(u.pos[0], 0, u.pos[1]), screen);
        return {
          id: u.id,
          kind: u.seat != null ? 'hero' : 'unit',
          seat: u.seat ?? null,
          inView:
            screen.x >= 0 &&
            screen.x <= rect.width &&
            screen.y >= 0 &&
            screen.y <= rect.height &&
            camera.forward.dot(point.sub(camera.getPosition())) > 0,
          team: u.team,
          role: u.role ?? null,
          alive: u.alive,
          x: rect.left + screen.x,
          y: rect.top + screen.y
        };
      })
    };
  }
  return { render, ground, resize, diagnostics, showGroundAim };
}
