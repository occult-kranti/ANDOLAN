import * as pc from 'playcanvas';
import { RenderKit, RAD, clamp, mixAngle } from '../../yuga/client/render-kit';
import { createOriginalEnvironment } from '../../yuga/client/environment-light';

type Assets = { hero: string; soldier: string; architecture: string; nature: string };
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

function figure(container: pc.ContainerResource, parent: pc.Entity) {
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
  anim.baseLayer.play('idle');
  return { model, anim, tracks, bones, clip: 'idle' };
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

function makeTelegraph(kit: RenderKit, rule: any) {
  const root = new pc.Entity(rule.id, kit.app);
  kit.app.root.addChild(root);
  // Double-sided ribbons remain visible for oblique cameras and both winding orders.
  const material = kit.material(rule.id, '#' + rule.color, 0.75, 0.25, 0.82);
  material.cull = pc.CULLFACE_NONE;
  material.update();
  const g = rule.geometry,
    radius = g.range_m ?? g.radius_m ?? 0.65;
  const half = g.kind === 'sector' ? Math.acos(g.half_angle_cos) : Math.PI;
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
  if (g.kind === 'disk')
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
  const mote = g.kind === 'disk' ? kit.shape(root, 'sphere', material, 0, 1, 0, 0.4, 0.6, 0.4) : null;
  root.enabled = false;
  return { root, wave, material, trail, mote, geometry: g };
}

export async function makeScene(canvas: HTMLCanvasElement, assets: Assets, map: any, rules: any) {
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
  const [hanuman, soldier, architecture, nature] = await Promise.all([
    loadGlb(app, assets.hero, 'hanuman'),
    loadGlb(app, assets.soldier, 'soldier'),
    loadGlb(app, assets.architecture, 'architecture'),
    loadGlb(app, assets.nature, 'nature')
  ]);
  const kit = new RenderKit(app);
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
  const holder = new pc.Entity('Hanuman feet', app);
  app.root.addChild(holder);
  const hero = figure(hanuman, holder);
  for (const rule of rules.abilities)
    if (!hero.tracks.has(rule.motion)) throw new Error('Hero ability clip missing: ' + rule.motion);
  const poses = ['spine03', 'upperarm01.R', 'lowerarm01.R', 'wrist.R', 'upperleg01.L', 'tail_02'];
  const poseNodes = poses
    .map((name) => hero.model.findByName(name))
    .filter((n): n is pc.GraphNode => !!n);
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
  const effects = new Map<string, ReturnType<typeof makeTelegraph>>(
    rules.abilities.map((rule: any) => [rule.id, makeTelegraph(kit, rule)])
  );
  const screen = new pc.Vec3(),
    point = new pc.Vec3();
  let frames = 0,
    phase = 0,
    lastState: any,
    visibleCasts: string[] = [];
  let yaw = 0,
    generation = -1;
  function render(state: any, previous: any, alpha: number, dt: number) {
    if (!state?.actor) return;
    const reset = generation !== state.generation;
    generation = state.generation;
    const prev = !reset && previous?.generation === generation ? previous : state;
    const t = clamp(alpha, 0, 1),
      a = state.actor,
      b = prev.actor;
    const x = lerp(b.pos[0], a.pos[0], t),
      y = lerp(b.y, a.y, t),
      z = lerp(b.pos[1], a.pos[1], t);
    const active = state.active;
    const moving = (a.pos[0] - b.pos[0]) ** 2 + (a.pos[1] - b.pos[1]) ** 2 > 1e-8;
    const clip = active?.motion ?? (moving ? 'run' : 'idle');
    if (clip !== hero.clip || reset) {
      hero.anim.baseLayer.play(clip);
      hero.clip = clip;
    }
    if (active) {
      const current = active.motion_phase_normalized;
      const old =
        prev.active?.cast_id === active.cast_id ? prev.active.motion_phase_normalized : current;
      phase = lerp(old, current, t);
      hero.anim.speed = 0;
      hero.anim.baseLayer.activeStateCurrentTime = phase * hero.tracks.get(clip)!.duration;
    } else hero.anim.speed = 1;
    const targetYaw = angle(active?.aim ?? a.aim);
    yaw = reset ? targetYaw : mixAngle(yaw, targetYaw, Math.min(1, Math.max(dt, 0) * 18));
    holder.setLocalPosition(x, y, z);
    holder.setLocalEulerAngles(0, yaw * RAD, 0);
    camera.setPosition(x + 1.35, 4.4 + Math.min(y, 0.8) * 0.5, z - 8.4);
    camera.lookAt(x + 0.15, 0.85 + Math.min(y, 0.8) * 0.5, z + 0.2);
    for (const unit of state.targets) {
      let body = soldierActors.get(unit.id);
      if (!body) {
        body = makeSoldier(unit);
        soldierActors.set(unit.id, body);
      }
      body.root.setLocalPosition(unit.pos[0], 0, unit.pos[1]);
      const soldierClip = unit.alive ? 'idle' : 'defeat';
      if (soldierClip !== body.skin.clip || reset) {
        body.skin.anim.baseLayer.play(soldierClip);
        body.skin.clip = soldierClip;
      }
      body.skin.model.setLocalEulerAngles(0, Math.atan2(x - unit.pos[0], z - unit.pos[1]) * RAD, 0);
      body.bar.enabled = body.hp.enabled = unit.alive;
      const ratio = clamp(unit.hp / unit.max_hp, 0, 1);
      body.hp.setLocalScale(0.77 * ratio, 0.057, 0.018);
      body.hp.setLocalPosition((1 - ratio) * 0.385, 2.122, -0.025);
    }
    for (const e of effects.values()) e.root.enabled = false;
    visibleCasts.length = 0;
    for (const cast of state.casts) {
      const e = effects.get(cast.id);
      if (!e) continue;
      e.root.enabled = true;
      visibleCasts.push(cast.id);
      const aimed = e.geometry.kind !== 'sector',
        base = aimed ? cast.target : cast.origin;
      const direction = angle(cast.aim) + (e.geometry.direction === 'rear' ? Math.PI : 0);
      e.root.setLocalPosition(base[0], 0, base[1]);
      e.root.setLocalEulerAngles(0, direction * RAD, 0);
      const prior = prev.casts?.find((v: any) => v.cast_id === cast.cast_id);
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
      if (e.trail) {
        const length = Math.hypot(cast.target[0] - cast.origin[0], cast.target[1] - cast.origin[1]);
        e.trail.setLocalScale(0.13, 1, length);
        e.trail.setLocalPosition(0, 0.035, -length * 0.5);
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
          1.15 * (1 - q) + 3.5 * Math.sin(Math.PI * q) + 0.1,
          lerp(cast.origin[1], cast.target[1], q)
        );
      }
    }
    app.update(clamp(dt, 0, 0.2));
    app.render();
    frames++;
    lastState = state;
    if (!active) phase = hero.anim.baseLayer.activeStateProgress % 1;
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
    return {
      frames,
      mapProps: map.props.length,
      lanes: map.lanes.length,
      waters: map.waters.length,
      decks: map.traversal.native_collision_boxes.length,
      visualSolidIds: [...visualSolidIds],
      heroClips: [...hero.tracks.keys()],
      heroBones: hero.bones.size,
      activeClip: hero.clip,
      posePhase: phase,
      poseTime: hero.anim.baseLayer.activeStateCurrentTime,
      heroPose: poseNodes.flatMap((bone) => {
        const q = bone.getLocalRotation();
        return [q.x, q.y, q.z, q.w];
      }),
      soldierCount: soldierActors.size,
      visibleCasts: [...visibleCasts],
      targetScreens: (lastState?.targets ?? []).map((u: any) => {
        camera.camera!.worldToScreen(point.set(u.pos[0], 0, u.pos[1]), screen);
        return { id: u.id, alive: u.alive, x: rect.left + screen.x, y: rect.top + screen.y };
      })
    };
  }
  return { render, ground, resize, diagnostics };
}
