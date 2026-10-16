import * as pc from 'playcanvas';
import { HEROES } from '../shared/heroes';
import { lockedCastPlayback } from './hero-cast-playback';

// Vite emits these as separately cached GLB files. Concept illustrations are never used as avatars.
const modelUrls = import.meta.glob('./assets/heroes/*.glb', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
const REQUIRED_CLIPS = ['idle', 'run', 'fire', 'cast', 'cast1', 'cast2', 'cast3', 'jump', 'defeat'] as const;
type Motion = typeof REQUIRED_CLIPS[number];
export interface HeroModelFrame {
  speed: number; airborne: boolean; alive: boolean; shot: number; cast: number;
  castSlot: number; casting: boolean; reducedMotion: boolean;
  castElapsed?: number; castStartedAt?: number;
  pitch?: number;
}
export interface HeroAssetDiagnostic {
  heroId: string; state: 'loading' | 'ready' | 'failed'; error?: string;
  url: string; triangles: number; materials: number; skinnedPrimitives: number; animations: string[];
}
export interface HeroModel {
  root: pc.Entity;
  update(frame: HeroModelFrame, dt: number): void;
  setShadows(enabled: boolean): void;
  diagnostic(): { id: string; heroId: string; url: string; loaded: boolean; fallback: boolean; skinned: boolean; skeletons: number[]; bones: number; clips: string[]; state: string; action: string; animationTime: number; poseBones: string[]; pose: number[]; transitions: Record<string, number> };
  destroy(): void;
}

function animationName(name: string) { return name.split('|').at(-1)!.replace(/\.\d+$/, '').toLowerCase(); }
function animationTracks(resource: pc.ContainerResource) {
  const result = new Map<string, pc.AnimTrack>();
  for (const asset of resource.animations) if (asset.resource instanceof pc.AnimTrack) result.set(animationName(asset.resource.name), asset.resource);
  return result;
}

/** Asset lifetime belongs to the scene. Hero clones share meshes, textures and animation tracks. */
export class HeroModelLibrary {
  private readonly assets = new Map<string, pc.Asset<'container'>>();
  private readonly pending = new Map<string, Promise<void>>();
  private readonly states = new Map<string, HeroAssetDiagnostic>();
  private readonly instances = new Set<HeroModel>();
  private readonly skeletonIds = new WeakMap<pc.SkinInstance, number>();
  private nextSkeletonId = 1;
  private disposed = false;
  private active = true;
  private readonly aimPasses = new Set<{ apply: () => void; restore: () => void }>();

  constructor(private readonly app: pc.Application) {
    app.on('prerender', this.applyAim, this); app.on('postrender', this.restoreAim, this);
  }
  private applyAim() { for (const pass of this.aimPasses) pass.apply(); }
  private restoreAim() { for (const pass of this.aimPasses) pass.restore(); }
  setActive(enabled: boolean) { this.active = enabled; for (const model of this.instances) model.root.anim!.enabled = enabled; }

  diagnostics() {
    return {
      assets: [...this.states.values()].map(value => ({ ...value, animations: [...value.animations] })),
      instances: [...this.instances].map(model => model.diagnostic()),
    };
  }

  async preload(ids: string[], progress?: (done: number, total: number, heroId: string) => void) {
    const unique = [...new Set(ids)]; let done = 0;
    const outcomes = await Promise.allSettled(unique.map(async id => {
      try { await this.load(id); } finally { progress?.(++done, unique.length, id); }
    }));
    const failures = outcomes.flatMap((result, index) => result.status === 'rejected' ? [unique[index]!] : []);
    if (failures.length) throw new Error(`Hero artwork could not load: ${failures.join(', ')}. Reload to retry.`);
  }

  load(heroId: string): Promise<void> {
    if (this.assets.has(heroId)) return Promise.resolve();
    const pending = this.pending.get(heroId); if (pending) return pending;
    if (!HEROES.some(h => h.id === heroId)) return Promise.reject(new Error('Unknown hero asset'));
    const url = modelUrls[`./assets/heroes/${heroId}.glb`] || '';
    const diagnostic: HeroAssetDiagnostic = { heroId, state: 'loading', url, triangles: 0, materials: 0, skinnedPrimitives: 0, animations: [] };
    this.states.set(heroId, diagnostic);
    const job = new Promise<void>((resolve, reject) => {
      const fail = (message: string, asset?: pc.Asset<'container'>) => {
        diagnostic.state = 'failed'; diagnostic.error = message;
        if (asset) { asset.unload(); this.app.assets.remove(asset); }
        reject(new Error(`${heroId}: ${message}`));
      };
      if (!url) { fail('Published GLB file is missing'); return; }
      this.app.assets.loadFromUrl(url, 'container', (error, asset) => {
        if (error || !asset?.resource) { fail(String(error || 'GLB container unavailable'), asset); return; }
        if (this.disposed) { fail('Scene closed before asset finished loading', asset); return; }
        const resource = asset.resource;
        diagnostic.animations = [...animationTracks(resource).keys()];
        const missing = REQUIRED_CLIPS.filter(name => !diagnostic.animations.includes(name));
        if (missing.length) { fail(`Required animation clips missing: ${missing.join(', ')}`, asset); return; }
        const probe = resource.instantiateRenderEntity();
        const meshSet = new Set<pc.Mesh>(), materialSet = new Set<pc.Material>();
        for (const component of probe.findComponents('render') as pc.RenderComponent[]) {
          for (const meshInstance of component.meshInstances) {
            if (meshInstance.mesh) meshSet.add(meshInstance.mesh);
            if (meshInstance.material) materialSet.add(meshInstance.material);
            if (meshInstance.skinInstance) diagnostic.skinnedPrimitives++;
          }
        }
        for (const mesh of meshSet) for (const primitive of mesh.primitive) if (primitive.type === pc.PRIMITIVE_TRIANGLES) diagnostic.triangles += primitive.count / 3;
        diagnostic.materials = materialSet.size;
        probe.destroy();
        if (!diagnostic.skinnedPrimitives) { fail('Hero GLB has no deforming skinned mesh', asset); return; }
        diagnostic.state = 'ready'; this.assets.set(heroId, asset); resolve();
      });
    });
    this.pending.set(heroId, job);
    void job.finally(() => this.pending.delete(heroId)).catch(() => { /* The caller receives the rejection. */ });
    return job;
  }

  instantiate(heroId: string, id: string, parent: pc.Entity): HeroModel | null {
    const resource = this.assets.get(heroId)?.resource; if (!resource || this.disposed) return null;
    const root = resource.instantiateRenderEntity({ castShadows: true, receiveShadows: true });
    root.name = `authored-${heroId}`; parent.addChild(root);
    root.addComponent('anim', { activate: true });
    const tracks = animationTracks(resource);
    const anim = root.anim!;
    anim.enabled = this.active;
    for (const name of REQUIRED_CLIPS) anim.assignAnimation(name, tracks.get(name)!, undefined, 1, ['idle', 'run'].includes(name));
    // Keep locomotion in the lower body while an acknowledged attack animates the upper body.
    const upperPath = tracks.get('idle')!.curves.flatMap(curve => curve.paths).find(path => ['spine03', 'Spine2', 'Chest'].includes(path.entityPath.at(-1)!))?.entityPath;
    const mask = upperPath ? { [upperPath.join('/')]: { children: true } } : undefined;
    // PlayCanvas's runtime mask is a path dictionary; its 2.23 declaration calls it object[].
    const upper = mask ? anim.addLayer('Action', 0, mask as unknown as object[], pc.ANIM_LAYER_OVERWRITE) : undefined;
    if (upper) {
      for (const name of ['fire', 'cast', 'cast1', 'cast2', 'cast3']) {
        const track = tracks.get(name); if (track) anim.assignAnimation(name, track, 'Action', 1, false);
      }
    }
    const renders = root.findComponents('render') as pc.RenderComponent[];
    const skins = [...new Set(renders.flatMap(render => render.meshInstances.map(instance => instance.skinInstance)).filter((skin): skin is pc.SkinInstance => !!skin))];
    const skeletons = skins.map(skin => { if (!this.skeletonIds.has(skin)) this.skeletonIds.set(skin, this.nextSkeletonId++); return this.skeletonIds.get(skin)!; });
    const transitions: Record<string, number> = { idle: 1 };
    let time = 0, lastShot = -1, lastCast = -1, actionUntil = 0, action = '', base = 'idle', dead = false, disposed = false, fading = false, aimPitch = 0;
    let lockedCastKey: string | null = null;
    const baseLayer = anim.baseLayer!; baseLayer.play('idle');
    const aimBones = [['spine03', .25], ['upperarm01.L', .75], ['upperarm01.R', .75], ['head', .75]] as const;
    const aimNodes = aimBones.flatMap(([name, amount]) => {
      const node = root.findByName(name); return node ? [{ node, amount, saved: new pc.Quat() }] : [];
    });
    // Sample both halves of the actual skeleton: an archer can hold a steady bow while running.
    const poseNodes = [...aimBones.map(([name]) => name), 'upperleg01.L', 'lowerleg01.L', 'upperleg01.R', 'lowerleg01.R'].flatMap(name => {
      const node = root.findByName(name); return node ? [{ name, node }] : [];
    });
    let applied = false;
    const aimPass = {
      apply: () => {
        if (!root.enabled || dead || !aimPitch || !this.active) return;
        const axis = root.getRotation().transformVector(pc.Vec3.RIGHT, new pc.Vec3());
        for (const item of aimNodes) {
          item.saved.copy(item.node.getLocalRotation());
          const delta = new pc.Quat().setFromAxisAngle(axis, -aimPitch * 180 / Math.PI * item.amount);
          item.node.setRotation(delta.mul(item.node.getRotation().clone()));
        }
        applied = true;
      },
      restore: () => { if (applied) for (let i = aimNodes.length - 1; i >= 0; i--) aimNodes[i]!.node.setLocalRotation(aimNodes[i]!.saved); applied = false; },
    };
    this.aimPasses.add(aimPass);
    const result: HeroModel = {
      root,
      update(frame, dt) {
        if (disposed) return; time += dt;
        aimPitch = Math.max(-1.1, Math.min(1.1, frame.pitch ?? 0));
        if (frame.alive && dead) { baseLayer.transition('idle', 0); base = 'idle'; actionUntil = 0; if (upper) upper.weight = 0; }
        dead = !frame.alive;
        const castName = tracks.has(`cast${frame.castSlot + 1}`) ? `cast${frame.castSlot + 1}` : 'cast';
        const actionName = frame.cast > lastCast && frame.cast > 0 ? castName : frame.shot > lastShot && frame.shot > 0 ? 'fire' : '';
        lastShot = frame.shot; lastCast = frame.cast;
        const locked = lockedCastPlayback(frame, lockedCastKey, tracks.get(castName)!.duration);
        if (locked) {
          // Stationary preparation and authority-driven travel use the complete
          // authored pose, including hips/knees. Airborne does not replace it.
          action = ''; actionUntil = 0; fading = false;
          if (locked.seekSeconds !== null) {
            // Direct weight assignment alone does not cancel PlayCanvas's
            // outstanding blend target. Cancel once, when this cast is entered.
            if (upper) { upper.blendToWeight(0, 0); upper.weight = 0; }
            baseLayer.transition(locked.clip, 0);
            baseLayer.activeStateCurrentTime = locked.seekSeconds;
            base = locked.clip; transitions[base] = (transitions[base] || 0) + 1;
          }
          lockedCastKey = locked.key; anim.speed = 1;
          return;
        }
        if (lockedCastKey !== null) {
          lockedCastKey = null; action = ''; actionUntil = 0;
          if (upper) { upper.blendToWeight(0, 0); upper.weight = 0; }
        }
        if (actionName && frame.alive) {
          transitions[actionName] = (transitions[actionName] || 0) + 1;
          action = actionName; actionUntil = time + Math.min(actionName === 'fire' ? .6 : 3, tracks.get(actionName)!.duration);
          if (upper) { upper.transition(actionName, frame.reducedMotion ? 0 : .065); upper.blendToWeight(1, .05); fading = false; }
        }
        const next: Motion | string = !frame.alive ? 'defeat' : frame.airborne ? 'jump' : !upper && actionUntil > time ? action : frame.speed > .4 ? 'run' : 'idle';
        if (next !== base) { baseLayer.transition(next, frame.reducedMotion || next === 'defeat' ? 0 : .12); base = next; transitions[next] = (transitions[next] || 0) + 1; }
        if (upper && (time >= actionUntil || !frame.alive || frame.airborne)) {
          if (!fading) { upper.blendToWeight(0, .1); fading = true; }
          if (time >= actionUntil) action = '';
        }
        anim.speed = frame.reducedMotion && base === 'idle' && !action ? 0 : 1;
      },
      setShadows(enabled) { for (const render of renders) render.castShadows = enabled; },
      diagnostic: () => ({ id, heroId, url: this.states.get(heroId)!.url, loaded: true, fallback: false, skinned: true, skeletons: [...skeletons], bones: Math.max(...skins.map(skin => skin.bones.length)), clips: [...tracks.keys()], state: baseLayer.activeState, action: upper && upper.weight > .01 ? upper.activeState : '', animationTime: baseLayer.activeStateCurrentTime,
        poseBones: poseNodes.map(({ name }) => name), pose: poseNodes.flatMap(({ node }) => { const q = node.getLocalRotation(); return [q.x, q.y, q.z, q.w].map(value => Math.round(value * 10000) / 10000); }), transitions: { ...transitions } }),
      destroy: () => { if (disposed) return; disposed = true; aimPass.restore(); this.aimPasses.delete(aimPass); root.destroy(); this.instances.delete(result); },
    };
    this.instances.add(result); return result;
  }

  destroy() {
    if (this.disposed) return; this.disposed = true;
    this.app.off('prerender', this.applyAim, this); this.app.off('postrender', this.restoreAim, this);
    for (const model of [...this.instances]) model.destroy();
    for (const asset of this.assets.values()) { asset.unload(); this.app.assets.remove(asset); }
    this.assets.clear();
  }
}
