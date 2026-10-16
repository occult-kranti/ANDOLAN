import * as pc from 'playcanvas';
import type { HeroModelFrame } from './hero-models';

export const UNIT_IDS = ['soldier', 'city-watch', 'minister', 'king', 'yaksha', 'naga', 'sky-sentinel'] as const;
export type UnitModelId = typeof UNIT_IDS[number];
const CLIPS = ['idle', 'run', 'fire', 'defeat'] as const;
const urls = import.meta.glob('./assets/units/*.glb', { eager: true, query: '?url', import: 'default' }) as Record<string, string>;
export interface UnitAssetDiagnostic {
  unitId: UnitModelId; url: string; state: 'loading' | 'ready' | 'failed'; error?: string;
  triangles: number; materials: number; skinnedPrimitives: number; animations: string[];
}
export interface UnitModel {
  root: pc.Entity;
  update(frame: HeroModelFrame, dt: number): void;
  setShadows(enabled: boolean): void;
  setAnimated(enabled: boolean): void;
  diagnostic(): { id: string; unitId: UnitModelId; url: string; loaded: true; fallback: false; skeletons: number[]; bones: number; clips: string[]; state: string; action: string; animationTime: number; animated: boolean; pose: number[]; transitions: Record<string, number> };
  destroy(): void;
}
function tracksOf(resource: pc.ContainerResource) {
  const tracks = new Map<string, pc.AnimTrack>();
  for (const asset of resource.animations) if (asset.resource instanceof pc.AnimTrack) tracks.set(asset.resource.name.split('|').at(-1)!.replace(/\.\d+$/, '').toLowerCase(), asset.resource);
  return tracks;
}

/** Shared unit meshes, individual skin state. Loading failure remains visible to the caller. */
export class UnitModelLibrary {
  private readonly assets = new Map<UnitModelId, pc.Asset<'container'>>();
  private readonly states = new Map<UnitModelId, UnitAssetDiagnostic>();
  private readonly pending = new Map<UnitModelId, Promise<void>>();
  private readonly instances = new Set<UnitModel>();
  private readonly skinIds = new WeakMap<pc.SkinInstance, number>();
  private nextSkinId = 1;
  private readonly refreshAnimations = new Set<() => void>();
  private active = true;
  private disposed = false;
  constructor(private readonly app: pc.Application) {}

  async preload(progress?: (done: number, total: number, unitId: string) => void) {
    let done = 0;
    const results = await Promise.allSettled(UNIT_IDS.map(async id => { try { await this.load(id); } finally { progress?.(++done, UNIT_IDS.length, id); } }));
    const failed = results.flatMap((r, i) => r.status === 'rejected' ? [UNIT_IDS[i]!] : []);
    if (failed.length) throw new Error(`Unit artwork could not load: ${failed.join(', ')}. Reload to retry.`);
  }
  private load(unitId: UnitModelId): Promise<void> {
    if (this.disposed) return Promise.reject(new Error('Unit scene is closed'));
    if (this.assets.has(unitId)) return Promise.resolve();
    const pending = this.pending.get(unitId); if (pending) return pending;
    const url = urls[`./assets/units/${unitId}.glb`] || '';
    const diagnostic: UnitAssetDiagnostic = { unitId, url, state: 'loading', triangles: 0, materials: 0, skinnedPrimitives: 0, animations: [] };
    this.states.set(unitId, diagnostic);
    const job = new Promise<void>((resolve, reject) => {
      const fail = (error: string, asset?: pc.Asset<'container'>) => {
        diagnostic.state = 'failed'; diagnostic.error = error;
        if (asset) { asset.unload(); this.app.assets.remove(asset); }
        reject(new Error(`${unitId}: ${error}`));
      };
      if (!url) { fail('Published GLB file is missing'); return; }
      this.app.assets.loadFromUrl(url, 'container', (error, asset) => {
        if (error || !asset?.resource) { fail(String(error || 'GLB container unavailable'), asset); return; }
        if (this.disposed) { fail('Scene closed during unit loading', asset); return; }
        const resource = asset.resource, tracks = tracksOf(resource);
        diagnostic.animations = [...tracks.keys()];
        const missing = CLIPS.filter(clip => !tracks.has(clip));
        if (missing.length) { fail(`Missing clips: ${missing.join(', ')}`, asset); return; }
        const probe = resource.instantiateRenderEntity(), meshes = new Set<pc.Mesh>(), materials = new Set<pc.Material>();
        for (const component of probe.findComponents('render') as pc.RenderComponent[]) for (const instance of component.meshInstances) {
          if (instance.mesh) meshes.add(instance.mesh); if (instance.material) materials.add(instance.material); if (instance.skinInstance) diagnostic.skinnedPrimitives++;
        }
        for (const mesh of meshes) for (const primitive of mesh.primitive) if (primitive.type === pc.PRIMITIVE_TRIANGLES) diagnostic.triangles += primitive.count / 3;
        diagnostic.materials = materials.size; probe.destroy();
        if (!diagnostic.skinnedPrimitives) { fail('Unit GLB has no skinned mesh', asset); return; }
        this.assets.set(unitId, asset); diagnostic.state = 'ready'; resolve();
      });
    });
    this.pending.set(unitId, job); void job.finally(() => this.pending.delete(unitId)).catch(() => {});
    return job;
  }

  instantiate(unitId: UnitModelId, id: string, parent: pc.Entity): UnitModel | null {
    const resource = this.assets.get(unitId)?.resource; if (!resource || this.disposed) return null;
    const root = resource.instantiateRenderEntity({ castShadows: true, receiveShadows: true }); root.name = `authored-unit-${unitId}`; parent.addChild(root);
    root.addComponent('anim', { activate: true }); const anim = root.anim!, tracks = tracksOf(resource);
    for (const clip of CLIPS) anim.assignAnimation(clip, tracks.get(clip)!, undefined, 1, clip === 'idle' || clip === 'run');
    const base = anim.baseLayer!; base.play('idle');
    const spine = tracks.get('idle')!.curves.flatMap(curve => curve.paths).find(path => path.entityPath.at(-1) === 'spine03')?.entityPath;
    const action = spine ? anim.addLayer('Action', 0, { [spine.join('/')]: { children: true } } as unknown as object[], pc.ANIM_LAYER_OVERWRITE) : undefined;
    if (action) anim.assignAnimation('fire', tracks.get('fire')!, 'Action', 1, false);
    const renders = root.findComponents('render') as pc.RenderComponent[];
    const skins = [...new Set(renders.flatMap(r => r.meshInstances.map(m => m.skinInstance)).filter((s): s is pc.SkinInstance => !!s))];
    const skeletons = skins.map(skin => { if (!this.skinIds.has(skin)) this.skinIds.set(skin, this.nextSkinId++); return this.skinIds.get(skin)!; });
    const poseNodes = ['spine03', 'upperarm01.L', 'upperarm01.R', 'upperleg01.L', 'lowerleg01.L', 'upperleg01.R'].flatMap(name => { const node = root.findByName(name); return node ? [node] : []; });
    const transitions: Record<string, number> = { idle: 1 };
    let clock = 0, shotId = 0, attackUntil = 0, state = 'idle', dead = false, animate = true, disposed = false;
    const setEnabled = () => { anim.enabled = this.active && animate; };
    const model: UnitModel = {
      root,
      update(frame, dt) {
        if (disposed) return; clock += dt;
        if (frame.alive && dead) { state = ''; attackUntil = 0; if (action) action.weight = 0; }
        dead = !frame.alive;
        if (frame.alive && frame.shot > shotId) {
          attackUntil = clock + tracks.get('fire')!.duration;
          transitions.fire = (transitions.fire || 0) + 1;
          if (action) { action.transition('fire', .04); action.weight = 1; }
        }
        shotId = frame.shot;
        if (action && (dead || clock >= attackUntil)) action.weight = 0;
        const next = dead ? 'defeat' : !action && clock < attackUntil ? 'fire' : frame.speed > .3 ? 'run' : 'idle';
        if (next !== state) { base.transition(next, dead || frame.reducedMotion ? 0 : .09); state = next; transitions[next] = (transitions[next] || 0) + 1; }
        anim.speed = frame.reducedMotion && state === 'idle' && clock >= attackUntil ? 0 : 1;
      },
      setShadows(enabled) { for (const r of renders) r.castShadows = enabled; },
      setAnimated(enabled) { animate = enabled; setEnabled(); },
      diagnostic: () => ({ id, unitId, url: this.states.get(unitId)!.url, loaded: true, fallback: false, skeletons: [...skeletons], bones: Math.max(...skins.map(s => s.bones.length)), clips: [...tracks.keys()], state: base.activeState, action: action && action.weight > .01 ? action.activeState : '', animationTime: base.activeStateCurrentTime, animated: anim.enabled,
        pose: poseNodes.flatMap(node => { const q = node.getLocalRotation(); return [q.x, q.y, q.z, q.w].map(v => Math.round(v * 10000) / 10000); }), transitions: { ...transitions } }),
      destroy: () => { if (disposed) return; disposed = true; root.destroy(); this.instances.delete(model); this.refreshAnimations.delete(setEnabled); },
    };
    this.instances.add(model); this.refreshAnimations.add(setEnabled); setEnabled(); return model;
  }
  setActive(enabled: boolean) { this.active = enabled; for (const refresh of this.refreshAnimations) refresh(); }
  diagnostics() { return { assets: [...this.states.values()].map(s => ({ ...s, animations: [...s.animations] })), instances: [...this.instances].map(m => m.diagnostic()) }; }
  destroy() { if (this.disposed) return; this.disposed = true; for (const model of [...this.instances]) model.destroy(); for (const asset of this.assets.values()) { asset.unload(); this.app.assets.remove(asset); } this.assets.clear(); }
}
