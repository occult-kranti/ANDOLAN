import * as pc from 'playcanvas';
import { createOriginalEnvironment } from '../../../../../yuga/client/environment-light';
import { RenderKit } from '../../../../../yuga/client/render-kit';

type Shot = {
  clip: string;
  label: string;
  frames: number;
  angle: [number, number];
  distance: number;
  height: number;
  range?: [number, number];
  effect?: string;
};
type Hero = { title: string; accent: string; shots: Shot[]; cacheStaticStage?: boolean };
const radians = Math.PI / 180;
const color = (hex: string) => new pc.Color().fromString(hex);
const smooth = (v: number) => v * v * (3 - 2 * v);
const saturate = (v: number) => Math.max(0, Math.min(1, v));
function load(app: pc.Application, path: string): Promise<pc.ContainerResource> {
  return new Promise((ok, fail) => {
    app.assets.loadFromUrl(path, 'container', (err, a) => {
      if (err || !a?.resource) fail(new Error('Could not load ' + path + ': ' + (err ?? 'missing GLB')));
      else ok(a.resource);
    });
  });
}
function aimDirection(
  app: pc.Application,
  label: string,
  angles: number[],
  c: string,
  intensity: number,
  shadow = false,
) {
  const lamp = new pc.Entity(label, app);
  app.root.addChild(lamp);
  lamp.addComponent('light', {
    type: 'directional',
    color: color(c),
    intensity,
    castShadows: shadow,
    shadowDistance: 9,
    shadowBias: 0.12,
    normalOffsetBias: 0.035,
    shadowResolution: 1024,
  });
  lamp.setEulerAngles(angles[0], angles[1], 0);
}
function makeEffects(kit: RenderKit, tint: string) {
  const mat = kit.material('Ability light', tint, 1.2, 0.35, 0.9),
    hot = kit.material('Hot core', '#ffe2ab', 1.3, 0.4, 0.88);
  const app = kit.app,
    root = new pc.Entity('Presentation effects', app);
  app.root.addChild(root);
  const effects: pc.Entity[] = [];
  function model(e: pc.Entity) {
    e.enabled = false;
    effects.push(e);
    return e;
  }
  const rings = Array.from({ length: 4 }, (_, i) =>
    model(kit.ring(root, i === 0 ? hot : mat, 1, 0.034, 0, 64)),
  );
  const darts = Array.from({ length: 5 }, () =>
    model(kit.shape(root, 'sphere', hot, 0, 0, 0, 0.028, 0.028, 0.64)),
  );
  const motes = Array.from({ length: 12 }, () =>
    model(kit.shape(root, 'sphere', mat, 0, 0, 0, 0.027, 0.035, 0.027)),
  );
  function ring(i: number, p: pc.Vec3, radius: number, tilt = 0, spin = 0) {
    const e = rings[i];
    e.enabled = true;
    e.setPosition(p);
    e.setLocalScale(radius, 1, radius);
    e.setEulerAngles(tilt, spin, 0);
  }
  const wrist = new pc.Vec3(),
    target = new pc.Vec3(),
    point = new pc.Vec3();
  return (effect: string | undefined, phase: number, hero: pc.Entity) => {
    for (const e of effects) e.enabled = false;
    if (!effect) return;
    const joint = hero.findByName(effect === 'refrain' ? 'wrist.L' : 'wrist.R');
    if (joint) wrist.copy(joint.getPosition());
    else wrist.set(0, 1.2, 0);
    if (effect === 'arrow' || effect === 'volley') {
      const shots = effect === 'volley' ? 5 : 1;
      for (let i = 0; i < shots; i++) {
        const p = (phase - i * 0.045) / 0.78;
        if (p < 0 || p > 1) continue;
        const yaw = (i - (shots - 1) / 2) * 0.11;
        const e = darts[i];
        e.enabled = true;
        e.setPosition(
          wrist.x + Math.sin(yaw) * p * 4,
          wrist.y + 0.05,
          wrist.z + 0.12 + Math.cos(yaw) * p * 4,
        );
        e.setEulerAngles(0, yaw / radians, 0);
        e.setLocalScale(0.021, 0.021, 0.74);
      }
      return;
    }
    const onset =
      (
        {
          gada: 0.26,
          breath: 0.5,
          vault: 0.68,
          tail: 0.43,
          pulse: 0.66,
          ward: 0.06,
          crescent: 0.3,
          threefold: 0.37,
          coil: 0.32,
          tandava: 0.66,
          chakra: 0.25,
          star: 0.28,
          refrain: 0.29,
          canopy: 0.36,
        } as Record<string, number>
      )[effect] ?? 0.4;
    if (phase < onset) return;
    const t = saturate((phase - onset) / (1 - onset));
    if (effect === 'chakra' || effect === 'star' || effect === 'crescent') {
      const reach = (effect === 'star' ? Math.sin(t * Math.PI) : t) * 2.2;
      point.copy(wrist).add(target.set(0.15 * reach, Math.sin(Math.PI * t) * 0.16, reach));
      ring(0, point, effect === 'crescent' ? 0.12 : 0.2, 54 + t * 25, t * 380);
    } else if (effect === 'breath' || effect === 'coil' || effect === 'canopy' || effect === 'refrain') {
      for (let i = 0; i < 3; i++) {
        const q = t - i * 0.14;
        if (q < 0 || q > 1) continue;
        target.set(
          0,
          effect === 'canopy' ? 1.9 + 0.26 * q : effect === 'refrain' ? 1.15 + 0.05 * i : 0.16 + q * 1.1,
          0,
        );
        ring(i, target, 0.29 + q * 0.63, effect === 'refrain' ? 65 : 0, i * 72);
      }
    } else {
      for (let i = 0; i < 2; i++) {
        const q = t - i * 0.18;
        if (q < 0) continue;
        target.set(0, 0.025 + i * 0.004, effect === 'pulse' ? 1.65 : effect === 'gada' ? 0.68 : 0);
        ring(i, target, 0.18 + q * (effect === 'ward' ? 1.65 : 1.28));
      }
    }
    for (let i = 0; i < motes.length; i++) {
      const p = t - (i % 3) * 0.08;
      if (p <= 0) continue;
      const angle = i * 2.39996,
        r = 0.12 + 0.65 * p;
      const e = motes[i];
      e.enabled = p < 0.82;
      const baseY = effect === 'canopy' ? 1.85 : effect === 'refrain' ? 1.15 : 0.15;
      e.setPosition(
        Math.cos(angle) * r,
        baseY + Math.sin(p * Math.PI) * (0.25 + (i % 4) * 0.08),
        Math.sin(angle) * r + (effect === 'pulse' ? 1.65 : 0),
      );
    }
  };
}
function round(n: number) {
  return Math.round(n * 100000) / 100000;
}
export async function prepare(heroId: string, spec: Hero, width: number, height: number) {
  const canvas = document.querySelector<HTMLCanvasElement>('#scene')!,
    film = document.querySelector<HTMLCanvasElement>('#film')!;
  canvas.width = film.width = width;
  canvas.height = film.height = height;
  const app = new pc.Application(canvas, {
    graphicsDeviceOptions: { alpha: !!spec.cacheStaticStage, antialias: true, preserveDrawingBuffer: true },
  });
  app.setCanvasResolution(pc.RESOLUTION_FIXED, width, height);
  const [body, courtyard] = await Promise.all([load(app, './actor.glb'), load(app, './court.glb')]);
  createOriginalEnvironment(app);
  app.scene.ambientLight = new pc.Color(0.27, 0.29, 0.32);
  app.scene.skyboxIntensity = 0.48;
  app.scene.fog.type = pc.FOG_EXP2;
  app.scene.fog.density = 0.06;
  app.scene.fog.color = color('#25353c');
  const kit = new RenderKit(app),
    stage = courtyard.instantiateRenderEntity({ castShadows: false, receiveShadows: true });
  app.root.addChild(stage);
  stage.setLocalScale(0.53, 0.53, 0.53);
  // Re-light the courtyard as a dusk location while retaining its original stonework and illuminated lamps.
  for (const renderer of stage.findComponents('render') as pc.RenderComponent[]) {
    for (const mesh of renderer.meshInstances) {
      const mat = mesh.material as pc.StandardMaterial;
      if (mat && mat.diffuse && !(mat as any).__graded) {
        (mat as any).__graded = true;
        mat.diffuse.set(mat.diffuse.r * 0.38, mat.diffuse.g * 0.48, mat.diffuse.b * 0.53);
        mat.update();
      }
    }
  }
  const character = body.instantiateRenderEntity({ castShadows: true, receiveShadows: true });
  app.root.addChild(character);
  character.addComponent('anim', { activate: true });
  const animation = character.anim!,
    tracks = new Map<string, pc.AnimTrack>();
  for (const asset of body.animations) {
    const t = asset.resource as pc.AnimTrack;
    const name = t.name
      .split('|')
      .at(-1)!
      .replace(/\.\d+$/, '')
      .toLowerCase();
    tracks.set(name, t);
    animation.assignAnimation(name, t, undefined, 1, false);
  }
  const skinMeshes = (character.findComponents('render') as pc.RenderComponent[])
    .flatMap((c) => c.meshInstances)
    .filter((m) => m.skinInstance);
  const jointCount = new Set(skinMeshes.flatMap((m) => m.skinInstance!.bones)).size;
  if (!jointCount) throw Error('No live skinned model for ' + heroId);
  const layer = animation.baseLayer!;
  const camera = new pc.Entity('Editorial lens', app);
  app.root.addChild(camera);
  camera.addComponent('camera', { fov: 30, farClip: 65, nearClip: 0.1, clearColor: color('#26363d') });
  aimDirection(app, 'Warm key', [55, -30], '#ffdfb8', 1.58, true);
  aimDirection(app, 'Blue bounce', [17, 45], '#c4deee', 0.94);
  aimDirection(app, 'Edge light', [25, 166], '#f6c689', 1.35);
  const effects = makeEffects(kit, spec.accent);
  const overlay = film.getContext('2d', { alpha: false })!;
  const bottom = overlay.createLinearGradient(0, height * 0.72, 0, height);
  bottom.addColorStop(0, 'rgba(12,20,24,0)');
  bottom.addColorStop(0.72, 'rgba(12,20,24,.64)');
  bottom.addColorStop(1, 'rgba(9,15,19,.86)');
  const bones = ['root', 'head', 'wrist.L', 'wrist.R', 'foot.L', 'foot.R', 'tail_02', 'tail_04', 'bowstring']
    .map((name) => [name, character.findByName(name)] as const)
    .filter(([, bone]) => bone);
  let lastClip = '';
  let cachedShot = -1;
  const backdrop = document.createElement('canvas');
  backdrop.width = width;
  backdrop.height = height;
  const plate = backdrop.getContext('2d', { alpha: false })!;
  const sky = app.scene.layers.getLayerById(pc.LAYERID_SKYBOX);
  const clear = color('#26363d'),
    transparent = new pc.Color(0, 0, 0, 0);
  // Project a soft contact shadow into the same ground plane as the saved color pass.
  const foot = character.findByName('foot.L'),
    otherFoot = character.findByName('foot.R');
  const v = new pc.Vec3(),
    center = new pc.Vec3(),
    right = new pc.Vec3(),
    forward = new pc.Vec3();
  function groundShadow() {
    const a = foot?.getPosition(),
      b = otherFoot?.getPosition();
    const x = a && b ? (a.x + b.x) * 0.5 : 0,
      z = a && b ? (a.z + b.z) * 0.5 : 0;
    camera.camera!.worldToScreen(v.set(x, 0.01, z), center);
    camera.camera!.worldToScreen(v.set(x + 0.49, 0.01, z), right);
    camera.camera!.worldToScreen(v.set(x, 0.01, z + 0.31), forward);
    overlay.save();
    overlay.setTransform(
      right.x - center.x,
      right.y - center.y,
      forward.x - center.x,
      forward.y - center.y,
      center.x,
      center.y,
    );
    const ink = overlay.createRadialGradient(0, 0, 0, 0, 0, 1);
    ink.addColorStop(0, 'rgba(7,12,16,.46)');
    ink.addColorStop(1, 'rgba(7,12,16,0)');
    overlay.fillStyle = ink;
    overlay.fillRect(-1, -1, 2, 2);
    overlay.restore();
  }
  function frame(shot: number, index: number, savePose: boolean) {
    const s = spec.shots[shot],
      track = tracks.get(s.clip);
    if (!track) throw Error('Missing action ' + s.clip + ' on ' + heroId);
    const t = index / Math.max(1, s.frames - 1),
      range = s.range ?? [0, 0.999];
    const phase = range[0] + (range[1] - range[0]) * t;
    const az = (s.angle[0] + (s.angle[1] - s.angle[0]) * smooth(t)) * radians;
    const distance = s.distance;
    camera.setPosition(Math.sin(az) * distance, 1.29 + 0.16 * Math.cos(az), Math.cos(az) * distance);
    camera.lookAt(0, s.height, 0);
    const usePlate = !!spec.cacheStaticStage && s.angle[0] === s.angle[1];
    if (usePlate && cachedShot !== shot) {
      stage.enabled = true;
      if (sky) sky.enabled = true;
      camera.camera!.clearColor = clear;
      // Disable mesh draw components only, leaving the selected animation and its playhead intact.
      const parts = character.findComponents('render') as pc.RenderComponent[];
      for (const part of parts) part.enabled = false;
      effects(undefined, 0, character);
      app.render();
      plate.drawImage(canvas, 0, 0);
      for (const part of parts) part.enabled = true;
      cachedShot = shot;
    }
    if (spec.cacheStaticStage) {
      stage.enabled = !usePlate;
      if (sky) sky.enabled = !usePlate;
      camera.camera!.clearColor = usePlate ? transparent : clear;
    }
    if (lastClip !== s.clip) {
      layer.play(s.clip);
      lastClip = s.clip;
    }
    animation.speed = 0;
    layer.activeStateCurrentTime = phase * track.duration;
    app.update(0);
    effects(s.effect, phase, character);
    app.render();
    if (usePlate) {
      overlay.drawImage(backdrop, 0, 0);
      groundShadow();
    }
    overlay.drawImage(canvas, 0, 0);
    overlay.fillStyle = bottom;
    overlay.fillRect(0, height * 0.72, width, height * 0.28);
    const base = width / 960,
      margin = 36 * base;
    overlay.fillStyle = '#fff2d5';
    overlay.font = 31 * base + 'px Georgia,serif';
    overlay.fillText(spec.title, margin, height - 39 * base);
    overlay.fillStyle = spec.accent;
    overlay.font = '600 ' + 15 * base + 'px sans-serif';
    overlay.fillText(s.label, margin, height - 17 * base);
    const q = savePose
      ? Object.fromEntries(
          bones.map(([name, b]) => {
            const p = b!.getPosition(),
              r = b!.getRotation();
            return [name, [p.x, p.y, p.z, r.w, r.x, r.y, r.z].map(round)];
          }),
        )
      : null;
    return {
      image: film.toDataURL('image/jpeg', 0.93).split(',')[1],
      pose: q
        ? {
            phase: round(phase),
            camera_world: Array.from(camera.getWorldTransform().data, round),
            bones: q,
          }
        : null,
    };
  }
  const gl = (app.graphicsDevice as pc.WebglGraphicsDevice).gl;
  const rendererInfo = gl.getExtension('WEBGL_debug_renderer_info');
  return {
    frame,
    info: {
      renderer: rendererInfo ? gl.getParameter(rendererInfo.UNMASKED_RENDERER_WEBGL) : 'WebGL2',
      modelMeshes: skinMeshes.length,
      joints: jointCount,
      clips: [...tracks].map(([clip, t]) => ({ clip, duration: t.duration })),
      engine: 'PlayCanvas ' + pc.version,
    },
  };
}
