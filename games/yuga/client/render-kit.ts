import * as pc from 'playcanvas';

export type Shape = 'box' | 'sphere' | 'cylinder' | 'cone' | 'capsule' | 'plane';
export type XYZ = { x: number; y: number; z: number };
export const RAD = 180 / Math.PI;
export const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));
export const mixAngle = (a: number, b: number, t: number) => a + Math.atan2(Math.sin(b - a), Math.cos(b - a)) * t;

/** Original small procedural meshes, shared by every instance; no imported art. */
export class RenderKit {
  readonly materials: pc.StandardMaterial[] = [];
  readonly textures: pc.Texture[] = [];
  readonly meshes = new Map<Shape, pc.Mesh>();
  readonly staticGroup: number;
  readonly actorGroup: number;
  private readonly cache = new Map<string, pc.StandardMaterial>();

  constructor(readonly app: pc.Application) {
    this.staticGroup = app.batcher.addGroup('Sangam static architecture', false, 45).id;
    this.actorGroup = app.batcher.addGroup('Sangam animated hero and sentinel parts', true, 55).id;
    const shapes: Record<Shape, pc.Geometry> = {
      box: new pc.BoxGeometry(),
      sphere: new pc.SphereGeometry({ latitudeBands: 8, longitudeBands: 12 }),
      cylinder: new pc.CylinderGeometry({ capSegments: 12, heightSegments: 1 }),
      cone: new pc.ConeGeometry({ capSegments: 12, heightSegments: 1 }),
      capsule: new pc.CapsuleGeometry({ sides: 10, heightSegments: 1, radius: .5, height: 2 }),
      plane: new pc.PlaneGeometry({ widthSegments: 1, lengthSegments: 1 }),
    };
    for (const [name, geometry] of Object.entries(shapes)) {
      const mesh = pc.Mesh.fromGeometry(app.graphicsDevice, geometry);
      // The cache owns a reference across an empty actor set or a replay transition.
      mesh.incRefCount(); this.meshes.set(name as Shape, mesh);
    }
  }

  material(name: string, color: string, glow = 0, gloss = .25, opacity = 1) {
    const key = `${name}/${color}/${glow}/${opacity}`;
    const existing = this.cache.get(key); if (existing) return existing;
    const m = new pc.StandardMaterial(); m.name = name;
    m.diffuse.fromString(color); m.gloss = gloss; m.useMetalness = true; m.metalness = .06;
    if (glow) { m.emissive.copy(m.diffuse); m.emissiveIntensity = glow; }
    if (opacity < 1) { m.opacity = opacity; m.blendType = pc.BLEND_NORMAL; m.depthWrite = false; }
    m.update(); this.materials.push(m); this.cache.set(key, m); return m;
  }

  texture(name: string, w: number, h: number, paint: (ctx: CanvasRenderingContext2D) => void) {
    const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext('2d'); if (!ctx) throw new Error('Canvas textures unavailable');
    paint(ctx);
    const texture = new pc.Texture(this.app.graphicsDevice, { name, width: w, height: h, mipmaps: true });
    texture.setSource(canvas); this.textures.push(texture); return texture;
  }

  shape(parent: pc.Entity, type: Shape, m: pc.Material, x: number, y: number, z: number, sx = 1, sy = 1, sz = 1, batch = false) {
    const e = new pc.Entity(type, this.app); parent.addChild(e);
    e.addComponent('render', { meshInstances: [new pc.MeshInstance(this.meshes.get(type)!, m)], castShadows: type !== 'plane', receiveShadows: true });
    e.setLocalPosition(x, y, z); e.setLocalScale(sx, sy, sz);
    if (batch) e.render!.batchGroupId = this.staticGroup;
    return e;
  }

  line(parent: pc.Entity, m: pc.Material, a: XYZ, b: XYZ, width: number, batch = false) {
    const d = new pc.Vec3(b.x - a.x, b.y - a.y, b.z - a.z);
    const length = d.length();
    const e = this.shape(parent, 'cylinder', m, (a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2, width, length, width, batch);
    e.setLocalRotation(new pc.Quat().setFromDirections(pc.Vec3.UP, d.normalize())); return e;
  }

  ring(parent: pc.Entity, m: pc.Material, radius: number, width: number, y: number, segments = 32, batch = false) {
    return this.arc(parent, m, radius, width, y, 0, Math.PI * 2, segments, batch);
  }

  arc(parent: pc.Entity, m: pc.Material, radius: number, width: number, y: number, start: number, end: number, segments = 32, batch = false) {
    const group = new pc.Entity('inlaid ring', this.app); parent.addChild(group); group.setLocalPosition(0, y, 0);
    const positions: number[] = [], normals: number[] = [], uvs: number[] = [], indices: number[] = [];
    for (let i = 0; i <= segments; i++) {
      const a = start + i / segments * (end - start);
      for (const r of [radius - width / 2, radius + width / 2]) {
        positions.push(Math.sin(a) * r, 0, Math.cos(a) * r); normals.push(0, 1, 0); uvs.push(i / segments, r > radius ? 1 : 0);
      }
      if (i < segments) { const n = i * 2; indices.push(n, n + 1, n + 2, n + 1, n + 3, n + 2); }
    }
    const mesh = pc.createMesh(this.app.graphicsDevice, positions, { normals, uvs, indices });
    group.addComponent('render', { meshInstances: [new pc.MeshInstance(mesh, m)], castShadows: false, receiveShadows: true });
    if (batch) group.render!.batchGroupId = this.staticGroup;
    return group;
  }

  sign(parent: pc.Entity, title: string, subtitle: string, color: string, w: number, h: number, x: number, y: number, z: number, yaw = 0) {
    const tex = this.texture(title, 512, 160, ctx => {
      ctx.fillStyle = '#102e38'; ctx.fillRect(0, 0, 512, 160);
      ctx.strokeStyle = color; ctx.lineWidth = 5; ctx.strokeRect(7, 7, 498, 146);
      ctx.textAlign = 'center'; ctx.fillStyle = '#fff1d4'; ctx.font = '600 39px sans-serif'; ctx.fillText(title, 256, 71);
      ctx.fillStyle = color; ctx.font = '500 20px sans-serif'; ctx.fillText(subtitle, 256, 116);
    });
    const m = this.material(`sign ${title}`, '#ffffff', .15); m.diffuseMap = tex; m.emissiveMap = tex; m.update();
    const e = this.shape(parent, 'plane', m, x, y, z, w, 1, h, true); e.setLocalEulerAngles(90, yaw + 180, 0); return e;
  }

  dispose() {
    for (const material of this.materials) material.destroy();
    for (const texture of this.textures) texture.destroy();
    // Shared meshes are released after the scene's mesh instances have been destroyed.
    for (const mesh of this.meshes.values()) { mesh.decRefCount(); if (mesh.refCount === 0) mesh.destroy(); }
  }
}
