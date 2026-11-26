#!/usr/bin/env node
/** Read-only checks for this original, flat-scene GLB package; no engine launch. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const directory = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(directory, '../..');
const packageRoot = path.join(repoRoot, 'games/yuga-native/art/daftar-route-lab');
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const require = (condition, message) => { if (!condition) throw new Error(message); };
const near = (a, b, tolerance = 0.02) => Number.isFinite(a) && Math.abs(a - b) <= tolerance;
function read(root, name, limit = 32 * 1024 * 1024) {
  require(typeof name === 'string' && /^[A-Za-z0-9_.-]+$/.test(name) && !['.', '..'].includes(name), 'Package filenames must be direct children.');
  const file = path.join(root, name), stat = fs.lstatSync(file);
  require(stat.isFile() && !stat.isSymbolicLink() && stat.size <= limit, `Invalid or oversized package file: ${name}`);
  return fs.readFileSync(file);
}

function transform(point, node) {
  if (node.matrix) {
    const m = node.matrix;
    require(m.length === 16 && m.every(Number.isFinite), 'Invalid GLB matrix.');
    return [0, 1, 2].map(i => m[i] * point[0] + m[i + 4] * point[1] + m[i + 8] * point[2] + m[i + 12]);
  }
  const scale = node.scale ?? [1, 1, 1], t = node.translation ?? [0, 0, 0], q = node.rotation ?? [0, 0, 0, 1];
  require(scale.length === 3 && t.length === 3 && q.length === 4 && [...scale, ...t, ...q].every(Number.isFinite), 'Invalid GLB transform.');
  require(near(q.reduce((sum, x) => sum + x * x, 0), 1, 0.001), 'Non-unit GLB rotation.');
  const [x, y, z] = point.map((value, index) => value * scale[index]);
  const [qx, qy, qz, qw] = q;
  const uv = [qy * z - qz * y, qz * x - qx * z, qx * y - qy * x];
  const uuv = [qy * uv[2] - qz * uv[1], qz * uv[0] - qx * uv[2], qx * uv[1] - qy * uv[0]];
  return [x, y, z].map((value, index) => value + 2 * (qw * uv[index] + uuv[index]) + t[index]);
}

export function checkGlb(bytes, manifest) {
  require(bytes.length >= 28 && bytes.readUInt32LE(0) === 0x46546c67 && bytes.readUInt32LE(4) === 2, 'Expected a binary glTF 2.0 file.');
  require(bytes.readUInt32LE(8) === bytes.length, 'GLB declared length differs from its bytes.');
  const chunks = [];
  for (let offset = 12; offset < bytes.length;) {
    require(offset + 8 <= bytes.length, 'Truncated GLB chunk.');
    const length = bytes.readUInt32LE(offset), type = bytes.readUInt32LE(offset + 4);
    require(length % 4 === 0 && offset + 8 + length <= bytes.length, 'Invalid GLB chunk range.');
    chunks.push({ type, bytes: bytes.subarray(offset + 8, offset + 8 + length) });
    offset += 8 + length;
  }
  require(chunks.length === 2 && chunks[0].type === 0x4e4f534a && chunks[1].type === 0x004e4942, 'Expected one JSON and one embedded binary chunk.');
  const gltf = JSON.parse(chunks[0].bytes.toString('utf8')), binary = chunks[1].bytes;
  require(gltf.asset?.version === '2.0' && gltf.buffers?.length === 1 && !gltf.buffers[0].uri, 'External GLB buffers are not permitted.');
  require(Number.isInteger(gltf.buffers[0].byteLength) && gltf.buffers[0].byteLength > 0 && binary.length >= gltf.buffers[0].byteLength && binary.length - gltf.buffers[0].byteLength < 4, 'Invalid embedded buffer size.');
  require(!(gltf.images?.length) && !(gltf.cameras?.length) && !gltf.extensions?.KHR_lights_punctual, 'This package must contain geometry/materials without external images or scene cameras/lights.');
  require(gltf.nodes?.length === manifest.geometry.gltf_nodes && gltf.meshes?.length === manifest.geometry.gltf_meshes, 'GLB object counts differ from the manifest.');
  const roots = gltf.scenes?.[gltf.scene ?? 0]?.nodes;
  require(Array.isArray(roots) && roots.length === gltf.nodes.length && new Set(roots).size === roots.length
    && roots.every(index => Number.isInteger(index) && index >= 0 && index < gltf.nodes.length), 'The Route Lab expects one flat exported scene.');
  const minimum = [Infinity, Infinity, Infinity], maximum = [-Infinity, -Infinity, -Infinity];
  let positionSamples = 0;
  for (const index of roots) {
    const node = gltf.nodes[index];
    require(!node.children?.length && Number.isInteger(node.mesh) && gltf.meshes[node.mesh], 'The Route Lab expects direct mesh roots.');
    const primitives = gltf.meshes[node.mesh].primitives;
    require(Array.isArray(primitives) && primitives.length > 0, 'A Route Lab mesh has no primitives.');
    for (const primitive of primitives) {
      const accessor = gltf.accessors?.[primitive.attributes?.POSITION];
      require(accessor?.type === 'VEC3' && accessor.componentType === 5126 && !accessor.sparse && !accessor.normalized
        && Number.isInteger(accessor.count) && accessor.count > 0 && accessor.count <= 100000, 'Unsupported or invalid position accessor.');
      const view = gltf.bufferViews?.[accessor.bufferView];
      require(view?.buffer === 0 && Number.isInteger(view.byteLength) && view.byteLength > 0, 'Invalid position buffer view.');
      const start = view.byteOffset ?? 0, relative = accessor.byteOffset ?? 0, stride = view.byteStride ?? 12;
      require([start, relative, stride].every(Number.isInteger) && start >= 0 && relative >= 0 && stride >= 12 && stride <= 252 && stride % 4 === 0
        && relative + (accessor.count - 1) * stride + 12 <= view.byteLength && start + view.byteLength <= gltf.buffers[0].byteLength, 'Position accessor escapes the embedded buffer.');
      require(start % 4 === 0 && relative % 4 === 0, 'Misaligned GLB position coordinates.');
      positionSamples += accessor.count;
      require(positionSamples <= 500000, 'Geometry exceeds the small prototype check bound.');
      for (let vertex = 0; vertex < accessor.count; vertex++) {
        const offset = start + relative + vertex * stride;
        const point = transform([binary.readFloatLE(offset), binary.readFloatLE(offset + 4), binary.readFloatLE(offset + 8)], node);
        require(point.every(Number.isFinite), 'Non-finite vertex coordinates.');
        for (let axis = 0; axis < 3; axis++) { minimum[axis] = Math.min(minimum[axis], point[axis]); maximum[axis] = Math.max(maximum[axis], point[axis]); }
      }
    }
  }
  require(positionSamples > 0, 'GLB has no measured vertices.');
  const expectedMinimum = [-manifest.dimensions_m.east_west / 2, -0.4, -manifest.dimensions_m.north_south / 2];
  const expectedMaximum = [manifest.dimensions_m.east_west / 2, 3.37, manifest.dimensions_m.north_south / 2];
  require(minimum.every((value, i) => near(value, expectedMinimum[i])) && maximum.every((value, i) => near(value, expectedMaximum[i])), 'Measured GLB bounds do not match the metre-scale Route Lab.');
  const spawns = gltf.nodes.filter(node => typeof node.extras?.spawn_id === 'string');
  require(spawns.length === 10 && manifest.spawns.length === 10, 'Expected ten spawn markers.');
  require(new Set(manifest.spawns.map(spawn => spawn.id)).size === 10, 'Duplicate spawn IDs in the manifest.');
  const teams = new Map([['south', 0], ['north', 0]]);
  for (const expected of manifest.spawns) {
    require(teams.has(expected.team) && expected.id.startsWith(`spawn_${expected.team}_`)
      && expected.facing_north === (expected.team === 'south')
      && Number.isFinite(expected.north) && (expected.team === 'south' ? expected.north < 0 : expected.north > 0)
      && near(expected.ground_height_m, 0.12, 0.001), 'Spawn team, facing or ground-height metadata differs from the Route Lab plan.');
    teams.set(expected.team, teams.get(expected.team) + 1);
    const matches = spawns.filter(node => node.extras.spawn_id === expected.id);
    require(matches.length === 1, 'Missing or duplicated spawn marker.');
    const marker = matches[0];
    require(marker.extras.daftar_role === 'spawn_visual_only' && marker.extras.prototype_only === true, 'Spawn marker must remain visual-only.');
    const position = transform([0, 0, 0], marker);
    // The Blender cylinder origin sits at 0.85 m, not at the 0.12 m pad surface.
    require(near(position[0], expected.east, 0.001) && near(position[1], 0.85, 0.001)
      && near(position[2], -expected.north, 0.001), 'Spawn coordinate does not match the plan-to-GLB axis mapping.');
  }
  require([...teams.values()].every(count => count === 5), 'Expected five spawn markers per team.');
  return { nodes: gltf.nodes.length, meshes: gltf.meshes.length, positionSamples,
    gltfBoundsMinM: minimum.map(value => Number(value.toFixed(6))), gltfBoundsMaxM: maximum.map(value => Number(value.toFixed(6))),
    spawnMarkersVerified: spawns.length };
}

export function checkPackage(root = packageRoot) {
  const manifestBytes = read(root, 'manifest.json', 256 * 1024), manifest = JSON.parse(manifestBytes);
  require(manifest.schema_version === 1 && manifest.id === 'daftar-route-lab' && manifest.status === 'original_blockout_prototype', 'Unexpected package identity.');
  require(manifest.authored_map_replacement === false && manifest.gameplay_integration_verified === false && manifest.unreal_executed === false, 'Prototype and engine acceptance boundaries changed; review before promotion.');
  require(manifest.dimensions_m?.east_west === 48 && manifest.dimensions_m?.north_south === 56
    && manifest.objective?.disk_radius_m === 3 && manifest.objective?.clearance_radius_from_centre_m === 4.5, 'Unexpected scale or objective convention.');
  for (const name of ['daftar-route-lab.blend', 'daftar-route-lab.glb', 'route-lab-preview.png']) require(manifest.files?.[name], `Missing artifact: ${name}`);
  for (const [name, expected] of Object.entries(manifest.files)) {
    const bytes = read(root, name);
    require(Number.isInteger(expected.bytes) && bytes.length === expected.bytes && /^[a-f0-9]{64}$/.test(expected.sha256) && hash(bytes) === expected.sha256, `Package bytes changed: ${name}`);
  }
  require(hash(read(root, 'build_route_lab.py', 1024 * 1024)) === manifest.recipe_sha256, 'Procedural source differs from its render/export manifest.');
  const geometry = checkGlb(read(root, 'daftar-route-lab.glb'), manifest);
  const evidence = JSON.parse(read(root, 'geometry-acceptance.json', 256 * 1024));
  require(evidence.manifest_sha256 === hash(manifestBytes) && evidence.status === 'portable_geometry_verified'
    && evidence.reimported_glb_mesh_objects === geometry.meshes && evidence.spawn_markers_position_verified === 10, 'Stored Blender evidence does not identify this package.');
  const png = read(root, 'route-lab-preview.png');
  require(png.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])) && png.readUInt32BE(16) === 1024 && png.readUInt32BE(20) === 832, 'Unexpected preview dimensions.');
  return { schemaVersion: 1, status: 'package_integrity_and_geometry_verified', sourceRepository: manifest.source_repository,
    conventionsCommit: manifest.conventions_commit, manifestSha256: hash(manifestBytes), glbSha256: manifest.files['daftar-route-lab.glb'].sha256,
    ...geometry, storedBlenderReimportEvidenceBound: true, engineLaunchedByThisCheck: false,
    gameplayVerified: false, unrealExecuted: false, gpuTested: false };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    require(process.argv.length === 2, 'This check accepts no shell commands, paths or engine options.');
    console.log(JSON.stringify(checkPackage(), null, 2));
  } catch (error) { console.error(`Route Lab check failed: ${error.message}`); process.exitCode = 1; }
}
