import * as pc from 'playcanvas';
import { LANES, SOLIDS } from '../shared/map';
import { RenderKit } from './render-kit';

/** Every opaque prop sits within a shared solid or outside the playable boundary. */
export function buildSangamCity(kit: RenderKit, root: pc.Entity) {
  const M = {
    paving: kit.material('blue-grey civic paving', '#75918f'), ivory: kit.material('chalk limestone', '#e8d9b4'),
    stone: kit.material('honey sandstone', '#c58c60'), clay: kit.material('sandstone shadow', '#94634d'),
    trim: kit.material('carved warm cornices', '#f2c690'), dark: kit.material('obsidian teal', '#193c4a'),
    glass: kit.material('metro blue-green glass', '#376e7e', .05, .8), metal: kit.material('brushed copper', '#aa7754', 0, .7),
    gold: kit.material('avenue brass inlay', '#ead3a0', .12), jade: kit.material('metro lane inlay', '#8bddd3', .2),
    warm: kit.material('ghat lane inlay', '#e7b982', .12), leaf: kit.material('garden leaf', '#486d59'),
    leafLight: kit.material('sunlit leaves', '#779a68'), trunk: kit.material('tree bark', '#755a45'),
    water: kit.material('confluence water', '#467c87', .07, .8), lamp: kit.material('civic warm light', '#ffe1a1', 1.2),
    roof: kit.material('patinated teal roof', '#477e7d'), lane: kit.material('polished lane slab', '#a7b5aa', 0, .45),
    sun: kit.material('sun base', '#efb95b', .5), moon: kit.material('moon base', '#78d9ec', .5),
  };
  const b = (type: Parameters<RenderKit['shape']>[1], m: pc.Material, x: number, y: number, z: number, sx: number, sy: number, sz: number) => kit.shape(root, type, m, x, y, z, sx, sy, sz, true);
  b('box', M.paving, 0, -.21, 0, 140, .4, 170);
  const paving = kit.texture('original civic stone joints', 512, 512, ctx => {
    ctx.fillStyle = '#9aaca4'; ctx.fillRect(0, 0, 512, 512);
    for (let row = 0; row < 8; row++) for (let col = -1; col < 9; col++) {
      const x = col * 64 + (row % 2) * 32;
      ctx.fillStyle = (row + col) % 3 === 0 ? '#aab8ac' : '#a3b3aa'; ctx.fillRect(x + 1, row * 64 + 1, 62, 62);
      ctx.fillStyle = '#b7c2b4'; ctx.fillRect(x + 4, row * 64 + 3, 58, 1);
    }
  });
  M.paving.diffuseMap = paving; M.paving.diffuseMapTiling.set(14, 17); M.paving.update();
  // Broad inlaid paths: visual navigation only, same level as the flat authority plane.
  for (const lane of [0, 1, 2] as const) {
    const pts = LANES[lane], accent = [M.warm, M.gold, M.jade][lane]!;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1]!, c = pts[i]!, dx = c.x - a.x, dz = c.z - a.z, length = Math.hypot(dx, dz), yaw = Math.atan2(dx, dz) * 180 / Math.PI;
      const path = b('box', M.lane, (a.x + c.x) / 2, .004, (a.z + c.z) / 2, lane === 1 ? 13 : 11, .016, length + .3); path.setLocalEulerAngles(0, yaw, 0);
      for (const side of [-1, 1]) {
        const line = b('box', accent, (a.x + c.x) / 2 + side * Math.cos(yaw * Math.PI / 180) * 4.5, .025, (a.z + c.z) / 2 - side * Math.sin(yaw * Math.PI / 180) * 4.5, .13, .02, length);
        line.setLocalEulerAngles(0, yaw, 0);
      }
    }
  }
  for (const z of [-56, 0, 56]) for (const x of [-40, 0, 40]) {
    const node = new pc.Entity('lane compass'); root.addChild(node); node.setPosition(x, .03, z);
    kit.ring(node, M.gold, 3, .08, 0, 32, true);
    for (let a = 0; a < 8; a++) { const rad = a / 8 * Math.PI * 2; const tile = kit.shape(node, 'box', M.ivory, Math.sin(rad) * 2.4, 0, Math.cos(rad) * 2.4, .18, .02, .65, true); tile.setLocalEulerAngles(0, rad * 180 / Math.PI, 0); }
  }
  // River and stepped embankment lie beyond the impassable west edge.
  b('box', M.water, -105, -.65, 0, 70, .12, 250);
  for (let i = 0; i < 5; i++) b('box', i % 2 ? M.clay : M.stone, -70.7 - i * 1.5, -.12 - i * .15, 0, 1.5, .3, 170);
  for (let i = 0; i < 16; i++) b('box', M.jade, -88 - (i % 4) * 7, -.56, -105 + i * 14, 3 + (i % 3) * 2, .012, .13);
  for (const side of [-1, 1]) {
    for (const z of [-78, -50, -6, 48, 78]) {
      b('cylinder', M.dark, side * 69.6, 2.6, z, .22, 5.2, .22);
      b('sphere', M.lamp, side * 69.6, 5.3, z, .48, .7, .48);
      b('cone', M.roof, side * 69.6, 5.8, z, .95, .35, .95);
    }
    b('box', M.trim, side * 69.9, .08, 0, .3, .18, 166);
  }
  for (const s of SOLIDS) {
    const west = s.style === 'sandstone', wall = west ? M.stone : M.glass;
    // Recess the wall behind its authored facade; all trims still fit the shared solid.
    b('box', wall, s.x, s.height / 2, s.z, s.w - .4, s.height, s.d - .4);
    b('box', west ? M.clay : M.dark, s.x, .45, s.z, s.w, .9, s.d);
    if (west) {
      b('box', M.trim, s.x, s.height - .25, s.z, s.w, .5, s.d);
      b('box', M.clay, s.x, s.height - .7, s.z, s.w - .3, .25, s.d - .3);
      // Recessed front and side colonnades are surface decoration, entirely in footprint.
      for (const face of [-1, 1]) {
        for (let i = -2; i <= 2; i++) {
          const x = s.x + i * (s.w / 6), z = s.z + face * (s.d / 2 - .07);
          b('box', M.clay, x, 3.5, z, s.w / 7, 5.2, .14);
          b('cylinder', M.trim, x - s.w / 14 + .1, 2.8, z - face * .16, .3, 4.7, .3);
          b('box', M.trim, x, 6.1, z - face * .05, s.w / 6 - .2, .3, .2);
          const arch = b('sphere', M.trim, x, 5.4, z - face * .03, s.w / 7, 1.4, .12);
          arch.setLocalScale(s.w / 7, 1.4, .12);
          b('sphere', M.clay, x, 5.25, z - face * .11, s.w / 8, 1.2, .13);
        }
        for (const dz of [-5, 0, 5]) {
          b('box', M.clay, s.x + face * (s.w / 2 - .06), 4.1, s.z + dz, .14, 3.5, 2.1);
          b('box', M.trim, s.x + face * (s.w / 2 - .16), 6, s.z + dz, .22, .25, 2.4);
        }
      }
      // Roof chhatri, kept below the shared solid's top so camera rays remain honest.
      b('box', M.trim, s.x, s.height - 1.1, s.z, 5.4, .3, 5.4);
      b('sphere', M.roof, s.x, s.height - .7, s.z, 4.5, 1.1, 4.5);
      for (let i = -3; i <= 3; i++) b('box', M.trim, s.x + i * 2.2, s.height - .1, s.z - s.d / 2 + .45, .8, .2, .7);
      kit.sign(root, s.x < -50 ? 'GHAT ARCHIVE' : 'SANGAM HOUSE', 'GHAT PROMENADE  /  01', '#f2c690', Math.min(7, s.w - 2), 1.65, s.x, 7, s.z - s.d / 2 - .012, 0);
    } else {
      for (let y = 2.6; y < s.height; y += 2.8) b('box', M.ivory, s.x, y, s.z, s.w, .17, s.d);
      for (const side of [-1, 1]) {
        for (let i = -3; i <= 3; i++) {
          const x = s.x + i * 2.3;
          b('box', M.dark, x, s.height / 2, s.z + side * (s.d / 2 - .06), .17, s.height, .14);
          if (i % 2 === 0) for (let y = 4; y < s.height; y += 5.6) b('box', M.jade, x + .6, y, s.z + side * (s.d / 2 - .025), .9, 1.1, .06);
        }
        for (const dz of [-6, 0, 6]) b('box', M.ivory, s.x + side * (s.w / 2 - .08), s.height / 2, s.z + dz, .16, s.height, .23);
      }
      b('box', M.dark, s.x, s.height - .3, s.z, s.w, .6, s.d);
      b('box', M.jade, s.x, s.height - .15, s.z - s.d / 2 + .14, s.w - 1, .15, .3);
      b('box', M.leaf, s.x, s.height - .05, s.z, s.w - 2, .1, s.d - 2);
      kit.sign(root, s.x > 50 ? 'EAST METRO' : 'CONFLUENCE LAB', 'METRO GARDENS  /  03', '#9de6dd', 7.6, 1.65, s.x, 3.5, s.z - s.d / 2 - .012, 0);
    }
    // Garden crowns emerge from recessed rooftop terraces, no ground-level phantom props.
    if (!west) for (const dx of [-5.7, 5.7]) {
      b('cylinder', M.trunk, s.x + dx, s.height - 1.7, s.z + 4, .35, 2.2, .35);
      b('sphere', M.leaf, s.x + dx, s.height - 1.2, s.z + 4, 3, 2.2, 3);
      b('sphere', M.leafLight, s.x + dx - .4, s.height - .65, s.z + 3.7, 2.1, 1.2, 2.2);
    }
  }
  // Far-city silhouettes and boundary monumental gates do not occupy walkable lanes.
  for (let i = 0; i < 14; i++) {
    const x = 82 + (i % 3) * 11, z = -102 + i * 17, h = 15 + (i * 7 % 24);
    b('box', i % 2 ? M.glass : M.dark, x, h / 2, z, 8 + i % 4, h, 10);
    b('box', M.jade, x, h - 1, z - 5.1, 5, .15, .05);
  }
  for (const sign of [-1, 1]) {
    const z = sign * 86;
    for (const x of [-13, 13]) {
      b('box', M.stone, x, 7.5, z, 4, 15, 4);
      b('box', M.trim, x, 13.6, z, 4.3, .6, 4.3);
      b('cone', M.roof, x, 16, z, 5, 2, 5);
    }
    b('box', M.clay, 0, 12.5, z, 30, 1.6, 4);
    b('box', M.trim, 0, 13.4, z, 31, .4, 4.4);
    const base = new pc.Entity('team spawn mandala'); root.addChild(base); base.setPosition(0, .04, sign * 69);
    kit.ring(base, sign < 0 ? M.sun : M.moon, 7.5, .25, 0, 64, true);
    kit.ring(base, M.gold, 8, .07, .002, 64, true);
    for (let a = 0; a < 12; a++) { const r = a / 12 * Math.PI * 2; const tile = kit.shape(base, 'box', M.ivory, Math.sin(r) * 6.3, 0, Math.cos(r) * 6.3, .5, .02, 1.5, true); tile.setLocalEulerAngles(0, r * 180 / Math.PI, 0); }
  }
  // Horizon dome uses a painted original gradient, zero diffuse to retain the sky colors.
  const skyTexture = kit.texture('Sangam late-afternoon sky', 32, 256, ctx => {
    const gradient = ctx.createLinearGradient(0, 0, 0, 256);
    gradient.addColorStop(0, '#416a82'); gradient.addColorStop(.35, '#77a3b1'); gradient.addColorStop(.56, '#d6cdb7'); gradient.addColorStop(.72, '#edc9a2'); gradient.addColorStop(1, '#a9b5ae');
    ctx.fillStyle = gradient; ctx.fillRect(0, 0, 32, 256);
  });
  const skyMaterial = kit.material('painted sky dome', '#000000'); skyMaterial.useLighting = false; skyMaterial.useFog = false;
  skyMaterial.emissive.set(1, 1, 1); skyMaterial.emissiveMap = skyTexture; skyMaterial.cull = pc.CULLFACE_FRONT; skyMaterial.depthWrite = false; skyMaterial.update();
  const sky = kit.shape(root, 'sphere', skyMaterial, 0, 0, 0, 780, 780, 780); sky.render!.castShadows = false;
  return { sky };
}
