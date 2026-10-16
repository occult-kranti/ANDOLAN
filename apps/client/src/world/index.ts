import * as pc from 'playcanvas';
import { WORLD } from '../../../../packages/sim/src/world';
import type { Snapshot, PlayerSnapshot, VehicleSnapshot } from '../../../../packages/protocol/src/index';

/** All meshes, signs, maps and textures in this scene are original and generated here. */
export interface WorldView {
  update(snapshot: Snapshot | null, localPlayerId: string | null, dt: number): void;
  setQuality(quality: 'low' | 'high'): void;
  setCamera(yawDelta: number, pitchDelta: number): void;
  setComfort(enabled: boolean): void;
  setOverview(enabled: boolean): void;
  getCameraYaw(): number;
  project(x: number, z: number, y?: number): { x: number; y: number; visible: boolean };
  destroy(): void;
}

type Person = { root: pc.Entity; leftArm: pc.Entity; rightArm: pc.Entity; leftLeg: pc.Entity; rightLeg: pc.Entity; phase: number; lastX: number; lastZ: number };
type Car = { root: pc.Entity; wheels: pc.Entity[]; phase: number };
type Pedestrian = { person: Person; startX: number; startZ: number; alongX: boolean; length: number; speed: number; offset: number };
type Quality = 'high' | 'low';
const RAD = 180 / Math.PI;
const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n));
const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const angleMix = (a: number, b: number, t: number) => a + Math.atan2(Math.sin(b - a), Math.cos(b - a)) * t;

export async function createWorld(canvas: HTMLCanvasElement): Promise<WorldView> {
  const app = new pc.Application(canvas, {
    graphicsDeviceOptions: { alpha: false, antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true },
  });
  app.setCanvasFillMode(pc.FILLMODE_NONE);
  app.setCanvasResolution(pc.RESOLUTION_AUTO);
  app.graphicsDevice.maxPixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
  app.scene.ambientLight = new pc.Color(0.50, 0.53, 0.54);
  app.scene.exposure = 1.05;
  app.scene.fog.type = pc.FOG_LINEAR;
  app.scene.fog.color = new pc.Color(0.61, 0.66, 0.67);
  app.scene.fog.start = 85;
  app.scene.fog.end = 210;
  const staticGroup = app.batcher.addGroup('Devnagar architecture', false, 48);
  const dynamicGroup = app.batcher.addGroup('Citizens and vehicles', true, 80);
  const materials: pc.StandardMaterial[] = [];
  const textures: pc.Texture[] = [];
  const root = new pc.Entity('DEVNAGAR / OLD MARKET');
  app.root.addChild(root);
  let quality: Quality = 'high';
  let elapsed = 0;
  let cameraYaw = -Math.PI / 2;
  let cameraPitch = 0.30;
  let lastOrbit = -100;
  let cameraInitialized = false;
  let overview = false;
  let comfort = false;
  const people = new Map<string, Person>();
  const vehicles = new Map<string, Car>();
  const pedestrians: Pedestrian[] = [];

  function mat(name: string, color: string, gloss = 0.1, emission = 0): pc.StandardMaterial {
    const material = new pc.StandardMaterial();
    material.name = name;
    material.diffuse = new pc.Color().fromString(color);
    material.gloss = gloss;
    material.useMetalness = true;
    material.metalness = 0.02;
    if (emission > 0) { material.emissive.copy(material.diffuse); material.emissiveIntensity = emission; }
    material.update(); materials.push(material); return material;
  }
  const M = {
    stone: mat('warm concrete', '#adab96'), curb: mat('sandstone kerb', '#d0c3a5'),
    white: mat('painted ivory', '#e0d6b9'), cream: mat('old plaster', '#d5bf91'),
    dark: mat('ink metal', '#26383b', 0.35), metal: mat('aged steel', '#63716b', 0.55),
    asphalt: mat('rain-dark asphalt', '#82969a', 0.38), roadLine: mat('worn lane paint', '#ada88e', 0.2),
    teal: mat('market teal', '#206565'), blue: mat('deep petrol blue', '#375c6a'),
    terracotta: mat('burnt clay', '#a95f41'), yellow: mat('saffron paint', '#d6a947'),
    red: mat('muted vermilion', '#993e36'), wood: mat('dark teak', '#684e3d'),
    rubber: mat('rubber', '#202b2c'), glass: mat('rainy blue glass', '#30545d', 0.8),
    leaf: mat('mature foliage', '#375e4d'), leafLight: mat('new leaves', '#60794a'),
    grass: mat('park grass', '#687557'), trunk: mat('tree bark', '#605341'),
    amber: mat('warm shop light', '#efbe70', 0.15, 0.55), lamp: mat('streetlight glow', '#ffe2a3', 0.3, 2),
    sky: mat('horizon', '#a7b1ac'), puddle: mat('puddle reflection', '#5b7278', 0.45),
    skin: mat('warm skin', '#a77351'), hair: mat('dark hair', '#293232'),
    paper: mat('paper', '#e2d8b8'), marker: mat('objective gold', '#edc75d', 0.4, 0.65),
    brake: mat('tail lights', '#e76d4f', 0.1, 0.5), headlamp: mat('head lights', '#f7e5be', 0.1, 1.2),
  };

  function texture(name: string, width: number, height: number, paint: (ctx: CanvasRenderingContext2D) => void) {
    const el = document.createElement('canvas'); el.width = width; el.height = height;
    const ctx = el.getContext('2d')!; paint(ctx);
    const tex = new pc.Texture(app.graphicsDevice, { name, width, height, mipmaps: true });
    tex.setSource(el); textures.push(tex); return tex;
  }
  let randomState = 8917;
  function random() { randomState = (randomState * 1664525 + 1013904223) >>> 0; return randomState / 4294967296; }
  const asphaltTexture = texture('original asphalt noise', 256, 256, c => {
    c.fillStyle = '#61747a'; c.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 5500; i++) { c.fillStyle = random() > 0.5 ? '#73878c' : '#455c64'; c.globalAlpha = 0.2 + random() * 0.3; c.fillRect(random() * 256, random() * 256, 1 + random() * 2, 1 + random() * 2); }
    c.globalAlpha = 0.18; c.strokeStyle = '#182f37'; c.lineWidth = 1;
    for (let i = 0; i < 6; i++) { c.beginPath(); let x = random() * 256; let y = random() * 256; c.moveTo(x, y); for (let j = 0; j < 5; j++) { x += random() * 30 - 15; y += 16; c.lineTo(x, y); } c.stroke(); }
  });
  M.asphalt.diffuseMap = asphaltTexture; M.asphalt.diffuseMapTiling.set(24, 24); M.asphalt.update();
  const stuccoTexture = texture('original plaster patina', 128, 128, c => {
    c.fillStyle = '#f7f2df'; c.fillRect(0, 0, 128, 128);
    for (let i = 0; i < 1800; i++) { c.globalAlpha = random() * 0.06; c.fillStyle = '#34332d'; c.fillRect(random() * 128, random() * 128, 1 + random() * 4, 2 + random() * 7); }
  });
  const sidewalkTexture = texture('original stone joints', 128, 128, c => {
    c.fillStyle = '#d5d0b8'; c.fillRect(0, 0, 128, 128); c.strokeStyle = '#adae9d'; c.lineWidth = 2;
    c.strokeRect(0, 0, 64, 64); c.strokeRect(64, 0, 64, 64); c.strokeRect(-32, 64, 64, 64); c.strokeRect(32, 64, 64, 64); c.strokeRect(96, 64, 64, 64);
  });
  M.stone.diffuseMap = sidewalkTexture; M.stone.diffuseMapTiling.set(8, 8); M.stone.update();
  M.puddle.opacity = 0.28; M.puddle.blendType = pc.BLEND_NORMAL; M.puddle.depthWrite = false; M.puddle.update();
  const lampPoolTexture = texture('original soft lamp falloff', 128, 128, c => {
    const gradient = c.createRadialGradient(64, 64, 0, 64, 64, 63);
    gradient.addColorStop(0, 'rgba(255,220,151,0.16)'); gradient.addColorStop(0.45, 'rgba(255,220,151,0.08)'); gradient.addColorStop(1, 'rgba(255,220,151,0)');
    c.fillStyle = gradient; c.fillRect(0, 0, 128, 128);
  });
  const lampPool = mat('soft streetlamp reflection', '#edd5a2', 0, 0.1);
  lampPool.diffuseMap = lampPoolTexture; lampPool.opacityMap = lampPoolTexture; lampPool.opacityMapChannel = 'a'; lampPool.blendType = pc.BLEND_NORMAL; lampPool.depthWrite = false; lampPool.update();
  const destinationTexture = texture('original destination ring', 128, 128, c => {
    const gradient = c.createRadialGradient(64, 64, 0, 64, 64, 63);
    gradient.addColorStop(0, 'rgba(236,190,82,0)'); gradient.addColorStop(0.72, 'rgba(236,190,82,0)'); gradient.addColorStop(0.79, 'rgba(236,190,82,0.65)'); gradient.addColorStop(0.86, 'rgba(236,190,82,0)'); gradient.addColorStop(1, 'rgba(236,190,82,0)');
    c.fillStyle = gradient; c.fillRect(0, 0, 128, 128);
  });
  const destinationRing = mat('soft destination ring', '#ecc363', 0, 0.5);
  destinationRing.diffuseMap = destinationTexture; destinationRing.opacityMap = destinationTexture; destinationRing.opacityMapChannel = 'a'; destinationRing.blendType = pc.BLEND_NORMAL; destinationRing.depthWrite = false; destinationRing.update();

  function primitive(name: string, type: 'box' | 'sphere' | 'cylinder' | 'cone' | 'capsule' | 'plane', material: pc.Material,
    x: number, y: number, z: number, sx: number, sy: number, sz: number, parent = root, batch = true) {
    const e = new pc.Entity(name); e.addComponent('render', { type, material, castShadows: true, receiveShadows: true });
    e.setLocalPosition(x, y, z); e.setLocalScale(sx, sy, sz); parent.addChild(e);
    if (batch && e.render) e.render.batchGroupId = staticGroup.id;
    return e;
  }
  const box = (name: string, material: pc.Material, x: number, y: number, z: number, sx: number, sy: number, sz: number, parent = root, batch = true) => primitive(name, 'box', material, x, y, z, sx, sy, sz, parent, batch);
  const cylinder = (name: string, material: pc.Material, x: number, y: number, z: number, sx: number, sy: number, sz: number, parent = root, batch = true) => primitive(name, 'cylinder', material, x, y, z, sx, sy, sz, parent, batch);
  const sphere = (name: string, material: pc.Material, x: number, y: number, z: number, sx: number, sy: number, sz: number, parent = root, batch = true) => primitive(name, 'sphere', material, x, y, z, sx, sy, sz, parent, batch);
  function batchMovingParts(entity: pc.Entity) {
    if (entity.render) entity.render.batchGroupId = dynamicGroup.id;
    for (const child of entity.children) if (child instanceof pc.Entity) batchMovingParts(child);
  }

  function sign(text: string, subtitle: string, x: number, y: number, z: number, width: number, height: number, yaw = 0, background = '#1f5053', foreground = '#f2e3b9') {
    const tex = texture(`original sign: ${text}`, 1024, 256, c => {
      c.fillStyle = background; c.fillRect(0, 0, 1024, 256);
      c.strokeStyle = foreground; c.lineWidth = 4; c.strokeRect(15, 15, 994, 226);
      c.fillStyle = foreground; c.textAlign = 'center'; c.textBaseline = 'middle';
      c.font = `700 ${text.length > 18 ? 58 : 76}px sans-serif`; c.fillText(text, 512, subtitle ? 103 : 130, 950);
      if (subtitle) { c.font = '500 28px sans-serif'; c.fillText(subtitle.toUpperCase().split('').join(' '), 512, 188, 930); }
    });
    const material = mat(`sign ${text}`, '#ffffff', 0.05, 0.15); material.diffuseMap = tex; material.emissiveMap = tex; material.cull = pc.CULLFACE_NONE; material.update();
    const panel = primitive(text, 'plane', material, x, y, z, width, 1, height);
    panel.setLocalEulerAngles(90, yaw, 0); return panel;
  }

  function line(name: string, material: pc.Material, from: [number, number, number], to: [number, number, number], radius = 0.04, parent = root) {
    const a = new pc.Vec3(...from); const b = new pc.Vec3(...to); const direction = b.clone().sub(a);
    const e = cylinder(name, material, (a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2, radius, direction.length(), radius, parent);
    e.setLocalRotation(new pc.Quat().setFromDirections(pc.Vec3.UP, direction.normalize())); return e;
  }

  const sun = new pc.Entity('Monsoon sunset'); sun.addComponent('light', { type: 'directional', color: new pc.Color(1, 0.89, 0.74), intensity: 1.25, castShadows: true, shadowDistance: 95, shadowResolution: 2048, shadowType: pc.SHADOW_PCF3, normalOffsetBias: 0.08, shadowBias: 0.2, numCascades: 2 }); sun.setEulerAngles(43, -38, -12); root.addChild(sun);
  const camera = new pc.Entity('Third person camera'); camera.addComponent('camera', { clearColor: new pc.Color(0.62, 0.68, 0.68), farClip: 350, nearClip: 0.1, fov: 61 }); root.addChild(camera);
  camera.camera!.toneMapping = pc.TONEMAP_ACES;
  camera.setPosition(-60, 5, 55); camera.lookAt(-52, 1.4, 48);
  const skyTexture = texture('original monsoon dusk gradient', 512, 512, c => {
    const gradient = c.createLinearGradient(0, 0, 0, 512);
    gradient.addColorStop(0, '#526b77'); gradient.addColorStop(0.36, '#7f959b'); gradient.addColorStop(0.50, '#c4b89e'); gradient.addColorStop(0.64, '#7f959b'); gradient.addColorStop(1, '#526b77');
    c.fillStyle = gradient; c.fillRect(0, 0, 512, 512);
  });
  const skyMaterial = mat('painted monsoon sky', '#ffffff', 0, 1);
  skyMaterial.emissiveMap = skyTexture; skyMaterial.useLighting = false; skyMaterial.useFog = false; skyMaterial.cull = pc.CULLFACE_FRONT; skyMaterial.depthWrite = false; skyMaterial.update();
  const skyDome = sphere('monsoon sky dome', skyMaterial, 0, 0, 0, 570, 570, 570, root, false); skyDome.render!.castShadows = false;

  // Streets are authored from the exact grid used by the authoritative collision map.
  box('wet street foundation', M.asphalt, 0, -0.18, 0, 204, 0.3, 204);
  const blockCenters = [-74, -24, 24, 74];
  for (const x of blockCenters) for (const z of blockCenters) {
    const edge = Math.abs(x) === 74 || Math.abs(z) === 74;
    box('raised sidewalk block', M.stone, x, -0.04, z, Math.abs(x) === 74 ? 33 : 33, 0.24, Math.abs(z) === 74 ? 33 : 33);
    // Low sandstone edges catch the sunset and clearly define driveable space.
    box('sidewalk east kerb', M.curb, x + 16.5, 0.07, z, 0.3, 0.25, 33);
    box('sidewalk west kerb', M.curb, x - 16.5, 0.07, z, 0.3, 0.25, 33);
    box('sidewalk north kerb', M.curb, x, 0.07, z + 16.5, 33, 0.25, 0.3);
    box('sidewalk south kerb', M.curb, x, 0.07, z - 16.5, 33, 0.25, 0.3);
    void edge;
  }
  for (const street of WORLD.roads) {
    for (let d = -94; d < 97; d += 8) if (!WORLD.roads.some(v => Math.abs(v - d) < 9)) {
      box('lane divider', M.roadLine, street, 0.007, d, 0.15, 0.018, 3.6);
      box('lane divider', M.roadLine, d, 0.009, street, 3.6, 0.018, 0.15);
    }
    for (const crossing of WORLD.roads) {
      for (let d = -4; d <= 4; d += 1.8) {
        box('pedestrian crossing', M.roadLine, street + d, 0.012, crossing + 8, 0.8, 0.018, 2.6);
        box('pedestrian crossing', M.roadLine, street + 8, 0.014, crossing + d, 2.6, 0.018, 0.8);
      }
    }
  }
  for (let i = 0; i < 45; i++) {
    const road = WORLD.roads[i % 3]; const d = random() * 190 - 95; const off = (random() > 0.5 ? 1 : -1) * (3.5 + random());
    const puddle = sphere('shallow street puddle', M.puddle, i % 2 ? road + off : d, 0.001, i % 2 ? d : road + off, 1 + random() * 1.7, 0.007, 2 + random() * 2);
    puddle.setEulerAngles(0, random() * 180, 0); puddle.render!.castShadows = false;
  }

  const shopNames = [['KIRAN STORES', 'PROVISIONS · EVERY DAY'], ['SUNEHRI CHAI', 'TEA & CONVERSATION'], ['CITY CYCLE WORKS', 'REPAIR · RESTORE · RIDE'], ['NAYA PRINT', 'IDEAS ON PAPER'], ['MEERA TEXTILES', 'WOVEN IN DEVNAGAR'], ['MONSOON BOOKS', 'STORIES LIVE HERE'], ['OLD MARKET', 'FRESH FRUIT & FLOWERS'], ['AADI ELECTRICAL', 'LIGHTING THE CITY']];
  const awningColors = [M.teal, M.yellow, M.red, M.blue];
  WORLD.buildings.forEach((b, buildingIndex) => {
    const facade = mat(`plaster ${b.id}`, b.color); facade.diffuseMap = stuccoTexture; facade.diffuseMapTiling.set(2, 2); facade.update();
    box(b.id, facade, b.x, b.height / 2, b.z, b.width, b.height, b.depth);
    box('roof cornice', M.cream, b.x, b.height + 0.12, b.z, b.width + 0.6, 0.38, b.depth + 0.6);
    box('roof inset', M.dark, b.x, b.height + 0.34, b.z, b.width - 0.5, 0.05, b.depth - 0.5);
    for (let level = 4.2; level < b.height - 0.8; level += 3.8) {
      box('floor moulding', M.cream, b.x, level - 1.1, b.z, b.width + 0.22, 0.16, b.depth + 0.22);
      for (let wx = -b.width / 2 + 2.4; wx < b.width / 2 - 1; wx += 4.3) {
        for (const side of [-1, 1]) {
          const z = b.z + side * (b.depth / 2 + 0.055);
          box('window recess', M.dark, b.x + wx, level, z, 1.65, 2.0, 0.12);
          box('window pane', (buildingIndex + Math.floor(wx) + Math.floor(level)) % 4 === 0 ? M.amber : M.glass, b.x + wx, level + 0.02, z + side * 0.07, 1.36, 1.7, 0.05);
          box('window sill', M.cream, b.x + wx, level - 1.02, z + side * 0.12, 1.94, 0.16, 0.38);
          box('window mullion', M.cream, b.x + wx, level, z + side * 0.11, 0.075, 1.8, 0.07);
        }
      }
      for (let wz = -b.depth / 2 + 2.6; wz < b.depth / 2 - 1; wz += 4.5) {
        for (const side of [-1, 1]) {
          const x = b.x + side * (b.width / 2 + 0.06);
          box('window recess', M.dark, x, level, b.z + wz, 0.12, 2, 1.65);
          box('window pane', (buildingIndex + Math.floor(wz)) % 5 === 0 ? M.amber : M.glass, x + side * 0.07, level + 0.02, b.z + wz, 0.05, 1.7, 1.36);
          box('window sill', M.cream, x + side * 0.12, level - 1.02, b.z + wz, 0.38, 0.16, 1.94);
        }
      }
    }
    // Small ground-floor storefronts add human scale on every visible street edge.
    for (const front of [-1, 1]) {
    const doorZ = b.z + front * (b.depth / 2 + 0.12);
    for (let j = -1; j <= 1; j++) {
      const x = b.x + j * (b.width / 3); const awning = awningColors[(buildingIndex + j + 5) % awningColors.length];
      box('shopfront shadow', M.dark, x, 1.45, doorZ, b.width / 3 - 0.9, 2.75, 0.1);
      box('shop front glass', M.glass, x - 0.65, 1.5, doorZ + front * 0.08, b.width / 3 - 2.5, 2.5, 0.04);
      for (let k = 0; k < 7; k++) {
        const canopy = box('striped canvas awning', k % 2 ? M.cream : awning, x - (b.width / 3 - 0.7) / 2 + k * (b.width / 3 - 0.7) / 7, 3.1, doorZ + front * 0.85, (b.width / 3 - 0.7) / 7 + 0.01, 0.12, 1.8);
        canopy.setLocalEulerAngles(front * -11, 0, 0);
      }
      box('awning valance', awning, x - 0.5, 2.92, doorZ + front * 1.7, b.width / 3 - 0.7, 0.36, 0.07);
    }
    const text = shopNames[buildingIndex % shopNames.length];
    sign(text[0], text[1], b.x, 3.85, doorZ + front * 0.18, b.width - 1.7, 1.3, front > 0 ? 0 : 180, buildingIndex % 3 === 0 ? '#793e31' : '#285654');
    }
    const sideX = b.x - b.width / 2 - 0.12;
    const sideShop = shopNames[(buildingIndex + 3) % shopNames.length];
    sign(sideShop[0], sideShop[1], sideX - 0.06, 3.6, b.z, b.depth - 2.4, 1.25, -90, buildingIndex % 2 ? '#947844' : '#345b61');
    for (let j = -1; j <= 1; j++) {
      const z = b.z + j * b.depth / 3;
      box('west shop window', M.dark, sideX, 1.45, z, 0.1, 2.7, b.depth / 3 - 1.1);
      box('west shop glass', M.glass, sideX - 0.07, 1.45, z, 0.05, 2.4, b.depth / 3 - 1.5);
      const canopy = box('west shop canopy', awningColors[buildingIndex % awningColors.length], sideX - 0.65, 3, z, 1.5, 0.12, b.depth / 3 - 0.7); canopy.setEulerAngles(0, 0, -9);
      box('west canopy hem', M.cream, sideX - 1.4, 2.8, z, 0.08, 0.25, b.depth / 3 - 0.7);
    }
    // Roof tanks, antennae and stairs give the skyline an authored silhouette.
    cylinder('rooftop water tank', M.dark, b.x + b.width * 0.26, b.height + 1.45, b.z + b.depth * 0.2, 2.4, 2.2, 2.4);
    cylinder('tank lid', M.metal, b.x + b.width * 0.26, b.height + 2.59, b.z + b.depth * 0.2, 2.55, 0.1, 2.55);
    box('roof stairwell', facade, b.x - b.width * 0.25, b.height + 1.2, b.z - b.depth * 0.23, 4, 2.4, 4.5);
    line('antenna pole', M.metal, [b.x, b.height + 0.3, b.z], [b.x, b.height + 4.8, b.z], 0.055);
    for (let a = 0; a < 3; a++) line('antenna crosspiece', M.metal, [b.x - 0.8 + a * 0.15, b.height + 4.3 - a * 0.4, b.z], [b.x + 0.8 - a * 0.15, b.height + 4.3 - a * 0.4, b.z], 0.035);
  });

  function tree(x: number, z: number, scale = 1) {
    cylinder('rain tree trunk', M.trunk, x, 2.3 * scale, z, 0.45 * scale, 4.6 * scale, 0.45 * scale);
    const crown = sphere('rain tree crown', M.leaf, x, 5.6 * scale, z, 5.3 * scale, 3.2 * scale, 4.3 * scale); crown.setEulerAngles(0, random() * 80, 0);
    sphere('rain tree crown light', M.leafLight, x + 1 * scale, 6.1 * scale, z - 0.7 * scale, 3.7 * scale, 2.1 * scale, 3.6 * scale);
    sphere('rain tree crown shade', M.leaf, x - 1.4 * scale, 5.2 * scale, z + 0.6 * scale, 3.3 * scale, 2.5 * scale, 3.8 * scale);
    cylinder('tree bed', M.trunk, x, 0.15, z, 1.5 * scale, 0.1, 1.5 * scale);
  }
  function bench(x: number, z: number, yaw = 0) {
    const seat = new pc.Entity('public bench'); seat.setPosition(x, 0, z); seat.setEulerAngles(0, yaw, 0); root.addChild(seat);
    for (let i = 0; i < 4; i++) box('bench slat', M.wood, 0, 0.65, -0.25 + i * 0.18, 2.4, 0.1, 0.14, seat);
    for (let i = 0; i < 3; i++) box('bench back', M.wood, 0, 0.9 + i * 0.18, 0.36, 2.4, 0.13, 0.1, seat);
    box('bench foot', M.dark, -0.85, 0.3, 0, 0.12, 0.6, 0.7, seat); box('bench foot', M.dark, 0.85, 0.3, 0, 0.12, 0.6, 0.7, seat);
  }
  function streetLamp(x: number, z: number, yaw = 0) {
    const pole = new pc.Entity('municipal streetlamp'); pole.setPosition(x, 0, z); pole.setEulerAngles(0, yaw, 0); root.addChild(pole);
    cylinder('lamp post base', M.dark, 0, 0.3, 0, 0.4, 0.6, 0.4, pole);
    cylinder('lamp post', M.dark, 0, 3.9, 0, 0.16, 7.8, 0.16, pole);
    line('lamp arm', M.dark, [0, 7.4, 0], [1.3, 7.8, 0], 0.14, pole);
    box('lamp hood', M.dark, 1.4, 7.8, 0, 1.1, 0.2, 0.55, pole);
    box('lamp glass', M.lamp, 1.4, 7.68, 0, 0.87, 0.08, 0.36, pole);
    const pool = primitive('soft lamp pool', 'plane', lampPool, x + Math.cos(yaw / RAD) * 1.4, 0.018, z - Math.sin(yaw / RAD) * 1.4, 4.2, 1, 4.2); pool.render!.castShadows = false;
  }
  for (const road of WORLD.roads) {
    for (const d of [-88, -65, -32, -13, 14, 33, 65, 88]) {
      streetLamp(road - 7.8, d, 0);
      if (road !== 0 || Math.abs(d) < 40) streetLamp(d, road + 7.8, 90);
    }
  }
  // Civic trees and small parklets soften the hard grid without blocking travel.
  for (const [x, z] of [[-40, 16], [-39, 33], [40, 16], [39, -33], [-40, -16], [58, 38], [37, 60], [-37, -60], [-88, 37], [-88, 59], [88, -39], [88, 38]]) tree(x, z, 0.85 + random() * 0.25);
  for (const [x, z] of [[-38, 27], [38, 30], [38, -30], [-38, -32]]) bench(x, z, 90);
  // Telephone wires have a gentle sag between their supports.
  for (const road of [-48, 48]) {
    for (let d = -78; d < 80; d += 26) {
      cylinder('utility pole', M.wood, road + 7.3, 4.9, d, 0.18, 9.8, 0.18);
      box('utility crossbar', M.dark, road + 7.3, 9.3, d, 1.5, 0.12, 0.12);
      if (d < 78) for (let k = 0; k < 8; k++) {
        const t1 = k / 8; const t2 = (k + 1) / 8;
        line('overhead cable', M.dark, [road + 7.3, 9.3 - Math.sin(t1 * Math.PI) * 0.8, d + t1 * 26], [road + 7.3, 9.3 - Math.sin(t2 * Math.PI) * 0.8, d + t2 * 26], 0.022);
      }
    }
  }

  // Headquarters: a drive-in workshop with a real open floor and a visible evidence wall.
  box('garage floor', M.stone, -69.5, 0.01, 48, 23, 0.18, 22);
  box('garage back wall', M.teal, -80, 3.8, 48, 0.5, 7.6, 23);
  box('garage north wall', M.cream, -69.5, 3.8, 36.7, 21, 7.6, 0.4);
  box('garage south wall', M.cream, -69.5, 3.8, 59.3, 21, 7.6, 0.4);
  box('garage roof', M.terracotta, -69.5, 7.7, 48, 23, 0.5, 23.6);
  box('garage fascia', M.teal, -58, 6.7, 48, 0.6, 2, 23);
  for (const z of [36.7, 59.3]) box('garage entrance pillar', M.cream, -58, 3.1, z, 0.7, 6.2, 0.7);
  sign('YUSUF’S GARAGE', 'REPAIR · RESTORE · KEEP GOING', -57.64, 6.75, 48, 20.6, 1.75, 90, '#245653');
  sign('THE NEWSROOM', 'INDEPENDENT · LOCAL · OPEN', -69.5, 8.6, 36.5, 14, 1.6, 180, '#e1c887', '#343f3d');
  box('workbench', M.wood, -77.6, 0.95, 52, 1.5, 0.22, 7);
  box('tool chest', M.red, -77.8, 0.6, 56, 1.2, 1.1, 1.7);
  for (let i = 0; i < 4; i++) box('drawer pull', M.metal, -77.13, 0.2 + i * 0.23, 56, 0.04, 0.04, 1.2);
  for (const z of [53, 54.5]) { const tyre = cylinder('spare tyre', M.rubber, -76.5, 0.55, z, 1, 0.45, 1); tyre.setEulerAngles(0, 0, 90); }
  box('workshop lamp', M.lamp, -69, 7.36, 46, 7.5, 0.08, 0.25);
  box('evidence board frame', M.wood, -69, 2.45, 37.1, 7, 3.5, 0.15);
  box('evidence board felt', M.dark, -69, 2.45, 37.21, 6.7, 3.2, 0.08);
  const recordTexture = texture('original public record page', 256, 256, c => {
    c.fillStyle = '#e3d6b0'; c.fillRect(0, 0, 256, 256); c.fillStyle = '#485451'; c.font = '700 20px sans-serif';
    c.fillText('DEVNAGAR', 18, 35); c.font = '12px sans-serif'; c.fillText('PUBLIC RECORD / C-17', 18, 59);
    c.fillRect(18, 74, 216, 2); c.globalAlpha = 0.5;
    for (let i = 0; i < 8; i++) c.fillRect(18, 95 + i * 14, i % 3 === 0 ? 160 : 215, 3);
    c.globalAlpha = 1; c.font = '10px sans-serif'; c.fillText('A QUESTION. CHECK THE SOURCE.', 18, 237);
  });
  const recordMaterial = mat('pinned record paper', '#ffffff'); recordMaterial.diffuseMap = recordTexture; recordMaterial.update();
  const evidencePapers: pc.Entity[] = []; const evidenceThreads: pc.Entity[] = [];
  for (let i = 0; i < 6; i++) {
    const x = -71.2 + i % 3 * 2.15; const y = 1.7 + Math.floor(i / 3) * 1.5;
    const note = box('record earned through investigation', recordMaterial, x, y, 37.29, 1.4, 1.0, 0.04, root, false); note.setEulerAngles(0, 0, (i % 3 - 1) * 7); note.enabled = false; evidencePapers.push(note);
    if (i > 0) {
      const previousX = -71.2 + (i - 1) % 3 * 2.15; const previousY = 1.7 + Math.floor((i - 1) / 3) * 1.5;
      const thread = box('record comparison thread', M.terracotta, (x + previousX) / 2, (y + previousY) / 2, 37.34, Math.hypot(x - previousX, y - previousY), 0.035, 0.025, root, false);
      thread.setEulerAngles(0, 0, Math.atan2(y - previousY, x - previousX) * RAD); thread.enabled = false; evidenceThreads.push(thread);
    }
  }
  sign('START WITH A QUESTION', 'THE DEVNAGAR OBSERVER', -69, 4.9, 37.2, 7, 0.85, 0, '#345855');
  box('kitchen table', M.wood, -62, 0.8, 55, 3.2, 0.15, 1.6);
  cylinder('chai pot', M.metal, -62.5, 1.1, 55, 0.4, 0.5, 0.4);
  for (let i = 0; i < 3; i++) cylinder('chai cup', M.cream, -61.8 + i * 0.38, 0.95, 55.2, 0.2, 0.2, 0.2);
  bench(-62, 56.5);

  // The night desk occupies the open clinic arcade directly off the east ring road.
  box('clinic terrace', M.stone, 68, 0.04, -48, 22, 0.22, 17);
  box('clinic back wall', M.cream, 79, 3.2, -48, 0.5, 6.4, 17);
  box('clinic rear wing', M.white, 70, 5, -58, 18, 10, 3);
  box('clinic roof', M.teal, 68, 6.6, -48, 23, 0.4, 18);
  for (const z of [-40, -56]) box('clinic pillar', M.white, 57, 3.2, z, 0.55, 6.4, 0.55);
  sign('NIGHT CLINIC', 'CARE FOR EVERY NEIGHBOUR', 56.64, 5.7, -48, 15, 1.7, -90, '#355c52');
  box('clinic desk', M.teal, 65, 0.9, -48, 1.4, 1.8, 4);
  box('clinic desk top', M.white, 64.9, 1.85, -48, 1.7, 0.1, 4.3);
  for (const z of [-45, -51]) bench(73, z, 90);
  box('clinic cross horizontal', M.white, 56.55, 3.8, -43, 0.05, 0.35, 1.7);
  box('clinic cross vertical', M.white, 56.5, 3.8, -43, 0.05, 1.7, 0.35);
  box('clinic warm strip', M.lamp, 65, 6.3, -48, 0.2, 0.08, 10);
  const restoredSupplies = new pc.Entity('supplies restored after the depot visit'); root.addChild(restoredSupplies);
  for (let i = 0; i < 3; i++) {
    box('replacement clinic supply crate', M.cream, 68, 0.55, -53 + i * 1.2, 1.1, 1.1, 1, restoredSupplies, false);
    box('supply crate clinic mark', M.teal, 67.43, 0.55, -53 + i * 1.2, 0.04, 0.45, 0.45, restoredSupplies, false);
  }
  restoredSupplies.enabled = false;

  // Freestanding readable landmarks leave all server-owned objective circles reachable.
  sign('CITY RECORDS', 'PUBLIC ARCHIVE · EAST WING', 56.5, 4.6, -66, 11, 1.6, -90, '#92734c');
  box('archive canopy', M.cream, 52, 5.7, -66, 11, 0.25, 7);
  for (const z of [-69.3, -62.7]) cylinder('archive column', M.cream, 55.5, 2.7, z, 0.55, 5.4, 0.55);
  box('archive reading desk', M.wood, 53, 0.85, -67, 1.2, 1.6, 3);
  sign('MILL WARD', 'COOPERATIVE DEPOT · GATE 2', -56.5, 4.1, -68, 12, 1.6, 90, '#793e31');
  for (const z of [-72, -68, -64]) { box('supply crate', M.wood, -58.5, 0.65, z, 1.5, 1.3, 1.5); box('crate crossbar', M.cream, -57.71, 0.65, z, 0.03, 0.1, 1.4); }
  sign('OPEN FREQUENCY', 'COMMUNITY RADIO · 92.4 FM', 65, 4, -8, 14, 1.75, 0, '#305461');
  box('radio booth', M.teal, 69, 1.6, -8.2, 7, 3.2, 0.7);
  cylinder('radio mast', M.metal, 75, 10, -8, 0.2, 20, 0.2);
  for (let i = 0; i < 4; i++) line('radio aerial', M.metal, [73.2, 14 + i * 1.5, -8], [76.8, 14 + i * 1.5, -8], 0.06);
  sphere('radio beacon', M.brake, 75, 20, -8, 0.3, 0.3, 0.3);

  // The assembly terrace turns the south road into a welcoming civic pedestrian space.
  box('assembly terrace', M.stone, 0, 0.03, 78, 17, 0.22, 30);
  for (const x of [-7.3, 7.3]) { tree(x, 67, 0.95); bench(x, 73, x < 0 ? 90 : -90); }
  box('civic hall back', M.cream, 0, 7.2, 96, 29, 14.4, 5);
  box('civic portico roof', M.cream, 0, 10.4, 88, 24, 0.7, 13);
  box('civic frieze', M.teal, 0, 9.35, 81.4, 24, 1.4, 0.5);
  for (const x of [-10.5, -5.5, 5.5, 10.5]) { cylinder('civic hall column', M.cream, x, 4.7, 82, 0.8, 9.4, 0.8); cylinder('column base', M.white, x, 0.3, 82, 1.2, 0.6, 1.2); }
  sign('THE PEOPLE’S HALL', 'DEVNAGAR · PUBLIC HEARING', 0, 9.4, 81.08, 20, 1.4, 180, '#315b5c');
  sign('ASSEMBLY SQUARE', 'MANY VOICES. ONE CITY.', 7.2, 2.6, 64, 6, 0.9, 180, '#80653f');
  box('public lectern', M.wood, 0, 0.7, 88, 1.2, 1.4, 0.8);
  for (const z of [84, 86]) for (const x of [-7, -4, 4, 7]) bench(x, z, 180);

  // A strip of water and distant embankment give the city a geographic horizon.
  const water = mat('river surface', '#607f83', 0.95);
  box('Devnagar river', water, 125, -0.7, 0, 48, 0.12, 300);
  box('river embankment', M.cream, 99, -0.6, 0, 2, 2, 204);
  for (let z = -95; z <= 95; z += 7) { box('river railing post', M.dark, 98, 0.7, z, 0.12, 1.4, 0.12); }
  box('river rail', M.dark, 98, 1.1, 0, 0.1, 0.1, 198);
  box('river overlook', M.stone, 91, 0, 48, 15, 0.15, 17);
  sign('RIVER STEPS', 'THE CITY MEETS THE WATER', 88, 3, 39, 9, 1.2, 0, '#375d5b');
  bench(92, 45, 90); bench(92, 51, 90); tree(91, 57, 1.1);
  for (let i = 0; i < 35; i++) {
    const x = -165 + random() * 330; const z = -135 - random() * 65; const h = 12 + random() * 40;
    box('distant skyline', i % 2 ? M.sky : M.metal, x, h / 2 - 3, z, 6 + random() * 13, h, 8 + random() * 12);
  }
  // Original posters and crates create close-range details around the opening street.
  sign('A CITY IS ITS PEOPLE', 'DEVNAGAR NEIGHBOURHOOD ASSEMBLY', -38.49, 1.8, 25, 3.4, 2.1, -90, '#dcbe73', '#394846');
  sign('LISTEN FIRST', 'THE OBSERVER · INDEPENDENT SINCE 1986', -38.5, 1.8, 18, 2.5, 2.6, -90, '#a8533f', '#f3ddaa');
  box('fruit stall counter', M.wood, -39.5, 0.8, 36, 2, 1.4, 3);
  for (let i = 0; i < 18; i++) sphere('market produce', i % 3 ? M.yellow : M.terracotta, -39.2 + i % 3 * 0.35, 1.6, 34.9 + Math.floor(i / 3) * 0.36, 0.32, 0.32, 0.32);

  function person(color: number, x: number, z: number, batch = false): Person {
    const p = new pc.Entity('citizen'); root.addChild(p); p.setPosition(x, 0, z);
    const shirts = [M.teal, M.terracotta, M.yellow, M.blue, M.cream, M.red]; const shirt = shirts[Math.abs(color) % shirts.length];
    box('jacket body', shirt, 0, 1.19, 0, 0.54, 0.7, 0.32, p, batch);
    box('jacket centre seam', M.cream, 0, 1.23, 0.167, 0.035, 0.53, 0.02, p, batch);
    box('shirt hem', M.dark, 0, 0.84, 0, 0.5, 0.1, 0.3, p, batch);
    cylinder('neck', M.skin, 0, 1.6, 0, 0.19, 0.2, 0.19, p, batch);
    sphere('head', M.skin, 0, 1.8, 0, 0.37, 0.43, 0.35, p, batch);
    sphere('hair', M.hair, 0, 1.96, -0.035, 0.39, 0.22, 0.35, p, batch);
    box('nose', M.skin, 0, 1.79, 0.18, 0.08, 0.10, 0.07, p, batch);
    const limb = (name: string, x: number, y: number, material: pc.Material, width: number, length: number) => {
      const pivot = new pc.Entity(name); pivot.setLocalPosition(x, y, 0); p.addChild(pivot);
      box(name, material, 0, -length / 2, 0, width, length, width * 1.15, pivot, batch); return pivot;
    };
    const leftArm = limb('left arm', -0.36, 1.49, shirt, 0.19, 0.62); const rightArm = limb('right arm', 0.36, 1.49, shirt, 0.19, 0.62);
    sphere('left hand', M.skin, 0, -0.64, 0, 0.18, 0.21, 0.18, leftArm, batch); sphere('right hand', M.skin, 0, -0.64, 0, 0.18, 0.21, 0.18, rightArm, batch);
    const leftLeg = limb('left leg', -0.145, 0.83, M.dark, 0.22, 0.71); const rightLeg = limb('right leg', 0.145, 0.83, M.dark, 0.22, 0.71);
    box('left shoe', M.rubber, 0, -0.71, 0.06, 0.24, 0.14, 0.36, leftLeg, batch); box('right shoe', M.rubber, 0, -0.71, 0.06, 0.24, 0.14, 0.36, rightLeg, batch);
    if (!batch) batchMovingParts(p);
    return { root: p, leftArm, rightArm, leftLeg, rightLeg, phase: random() * 6, lastX: x, lastZ: z };
  }
  function animatePerson(p: Person, speed: number, dt: number) {
    p.phase += dt * Math.min(speed * 2.2, 14); const stride = Math.sin(p.phase) * Math.min(speed * 9, 34);
    p.leftArm.setLocalEulerAngles(stride, 0, -5); p.rightArm.setLocalEulerAngles(-stride, 0, 5);
    p.leftLeg.setLocalEulerAngles(-stride, 0, 0); p.rightLeg.setLocalEulerAngles(stride, 0, 0);
  }
  // Short loops stay on pavements and never participate in collision or mission state.
  const pedRoutes: [number, number, boolean, number][] = [[-39.1, 15, false, 18], [-8.6, -34, false, 18], [8.7, 13, false, 18], [38.7, -33, false, 16], [-33, 39, true, 19], [13, -39, true, 18], [-88, -30, false, 15], [58.8, 16, false, 16], [18, 58.8, true, 14], [-32, -58.8, true, 15], [86.8, -28, false, 16], [-9, 67, false, 10]];
  pedRoutes.forEach(([x, z, alongX, length], i) => pedestrians.push({ person: person(i + 1, x, z), startX: x, startZ: z, alongX, length, speed: 0.65 + random() * 0.3, offset: random() * length, }));
  function contact(name: string, role: string, x: number, z: number, color: number, heading: number, accessory: 'apron' | 'record' | 'scarf' | 'camera' = 'record') {
    const citizen = person(color, x, z, true); citizen.root.name = `${name} / ${role}`; citizen.root.setEulerAngles(0, heading, 0);
    if (accessory === 'apron') {
      box('mechanic’s canvas apron', M.wood, 0, 1.06, 0.18, 0.39, 0.58, 0.035, citizen.root);
      box('apron pocket', M.cream, 0, 1.02, 0.21, 0.26, 0.18, 0.025, citizen.root);
      box('workshop wrench', M.metal, 0.29, 0.84, 0.18, 0.06, 0.29, 0.06, citizen.root);
    } else if (accessory === 'record') {
      box('held public record', M.paper, 0.38, 1.02, 0.15, 0.29, 0.37, 0.035, citizen.root);
    } else if (accessory === 'camera') {
      box('journalist camera strap', M.dark, -0.1, 1.25, 0.19, 0.05, 0.5, 0.04, citizen.root);
      box('journalist camera', M.dark, -0.1, 1.02, 0.24, 0.29, 0.18, 0.14, citizen.root);
      sphere('camera lens', M.glass, -0.1, 1.02, 0.33, 0.12, 0.12, 0.1, citizen.root);
    } else box('woven scarf', M.yellow, 0.13, 1.3, 0.2, 0.14, 0.62, 0.06, citizen.root);
    sign(name.toUpperCase(), role, x + Math.sin(heading / RAD) * 0.05, 2.5, z + Math.cos(heading / RAD) * 0.05, 2.5, 0.52, heading, '#304c4a', '#eadbb4');
    return citizen;
  }
  contact('Yusuf', 'THE WORKSHOP', -61.5, 48, 0, 90, 'apron');
  contact('Kavya', 'THE NIGHT DESK', 61.5, -48, 4, -90, 'record');
  contact('Noor', 'THE NEWSROOM', -67, 41.5, 1, 0, 'camera');
  contact('Records clerk', 'PUBLIC ARCHIVE', 51, -66, 3, -90, 'record');
  contact('Shipping clerk', 'MILL WARD DEPOT', -53, -68, 4, 90, 'apron');
  contact('Print editor', 'OPEN FREQUENCY', 65, -5, 2, 0, 'record');
  contact('Tara', 'ASSEMBLY SQUARE', 2, 67, 1, 180, 'scarf');
  contact('Hearing clerk', 'PUBLIC HEARING', 2, 87, 3, 180, 'record');
  contact('Leela', 'RIVER ENGINEER', 88, 48, 4, -90, 'record');
  const assemblyCitizens = [[-4, 69], [-1, 70], [4, 70], [-3, 74], [3, 74], [6, 69]].map(([x, z], i) => {
    const citizen = person(i + 1, x, z); citizen.root.name = 'resident attending the public assembly'; citizen.root.setEulerAngles(0, 180, 0); citizen.root.enabled = false; return citizen;
  });

  function car(v: VehicleSnapshot): Car {
    const carRoot = new pc.Entity(v.kind === 'van' ? 'community service van' : 'Aadi’s compact'); root.addChild(carRoot);
    const paint = v.kind === 'van' ? M.cream : M.teal; const isVan = v.kind === 'van'; const length = isVan ? 4.6 : 3.9;
    box('chassis', M.dark, 0, 0.48, 0, 1.8, 0.2, length, carRoot, false);
    box('painted body', paint, 0, 0.78, 0, 1.86, 0.57, length, carRoot, false);
    box('hood', paint, 0, 1.02, 1.2, 1.79, 0.19, 1.16, carRoot, false);
    box('cabin glass', M.glass, 0, 1.42, isVan ? -0.38 : -0.15, 1.63, isVan ? 1.05 : 0.74, isVan ? 3.1 : 2.02, carRoot, false);
    if (isVan) box('van cargo body', paint, 0, 1.45, -0.72, 1.79, 1.1, 2.9, carRoot, false);
    box('roof', paint, 0, isVan ? 2.02 : 1.83, isVan ? -0.4 : -0.25, 1.7, 0.13, isVan ? 3.2 : 1.75, carRoot, false);
    for (const x of [-0.84, 0.84]) {
      const windshield = box('windscreen pillar', paint, x, 1.46, 0.75, 0.1, 0.85, 0.12, carRoot, false); windshield.setLocalEulerAngles(-14, 0, 0);
      box('window pillar', paint, x, 1.4, -0.35, 0.1, 0.76, 0.12, carRoot, false);
      box('rear pillar', paint, x, 1.4, -1.06, 0.1, 0.73, 0.15, carRoot, false);
      box('door handle', M.metal, x * 1.13, 1.03, -0.1, 0.05, 0.07, 0.23, carRoot, false);
      box('wing mirror', M.dark, x * 1.17, 1.18, 0.57, 0.26, 0.18, 0.23, carRoot, false);
      box('door seam', M.dark, x * 1.12, 0.79, -0.39, 0.018, 0.39, 0.018, carRoot, false);
    }
    box('front bumper', M.dark, 0, 0.54, length / 2 + 0.04, 1.88, 0.19, 0.17, carRoot, false);
    box('rear bumper', M.dark, 0, 0.54, -length / 2 - 0.03, 1.88, 0.19, 0.17, carRoot, false);
    box('grille', M.dark, 0, 0.83, length / 2 + 0.015, 0.75, 0.22, 0.035, carRoot, false);
    box('registration plate', M.paper, 0, 0.59, length / 2 + 0.14, 0.53, 0.16, 0.025, carRoot, false);
    for (const x of [-0.64, 0.64]) {
      box('headlamp', M.headlamp, x, 0.84, length / 2 + 0.05, 0.43, 0.25, 0.055, carRoot, false);
      box('rear lamp', M.brake, x, 0.87, -length / 2 - 0.05, 0.35, 0.25, 0.055, carRoot, false);
    }
    const wheels: pc.Entity[] = [];
    for (const x of [-0.94, 0.94]) for (const z of [-1.22, 1.25]) {
      const pivot = new pc.Entity('wheel axle'); pivot.setLocalPosition(x, 0.45, z); carRoot.addChild(pivot);
      const tyre = cylinder('tyre', M.rubber, 0, 0, 0, 0.79, 0.25, 0.79, pivot, false); tyre.setLocalEulerAngles(0, 0, 90);
      const hub = cylinder('wheel hub', M.metal, x > 0 ? 0.14 : -0.14, 0, 0, 0.45, 0.025, 0.45, pivot, false); hub.setLocalEulerAngles(0, 0, 90);
      const hubcap = cylinder('wheel centre', M.dark, x > 0 ? 0.16 : -0.16, 0, 0, 0.18, 0.025, 0.18, pivot, false); hubcap.setLocalEulerAngles(0, 0, 90); wheels.push(pivot);
    }
    batchMovingParts(carRoot);
    return { root: carRoot, wheels, phase: 0 };
  }
  const markerRoot = new pc.Entity('current objective'); root.addChild(markerRoot);
  const markerRing = primitive('objective ground ring', 'plane', destinationRing, 0, 0.08, 0, 3, 1, 3, markerRoot, false); markerRing.render!.castShadows = false;
  cylinder('destination lantern post', M.dark, 0.7, 1.45, 0, 0.075, 2.9, 0.075, markerRoot, false);
  box('destination lantern bracket', M.dark, 0.43, 2.92, 0, 0.62, 0.065, 0.065, markerRoot, false);
  const markerLantern = new pc.Entity('amber destination lantern'); markerRoot.addChild(markerLantern);
  cylinder('lantern amber glass', M.marker, 0, 2.47, 0, 0.38, 0.62, 0.38, markerLantern, false);
  cylinder('lantern base', M.dark, 0, 2.12, 0, 0.49, 0.09, 0.49, markerLantern, false);
  cylinder('lantern cap', M.dark, 0, 2.83, 0, 0.51, 0.09, 0.51, markerLantern, false);
  primitive('lantern pitched lid', 'cone', M.dark, 0, 2.94, 0, 0.48, 0.2, 0.48, markerLantern, false);
  for (const x of [-0.15, 0.15]) for (const z of [-0.15, 0.15]) box('lantern frame', M.dark, x, 2.48, z, 0.035, 0.65, 0.035, markerLantern, false);
  const rainMaterial = mat('rain', '#b3c6c5'); rainMaterial.opacity = 0.18; rainMaterial.blendType = pc.BLEND_NORMAL; rainMaterial.depthWrite = false; rainMaterial.update();
  const rain = new pc.Entity('near-camera monsoon rain'); root.addChild(rain);
  const rainDrops: { entity: pc.Entity; x: number; y: number; z: number; speed: number }[] = [];
  for (let i = 0; i < 55; i++) {
    const x = random() * 28 - 14; const y = random() * 15; const z = random() * 28 - 14;
    const e = box('rain streak', rainMaterial, x, y, z, 0.012, 0.25 + random() * 0.25, 0.012, rain, false); e.render!.castShadows = false; e.setEulerAngles(0, 0, -12);
    rainDrops.push({ entity: e, x, y, z, speed: 10 + random() * 5 });
  }

  app.batcher.generate();
  function resize() { const rect = canvas.getBoundingClientRect(); if (rect.width && rect.height) app.resizeCanvas(rect.width, rect.height); }
  const resizeObserver = new ResizeObserver(resize); resizeObserver.observe(canvas); resize();
  app.start();
  const target = new pc.Vec3(WORLD.spawn.x, 1.45, WORLD.spawn.z);
  const cameraPosition = new pc.Vec3(-60, 5, 55);

  function updatePerson(p: PlayerSnapshot, dt: number) {
    let visual = people.get(p.id);
    if (!visual) { visual = person(p.color, p.x, p.z); visual.root.setEulerAngles(0, p.heading * RAD, 0); people.set(p.id, visual); }
    visual.root.enabled = !p.vehicleId;
    const position = visual.root.getPosition(); const factor = 1 - Math.exp(-dt * 18);
    const nx = mix(position.x, p.x, factor); const nz = mix(position.z, p.z, factor);
    const speed = Math.hypot(nx - visual.lastX, nz - visual.lastZ) / Math.max(dt, 0.001);
    visual.root.setPosition(nx, Math.min(speed, 5) * 0.006 * Math.abs(Math.sin(visual.phase)), nz);
    const oldHeading = visual.root.getEulerAngles().y / RAD;
    visual.root.setEulerAngles(0, angleMix(oldHeading, p.heading, factor) * RAD, 0);
    animatePerson(visual, speed, dt); visual.lastX = nx; visual.lastZ = nz;
  }
  function updateVehicle(v: VehicleSnapshot, dt: number) {
    let visual = vehicles.get(v.id);
    if (!visual) { visual = car(v); visual.root.setPosition(v.x, 0, v.z); visual.root.setEulerAngles(0, v.heading * RAD, 0); vehicles.set(v.id, visual); }
    const pos = visual.root.getPosition(); const factor = 1 - Math.exp(-dt * 16);
    visual.root.setPosition(mix(pos.x, v.x, factor), 0, mix(pos.z, v.z, factor));
    const heading = visual.root.getEulerAngles().y / RAD;
    visual.root.setEulerAngles(0, angleMix(heading, v.heading, factor) * RAD, 0);
    visual.phase += v.speed * dt * 140;
    for (const wheel of visual.wheels) wheel.setLocalEulerAngles(visual.phase, 0, 0);
  }
  function obstructionDistance(from: pc.Vec3, to: pc.Vec3): number {
    let closest = 1;
    for (const b of [...WORLD.buildings, ...WORLD.obstacles]) {
      const min = [b.x - b.width / 2 - 0.4, -0.5, b.z - b.depth / 2 - 0.4];
      const max = [b.x + b.width / 2 + 0.4, b.height + 0.7, b.z + b.depth / 2 + 0.4];
      const origin = [from.x, from.y, from.z]; const end = [to.x, to.y, to.z];
      let near = 0; let far = 1; let hit = true;
      for (let axis = 0; axis < 3; axis++) {
        const delta = end[axis] - origin[axis];
        if (Math.abs(delta) < 0.0001) { if (origin[axis] < min[axis] || origin[axis] > max[axis]) { hit = false; break; } }
        else { let a = (min[axis] - origin[axis]) / delta; let c = (max[axis] - origin[axis]) / delta; if (a > c) [a, c] = [c, a]; near = Math.max(near, a); far = Math.min(far, c); if (near > far) { hit = false; break; } }
      }
      if (hit && near >= 0 && near < closest) closest = Math.max(0.01, near - 0.05);
    }
    return closest;
  }

  return {
    update(snapshot, localPlayerId, rawDt) {
      const dt = Math.min(rawDt, 0.1); elapsed += dt;
      for (const pedestrian of pedestrians) {
        if (!pedestrian.person.root.enabled || comfort || quality === 'low') continue;
        const raw = (elapsed * pedestrian.speed + pedestrian.offset) % (pedestrian.length * 2);
        const reverse = raw > pedestrian.length; const progress = reverse ? pedestrian.length * 2 - raw : raw;
        pedestrian.person.root.setPosition(pedestrian.startX + (pedestrian.alongX ? progress : 0), 0, pedestrian.startZ + (pedestrian.alongX ? 0 : progress));
        pedestrian.person.root.setEulerAngles(0, (pedestrian.alongX ? 90 : 0) + (reverse ? 180 : 0), 0);
        animatePerson(pedestrian.person, pedestrian.speed, dt);
      }
      let tx = WORLD.spawn.x; let tz = WORLD.spawn.z; let driving = false; let heading = cameraYaw;
      if (snapshot) {
        for (const p of snapshot.players) updatePerson(p, dt);
        for (const v of snapshot.vehicles) updateVehicle(v, dt);
        for (const [id, visual] of people) if (!snapshot.players.some(p => p.id === id)) { visual.root.destroy(); people.delete(id); }
        for (const [id, visual] of vehicles) if (!snapshot.vehicles.some(v => v.id === id)) { visual.root.destroy(); vehicles.delete(id); }
        const p = snapshot.players.find(player => player.id === localPlayerId) || snapshot.players[0];
        if (p) { const v = snapshot.vehicles.find(vehicle => vehicle.id === p.vehicleId); const tracked = v ? vehicles.get(v.id)?.root : people.get(p.id)?.root; const pos = tracked?.getPosition(); tx = pos?.x ?? p.x; tz = pos?.z ?? p.z; driving = !!v; heading = v?.heading ?? p.heading;
          if (v && Math.abs(v.speed) > 2 && elapsed - lastOrbit > (comfort ? 4 : 2)) {
            // Reversing keeps the vehicle's heading: parking must not trigger a 180° camera swing.
            const delta = Math.atan2(Math.sin(heading - cameraYaw), Math.cos(heading - cameraYaw));
            const turn = delta * (1 - Math.exp(-dt * (comfort ? 0.8 : 1.5)));
            const maxTurn = (comfort ? 45 : 120) / RAD * dt;
            cameraYaw += clamp(turn, -maxTurn, maxTurn);
          }
        }
        const destination = WORLD.landmarks.find(l => l.id === snapshot.mission.targetId);
        markerRoot.enabled = !!destination && !snapshot.mission.complete;
        if (destination) markerRoot.setPosition(destination.x, 0, destination.z);
        evidencePapers.forEach((paper, i) => paper.enabled = snapshot.mission.evidence.length > i);
        evidenceThreads.forEach((thread, i) => thread.enabled = snapshot.mission.evidence.length > i + 1);
        restoredSupplies.enabled = snapshot.mission.evidence.includes('clinicRestored');
        assemblyCitizens.forEach(citizen => citizen.root.enabled = snapshot.mission.chapterIndex >= 4 || snapshot.mission.complete);
      } else markerRoot.enabled = false;
      markerLantern.setLocalEulerAngles(0, 0, comfort ? 0 : Math.sin(elapsed * 1.4) * 1.2);
      if (overview) { camera.setPosition(-66 + (comfort ? 0 : Math.sin(elapsed * 0.024) * 5), 19, 67); camera.lookAt(-16, 5, 11); skyDome.setPosition(camera.getPosition()); return; }
      const follow = 1 - Math.exp(-dt * (comfort ? 18 : 10));
      if (!cameraInitialized) target.set(tx, driving ? 1.65 : 1.4, tz);
      else { target.x = mix(target.x, tx, follow); target.y = mix(target.y, driving ? 1.65 : 1.4, follow); target.z = mix(target.z, tz, follow); }
      const distance = driving ? 11.2 : 7.5; const desired = new pc.Vec3(target.x - Math.sin(cameraYaw) * distance, target.y + distance * Math.tan(cameraPitch), target.z - Math.cos(cameraYaw) * distance);
      const fraction = obstructionDistance(target, desired); desired.lerp(target, desired, fraction);
      if (!cameraInitialized) { cameraPosition.copy(desired); cameraInitialized = true; } else cameraPosition.lerp(cameraPosition, desired, 1 - Math.exp(-dt * 12));
      // The eased position can still be beyond a newly crossed wall. Pull in immediately;
      // the regular easing above lets the camera return outward without a pop.
      const finalFraction = obstructionDistance(target, cameraPosition);
      if (finalFraction < 1) cameraPosition.lerp(target, cameraPosition, finalFraction);
      camera.setPosition(cameraPosition); camera.lookAt(target); skyDome.setPosition(cameraPosition);
      rain.setPosition(tx, 0, tz);
      if (quality === 'high') for (const d of rainDrops) { d.y -= dt * d.speed; if (d.y < 0) d.y += 15; d.entity.setLocalPosition(d.x, d.y, d.z); }
    },
    setQuality(next) { quality = next; app.graphicsDevice.maxPixelRatio = next === 'high' ? Math.min(window.devicePixelRatio || 1, 1.5) : 0.6; sun.light!.castShadows = next === 'high'; rain.enabled = next === 'high' && !comfort; pedestrians.forEach((p, i) => p.person.root.enabled = next === 'high' || i % 3 === 0); resize(); },
    setCamera(yawDelta, pitchDelta) { cameraYaw += yawDelta; cameraPitch = clamp(cameraPitch + pitchDelta, 0.08, 0.9); lastOrbit = elapsed; },
    setComfort(enabled) { comfort = enabled; rain.enabled = !enabled && quality === 'high'; },
    setOverview(enabled) { overview = enabled; cameraInitialized = false; },
    getCameraYaw() { return cameraYaw; },
    project(x, z, y = 2.4) { const screen = camera.camera!.worldToScreen(new pc.Vec3(x, y, z)); const rect = canvas.getBoundingClientRect(); const ahead = new pc.Vec3(x, y, z).sub(camera.getPosition()).dot(camera.forward) > 0; return { x: screen.x, y: screen.y, visible: ahead && screen.x >= 0 && screen.y >= 0 && screen.x <= rect.width && screen.y <= rect.height }; },
    destroy() { resizeObserver.disconnect(); app.destroy(); for (const texture of textures) texture.destroy(); for (const material of materials) material.destroy(); },
  };
}
